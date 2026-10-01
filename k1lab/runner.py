from __future__ import annotations
import importlib.metadata
import json
import os
import platform
import time
from pathlib import Path
from .contracts import Limits
from .errors import ContractError,Unavailable
from .journal import Journal,verify
from .k1_extension import registry_factory,K1Port
from .model_client import client_factory
from .native import make_adapter
from .policy import HTTPPolicy,PolicySpec
from .sources import load_k1,K1_REV,LIBERO_REV
from .util import atomic_json,load_json,digest,file_sha
from .manifests import validate
from .report import render

MODES=('k1_baseline','k1_stepwise','k1_sparse','hybrid_stepwise','hybrid_sparse','policy_only')


def validate_config(config):
    if config.get('condition') not in MODES:raise ContractError('unknown condition')
    if any(key in config.get('planner', {}) for key in ('api_key', 'access_token', 'authorization')):
        raise ContractError('credentials must come from environment variables, not saved configs')
    if config.get('memory_scope')!='current_episode_only':raise ContractError('only episode-local memory is allowed')
    if any(k in config for k in ('memory_dir','task_memory','exploration_memory','oracle_geometry','task_skill_library')):
        raise ContractError('task/oracle memory options are forbidden in this protocol')
    if config.get('policy') and config['condition'] in ('k1_baseline','k1_stepwise','k1_sparse'):
        raise ContractError('no policy is allowed in the matched no-VLA contrast')
    if config['condition'].startswith('hybrid') or config['condition']=='policy_only':
        if not config.get('policy'):raise ContractError('hybrid requires an explicit policy identity')
        PolicySpec.from_dict(config['policy']['spec'])
    if config.get('registry_options', {}).get('completion_feedback', False):
        raise ContractError('main protocol permits native success stopping, not actor-requested completion queries')
    Limits.from_dict(config.get('limits',{}))
    model=config.get('model') or os.environ.get('K1_MODEL')
    if config['condition']!='policy_only' and (not model or model.startswith('SET_')):
        raise ContractError('set explicit model ID via config or K1_MODEL')
    return model


def source_hash():
    root=Path(__file__).resolve().parents[1]
    paths=list((root/'k1lab').glob('*.py')) + list((root/'scripts').glob('*.py')) + [root/'run.py']
    return digest({str(p.relative_to(root)):file_sha(p) for p in sorted(paths) if p.is_file()})


def common_signature(config,case,models):
    model_config=dict(config.get('planner',{}))
    return digest({'model':config.get('model') or os.environ.get('K1_MODEL'),
        'planner':model_config,'k1':K1_REV,'libero':LIBERO_REV,
        'source':source_hash(),'resolution':config.get('resolution',384),'delta_axis':config.get('delta_axis',.03),
        'registry_options':config.get('registry_options',{}),'limits':config.get('limits',{}),
        'policy':config.get('policy',{}).get('spec'),'memory':'current_episode_only',
        'horizon_profile':'manifest','recording':'same_native_step_journal',
        'max_model_calls':config.get('max_model_calls',100)})


