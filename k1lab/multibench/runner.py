"""Single owner, one fresh episode; no uncertain mutation is retried.

Policy acknowledgements follow actual physical ACKs, never a proposed suffix.
Evaluator score is collected in results only. The reviewer sees no reward signal.
"""
from __future__ import annotations
import time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from k1lab.util import atomic_json, digest
from k1lab.journal import Journal
from k1lab.errors import ContractError
from .governor import SparseGovernor,MonitorConfig
from .types import Proposal


MODES={'motor_only','review_every_chunk','sparse','direct_dense','direct_sparse'}


def run_episode(env, policy, reviewer, case, config, output, *, clock=time.monotonic):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if any((output/name).exists() for name in ('events.jsonl','run.json','result.json','observations')):
        raise FileExistsError('refusing to overwrite existing episode')
    journal=Journal(output/'events.jsonl')
    mode=config['mode']
    if mode not in MODES:raise ContractError('unsupported condition')
    direct=mode.startswith('direct_')
    if direct != (policy is None):raise ContractError('direct must have no motor model; hybrid must have one')
    if mode!='motor_only' and reviewer is None:raise ContractError('reviewer required')
    governor=SparseGovernor(MonitorConfig(**config.get('monitor',{})))
    started=clock(); times={'policy_s':0.,'review_s':0.,'env_s':0.,'ack_s':0.,'setup_s':0.,'preview_s':0.}
    metrics={'policy_calls':0,'review_calls':0,'corrected_steps':0,'motor_steps':0,
             'discarded_policy_actions':0,'interruptions':0,'policy_invalidation_requests':0,'shortened_chunks':0}
    status='incomplete';reason=None;native_success=False;score=None;obs=None;last=None;error=None
    receipts=[];last_receipt=None;serial=0;proposal=None
    max_steps=int(config.get('max_decision_steps',15))
    wall_limit=float(config.get('wall_limit_s',3600))
    max_reviews=int(config.get('max_reviews',180))
    contract={'correction_space':env.correction_space,'max_decision_steps':max_steps,
              'translation_limit_m':config.get('translation_limit_m',.05),'rotation_limit_rad':.35,
              'pose_frame':getattr(env,'pose_frame','adapter-defined'),
              'max_correction_steps':config.get('max_correction_steps',5),
              'mode':mode,'meaning':getattr(env,'correction_description','See adapter contract.')}

    def log(event,value):journal.append(event,value)
    def ack(observation):
        if policy is not None:
            t=clock();policy.observe(observation);times['ack_s']+=clock()-t
    def invalidate(why):
        if policy is not None:
            t=clock();policy.invalidate(why);metrics['policy_invalidation_requests']+=1;times['ack_s']+=clock()-t
            log('policy_queue_invalidated',{'reason':why,'frame':obs.step})
    def record(observation):
        directory=output/'observations'/f'{observation.step:06d}'
        directory.mkdir(parents=True,exist_ok=False)
        atomic_json(directory/'state.json',observation.actor_state())
        np.savez_compressed(directory/'sensors.npz',state=observation.state,**observation.rgb)
        from PIL import Image
        for key,image in observation.rgb.items():
            # Native camera names are mapped to safe filenames; no arbitrary source paths.
            if not key.replace('_','').replace('.','').isalnum():raise ContractError('unsafe camera name')
            Image.fromarray(image).save(directory/(key+'.jpg'),quality=90)

    try:
        t=clock();obs=env.reset(case);times['setup_s']+=clock()-t
        initial=obs.stamp; record(obs)
        contract['initial_robot_poses']=obs.eef
        contract['public_task_requirements']=getattr(env,'public_task_requirements',{})
        if policy is not None:policy.reset();ack(obs)
        if reviewer:reviewer.reset()
        log('episode_begin',{'case':case,'config':config,'initial_observation_sha256':initial,
                             'initial_hash_scope':'RGB/proprio/instruction; NOT a complete physics state',
                             'policy':asdict(policy.identity) if policy else None,
                             'environment':env.describe(), 'contract':contract})
        atomic_json(output/'run.json',{'case':case,'config':config,'policy':asdict(policy.identity) if policy else None,
                                      'environment':env.describe(),'initial_observation_sha256':initial})
        while obs.step < env.horizon:
            if clock()-started > wall_limit:reason='wall_limit';break
            start_step=obs.step;proposal=None;reviewed=False
            if not direct:
                t=clock();proposal=policy.propose(obs);times['policy_s']+=clock()-t;metrics['policy_calls']+=1
                proposal.validate(obs,policy.identity)
                log('policy_proposal',{'step':obs.step,'policy_identity':proposal.policy_identity,
                                      'actions':[a.json() for a in proposal.actions],
                                      'observation_sha256':proposal.observation_sha256})
                reasons=governor.review_reasons(mode,obs.step,proposal,obs)
            else:reasons=['direct_action_request']
            if reasons:
                if metrics['review_calls']>=max_reviews:reason='review_budget';break
                if proposal is not None and config.get('robot_preview',True):
                    t=clock();proposal.diagnostics['robot_preview']=env.preview(proposal);times['preview_s']+=clock()-t
                t=clock();decision=reviewer.review(obs,proposal,reasons,last_receipt,contract,direct=direct)
                times['review_s']+=clock()-t;metrics['review_calls']+=1;reviewed=True
                # Revalidate at the execution boundary, including external/scripted actors.
                from .actor import decode
                payload=asdict(decision);payload['actions']=[a.values.tolist() for a in decision.actions]
                decision=decode(payload,obs,proposal,contract['correction_space'],max_steps,direct=direct,
                    translation_limit=contract['translation_limit_m'],rotation_limit=contract['rotation_limit_rad'])
                if decision.mode=='correct' and decision.steps>contract['max_correction_steps']:
                    raise ContractError('correction horizon exceeds lease')
                governor.reviewed(obs.step)
                log('review',{'step':obs.step,'reasons':reasons,'decision':asdict(decision)})
                if decision.mode=='stop':reason='model_stop_incomplete';break
            else:
                from .actor import Decision
                decision=Decision('accept',min(policy.identity.execute_steps,len(proposal.actions)))
            if clock()-started > wall_limit:reason='wall_limit_after_inference';break
            correction=decision.mode=='correct'
            if correction:
                if policy is not None:
                    metrics['discarded_policy_actions']+=len(proposal.actions);invalidate('teacher_correction')
                actions=decision.actions
                count=decision.steps
            else:
                count=decision.steps
                if count>policy.identity.execute_steps:raise ContractError('review may not extend source execution horizon')
                count=governor.allowance(obs.step,count,mode)
                if count<1:raise ContractError('empty execution lease')
                if count<len(proposal.actions):metrics['shortened_chunks']+=1
                actions=proposal.actions[:count]
            if reviewer and hasattr(reviewer,'note_execution_start'):reviewer.note_execution_start(obs)
            end_reason='prefix_completed';executed=0
            for i in range(count):
                if obs.step>=env.horizon: end_reason='episode_budget';break
                if clock()-started>wall_limit:end_reason='wall_limit';break
                action=actions[0] if correction and len(actions)==1 else actions[i]
                before=obs.step;t=clock()
                result=env.step(action,correction=correction)
                times['env_s']+=clock()-t
                if result.observation.episode!=obs.episode or result.observation.step!=before+1:
                    raise ContractError('physical ACK identity/counter mismatch')
                obs=result.observation;last=result;executed+=1
                metrics['corrected_steps' if correction else 'motor_steps']+=1
                ack(obs);governor.observe(obs,executed_action=action)
                log('control_ack',{'step':obs.step,'action':action.json(),'correction':correction,
                                   'eef':obs.eef,'terminated':result.terminated,'truncated':result.truncated})
                # Native scores intentionally never become part of execution receipts.
                if result.terminated or result.truncated:
                    native_success=result.success;score=result.score;status='native_completed';reason='native_terminal'
                    end_reason='native_terminal';break
                if mode=='sparse' and governor.pending:
                    end_reason='monitor_event';metrics['interruptions']+=1;break
                if correction and len(actions)==1 and executed>=min(5,count) and hasattr(env,'correction_reached') and env.correction_reached(action):
                    end_reason='robot_target_reached_not_task_success';break
            if proposal is not None and not correction:
                unused=len(proposal.actions)-executed
                metrics['discarded_policy_actions']+=unused
                # Stateful adapters can consume their exposed prefix fully even when the
                # network predicted additional hidden steps. Only shortened EXPOSED prefix
                # triggers invalidation; native adapter owns its internal suffix semantics.
                if unused:invalidate('unexecuted_proposal_suffix')
            governor.chunk_finished()
            last_receipt={'serial':serial,'start_step':start_step,'end_step':obs.step,
                          'executed_steps':executed,'executor':'correction' if correction else 'motor',
                          'stop_reason':end_reason,'reviewed':reviewed,
                          'object_effect':'not_certified_by_robot_motion'}
            receipts.append(last_receipt);serial+=1;log('execution_receipt',last_receipt);record(obs)
            if status=='native_completed':break
            if not executed:raise ContractError('executor made no progress')
        if status!='native_completed' and obs.step>=env.horizon:
            status='budget_exhausted';reason='native_step_budget'
        # Score readout occurs after execution, only from evaluator adapter.
        final=env.finish(reason or 'incomplete')
        if status=='native_completed' and final.get('score') is not None:score=final['score']
        if final.get('success') is True and not native_success:raise ContractError('finish disagrees with terminal ACK')
    except Exception as exc:
        reason='error:'+type(exc).__name__;error=str(exc)[:600];status='infrastructure_or_contract_error'
        log('error',{'reason':reason,'detail':error,'automatic_retry':False})
        try:env.finish(reason)
        except Exception:pass
    finally:
        try:env.close()
        except Exception:pass
        if policy is not None:
            try:policy.close()
            except Exception:pass
        if reviewer:
            try:reviewer.close()
            except Exception:pass
    elapsed=clock()-started
    result={'schema':'multibench.result.v1','case_id':case['case_id'],'task':case['task'],
            'benchmark':case['benchmark'],'condition':config['name'],'mode':mode,
            'split':case.get('split'),'partition':case.get('partition','dev'),
            'group':case.get('task_group',case['task']),
            'success':bool(native_success and status=='native_completed'),
            'native_score':score,'status':status,'termination':reason,'error':error,
            'native_steps':obs.step if obs else 0,'simulated_seconds':obs.step/obs.control_hz if obs else 0.,
            'elapsed_s':elapsed,'timing':times,'metrics':metrics,
            'config_sha256':digest(config),'case_sha256':digest(case),
            'initial_observation_sha256':initial if obs is not None and 'initial' in locals() else None,
            'simulation_advances_during_model_wait':False,
            'evidence_kind':getattr(env,'evidence_kind','native_unqualified'),
            'runtime_fingerprint':getattr(env,'runtime_fingerprint',{}),
            'policy_identity':policy.identity.identity if policy else None,
            'policy_runtime_fingerprint':getattr(policy,'server_info',{}).get('runtime_fingerprint') if policy else None,
            'planner_model':config.get('model',{}).get('model') if reviewer else None,
            'environment_contract_sha256':digest(env.describe()) if obs else None,
            'planner_config':config.get('model') if reviewer else None,
            'usage':usage_summary(reviewer),
            'task_memory':False,'task_demonstrations':False}
    atomic_json(output/'result.json',result);atomic_json(output/'receipts.json',receipts)
    log('episode_end',result);journal.close()
    return result


def usage_summary(reviewer):
    if reviewer is None:
        return {'api_requests':0,'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'reasoning_tokens':0,'source':'no model used'}
    c=getattr(reviewer,'client',None)
    if c is None:return {'source':'scripted/externally controlled actor; tokens unmeasured'}
    rows=getattr(c,'usages',[])
    def total(fn):
        vals=[fn(r) for r in rows]
        return sum(vals) if vals and all(type(v) is int for v in vals) else None
    return {'source':'provider-reported, missing fields remain null',
        'api_requests':getattr(c,'n',None),
        'input_tokens':total(lambda r:r.get('prompt_tokens')),
        'cached_input_tokens':total(lambda r:(r.get('prompt_tokens_details') or {}).get('cached_tokens')),
        'output_tokens':total(lambda r:r.get('completion_tokens')),
        'reasoning_tokens':total(lambda r:(r.get('completion_tokens_details') or {}).get('reasoning_tokens')),
        'reasoning_is_subset_of_output':True,
        'served_models':sorted(set(str(x) for x in getattr(c,'served_models',[]))),
        'served_tiers':sorted(set(str(x) for x in getattr(c,'served_tiers',[]))),
        'unresolved_output_reservations':getattr(c,'reserved',None)}
