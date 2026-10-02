"""Scoped transfer of retained native evidence to the fixed matched task panel.

This binds the screened simulator runtime, not singleton numerical parity,
whole-benchmark qualification, or real-robot safety.
"""
from pathlib import Path

import numpy as np

from k1lab.errors import ContractError
from k1lab.util import file_sha, load_json


CORE = ('semantic_lab/task_rows.py', 'semantic_lab/native_execution.py',
        'semantic_lab/native_io.py', 'semantic_lab/pi05_batch.py',
        'scripts/semantic/serve_pi05_batch.py')


def check_transfer(root, baseline, native_reference, panel, controller_run):
    root, baseline = Path(root), Path(baseline)
    from k1lab.multibench.manifest import seal
    if native_reference.get('sha256') != seal(native_reference)['sha256']:
        raise ContractError('invalid native reference freeze')
    report = load_json(baseline / 'report.json')
    audit = load_json(baseline / 'integrity-audit.json')
    if (report['status'] != 'completed_full_original_only_cohort'
            or not audit.get('integrity_passed') or audit['distinct_cases'] != 10
            or audit['native_actions'] != sum(sum(g['action_counts']) for g in report['groups'])
            or report['comparison_plan_sha256'] is None
            or set(report['cases']) != {row['case_id'] for row in panel['cases']}):
        raise ContractError('matched admission requires the audited full fixed baseline')
    if any(file_sha(root / path) != report['source_hashes'][path] for path in CORE):
        raise ContractError('baseline task/control/inference core changed; review and rebind evidence')
    native = native_reference['execution_sources']['files']
    selectors = [s for s in native_reference['execution_sources']['selectors']
                 if s.startswith('external/') or s.startswith('configs/local/')]
    from semantic_lab.protocol import execution_snapshot
    actual = execution_snapshot(root, selectors)['files']
    expected = {name: sha for name, sha in native.items()
                if any(name == s or name.startswith(s + '/') for s in selectors)}
    if not expected or actual != expected:
        raise ContractError('retained native source/config snapshot changed')
    control_sources = ('semantic_lab/robot_controls.py', 'semantic_lab/robot_view.py',
                       'semantic_lab/vector.py')
    if any(native.get(path) != file_sha(root / path) for path in control_sources):
        raise ContractError('indexed controller/coordinator changed since native integration evidence')
    control_audit_path = root / 'docs/evidence/reference-execution-binding001-20261002/interleaving-audit001.json'
    control_audit = load_json(control_audit_path)
    if (not control_audit.get('passed') or control_audit['paid_calls'] != 0
            or {row['correction_arm'] for row in control_audit['environments'].values()} != {'left', 'right'}
            or any(row['actions'] != 45 for row in control_audit['environments'].values())
            or not control_audit.get('evidence')):
        raise ContractError('native indexed controller evidence incomplete')
    for path, expected_sha in control_audit['evidence'].items():
        relative = Path(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ContractError('unsafe controller evidence path')
        if file_sha(Path(controller_run) / relative) != expected_sha:
            raise ContractError('retained native controller evidence changed')
    return dict(scope='fixed ten-task matched simulator screen only',
                transfer_checks_passed=True, live_reset_binding_required=True,
                benchmark_qualified=False, singleton_numerical_parity=False,
                baseline_report_sha256=file_sha(baseline / 'report.json'),
                baseline_integrity_sha256=file_sha(baseline / 'integrity-audit.json'),
                native_reference_sha256=native_reference['sha256'],
                unchanged_core={path: file_sha(root / path) for path in CORE},
                native_source_config_files=len(expected),
                native_controller_audit_sha256=file_sha(control_audit_path),
                native_controller_files_checked=len(control_audit['evidence']))


def check_reset(baseline_group, cases, resolved, bindings, horizons, observations):
    """Evaluator-only binding; do not attach layouts/configs to actor prompts."""
    baseline_group = Path(baseline_group)
    if (load_json(baseline_group / 'resolved-configs.json') != resolved
            or load_json(baseline_group / 'task-bindings.json') != bindings
            or horizons != [case['horizon'] for case in cases]):
        raise ContractError('native layout/config/horizon differs from the matched baseline')
    rows = []
    with np.load(baseline_group / 'request-0000.npz', allow_pickle=False) as reference:
        ids = reference['env_ids'].tolist()
        if ids != sorted(observations) or len(ids) != len(cases):
            raise ContractError('baseline initial input coverage differs from the live cohort')
        for offset, idx in enumerate(ids):
            obs = observations[idx]
            error = float(np.max(np.abs(reference['states'][offset] - obs.state)))
            if (obs.step != 0 or error > 1e-5
                    or obs.instruction != str(reference['prompts'][offset])):
                raise ContractError('native reset proprioception/instruction differs from baseline')
            rows.append(dict(case_id=cases[idx]['case_id'], env_idx=idx,
                             reset_proprio_max_error=error, native_instruction_matches=True))
    return dict(scope='matched native configuration/layout/horizon and legal reset proprioception',
                passed=True, rows=rows, rgb_bitwise_parity_required=False,
                rgb_note='same native camera contract; rendered pixel equality not established')
