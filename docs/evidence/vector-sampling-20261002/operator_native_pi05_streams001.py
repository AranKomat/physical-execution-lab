"""Exercise the vector worker against retained native singleton references."""
import json
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import jax

ROOT = Path('/root/physical-execution-lab')
sys.path.insert(0, str(ROOT / 'runs'))
from operator_vector_pi05_rollout001 import wait_file

p = argparse.ArgumentParser()
p.add_argument('--tag', default='001')
args = p.parse_args()
assert args.tag.isdigit()
out = ROOT / ('runs/pi05-native-stream-check-' + args.tag)
out.mkdir(exist_ok=False)
reference = ROOT / 'runs/pi05-vector-sampling-002'
source = ROOT / 'runs/vector-pi05-5-002'
shutil.copyfile(source / 'request-0000.npz', out / 'request-0000.npz')
with np.load(source / 'request-0001.npz', allow_pickle=False) as request:
    order = [2, 0, 4]
    np.savez_compressed(out / 'request-0001.npz', **{key: request[key][order] for key in request.files})
report = {'control_actions': 0, 'paid_calls': 0,
    'scope': 'retained legal inputs; native-singleton worker under changing membership/order', 'rounds': []}
child = None
try:
    with (out / 'worker.log').open('x') as log:
        child = subprocess.Popen([sys.executable, '-u', str(ROOT / 'runs/operator_vector_pi05_rollout001.py'),
            '--worker', str(out), '--inference-mode', 'native_singleton'], stdout=log, stderr=subprocess.STDOUT)
        for boundary in range(2):
            wait_file(out / f'prediction-{boundary:04d}.json', child, timeout=300)
            metadata = json.loads((out / f'prediction-{boundary:04d}.json').read_text())
            with np.load(out / f'prediction-{boundary:04d}.npz') as result, np.load(reference / f'round-{boundary}.npz') as expected:
                env_ids = result['env_ids'].tolist()
                values = expected['isolated'][env_ids].copy()
                delta = float(np.abs(values - result['raw_actions']).max())
                expected_counts = {str(i): (boundary + 1 if i in env_ids else 1) for i in range(5)}
                assert metadata['native_calls_per_env'] == expected_counts
                for idx, count in expected_counts.items():
                    key = jax.random.key(0)
                    for _ in range(count):
                        key, _ = jax.random.split(key)
                    assert metadata['rng_keys_after'][idx] == jax.random.key_data(key).tolist()
                report['rounds'].append({'boundary': boundary, 'env_ids': env_ids,
                    'source_raw_max_delta': delta, 'source_raw_bitwise_equal': bool(np.array_equal(values, result['raw_actions'])),
                    'source_raw_allclose_1e4': bool(np.allclose(values, result['raw_actions'], rtol=0, atol=.0001)),
                    'native_calls_per_env': metadata['native_calls_per_env'], 'rng_key_advance_exact': True})
        report['status'] = 'native_stream_accounting_passed_numerical_comparison_recorded'
except BaseException as exc:
    report.update(status='error_stop_no_retry', error=type(exc).__name__ + ': ' + str(exc))
    raise
finally:
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (out / 'stop-worker').touch()
    if child is not None:
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait(timeout=30)
    print(json.dumps(report), flush=True)
