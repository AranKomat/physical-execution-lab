"""Audit concurrent semantic families, source RNG and native terminal receipts."""
import json
from pathlib import Path
import subprocess
import sys
import jax
import numpy as np

out = Path(sys.argv[1])
report = json.loads((out / 'report.json').read_text())
assert report['status'] in ('native_terminal_concurrent_waves', 'bounded_concurrent_waves_completed', 'error_stop_no_retry')
service = json.loads((out / 'shared-worker/service-result.json').read_text())
assert service['status'] == 'stopped'
assert set(service['waves']) == set(report['wave_outputs'].values())
audits = {}
for task, name in report['wave_outputs'].items():
    wave = Path(name)
    data = json.loads((wave / 'report.json').read_text())
    auditor = ('operator_audit_semantic_vector001.py' if data['paid_calls'] == 0 else
        'operator_audit_semantic_recovery_vector001.py')
    subprocess.run([sys.executable, str(Path(__file__).with_name(auditor)), name], check=True)
    audits[task] = json.loads((wave / 'offline-audit.json').read_text())
    assert data['task'] == task
    assert data['reset_seeds'] == ([0, 1, 2] if task == 'classify_objects' else [0, 1])
    state = service['waves'][name]
    calls = {str(idx): (steps + 14) // 15 for idx, steps in enumerate(data['action_counts'])}
    assert state['calls'] == calls and state['index'] == data['predictions']
    last = json.loads((wave / f'prediction-{data["predictions"]-1:04d}.json').read_text())
    for idx, count in calls.items():
        key = jax.random.key(0)
        for _ in range(count):
            key, _ = jax.random.split(key)
        assert last['rng_keys_after'][idx] == jax.random.key_data(key).tolist()
    dispatches = data['dispatches']
    for idx, result in data['controller_results'].items():
        count = int(idx)
        assert sum(count in d['env_ids'] for d in dispatches if d['operation'] == 'action') == result['native_steps']
        assert sum(count in d['env_ids'] for d in dispatches if d['operation'] == 'infer') == calls[idx]
        if data['status'] == 'native_terminal_semantic_wave':
            assert result['native_terminal_observed'] and result['status'] == 'native_completed'
        with np.load(wave / 'request-0000.npz', allow_pickle=False) as request:
            assert result['native_steps'] > 0
    assert sum(r['metrics']['semantic_calls'] for r in data['controller_results'].values()) == data['paid_calls']
paid_calls = sum(json.loads((Path(name) / 'report.json').read_text())['paid_calls'] for name in report['wave_outputs'].values())
result = {'status': 'concurrent_semantic_families_audited', 'families': audits,
    'actual_controls': sum(a['actual_controls'] for a in audits.values()),
    'paid_calls': paid_calls, 'supervisor_reported_paid_calls': report['paid_calls'],
    'supervisor_status': report['status'], 'source_rng_and_membership_counts_verified': True,
    'all_planner_contracts_valid': all(a.get('all_planner_contracts_valid', True) for a in audits.values()),
    'scope': 'execution/rejection accounting with retained supervisor error; not all-valid planner qualification'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
