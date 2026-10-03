import json

import pytest

from k1lab.errors import ContractError
from semantic_lab.contracts import ScheduleConfig, SemanticContext
from semantic_lab.planner import COACHING_SYSTEM, SemanticPlanner, tool_schema
from semantic_lab.policy import InstructionPolicy
from semantic_lab.runner import run_episode
from semantic_lab.state import SemanticState
from semantic_lab.synthetic import ToyEnvironment, ToyPolicy
from tests.semantic.test_semantic_contracts import decision


def coaching_state(obs):
    state = SemanticState(obs.instruction, 'task_plus_correction',
        ScheduleConfig(allow_semantic_recovery=True, mistake_only_coaching=True))
    state.observe(obs)
    return state


def test_original_bytes_and_correct_clear_cycle():
    obs = ToyEnvironment().obs()
    state = coaching_state(obs)
    original = state.context
    state.apply(decision(obs, operation='continue', subtask='', assessment='uncertain'), obs)
    assert state.context is original
    state.apply(decision(obs, operation='recover', assessment='failed'), obs)
    assert state.context.effective_prompt == obs.instruction + '\n\nCorrection:\nPick up an object.'
    state.apply(decision(obs, epoch=1, operation='clear_feedback', subtask='', assessment='complete'), obs)
    assert state.context.epoch == 2 and state.context.effective_prompt == obs.instruction
    task = '  Original bytes\nwith spaces. '
    assert SemanticContext(task, prompt_mode='task_plus_correction').effective_prompt == task


@pytest.mark.parametrize('operation,assessment,subtask', [
    ('set_subtask', 'progressing', 'Do another stage'),
    ('recover', 'uncertain', 'An error might happen'),
    ('recover', 'progressing', 'Prevent a future error'),
    ('clear_feedback', 'complete', ''),
])
def test_reject_proactive_or_unfounded_feedback(operation, assessment, subtask):
    obs = ToyEnvironment().obs(); state = coaching_state(obs)
    with pytest.raises(ContractError):
        state.apply(decision(obs, operation=operation, assessment=assessment, subtask=subtask), obs)
    assert state.context.epoch == 0


def test_uncertain_cannot_clear_active_feedback_and_legacy_cannot_clear():
    obs = ToyEnvironment().obs(); state = coaching_state(obs)
    state.apply(decision(obs, operation='recover', assessment='failed'), obs)
    with pytest.raises(ContractError):
        state.apply(decision(obs, epoch=1, operation='clear_feedback', subtask='', assessment='uncertain'), obs)
    assert state.context.epoch == 1
    with pytest.raises(ContractError):
        SemanticState(obs.instruction, 'original_only').apply(
            decision(obs, operation='clear_feedback', subtask='', assessment='complete'), obs)


@pytest.mark.parametrize('mode,schedule', [
    ('task_plus_correction', ScheduleConfig()),
    ('subtask_only', ScheduleConfig(allow_semantic_recovery=True, mistake_only_coaching=True)),
])
def test_coaching_mode_is_explicit(mode, schedule):
    with pytest.raises(ContractError): SemanticState('Task', mode, schedule)


def test_coaching_schedule_requires_real_boolean_and_recovery():
    with pytest.raises(ContractError): ScheduleConfig(mistake_only_coaching=True)
    with pytest.raises(ContractError): ScheduleConfig(mistake_only_coaching='yes')


