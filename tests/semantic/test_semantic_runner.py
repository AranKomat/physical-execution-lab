from dataclasses import replace
import json
from pathlib import Path
import numpy as np
import pytest
from k1lab.errors import ContractError
from k1lab.util import digest, load_json
from semantic_lab.synthetic import ToyEnvironment, ToyPolicy, ToyPlanner
from semantic_lab.policy import InstructionPolicy
from semantic_lab.runner import run_episode
from semantic_lab.contracts import SemanticDecision, Claim
from semantic_lab.audit import audit
from semantic_lab.report import aggregate, paired

CASE = dict(case_id='case', task='fixture', task_group='fixture', benchmark='synthetic', partition='dev')

def config(mode, prompt='original_only', **kw):
    return dict(name=mode + prompt, mode=mode, prompt_mode=prompt, max_semantic_calls=50,
        wall_limit_s=120, semantic_schedule=dict(review_interval_steps=6, minimum_dwell_steps=3,
        event_cooldown_steps=3), **kw)

def run(tmp_path, cfg, planner=None, env=None):
    env = env or ToyEnvironment(horizon=24)
    base = ToyPolicy()
    pol = InstructionPolicy(base, kind='test')
    result = run_episode(env, pol, planner, CASE, cfg, tmp_path)
    return result, env, base


def test_shadow_has_exact_motor_sequence_and_rng_calls(tmp_path):
    a, ae, ap = run(tmp_path / 'a', config('motor_only'))
    b, be, bp = run(tmp_path / 'b', config('semantic_shadow'), ToyPlanner())
    assert ae.actions == be.actions
    assert ap.steps == bp.steps == list(range(0, 24, 3))
    assert ap.acks == bp.acks == list(range(25))
    assert not ap.invalidations and not bp.invalidations
    assert b['metrics']['motor_prompt_changes'] == 0
    assert b['metrics']['semantic_calls'] > 0
    assert a['success'] and b['success']


def test_continue_parity_with_baseline(tmp_path):
    _, ae, ap = run(tmp_path / 'a', config('motor_only'))
    r, be, bp = run(tmp_path / 'b', config('semantic_subtask_hierarchy', 'task_plus_subtask'), ToyPlanner('continue'))
    assert ae.actions == be.actions and ap.steps == bp.steps
    assert r['metrics']['gpt_induced_prefix_shortening'] == 0
    assert audit(tmp_path / 'b')['prefix_cadence_verified']


def test_soft_event_never_interrupts_motor_prefix(tmp_path):
    planner = ToyPlanner()
    r, e, b = run(tmp_path, config('semantic_subtask_hierarchy', 'task_plus_subtask'), planner,
                  ToyEnvironment(24, soft_event=True))
    assert planner.calls[:2] == [0, 3]  # event at step 1 handled AFTER 3-step prefix
    assert b.steps == list(range(0, 24, 3))
    assert r['metrics']['abort_prefix_discards'] == 0


def test_call_budget_not_task_failure_or_native_success(tmp_path):
    cfg = config('semantic_subtask_hierarchy', 'subtask_only'); cfg['max_semantic_calls'] = 1
    r, _, b = run(tmp_path, cfg, ToyPlanner())
    assert r['status'] == 'resource_limited' and r['termination'] == 'semantic_call_budget'
    assert r['native_steps'] == 6 and r['native_score'] is None
    assert not b.invalidations


def test_terminal_mid_prefix_is_legal_not_semantic_shortening(tmp_path):
    r, _, b = run(tmp_path, config('motor_only'), env=ToyEnvironment(horizon=5))
    assert r['success'] and r['native_steps'] == 5
    assert r['metrics']['abort_prefix_discards'] == 1
    assert r['metrics']['unresolved_policy_actions'] == 0
    assert b.invalidations == ['native_terminal']
    assert audit(tmp_path)['actual_control_acks'] == 5


def test_planner_stop_is_not_native_success(tmp_path):
    class Stop(ToyPlanner):
        def decide(self, obs, state, reasons, receipt):
            return SemanticDecision(obs.episode, obs.step, obs.stamp, state.context.epoch,
                'stop', '', 'complete', 'Model thinks finished; not native truth.')
    r, _, b = run(tmp_path, config('semantic_subtask_hierarchy', 'subtask_only'), Stop())
    assert r['status'] == 'planner_stop_incomplete' and not r['success'] and not b.steps


