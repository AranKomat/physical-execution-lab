from __future__ import annotations
import math
import random
from pathlib import Path
from collections import Counter,defaultdict
from .errors import ValidationError
from .journal import Journal
from .manifests import load_manifest
from .util import read_json,digest


def wilson(k,n,z=1.959963984540054):
    if not 0<=k<=n: raise ValidationError('invalid_binomial_counts')
    if not n: return [None,None]
    p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return [max(0.,center-half),min(1.,center+half)]


def mcnemar_exact(wins,losses):
    n=wins+losses
    if not n:return 1.0
    k=min(wins,losses)
    logs=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)-n*math.log(2) for i in range(k+1)]
    m=max(logs)
    return min(1.,2*math.exp(m)*sum(math.exp(x-m) for x in logs))


def cluster_bootstrap(pairs,draws=2000,seed=0):
    """Paired bootstrap resampling task clusters, not pretending seeds are tasks."""
    if not pairs:return [None,None]
    groups=defaultdict(list)
    for row in pairs: groups[row['task_cluster']].append(row['delta'])
    values=list(groups.values()); rng=random.Random(seed); dist=[]
    if len(values)==1:
        # No credible across-task uncertainty from a single task.
        return [None,None]
    for _ in range(draws):
        sample=[x for _ in values for x in rng.choice(values)]
        dist.append(sum(sample)/len(sample))
    dist.sort()
    return [dist[int(.025*(draws-1))],dist[int(.975*(draws-1))]]


def read_run(path):
    path=Path(path)
    info=read_json(path/'run.json')
    manifest,cases=load_manifest(path/'manifest.json')
    if manifest['sha256']!=info['manifest_sha256']: raise ValidationError('run_manifest_mismatch')
    results={}
    for c in cases:
        p=path/'episodes'/c.case_id/'result.json'
        if not p.exists():continue
        r=read_json(p)
        if r['identity']!=c.identity or r['source']!=info['source']:
            raise ValidationError('result_identity_or_source_mismatch')
        rows=Journal.verify(p.parent/'events.jsonl')
        if not rows or rows[-1]['hash']!=r['journal_tail_sha256']:
            raise ValidationError('result_journal_mismatch')
        event=rows[-1]
        if event['kind']!='episode_result': raise ValidationError('missing_final_result_event')
        if digest(event['data'])!=digest({k:v for k,v in r.items() if k!='journal_tail_sha256'}):
            raise ValidationError('result_modified_after_journal')
        if r['status']=='completed' and not isinstance(r['native_success'],bool):
            raise ValidationError('completed_episode_needs_boolean_native_verdict')
        results[c.case_id]=r
    return info,manifest,cases,results


def summarize_run(path):
    info,manifest,cases,results=read_run(path)
    completed=[r for r in results.values() if r['status']=='completed']
    wins=sum(r['native_success'] is True for r in completed)
    by_suite={}
    for suite in sorted({c.suite for c in cases}):
        planned=[c for c in cases if c.suite==suite]
        rs=[results[c.case_id] for c in planned if c.case_id in results and results[c.case_id]['status']=='completed']
        k=sum(r['native_success'] is True for r in rs)
        by_suite[suite]={'planned':len(planned),'completed':len(rs),'successes':k,
                         'success_rate_completed':k/len(rs) if rs else None,
                         'wilson95_descriptive':wilson(k,len(rs))}
    return {'source':info['source'],'mode':info['mode'],'benchmark':info['benchmark'],
        'claim':('SYNTHETIC CONTRACT TESTS ONLY. These are not robotics benchmark scores.'
                 if info['source']=='synthetic' else
                 'Local native simulation results; not a DynaHarness reproduction without protocol parity.'),
        'planned':len(cases),'started':len(results),'completed':len(completed),'successes':wins,
        'missing':len(cases)-len(results),'infrastructure_or_protocol_errors':len(results)-len(completed),
        'fully_completed':len(completed)==len(cases),
        'success_rate_completed':wins/len(completed) if completed else None,
        'success_lower_bound_planned':wins/len(cases),
        'wilson95_descriptive':wilson(wins,len(completed)),
        'status_counts':dict(Counter(r['status'] for r in results.values())),
        'reason_counts':dict(Counter(r['reason'] for r in results.values())),
        'totals':{k:sum(r[k] for r in results.values()) for k in
                  ('native_steps','simulated_seconds','planner_calls','vla_calls','wall_s','refusals','interrupts','substitutions')},
        'by_suite':by_suite,'manifest_sha256':manifest['sha256'],
        'notes':['Missing, infrastructure/protocol errors and campaign budget exhaustion are reported, never silently removed.',
                 'Wilson intervals describe case success; task-cluster uncertainty is in paired comparisons.',
                 'Wall time includes provider/simulator overhead and is NOT physical execution time.'],
        'episodes':list(results.values())}


def compare_runs(a,b,contrast='governor'):
    ia,ma,ca,ra=read_run(a); ib,mb,cb,rb=read_run(b)
    for key in ('source','manifest_sha256','split'):
        if ia[key]!=ib[key]:raise ValidationError(f'unmatched_comparison:{key}')
    if contrast not in ('governor','system','perception','evolution'):
        raise ValidationError('unknown_contrast')
    common=('backend','max_steps','max_wall_s','max_decisions','information_profile',
            'checkpoint_id','checkpoint_sha256','control_hz')
    for key in common:
        if ia['config'].get(key)!=ib['config'].get(key):
            raise ValidationError(f'unmatched_config:{key}')
    if contrast=='governor':
        for key in ('planner_identity','capability_sha256','code_sha256'):
            if ia[key]!=ib[key]:raise ValidationError(f'governor_contrast_changes:{key}')
        # Same planner configuration, not just same model name.
        if digest(ia['config'].get('planner'))!=digest(ib['config'].get('planner')):
            raise ValidationError('governor_contrast_changes_planner_settings')
    pairs=[]; missing=[]
    for c in ca:
        x,y=ra.get(c.case_id),rb.get(c.case_id)
        if x is None or y is None or x['status']!='completed' or y['status']!='completed':
            missing.append(c.case_id);continue
        pairs.append({'case_id':c.case_id,'task_cluster':f'{c.suite}/{c.task_id}',
                      'a':int(x['native_success']),'b':int(y['native_success']),
                      'delta':int(y['native_success'])-int(x['native_success']),
                      'wall_delta_s':y['wall_s']-x['wall_s'],
                      'step_delta':y['native_steps']-x['native_steps']})
    wins=sum(r['delta']==1 for r in pairs); losses=sum(r['delta']==-1 for r in pairs)
    return {'contrast':contrast,'source':ia['source'],'a_mode':ia['mode'],'b_mode':ib['mode'],
            'planned_pairs':len(ca),'complete_pairs':len(pairs),'missing_pairs':missing,
            'complete':not missing,'wins_b_only':wins,'wins_a_only':losses,
            'same_success':sum(r['a']==1 and r['b']==1 for r in pairs),
            'same_failure':sum(r['a']==0 and r['b']==0 for r in pairs),
            'success_delta_pp':100*sum(r['delta'] for r in pairs)/len(pairs) if pairs else None,
            'mcnemar_exact_p_descriptive':mcnemar_exact(wins,losses) if pairs else None,
            'task_cluster_bootstrap95_delta':cluster_bootstrap(pairs),
            'pairs':pairs,'warning':('SYNTHETIC ONLY: not a learned-policy performance comparison.'
                if ia['source']=='synthetic' else
                'Independent implementation. Paired environments do not imply seeded VLA sampling; inspect backend metadata.')}
