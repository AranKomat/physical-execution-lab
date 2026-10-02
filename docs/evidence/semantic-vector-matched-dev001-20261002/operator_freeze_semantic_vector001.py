"""Bind the new vector development cohort before its first comparison actions."""
import hashlib
import json
from pathlib import Path

root = Path('/root/physical-execution-lab')
output = root / 'runs/semantic-vector-matched-dev001'
output.mkdir(exist_ok=False)
sources = ['operator_vector_pi05_rollout001.py', 'operator_semantic_vector_native001.py',
    'operator_semantic_vector_coordinator001.py', 'operator_run_semantic_multifamily001.py',
    'operator_pi05_multifamily_worker001.py']
config = json.loads((root / 'runs/semantic-vector-motor-comparison001.json').read_text())
plan = {'cohort': 'semantic-vector-matched-dev001',
    'scope': 'fresh concurrent development comparison; not historical serial cohort or held-out',
    'roster': {'classify_objects': [0, 1, 2], 'build_tower': [0, 1]},
    'conditions_in_order': ['motor_only', 'task_plus_subtask', 'subtask_only'],
    'source_sha256': {name: hashlib.sha256((root / 'runs' / name).read_bytes()).hexdigest() for name in sources},
    'provider': json.loads((root / 'configs/local/pi05-exact-bound-001/provider.json').read_text()),
    'motor_config': config, 'native_seed': 0, 'native_prefix': 15, 'prediction_horizon': 50,
    'planner': {'model': 'gpt-6.1-sol', 'effort': 'medium', 'tier': 'flex',
        'max_calls_per_episode': 16, 'allow_semantic_recovery': False},
    'conditions_must_be_bound_before_launch': True, 'no_case_replacement_or_automatic_retry': True,
    'retain_all_stops_missing_cases_and_errors': True,
    'same_simulator_gpu': 0, 'same_shared_policy_gpu': 1,
    'rng': 'source seed0 singleton streams isolated per wave/env',
    'limits': {'classify_objects': 1100, 'build_tower': 1050},
    'counterfactual_trajectory_parity': False, 'memory_and_demonstrations': False}
(output / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
print(json.dumps({'frozen': str(output / 'plan.json'), 'roster': plan['roster']}))
