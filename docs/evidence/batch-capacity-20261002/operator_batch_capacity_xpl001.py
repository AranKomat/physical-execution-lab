import argparse
import gc
import json
import os
from pathlib import Path
import sys
import time

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from k1lab.util import load_json, atomic_json, file_sha
from k1lab.multibench.transport import decode_obs
from k1lab.multibench.adapters.xpolicylab import XPolicyModel, to_xpl, decode_xpl

p = argparse.ArgumentParser()
p.add_argument('--model', choices=('g05', 'intern'), required=True)
p.add_argument('--batches', type=int, nargs='+', default=[1, 2, 4, 8])
p.add_argument('--tag', default='001')
a = p.parse_args()
assert a.tag.isdigit() and all(1 <= n <= 32 for n in a.batches)
out = root / ('runs/batch-capacity-' + a.model + '-' + a.tag)
out.mkdir(exist_ok=False)
path = root / ('configs/local/g05-fla-seed0-ancillary-bound-004/provider.json' if a.model == 'g05'
    else 'configs/local/intern-two-gpu-bound-001/provider.json')
cfg = load_json(path)
obs_path = root / 'runs/capture-005/observation.wire.json'
obs = decode_obs(load_json(obs_path))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['ROBODOJO_LEROBOT_V30_ROOT'] = '/nonexistent/inference-does-not-load-datasets'
import torch
devices = list(range(torch.cuda.device_count())) if a.model == 'intern' else [0]

def sync():
    for d in devices:
        torch.cuda.synchronize(d)

def memory():
    return {str(d): {'allocated_gib': torch.cuda.max_memory_allocated(d) / 2**30,
        'reserved_gib': torch.cuda.max_memory_reserved(d) / 2**30} for d in devices}

sync()
start = time.perf_counter()
adapter = XPolicyModel(cfg)
model = adapter.model
sync()
load_s = time.perf_counter() - start
rows = []
for batch in a.batches:
    timings = []
    try:
        model.reset()
        gc.collect()
        torch.cuda.empty_cache()
        for d in devices:
            torch.cuda.reset_peak_memory_stats(d)
        if a.model == 'g05':
            model.inference_batch_size = batch
        for repeat in range(3):
            model.reset()
            inputs = [to_xpl(obs) | {'env_idx': i} for i in range(batch)]
            sync()
            start = time.perf_counter()
            model.update_obs_batch(inputs)
            chunks = model.get_action_batch()
            sync()
            timings.append(time.perf_counter() - start)
            assert len(chunks) == batch
            for chunk in chunks:
                actions, _ = decode_xpl(chunk, 'x5_joint14', cfg.get('gripper_clip', False))
                assert len(actions) == cfg['identity']['execute_steps']
        row = {'requested_batch': batch, 'status': 'valid_proposals',
            'first_s': timings[0], 'warm_s': timings[1:],
            'warm_proposals_per_second': 2 * batch / sum(timings[1:]), 'memory': memory(),
            'implementation': 'fused_inferencer_batch' if a.model == 'g05' else 'sequential_shared_runtime_sessions'}
    except torch.cuda.OutOfMemoryError as exc:
        row = {'requested_batch': batch, 'status': 'oom_stop_no_retry',
            'error': str(exc)[:400], 'memory': memory()}
    except Exception as exc:
        row = {'requested_batch': batch, 'status': 'interface_error_stop_no_retry',
            'error': type(exc).__name__ + ': ' + str(exc)[:400], 'memory': memory()}
    rows.append(row)
    report = {'model': a.model, 'provider_file': str(path), 'provider_sha256': file_sha(path),
        'observation_sha256': file_sha(obs_path), 'load_s': load_s, 'rows': rows,
        'actions_executed': 0, 'paid_calls': 0, 'simulators_in_probe': 0,
        'scope': 'bounded repeated reset-observation capacity; not native task throughput or recurrent history qualification',
        'repeated_input_caveat': 'identical legal RGB/state/text at every batch row; diverse tasks and growing history unmeasured'}
    atomic_json(out / 'report.json', report)
    print(json.dumps(row), flush=True)
    if row['status'] != 'valid_proposals':
        break
