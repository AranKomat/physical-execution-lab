"""Verify source ten-action prefixes and recurrent ACKs for the bounded pilot."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

out = Path(sys.argv[1])
report = json.loads((out / 'report.json').read_text())
assert report['status'] == 'bounded_wave_incomplete'
assert report['action_counts'] == [20, 20] and not report['unstable_envs']
assert report['predictions'] == 2 and report['paid_calls'] == 0
worker = json.loads((out / 'intern-worker-result.json').read_text())
assert worker['native_calls_per_env'] == {'0': 2, '1': 2}
assert worker['actual_acks_per_env'] == {'0': 20, '1': 20}
assert worker['session_keys'] == [0, 1] and worker['pending_actions'] == {'0': 0, '1': 0}
rows = [json.loads(line) for line in (out / 'actions.jsonl').read_text().splitlines()]
assert len(rows) == 40
for idx in range(2):
    own = [row for row in rows if row['env_idx'] == idx]
    assert [row['step'] for row in own] == list(range(1, 21))
    for row in own:
        prediction = (row['step'] - 1) // 10
        prefix = (row['step'] - 1) % 10
        with np.load(out / f'prediction-{prediction:04d}.npz') as data:
            pos = data['env_ids'].tolist().index(idx)
            assert np.array_equal(data['actions'][pos, prefix], np.asarray(row['action'], np.float32))
for step in range(1, 21):
    path = out / f'source-ack-{step:04d}.npz'
    ack = json.loads(path.with_suffix('.json').read_text())
    assert ack['ack_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert ack['steps'] == {'0': step, '1': step}
    assert ack['source_pending_actions'] == {'0': (10 - step % 10) % 10, '1': (10 - step % 10) % 10}
    with np.load(path) as data:
        assert data['env_ids'].tolist() == [0, 1] and data['steps'].tolist() == [step, step]
        for camera in ('cam_high', 'cam_left_wrist', 'cam_right_wrist'):
            assert all(image.std() > 1 for image in data[camera])
        for idx in (0, 1):
            row = next(row for row in rows if row['step'] == step and row['env_idx'] == idx)
            assert np.array_equal(data['states'][idx].astype(np.float32), np.asarray(row['state'], np.float32))
result = {'status': 'bounded_native_intern_vector_audit_passed', 'actual_controls': 40,
    'per_env_actions': [20, 20], 'source_recurrent_acks_per_env': [20, 20],
    'source_predictions_equal_journal': True, 'separate_session_keys': True,
    'no_pending_actions': True, 'paid_calls': 0,
    'scope': 'two-env/two-prefix coexistence; not full horizon, long history or hierarchy qualification'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
