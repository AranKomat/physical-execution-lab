#!/usr/bin/env python3
"""Check executed mechanisms, not just treatment configuration names."""
from pathlib import Path
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.evaluation import read_run
from prl.journal import Journal
from prl.util import atomic_json
from prl.dyna.capabilities import CONTACT,RECOVERY


def audit(path):
    info,m,cases,rows=read_run(path);arm=info['mode'];errors=[];stores=0
    disabled=set(CONTACT if arm in ('no_contact','no_groups') else ())|set(RECOVERY if arm in ('no_recovery','no_groups') else ())
    if arm=='no_vla':disabled.add('vla_act')
    for case in cases:
        p=Path(path)/'episodes'/case.case_id/'events.jsonl'
        if not p.exists():errors.append('missing:'+case.case_id);continue
        events=Journal.verify(p);stores+=1
        for e in events:
            kind,d=e['kind'],e['data']
            if kind=='grounded_command' and d['capability'] in disabled:
                errors.append('removed_capability_executed:'+case.case_id+':'+d['capability'])
            if arm in ('A2static','A2seq') and kind in ('capability_substitution','recovery_insertion'):
                errors.append('forbidden_dynamic_event:'+case.case_id)
            if arm in ('A2static','A2seq') and kind=='slow_brain_completed' and d['reason']=='failure':
                errors.append('failure_replan_in_nominal_arm:'+case.case_id)
        calls=sum(e['kind']=='slow_brain_completed' for e in events)
        if arm=='A2seq' and rows.get(case.case_id,{}).get('status')=='completed' and calls!=1:
            errors.append('frozen_sequence_planner_call_count:'+case.case_id)
    return {'arm':arm,'trace_count':stores,'planned':len(cases),'valid':not errors,'errors':errors,
            'source':info['source'],'note':'Passing checks does not establish paper performance or native physical correctness.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--output');a=p.parse_args()
    result=audit(a.run)
    if a.output:atomic_json(Path(a.output),result)
    print(__import__('json').dumps(result,indent=2));raise SystemExit(0 if result['valid'] else 1)
