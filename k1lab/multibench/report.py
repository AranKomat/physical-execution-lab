"""Full-denominator evaluation, task-weighted aggregates and descriptive Pareto data."""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import csv
import html
import json
import numpy as np
from k1lab.errors import ContractError
from k1lab.util import atomic_json,digest


def wilson(k,n):
    if n==0:return None
    z=1.959963984540054;p=k/n;d=1+z*z/n
    m=(p+z*z/(2*n))/d;r=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(m-r),float(m+r)]


def aggregate(cases,results,condition):
    ids={c['case_id'] for c in cases};rows={}
    for r in results:
        if r['condition']!=condition:continue
        key=r['case_id']
        if key not in ids or key in rows:raise ContractError('unknown or duplicate result case')
        rows[key]=r
    n=len(cases);k=sum(r.get('success') is True for r in rows.values())
    statuses=Counter(r.get('status','unspecified') for r in rows.values())
    terminations=Counter(r.get('termination') or 'unspecified' for r in rows.values())
    native_failures=sum(r.get('status')=='native_completed' and r.get('success') is False
                        for r in rows.values())
    budget_stops=sum(r.get('status')=='budget_exhausted' or
                     (r.get('status')=='incomplete' and
                      r.get('termination') in ('wall_limit','review_budget','native_step_budget'))
                     for r in rows.values())
    by_task=defaultdict(list)
    for c in cases:by_task[c['task']].append(bool(rows.get(c['case_id'],{}).get('success',False)))
    scores=[r['native_score'] for r in rows.values() if r.get('native_score') is not None]
    elapsed=[r['elapsed_s'] for r in rows.values()]
    steps=sum(r['native_steps'] for r in rows.values())
    category=defaultdict(list)
    for c in cases:category[c.get('category','unmapped')].append(c)
    return {'condition':condition,'scheduled':n,'results_present':len(rows),'missing':n-len(rows),
            'successes':k,'success_rate_full_denominator':k/n if n else None,'wilson95':wilson(k,n),
            'status_counts':dict(statuses),'termination_counts':dict(terminations),
            'native_failures':native_failures,
            'contract_errors':statuses['infrastructure_or_contract_error'],
            'budget_stops':budget_stops,
            'task_weighted_success':float(np.mean([np.mean(x) for x in by_task.values()])) if by_task else None,
            'score_mean_available_only':float(np.mean(scores)) if scores else None,'score_coverage':len(scores),
            'mean_episode_wall_s_available':float(np.mean(elapsed)) if elapsed else None,
            'mean_control_steps_available':steps/len(rows) if rows else None,
            'total_steps_per_success':steps/k if k else None,
            'total_control_steps':steps,'review_calls':sum(r['metrics']['review_calls'] for r in rows.values()),
            'policy_calls':sum(r['metrics']['policy_calls'] for r in rows.values()),
            'token_totals':{field:sum(r['usage'][field] for r in rows.values())
                if rows and all(type(r.get('usage',{}).get(field)) is int for r in rows.values()) else None
                for field in ('input_tokens','cached_input_tokens','output_tokens','reasoning_tokens')},
            'category_success':{cat:sum(rows.get(c['case_id'],{}).get('success') is True for c in cc)/len(cc) for cat,cc in category.items()},
            'interpretation':'Missing runs remain unsuccessful in success denominator; wall/score coverage is shown separately.'}


