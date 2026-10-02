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
assert report['status'] in ('bounded_concurrent_waves_completed', 'native_terminal_concurrent_waves')
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
    if report['status'] == 'bounded_concurrent_waves_completed':
        assert data['action_counts'] == [report.get('requested_action_bound_per_env', 150)] * 5
    else:
        assert data['status'] == 'native_terminal_wave' and data['active_envs'] == []
        assert set(data['terminal']) == {str(idx) for idx in range(5)}
    assert data['shared_worker_root'] == str(out / 'shared-worker')
    state = service['waves'][path]
    expected_calls = {str(idx): (steps + 14) // 15 for idx, steps in enumerate(data['action_counts'])}
    assert state['index'] == data['predictions'] and state['calls'] == expected_calls
    import jax
    import numpy as np
    expected_keys = {}
    for idx, count in expected_calls.items():
        key = jax.random.key(0)
        for _ in range(count):
            key, _ = jax.random.split(key)
        expected_keys[idx] = jax.random.key_data(key).tolist()
    last = json.loads((wave / f'prediction-{data["predictions"]-1:04d}.json').read_text())
    assert last['rng_keys_after'] == expected_keys
    with np.load(wave / 'request-0000.npz', allow_pickle=False) as request:
        original_prompts = request['prompts'].tolist()
    for index in range(data['predictions']):
        with np.load(wave / f'request-{index:04d}.npz', allow_pickle=False) as request:
            assert request['prompts'].tolist() == [original_prompts[idx] for idx in request['env_ids'].tolist()]
    prompts[task] = original_prompts
assert set(prompts['classify_objects']).isdisjoint(prompts['build_tower'])
result = {'actual_controls': sum(audit['audited_actions'] for audit in audits.values()),
    'task_families': sorted(audits), 'native_wave_audits': audits,
    'shared_worker_call_and_rng_accounting_verified': True,
    'original_family_instructions_preserved': True, 'paid_calls': 0,
    'scope': 'concurrent native execution; not trajectory equivalence, hierarchy or held-out qualification',
    'native_terminal_membership_verified': report['status'] == 'native_terminal_concurrent_waves'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
