"""One source pi0.5 runtime for independently owned native family simulators."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path('/root/physical-execution-lab')
sys.path[:0] = [str(ROOT), str(ROOT / 'external/GPT-as-Policy')]
from operator_vector_pi05_rollout001 import write_json, memory

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
a = p.parse_args()
broker = a.root.resolve()
assert broker.is_relative_to(ROOT / 'runs') and broker.is_dir()
assert not (broker / 'service-ready.json').exists()
import jax
import numpy as np
from openpi.policies.policy_config import create_trained_policy
from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract, checkpoint_identity
provider = json.loads((ROOT / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
checkpoint = Path(provider['checkpoint_path'])
cfg, _ = data_contract(checkpoint)
policy = create_trained_policy(cfg, checkpoint)
from openpi.models.tokenizer import PaligemmaTokenizer
from semantic_lab.token_retention import PromptRetentionGuard
prompt_records = []
def record_prompt(row):
    prompt_records.append(row)
    with (broker / 'live-token-retention.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(row, wave=out.name, prediction_index=index,
            row_in_request=len(prompt_records)-1)) + '\n')
decoder = PaligemmaTokenizer(cfg.model.max_token_len)._tokenizer.decode
policy._input_transform = PromptRetentionGuard(policy._input_transform, decoder, record_prompt)
identity = checkpoint_identity(checkpoint)
ready = {'identity': identity, 'inference_mode': 'native_singleton',
    'rng': 'separate source seed0 streams keyed by wave and env',
    'memory': memory(), 'shared_model': True}
write_json(broker / 'service-ready.json', ready)
print(json.dumps({'event': 'ready', **ready}), flush=True)
waves, keys = {}, {}
try:
    while not (broker / 'stop-service').exists():
        for registration in sorted(broker.glob('*.registration.json')):
            out = Path(json.loads(registration.read_text())['output']).resolve()
            assert out.is_relative_to(ROOT / 'runs') and out.is_dir()
            if out not in waves:
                waves[out] = {'index': 0, 'calls': {}}
                write_json(out / 'worker-ready.json', ready)
        progressed = False
        for out, state in list(waves.items()):
            if (out / 'stop-worker').exists():
                continue
            index = state['index']
            request = out / f'request-{index:04d}.npz'
            if not request.exists():
                continue
            start = time.perf_counter()
            prompt_records.clear()
            values = []
            with np.load(request, allow_pickle=False) as data:
                env_ids = data['env_ids'].tolist()
                assert len(set(env_ids)) == len(env_ids)
                for row, idx in enumerate(env_ids):
                    raw = {'state': data['states'][row].copy(),
                        'prompt': str(data['prompts'][row]), 'images': {
                            name: np.transpose(data[name][row], (2, 0, 1)).copy()
                            for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
                    key = (str(out), idx)
                    policy._rng = keys.get(key, jax.random.key(0))
                    values.append(np.asarray(policy.infer(raw)['actions'], np.float32))
                    keys[key] = policy._rng
                    state['calls'][idx] = state['calls'].get(idx, 0) + 1
            raw_actions = np.stack(values)
            assert raw_actions.shape == (len(env_ids), 50, 14) and np.isfinite(raw_actions).all()
            actions = raw_actions.copy()
            actions[:, :, [6, 13]] = np.clip(actions[:, :, [6, 13]], 0., 1.)
            np.savez_compressed(out / f'prediction-{index:04d}.npz', actions=actions,
                raw_actions=raw_actions, env_ids=np.array(env_ids))
            write_json(out / f'prediction-{index:04d}.json', {
                'inference_s': time.perf_counter() - start, 'env_ids': env_ids,
                'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
                'memory': memory(), 'inference_mode': 'native_singleton',
                'native_calls_per_env': state['calls'], 'shared_worker_root': str(broker),
                'live_prompt_retention': list(prompt_records),
                'rng_keys_after': {str(idx): jax.random.key_data(keys[(str(out), idx)]).tolist()
                    for idx in state['calls']}})
            state['index'] += 1
            progressed = True
        if not progressed:
            time.sleep(.05)
except BaseException as exc:
    error = {'error': type(exc).__name__ + ': ' + str(exc), 'automatic_retry': False}
    write_json(broker / 'service-error.json', error)
    for out in waves:
        write_json(out / 'worker-error.json', error)
    raise
finally:
    write_json(broker / 'service-result.json', {
        'status': 'error_stop_no_retry' if (broker / 'service-error.json').exists() else 'stopped',
        'waves': {str(out): state for out, state in waves.items()}, 'memory': memory()})
