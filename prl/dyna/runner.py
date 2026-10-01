"""Paper-track CLI with full-denominator scoring and explicit replication gaps."""
from pathlib import Path
import argparse
import time
import sys
import traceback
import platform
from .protocol import PaperSettings,ARMS,suite_budget,PAPER_SUITES
from .engine import Engine
from .capabilities import PaperLibrary
from ..manifests import load_manifest
from ..budget import CallLedger
from ..journal import Journal
from ..util import plain,read_json,atomic_json,digest,file_digest
from ..errors import ValidationError,PRLError,Unavailable
from ..runner import source_fingerprint
from ..evaluation import wilson,cluster_bootstrap,mcnemar_exact,read_run


def run(config,manifest_path,out,allow_native=False,allow_api=False):
    manifest,cases=load_manifest(manifest_path);root=Path(__file__).resolve().parents[2]
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    source=manifest['source'];arm=config['arm'];settings=PaperSettings(**config.get('settings',{}))
    if arm not in ARMS:raise ValidationError('unknown_arm')
    native=source=='native'
    if native and not allow_native:raise Unavailable('--allow-native required')
    if config['backend']!=('direct_libero' if native else 'synthetic'):
        raise ValidationError('manifest_backend_mismatch')
    if native and config.get('information_profile')!='privileged_sim':
        raise ValidationError('separate_K1_sensor_extension_from_paper_geometry_profile')
    info={'version':2,'track':'pdf_reproduction','source':source,'mode':arm,'split':manifest['split'],
          'benchmark':'LIBERO-PRO' if native else 'SYNTHETIC-CONTRACT-FIXTURE',
          'manifest_sha256':manifest['sha256'],'config':config,'config_sha256':digest(config),
          'capability_sha256':PaperLibrary(settings,arm).fingerprint,'code_sha256':source_fingerprint(root),
          'python':platform.python_version(),'pdf_sha256':file_digest(root/'references/2609.40306v1.pdf'),
          'protocol_sha256':file_digest(root/'configs/dyna/paper_spec.json'),
          'claim':'PDF-grounded reconstruction; native qualification and outcome reproduction not implied'}
    atomic_json(out/'manifest.json',manifest);atomic_json(out/'run.json',info)
    global_log=Journal(out/'model_calls.jsonl');ledger=CallLedger(global_log,**config.get('call_budget',{}))
    planner=None
    if arm!='bare':
        if native:
            from .planner import PaperPlanner
            planner=PaperPlanner(config['planner'],ledger,settings,allow_api)
        else:
            from .fixture import FixturePlanner
            planner=FixturePlanner()
    info['planner_identity']='none' if planner is None else planner.identity
    atomic_json(out/'run.json',info);errors=0
    try:
        for case in cases:
            p=out/'episodes'/case.case_id;p.mkdir(parents=True)
            log=Journal(p/'events.jsonl');backend=None;engine=None;started=time.monotonic()
            atomic_json(p/'STARTED.json',{'case_id':case.case_id,'identity':case.identity})
            status='completed';result={};error=None
            try:
                maximum=suite_budget(case.suite) if native else config.get('fixture_steps',300)
                if native:
                    from .native import NativeBackend
                    backend=NativeBackend(case,p,{**config,'allow_native':True},settings)
                else:
                    from .fixture import FixtureBackend
                    backend=FixtureBackend(case.case_id,blocked=case.fixture=='blocked')
                atomic_json(p/'backend.json',backend.metadata)
                if hasattr(planner,'calls'):planner.calls=0
                engine=Engine(backend,planner,log,settings,arm,maximum,p)
                result=engine.run()
            except Exception as e:
                status='protocol_error' if isinstance(e,ValidationError) else 'infrastructure_error'
                error=type(e).__name__;result={'reason':str(e),'native_success':None}
                (p/'traceback.txt').write_text(traceback.format_exc())
                log.append('error',{'reason':str(e),'type':error});errors+=1
            finally:
                if backend is not None:
                    try:backend.close()
                    except Exception as e:
                        status='infrastructure_error';error=type(e).__name__;errors+=1
                        log.append('cleanup_error',{'reason':str(e)})
                metrics={k:0 for k in ('native_steps','planner_calls','vla_calls','refusals','substitutions')}
                if engine:
                    metrics.update(native_steps=engine.steps,planner_calls=engine.planner_calls,
                        vla_calls=engine.vla_calls,refusals=engine.refusals,substitutions=engine.substitutions)
                result={**metrics,**result,'case':plain(case),'identity':case.identity,'source':source,
                    'status':status,'native_success':result.get('native_success') if status=='completed' else None,
                    'wall_s':time.monotonic()-started,'simulated_seconds':metrics['native_steps']/settings.control_hz,
                    'interrupts':sum(r['status']=='failed' for r in engine.receipts) if engine else 0,
                    'error_type':error,'policy_rng_control':'not_exposed' if native else 'synthetic',
                    'contamination_flags':([status] if status!='completed' else []),
                    'attribution':None}
                h=log.append('episode_result',result);result['journal_tail_sha256']=h
                atomic_json(p/'result.json',result);log.close()
            if errors>=config.get('max_infrastructure_errors',1):
                atomic_json(out/'STOPPED.json',{'reason':'infrastructure_error_limit','case_id':case.case_id});break
    finally:global_log.close()
    summary=summarize(out);atomic_json(out/'summary.json',summary)
    from .report import write_report
    write_report(out/'report.html',summary)
    return summary


