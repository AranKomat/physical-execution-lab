import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path('/root/physical-execution-lab')
sys.path.insert(0, str(root))
from k1lab.util import load_json, atomic_json
from k1lab.multibench.adapters.robodojo import RoboDojoRPC
from scripts.multibench.launch_robodojo_case import source_ready, stop_child

out = root / 'runs/parallel-capacity-simonly-001'
out.mkdir(exist_ok=False)
base = root / 'runs/semantic-pi05-hierarchy-001/motor_only/classify_objects__standard__g0__l0/episode'
launch = load_json(base / 'launch.json')
assert launch['case']['partition'] == 'dev'
native = out / 'native'
native.mkdir()
atomic_json(out / 'source_case.json', load_json(base / 'source_case.json'), exclusive=True)
command = [s.replace(str(base), str(out)) for s in launch['server_argv']]
command[command.index('--port') + 1] = '19119'
env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES',
    OMP_NUM_THREADS='4', MKL_NUM_THREADS='4',
    PYTHONPATH=os.pathsep.join(str(root / 'external' / p) for p in ('GPT-as-Policy', 'RoboDojo', 'XPolicyLab')))

def memory():
    raw = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.free',
        '--format=csv,noheader,nounits'], text=True)
    return [{'gpu': int(a), 'used_mib': int(b), 'free_mib': int(c)}
        for a, b, c in (line.split(',') for line in raw.splitlines())]

before = memory()
assert before[0]['free_mib'] >= 7500, 'not enough headroom for an extra simulator probe'
samples = []
child = robot = None
status = 'starting'
try:
    with (out / 'server.log').open('x') as stream:
        child = subprocess.Popen(command, cwd=launch['server_cwd'], env=env,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        end = time.monotonic() + 600
        while not source_ready(out / 'server.log'):
            row = memory()
            samples.append(row)
            if row[0]['free_mib'] < 2500:
                status = 'capacity_guard_stop'
                raise RuntimeError('extra simulator stopped to preserve primary worker headroom')
            if child.poll() is not None or time.monotonic() > end:
                raise RuntimeError('extra simulator did not become ready; no retry')
            time.sleep(1)
        cfg = load_json(root / 'configs/local/semantic-pi05-hierarchy-001/robodojo_pi05_robodojo_semantic_v5_motor_matched_dev_001.json')
        robot = RoboDojoRPC(cfg['environment'] | {'sim_port': 19119,
            'native_outcome_path': str(native / 'evaluation_outcome.json')})
        observation = robot.reset(launch['case'])
        assert observation.step == 0
        for _ in range(10):
            row = memory()
            samples.append(row)
            if row[0]['free_mib'] < 2500:
                status = 'capacity_guard_stop'
                raise RuntimeError('extra simulator stopped to preserve primary worker headroom')
            time.sleep(.5)
        robot.finish('capacity_probe_no_actions_not_task_attempt')
        status = 'reset_render_completed_no_actions'
finally:
    if robot:
        robot.close()
    stop_child(child)
    atomic_json(out / 'report.json', {'status': status, 'before': before, 'samples': samples,
        'after': memory(), 'simulator_port': 19119, 'gpu': 0, 'case_id': launch['case']['case_id'],
        'command': command, 'control_actions': 0, 'policy_calls': 0, 'paid_calls': 0,
        'no_task_success_claim': True, 'scope': 'one extra reset/render simulator beside a live policy+sim worker; not five-task throughput'}, exclusive=True)
    print(json.dumps(load_json(out / 'report.json') | {'samples': len(samples)}), flush=True)
