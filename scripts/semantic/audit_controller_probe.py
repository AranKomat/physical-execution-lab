#!/usr/bin/env python3
"""Audit retained native calibration ACKs; not task or general-controller qualification."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.journal import verify
from k1lab.util import atomic_json, file_sha


def audit(root):
    report = json.loads((root/'report.json').read_text())
    assert report['controller_probe'] and report['policy'] is None
    assert report['predictions'] == report['paid_calls'] == 0
    assert report['unstable_envs'] == []
    fk = json.loads((root/'indexed-fk-validation.json').read_text())
    commands = [json.loads(line) for line in (root/'actions.jsonl').read_text().splitlines()]
    results = {}
    for idx, count in enumerate(report['action_counts']):
        assert count <= 30 and fk[str(idx)]['passed'] and fk[str(idx)]['physical_steps'] == 0
        path = root/'episodes'/str(idx)/'controller'/'events.jsonl'
        chain = verify(path)
        events = [json.loads(line) for line in path.read_text().splitlines()]
        acks = [row['data'] for row in events if row['event'] == 'control_ack']
        emitted = [row for row in commands if row['env_idx'] == idx]
        assert [row['step'] for row in acks] == list(range(1, count+1))
        assert [row['step'] for row in emitted] == list(range(1, count+1))
        for ack, command in zip(acks, emitted):
            assert ack['action'] == command['requested_action'] and command['correction']
            assert np.asarray(command['action']).shape == (14,)
            assert np.isfinite(command['action']).all()
            for arm in ('left', 'right'):
                d = command['source_dls_diagnostics'][arm]
                assert d['method'] == 'robot_only_numerical_jacobian_dls'
                assert max(abs(x) for x in d['proposed_joint_delta']) <= .050001
        receipts = [row['data'] for row in events if row['event'] == 'execution_receipt']
        assert len(receipts) == 2
        errors = []
        for receipt in receipts:
            assert receipt['stop_reason'] == 'robot_target_reached_not_task_success'
            final = acks[receipt['end_step']-1]
            target = final['action']['values']
            errors.append({arm: float(np.linalg.norm(np.asarray(final['eef'][arm]['xyz'])-
                np.asarray(target[offset:offset+3]))) for arm, offset in [('left', 0), ('right', 8)]})
        assert all(value <= .003 for error in errors for value in error.values())
        results[str(idx)] = dict(actions=count, journal=chain, endpoint_position_errors_m=errors,
                                 fk=fk[str(idx)])
    return dict(passed=True, environments=results, paid_calls=0, motor_predictions=0,
                scope='indexed native DLS out/back calibration only; no task success, contact safety or full executor qualification',
                evidence={str(p.relative_to(root)): file_sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    atomic_json(args.output, audit(args.root), exclusive=True)
