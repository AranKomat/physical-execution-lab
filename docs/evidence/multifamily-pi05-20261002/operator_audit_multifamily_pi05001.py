"""Audit separate native task-family traces served by one pi0.5 runtime."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
out = a.directory
report = json.loads((out / 'report.json').read_text())
assert report['status'] == 'bounded_concurrent_waves_completed'
assert report['policy_runtimes'] == 1 and report['simulator_processes'] == 2
assert report['paid_calls'] == 0
service = json.loads((out / 'shared-worker/service-result.json').read_text())
assert service['status'] == 'stopped'
assert set(service['waves']) == set(report['wave_outputs'].values())
audits, prompts = {}, {}
for task, path in report['wave_outputs'].items():
    wave = Path(path)
    subprocess.run([sys.executable, str(Path(__file__).with_name('operator_audit_vector_pi05001.py')),
        str(wave)], check=True)
    audits[task] = json.loads((wave / 'offline-audit.json').read_text())
    data = json.loads((wave / 'report.json').read_text())
    assert data['task'] == task and data['requested_envs'] == 5
    assert data['action_counts'] == [150] * 5 and data['predictions'] == 10
    assert data['shared_worker_root'] == str(out / 'shared-worker')
    state = service['waves'][path]
    assert state['index'] == 10 and state['calls'] == {str(idx): 10 for idx in range(5)}
    import jax
    import numpy as np
    expected_key = jax.random.key(0)
    for _ in range(10):
        expected_key, _ = jax.random.split(expected_key)
    last = json.loads((wave / 'prediction-0009.json').read_text())
    assert last['rng_keys_after'] == {str(idx): jax.random.key_data(expected_key).tolist()
        for idx in range(5)}
    with np.load(wave / 'request-0000.npz', allow_pickle=False) as request:
        original_prompts = request['prompts'].tolist()
    for index in range(10):
        with np.load(wave / f'request-{index:04d}.npz', allow_pickle=False) as request:
            assert request['prompts'].tolist() == original_prompts
    prompts[task] = original_prompts
assert set(prompts['classify_objects']).isdisjoint(prompts['build_tower'])
result = {'actual_controls': sum(audit['audited_actions'] for audit in audits.values()),
    'task_families': sorted(audits), 'native_wave_audits': audits,
    'shared_worker_call_and_rng_accounting_verified': True,
    'original_family_instructions_preserved': True, 'paid_calls': 0,
    'scope': 'bounded concurrent native execution; not trajectory equivalence, hierarchy or held-out qualification'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
