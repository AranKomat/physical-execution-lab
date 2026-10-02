from types import SimpleNamespace
import numpy as np
import pytest
from k1lab.errors import ContractError
from k1lab.multibench.types import Action
from semantic_lab.robot_controls import SourceRobotControls
from semantic_lab.control_review import CalibrationReviewer, InterleavingReviewer, SerializedReviewer


def controls():
    manager = SimpleNamespace(num_envs=2, robot_list=[], robot_key=[])
    class Kin:
        def __init__(self, env): self.idx = env.robot_manager.env_idx
        def check(self): return {'index': self.idx}
        def target(self, targets):
            self.targets = targets
            return dict(physical_steps=0, action=np.full(14, self.idx), diagnostics={'index': self.idx})
        def preview(self, actions):
            return dict(physical_steps=0, trajectory=list(range(len(actions))), measured_fk_check=self.check())
    return SourceRobotControls(manager, [0, 1], Kin)


def test_indexed_source_dispatch_preserves_motor_action_and_converts_only_correction():
    owner = controls()
    joint = Action('x5_joint14', np.zeros(14))
    assert owner.joint_target(0, dict(action=joint, correction=False)) == (joint, None)
    target = Action('x5_eef16_wxyz', [0, 0, .5, 1, 0, 0, 0, 1]*2)
    action, diagnostics = owner.joint_target(1, dict(action=target, correction=True))
    assert action.space == 'x5_joint14' and np.all(action.values == 1)
    assert diagnostics == {'index': 1}
    assert owner.kinematics[1].targets['left']['position'] == [0, 0, .5]
    with pytest.raises(ContractError): owner.joint_target(0, dict(action=target, correction=False))
    with pytest.raises(ContractError): owner.joint_target(0, dict(action=joint, correction=True))
    owner.kinematics[1].target = lambda targets: dict(physical_steps=1)
    with pytest.raises(ContractError): owner.joint_target(1, dict(action=target, correction=True))


def test_preview_samples_source_fk_without_advancing_physics():
    owner = controls()
    proposal = SimpleNamespace(actions=[Action('x5_joint14', np.zeros(14)) for _ in range(50)])
    reply = owner.preview({1: proposal})[1]
    assert len(reply['sampled_robot_fk']) == 8
    assert reply['sampled_robot_fk'][0] == 0 and reply['sampled_robot_fk'][-1] == 49
    assert reply['measured_fk_checks'] == [{'index': 1}]


def test_calibration_uses_initial_robot_pose_then_returns_without_task_or_policy():
    reviewer = CalibrationReviewer()
    eef = dict(xyz=[0, 0, .5], quaternion_xyzw=[0, 0, 0, 1], gripper_opening_command=1)
    obs = SimpleNamespace(eef={'left': eef, 'right': eef})
    contract = dict(correction_space='x5_eef16_wxyz', max_decision_steps=15, max_correction_steps=15)
    first = reviewer.review(obs, None, [], None, contract, direct=True)
    second = reviewer.review(obs, None, [], None, contract, direct=True)
    assert first.steps == second.steps == 15
    assert first.actions[0].values[2] == pytest.approx(.505)
    assert second.actions[0].values[2] == pytest.approx(.5)
    assert reviewer.review(obs, None, [], None, contract, direct=True).mode == 'stop'
    with pytest.raises(ContractError): reviewer.review(obs, None, [], None, contract, direct=False)


def test_serialized_reviewer_preserves_client_and_execution_history(tmp_path):
    calls = []
    reviewer = SimpleNamespace(client=SimpleNamespace(n=3),
        reset=lambda: calls.append('reset'), close=lambda: calls.append('close'),
        note_execution_start=lambda obs: calls.append(obs),
        review=lambda *args, **kwargs: (args, kwargs))
    wrapped = SerializedReviewer(reviewer, tmp_path/'lock')
    assert wrapped.client is reviewer.client
    assert wrapped.review('obs', direct=True) == (('obs',), {'direct': True})
    wrapped.reset(); wrapped.note_execution_start('obs'); wrapped.close()
    assert calls == ['reset', 'obs', 'close']


def test_interleaving_fixture_changes_only_selected_arm_and_requires_preview():
    eef = dict(xyz=[0, 0, .5], quaternion_xyzw=[0, 0, 0, 1], gripper_opening_command=1)
    obs = SimpleNamespace(eef={'left': eef, 'right': eef})
    proposal = SimpleNamespace(diagnostics={'robot_preview': {'not_contact_simulation': True}})
    contract = dict(correction_space='x5_eef16_wxyz')
    reviewer = InterleavingReviewer('right')
    assert reviewer.review(obs, proposal, [], None, contract).mode == 'accept'
    correction = reviewer.review(obs, proposal, [], None, contract)
    assert correction.actions[0].values[2] == .5
    assert correction.actions[0].values[10] == pytest.approx(.505)
    assert reviewer.review(obs, proposal, [], None, contract).mode == 'accept'
    proposal.diagnostics.clear()
    with pytest.raises(ContractError): reviewer.review(obs, proposal, [], None, contract)
