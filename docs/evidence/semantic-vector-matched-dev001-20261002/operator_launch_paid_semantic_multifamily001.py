"""Run one full concurrent semantic condition, retaining all stops/errors."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--condition', choices=('task_plus_subtask', 'subtask_only'), required=True)
a = p.parse_args()
root = Path('/root/physical-execution-lab')
condition = 'task-plus' if a.condition == 'task_plus_subtask' else 'subtask'
config = root / f'runs/semantic-vector-{condition}-comparison001.json'
assert json.loads(config.read_text())['prompt_mode'] == a.condition
cohort = root / 'runs/semantic-vector-matched-dev001'
plan = json.loads((cohort / 'plan.json').read_text())
for name, expected in plan['source_sha256'].items():
    assert hashlib.sha256((root / 'runs' / name).read_bytes()).hexdigest() == expected
binding = cohort / (a.condition + '-config.json')
with binding.open('x') as stream:
    json.dump({'config': json.loads(config.read_text()),
        'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
        'phase': 'development matched comparison', 'no_recovery': True}, stream, indent=2)
token = root / ('runs/semantic-vector-matched-dev001-' + a.condition + '-token')
env = dict(os.environ, K1_RELAY_TOKEN=token.read_text().strip())
run_tag, tag_base = ('002', '14') if a.condition == 'task_plus_subtask' else ('003', '16')
command = [str(root / '.venv/bin/python'), '-u', str(root / 'runs/operator_run_semantic_multifamily001.py'),
    '--run-tag', run_tag, '--tag-base', tag_base, '--steps', '1100', '--wall-limit-s', '2400',
    '--semantic-config', str(config), '--sorting-envs', '3', '--tower-envs', '2', '--allow-api']
try:
    with (cohort / (a.condition + '-launcher.log')).open('x') as log:
        subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
            check=True, timeout=2900)
finally:
    token.unlink(missing_ok=True)