def run_case(config,case,out,*,allow_native=False,allow_api=False,allow_policy=False,pilot=False):
    if not allow_native:raise Unavailable('native execution requires --allow-native')
    model=validate_config(config);condition=config['condition'];root=Path(out)
    if root.exists():raise FileExistsError('fresh episode directory required')
    root.mkdir(parents=True)
    t=time.monotonic();adapter=None;provider=None;result={};error=None;models=[]
    env_info={'python':platform.python_version(),'platform':platform.platform()}
    for p in ('numpy','scipy','mujoco','robosuite','httpx','torch'):
        try:env_info[p]=importlib.metadata.version(p)
        except importlib.metadata.PackageNotFoundError:env_info[p]=None
    atomic_json(root/'case.json',case);atomic_json(root/'config.json',config);atomic_json(root/'environment.json',env_info)
    with Journal(root/'events.jsonl') as journal:
        try:
            runtime=load_k1(config['native']['k1_root'])
            adapter=make_adapter(config['native']|{'resolution':config.get('resolution',384),'delta_axis':config.get('delta_axis',.03)},case,journal)
            if config.get('policy'):
                if not pilot:
                    from .qualification import verify_policy_qualification
                    verify_policy_qualification(config['policy'],PolicySpec.from_dict(config['policy']['spec']))
                provider=HTTPPolicy(config['policy']['endpoint'],PolicySpec.from_dict(config['policy']['spec']),
                                    allow_network=allow_policy,journal=journal)
            limits=Limits.from_dict(config.get('limits',{}))
            if condition=='k1_stepwise':
                from dataclasses import replace
                limits=replace(limits,max_segments=1)
            if condition=='hybrid_stepwise':
                from dataclasses import replace
                limits=replace(limits,max_policy_steps=min(limits.max_policy_steps,config.get('stepwise_policy_steps',8)))
            if condition=='policy_only':
                from .engine import ExecutionEngine
                # No planner, no memory, no analytic skills; fixed policy gets original task instruction.
                class Port:
                    def __getattr__(self,name):return getattr(adapter,name)
                    def native_action(self,a):return adapter.execute_native_action7(a)
                    @property
                    def control_hz(self):return 20
                port=Port();engine=ExecutionEngine(port,limits,journal);i=0
                while adapter.frame<adapter.horizon and not adapter.success():
                    before=adapter.frame
                    receipt=engine.run_policy({'command_id':f'policy-{i}','frame_id':adapter.frame,'arm':'arm',
                        'subgoal':adapter.observe()['instruction'],'max_native_steps':limits.max_policy_steps},provider)
                    i+=1
                    if adapter.frame==before or 'exception' in receipt['stop_reason']:break
                result={'native_success':adapter.success(),'native_steps':adapter.frame,'llm_calls':0,
                        'termination':'native_success' if adapter.success() else 'budget'}
            else:
                opts=dict(config.get('registry_options',{}))
                allowed={'history_rounds','history_image_rounds','region_tools','interaction_feedback','completion_feedback',
                         'tracking_backend','tracking_device','grasp_provider','move_toward_max_steps','move_toward_stall_steps','move_toward_tolerance_m'}
                if set(opts)-allowed:raise ContractError('unsupported K1 option')
                registry=None if condition=='k1_baseline' else registry_factory(
                    sparse=condition in ('k1_stepwise','k1_sparse','hybrid_sparse'),policy=provider,limits=limits,journal=journal,grasp_macro=condition!='k1_stepwise')
                result=runtime.run_agent(adapter,root/'k1','http://local-transport.invalid/v1','not-a-real-key',
                    model=model,max_calls=config.get('max_model_calls',100),delta_axis=config.get('delta_axis',.03),
                    registry_class=registry,client_factory=client_factory(config['planner'],root/'wire',journal,allow_api),**opts)
                agent_path=root/'k1/agent.jsonl'
                if agent_path.exists():
                    models=sorted({r.get('model') or 'unreported' for r in (json.loads(line) for line in agent_path.read_text().splitlines())})
                if len(models)>1:raise ContractError('model revision drift within episode')
        except Exception as exc:
            error={'type':type(exc).__name__,'message':str(exc)[:1000]}
            journal.append('episode_error',error)
        finally:
            # Preserve actual partial progress, never count a transport failure as native success by fiat.
            success=False
            steps=int(adapter.frame) if adapter is not None else 0
            if adapter is not None:
                try:
                    success=bool(adapter.success())
                except Exception as exc:
                    error=error or {'type':type(exc).__name__,'message':'final native success read failed'}
                    journal.append('final_observation_error',error)
            for resource in (provider, adapter):
                if resource is not None:
                    try:
                        resource.close()
                    except Exception as exc:
                        # Cleanup cannot silently delete a measured outcome.
                        journal.append('cleanup_error',{'type':type(exc).__name__,'message':str(exc)[:300]})
        journal.append('episode_end',{'native_success':success,'native_steps':steps,'error':error})
    rows=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    planner_requests=[x for x in rows if x['event']=='model_request']; policy_requests=[x for x in rows if x['event']=='policy_request']
    model_responses=[x['data'] for x in rows if x['event']=='model_response']
    policy_responses=[x['data'] for x in rows if x['event']=='policy_response']
    usages=[x.get('usage') or {} for x in model_responses]
    token_totals={name:sum(u.get(name,0) for u in usages if type(u.get(name)) is int)
                  for name in ('prompt_tokens','completion_tokens')}
    known_usage=sum(type(u.get('prompt_tokens')) is int and type(u.get('completion_tokens')) is int for u in usages)
    out_result={**result,'case_id':case['id'],'state_sha256':case['state_sha256'],'condition':condition,
        'domain':'native_libero_pro','native_success':success,'native_steps':steps,'elapsed_seconds':time.monotonic()-t,
        'llm_calls':len(planner_requests),'policy_calls':len(policy_requests),'resolved_models':models,
        'provider_reported_input_tokens':token_totals['prompt_tokens'],
        'provider_reported_output_tokens':token_totals['completion_tokens'],
        'model_calls_with_known_usage':known_usage,
        'model_wait_s':sum(x.get('latency_s',0) for x in model_responses),
        'policy_wait_s':sum(x.get('latency_s',0) for x in policy_responses),
        'upstream_agent_elapsed_s':result.get('elapsed_seconds'),
        'timing_scope':'episode wall includes reset/setup/close; successful model/policy waits separately; failed-call time only in wall',
        'termination':'native_success' if success else 'infrastructure_failure' if error else 'task_failure',
        'error':error,'pilot':pilot,'partition':case['partition'],
        'comparison_signature':common_signature(config,case,models),'source_sha256':source_hash(),
        'epoch_memory':'empty_at_episode_start','benchmark_predicate_role':'native_stop_only',
        'timing':{'observe_seconds_inclusive':getattr(adapter,'observe_seconds',None),
                  'motion_seconds_inclusive':getattr(adapter,'motion_seconds',None),
                  'note':'Inclusive timings overlap; do not sum. Wall time includes setup unless noted.'}}
    atomic_json(root/'evaluation_result.json',out_result)
    atomic_json(root/'journal_verification.json',verify(root/'events.jsonl'))
    return out_result


