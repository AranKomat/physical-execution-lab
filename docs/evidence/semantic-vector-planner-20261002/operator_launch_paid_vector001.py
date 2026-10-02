"""Remote launcher: token never enters process arguments or evidence."""
import os
from pathlib import Path
import subprocess

root = Path('/root/physical-execution-lab')
token = root / 'runs/semantic-vector-planner-pilot001-token'
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES',
    OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', K1_RELAY_TOKEN=token.read_text().strip())
command = ['/root/miniconda3/envs/RoboDojo/bin/python3.11', '-u',
    str(root / 'runs/operator_vector_pi05_rollout001.py'), '--num-envs', '5', '--steps', '150',
    '--tag', '011', '--task', 'classify_objects', '--inference-mode', 'native_singleton',
    '--semantic-config', str(root / 'runs/semantic-vector-planner-pilot001.json'), '--allow-api']
try:
    with (root / 'runs/semantic-vector-planner-pilot001-native.log').open('x') as log:
        subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
            check=True, timeout=2200)
finally:
    token.unlink(missing_ok=True)
