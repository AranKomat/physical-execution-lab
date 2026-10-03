"""Subtask-only offline audit; no robot actions, calls, or outcome tuning."""
import json
import hashlib
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_lab.audit import audit
from semantic_lab.contracts import SemanticContext
from k1lab.util import digest, file_sha

run = Path(sys.argv[1])
parent = json.loads((run / 'report.json').read_text())
assert parent['method'] == 'semantic'
rows = []
seen = set()
for group in sorted(run.glob('group[0-9]')):
    report = json.loads((group / 'report.json').read_text())
    binding = json.loads((group / 'pre-action-admission.json').read_text())
    assert binding['passed']
    assert json.loads((group / 'cohort-admitted.json').read_text())['all_ten_reset_bindings_passed']
    commands = [json.loads(s) for s in (group / 'actions.jsonl').read_text().splitlines()]
    for idx, result in report['controller_results'].items():
        controller = group / 'episodes' / idx / 'controller'
        checks = audit(controller)
        metadata = json.loads((controller / 'run.json').read_text())
        assert result == json.loads((controller / 'result.json').read_text())
        assert result['case_id'] not in seen
        seen.add(result['case_id'])
        assert result['policy_identity'] is not None
        assert metadata['config']['prompt_mode'] == 'subtask_only'
        assert metadata['config']['semantic_schedule']['allow_semantic_recovery'] is False
        events = [json.loads(s) for s in (controller / 'events.jsonl').read_text().splitlines()]
        proposals = [e['data'] for e in events if e['event'] == 'policy_proposal']
        acks = [e['data'] for e in events if e['event'] == 'control_ack']
        emitted = [c for c in commands if c['env_idx'] == int(idx)]
        assert len(acks) == len(emitted) == result['native_steps']
        assert len(proposals) == result['metrics']['policy_calls']
        for call, proposal in enumerate(proposals):
            assert proposal['step'] == call * 15
            assert proposal['natural_prefix_length'] == 15
            values = np.asarray([a['values'] for a in proposal['actions']], np.float32)
            with np.load(group / 'source-policy-proposals' / idx / f'proposal_{call:06d}.npz') as source:
                assert values.shape == source['actions'].shape == (50, 14)
                assert np.array_equal(values, source['actions'])
            sem = proposal['diagnostics']['semantic']
            context = SemanticContext(**sem['context'])
            assert context.prompt_mode == 'subtask_only'
            assert context.original_task == metadata['original_task']
            assert context.effective_prompt == sem['effective_prompt']
            assert context.effective_prompt == (context.subtask or context.original_task)
            assert digest(sem['effective_prompt']) == sem['effective_prompt_sha256']
            assert context.identity == sem['context_sha256']
            assert sem['history_reset'] is False
            prediction = proposal['diagnostics']['vector_prediction_index']
            with np.load(group / f'request-{prediction:04d}.npz', allow_pickle=False) as request:
                row = request['env_ids'].tolist().index(int(idx))
                assert str(request['prompts'][row]) == context.effective_prompt
                assert int(request['steps'][row]) == proposal['step']
            prediction_record = json.loads((group / f'prediction-{prediction:04d}.json').read_text())
            token_row = prediction_record['env_ids'].index(int(idx))
            retention = prediction_record['live_prompt_retention'][token_row]
            assert retention['entire_cleaned_prompt_present'] is True
            assert retention['prompt_sha256'] == hashlib.sha256(context.effective_prompt.encode()).hexdigest()
            assert 0 < retention['active_tokens'] <= retention['token_limit'] == 200
        for ack, command in zip(acks, emitted):
            assert ack['step'] == command['step']
            assert ack['action']['space'] == 'x5_joint14'
            assert ack['action']['values'] == command['action']
        for key in ('gpt_induced_motor_resamples', 'gpt_induced_policy_resets',
                    'gpt_induced_prefix_shortening', 'corrections', 'unresolved_policy_actions'):
            assert result['metrics'][key] == 0, (result['case_id'], key)
        planner_requests = sorted((controller.parent / 'planner').glob('*/request.json'))
        assert len(planner_requests) == result['metrics']['semantic_calls']
        for path in planner_requests:
            request = json.loads(path.read_text())['chat_request']
            packet = json.loads(request['messages'][1]['content'][0]['text'])
            obs = packet['observation']
            assert obs['instruction'] == metadata['original_task']
            assert set(obs) == {'episode', 'step', 'instruction', 'robot_state', 'eef',
                                'control_hz', 'sensor_signals', 'observation_sha256'}
            assert request['tools'][0]['function']['name'] == 'semantic_goal'
            props = request['tools'][0]['function']['parameters']['properties']
            assert all(props[k]['enum'] == [v] for k, v in packet['request_binding'].items())
        if result['status'] == 'native_completed':
            assert emitted[-1]['ended']
            assert emitted[-1]['success'] == result['success']
        rows.append(dict(case_id=result['case_id'], status=result['status'],
            termination=result['termination'], native_steps=result['native_steps'],
            native_score=result['native_score'], success=result['success'], error=result['error'],
            journal_checks=checks, planner_requests=len(planner_requests),
            motor_predictions_checked=len(proposals),
            actual_model_request_prompts_verified=bool(proposals),
            source_predictions_and_native_acks_equal=True))
assert seen == set(parent['cases']) and len(rows) == 10
value = dict(integrity_passed=True, benchmark_qualified=False, prompt_mode='subtask_only',
    scope='all-ten admission, prompt boundary, prefix cadence, source predictions and native ACK integrity',
    raw_parent_report_sha256=file_sha(run / 'report.json'), rows=rows,
    native_actions=sum(r['native_steps'] for r in rows),
    semantic_calls=sum(r['planner_requests'] for r in rows),
    native_terminal_cases=sum(r['status'] == 'native_completed' for r in rows),
    episodes_with_motor_prompt_evidence=sum(r['motor_predictions_checked'] > 0 for r in rows),
    successes=sum(r['success'] for r in rows),
    missing_native_scores=sum(r['native_score'] is None for r in rows))
output = Path(sys.argv[2])
assert not output.exists()
output.write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps(value))
