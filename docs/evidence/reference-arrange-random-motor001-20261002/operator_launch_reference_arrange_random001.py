"""Fill the three missing reference motor baselines; no paid requests."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from semantic_lab.protocol import code_fingerprint
from semantic_lab.reference import bind_reference_wave

usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True)
assert all(int(value) == 0 for value in usage.splitlines()), 'preserve active GPU workload'
assert shutil.disk_usage(root).free > 8 * 1024**3, 'retain recording headroom'
manifest_path = root / 'configs/local/robodojo-cases.json'
ids = [f'arrange_largest_number__random__g0__l{idx}' for idx in range(3)]
cases = bind_reference_wave(json.loads(manifest_path.read_text()), ids, 'arrange_largest_number_random')
config_path = root / 'runs/reference-motor-original001.json'
config = json.loads(config_path.read_text())
assert config['mode'] == 'motor_only' and config['prompt_mode'] == 'original_only'
assert config['max_semantic_calls'] == 0
out = root / 'runs/reference-arrange-random-motor001'
out.mkdir(exist_ok=False)
paths = [root / 'runs' / name for name in (
    'operator_reference_rollout001.py', 'operator_reference_native001.py',
    'operator_semantic_vector_coordinator001.py', 'operator_vector_pi05_rollout001.py')]
paths += [root / 'external/RoboDojo/src/eval_client/eval_env.py',
          root / 'external/GPT-as-Policy/hybrid_rollout/robodojo/robodojo_server/session.py']
plan = {'scope': 'three missing random reference cases from historically opened arrange family',
        'cases': cases, 'paid_calls': 0, 'automatic_retry': False,
        'source_sha256': code_fingerprint(root),
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
        'sources': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        'untouched_heldout_claim': False, 'native_qualified_claim': False,
        'selection': 'all remaining selected arrange reference cases; no replacement or outcome selection'}
(out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
command = ['/root/miniconda3/envs/RoboDojo/bin/python3.11', '-u',
           str(root / 'runs/operator_reference_rollout001.py'), '--policy', 'pi05',
           '--worker-gpu', '1', '--num-envs', '3', '--steps', '1050', '--tag', '003',
           '--task', 'arrange_largest_number_random', '--case-manifest', str(manifest_path),
           '--case-ids', *ids, '--semantic-config', str(config_path)]
with (out / 'launcher.log').open('x') as log:
    subprocess.run(command, cwd=root,
                   env=dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES',
                            OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'),
                   stdout=log, stderr=subprocess.STDOUT, check=True, timeout=2100)
