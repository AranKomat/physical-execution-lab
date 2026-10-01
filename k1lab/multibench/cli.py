from __future__ import annotations
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import time
from k1lab.util import atomic_json,load_json,digest
from k1lab.errors import ContractError
from . import manifest as mf


def main(argv=None):
    p=argparse.ArgumentParser(description='Physical execution lab: no task recipe memory, explicit native opt-in')
    sp=p.add_subparsers(dest='command',required=True)
    d=sp.add_parser('doctor')
    q=sp.add_parser('make-configs');q.add_argument('--output',default='configs/multibench')
    q=sp.add_parser('synthetic');q.add_argument('--output',required=True)
    q=sp.add_parser('hash-artifacts');q.add_argument('--root',required=True);q.add_argument('--output',required=True)
    q=sp.add_parser('import-robodojo');q.add_argument('--source-results',required=True);q.add_argument('--source-panel');q.add_argument('--output',required=True)
    q=sp.add_parser('robocasa-manifest');q.add_argument('--trials',type=int,default=50);q.add_argument('--seed',type=int,default=7);q.add_argument('--split',default='pretrain');q.add_argument('--output',required=True)
    q=sp.add_parser('freeze');q.add_argument('--manifest',required=True);q.add_argument('--configs',nargs='+',required=True);q.add_argument('--output',required=True)
    q=sp.add_parser('run-case');q.add_argument('--config',required=True);q.add_argument('--manifest',required=True);q.add_argument('--case-id',required=True);q.add_argument('--output',required=True)
    q.add_argument('--freeze');q.add_argument('--qualification');q.add_argument('--development',action='store_true')
    for flag in ('allow-native','allow-policy','allow-api'):q.add_argument('--'+flag,action='store_true')
    q=sp.add_parser('serve-policy');q.add_argument('--config',required=True);q.add_argument('--port',type=int,default=19600);q.add_argument('--allow-policy',action='store_true')
    q=sp.add_parser('latency');q.add_argument('--config',required=True);q.add_argument('--observations',nargs='+',required=True);q.add_argument('--warmup',type=int,default=3);q.add_argument('--repeats',type=int,default=30);q.add_argument('--output',required=True);q.add_argument('--allow-policy',action='store_true')
    q=sp.add_parser('report');q.add_argument('--manifest',required=True);q.add_argument('--runs',required=True);q.add_argument('--output',required=True);q.add_argument('--baseline');q.add_argument('--candidate');q.add_argument('--conditions',nargs='+');q.add_argument('--partition',choices=['dev','test','all'],default='test')
    a=p.parse_args(argv);root=Path(__file__).resolve().parents[2]
    if a.command=='doctor':
        print(json.dumps({'model_default':'gpt-6.1-sol','model_transport':'responses','service_tiers':'flex default; explicit default comparison; no silent fallback',
            'native_experiments_run_on_build_host':0,'gpu_policy_inferences_on_build_host':0,
            'benchmarks':['robodojo','robocasa365','legacy K1/LIBERO via run.py'],
            'Xiaomi_RoboDojo_caveat':'current RPC port uses bounded-DLS controller variant; qualify separately',
            'depth_status':'not exported by source RoboDojo RPC; K1 RGB-D remains LIBERO-only',
            'network_default':'off'},indent=2));return
    if a.command=='make-configs':
        from .catalog import write_configs
        write_configs(a.output);print(a.output);return
    if a.command=='synthetic':
        from .synthetic import run
        print(json.dumps(run(a.output),indent=2));return
    if a.command=='hash-artifacts':atomic_json(a.output,mf.artifacts(a.root),exclusive=True);return
    if a.command=='import-robodojo':atomic_json(a.output,mf.import_robodojo(a.source_results,a.source_panel),exclusive=True);return
    if a.command=='robocasa-manifest':
        from robocasa.utils.dataset_registry import TASK_SET_REGISTRY
        from robocasa.utils.dataset_registry_utils import get_task_horizon
        tasks=list(TASK_SET_REGISTRY['target50'])
        if len(tasks)!=50:raise ContractError('target50 registry does not have 50 tasks; inspect source revision')
        atomic_json(a.output,mf.robocasa_cases(tasks,{t:get_task_horizon(t) for t in tasks},a.trials,a.seed,a.split),exclusive=True);return
    if a.command=='freeze':
        m=load_json(a.manifest);c=[mf.resolved_config(load_json(x)) for x in a.configs]
        atomic_json(a.output,mf.freeze(root,m,c),exclusive=True);return
    if a.command=='serve-policy':
        from .factory import policy
        from .transport import serve
        c=load_json(a.config); c=mf.resolved_config({'policy':c})['policy']
        t=time.perf_counter();pol=policy(c,a.allow_policy);elapsed=time.perf_counter()-t
        serve(pol,a.port,elapsed);return
    if a.command=='latency':
        from .factory import policy
        from .transport import decode_obs
        from .latency import benchmark
        c=mf.resolved_config({'policy':load_json(a.config)})['policy'];pol=policy(c,a.allow_policy)
        try:result=benchmark(pol,[decode_obs(load_json(f)) for f in a.observations],warmup=a.warmup,repeats=a.repeats)
        finally:pol.close()
        atomic_json(a.output,result,exclusive=True);return
    if a.command=='run-case':
        from .factory import environment,policy
        from .actor import ModelReviewer
        from .runner import run_episode
        m=mf.check(load_json(a.manifest));c=mf.resolved_config(load_json(a.config))
        case=next((v for v in m['cases'] if v['case_id']==a.case_id),None)
        if case is None or case['benchmark']!=c['benchmark']:raise ContractError('case/config benchmark mismatch')
        if a.development:
            if case['partition']!='dev':raise ContractError('development cannot run held-out cases')
        else:
            if not a.freeze or not a.qualification:raise ContractError('scored native run requires freeze and qualification')
            mf.verify_freeze(root,load_json(a.freeze),m,c)
            mf.verify_qualification(load_json(a.qualification),c)
        # Fail before opening simulation on missing permissions.
        if not a.allow_native:raise ContractError('native run requires --allow-native')
        if c.get('policy') and not a.allow_policy:raise ContractError('policy run requires --allow-policy')
        if c['mode']!='motor_only' and c['model']['transport'] in ('responses','chat') and not a.allow_api:raise ContractError('model requires --allow-api')
        out=Path(a.output)
        if out.exists():raise FileExistsError(out)
        actor=None;pol=None;env=None
        try:
            if c['mode']!='motor_only':actor=ModelReviewer(c['model'],out/'model',allow_api=a.allow_api)
            if c.get('policy'):pol=policy(c['policy'],a.allow_policy)
            env=environment(c['environment'],a.allow_native)
            from .fingerprint import capture
            env.runtime_fingerprint=capture()
            result=run_episode(env,pol,actor,case,c,out)
        except Exception:
            for obj in (env,pol,actor):
                if obj:
                    try:obj.close()
                    except Exception:pass
            raise
        print(json.dumps(result,indent=2))
        if result['status']=='infrastructure_or_contract_error':raise SystemExit(2)
        return
    if a.command=='report':
        from .report import render,paired
        m=mf.check(load_json(a.manifest));cases=[c for c in m['cases'] if a.partition=='all' or c['partition']==a.partition]
        ids={c['case_id'] for c in cases}
        results=[load_json(f) for f in Path(a.runs).rglob('result.json')]
        results=[r for r in results if r.get('schema')=='multibench.result.v1' and r['case_id'] in ids]
        render(cases,results,a.output,a.conditions)
        if a.baseline and a.candidate:atomic_json(Path(a.output)/'paired.json',paired(cases,results,a.baseline,a.candidate))
        return

if __name__=='__main__':main()
