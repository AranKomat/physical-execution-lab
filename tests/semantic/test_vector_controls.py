from dataclasses import replace
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.runner import run_episode
from k1lab.multibench.synthetic import ToyEnv, ToyPolicy, ToyReviewer
from k1lab.multibench.types import Action, Proposal
from semantic_lab.vector import Coordinator, ControlEpisodeEnv, EpisodePolicy


def fixture(tmp_path, mode, mixed=True, fail_step=False):
    cases = {i: {'case_id': f'fixture{i}', 'task': 'fixture', 'task_group': 'fixture',
                 'benchmark': 'synthetic', 'partition': 'dev'} for i in range(2)}
    envs = {i: ToyEnv(horizon=9) for i in cases}
    initial = {i: envs[i].reset(case) for i, case in cases.items()}
    identity = replace(ToyPolicy(prefix=3).identity, stateful=False)
    calls = {i: [] for i in cases}; actions = {i: [] for i in cases}
    def infer(values):
        results = {}
        for idx, obs in values.items():
            calls[idx].append(obs.step)
            results[idx] = Proposal(obs.stamp, obs.step, identity.identity,
                [Action('x5_joint14', obs.state.copy()) for _ in range(3)])
        return results
    def step(values):
        if fail_step:
            raise RuntimeError('uncertain physical write; no retry')
        results = {}
        for idx, value in values.items():
            result = envs[idx].step(value['action'], correction=value['correction'])
            actions[idx].append(result.observation.step)
            results[idx] = result
        return results
    class Reviewer(ToyReviewer):
        def review(self, obs, proposal, reasons, receipt, contract, direct=False):
            result = super().review(obs, proposal, reasons, receipt, contract, direct)
            if not direct and obs.episode == 'fixture0':
                result.mode = 'shorten'; result.steps = 1
            return result
    coordinator = Coordinator(initial, identity, {i: 9 for i in cases},
        lambda idx: envs[idx].describe(), infer, step, timeout_s=5,
        evidence_kind='synthetic', mixed_operations=mixed,
        preview_batch=lambda values: {i: {'kind': 'fixture_not_physics'} for i in values})
    config = {'name': mode, 'mode': mode, 'max_decision_steps': 4,
              'max_correction_steps': 4, 'max_reviews': 30, 'wall_limit_s': 5}
    result = coordinator.run(cases, config, {i: tmp_path / str(i) for i in cases},
        {i: Reviewer() for i in cases}, episode_runner=run_episode,
        env_factory=ControlEpisodeEnv,
        policy_factory=(lambda owner, idx: None) if mode.startswith('direct') else EpisodePolicy)
    return result, coordinator, calls, actions


def test_numeric_shortening_shares_owner_without_forcing_equal_inference_cadence(tmp_path):
    result, coordinator, calls, actions = fixture(tmp_path, 'review_every_chunk')
    assert all(row['native_steps'] == 9 for row in result.values())
    assert all(row['evidence_kind'] == 'synthetic' for row in result.values())
    assert calls[0] == list(range(9)) and calls[1] == [0, 3, 6]
    assert all(acks == list(range(1, 10)) for acks in actions.values())
    assert any(row == {'operation': 'infer', 'env_ids': [0]} for row in coordinator.dispatches)


def test_direct_uses_existing_runner_with_no_policy_inference(tmp_path):
    result, coordinator, calls, actions = fixture(tmp_path, 'direct_sparse')
    assert all(row['native_steps'] == 9 and row['policy_identity'] is None for row in result.values())
    assert all(row['metrics']['policy_calls'] == 0 for row in result.values())
    assert calls == {0: [], 1: []}
    assert all(acks == list(range(1, 10)) for acks in actions.values())
    assert all(row['operation'] == 'action' for row in coordinator.dispatches)


def test_strict_semantic_barriers_do_not_silently_admit_numeric_mixed_operations(tmp_path):
    with pytest.raises(ContractError, match='prefix barriers'):
        fixture(tmp_path, 'review_every_chunk', mixed=False)


def test_uncertain_batch_step_stops_without_retry(tmp_path):
    with pytest.raises(RuntimeError, match='no retry'):
        fixture(tmp_path, 'direct_sparse', fail_step=True)


def test_runner_error_before_first_request_retires_without_waiting_for_wall_limit(tmp_path):
    initial = {0: ToyEnv().observation()}
    coordinator = Coordinator(initial, None, {0: 1}, lambda idx: {},
        lambda values: {}, lambda values: {}, timeout_s=5)
    def reject(*args):
        raise ValueError('bad configuration')
    with pytest.raises(ValueError, match='bad configuration'):
        coordinator.run({0: {}}, {}, {0: tmp_path}, {0: None},
            episode_runner=reject, policy_factory=lambda owner, idx: None)
    assert coordinator.active == set()


def test_default_semantic_path_preserves_aligned_natural_prefixes(tmp_path):
    cases = {i: {'case_id': f'fixture{i}', 'task': 'fixture', 'task_group': 'fixture',
                 'benchmark': 'synthetic', 'partition': 'dev'} for i in range(2)}
    envs = {i: ToyEnv(horizon=9) for i in cases}
    identity = replace(ToyPolicy(prefix=3).identity, stateful=False)
    calls = {i: [] for i in cases}
    def infer(values):
        result = {}
        for idx, obs in values.items():
            calls[idx].append(obs.step)
            result[idx] = Proposal(obs.stamp, obs.step, identity.identity,
                [Action('x5_joint14', obs.state.copy()) for _ in range(3)])
        return result
    coordinator = Coordinator({i: envs[i].reset(case) for i, case in cases.items()},
        identity, {i: 9 for i in cases}, lambda idx: envs[idx].describe(), infer,
        lambda values: {idx: envs[idx].step(action) for idx, action in values.items()},
        timeout_s=5, evidence_kind='synthetic')
    result = coordinator.run(cases, {'name': 'original', 'mode': 'motor_only',
        'prompt_mode': 'original_only', 'max_semantic_calls': 0, 'wall_limit_s': 5},
        {i: tmp_path / str(i) for i in cases}, {i: None for i in cases})
    assert not coordinator.mixed_operations
    assert calls == {0: [0, 3, 6], 1: [0, 3, 6]}
    assert all(row['metrics']['completed_prefixes'] == 3 for row in result.values())
    assert all(row['env_ids'] == [0, 1] for row in coordinator.dispatches)
