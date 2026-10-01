from __future__ import annotations
import time
import traceback
import platform
from pathlib import Path
from .contracts import Proposal,MODES
from .budget import Budget,CallLedger
from .governor import Governor,GovernorConfig
from .registry import Registry
from .journal import Journal
from .errors import PRLError,Unavailable,ValidationError
from .manifests import load_manifest
from .util import digest,plain,atomic_json,file_digest
from .planners.base import make_context
from .planners.local import ReferencePlanner,CommandPlanner,FilePlanner
from .planners.compatible_api import CompatibleAPIPlanner


def source_fingerprint(root):
    return digest({str(p.relative_to(root)):file_digest(p)
                   for folder in ('prl','scripts','examples')
                   for p in sorted((root/folder).rglob('*.py'))})


def planner_factory(config,ledger,allow_api):
    p=config.get('planner',{'kind':'reference'}); kind=p.get('kind')
    if kind=='reference': return ReferencePlanner()
    if kind=='command': return CommandPlanner(p['command'],p.get('timeout_s',120))
    if kind=='file': return FilePlanner(p['queue'],p.get('timeout_s',300))
    if kind=='api': return CompatibleAPIPlanner(p,ledger,allow_api=allow_api)
    raise ValidationError(f'unknown_planner:{kind}')


def run_experiment(config,manifest_path,output,*,allow_native=False,allow_api=False,resume=False):
    manifest,cases=load_manifest(manifest_path)
    mode=config['mode']
    if mode not in MODES: raise ValidationError('invalid_experiment_mode')
    if config.get('backend') not in ('synthetic','rpent'):
        raise ValidationError('backend_must_be_synthetic_or_rpent')
    native=config.get('backend')=='rpent'
    if native and not allow_native: raise Unavailable('Pass --allow-native to launch simulation')
    if native != (manifest['source']=='native'): raise ValidationError('backend_manifest_source_mismatch')
    if native and config.get('planner',{}).get('kind')=='reference' and mode!='frozen':
        raise ValidationError('Reference fixture planner cannot operate native benchmark')
    output=Path(output)
    if output.exists() and not resume: raise FileExistsError(output)
    output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    runtime_config={**config,'allow_native':allow_native}
    registry=Registry(k1=mode=='dynamic_k1',**config.get('registry',{}))
    run_info={'version':1,'source':'native' if native else 'synthetic',
              'mode':mode,'manifest_sha256':manifest['sha256'],'split':manifest['split'],
              'code_sha256':source_fingerprint(root),'config_sha256':digest(config),
              'capability_sha256':registry.fingerprint,'python':platform.python_version(),
              'config':config,'benchmark':'LIBERO-PRO' if native else 'SYNTHETIC-CONTRACT-FIXTURE',
              'claim':'Independent implementation, not an exact DynaHarness reproduction.'}
    if resume:
        from .util import read_json
        previous=read_json(output/'run.json')
        for key in ('source','manifest_sha256','config_sha256','code_sha256'):
            if previous[key]!=run_info[key]: raise ValidationError(f'resume_mismatch:{key}')
        if (output/'model_calls.jsonl').exists():
            # Do not silently reset shared API spend after a process restart.
            rows=Journal.verify(output/'model_calls.jsonl')
            if any(r['kind']=='model_reservation' for r in rows):
                raise ValidationError('API resume requires explicit ledger reconciliation; start a new run')
    atomic_json(output/'run.json',run_info)
    atomic_json(output/'manifest.json',manifest)
    calls=Journal(output/'model_calls.jsonl',resume=resume)
    ledger=CallLedger(calls,**config.get('call_budget',{}))
    try:
        planner=None if mode=='frozen' else planner_factory(config,ledger,allow_api)
        run_info['planner_identity']='none' if planner is None else planner.identity
        atomic_json(output/'run.json',run_info)
        infra_errors=0
        for case in cases:
            d=output/'episodes'/case.case_id
            if d.exists():
                if resume and (d/'result.json').exists(): continue
                raise ValidationError(f'incomplete_episode_requires_manual_reconciliation:{case.case_id}')
            d.mkdir(parents=True)
            atomic_json(d/'STARTED.json',{'case_id':case.case_id,'identity':case.identity})
            result=run_case(case,d,runtime_config,registry,planner,mode)
            if result['status']!='completed':
                infra_errors+=1
                if infra_errors>=config.get('max_infrastructure_errors',1):
                    atomic_json(output/'STOPPED.json',{'reason':'infrastructure_error_limit',
                        'case_id':case.case_id,'errors':infra_errors})
                    break
    finally: calls.close()
    from .evaluation import summarize_run
    summary=summarize_run(output)
    atomic_json(output/'summary.json',summary)
    from .report import write_report
    write_report(output/'report.html',summary)
    return summary