def run_matrix(configs,manifest_path,output,partition='dev',allow_native=False,allow_api=False,allow_policy=False,pilot=False):
    manifest=validate(load_json(manifest_path));cases=[c for c in manifest['cases'] if c['partition']==partition]
    if not cases:raise ContractError('empty partition')
    configs=[load_json(p) for p in configs]
    if len({c['condition'] for c in configs})!=len(configs):raise ContractError('duplicate conditions')
    out=Path(output)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True);atomic_json(out/'manifest.json',manifest)
    for config in configs:
        validate_config(config)
        if partition=='test':
            if pilot:raise ContractError('pilot is for dev only; do not expose test cases during bring-up')
            from .qualification import verify_freeze
            verify_freeze(config,manifest)
    results={c['condition']:[] for c in configs}
    # Alternate order by episode, not all baseline then all treatment.
    for i,case in enumerate(cases):
        order=configs[i%len(configs):]+configs[:i%len(configs)]
        for config in order:
            row=run_case(config,case,out/config['condition']/case['id'],allow_native=allow_native,
                         allow_api=allow_api,allow_policy=allow_policy,pilot=pilot)
            results[config['condition']].append(row)
            atomic_json(out/'outcomes.json',results)
            render(out/'report.html',cases,results,'native_libero_pro')
    return results
