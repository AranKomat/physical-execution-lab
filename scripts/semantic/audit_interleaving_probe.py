#!/usr/bin/env python3
"""Audit bounded source-policy/FK/correction integration, not task performance."""
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
    assert report['controller_probe'] and not report['policy_free_direct']
    assert report['paid_calls'] == 0 and report['unstable_envs'] == []
    commands = [json.loads(line) for line in (root/'actions.jsonl').read_text().splitlines()]
    results = {}
    for idx, count in enumerate(report['action_counts']):
        assert count == 45
        path = root/'episodes'/str(idx)/'controller'/'events.jsonl'
        chain = verify(path)
        events = [json.loads(line) for line in path.read_text().splitlines()]
        acks = [r['data'] for r in events if r['event'] == 'control_ack']
        emitted = [r for r in commands if r['env_idx'] == idx]
        assert [r['step'] for r in acks] == [r['step'] for r in emitted] == list(range(1,46))
        proposals = [r['data'] for r in events if r['event'] == 'policy_proposal']
        assert len(proposals) == 4
        for serial, proposal in enumerate(proposals):
            with np.load(root/'source-policy-proposals'/str(idx)/f'proposal_{serial:06d}.npz') as source:
                actual = np.array([r['values'] for r in proposal['actions']], dtype=np.float32)
                assert np.array_equal(actual, source['actions']) and actual.shape == (50,14)
        receipts = [r['data'] for r in events if r['event'] == 'execution_receipt']
        assert [(r['executor'],r['executed_steps']) for r in receipts] == [
            ('motor',15),('correction',5),('motor',15),('motor',10)]
        for ack, command in zip(acks, emitted):
            assert ack['action'] == command['requested_action'] and ack['correction'] == command['correction']
            if not command['correction']:
                assert command['action'] == ack['action']['values']
                start = max(r['step'] for r in proposals if r['step'] < ack['step'])
                proposal = next(r for r in proposals if r['step'] == start)
                assert ack['action'] == proposal['actions'][ack['step']-start-1]
            else:
                for arm in ('left','right'):
                    d = command['source_dls_diagnostics'][arm]
                    assert d['method'] == 'robot_only_numerical_jacobian_dls'
                    assert max(abs(x) for x in d['proposed_joint_delta']) <= .050001
        reviews = [r['data'] for r in events if r['event'] == 'review']
        target = reviews[1]['decision']['actions'][0]['values']
        at15 = acks[14]['eef']
        moved = 'left' if idx % 2 == 0 else 'right'
        for arm, off in [('left',0),('right',8)]:
            delta = np.array(target[off:off+3])-at15[arm]['xyz']
            assert np.allclose(delta, [0,0,.005] if arm == moved else [0,0,0], atol=1e-6)
        preview_dispatches = [d for d in report['dispatches'] if d['operation'] == 'preview' and idx in d['env_ids']]
        assert len(preview_dispatches) == 4
        results[str(idx)] = dict(actions=count, motor_steps=40, corrected_steps=5,
                                policy_calls=4, preview_dispatches=4, correction_arm=moved, journal=chain)
    return dict(passed=True, environments=results, paid_calls=0,
        scope='bounded native execution integration; forced correction fixture, no task-performance claim or unseen-task admission',
        evidence={str(p.relative_to(root)):file_sha(p) for p in sorted(root.rglob('*')) if p.is_file()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    atomic_json(args.output,audit(args.root),exclusive=True)
