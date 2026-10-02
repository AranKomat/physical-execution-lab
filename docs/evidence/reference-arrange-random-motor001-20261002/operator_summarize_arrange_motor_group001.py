"""Combine the five explicit reference motor cases, retaining native qualification limits."""
import hashlib
import json
from pathlib import Path

root = Path('/root/physical-execution-lab')
reports = []
identities = []
config_hashes = set()
for name in ('reference-pi05-2-001', 'reference-pi05-3-003'):
    directory = root / 'runs' / name
    report = json.loads((directory / 'report.json').read_text())
    audit = json.loads((directory / 'offline-audit.json').read_text())
    assert report['status'] == 'native_terminal_semantic_wave'
    assert audit['case_layout_variant_horizon_binding_verified'] and audit['source_predictions_and_native_acks_match']
    assert not report['unstable_envs'] and report['paid_calls'] == 0
    binding = json.loads((directory / 'pre-action-binding.json').read_text())
    for path, expected in binding['sources'].items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
    config_hashes.add(binding['semantic_config_file_sha256'])
    identities.append(json.loads((directory / 'worker-ready.json').read_text())['identity'])
    reports.append((name, report))
assert identities[0] == identities[1] and len(config_hashes) == 1
manifest_path = root / 'configs/local/robodojo-cases.json'
manifest = json.loads(manifest_path.read_text())
expected = {row['case_id'] for row in manifest['cases'] if row['task_group'] == 'arrange_largest_number'}
rows = []
for name, report in reports:
    assert report['reference_manifest_file_sha256'] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    for idx, case in enumerate(report['reference_cases']):
        final = report['controller_results'][str(idx)]
        assert final['status'] == 'native_completed' and final['native_terminal_observed']
        rows.append({'case_id': case['case_id'], 'variant': case['variant'], 'layout_id': case['layout_id'],
                     'partition': case['partition'], 'source_run': name, 'success': final['success'],
                     'native_score': final['native_score'], 'native_steps': final['native_steps']})
assert len(rows) == len(expected) == 5 and {row['case_id'] for row in rows} == expected
summary = {'scope': 'all five selected reference cases of one historically opened task group; not full benchmark or untouched evaluation',
           'native_qualified': False, 'checkpoint_config_source_bindings_verified': True,
           'cases_executed': len(rows), 'successes': sum(row['success'] for row in rows),
           'mean_native_score': sum(row['native_score'] for row in rows) / len(rows),
           'paid_calls': 0, 'rollout_wall_s': {name: report['wall_s'] for name, report in reports},
           'startup_shutdown_excluded_from_rollout_wall': True,
           'hierarchy_remaining_reference_case_ids': sorted(row['case_id'] for row in rows if row['variant'] == 'random'),
           'cases': rows}
target = root / 'runs/reference-arrange-random-motor001/group-summary.json'
with target.open('x') as stream:
    json.dump(summary, stream, indent=2)
    stream.write('\n')
print(json.dumps(summary))