def summarize(path):
    info,manifest,cases,results=read_run(path)
    wins=sum(r['status']=='completed' and r['native_success'] is True for r in results.values())
    errors=sum(r['status']!='completed' for r in results.values())
    by_suite={}
    for suite in sorted({c.suite for c in cases}):
        cs=[c for c in cases if c.suite==suite]
        k=sum(results.get(c.case_id,{}).get('native_success') is True and
              results[c.case_id]['status']=='completed' for c in cs)
        by_suite[suite]={'planned':len(cs),'successes':k,'full_denominator_rate':k/len(cs),
                         'wilson95':wilson(k,len(cs))}
    return {'source':info['source'],'arm':info['mode'],'planned':len(cases),'started':len(results),
        'missing':len(cases)-len(results),'errors':errors,'successes':wins,
        'paper_primary_rate':wins/len(cases),'wilson95_full_denominator':wilson(wins,len(cases)),
        'complete_manifest':len(results)==len(cases),'benchmark':info['benchmark'],'by_suite':by_suite,
        'totals':{k:sum(r.get(k,0) or 0 for r in results.values()) for k in (
            'native_steps','planner_calls','actual_model_calls','vla_calls','wall_s','refusals','substitutions','fixed_retries',
            'fixed_replays','failure_replans','fast_decisions','recovery_insertions','safety_checks')},
        'claim':('SYNTHETIC CONTRACT TESTS ONLY — no physics or learned model.' if info['source']=='synthetic' else
                 'Local simulation with simulator-state geometry; not a sensor-only result or proven paper reproduction.'),
        'notes':['Infrastructure failures count against the full planned denominator.',
                 'An incomplete campaign is marked incomplete, not reported as a completed benchmark.',
                 'No source-paper scores are substituted for measured outcomes.'],
        'episodes':list(results.values())}


