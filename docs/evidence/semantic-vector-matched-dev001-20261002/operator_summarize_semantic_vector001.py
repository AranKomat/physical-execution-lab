"""Evaluator-only summary; never supplies scores or predicates to the actor."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, default=Path('/root/physical-execution-lab'))
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
conditions = {'motor_only': '001', 'task_plus_subtask': '002', 'subtask_only': '003'}
rows, conditions_audited = {}, {}
for condition, tag in conditions.items():
    directory = a.root / f'runs/semantic-multifamily-pi05-{tag}'
    report_path = directory / 'report.json'
    if not report_path.exists():
        conditions_audited[condition] = False
        continue
    report = json.loads(report_path.read_text())
    if report['status'] not in ('native_terminal_concurrent_waves', 'bounded_concurrent_waves_completed'):
        conditions_audited[condition] = False
        continue
    conditions_audited[condition] = (directory / 'offline-audit.json').exists()
    for task, wave in report['waves'].items():
        for idx, result in wave['controller_results'].items():
            layout = wave['reset_seeds'][int(idx)]
            name = f'{task}__layout{layout}'
            row = rows.setdefault(name, {'task': task, 'layout': layout, 'conditions': {}})
            binding = wave['layout_bindings'][int(idx)]['sha256']
            assert row.setdefault('layout_sha256', binding) == binding
            assert condition not in row['conditions']
            row['conditions'][condition] = {'status': result['status'],
                'native_terminal': result['native_terminal_observed'],
                'success': result['success'], 'native_score': result['native_score'],
                'actions': result['native_steps'], 'policy_calls': result['metrics']['policy_calls'],
                'semantic_calls': result['metrics']['semantic_calls'],
                'semantic_changes': result['metrics']['semantic_changes'],
                'semantic_recoveries': result['metrics']['semantic_recoveries']}
value = {'cohort': 'semantic-vector-matched-dev001',
    'scope': 'five unique task-layout cases across two development task types; not benchmark SR',
    'conditions_audited': conditions_audited,
    'all_conditions_present_and_audited': all(conditions_audited.values()) and len(rows) == 5,
    'cases': rows, 'missing_cases_by_condition': {condition: [name for name, row in rows.items()
        if condition not in row['conditions']] for condition in conditions},
    'historical_serial_cohort_not_pooled': True, 'recovery_enabled': False}
with a.output.open('x') as stream:
    json.dump(value, stream, indent=2)
    stream.write('\n')
print(json.dumps(value))
