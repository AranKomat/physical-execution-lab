"""Bind a semantic factor to the retained reference motor baseline."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

root = Path('/root/physical-execution-lab')
baseline = root / 'runs/reference-pi05-2-001'
binding_path = baseline / 'pre-action-binding.json'
binding = json.loads(binding_path.read_text())
report = json.loads((baseline / 'report.json').read_text())
audit = json.loads((baseline / 'offline-audit.json').read_text())
assert audit['source_predictions_and_native_acks_match']
assert audit['case_layout_variant_horizon_binding_verified']
assert report['status'] == 'native_terminal_semantic_wave'
for path, expected in binding['sources'].items():
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected
usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True)
assert all(int(value) < 500 for value in usage.splitlines()), 'preserve active GPU workload'
base_config_path = root / 'runs/semantic-vector-recovery-dev001/config.json'
config = json.loads(base_config_path.read_text())
assert config['prompt_mode'] == 'task_plus_subtask'
assert config['semantic_schedule']['allow_semantic_recovery'] is True
assert config['model']['reasoning_effort'] == 'medium' and config['model']['service_tier'] == 'flex'
config['name'] = 'reference_arrange_task_plus_recovery001'
out = root / 'runs/reference-arrange-semantic001'
out.mkdir(exist_ok=False)
config_path = out / 'config.json'
config_path.write_text(json.dumps(config, indent=2) + '\n')
plan = {'scope': 'same reference cases; historically opened task; not untouched held-out',
    'baseline_first': True, 'candidate_selection': 'carry forward recovery-enabled task-plus-subtask factor from prior development panel',
    'baseline_binding_sha256': hashlib.sha256(binding_path.read_bytes()).hexdigest(),
    'baseline_report_sha256': hashlib.sha256((baseline / 'report.json').read_bytes()).hexdigest(),
    'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
    'parent_config_sha256': hashlib.sha256(base_config_path.read_bytes()).hexdigest(),
    'baseline_binding': binding, 'cases': report['reference_cases'],
    'no_case_replacement_or_automatic_retry': True,
    'claim_limits': 'single execution per condition/case; no bitwise trajectory parity or causal gain established'}
(out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
token = root / 'runs/reference-arrange-semantic001-token'
command = ['/root/miniconda3/envs/RoboDojo/bin/python3.11', '-u',
    str(root / 'runs/operator_reference_rollout001.py'), '--policy', 'pi05',
    '--worker-gpu', '1', '--num-envs', '2', '--steps', '1050', '--tag', '002',
    '--task', 'arrange_largest_number', '--case-manifest',
    str(root / 'configs/local/robodojo-cases.json'), '--case-ids',
    *[case['case_id'] for case in report['reference_cases']], '--semantic-config', str(config_path), '--allow-api']
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES',
    OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', K1_RELAY_TOKEN=token.read_text().strip())
try:
    with (out / 'launcher.log').open('x') as log:
        subprocess.run(command, cwd=root, env=env, stdout=log,
            stderr=subprocess.STDOUT, check=True, timeout=2900)
finally:
    token.unlink(missing_ok=True)
