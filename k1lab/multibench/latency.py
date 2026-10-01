"""Measured replay inference timing, not invented control throughput.

Independent-observation mode resets temporal memory between samples and labels
that distribution shift. End-to-end rollout timing is the primary comparison.
"""
from __future__ import annotations
import time
import numpy as np
from k1lab.errors import ContractError
from k1lab.util import digest,atomic_json


def benchmark(policy,observations,*,warmup=3,repeats=30,clock=time.perf_counter):
    if not observations or warmup<0 or repeats<1:raise ContractError('nonempty replay data and positive repeats')
    timings=[];returns=[];hashes=[o.stamp for o in observations]
    for i in range(warmup+repeats):
        obs=observations[i%len(observations)]
        policy.reset();policy.synchronize()
        start=clock();policy.observe(obs);p=policy.propose(obs);policy.synchronize();elapsed=clock()-start
        p.validate(obs,policy.identity)
        if i>=warmup:timings.append(elapsed);returns.append(len(p.actions))
        policy.invalidate('microbenchmark_discards_predictions_no_physics')
    a=np.asarray(timings)
    prefix=np.minimum(returns,policy.identity.execute_steps)
    result={'schema':'multibench.latency.v1','policy_identity':policy.identity.identity,
            'policy':policy.identity.name,'warmup':warmup,'samples':repeats,
            'measurement':'blocking end-to-end policy transport+preprocessing+inference+postprocessing',
            'temporal_mode':'reset temporal memory per independent observation; not steady-state rollout',
            'observation_corpus_sha256':digest(hashes),'p50_ms':float(np.median(a)*1000),
            'p90_ms':float(np.percentile(a,90)*1000),'p99_ms':float(np.percentile(a,99)*1000),
            'mean_ms':float(a.mean()*1000),'nominal_ms_per_exposed_action':float(np.mean(a*1000/prefix)),
            'native_execution_measured':False,'prefix_lengths':prefix.tolist(),
            'latency_seconds':timings,'memory':policy.memory(),
            'cold_load_seconds':getattr(policy,'server_info',{}).get('load_seconds')}
    return result
