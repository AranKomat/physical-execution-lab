"""Auditable unbundled/bundled script check; never reports K1/model performance."""
from __future__ import annotations
from pathlib import Path
from .fixture import FixturePort
from .engine import ExecutionEngine
from .contracts import Limits
from .journal import Journal
from .util import digest,atomic_json
from .report import render
from .evaluation import compare


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('use a fresh synthetic output directory')
    output.mkdir(parents=True)
    cases=[];arms={n:[] for n in ('scripted_unbundled','scripted_bundled')}
    for i,fault in enumerate(('none','blocked','native_stop','lost_feature')):
        c={'id':f'fixture_{i}','suite':'software_fixture','task_id':i,'horizon':220,
           'state_sha256':digest(fault)};cases.append(c)
        for name in arms:
            root=output/name/c['id'];root.mkdir(parents=True)
            port=FixturePort(horizon=220,blocked=fault=='blocked',terminal_at=7 if fault=='native_stop' else None,
                             lost_at=5 if fault=='lost_feature' else None)
            with Journal(root/'events.jsonl') as journal:
                engine=ExecutionEngine(port,Limits(),journal)
                seq=[{'kind':'pose','target_xyz_world_m':[0.1,0.,0.5],'target_quaternion_xyzw':[0,0,0,1]},
                     {'kind':'gripper','gripper':0.,'settle_steps':10},
                     {'kind':'pose','target_xyz_world_m':[0.1,0.,0.52],'target_quaternion_xyzw':[0,0,0,1],'profile':'approach'}]
                groups=[[s] for s in seq] if name=='scripted_unbundled' else [seq]
                decisions=0;receipts=[]
                for j,segments in enumerate(groups):
                    decisions+=1
                    result=engine.execute({'frame_id':port.frame,'arm':'arm','command_id':f'cmd{j}',
                            'segments':segments,'max_native_steps':160,'watch_points':['P1'] if fault=='lost_feature' else []})
                    receipts.append(result)
                    if result['stop_reason']!='completed':break
                # This artificial goal is deliberately NOT LIBERO native success.
                success=bool(port.success() or (not port.blocked and port.xyz[0]>=.099 and port.xyz[2]>=.516 and fault!='lost_feature'))
                row={'case_id':c['id'],'state_sha256':c['state_sha256'],'domain':'synthetic','native_success':success,
                     'native_steps':port.frame,'elapsed_seconds':None,'llm_calls':0,'script_decisions':decisions,
                     'policy_calls':0,'termination':'synthetic_completed' if success else 'synthetic_failed',
                     'comparison_signature':digest({'fixture':'v1','limits':Limits().as_dict()}),
                     'note':'authored scripts and kinematics; no K1, LLM, VLA or real physics executed'}
                atomic_json(root/'result.json',row);atomic_json(root/'receipts.json',receipts);arms[name].append(row)
    atomic_json(output/'cases.json',cases);atomic_json(output/'outcomes.json',arms)
    atomic_json(output/'comparison.json',compare(cases,*arms.values()))
    render(output/'report.html',cases,arms,'synthetic')
    return {'report':str(output/'report.html'),'cases':len(cases),'episodes':sum(map(len,arms.values())),
            'status':'synthetic_software_test_only'}
