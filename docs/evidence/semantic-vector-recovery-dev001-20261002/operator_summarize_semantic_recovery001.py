"""Summarize the frozen recovery factor without pooling historical runs."""
import json
from pathlib import Path

root = Path('/root/physical-execution-lab')
out = root / 'runs/semantic-vector-recovery-dev001'
report = json.loads((root / 'runs/semantic-multifamily-pi05-004/report.json').read_text())
audit = json.loads((root / 'runs/semantic-multifamily-pi05-004/offline-audit.json').read_text())
assert audit['status'] == 'concurrent_semantic_families_audited'
prior = json.loads((root / 'runs/semantic-vector-matched-dev001/three-condition-summary.json').read_text())
rows = []
for task, wave_path in report['wave_outputs'].items():
    wave = Path(wave_path)
    data = json.loads((wave / 'report.json').read_text())
    for binding in data['layout_bindings']:
        idx = binding['env_idx']
        key = task + '__layout' + str(binding['layout_id'])
        assert prior['cases'][key]['layout_sha256'] == binding['sha256']
        result = data['controller_results'][str(idx)]
        events = [json.loads(line) for line in
            (wave / 'episodes' / str(idx) / 'controller/events.jsonl').read_text().splitlines()]
        recoveries = [event['data'] for event in events
            if event['event'] == 'semantic_decision' and event['data']['decision']['operation'] == 'recover']
        applied = [event for event in recoveries if event['effect'].get('changed')]
        assert len(applied) == result['metrics']['semantic_recoveries']
        rows.append({
            'case': key, 'status': result['status'], 'success': result['success'],
            'native_score': result['native_score'], 'actions': result['native_steps'],
            'semantic_calls': result['metrics']['semantic_calls'],
            'recovery_decisions': recoveries, 'applied_recoveries': len(applied),
            'native_success_after_applied_recovery': bool(applied and result['success']),
            'causal_recovery_success_established': False,
            'prior_same_layout_conditions': prior['cases'][key]['conditions'],
        })
assert len(rows) == 5 and len({row['case'] for row in rows}) == 5
summary = {
    'cohort': 'semantic-vector-recovery-dev001', 'phase': 'D',
    'scope': 'five development task-layout cases; single execution each; not benchmark SR',
    'all_cases_accounted_for': True, 'audit_passed': True,
    'successes': sum(row['success'] for row in rows),
    'applied_recoveries': sum(row['applied_recoveries'] for row in rows),
    'cases_with_native_success_after_applied_recovery': sum(row['native_success_after_applied_recovery'] for row in rows),
    'causal_benefit_established': False,
    'total_wall_s': report['total_wall_s'], 'paid_calls': audit['paid_calls'],
    'supervisor_status': report['status'],
    'supervisor_reported_paid_calls': report['paid_calls'],
    'all_planner_contracts_valid': audit['all_planner_contracts_valid'], 'cases': rows,
}
with (out / 'summary.json').open('x') as stream:
    json.dump(summary, stream, indent=2)
    stream.write('\n')
print(json.dumps(summary))