def compare(a,b,contrast='executor',draws=20000):
    ia,ma,ca,ra=read_run(a);ib,mb,cb,rb=read_run(b)
    for k in ('manifest_sha256','source','pdf_sha256','split'):
        if ia.get(k)!=ib.get(k):raise ValidationError('unmatched_'+k)
    for k in ('information_profile','checkpoint_sha256','geometry_overrides','settle_steps','record_video','call_budget'):
        if ia['config'].get(k)!=ib['config'].get(k):raise ValidationError('unmatched_config_'+k)
    if digest(ia['config'].get('settings',{}))!=digest(ib['config'].get('settings',{})):
        raise ValidationError('unmatched_settings')
    if contrast=='executor':
        for k in ('capability_sha256','code_sha256','planner_identity'):
            if ia.get(k)!=ib.get(k):raise ValidationError('executor_changes_'+k)
        if digest(ia['config'].get('planner'))!=digest(ib['config'].get('planner')):
            raise ValidationError('executor_changes_planner')
    elif contrast not in ('system','evolution','capability'):raise ValidationError('unknown_contrast')
    pairs=[];missing=[]
    for c in ca:
        if c.case_id not in ra or c.case_id not in rb:missing.append(c.case_id);continue
        x,y=ra[c.case_id],rb[c.case_id]
        if ia['source']=='native' and x['status']=='completed' and y['status']=='completed':
            ba=read_json(Path(a)/'episodes'/c.case_id/'backend.json')
            bb=read_json(Path(b)/'episodes'/c.case_id/'backend.json')
            for key in ('post_reset_state_sha256','bddl_sha256','mujoco_version','robosuite_version',
                        'OSC_output_max','override_hash','policy_checkpoint_sha256','policy_preset'):
                if ba.get(key)!=bb.get(key):raise ValidationError('native_pair_mismatch:'+c.case_id+':'+key)
        xa=int(x['status']=='completed' and x['native_success'] is True)
        yb=int(y['status']=='completed' and y['native_success'] is True)
        pairs.append({'task_cluster':f'{c.suite}/{c.task_id}','case_id':c.case_id,
                      'a':xa,'b':yb,'delta':yb-xa})
    wins=sum(p['delta']==1 for p in pairs);loss=sum(p['delta']==-1 for p in pairs)
    return {'source':ia['source'],'contrast':contrast,'complete':not missing,'planned':len(ca),
            'paired_started':len(pairs),'missing':missing,'wins_b_only':wins,'wins_a_only':loss,
            'delta_pp':100*(wins-loss)/len(ca),'exact_discordant_p':mcnemar_exact(wins,loss) if not missing else None,
            'cell_bootstrap95_delta':cluster_bootstrap(pairs,draws,20260926) if not missing else [None,None],
            'infrastructure_counted_as_failure':True,'pairs':pairs,
            'claim':'Local measurements only; no guarantee of matching paper checkpoints, skills, or outcomes.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--config',required=True);r.add_argument('--manifest',required=True)
    r.add_argument('--output',required=True);r.add_argument('--allow-native',action='store_true');r.add_argument('--allow-api',action='store_true')
    r=sub.add_parser('audit');r.add_argument('--spec',default='configs/dyna/paper_spec.json')
    r=sub.add_parser('summary');r.add_argument('path')
    r=sub.add_parser('compare');r.add_argument('a');r.add_argument('b');r.add_argument('--contrast',default='executor')
    r.add_argument('--output');r.add_argument('--draws',type=int,default=20000)
    a=p.parse_args(argv)
    try:
        if a.command=='run':data=run(read_json(a.config),a.manifest,a.output,a.allow_native,a.allow_api)
        elif a.command=='audit':
            spec=read_json(a.spec);data={'source':spec['source'],'implemented':spec['implemented'],
                                       'remaining_qualification':spec['remaining_qualification'],
                                       'paper_results_reproduced':False}
        elif a.command=='summary':data=summarize(a.path)
        else:
            data=compare(a.a,a.b,a.contrast,a.draws)
            if a.output:atomic_json(Path(a.output),data)
        print(__import__('json').dumps(plain({k:v for k,v in data.items() if k!='episodes'}),indent=2));return 0
    except (PRLError,OSError,ValueError,KeyError) as e:
        print(f'{type(e).__name__}: {e}',file=sys.stderr);return 2