def test_planner_uses_coaching_system_and_bound_narrow_schema(tmp_path):
    obs = ToyEnvironment().obs(); state = coaching_state(obs)
    answer = decision(obs, operation='continue', subtask='', assessment='progressing')
    class Client:
        def post(self, _, headers, json):
            self.payload = json
            class Response:
                def json(self):
                    return {'choices': [{'message': {'tool_calls': [{'function': {
                        'name': 'semantic_goal', 'arguments': __import__('json').dumps(answer.wire())}}]}}]}
            return Response()
    client = Client()
    planner = SemanticPlanner({'model': 'test'}, tmp_path, client=client)
    assert planner.decide(obs, state, [], None) == answer
    assert client.payload['messages'][0]['content'] == COACHING_SYSTEM
    props = client.payload['tools'][0]['function']['parameters']['properties']
    assert props['operation']['enum'] == ['continue', 'recover', 'clear_feedback', 'stop']
    assert props['expected_epoch']['enum'] == [0]
    assert 'set_subtask' in tool_schema()['function']['parameters']['properties']['operation']['enum']


def test_no_error_coaching_preserves_actual_motor_stream(tmp_path):
    class ContinuePlanner:
        def reset(self): pass
        def close(self): pass
        def decide(self, obs, state, reasons, receipt):
            return decision(obs, epoch=state.context.epoch, operation='continue', subtask='')
    case = dict(case_id='c', task='t', task_group='t', benchmark='synthetic', partition='dev')
    schedule = dict(review_interval_steps=3, minimum_dwell_steps=3, event_cooldown_steps=3,
                    allow_semantic_recovery=True, mistake_only_coaching=True)
    cfg = dict(name='coaching', mode='semantic_subtask_hierarchy', prompt_mode='task_plus_correction',
               semantic_schedule=schedule)
    results = []
    for name, config, planner in [('coaching', cfg, ContinuePlanner()),
            ('baseline', dict(name='baseline', mode='motor_only', prompt_mode='original_only'), None)]:
        results.append(run_episode(ToyEnvironment(horizon=12),
            InstructionPolicy(ToyPolicy(), kind='test'), planner, case, config, tmp_path / name))
    def stream(name):
        events = [json.loads(line) for line in (tmp_path / name / 'events.jsonl').read_text().splitlines()]
        return [(e['data']['step'], e['data']['action']) for e in events if e['event'] == 'control_ack']
    assert stream('coaching') == stream('baseline')
    assert results[0]['metrics']['semantic_calls'] == 4
    for key in ('motor_prompt_changes', 'semantic_changes', 'gpt_induced_motor_resamples',
                'gpt_induced_policy_resets', 'gpt_induced_prefix_shortening'):
        assert results[0]['metrics'][key] == 0
    assert results[0]['metrics']['policy_calls'] == results[1]['metrics']['policy_calls'] == 4


def test_correction_clear_at_drained_boundaries_preserves_ack_history(tmp_path):
    from semantic_lab.audit import audit
    class Planner:
        def reset(self): pass
        def close(self): pass
        def decide(self, obs, state, reasons, receipt):
            if obs.step == 3:
                return decision(obs, operation='recover', assessment='failed')
            if obs.step == 6:
                return decision(obs, epoch=1, operation='clear_feedback', subtask='', assessment='complete')
            return decision(obs, epoch=state.context.epoch, operation='continue', subtask='')
    base = ToyPolicy()
    result = run_episode(ToyEnvironment(horizon=12), InstructionPolicy(base, kind='test'), Planner(),
        dict(case_id='c', task='t', task_group='t', benchmark='synthetic', partition='dev'),
        dict(name='cycle', mode='semantic_subtask_hierarchy', prompt_mode='task_plus_correction',
             semantic_schedule=dict(review_interval_steps=3, minimum_dwell_steps=30,
                 allow_semantic_recovery=True, mistake_only_coaching=True)), tmp_path)
    assert result['status'] == 'native_completed'
    assert base.acks == list(range(13)) and not base.invalidations
    assert base.prompts == ['Move the test actuator to its goal.',
        'Move the test actuator to its goal.\n\nCorrection:\nPick up an object.',
        'Move the test actuator to its goal.', 'Move the test actuator to its goal.']
    assert result['metrics']['semantic_recoveries'] == 1
    assert result['metrics']['motor_prompt_changes'] == 2
    assert audit(tmp_path)['actual_control_acks'] == 12
