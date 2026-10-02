from types import SimpleNamespace

import pytest

from k1lab.errors import ContractError
from semantic_lab.task_rows import IndexedManager, OwnerRow, TaskRowRewards, make_task_row, row_episode_end


def test_owner_row_survives_reset_and_writes_only_its_environment():
    owner = SimpleNamespace(success=[True, True])
    row = OwnerRow(owner, 'success', 1)
    row[0] = False
    assert owner.success == [True, False]
    owner.success = [False, True]
    assert list(row) == [True]
    with pytest.raises(IndexError):
        row[1] = False


def test_manager_remaps_positional_and_vector_queries():
    class Manager:
        num_envs = 3
        env_origins = [10, 20, 30]

        def get_layout_records(self, env_idx, category):
            return (env_idx, category)

        def get_real_endpose(self, robot, env_idx_list=None):
            return {idx: f'{robot}/{idx}' for idx in env_idx_list}

        def reset(self):
            pytest.fail('singleton task must never reset shared resources')
    row = IndexedManager(Manager(), 2)
    assert row.get_layout_records(0, 'Rigid') == (2, 'Rigid')
    assert row.get_real_endpose('arm') == {0: 'arm/2'}
    assert row.env_origins == [30]
    with pytest.raises(ContractError):
        row.get_layout_records(1, 'Rigid')
    with pytest.raises(ContractError):
        row.reset()


def test_source_task_lifecycle_uses_shared_boundary_once():
    class TaskEnv:
        def __init__(self, *args, **kwargs):
            pytest.fail('task delegate must not allocate another simulator')

        def get_env_seed(self, idx):
            return self.env_seeds[idx]

    class NativeTaskCommon:
        def __init__(self, config, app, **kwargs):
            super().__init__(config, app, **kwargs)
            self.native_initializations = 1

        def reset(self, seed=None, options=None):
            super().reset(seed=seed, options=options)
            self.native_resets = getattr(self, 'native_resets', 0) + 1

    class NativeTask(NativeTaskCommon, TaskEnv):
        pass
    owner = SimpleNamespace(num_envs=2, env_seeds=[0, 0], sim=object(), device='cpu', dt=.01,
        scene_manager=object(), robot_manager=object(), success=[True, True],
        end_flag=[False, False], take_action_cnt=[0, 0])
    cfg = SimpleNamespace(sim=object(), eval_cfg=SimpleNamespace(seed=0))
    row = make_task_row(NativeTask, TaskEnv, owner, 1, cfg, object())
    row.reset(seed=[0])
    assert row.num_envs == 1 and row.native_resets == row.native_initializations == 1
    assert row.get_env_seed(0) == 0
    row.success[0] = False
    assert owner.success == [True, False]


def test_independent_final_checks_and_frozen_terminal_scores():
    class Rewards:
        def __init__(self):
            self.final = []
            self.score = 25

        def get_reward(self, final_check=False):
            self.final.append(final_check)
            return [0]

        def get_score(self):
            return [self.score]
    rows = [SimpleNamespace(step_lim=5, reward_manager=Rewards()),
            SimpleNamespace(step_lim=10, reward_manager=Rewards())]
    obs = []
    owner = SimpleNamespace(task_rows=rows, success=[True, True], end_flag=[False, False],
        take_action_cnt=[5, 5], get_obs_batch=lambda **kwargs: obs.append(kwargs))
    owner.reward_manager = TaskRowRewards(owner, rows)
    assert not row_episode_end(owner)
    assert owner.end_flag == [True, False] and owner.success == [False, True]
    assert rows[0].reward_manager.final == [True]
    assert rows[1].reward_manager.final == [False]
    rows[0].reward_manager.score = 99
    assert owner.reward_manager.get_score() == [25, 25]
    assert obs == [dict(env_idx_list=[0], last_frame=True)]
