"""Freeze the recovery factor, then launch the unchanged concurrent executor."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path('/root/physical-execution-lab')
prior = root / 'runs/semantic-vector-matched-dev001/plan.json'
plan = json.loads(prior.read_text())
for name, expected in plan['source_sha256'].items():
    assert hashlib.sha256((root / 'runs' / name).read_bytes()).hexdigest() == expected
base_path = root / 'runs/semantic-vector-task-plus-comparison001.json'
config = json.loads(base_path.read_text())
assert config['prompt_mode'] == 'task_plus_subtask'
assert config['semantic_schedule']['allow_semantic_recovery'] is False
config['name'] = 'semantic_vector_recovery_dev001_task_plus_subtask'
config['semantic_schedule']['allow_semantic_recovery'] = True
out = root / 'runs/semantic-vector-recovery-dev001'
out.mkdir(exist_ok=False)
config_path = out / 'config.json'
config_path.write_text(json.dumps(config, indent=2) + '\n')
binding = {
    'cohort': 'semantic-vector-recovery-dev001',
    'phase': 'D, separate development recovery factor; not held-out',
    'parent_plan_sha256': hashlib.sha256(prior.read_bytes()).hexdigest(),
    'parent_config_sha256': hashlib.sha256(base_path.read_bytes()).hexdigest(),
    'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
    'changed_fields': ['name', 'semantic_schedule.allow_semantic_recovery'],
    'parent_plan': plan,
    'no_case_replacement_or_automatic_retry': True,
    'success_rule': 'native evaluator success; recovery issuance alone is not success',
    'retained_stops': True,
}
(out / 'plan.json').write_text(json.dumps(binding, indent=2) + '\n')
token = root / 'runs/semantic-vector-recovery-dev001-token'
env = dict(os.environ, K1_RELAY_TOKEN=token.read_text().strip())
command = [str(root / '.venv/bin/python'), '-u',
    str(root / 'runs/operator_run_semantic_multifamily001.py'),
    '--run-tag', '004', '--tag-base', '18', '--steps', '1100',
    '--wall-limit-s', '2400', '--semantic-config', str(config_path),
    '--sorting-envs', '3', '--tower-envs', '2', '--allow-api']
try:
    with (out / 'launcher.log').open('x') as log:
        subprocess.run(command, cwd=root, env=env, stdout=log,
            stderr=subprocess.STDOUT, check=True, timeout=2900)
finally:
    token.unlink(missing_ok=True)
