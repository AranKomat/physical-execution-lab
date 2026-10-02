"""Audit the zero-API native semantic-loop pilot against source predictions."""
import json
import hashlib
from pathlib import Path
import sys
import numpy as np
import jax

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_lab.audit import audit

out = Path(sys.argv[1])
report = json.loads((out / 'report.json').read_text())
assert report['paid_calls'] == 0 and not report['unstable_envs']
assert report['inference_mode'] == 'native_singleton'
binding = json.loads((out / 'pre-action-binding.json').read_text())
for path, expected in binding['sources'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
assert binding['report']['reference_cases'] == report['reference_cases']
assert [row['layout_id'] for row in report['reference_cases']] == report['reset_seeds']
assert len({row['case_id'] for row in report['reference_cases']}) == report['requested_envs']
assert all(row['layout_sha256'] == actual['sha256'] for row, actual in
    zip(report['reference_cases'], report['layout_bindings']))
assert all(sum(report['native_registration']['condition_group_counts'][name][idx]
    for name in ('check_list', 'final_check_list', 'trigger_check_list')) > 0
    for idx in range(report['requested_envs']))
actions = [json.loads(line) for line in (out / 'actions.jsonl').read_text().splitlines()]
audits = {}
for idx, steps in enumerate(report['action_counts']):
    controller = out / 'episodes' / str(idx) / 'controller'
    run = json.loads((controller / 'run.json').read_text())
    final = report['controller_results'][str(idx)]
    assert final['case_id'] == report['reference_cases'][idx]['case_id']
    assert final['partition'] == report['reference_cases'][idx]['partition']
    assert final['metrics']['controller_faults'] == final['metrics']['unresolved_policy_actions'] == 0
    assert final['status'] == 'native_completed' and final['native_terminal_observed']
    assert np.isclose(final['simulated_seconds'] * report['reference_cases'][idx]['native_hz'], steps)
    audits[idx] = audit(controller)
    events = [json.loads(line) for line in (controller / 'events.jsonl').read_text().splitlines()]
    proposals = [e['data'] for e in events if e['event'] == 'policy_proposal']
    acks = [e['data'] for e in events if e['event'] == 'control_ack']
    native = [row for row in actions if row['env_idx'] == idx]
    assert len(acks) == len(native) == steps
    assert [row['step'] for row in native] == list(range(1, steps + 1))
    assert len(proposals) == report['native_calls_per_env'][str(idx)] == (steps + 14) // 15
    assert not any(e['event'] == 'semantic_decision' for e in events)
    prompts = []
    for call, proposal in enumerate(proposals):
        with np.load(out / 'source-policy-proposals' / str(idx) / f'proposal_{call:06d}.npz') as source:
            expected = source['actions']
        actual = np.asarray([action['values'] for action in proposal['actions']], np.float32)
        assert expected.shape == actual.shape == (50, 14)
        assert np.array_equal(expected, actual)
        assert proposal['step'] == call * 15
        assert proposal['natural_prefix_length'] == 15
        prompts.append(proposal['diagnostics']['semantic']['effective_prompt'])
        prediction = proposal['diagnostics']['vector_prediction_index']
        with np.load(out / f'request-{prediction:04d}.npz', allow_pickle=False) as data:
            row = data['env_ids'].tolist().index(idx)
            assert int(data['steps'][row]) == call * 15
            assert str(data['prompts'][row]) == run['original_task'] == prompts[-1]
            assert all(data[key][row].std() > 1 for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist'))
    assert len(set(prompts)) == 1
    for ack, row in zip(acks, native):
        assert ack['step'] == row['step']
        assert ack['action']['values'] == row['action']
    audits[idx]['source_H50_predictions_equal'] = True
    key = jax.random.key(0)
    for _ in proposals:
        key, _ = jax.random.split(key)
    last = json.loads((out / f'prediction-{report["predictions"]-1:04d}.json').read_text())
    assert last['rng_keys_after'][str(idx)] == jax.random.key_data(key).tolist()
    audits[idx]['source_rng_verified'] = True
result = {'status': 'native_semantic_motor_vector_audit_passed', 'actual_controls': len(actions),
    'episodes': audits, 'paid_calls': 0, 'source_predictions_and_native_acks_match': True,
    'case_layout_variant_horizon_binding_verified': True,
    'scope': 'reference-bound previously opened task; not untouched held-out or hierarchy qualification'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
