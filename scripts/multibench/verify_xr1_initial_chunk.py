#!/usr/bin/env python3
"""Replay one legal initial observation through the official client; no motion."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.journal import verify
from k1lab.multibench.adapters.robocasa import load_evaluator
from k1lab.util import atomic_json, file_sha, load_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('episode-root', 'xiaomi-root', 'checkpoint-dir', 'output'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--port', type=int, required=True)
    a = p.parse_args()
    episode = Path(a.episode_root)
    chain = verify(episode / 'events.jsonl')
    with (episode / 'events.jsonl').open() as stream:
        proposal = next(json.loads(line)['data'] for line in stream
                        if json.loads(line)['event'] == 'policy_proposal')
    if proposal['step'] != 0:
        raise ValueError('initial chunk required')
    state = load_json(episode / 'observations/000000/state.json')
    helper = load_evaluator(a.xiaomi_root)
    # Reconstruct only the initial public sensor history, never simulator state.
    with np.load(episode / 'observations/000000/sensors.npz', allow_pickle=False) as sensors:
        states = np.repeat(sensors['state'][None], 4, axis=0)
        images = {key: np.repeat(sensors[key][None], 4, axis=0)
                  for key in helper.CAMERA_KEYS}
    client = helper.EvalClient(a.checkpoint_dir, '127.0.0.1', a.port, 'robocasa365', .95)
    try:
        actual = client.infer(states, images, state['instruction'])
    finally:
        client.close()
    expected = np.asarray([row['values'] for row in proposal['actions']], dtype=np.float32)
    prefix = actual[:len(expected)]
    if prefix.shape != expected.shape or not np.isfinite(prefix).all():
        raise ValueError('invalid official prefix')
    error = float(np.max(np.abs(prefix - expected)))
    passed = bool(np.allclose(prefix, expected, atol=1e-6, rtol=0))
    atomic_json(a.output, {'scope': 'initial legal-observation client/preprocessing/prefix parity only',
        'episode_root': str(episode), 'journal': chain,
        'sensor_sha256': file_sha(episode / 'observations/000000/sensors.npz'),
        'initial_observation_sha256': state['observation_sha256'],
        'required_fresh_server_seed': 7, 'actual_source_horizon': len(actual),
        'compared_prefix': len(expected), 'max_abs_error': error,
        'atol': 1e-6, 'rtol': 0, 'passed': passed,
        'physical_actions': 0, 'paid_calls': 0}, exclusive=True)
    if not passed:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
