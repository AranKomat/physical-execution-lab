"""A single-environment robot-only view for the pinned source DLS implementation."""
from types import SimpleNamespace
from k1lab.errors import ContractError


class SingleEnvironmentRobotManager:
    def __init__(self, manager, env_idx):
        if type(env_idx) is not int or not 0 <= env_idx < manager.num_envs:
            raise ContractError('invalid robot kinematics environment index')
        self.manager = manager
        self.env_idx = env_idx
        self.num_envs = 1
        self.robot_list = manager.robot_list
        self.robot_key = []
        for key in manager.robot_key:
            limits = key.data.soft_joint_pos_limits
            if limits.shape[0] != manager.num_envs:
                raise ContractError('robot joint limits do not bind every native environment')
            self.robot_key.append(SimpleNamespace(data=SimpleNamespace(
                soft_joint_pos_limits=limits[env_idx:env_idx+1])))

    def _query(self, method, *args, env_idx_list=None, **kwargs):
        if env_idx_list is not None and list(env_idx_list) != [0]:
            raise ContractError('single-environment robot view only exposes local index0')
        rows = method(*args, env_idx_list=[self.env_idx], **kwargs)
        if not isinstance(rows, dict) or rows.get(self.env_idx) is None:
            raise ContractError('native robot query omitted the bound environment')
        return {0: rows[self.env_idx]}

    def get_link_pose(self, *args, **kwargs):
        return self._query(self.manager.get_link_pose, *args, **kwargs)

    def get_joint(self, *args, **kwargs):
        return self._query(self.manager.get_joint, *args, **kwargs)

    def get_real_endpose(self, *args, **kwargs):
        return self._query(self.manager.get_real_endpose, *args, **kwargs)
