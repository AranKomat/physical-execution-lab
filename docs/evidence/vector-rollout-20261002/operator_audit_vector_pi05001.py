"""Audit retained vector proposals, native ACK counters and prefix cadence."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
root = a.directory
report = json.loads((root / 'report.json').read_text())
assert report['status'] in ('bounded_wave_incomplete', 'native_terminal_wave')
registration = report['native_registration']['condition_group_counts']
assert all(sum(registration[name][i] for name in registration) > 0
    for i in range(report['requested_envs']))
rows = [json.loads(line) for line in (root / 'actions.jsonl').read_text().splitlines()]
by_env = {idx: [] for idx in range(report['requested_envs'])}
for row in rows:
    by_env[row['env_idx']].append(row)
for idx, values in by_env.items():
    assert [row['step'] for row in values] == list(range(1, report['action_counts'][idx] + 1))
    ended = [i for i, row in enumerate(values) if row['ended']]
    assert not ended or ended == [len(values) - 1]
    for row in values:
        assert row['prediction'] == (row['step'] - 1) // 15
        assert row['prefix_index'] == (row['step'] - 1) % 15
for prediction in range(report['predictions']):
    metadata = json.loads((root / f'prediction-{prediction:04d}.json').read_text())
    assert hashlib.sha256((root / f'request-{prediction:04d}.npz').read_bytes()).hexdigest() == metadata['request_sha256']
    with np.load(root / f'prediction-{prediction:04d}.npz') as source, np.load(root / f'request-{prediction:04d}.npz') as obs:
        assert source['env_ids'].tolist() == obs['env_ids'].tolist() == metadata['env_ids']
        assert source['actions'].shape == (len(metadata['env_ids']), 50, 14)
        assert np.isfinite(source['actions']).all()
        converted = source['raw_actions'].copy()
        converted[:, :, [6, 13]] = np.clip(converted[:, :, [6, 13]], 0., 1.)
        assert np.array_equal(converted, source['actions'])
        assert obs['steps'].tolist() == [prediction * 15] * len(metadata['env_ids'])
        for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist'):
            assert obs[name].shape == (len(metadata['env_ids']), 480, 640, 3)
            assert all(image.std() > 1 for image in obs[name])
        for batch_row, idx in enumerate(metadata['env_ids']):
            for row in by_env[idx]:
                if row['prediction'] == prediction:
                    assert np.array_equal(np.asarray(row['action']), source['actions'][batch_row, row['prefix_index']])
for path in root.glob('ack-*.npz'):
    step = int(path.stem.split('-')[1])
    with np.load(path) as ack:
        for batch_row, idx in enumerate(ack['env_ids'].tolist()):
            assert np.array_equal(ack['states'][batch_row], np.asarray(by_env[idx][step - 1]['state']))
result = {'audited_actions': len(rows), 'per_env_actions': report['action_counts'],
    'prediction_and_request_env_routing': True, 'source_actions_match_journal': True,
    'contiguous_native_counter_acks': True, 'H50_15_prefix_cadence': True,
    'post_action_state_matches_ack_payload': True, 'nonempty_native_completion_conditions': True,
    'all_policy_cameras_nonblank': True, 'scope': 'bounded vector rollout trace, not isolated-trajectory parity or held-out qualification'}
(root / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
