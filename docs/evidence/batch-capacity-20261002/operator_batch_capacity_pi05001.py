import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'external/GPT-as-Policy'))
from k1lab.util import load_json, atomic_json, file_sha
from k1lab.multibench.transport import decode_obs
from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract
from openpi.policies.policy_config import create_trained_policy
from openpi.models.model import Observation
import jax
import jax.numpy as jnp
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--batches', type=int, nargs='+', default=[1, 2, 4, 8])
p.add_argument('--tag', default='001')
a = p.parse_args()
assert a.tag.isdigit() and all(1 <= n <= 32 for n in a.batches)
out = root / ('runs/batch-capacity-pi05-' + a.tag)
out.mkdir(exist_ok=False)
provider_path = root / 'configs/local/pi05-exact-bound-001/provider.json'
provider = load_json(provider_path)
obs_path = root / 'runs/capture-005/observation.wire.json'
obs = decode_obs(load_json(obs_path))
checkpoint = Path(provider['checkpoint_path'])
cfg, _ = data_contract(checkpoint)
start = time.perf_counter()
policy = create_trained_policy(cfg, checkpoint)
load_s = time.perf_counter() - start
raw = {'state': obs.state, 'prompt': obs.instruction,
    'images': {key: np.transpose(obs.rgb[key], (2, 0, 1))
        for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
rows = []
for batch in a.batches:
    times = []
    try:
        for repeat in range(3):
            start = time.perf_counter()
            transformed = [policy._input_transform(jax.tree.map(lambda x: x, raw)) for _ in range(batch)]
            inputs = jax.tree.map(lambda *x: jnp.asarray(np.stack(x)), *transformed)
            _, sample_rng = jax.random.split(jax.random.key(0))
            actions = policy._sample_actions(sample_rng, Observation.from_dict(inputs), **policy._sample_kwargs)
            actions.block_until_ready()
            for i in range(batch):
                result = policy._output_transform({'state': np.asarray(inputs['state'][i]),
                    'actions': np.asarray(actions[i])})
                assert result['actions'].shape == (50, 14)
                assert np.isfinite(result['actions']).all()
            times.append(time.perf_counter() - start)
        stats = jax.devices()[0].memory_stats()
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.free',
            '--format=csv,noheader,nounits'], text=True)
        row = {'requested_batch': batch, 'status': 'valid_proposals', 'first_s': times[0],
            'warm_s': times[1:], 'warm_proposals_per_second': 2 * batch / sum(times[1:]),
            'jax_memory_stats': stats, 'nvidia_smi_snapshot': gpu,
            'implementation': 'per_row_native_transforms_then_fused_model_batch'}
    except Exception as exc:
        row = {'requested_batch': batch, 'status': 'error_stop_no_retry',
            'error': type(exc).__name__ + ': ' + str(exc)[:600]}
    rows.append(row)
    atomic_json(out / 'report.json', {'model': 'pi05', 'provider_sha256': file_sha(provider_path),
        'observation_sha256': file_sha(obs_path), 'load_s': load_s, 'rows': rows,
        'actions_executed': 0, 'paid_calls': 0, 'simulators_in_probe': 0,
        'scope': 'model-level capacity; native wire server has no batch scheduler',
        'rng_caveat': 'batched seed0 sampling is not per-episode RNG parity',
        'repeated_input_caveat': 'identical retained legal RGB/state/text per row; diverse tasks unmeasured'})
    print(json.dumps(row), flush=True)
    if row['status'] != 'valid_proposals':
        break
