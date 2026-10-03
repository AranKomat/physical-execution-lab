"""Audit retained prefixes/ACKs without inventing results for interrupted episodes."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.journal import verify
from k1lab.util import digest, file_sha
from semantic_lab.contracts import SemanticContext, SemanticDecision, ScheduleConfig
from semantic_lab.motor_contract import motor_contract

run, output = map(Path, sys.argv[1:])
parent = json.loads((run / 'report.json').read_text())
assert parent['method'] == 'semantic'
contract = motor_contract(parent['policy'])
rows = []
for group in sorted(run.glob('group[0-9]')):
    commands = [json.loads(s) for s in (group / 'actions.jsonl').read_text().splitlines()]
    for path in sorted(group.glob('episodes/*/controller/run.json')):
        controller = path.parent
        idx = int(controller.parent.name)
        metadata = json.loads(path.read_text())
        case = metadata['case']
        config = metadata['config']
        schedule = ScheduleConfig(**config['semantic_schedule'])
        context = SemanticContext(metadata['original_task'], prompt_mode=config['prompt_mode'])
        chain = verify(controller / 'events.jsonl')
        events = [json.loads(s) for s in (controller / 'events.jsonl').read_text().splitlines()]
        acks, proposals, decisions = [], [], []
        opened = None
        for event in events:
            data = event['data']
            if event['event'] == 'semantic_decision':
                assert opened is None
                decision = SemanticDecision.from_wire(data['decision'])
                assert decision.based_on_step == data['step'] == len(acks)
                assert decision.expected_epoch == context.epoch
                assert not data['native_evaluator_information_supplied']
                if schedule.mistake_only_coaching:
                    assert decision.operation in ('continue', 'recover', 'clear_feedback', 'stop')
                    if decision.operation == 'recover':
                        assert schedule.allow_semantic_recovery and decision.assessment == 'failed'
                    if decision.operation == 'clear_feedback':
                        assert context.subtask and decision.assessment == 'complete'
                    if decision.operation in ('recover', 'clear_feedback'):
                        assert data['effect']['changed'] == (decision.subtask != context.subtask)
                if decision.operation == 'continue':
                    assert decision.subtask in ('', context.subtask)
                if data['effect']['changed']:
                    assert decision.operation in ('recover', 'set_subtask', 'clear_feedback')
                    context = SemanticContext(context.original_task, decision.subtask,
                        context.epoch + 1, context.prompt_mode)
                decisions.append(data)
            if event['event'] == 'policy_proposal':
                assert opened is None and data['step'] == len(acks)
                assert data['natural_prefix_length'] == contract['execute']
                sem = data['diagnostics']['semantic']
                assert SemanticContext(**sem['context']) == context
                assert sem['effective_prompt'] == context.effective_prompt
                assert sem['effective_prompt_sha256'] == digest(context.effective_prompt)
                assert sem['context_sha256'] == context.identity and not sem['history_reset']
                values = np.asarray([a['values'] for a in data['actions']], np.float32)
                with np.load(group / 'source-policy-proposals' / str(idx) /
                             f'proposal_{len(proposals):06d}.npz') as source:
                    assert np.array_equal(values, source['actions'])
                    assert values.shape == (contract['returned'], 14)
                prediction = data['diagnostics']['vector_prediction_index']
                with np.load(group / f'request-{prediction:04d}.npz', allow_pickle=False) as request:
                    row = request['env_ids'].tolist().index(idx)
                    assert str(request['prompts'][row]) == context.effective_prompt
                    assert int(request['steps'][row]) == data['step']
                record = json.loads((group / f'prediction-{prediction:04d}.json').read_text())
                row = record['env_ids'].index(idx)
                retention = record['live_prompt_retention'][row]
                assert retention['entire_cleaned_prompt_present']
                assert retention['prompt_sha256'] == hashlib.sha256(context.effective_prompt.encode()).hexdigest()
                assert record['inference_mode'] == contract['mode']
                if parent['policy'] == 'g05':
                    assert record['observation_history_steps'] == 1
                    assert record['history_resets_during_episode'] == 0
                    with np.load(group / f'prediction-{prediction:04d}.npz', allow_pickle=False) as source:
                        expected = source['raw_actions'][row].astype(np.float32)
                        expected[:, [6, 13]] = np.clip(expected[:, [6, 13]], 0, 1)
                        assert np.array_equal(expected, source['actions'][row])
                        assert np.array_equal(expected, values)
                opened = dict(actions=data['actions'], executed=0)
                proposals.append(data)
            if event['event'] == 'control_ack':
                assert opened is not None and data['step'] == len(acks) + 1
                assert data['action'] == opened['actions'][opened['executed']]
                opened['executed'] += 1
                acks.append(data)
            if event['event'] == 'motor_prefix_receipt':
                assert opened is not None and data['executed_steps'] == opened['executed']
                if data['stop_reason'] == 'natural_boundary':
                    assert opened['executed'] == contract['execute']
                opened = None
        emitted = [c for c in commands if c['env_idx'] == idx]
        assert len(emitted) == len(acks)
        for ack, command in zip(acks, emitted):
            assert ack['step'] == command['step'] and ack['action']['values'] == command['action']
        result_path = controller / 'result.json'
        result = json.loads(result_path.read_text()) if result_path.exists() else None
        terminal = result is not None and result['status'] == 'native_completed'
        if result:
            assert result['native_steps'] == len(acks)
        if terminal:
            assert emitted[-1]['ended'] and emitted[-1]['success'] == result['success']
        rows.append(dict(case_id=case['case_id'], task=case['task'], journal=chain,
            native_actions=len(acks), proposals=len(proposals), prefix_open_at_end=opened is not None,
            completed_native_result=terminal, result_status=result['status'] if result else 'missing',
            success=result['success'] if terminal else None,
            native_score=result['native_score'] if terminal else None,
            decisions=len(decisions), correction_changes=sum(d['decision']['operation'] == 'recover'
                and d['effect']['changed'] for d in decisions),
            feedback_clears=sum(d['decision']['operation'] == 'clear_feedback' for d in decisions),
            decisions_evidence=decisions))
assert len(rows) == 10 and {r['case_id'] for r in rows} == set(parent['cases'])
value = dict(retained_trace_integrity_passed=True, completed_comparison=False,
    scope='retained source predictions, actual model prompts, observed ACKs and decision gates only',
    parent_report_sha256=file_sha(run / 'report.json'), rows=rows,
    native_actions=sum(r['native_actions'] for r in rows),
    completed_native_results=sum(r['completed_native_result'] for r in rows),
    known_successes=sum(r['success'] is True for r in rows),
    missing_native_scores=sum(r['native_score'] is None for r in rows),
    correction_changes=sum(r['correction_changes'] for r in rows),
    feedback_clears=sum(r['feedback_clears'] for r in rows))
assert not output.exists()
output.write_text(json.dumps(value, indent=2) + '\n')
print(json.dumps({k: v for k, v in value.items() if k != 'rows'}))
