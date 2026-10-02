#!/usr/bin/env python3
"""Audit retained full-panel numeric/direct ACKs, including censored trials."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.errors import ContractError
from k1lab.journal import verify
from k1lab.util import atomic_json, file_sha, load_json
from scripts.semantic.run_full_panel_baseline import summarize_cohort_results


def audit(run):
    parent = load_json(run / 'report.json')
    direct = parent['method'] == 'direct'
    if parent['method'] not in ('direct', 'numeric'):
        raise ContractError('requires the full native control panel')
    cases, actions, client_attempts = [], 0, 0
    for group in sorted(run.glob('group[0-9]')):
        report = load_json(group / 'report.json')
        binding = load_json(group / 'pre-action-admission.json')
        if not binding['passed'] or not load_json(group / 'cohort-admitted.json')['all_ten_reset_bindings_passed']:
            raise ContractError('full native pre-action admission was not established')
        if (len(binding['initial_fk_checks']) != len(report['controller_results'])
                or any(not row['passed'] for row in binding['initial_fk_checks'].values())):
            raise ContractError('indexed FK validation incomplete')
        commands = [json.loads(line) for line in (group / 'actions.jsonl').read_text().splitlines()]
        for key, result in report['controller_results'].items():
            idx = int(key)
            journal = group / 'episodes' / key / 'controller/events.jsonl'
            verify(journal)
            events = [json.loads(line) for line in journal.read_text().splitlines()]
            acks = [row['data'] for row in events if row['event'] == 'control_ack']
            emitted = [row for row in commands if row['env_idx'] == idx]
            if ([row['step'] for row in acks] != list(range(1, result['native_steps']+1))
                    or len(emitted) != len(acks)):
                raise ContractError('native action/ACK coverage is incomplete')
            if direct and (result['policy_identity'] is not None or result['metrics']['policy_calls'] != 0):
                raise ContractError('policy-free direct queried a motor policy')
            for ack, command in zip(acks, emitted):
                if (ack['step'] != command['step'] or ack['action'] != command['requested_action']
                        or ack['correction'] != command['correction']):
                    raise ContractError('requested native action differs from its physical ACK')
                if command['correction']:
                    if ack['action']['space'] != 'x5_eef16_wxyz':
                        raise ContractError('incorrect EEF correction convention')
                    for arm in ('left', 'right'):
                        diag = command['source_dls_diagnostics'][arm]
                        if (diag['method'] != 'robot_only_numerical_jacobian_dls'
                                or np.max(np.abs(diag['proposed_joint_delta'])) > .050001):
                            raise ContractError('native source DLS update exceeds its robot-only contract')
                elif command['action'] != ack['action']['values']:
                    raise ContractError('motor joint command was modified')
            if result['status'] == 'native_completed' and (
                    not emitted or not emitted[-1]['ended'] or emitted[-1]['success'] != result['success']):
                raise ContractError('native task result lacks a matching terminal ACK')
            cases.append(dict(case_id=result['case_id'], status=result['status'],
                native_steps=result['native_steps'], native_score=result['native_score'],
                success=result['success'], error=result['error']))
            actions += len(acks)
            client_attempts += result['usage'].get('api_requests') or 0
    if len(cases) != 10 or {row['case_id'] for row in cases} != set(parent['cases']):
        raise ContractError('control audit did not cover the complete fixed panel')
    return dict(scope='retained full-panel routing, admission and control ACK integrity',
        integrity_passed=True, benchmark_qualified=False,
        raw_parent_report_sha256=file_sha(run / 'report.json'),
        summary=summarize_cohort_results(parent['groups']),
        distinct_cases=10, native_actions=actions, client_http_attempts=client_attempts,
        motor_policy_loaded=not direct, rows=cases)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    atomic_json(args.output, audit(args.run), exclusive=True)
