#!/usr/bin/env python3
"""Audit a terminal RoboDojo episode offline; never supply evaluator data to control."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.errors import ContractError
from k1lab.journal import verify
from k1lab.util import atomic_json,load_json


def audit(root):
    root=Path(root)
    result=load_json(root/'controller/result.json')
    if result['status']!='native_completed':
        raise ContractError('terminal native episode required; no live evaluator inspection')
    outcome=load_json(root/'native/evaluation_outcome.json')
    native=load_json(root/'native/native_evaluation.json')
    if outcome['complete'] is not True:
        raise ContractError('terminal native episode required; no live evaluator inspection')
    for key,left,right in (('success',result['success'],outcome['native_success']),
                           ('score',result['native_score'],outcome['native_score']),
                           ('steps',result['native_steps'],outcome['native_control_steps']),
                           ('case',result['case_id'],outcome['evaluation_case']['case_id'])):
        if left!=right:raise ContractError('controller/evaluator mismatch: '+key)
    counts=native['condition_group_counts']
    if native.get('registered') is not True or not any(
        x>0 for key in ('check_list','final_check_list') for x in counts.get(key,[])
    ):raise ContractError('native completion registration is vacuous')
    journal=root/'controller/events.jsonl';verified=verify(journal)
    import json
    rows=[json.loads(line) for line in journal.read_text().splitlines()]
    acks=[r['data']['step'] for r in rows if r['event']=='control_ack']
    if acks!=list(range(1,result['native_steps']+1)):
        raise ContractError('ACKs not sequential/exactly once')
    proposals=[r['data'] for r in rows if r['event']=='policy_proposal']
    if len(proposals)!=result['metrics']['policy_calls']:
        raise ContractError('policy proposal count mismatch')
    seeds={p['diagnostics'].get('policy_rng_seed') for p in proposals}
    expected=outcome['evaluation_case']['policy_rng_seed']
    if proposals and seeds!={expected}:raise ContractError('policy seed differs from source case')
    if proposals and sum(len(p['actions']) for p in proposals)!= (
        result['metrics']['motor_steps']+result['metrics']['discarded_policy_actions']
    ):raise ContractError('proposal disposition count mismatch')
    clips=[p['diagnostics'] for p in proposals]
    return verified|{'sequential_acks':len(acks),'seeded_proposals':len(proposals),
        'policy_rng_seed':expected if proposals else None,
        'source_declared_policy_rng_seed':expected,'native_completion_nonvacuous':True,
        'controller_evaluator_agree':True,'success':result['success'],
        'raw_gripper_min':min((p['raw_gripper_min'] for p in clips),default=None),
        'raw_gripper_max':max((p['raw_gripper_max'] for p in clips),default=None),
        'max_gripper_clip_delta':max((p['max_gripper_clip_delta'] for p in clips),default=None),
        'scope':'offline bookkeeping/provenance audit, not automatic sensor legality or safety proof'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('episode');p.add_argument('--output',required=True);a=p.parse_args()
    result=audit(a.episode);atomic_json(a.output,result,exclusive=True);print(result)


if __name__=='__main__':main()
