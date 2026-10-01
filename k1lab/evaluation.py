"""Full-denominator comparisons. Synthetic runs can never be labeled benchmark results."""
from __future__ import annotations
import math
import random
import statistics
from .errors import ContractError
from .util import digest


def wilson(w,n,z=1.959963984540054):
    if n<=0:return [0.0,1.0]
    p=w/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;r=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [0.0 if w == 0 else max(0.0,c-r), 1.0 if w == n else min(1.0,c+r)]


def exact_discordant(wins,losses):
    n=wins+losses
    if not n:return 1.0
    return min(1.0,2*sum(math.comb(n,k) for k in range(min(wins,losses)+1))/(2**n))


def full_rows(cases,rows):
    mapping={}
    expected={x['id'] for x in cases}
    for row in rows:
        if row['case_id'] not in expected or row['case_id'] in mapping:raise ContractError('extra/duplicate outcome row')
        if type(row.get('native_success')) is not bool:raise ContractError('native_success must be boolean')
        mapping[row['case_id']]=row
    result=[]
    for c in cases:
        row=mapping.get(c['id'])
        if row is None:row={'case_id':c['id'],'native_success':False,'termination':'missing_result',
                           'native_steps':0,'elapsed_seconds':None,'llm_calls':0,'state_sha256':c['state_sha256']}
        if row.get('state_sha256')!=c['state_sha256']:raise ContractError('outcome/state mismatch')
        if not 0<=row.get('native_steps',0)<=c['horizon']:raise ContractError('invalid native-step accounting')
        from .manifests import base_task_key
        result.append({**row,'horizon':c['horizon'],'task_key':base_task_key(c['suite'],c['task_id'])})
    return result


def summarize(rows):
    n=len(rows);wins=sum(x['native_success'] for x in rows)
    all_steps=sum(x['native_steps'] for x in rows)
    # Failures are censored at the declared horizon for a reproducible efficiency diagnostic.
    penalized=sum(x['native_steps'] if x['native_success'] else x['horizon'] for x in rows)
    durations=[x['elapsed_seconds'] for x in rows if x.get('elapsed_seconds') is not None]
    return {'episodes':n,'successes':wins,'success_rate':wins/n if n else None,
        'wilson_95':wilson(wins,n),'measured_total_steps':all_steps,
        'failure_penalized_steps_per_case':penalized/n if n else None,
        'measured_steps_per_success':all_steps/wins if wins else None,
        'success_only_median_steps':statistics.median([x['native_steps'] for x in rows if x['native_success']]) if wins else None,
        'all_attempt_mean_wall_s':statistics.mean(durations) if durations else None,
        'wall_measurement_coverage':len(durations),'llm_calls':sum(x.get('llm_calls',0) for x in rows),
        'policy_calls':sum(x.get('policy_calls',0) for x in rows),
        'provider_reported_input_tokens':sum(x.get('provider_reported_input_tokens',0) for x in rows),
        'provider_reported_output_tokens':sum(x.get('provider_reported_output_tokens',0) for x in rows),
        'model_calls_with_known_usage':sum(x.get('model_calls_with_known_usage',0) for x in rows),
        'measured_model_wait_s':sum(x.get('model_wait_s',0) for x in rows),
        'measured_policy_wait_s':sum(x.get('policy_wait_s',0) for x in rows),
        'outcome_row_coverage':sum(x['termination']!='missing_result' for x in rows),
        'missing':sum(x['termination']=='missing_result' for x in rows),
        'infrastructure_failures':sum(x['termination']=='infrastructure_failure' for x in rows),
        'success_by_budget_fraction':[{ 'fraction':f,'rate':sum(x['native_success'] and x['native_steps']<=x['horizon']*f for x in rows)/n if n else 0}
                                     for f in (0.25,0.5,0.75,1.0)]}


def compare(cases,left,right,*,bootstrap=2000,seed=20261001):
    if not cases or bootstrap<1:raise ContractError('nonempty cases and positive bootstrap count required')
    a=full_rows(cases,left);b=full_rows(cases,right)
    signatures={x.get('comparison_signature') for x in a+b if x['termination']!='missing_result'}
    if len(signatures)>1:raise ContractError('unmatched model/policy/sensing/budget protocol; do not report causal harness gain')
    known_models={name for x in a+b for name in x.get('resolved_models',[]) if name!='unreported'}
    if len(known_models)>1:raise ContractError('reported provider model revisions differ')
    domains={x.get('domain') for x in a+b if x['termination']!='missing_result'}
    if len(domains)>1:raise ContractError('synthetic and native outcomes cannot be pooled')
    wins=sum(not x['native_success'] and y['native_success'] for x,y in zip(a,b))
    losses=sum(x['native_success'] and not y['native_success'] for x,y in zip(a,b))
    groups={}
    for x,y in zip(a,b):groups.setdefault(x['task_key'],[]).append(int(y['native_success'])-int(x['native_success']))
    rng=random.Random(seed);ks=list(groups);samples=[]
    for _ in range(bootstrap):
        selected=[groups[rng.choice(ks)] for _ in ks]
        samples.append(sum(sum(g) for g in selected)/sum(len(g) for g in selected))
    samples.sort();lower=samples[int(0.025*(len(samples)-1))];upper=samples[int(0.975*(len(samples)-1))]
    return {'left':summarize(a),'right':summarize(b),'right_only_wins':wins,'left_only_wins':losses,
            'difference_pp':100*(wins-losses)/len(a),'cell_bootstrap_95_pp':[100*lower,100*upper],
            'exact_discordant_p':exact_discordant(wins,losses),'task_clusters':len(groups),
            'domain':next(iter(domains),None),'claim_scope':'synthetic software test only' if domains=={'synthetic'} else
            'paired reported outcomes; inspect source freeze, protocol and holdout before claiming generalization'}
