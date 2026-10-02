"""Preserve all selected case outcomes in the reference-bound comparison."""
import json
from pathlib import Path

root = Path('/root/physical-execution-lab/runs')
base = json.loads((root / 'reference-pi05-2-001/report.json').read_text())
candidate = json.loads((root / 'reference-pi05-2-002/report.json').read_text())
audit = json.loads((root / 'reference-pi05-2-002/offline-audit.json').read_text())
assert base['reference_cases'] == candidate['reference_cases']
assert base['layout_bindings'] == candidate['layout_bindings']
assert base['reference_manifest_file_sha256'] == candidate['reference_manifest_file_sha256']
identities = [json.loads((root / f'reference-pi05-2-{tag}/worker-ready.json').read_text())['identity'] for tag in ('001', '002')]
assert identities[0] == identities[1]
rows = []
for idx, case in enumerate(base['reference_cases']):
    conditions = {}
    for label, data in [('motor_only', base), ('task_plus_recovery', candidate)]:
        r = data['controller_results'][str(idx)]
        conditions[label] = {key: r[key] for key in ('status', 'success', 'native_score',
            'native_steps', 'native_terminal_observed', 'error')}
        conditions[label]['metrics'] = r['metrics']
    rows.append({'case_id': case['case_id'], 'partition': case['partition'],
        'historically_opened_family': True, 'conditions': conditions})
summary = {'scope': 'two fixed reference cases from a historically opened task; not untouched held-out or benchmark SR',
    'checkpoint_and_reference_binding_equal': True,
    'all_planner_contracts_valid': audit['all_planner_contracts_valid'],
    'successes': {label: sum(row['conditions'][label]['success'] for row in rows)
        for label in ('motor_only', 'task_plus_recovery')},
    'paid_calls': candidate['paid_calls'],
    'rollout_wall_s': {'motor_only': base['wall_s'], 'task_plus_recovery': candidate['wall_s']},
    'counterfactual_trajectory_parity': False, 'causal_benefit_established': False, 'cases': rows}
target = root / 'reference-arrange-semantic001/paired-summary.json'
with target.open('x') as stream:
    json.dump(summary, stream, indent=2)
    stream.write('\n')
print(json.dumps(summary))
