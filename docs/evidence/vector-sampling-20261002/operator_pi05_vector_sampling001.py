"""Compare native isolated sampling to a fused batch with per-env noise streams."""
import copy
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path('/root/physical-execution-lab')
sys.path[:0] = [str(ROOT), str(ROOT / 'external/GPT-as-Policy')]
import jax
import jax.numpy as jnp
import numpy as np
from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract
from openpi.models.model import Observation
from openpi.policies.policy_config import create_trained_policy

p = argparse.ArgumentParser()
p.add_argument('--tag', default='001')
args = p.parse_args()
assert args.tag.isdigit()
out = ROOT / ('runs/pi05-vector-sampling-' + args.tag)
out.mkdir(exist_ok=False)
provider = json.loads((ROOT / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
checkpoint = Path(provider['checkpoint_path'])
cfg, _ = data_contract(checkpoint)
policy = create_trained_policy(cfg, checkpoint)
keys = {i: jax.random.key(0) for i in range(5)}
report = {'scope': 'retained legal observations; no simulator controls or paid calls',
    'paid_calls': 0, 'control_actions': 0, 'rounds': [],
    'checkpoint_path': str(checkpoint), 'comparison_atol': .0001, 'comparison_rtol': 0}
try:
    for boundary in range(2):
        path = ROOT / f'runs/vector-pi05-5-002/request-{boundary:04d}.npz'
        with np.load(path, allow_pickle=False) as data:
            env_ids = data['env_ids'].tolist()
            raws = [{'state': data['states'][i].copy(), 'prompt': str(data['prompts'][i]),
                'images': {name: np.transpose(data[name][i], (2, 0, 1)).copy()
                    for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
                for i in range(len(env_ids))]
        isolated = []
        transformed = []
        noises = []
        for idx, raw in zip(env_ids, raws):
            policy._rng = keys[idx]
            result = policy.infer(copy.deepcopy(raw))
            isolated.append(np.asarray(result['actions'], np.float32))
            next_key, sample_key = jax.random.split(keys[idx])
            assert np.array_equal(jax.random.key_data(policy._rng), jax.random.key_data(next_key))
            noise = jax.random.normal(sample_key, (1, policy._model.action_horizon, policy._model.action_dim))
            noises.append(noise[0])
            keys[idx] = next_key
            transformed.append(policy._input_transform(copy.deepcopy(raw)))
        inputs = jax.tree.map(lambda *x: jnp.asarray(np.stack(x)), *transformed)
        for row, original in enumerate(transformed):
            leaves = jax.tree.leaves(jax.tree.map(lambda x: np.asarray(x[row]), inputs))
            native_cast = jax.tree.map(lambda x: np.asarray(jnp.asarray(x)), original)
            assert all(np.array_equal(a, b) for a, b in zip(leaves, jax.tree.leaves(native_cast)))
        start = time.perf_counter()
        fused = policy._sample_actions(jax.random.key(0), Observation.from_dict(inputs),
            noise=jnp.stack(noises), **policy._sample_kwargs)
        fused.block_until_ready()
        model_s = time.perf_counter() - start
        batch_actions = np.stack([policy._output_transform({'state': np.asarray(inputs['state'][i]),
            'actions': np.asarray(fused[i])})['actions'] for i in range(len(env_ids))]).astype(np.float32)
        isolated = np.stack(isolated)
        assert batch_actions.shape == isolated.shape == (5, 50, 14)
        delta = np.abs(batch_actions - isolated)
        np.savez_compressed(out / f'round-{boundary}.npz', isolated=isolated,
            fused=batch_actions, noise=np.asarray(jnp.stack(noises)), env_ids=np.array(env_ids))
        report['rounds'].append({'boundary': boundary, 'request_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'transformed_inputs_exact': True, 'source_rng_advance_exact': True,
            'explicit_noise_shape': list(jnp.stack(noises).shape), 'fused_model_s': model_s,
            'raw_max_abs_delta': float(delta.max()), 'raw_per_env_max_abs_delta': delta.max(axis=(1, 2)).tolist(),
            'raw_per_dimension_max_abs_delta': delta.max(axis=(0, 1)).tolist(),
            'raw_allclose_1e4': bool(np.allclose(isolated, batch_actions, rtol=0, atol=.0001)),
            'raw_bitwise_equal': bool(np.array_equal(isolated, batch_actions))})
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    report['status'] = 'comparison_completed'
except BaseException as exc:
    report.update(status='error_stop_no_retry', error=type(exc).__name__ + ': ' + str(exc))
    raise
finally:
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
