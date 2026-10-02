"""Audit the zero-API native semantic-loop pilot against source predictions."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_lab.audit import audit

out = Path(sys.argv[1])
report = json.loads((out / 'report.json').read_text())
assert report['paid_calls'] == 0 and not report['unstable_envs']
assert report['inference_mode'] == 'native_singleton'
actions = [json.loads(line) for line in (out / 'actions.jsonl').read_text().splitlines()]
audits = {}
for idx, steps in enumerate(report['action_counts']):
    controller = out / 'episodes' / str(idx) / 'controller'
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
    assert len(set(prompts)) == 1
    for ack, row in zip(acks, native):
        assert ack['step'] == row['step']
        assert ack['action']['values'] == row['action']
    audits[idx]['source_H50_predictions_equal'] = True
result = {'status': 'native_semantic_motor_vector_audit_passed', 'actual_controls': len(actions),
    'episodes': audits, 'paid_calls': 0, 'source_predictions_and_native_acks_match': True,
    'scope': 'motor-only native semantic adapter; not paid planner or hierarchy qualification'}
(out / 'offline-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