def test_shadow_stop_does_not_stop_motor(tmp_path):
    class Stop(ToyPlanner):
        def decide(self, obs, state, reasons, receipt):
            return SemanticDecision(obs.episode, obs.step, obs.stamp, state.context.epoch,
                'stop', '', 'complete', 'Only a shadow assessment.')
    r, _, _ = run(tmp_path, config('semantic_shadow'), Stop())
    assert r['success'] and r['native_steps'] == 24


def test_controller_fault_stops_without_gpt_recovery(tmp_path):
    class Fault(ToyEnvironment):
        def obs(self):
            o = super().obs(); o.signals['controller_fault'] = self.step_id == 2; return o
    r, _, b = run(tmp_path, config('motor_only'), env=Fault())
    assert r['status'] == 'controller_fault' and r['native_steps'] == 2
    assert b.invalidations == ['controller_fault']


def test_no_native_rewards_in_planner_context(tmp_path):
    class AssertPlanner(ToyPlanner):
        def decide(self, obs, state, reasons, receipt):
            payload = json.dumps(dict(obs=obs.actor_state(), state=state.packet(), receipt=receipt))
            assert 'evaluator_secret' not in payload and 'native_score' not in payload
            return super().decide(obs, state, reasons, receipt)
    class Secret(ToyEnvironment):
        def obs(self):
            o = super().obs(); o.signals['evaluator_secret'] = 99; o.native['native_score'] = 1.; return o
    r, _, _ = run(tmp_path, config('semantic_subtask_hierarchy', 'subtask_only'), AssertPlanner(), Secret())
    assert r['success']


def test_ambiguous_ack_not_retried_or_counted_as_unexecuted(tmp_path):
    class Uncertain(ToyEnvironment):
        def step(self, action, correction=False):
            if self.step_id == 1:
                self.step_id += 1
                raise TimeoutError('may have moved')
            return super().step(action, correction)
    r, e, _ = run(tmp_path, config('motor_only'), env=Uncertain())
    assert r['status'] == 'infrastructure_or_contract_error'
    assert r['native_steps'] == 1 and e.step_id == 2
    assert r['metrics']['unresolved_policy_actions'] > 0


def test_stale_decision_is_not_applied(tmp_path):
    class Bad(ToyPlanner):
        def decide(self, obs, state, reasons, receipt):
            return replace(super().decide(obs, state, reasons, receipt), expected_epoch=9)
    r, _, b = run(tmp_path, config('semantic_subtask_hierarchy', 'subtask_only'), Bad())
    assert r['status'] == 'infrastructure_or_contract_error' and not b.steps


def test_report_retains_missing_and_rejects_duplicates(tmp_path):
    r, _, _ = run(tmp_path, config('motor_only'))
    cases = [CASE, dict(CASE, case_id='missing')]
    s, indexed = aggregate(cases, [r], [r['condition']])
    assert s[r['condition']]['success_rate_full_denominator'] == .5
    assert s[r['condition']]['missing'] == 1
    with pytest.raises(ContractError): aggregate(cases, [r, r], [r['condition']])


def test_auditor_rejects_tampered_chain(tmp_path):
    run(tmp_path, config('motor_only'))
    path = tmp_path / 'events.jsonl'; text = path.read_text(); path.write_text(text.replace('natural_boundary', 'shorten', 1))
    with pytest.raises(ContractError): audit(tmp_path)


def test_async_flag_is_not_silently_enabled(tmp_path):
    with pytest.raises(ContractError): run(tmp_path, config('motor_only', async_planner=True))


def test_known_physical_ack_survives_policy_transport_failure(tmp_path):
    class AckFailure(ToyPolicy):
        def observe(self, obs):
            if obs.step == 1: raise TimeoutError('model observation acknowledgement lost')
            super().observe(obs)
    env=ToyEnvironment(); pol=InstructionPolicy(AckFailure(),kind='test')
    r=run_episode(env,pol,None,CASE,config('motor_only'),tmp_path)
    assert r['status']=='infrastructure_or_contract_error' and r['native_steps']==1
    assert audit(tmp_path)['actual_control_acks']==1
