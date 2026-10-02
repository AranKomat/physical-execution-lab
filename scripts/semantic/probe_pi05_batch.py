#!/usr/bin/env python3
"""Bounded retained-input GPU check; no simulator actions or model downloads."""
import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'external/GPT-as-Policy')]
from k1lab.util import atomic_json, file_sha
from semantic_lab.pi05_batch import Pi05Batch


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    import jax
    from openpi.models.model import Observation
    from openpi.policies.policy_config import create_trained_policy
    from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract, checkpoint_identity
    provider = json.loads((ROOT/'configs/local/pi05-exact-bound-001/provider.json').read_text())
    checkpoint = Path(provider['checkpoint_path'])
    cfg,_ = data_contract(checkpoint)
    policy = create_trained_policy(cfg,checkpoint)
    print('Loaded source checkpoint; starting retained-input batch check',flush=True)
    with np.load(a.request,allow_pickle=False) as data:
        raws = [dict(state=data['states'][i].copy(),prompt=str(data['prompts'][i]),images={
            name:np.transpose(data[name][i],(2,0,1)).copy()
            for name in ('cam_high','cam_left_wrist','cam_right_wrist')}) for i in range(len(data['states']))]
    if not raws: raise ValueError('empty retained request')
    records = []
    batch = Pi05Batch(policy,Observation)
    for size in (1,2,10):
        values = [raws[i%len(raws)] for i in range(size)]
        ids = [f'capacity-{size}-{i}' for i in range(size)]
        start = time.perf_counter()
        reply = batch.infer(ids,values)
        elapsed = time.perf_counter()-start
        start = time.perf_counter()
        warm = batch.infer(ids,values)
        warm_s = time.perf_counter()-start
        errors = []
        for raw, actual in zip(values, reply['raw_actions']):
            policy._rng = jax.random.key(0)
            expected = np.asarray(policy.infer(raw)['actions'],np.float32)
            errors.append(float(np.max(np.abs(expected-actual))))
        records.append(dict(batch_size=size,including_compile_s=elapsed,warm_s=warm_s,
            output_shape=list(warm['actions'].shape),source_singleton_max_abs_errors=errors,
            repeated_retained_inputs=True,distinct_task_coverage=False,
            device_memory=jax.devices()[0].memory_stats()))
        print(json.dumps(records[-1]),flush=True)
    atomic_json(a.output,dict(scope='GPU batched-inference integration only, not task performance or full-task simulator capacity',
        source_request_sha256=file_sha(a.request),checkpoint_identity=checkpoint_identity(checkpoint),
        records=records,simulator_actions=0,paid_calls=0),exclusive=True)
    print(json.dumps(records))


if __name__ == '__main__':
    main()
