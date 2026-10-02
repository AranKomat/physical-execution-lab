"""Own two native semantic-loop waves and one shared pi0.5 runtime."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import argparse

ROOT = Path('/root/physical-execution-lab')
sys.path.insert(0, str(ROOT))
from scripts.multibench.launch_robodojo_case import stop_child
from operator_vector_pi05_rollout001 import write_json

p = argparse.ArgumentParser()
p.add_argument('--wait-idle-s', type=int, default=0)
p.add_argument('--run-tag', default='001')
p.add_argument('--tag-base', type=int, default=6)
p.add_argument('--steps', type=int, default=150)
p.add_argument('--wall-limit-s', type=int, default=1200)
p.add_argument('--semantic-config', type=Path, required=True)
p.add_argument('--allow-api', action='store_true')
p.add_argument('--sorting-envs', type=int, default=3)
p.add_argument('--tower-envs', type=int, default=2)
a = p.parse_args()
config = json.loads(a.semantic_config.read_text())
assert config['mode'] == 'motor_only' or a.allow_api
assert 1 <= a.sorting_envs <= 5 and 1 <= a.tower_envs <= 5
assert 0 <= a.wait_idle_s <= 1200
assert a.run_tag.isdigit() and a.tag_base > 0 and 1 <= a.steps <= 1100
assert 60 <= a.wall_limit_s <= 3600
deadline = time.monotonic() + a.wait_idle_s
while True:
    usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used',
        '--format=csv,noheader,nounits'], text=True)
    if all(int(value) < 500 for value in usage.splitlines()):
        break
    if time.monotonic() >= deadline:
        raise RuntimeError('GPU work remains active; do not interrupt')
    time.sleep(5)
out = ROOT / ('runs/semantic-multifamily-pi05-' + a.run_tag)
out.mkdir(exist_ok=False)
broker = out / 'shared-worker'
broker.mkdir()
children, logs = [], []
report = {'status': 'started', 'paid_calls': 0, 'policy_runtimes': 1,
    'simulator_processes': 2, 'simulator_gpu': 0, 'policy_gpu': 1,
    'scope': 'concurrent development execution, not hierarchy comparison or independent task coverage',
    'requested_action_bound_per_env': a.steps,
    'wave_outputs': {}, 'initial_device_usage_mib': usage.splitlines()}
start = time.perf_counter()
try:
    log = (out / 'shared-worker.log').open('x')
    logs.append(log)
    service = subprocess.Popen([str(ROOT / '.venv-pi05/bin/python'), '-u',
        str(ROOT / 'runs/operator_pi05_multifamily_worker001.py'), '--root', str(broker)],
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
            OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'),
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    children.append(service)
    deadline = time.monotonic() + 900
    while not (broker / 'service-ready.json').exists():
        if service.poll() is not None:
            raise RuntimeError('shared policy startup failed; no retry')
        if time.monotonic() > deadline:
            raise TimeoutError('shared policy startup')
        time.sleep(.2)
    wave_start = time.perf_counter()
    waves = {}
    for offset, task in enumerate(('classify_objects', 'build_tower')):
        tag = f'{a.tag_base + offset:03d}'
        log = (out / (task + '.log')).open('x')
        logs.append(log)
        command = [str(Path('/root/miniconda3/envs/RoboDojo/bin/python3.11')), '-u',
            str(ROOT / 'runs/operator_vector_pi05_rollout002.py'), '--task', task,
            '--tag', tag, '--num-envs', str(a.sorting_envs if offset == 0 else a.tower_envs), '--steps', str(a.steps),
            '--shared-worker-root', str(broker), '--inference-mode', 'native_singleton',
            '--semantic-config', str(a.semantic_config)]
        if a.allow_api:
            command.append('--allow-api')
        child = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES='0',
            OMNI_KIT_ACCEPT_EULA='YES', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4'),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        children.append(child)
        waves[task] = child
        count = a.sorting_envs if offset == 0 else a.tower_envs
        report['wave_outputs'][task] = str(ROOT / f'runs/vector-pi05-{count}-{tag}')
    write_json(out / 'report.json', report)
    deadline = time.monotonic() + a.wall_limit_s
    while any(child.poll() is None for child in waves.values()):
        if service.poll() is not None:
            raise RuntimeError('shared runtime exited during waves; no retry')
        if any(child.poll() not in (None, 0) for child in waves.values()):
            raise RuntimeError('wave failed; stop owned work and retain partial evidence')
        if time.monotonic() > deadline:
            raise TimeoutError('multi-family wave wall limit')
        time.sleep(1)
    report['concurrent_wave_wall_including_sim_setup_s'] = time.perf_counter() - wave_start
    report['waves'] = {task: json.loads((Path(path) / 'report.json').read_text())
        for task, path in report['wave_outputs'].items()}
    report['paid_calls'] = sum(wave['paid_calls'] for wave in report['waves'].values())
    assert all(wave['status'] in ('incomplete_semantic_wave', 'native_terminal_semantic_wave')
        for wave in report['waves'].values())
    report['status'] = ('native_terminal_concurrent_waves'
        if all(wave['status'] == 'native_terminal_semantic_wave' for wave in report['waves'].values())
        else 'bounded_concurrent_waves_completed')
except BaseException as exc:
    report.update(status='error_stop_no_retry', error=type(exc).__name__ + ': ' + str(exc))
    raise
finally:
    (broker / 'stop-service').touch()
    if children:
        try:
            children[0].wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
    for child in reversed(children):
        stop_child(child)
    for log in logs:
        log.close()
    report['total_wall_s'] = time.perf_counter() - start
    write_json(out / 'report.json', report)
    print(json.dumps(report), flush=True)