def paired(cases,results,a,b,seed=31):
    index={}
    for r in results:
        key=(r['condition'],r['case_id'])
        if key in index:raise ContractError('duplicate result')
        index[key]=r
    deltas=[];new=lost=0;groups=defaultdict(list);warnings=[]
    if not cases:raise ContractError('empty paired case list')
    for c in cases:
        x=index.get((a,c['case_id']));y=index.get((b,c['case_id']))
        if not x or not y:warnings.append('incomplete paired outcomes; missing runs are unsuccessful, not verified task failures')
        if x and y:
            for field in ('case_sha256','environment_contract_sha256','runtime_fingerprint','policy_runtime_fingerprint'):
                if x.get(field)!=y.get(field):warnings.append(f"{c['case_id']}: unequal {field}")
            if x.get('policy_identity')!=y.get('policy_identity'):
                warnings.append('motor policy differs; system comparison, not a harness-only ablation')
            if x.get('planner_config') and y.get('planner_config') and x['planner_config']!=y['planner_config']:
                warnings.append('planner model/tier/config differs')
            for field in ('served_models','served_tiers'):
                if x.get('usage',{}).get(field) and y.get('usage',{}).get(field) and x['usage'][field]!=y['usage'][field]:
                    warnings.append('actual provider '+field+' differ')
        d=int(bool(y and y.get('success')))-int(bool(x and x.get('success')))
        new+=d==1;lost+=d==-1;deltas.append(d);groups[c.get('task_group',c['task'])].append(d)
    # Task-cluster bootstrap respects related layouts/seeds; no independence claim per reset.
    g=list(groups.values());rng=np.random.default_rng(seed);boot=[]
    if g:
        for _ in range(2000):
            sample=[g[i] for i in rng.integers(0,len(g),len(g))]
            boot.append(float(np.mean([z for part in sample for z in part])))
    return {'baseline':a,'candidate':b,'paired_scheduled':len(cases),'gained':new,'lost':lost,
            'delta_success':float(np.mean(deltas)) if deltas else None,
            'task_cluster_bootstrap95':np.quantile(boot,[.025,.975]).tolist() if len(g)>1 else None,
            'matched_contract':not warnings,'warnings':sorted(set(warnings)),
            'note':'Missing outcomes count unsuccessful; preregistered task group is bootstrap unit.'}


def render(cases,results,output,conditions=None):
    root=Path(output);root.mkdir(parents=True,exist_ok=True)
    kinds={r.get('evidence_kind','unspecified') for r in results}
    if 'synthetic' in kinds and len(kinds)>1:raise ContractError('cannot combine synthetic and native evidence')
    conditions=sorted(set(conditions or [r['condition'] for r in results]));agg=[aggregate(cases,results,c) for c in conditions]
    synthetic=any(r.get('evidence_kind')=='synthetic' for r in results)
    label='SYNTHETIC CPU CONTRACT TESTS — NOT ROBOT BENCHMARK RESULTS' if synthetic else 'Measured run artifacts — inspect qualification and protocol before claims'
    doc=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Physical Execution Lab</title>',
         '<style>body{font:16px system-ui;margin:40px auto;max-width:1200px;padding:0 20px;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}code{white-space:pre-wrap}</style>',
         '<h1>Physical Execution Lab</h1><h2>'+html.escape(label)+'</h2>',
         '<p>Conditions include failures and missing runs. No historical paper score is counted as an experiment here. Token fields remain blank when unmeasured.</p>',
         '<table><tr><th>Condition</th><th>Success / scheduled</th><th>Missing</th><th>Terminal statuses</th><th>Mean wall s</th><th>Review calls</th><th>Policy calls</th></tr>']
    for r in agg:
        doc.append('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in (
            r['condition'],f"{r['successes']}/{r['scheduled']}",r['missing'],
            ', '.join(f'{key}: {value}' for key,value in sorted(r['status_counts'].items())),
            round(r['mean_episode_wall_s_available'],3) if r['mean_episode_wall_s_available'] is not None else '—',r['review_calls'],r['policy_calls']))+'</tr>')
    doc+=['</table><h2>Interpretation</h2><p>Model-only vs hybrid tests the additional supervisor. Every-chunk vs sparse tests invocation scheduling with the same motor and language model. Native and synthetic rows must never be combined.</p></html>']
    (root/'report.html').write_text('\n'.join(doc));atomic_json(root/'aggregates.json',agg)
    atomic_json(root/'outcomes.json',results)
    fields=['condition','scheduled','successes','missing','native_failures','contract_errors',
            'budget_stops','success_rate_full_denominator','mean_episode_wall_s_available',
            'total_steps_per_success','review_calls','policy_calls']
    with (root/'aggregates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(agg)
    return agg
