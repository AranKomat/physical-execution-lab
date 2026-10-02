from dataclasses import replace
import pytest
from k1lab.errors import ContractError
from semantic_lab.contracts import SemanticContext, SemanticDecision, Claim, ScheduleConfig, check_decision
from semantic_lab.state import SemanticState
from semantic_lab.synthetic import ToyEnvironment
from semantic_lab.mailbox import SemanticMailbox


def decision(obs, epoch=0, operation='set_subtask', subtask='Pick up an object.', **kw):
    args = dict(episode=obs.episode, based_on_step=obs.step, based_on_stamp=obs.stamp,
                expected_epoch=epoch, operation=operation, subtask=subtask,
                assessment='progressing', evidence='Current observation supports this language goal.')
    args.update(kw)
    return SemanticDecision(**args)


def test_original_bytes_preserved():
    task = '  Original instruction\nwith spaces. '
    assert SemanticContext(task, 'ignored', 1).effective_prompt == task

@pytest.mark.parametrize('mode,expected', [('original_only', 'Task'), ('subtask_only', 'Goal'),
    ('task_plus_subtask', 'Overall task:\nTask\n\nCurrent subtask:\nGoal')])
def test_prompt_modes(mode, expected):
    assert SemanticContext('Task', 'Goal', 1, mode).effective_prompt == expected

@pytest.mark.parametrize('mode', ['original_only', 'subtask_only', 'task_plus_subtask'])
def test_empty_subtask_falls_back(mode):
    assert SemanticContext('Task', prompt_mode=mode).effective_prompt == 'Task'

@pytest.mark.parametrize('kwargs', [{'epoch': -1}, {'epoch': True}, {'prompt_mode': 'magic'},
    {'original_task': ''}, {'subtask': 'a' * 601}])
def test_context_rejects_bad_fields(kwargs):
    args = {'original_task': 'Task'}; args.update(kwargs)
    with pytest.raises(ContractError): SemanticContext(**args)

@pytest.mark.parametrize('key,value', [('operation', 'shorten'), ('operation', 'correct'),
    ('expected_epoch', -1), ('expected_epoch', True), ('based_on_step', -1),
    ('assessment', 'native_success'), ('evidence', ''), ('subtask', 'x' * 601)])
def test_decision_validation(key, value):
    obs = ToyEnvironment().obs()
    with pytest.raises(ContractError): decision(obs, **{key: value})

def test_wire_roundtrip_and_forbidden_action_fields():
    obs = ToyEnvironment().obs(); d = decision(obs, completed_claims=(Claim('Something observed', (0,)),))
    assert SemanticDecision.from_wire(d.wire()) == d
    with pytest.raises(ContractError): SemanticDecision.from_wire(d.wire() | {'actions': [[0] * 14]})

@pytest.mark.parametrize('op', ['continue', 'stop'])
def test_continue_cannot_rewrite_goal(op):
    with pytest.raises(ContractError): decision(ToyEnvironment().obs(), operation=op)

def test_future_evidence_rejected():
    with pytest.raises(ContractError): decision(ToyEnvironment().obs(), completed_claims=(Claim('done', (1,)),))

def test_stale_epoch_and_observation():
    obs = ToyEnvironment().obs(); ctx = SemanticContext(obs.instruction)
    with pytest.raises(ContractError): check_decision(decision(obs, epoch=1), obs, ctx)
    with pytest.raises(ContractError): check_decision(replace(decision(obs), based_on_stamp='a' * 64), obs, ctx)
    with pytest.raises(ContractError): check_decision(replace(decision(obs), episode='other'), obs, ctx)


def test_continue_is_identity_no_goal_rephrase():
    obs = ToyEnvironment().obs(); state = SemanticState(obs.instruction, 'task_plus_subtask')
    state.observe(obs); state.apply(decision(obs), obs)
    ctx = state.context
    state.apply(decision(obs, epoch=1, operation='continue', subtask=''), obs)
    assert state.context is ctx


def test_goal_minimum_dwell_and_recovery():
    env = ToyEnvironment(); obs = env.obs()
    s = SemanticState(obs.instruction, 'task_plus_subtask', ScheduleConfig(allow_semantic_recovery=True))
    s.observe(obs); s.apply(decision(obs), obs)
    env.step_id = 5; now = env.obs(); s.observe(now)
    rejected = s.apply(decision(now, epoch=1, subtask='Open container.'), now)
    assert rejected['deferred'] == 'minimum_semantic_dwell'
    accepted = s.apply(decision(now, epoch=1, operation='recover', subtask='Release the object.', assessment='failed'), now)
    assert accepted['changed'] and s.context.epoch == 2


def test_recovery_default_disabled():
    obs = ToyEnvironment().obs(); s = SemanticState(obs.instruction, 'subtask_only')
    s.observe(obs)
    with pytest.raises(ContractError): s.apply(decision(obs, operation='recover', assessment='failed'), obs)


def test_memory_retractable_not_append_only():
    env = ToyEnvironment(); obs = env.obs(); s = SemanticState(obs.instruction, 'subtask_only')
    s.observe(obs); s.apply(decision(obs, completed_claims=(Claim('Object held', (0,)),)), obs)
    env.step_id = 30; obs = env.obs(); s.observe(obs)
    s.apply(decision(obs, epoch=1, operation='continue', subtask='',
                     uncertain_or_invalidated=('Object holding no longer established',)), obs)
    assert not s.memory['completed_claims'] and s.memory['uncertain_or_invalidated']


def test_mailbox_requires_drained_prefix_and_current_epoch():
    env = ToyEnvironment(); old = env.obs(); ctx = SemanticContext(old.instruction)
    box = SemanticMailbox(max_age_steps=10); box.submit(old, ctx); box.complete(decision(old))
    with pytest.raises(ContractError): box.take_at_boundary(old, ctx, prefix_drained=False)
    env.step_id = 4
    assert box.take_at_boundary(env.obs(), ctx, prefix_drained=True).based_on_step == 0
    box.submit(old, ctx); box.complete(decision(old)); env.step_id = 11
    with pytest.raises(ContractError): box.take_at_boundary(env.obs(), ctx, prefix_drained=True)


def test_mailbox_no_second_inflight_request_or_foreign_reply():
    obs = ToyEnvironment().obs(); ctx = SemanticContext(obs.instruction); box = SemanticMailbox()
    box.submit(obs, ctx)
    with pytest.raises(ContractError): box.submit(obs, ctx)
    with pytest.raises(ContractError): box.complete(decision(obs, epoch=1))

@pytest.mark.parametrize('key,value', [('review_interval_steps', 0), ('minimum_dwell_steps', -1),
    ('event_cooldown_steps', True), ('allow_semantic_recovery', 'yes')])
def test_schedule_validation(key, value):
    with pytest.raises(ContractError): ScheduleConfig(**{key: value})
