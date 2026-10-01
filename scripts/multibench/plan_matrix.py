#!/usr/bin/env python3
"""Build a deterministic schedule; no inference, simulator launch, or job submission."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json,load_json,digest
from k1lab.multibench.manifest import check,resolved_config,seal
from k1lab.errors import ContractError


def direct_budget_feasibility(case, config):
    """Upper bound only: early success or shorter decisions remain possible."""
    if config['mode'] not in ('direct_dense', 'direct_sparse'):
        return None
    steps = config.get('max_decision_steps', 15)
    reviews = config.get('max_reviews', 180)
    requests = config['model']['max_requests']
    horizon = case.get('horizon')
    if any(type(x) is not int or x < 1 for x in (steps, reviews, requests, horizon)):
        raise ContractError('direct schedule needs positive integer horizon and decision budgets')
    limit = min(reviews, requests)
    return {
        'native_horizon': horizon,
        'maximum_actions_per_decision': steps,
        'maximum_decisions': limit,
        'maximum_native_actions_from_call_budget': limit * steps,
        'minimum_decisions_for_full_horizon': (horizon + steps - 1) // steps,
        'full_horizon_possible_under_call_budget': limit * steps >= horizon,
        'scope': 'Upper bound only; early success possible. Ignores wall, cost, token and shortened-action limits.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True)
    p.add_argument('--configs',nargs='+',required=True);p.add_argument('--partition',choices=['dev','test'],required=True)
    p.add_argument('--per-task',type=int);p.add_argument('--output',required=True);a=p.parse_args()
    m=check(load_json(a.manifest));cfgs=[resolved_config(load_json(f)) for f in a.configs]
    selected=[];counts={}
    if a.per_task is not None and a.per_task<1:raise ContractError('positive per-task cap')
    for c in sorted(m['cases'],key=lambda c:c['case_id']):
        if c['partition']!=a.partition:continue
        n=counts.get(c['task_group'],0)
        if a.per_task is not None and n>=a.per_task:continue
        selected.append(c);counts[c['task_group']]=n+1
    if not selected:raise ContractError('empty schedule')
    jobs=[];calls=tokens=0
    for c in selected:
        for f,cfg in zip(a.configs,cfgs):
            if cfg['benchmark']!=c['benchmark']:raise ContractError('cross-benchmark config in matrix')
            job={'case_id':c['case_id'],'config_path':str(Path(f).resolve()),'config_sha256':digest(cfg),'condition':cfg['name']}
            feasibility=direct_budget_feasibility(c,cfg)
            if feasibility is not None:job['direct_budget_feasibility']=feasibility
            jobs.append(job)
            if cfg['mode']!='motor_only':
                limit=min(cfg['max_reviews'],cfg['model']['max_requests']);calls+=limit
                tokens+=min(limit*cfg['model']['max_output_tokens'],cfg['model']['max_total_output_tokens'])
    atomic_json(a.output,seal({'schema':'multibench.matrix.v1','manifest_sha256':m['sha256'],'partition':a.partition,
       'selection_rule':'First lexically sorted cases per task group; no outcome selection','jobs':jobs,
       'maximum_model_requests':calls,'maximum_output_token_reservations':tokens,
       'not_a_dollar_budget':True,'status':'PLAN ONLY; requires operator review and owned GPU workers'}),exclusive=True)
