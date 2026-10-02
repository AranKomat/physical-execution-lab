"""Shared G0.5 weights with source single-row inference and per-env RNG/history."""
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time


def worker(out, inference_mode):
    assert inference_mode == 'native_singleton', 'fused execution not qualified'
    root = Path('/root/physical-execution-lab')
    sys.path.insert(0, str(root))
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        ROBODOJO_LEROBOT_V30_ROOT='/nonexistent/inference-does-not-load-datasets')
    import numpy as np
    import torch
    from k1lab.multibench.adapters.xpolicylab import XPolicyModel, decode_xpl, seed_policy
    from operator_vector_pi05_rollout001 import write_json, memory
    provider_path = root / 'configs/local/g05-fla-seed0-ancillary-bound-004/provider.json'
    provider = json.loads(provider_path.read_text())
    adapter = XPolicyModel(provider)
    model = adapter.model
    model.reset()
    assert model.inference_batch_size == 1 and model.action_steps == 16

    def snapshot():
        return (random.getstate(), np.random.get_state(), torch.get_rng_state(),
            torch.cuda.get_rng_state())

    def restore(state):
        random.setstate(state[0])
        np.random.set_state(state[1])
        torch.set_rng_state(state[2])
        torch.cuda.set_rng_state(state[3])

    seed_policy(provider['policy_rng_seed'])
    initial = snapshot()
    streams, calls = {}, {}
    write_json(out / 'worker-ready.json', {'identity': provider['identity'],
        'provider_sha256': hashlib.sha256(provider_path.read_bytes()).hexdigest(),
        'inference_mode': inference_mode, 'rng': 'separate source seed0 streams per env',
        'history': 'source buffers keyed by env_idx; no within-episode reset',
        'memory': memory()})
    index = 0
    while not (out / 'stop-worker').exists():
        request = out / f'request-{index:04d}.npz'
        if not request.exists():
            time.sleep(.05)
            continue
        start = time.perf_counter()
        results, raw_results = [], []
        with np.load(request, allow_pickle=False) as data:
            env_ids = data['env_ids'].tolist()
            for row, idx in enumerate(env_ids):
                state = data['states'][row]
                obs = {'env_idx': idx, 'instruction': str(data['prompts'][row]),
                    'state': {key: state[offset+begin:offset+end].copy()
                        for arm, offset in (('left', 0), ('right', 7))
                        for key, begin, end in ((f'{arm}_arm_joint_state', 0, 6),
                            (f'{arm}_ee_joint_state', 6, 7))},
                    'vision': {name: {'color': data[name][row].copy()}
                        for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
                restore(streams.get(idx, initial))
                model.update_obs_batch([obs])
                chunks = model.get_action_batch()
                torch.cuda.synchronize()
                streams[idx] = snapshot()
                assert len(chunks) == 1
                raw = np.stack([np.concatenate([np.asarray(command[key]).reshape(-1)
                    for arm in ('left', 'right')
                    for key in (f'{arm}_arm_joint_state', f'{arm}_ee_joint_state')])
                    for command in chunks[0]]).astype(np.float32)
                converted, _ = decode_xpl(chunks[0], 'x5_joint14', provider['gripper_clip'])
                raw_results.append(raw)
                results.append(np.stack([a.values for a in converted]))
                calls[idx] = calls.get(idx, 0) + 1
        result, raw_result = np.stack(results), np.stack(raw_results)
        assert result.shape == (len(env_ids), 16, 14) and np.isfinite(result).all()
        np.savez_compressed(out / f'prediction-{index:04d}.npz', actions=result,
            raw_actions=raw_result, env_ids=np.array(env_ids))
        write_json(out / f'prediction-{index:04d}.json', {
            'inference_s': time.perf_counter() - start, 'env_ids': env_ids,
            'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
            'memory': memory(), 'inference_mode': inference_mode,
            'native_calls_per_env': calls, 'history_env_keys': list(model._history_buffers),
            'cuda_rng_sha256_after': {str(idx): hashlib.sha256(state[3].numpy().tobytes()).hexdigest()
                for idx, state in streams.items()}})
        index += 1
