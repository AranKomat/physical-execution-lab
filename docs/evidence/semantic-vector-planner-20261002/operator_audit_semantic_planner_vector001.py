"""Native vector planner isolation, prompt routing and action contract audit."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_lab.audit import audit

out = Path(sys.argv[1])
report = json.loads((out / 'report.json').read_text())
assert not report['unstable_envs']
actions = [json.loads(line) for line in (out / 'actions.jsonl').read_text().splitlines()]
audits, identities, planner_episodes = {}, set(), set()
for idx, steps in enumerate(report['action_counts']):
    controller = out / 'episodes' / str(idx) / 'controller'
    audits[idx] = audit(controller)
    run = json.loads((controller / 'run.json').read_text())
    result = json.loads((controller / 'result.json').read_text())
    episode = run['initial_observation_sha256']
    assert episode not in identities
    identities.add(episode)
    assert result['metrics']['controller_faults'] == 0
    assert result['metrics']['unresolved_policy_actions'] == 0
    assert all(result['metrics'][key] == 0 for key in ('gpt_induced_motor_resamples',
        'gpt_induced_policy_resets', 'gpt_induced_prefix_shortening', 'semantic_recoveries'))
    events = [json.loads(line) for line in (controller / 'events.jsonl').read_text().splitlines()]
    proposals = [e['data'] for e in events if e['event'] == 'policy_proposal']
    acks = [e['data'] for e in events if e['event'] == 'control_ack']
    native = [row for row in actions if row['env_idx'] == idx]
    assert len(acks) == len(native) == steps
    assert [row['step'] for row in native] == list(range(1, steps + 1))
    assert len(proposals) == report['native_calls_per_env'][str(idx)] == (steps + 14) // 15
    for call, proposal in enumerate(proposals):
        with np.load(out / 'source-policy-proposals' / str(idx) / f'proposal_{call:06d}.npz') as source:
            expected = source['actions']
        actual = np.asarray([action['values'] for action in proposal['actions']], np.float32)
        assert expected.shape == actual.shape == (50, 14) and np.array_equal(expected, actual)
        assert proposal['step'] == call * 15 and proposal['natural_prefix_length'] == 15
        prediction = proposal['diagnostics']['vector_prediction_index']
        with np.load(out / f'request-{prediction:04d}.npz', allow_pickle=False) as request:
            row = request['env_ids'].tolist().index(idx)
            assert str(request['prompts'][row]) == proposal['diagnostics']['semantic']['effective_prompt']
            assert int(request['steps'][row]) == proposal['step']
    for ack, row in zip(acks, native):
        assert ack['step'] == row['step'] and ack['action']['values'] == row['action']
    requests = sorted((out / 'episodes' / str(idx) / 'planner').glob('*/request.json'))
    assert len(requests) == result['metrics']['semantic_calls']
    bound_episode = None
    for request_path in requests:
        request = json.loads(request_path.read_text())['chat_request']
        packet = json.loads(request['messages'][1]['content'][0]['text'])
        observation = packet['observation']
        assert set(observation) == {'episode', 'step', 'instruction', 'robot_state', 'eef',
            'control_hz', 'sensor_signals', 'observation_sha256'}
        assert observation['instruction'] == run['original_task']
        if bound_episode is None:
            bound_episode = observation['episode']
        assert observation['episode'] == bound_episode
        response = json.loads((request_path.parent / 'chat_response.json').read_text())
        decision = json.loads(response['choices'][0]['message']['tool_calls'][0]['function']['arguments'])
        assert decision['episode'] == bound_episode
        assert decision['based_on_stamp'] == observation['observation_sha256']
        assert decision['based_on_step'] == observation['step']
        assert response['model'] in ('gpt-6.1-sol', 'openai/gpt-6.1-sol')
        assert response['service_tier'] == 'flex'
    if bound_episode is not None:
        assert bound_episode not in planner_episodes
        planner_episodes.add(bound_episode)
    audits[idx]['source_H50_predictions_and_effective_request_prompts_equal'] = True
    audits[idx]['planner_episode_bindings_verified'] = len(requests)
    audits[idx]['status'] = result['status']
assert sum(row['planner_episode_bindings_verified'] for row in audits.values()) == report['paid_calls']
value = {'status': 'native_semantic_planner_vector_audit_passed', 'actual_controls': len(actions),
    'episodes': audits, 'paid_calls': report['paid_calls'],
    'scope': 'bounded native planner integration, not hierarchy benefit or full-horizon qualification'}
(out / 'offline-audit.json').write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(value))
