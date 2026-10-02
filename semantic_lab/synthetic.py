"""Explicit deterministic software fixtures, not robot competence evidence."""
from dataclasses import asdict
from pathlib import Path
import numpy as np
from k1lab.multibench.types import Observation, Action, Proposal, PolicyIdentity, StepResult
from k1lab.util import digest
from .contracts import SemanticDecision
from .policy import InstructionPolicy
from .runner import run_episode
from .report import write_report


class ToyEnvironment:
    evidence_kind = 'synthetic'
    runtime_fingerprint = {}
    def __init__(self, horizon=24, soft_event=False):
        self.horizon = horizon
        self.soft_event = soft_event
        self.step_id = 0
        self.actions = []
        self.task = 'Move the test actuator to its goal.'
    def obs(self):
        return Observation('synthetic-episode', self.step_id, self.task,
            {'cam_high': np.full((16, 16, 3), self.step_id, np.uint8)}, np.zeros(14, np.float32),
            {'left': {'xyz': [self.step_id * .001, 0., 0.], 'quaternion_xyzw': [0., 0., 0., 1.]},
             'right': {'xyz': [0., 0., 0.], 'quaternion_xyzw': [0., 0., 0., 1.]}}, 25.,
            {'execution_failed': self.soft_event and self.step_id == 1})
    def reset(self, case):
        return self.obs()
    def step(self, action, correction=False):
        self.actions.append(action.values.tolist())
        self.step_id += 1
        done = self.step_id >= self.horizon
        return StepResult(self.obs(), done, done, False, 1. if done else None)
    def finish(self, reason):
        return {'success': self.step_id >= self.horizon}
    def describe(self):
        return {'benchmark': 'synthetic', 'horizon': self.horizon, 'control_hz': 25.}
    def close(self):
        pass


class ToyPolicy:
    def __init__(self, horizon=5, execute=3):
        self.identity = PolicyIdentity('synthetic-policy', '0' * 64, 'test', 'x5_joint14',
                                       'none, synthetic only', 25., execute, 'synthetic', horizon)
        self.horizon = horizon
        self.reset()
    def reset(self):
        self.rng = np.random.default_rng(7)
        self.steps = []
        self.prompts = []
        self.acks = []
        self.rebindings = 0
        self.invalidations = []
    def observe(self, obs):
        self.acks.append(obs.step)
    def rebind_instruction(self, obs):
        self.rebindings += 1
    def propose(self, obs):
        self.steps.append(obs.step)
        self.prompts.append(obs.instruction)
        actions = []
        for _ in range(self.horizon):
            a = self.rng.uniform(-.05, .05, 14)
            a[[6, 13]] = .5
            actions.append(Action('x5_joint14', a))
        return Proposal(obs.stamp, obs.step, self.identity.identity, actions)
    def invalidate(self, reason):
        self.invalidations.append(reason)
    def memory(self):
        return {}
    def synchronize(self):
        pass
    def close(self):
        pass


class ToyPlanner:
    def __init__(self, mode='change'):
        self.mode = mode
        self.calls = []
    def reset(self):
        self.calls.clear()
    def decide(self, obs, state, reasons, receipt):
        self.calls.append(obs.step)
        operation = 'set_subtask' if not state.context.subtask and self.mode == 'change' else 'continue'
        return SemanticDecision(obs.episode, obs.step, obs.stamp, state.context.epoch,
                operation, 'Move the test actuator.' if operation == 'set_subtask' else '',
                'progressing', 'Software fixture decision; not sensor-derived robot behavior.')
    def close(self):
        pass


def run(output):
    root = Path(output)
    cases = [{'case_id': f'toy-{i}', 'task': f'fixture-{i}', 'task_group': f'fixture-{i}',
              'benchmark': 'synthetic', 'partition': 'dev'} for i in range(2)]
    results = []
    variants = [('motor_only', 'original_only'), ('semantic_shadow', 'original_only'),
                ('semantic_subtask_hierarchy', 'task_plus_subtask'), ('semantic_subtask_hierarchy', 'subtask_only')]
    conditions = []
    for mode, prompt in variants:
        name = mode + '__' + prompt
        conditions.append(name)
        cfg = {'name': name, 'mode': mode, 'prompt_mode': prompt, 'max_semantic_calls': 10,
               'wall_limit_s': 120, 'semantic_schedule': {'review_interval_steps': 6,
                   'minimum_dwell_steps': 3, 'event_cooldown_steps': 3}}
        for i, case in enumerate(cases):
            env = ToyEnvironment(horizon=24, soft_event=bool(i))
            policy = InstructionPolicy(ToyPolicy(), kind='test')
            planner = None if mode == 'motor_only' else ToyPlanner()
            results.append(run_episode(env, policy, planner, case, cfg, root / name / case['case_id']))
    return write_report(cases, results, root, conditions, conditions[0], conditions[2])
