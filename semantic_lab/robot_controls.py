"""Bind native per-environment control to the unchanged source robot-only DLS."""
from types import SimpleNamespace
import numpy as np
from k1lab.errors import ContractError
from k1lab.multibench.adapters.robodojo import RoboDojoRPC
from k1lab.multibench.types import Action
from .robot_view import SingleEnvironmentRobotManager


class SourceRobotControls:
    def __init__(self, manager, env_ids, kinematics_factory):
        self.kinematics = {idx: kinematics_factory(SimpleNamespace(
            robot_manager=SingleEnvironmentRobotManager(manager, idx))) for idx in env_ids}
        self.initial_fk_checks = {idx: kin.check() for idx, kin in self.kinematics.items()}

    def joint_target(self, idx, value):
        action, correction = value['action'], value['correction']
        if type(correction) is not bool or idx not in self.kinematics:
            raise ContractError('invalid indexed native correction dispatch')
        if action.space == 'x5_joint14' and not correction:
            return action, None
        if action.space != 'x5_eef16_wxyz' or not correction:
            raise ContractError('native joint policy and EEF correction conventions cannot be interchanged')
        result = self.kinematics[idx].target(RoboDojoRPC.targets(action))
        if result.get('physical_steps') != 0:
            raise ContractError('source kinematics unexpectedly advanced physics')
        return Action('x5_joint14', result['action']), result['diagnostics']

    def preview(self, values):
        replies = {}
        for idx, proposal in values.items():
            if any(action.space != 'x5_joint14' for action in proposal.actions):
                raise ContractError('source joint FK preview required')
            result = self.kinematics[idx].preview(np.stack([a.values for a in proposal.actions]))
            if result.get('physical_steps') != 0:
                raise ContractError('source preview unexpectedly advanced physics')
            trajectory = result['trajectory']
            indices = np.unique(np.linspace(0, len(trajectory)-1, min(8, len(trajectory))).astype(int))
            replies[idx] = {'sampled_robot_fk': [trajectory[i] for i in indices],
                'measured_fk_checks': [result['measured_fk_check']], 'not_contact_simulation': True}
        return replies