def run_case(case,out,config,registry,planner,mode):
    journal=Journal(out/'events.jsonl')
    b=None; receipts=[]; status='infrastructure_error'; reason='not_started'; error=None
    start=time.monotonic()
    budget=Budget(max_steps=config.get('max_steps',520),max_decisions=config.get('max_decisions',30),
                  max_wall_s=config.get('max_wall_s',1800),max_vla_calls=config.get('max_vla_calls',100))
    try:
        if config.get('backend')=='rpent':
            from .backends.rpent import RPentBackend
            b=RPentBackend(case,out,config)
        else:
            from .backends.toy import ToyBackend
            b=ToyBackend(case,out,config)
        atomic_json(out/'backend.json',b.metadata)
        gc=GovernorConfig(dynamic=mode in ('dynamic','dynamic_k1'),**config.get('governor',{}))
        governor=Governor(b,registry,budget,journal,gc)
        while budget.steps<budget.max_steps and budget.decisions<budget.max_decisions:
            if b.native_success or b.native_truncated: break
            budget.check_wall()
            obs=b.capture()
            journal.append('observation',obs.actor_view())
            pid=f'{case.case_id}:d{budget.decisions}'
            if mode=='frozen':
                budget.take_decision()
                p=Proposal(pid,obs.observation_id,'vla',{},budget.max_steps-budget.steps,
                           'Frozen policy only, original task instruction.')
            else:
                context=make_context(obs,registry,receipts,budget,pid)
                turn=out/'turns'/f'{budget.decisions:04d}'; turn.mkdir(parents=True)
                atomic_json(turn/'context.json',context)
                budget.take_decision()
                t=time.monotonic()
                p=planner.decide(context,turn)
                journal.append('planner_call',{'proposal_id':pid,'wall_s':time.monotonic()-t,
                                               'planner':planner.identity})
            r=governor.execute(p); receipts.append(r)
            if p.capability=='finish': reason='agent_finish'; break
            if r.reason in ('episode_step_budget','vla_call_budget','wall_budget'):
                reason=r.reason; break
            if governor.poisoned: reason='uncertain_execution'; break
            if governor.terminal: break
            if mode=='frozen': break
        status='completed'
        if b.native_success: reason='native_success'
        elif b.native_truncated: reason='native_truncated'
        elif budget.steps>=budget.max_steps: reason='episode_step_budget'
        elif budget.decisions>=budget.max_decisions: reason='decision_budget'
        elif reason=='not_started': reason='stopped_without_native_success'
    except PRLError as e:
        from .errors import BudgetExceeded,UncertainExecution
        reason=str(e)
        if isinstance(e,BudgetExceeded):
            # Whole-campaign provider budget exhaustion must stop scheduling,
            # not turn every unattempted case into an algorithmic failure.
            status=('campaign_budget_exhausted' if reason in
                    ('model_reservation_budget','provider_usage_exceeded_reservation')
                    else 'completed')
        elif isinstance(e,UncertainExecution): status='uncertain_execution'
        elif isinstance(e,ValidationError): status='protocol_error'
        else: status='infrastructure_error'
        error=type(e).__name__
        journal.append('error',{'type':error,'reason':reason})
        (out/'traceback.txt').write_text(traceback.format_exc())
    except Exception as e:
        reason=f'{type(e).__name__}:{e}'; error=type(e).__name__
        journal.append('error',{'type':error,'reason':reason})
        (out/'traceback.txt').write_text(traceback.format_exc())
    finally:
        success=bool(b.native_success) if b is not None else None
        if b is not None:
            try: b.close()
            except Exception as e: journal.append('cleanup_error',{'type':type(e).__name__})
        result={'case':plain(case),'identity':case.identity,
                'source':'native' if config.get('backend')=='rpent' else 'synthetic',
                'status':status,'reason':reason,'native_success':success if status=='completed' else None,
                'native_steps':budget.steps,'simulated_seconds':budget.steps/config.get('control_hz',20),
                'control_hz':config.get('control_hz',20),'planner_calls':0 if mode=='frozen' else budget.decisions,
                'vla_calls':budget.vla_calls,'wall_s':time.monotonic()-start,
                'receipts':len(receipts),'refusals':sum(r.status=='refused' for r in receipts),
                'interrupts':sum(r.status=='interrupted' for r in receipts),
                'substitutions':sum(e.get('kind')=='substitution' for r in receipts for e in r.events),
                'error_type':error,'policy_seed_requested':case.policy_seed,
                'policy_rng_control':b.metadata.get('policy_rng_control') if b is not None else None}
        journal.append('episode_result',result)
        journal.close()
        result['journal_tail_sha256']=Journal.verify(out/'events.jsonl')[-1]['hash']
        atomic_json(out/'result.json',result)
    return result
