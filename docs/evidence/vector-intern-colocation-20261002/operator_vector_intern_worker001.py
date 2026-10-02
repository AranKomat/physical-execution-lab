"""Shared Intern weights; isolated source sessions, RNG and every actual ACK."""
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

def worker(out, inference_mode):
    assert inference_mode == 'native_singleton'
    root = Path('/root/physical-execution-lab')
    sys.path.insert(0, str(root))
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import numpy as np
    import torch
    from k1lab.multibench.adapters.xpolicylab import XPolicyModel, decode_xpl, seed_policy
    from operator_vector_pi05_rollout001 import write_json, memory
    path = root / 'configs/local/intern-two-gpu-bound-001/provider.json'
    provider = json.loads(path.read_text())
    adapter = XPolicyModel(provider)
    model = adapter.model
    model.reset()
    assert provider['identity']['execute_steps'] == 10

    def snapshot():
        return (random.getstate(), np.random.get_state(), torch.get_rng_state(), torch.cuda.get_rng_state_all())

    def restore(state):
        random.setstate(state[0]); np.random.set_state(state[1])
        torch.set_rng_state(state[2]); torch.cuda.set_rng_state_all(state[3])

    seed_policy(provider['policy_rng_seed'])
    initial = snapshot()
    streams, steps, calls, acknowledgements = {}, {}, {}, {}
    write_json(out / 'worker-ready.json', {'identity': provider['identity'],
        'memory': memory(), 'history': 'one source WAM session per env; every actual ACK',
        'rng': 'isolated Python/NumPy/Torch CPU and both CUDA streams per env'})

    def raw(data, row, idx):
        state = data['states'][row]
        return {'env_idx': idx, 'instruction': str(data['prompts'][row]),
            'state': {key: state[offset+begin:offset+end].copy()
                for arm, offset in (('left', 0), ('right', 7))
                for key, begin, end in ((f'{arm}_arm_joint_state', 0, 6), (f'{arm}_ee_joint_state', 6, 7))},
            'vision': {('cam_head' if name == 'cam_high' else name): {'color': data[name][row].copy()}
                for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}

    prediction, next_ack = 0, 1
    while not (out / 'stop-worker').exists():
        ack = out / f'source-ack-{next_ack:04d}.npz'
        request = out / f'request-{prediction:04d}.npz'
        if ack.exists() and not ack.with_suffix('.json').exists():
            with np.load(ack, allow_pickle=False) as data:
                ids = data['env_ids'].tolist()
                for row, idx in enumerate(ids):
                    assert int(data['steps'][row]) == steps[idx] + 1
                    session = model._session_for(idx)
                    before = len(session.pending_model_actions)
                    assert before > 0
                    restore(streams[idx])
                    model.update_obs_batch([raw(data, row, idx)])
                    assert len(session.pending_model_actions) == before - 1
                    steps[idx] += 1
                    acknowledgements[idx] = acknowledgements.get(idx, 0) + 1
                    streams[idx] = snapshot()
            write_json(ack.with_suffix('.json'), {'env_ids': ids, 'steps': dict(steps),
                'source_pending_actions': {idx: len(model._session_for(idx).pending_model_actions) for idx in ids},
                'ack_sha256': hashlib.sha256(ack.read_bytes()).hexdigest()})
            next_ack += 1
        elif request.exists() and not (out / f'prediction-{prediction:04d}.json').exists():
            start = time.perf_counter()
            values = []
            with np.load(request, allow_pickle=False) as data:
                ids = data['env_ids'].tolist()
                for row, idx in enumerate(ids):
                    restore(streams.get(idx, initial))
                    if idx not in steps:
                        assert int(data['steps'][row]) == 0
                        model.update_obs_batch([raw(data, row, idx)])
                        steps[idx] = 0
                    assert int(data['steps'][row]) == steps[idx]
                    assert not model._session_for(idx).pending_model_actions
                    chunk = model.get_action_batch(env_idx_list=[idx])[0]
                    actions, _ = decode_xpl(chunk, 'x5_joint14', provider['gripper_clip'])
                    values.append(np.stack([action.values for action in actions]))
                    calls[idx] = calls.get(idx, 0) + 1
                    streams[idx] = snapshot()
            result = np.stack(values)
            assert result.shape == (len(ids), 10, 14) and np.isfinite(result).all()
            np.savez_compressed(out / f'prediction-{prediction:04d}.npz', actions=result, env_ids=np.array(ids))
            write_json(out / f'prediction-{prediction:04d}.json', {'env_ids': ids,
                'inference_s': time.perf_counter()-start, 'native_calls_per_env': calls,
                'memory': memory(), 'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest()})
            prediction += 1
        else:
            time.sleep(.01)
    write_json(out / 'intern-worker-result.json', {'native_calls_per_env': calls,
        'actual_acks_per_env': acknowledgements, 'session_keys': list(model.env_sessions),
        'pending_actions': {idx: len(session.pending_model_actions) for idx, session in model.env_sessions.items()},
        'memory': memory(), 'paid_calls': 0})
