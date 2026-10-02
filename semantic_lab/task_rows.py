"""Route unchanged native task evaluators to rows of a shared simulator.

This is evaluator/lifecycle plumbing, never an actor observation source.
Task classes retain their own singleton state and native reward predicates.
"""
from collections.abc import MutableSequence
import inspect
from copy import deepcopy
from types import MethodType, SimpleNamespace

from k1lab.errors import ContractError


class OwnerRow(MutableSequence):
    """A live singleton view, including when reset replaces the owner's array."""
    def __init__(self, owner, name, index):
        self.owner, self.name, self.index = owner, name, index

    def __len__(self):
        return 1

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [getattr(self.owner, self.name)[self.index]][key]
        if key not in (0, -1):
            raise IndexError(key)
        return getattr(self.owner, self.name)[self.index]

    def __setitem__(self, key, value):
        if key not in (0, -1):
            raise IndexError(key)
        getattr(self.owner, self.name)[self.index] = value

    def __delitem__(self, key):
        raise ContractError('task rows cannot remove simulator environments')

    def insert(self, index, value):
        raise ContractError('task rows cannot add simulator environments')


class IndexedManager:
    """Translate source manager's explicitly indexed calls from local0 to a row."""
    ROW_ATTRIBUTES = frozenset(('env_origins', 'instance_type_by_env',
        'robot_origin_endpose', 'robot_init_joint', 'prev_control'))

    def __init__(self, manager, index):
        self._manager, self._index = manager, index
        self.num_envs = 1

    def __getattr__(self, name):
        value = getattr(self._manager, name)
        if name in self.ROW_ATTRIBUTES:
            return value[self._index:self._index + 1]
        if name in ('layout_manager', 'control_manager'):
            return IndexedManager(value, self._index)
        if not callable(value):
            return value
        signature = inspect.signature(value)
        parameters = signature.parameters
        scalar = next((key for key in ('env_idx', 'env_id') if key in parameters), None)
        vector = next((key for key in ('env_idx_list', 'env_ids') if key in parameters), None)
        if scalar is None and vector is None:
            if not name.startswith(('get_', 'process_', 'restore_')):
                raise ContractError(f'unscoped manager operation forbidden: {name}')
            return value

        def indexed(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            if scalar:
                if bound.arguments[scalar] != 0:
                    raise ContractError('native task view only exposes environment0')
                bound.arguments[scalar] = self._index
            if vector:
                indices = bound.arguments[vector]
                if indices is not None and list(indices) != [0]:
                    raise ContractError('native task view only exposes environment0')
                bound.arguments[vector] = [self._index]
            result = value(*bound.args, **bound.kwargs)
            if vector and result is not None:
                if isinstance(result, dict):
                    if self._index not in result:
                        raise ContractError(f'native indexed query omitted row: {name}')
                    return {0: result[self._index]}
                raise ContractError(f'unbound indexed query result: {name}')
            return result
        return indexed


def make_task_row(task_class, task_base, owner, index, config, app):
    """Insert a shared-resource base into the source task's cooperative MRO."""
    if not issubclass(task_class, task_base) or not 0 <= index < owner.num_envs:
        raise ContractError('task row does not bind a native TaskEnv and simulator row')

    class SharedResources(task_base):
        def __init__(self, config, app, **kwargs):
            self.num_envs = 1
            self.app = app
            self.config = config.sim
            self.eval_seed = int(config.eval_cfg.seed)
            self.env_seeds = [owner.env_seeds[index]]
            self.env_seed_list = self.env_seeds
            self._seed_list = self.env_seeds
            self._global_seed = self.env_seeds[0]
            self.device, self.dt = owner.device, owner.dt
            self.sim = owner.sim
            self.scene_manager = IndexedManager(owner.scene_manager, index)
            self.robot_manager = IndexedManager(owner.robot_manager, index)
            self.success = OwnerRow(owner, 'success', index)
            self.end_flag = OwnerRow(owner, 'end_flag', index)
            self.take_action_cnt = OwnerRow(owner, 'take_action_cnt', index)

        def _post_setup_scene(self, sim):
            self.sim = sim

        def reset(self, seed=None, options=None):
            if seed is not None and list(seed) != self.env_seeds:
                raise ContractError('native task reset seed differs from its bound row')

        def mark_env_unstable(self, env_idx):
            if env_idx != 0:
                raise ContractError('invalid task-local unstable index')
            owner.mark_env_unstable(index)

    row_class = type(f'SharedRow_{task_class.__name__}', (task_class, SharedResources), {})
    return row_class(config, app)


class TaskRowRewards:
    """Delegate native rewards independently, including final checks per horizon."""
    def __init__(self, owner, rows):
        self.owner, self.rows = owner, rows
        self.terminal = {}

    def init_state(self):
        self.terminal.clear()
        for row in self.rows:
            row.reward_manager.init_state()

    def step(self, env_idx_list=None):
        indices = range(len(self.rows)) if env_idx_list is None else env_idx_list
        for idx in indices:
            if idx not in self.terminal:
                self.rows[idx].reward_manager.step(env_idx_list=[0])

    def get_reward(self, final_check=False):
        rewards = []
        for idx, row in enumerate(self.rows):
            if idx in self.terminal:
                rewards.append(self.terminal[idx].reward)
                continue
            # Source EvalEnv uses a global final_check flag; distinct horizons
            # require final predicates only for the row that actually terminates.
            final = (self.owner.take_action_cnt[idx] >= row.step_lim
                     or not self.owner.success[idx])
            rewards.append(row.reward_manager.get_reward(final_check=final)[0])
        return rewards

    def get_score(self):
        return [self.terminal[idx].score if idx in self.terminal
                else row.reward_manager.get_score()[0] for idx, row in enumerate(self.rows)]

    def freeze(self, idx, reward):
        self.terminal[idx] = SimpleNamespace(reward=reward,
            score=self.rows[idx].reward_manager.get_score()[0])


def row_episode_end(env):
    """Source EvalEnv terminal rule with per-task horizons and frozen terminal scores."""
    previous = list(env.end_flag)
    rewards = env.reward_manager.get_reward()
    for idx, row in enumerate(env.task_rows):
        if env.end_flag[idx]:
            continue
        if rewards[idx] > 1 - 1e-3:
            env.end_flag[idx], env.success[idx] = True, True
        elif env.take_action_cnt[idx] >= row.step_lim or not env.success[idx]:
            env.end_flag[idx], env.success[idx] = True, False
        if env.end_flag[idx]:
            env.reward_manager.freeze(idx, rewards[idx])
    changed = [idx for idx, flag in enumerate(env.end_flag) if previous[idx] != flag]
    if changed:
        env.get_obs_batch(env_idx_list=changed, last_frame=True)
    return all(env.end_flag)


def create_mixed_eval_env(configs, app):
    """Build one native simulator for tasks with identical physical configuration.

    Separate processes must be used when global physics, robot or camera
    settings differ. This factory never silently changes those settings.
    """
    from omegaconf import OmegaConf
    from env.environment.task_env import TaskEnv
    from env.global_configs import BENCHMARK
    from env.seed_manager.seed_manager import SeedManager
    from src.eval_client import eval_env
    import importlib

    if not configs:
        raise ContractError('mixed task scene requires at least one task')
    def physical(cfg):
        result = OmegaConf.to_container(cfg, resolve=True)
        sim = deepcopy(result['sim'])
        sim.pop('seed', None)
        sim['scene'].pop('num_envs', None)
        return dict(sim=sim, **{key: result[key] for key in ('robot', 'scene', 'camera')})
    reference = physical(configs[0])
    if any(physical(cfg) != reference for cfg in configs[1:]):
        raise ContractError('incompatible native physical settings require separate simulator processes')
    registry = importlib.import_module(f'task.{BENCHMARK}.task_registry')
    bindings = [registry.load_task_class(cfg.eval_cfg.task_name) for cfg in configs]
    if len({name for name, _ in bindings}) != len(bindings):
        raise ContractError('distinct-task scene contains duplicate task types')

    class MixedTaskEnv(TaskEnv):
        def __init__(self, config, app, **kwargs):
            super().__init__(config, app, **kwargs)
            self.success = [True] * self.num_envs
            self.end_flag = [False] * self.num_envs
            self.take_action_cnt = [0] * self.num_envs
            self.task_rows = [make_task_row(task, TaskEnv, self, idx, cfg, app)
                              for idx, ((_, task), cfg) in enumerate(zip(bindings, configs))]
            self.step_limits = [row.step_lim for row in self.task_rows]
            self.step_lim = max(self.step_limits)
            self.interact = any(getattr(row, 'interact', False) for row in self.task_rows)
            self.reward_manager = TaskRowRewards(self, self.task_rows)

        def _post_setup_scene(self, sim):
            super()._post_setup_scene(sim)
            for row in self.task_rows:
                row._post_setup_scene(sim)

        def reset(self, seed=None, options=None):
            super().reset(seed=seed, options=options)
            for row in self.task_rows:
                row.reset(seed=row.env_seeds, options=options)

        def run_reward(self):
            for row in self.task_rows:
                row.run_reward()

        def get_score(self):
            for row in self.task_rows:
                row.get_score()

        def gen_instruction(self, env_idx):
            return self.task_rows[env_idx].gen_instruction(0)

        @property
        def support_arm_action(self):
            return [getattr(row, 'support_arm_action', [[]])[0] for row in self.task_rows]

        def query_support_arm_traj(self, env_idx):
            row = self.task_rows[env_idx]
            if hasattr(row, 'query_support_arm_traj'):
                row.query_support_arm_traj(0)

        def check_support_arm_stable(self, env_idx):
            row = self.task_rows[env_idx]
            if hasattr(row, 'check_support_arm_stable'):
                row.check_support_arm_stable(0)

    shared = deepcopy(configs[0])
    shared.sim.scene.num_envs = len(configs)
    shared.sim.seed = [0] * len(configs)
    shared.eval_cfg.eval_num = len(configs)
    # Native EvalEnv supplies the I/O/control loop; only its task-class lookup
    # is replaced temporarily. No installed source files are edited.
    original = registry.load_task_class
    try:
        registry.load_task_class = lambda name: (bindings[0][0], MixedTaskEnv)
        env = eval_env.create_eval_env(shared, app)
    finally:
        registry.load_task_class = original
    directories = []
    for cfg in configs:
        directory = SeedManager(cfg.eval_cfg)
        directory.init_eval(completed_layout_ids=[], abandoned_layout_ids=[])
        directories.append(directory)
    native_reset = env.reset
    native_lookup = env.seed_manager.get_seed_scene_info

    def reset(seed=None, options=None):
        if seed is None or list(seed) != [0] * len(configs):
            raise ContractError('this campaign binds group0/layout0 for every distinct task')
        next_row = 0
        def lookup(layout_id):
            nonlocal next_row
            if next_row >= len(directories) or layout_id != 0:
                raise ContractError('mixed scene layout lookup escaped its row binding')
            value = directories[next_row].get_seed_scene_info(layout_id)
            next_row += 1
            return value
        try:
            env.seed_manager.get_seed_scene_info = lookup
            native_reset(seed=seed, options=options)
            if next_row != len(directories):
                raise ContractError('native reset did not load exactly one layout per task')
        finally:
            env.seed_manager.get_seed_scene_info = native_lookup
    env.reset = reset
    env.is_episode_end = MethodType(row_episode_end, env)
    env.task_seed_managers = directories
    return env
