"""CPU structural checks; no native simulator, learned inference or paid calls."""
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from k1lab.multibench.types import Action, Observation, PolicyIdentity, Proposal, StepResult
from semantic_lab.contracts import SemanticDecision
from semantic_lab.audit import audit
from operator_semantic_vector_coordinator001 import Coordinator

out = ROOT / 'runs/semantic-vector-cpu-001'
out.mkdir(exist_ok=False)
identity = PolicyIdentity('synthetic', 'a' * 64, 'synthetic', 'x5_joint14',
    'no learned model', 25, 2, 'synthetic', prediction_horizon=3)
steps = {0: 0, 1: 0}
prompts, calls = {0: [], 1: []}, {0: 0, 1: 0}

def observation(idx):
    return Observation(f'synthetic-{idx}', steps[idx], f'Original task {idx}',
        {'cam_high': np.full((8, 8, 3), idx + steps[idx], np.uint8)},
        np.zeros(14, np.float32), {}, 25)

class Planner:
    def __init__(self, idx):
        self.idx = idx

    def reset(self):
        pass

    def close(self):
        pass

    def decide(self, obs, state, reasons, receipt):
        stop = self.idx == 0 and obs.step == 2
        operation = 'stop' if stop else 'set_subtask' if obs.step == 0 else 'continue'
        return SemanticDecision(obs.episode, obs.step, obs.stamp, state.context.epoch,
            operation, f'Goal {self.idx}' if operation == 'set_subtask' else '',
            'uncertain' if stop else 'progressing', 'Synthetic structural test, not physical evidence.')

def infer(values):
    result = {}
    for idx, obs in values.items():
        calls[idx] += 1
        prompts[idx].append(obs.instruction)
        actions = [Action('x5_joint14', np.zeros(14)) for _ in range(3)]
        result[idx] = Proposal(obs.stamp, obs.step, identity.identity, actions,
            {'inference_index': calls[idx] - 1})
    return result

def step(values):
    result = {}
    for idx, action in values.items():
        steps[idx] += 1
        terminal = steps[idx] == 5
        result[idx] = StepResult(observation(idx), terminal, terminal, score=1. if terminal else None)
    return result

config = {'name': 'synthetic-vector', 'mode': 'semantic_subtask_hierarchy',
    'prompt_mode': 'subtask_only', 'max_semantic_calls': 10, 'wall_limit_s': 30,
    'semantic_schedule': {'review_interval_steps': 2, 'minimum_dwell_steps': 1,
        'event_cooldown_steps': 1, 'max_decision_age_steps': 1}}
coordinator = Coordinator({idx: observation(idx) for idx in steps}, identity,
    {idx: 10 for idx in steps}, lambda idx: {'scope': 'synthetic CPU'}, infer, step,
    timeout_s=30, evidence_kind='synthetic')
cases = {idx: {'case_id': f'synthetic-{idx}', 'task': 'synthetic', 'benchmark': 'synthetic',
    'partition': 'dev'} for idx in steps}
outputs = {idx: out / str(idx) for idx in steps}
results = coordinator.run(cases, config, outputs, {idx: Planner(idx) for idx in steps})
assert steps == {0: 2, 1: 5} and calls == {0: 1, 1: 3}
assert prompts == {0: ['Goal 0'], 1: ['Goal 1'] * 3}
assert results[0]['status'] == 'planner_stop_incomplete' and results[0]['native_score'] is None
assert results[1]['status'] == 'native_completed' and results[1]['native_score'] == 1.
assert all(result['metrics']['unresolved_policy_actions'] == 0 for result in results.values())
audits = {idx: audit(path) for idx, path in outputs.items()}
report = {'status': 'synthetic_vector_structure_passed', 'controls': steps, 'policy_calls': calls,
    'per_episode_prompt_isolation': True, 'abstention_and_partial_terminal_prefix_accounted': True,
    'existing_semantic_journal_audits': audits, 'dispatches': coordinator.dispatches,
    'paid_calls': 0, 'native_simulators': 0, 'learned_model_inferences': 0,
    'scope': 'CPU structural check only; not native semantic vector qualification or phase completion'}
(out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
