import os
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

root = Path('/root/physical-execution-lab')
os.chdir(root)
sys.path.insert(0, str(root))
from k1lab.util import atomic_json, load_json, file_sha, digest
from semantic_lab.protocol import code_fingerprint, verify, freeze
from k1lab.multibench.manifest import resolved_config
from scripts.multibench.run_pi05_native_pilot import wait_ready
from scripts.multibench.launch_robodojo_case import stop_child

bound = root / 'configs/local/semantic-pi05-hierarchy-001'
p = argparse.ArgumentParser()
p.add_argument('--condition', choices=('motor_only', 'task_plus_subtask', 'subtask_only'), default='motor_only')
p.add_argument('--case-id', default='build_tower__standard__g0__l0')
p.add_argument('--worker-gpu', type=int, choices=(0, 1), default=0)
a = p.parse_args()
assert a.case_id in load_json(bound / 'roster-plan.json')['cases']
label = 'motor' if a.condition == 'motor_only' else a.condition
config_path = bound / ('robodojo_pi05_robodojo_semantic_v5_' + label + '_matched_dev_001.json')
cfg = resolved_config(load_json(config_path))
verify(root, load_json(bound / 'freeze.json'), load_json(root / 'configs/local/robodojo-cases.json'),
    cfg, load_json(bound / (cfg['name'] + '.qualification.json')))
if shutil.disk_usage(root).free < 3 * 1024**3:
    raise RuntimeError('insufficient disk for fresh matched baseline')
old = root / 'runs/semantic-pi05-dev-001/motor_only'
cohort = 'semantic-pi05-hierarchy-001' if a.worker_gpu == 0 else 'semantic-pi05-hierarchy-parallel-001'
out = root / 'runs' / cohort / a.condition / a.case_id
out.mkdir(parents=True, exist_ok=False)
provider = load_json(root / 'configs/local/pi05-exact-bound-001/provider.json')
provider['artifact_dir'] = str(out / 'source-policy-proposals')
if a.worker_gpu == 1:
    provider['port'] = 19115
    provider['identity'].pop('adapter_config_sha256')
    provider = resolved_config({'policy': provider})['policy']
    if a.condition != 'motor_only':
        baseline = root / 'runs' / cohort / 'motor_only' / a.case_id
        if load_json(baseline / 'episode/controller/result.json')['status'] != 'native_completed':
            raise RuntimeError('GPU1 candidate requires a terminal retained control')
        if load_json(baseline / 'provider.json')['identity'] != provider['identity']:
            raise RuntimeError('GPU1 control/candidate policy binding differs')
        baseline_audit = load_json(baseline / 'offline-audit.json')
        if not all(baseline_audit.get(k) is True for k in ('source_npz_proposals_match_journal',
                'prefix_cadence_verified', 'controller_evaluator_agree')):
            raise RuntimeError('GPU1 control lacks matching source/cadence/scoring audit')
    cfg['name'] += '_gpu1_transport_variant'
    cfg['policy']['endpoint'] = 'http://127.0.0.1:19604'
    cfg['policy']['identity'] = provider['identity']
    cfg = resolved_config(cfg)
    variant = out / 'worker-binding'
    variant.mkdir()
    config_path = variant / 'config.json'
    qualification = load_json(bound / ('robodojo_pi05_robodojo_semantic_v5_' + label + '_matched_dev_001.qualification.json'))
    qualification['config_sha256'] = digest(cfg)
    qualification['transport_rebinding'] = {
        'original_freeze_sha256': file_sha(bound / 'freeze.json'),
        'gpu': 1, 'source_port': 19115, 'bridge_port': 19604, 'sim_port': 19118,
        'scope': 'inherited tested stateless cadence/prompt seam; distinct transport cohort, not new physical parity evidence'}
    worker_freeze = freeze(root, load_json(root / 'configs/local/robodojo-cases.json'), [cfg])
    verify(root, worker_freeze, load_json(root / 'configs/local/robodojo-cases.json'), cfg, qualification)
    atomic_json(config_path, cfg, exclusive=True)
    atomic_json(variant / 'freeze.json', worker_freeze, exclusive=True)
    atomic_json(variant / 'qualification.json', qualification, exclusive=True)
atomic_json(out / 'provider.json', provider, exclusive=True)
previous = load_json(old / 'operator-plan.json')
source_cmd = [s.replace(str(old), str(out)) for s in previous['source']]
if a.worker_gpu == 1:
    source_cmd[source_cmd.index('--port') + 1] = '19115'
bridge_cmd = [str(root / '.venv-pi05/bin/python'), '-u', str(root / 'run_semantic.py'),
    'serve-policy', '--config', str(out / 'provider.json'), '--port', '19603', '--allow-policy']
old_config = str(root / 'configs/local/semantic-pi05-dev-001/robodojo_pi05_robodojo_semantic_v5_motor.json')
episode_cmd = [s.replace(str(old), str(out)).replace(old_config, str(config_path)) for s in previous['episode']]
episode_cmd[episode_cmd.index('--case-id') + 1] = a.case_id
if a.worker_gpu == 1:
    bridge_cmd[bridge_cmd.index('--port') + 1] = '19604'
    episode_cmd[episode_cmd.index('--sim-port') + 1] = '19118'
if a.condition != 'motor_only':
    episode_cmd.append('--allow-api')
atomic_json(out / 'operator-plan.json', {'source': source_cmd, 'bridge': bridge_cmd,
    'episode': episode_cmd, 'source_sha256': code_fingerprint(root),
    'freeze_sha256': file_sha(bound / 'freeze.json'), 'no_paid_calls': a.condition == 'motor_only',
    'case_id': a.case_id, 'condition': a.condition,
    'priority': 'existing hard development case, not panel replacement',
    'no_automatic_retry': True, 'same_gpu_as_candidate': a.worker_gpu == 0,
    'worker_gpu': a.worker_gpu, 'transport_variant': a.worker_gpu == 1}, exclusive=True)
shutil.copytree(bound, out / 'bound-config')
env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(a.worker_gpu), XLA_PYTHON_CLIENT_PREALLOCATE='false',
    PYTHONPATH=str(root / 'external/GPT-as-Policy'), OMP_NUM_THREADS='4', MKL_NUM_THREADS='4')
if a.condition != 'motor_only':
    env['K1_RELAY_TOKEN'] = (root / 'configs/local/semantic-pi05-dev-001/relay-token').read_text().strip()
children = []
try:
    for key, cmd, event in [('source', source_cmd, 'loaded'), ('bridge', bridge_cmd, 'ready')]:
        with (out / (key + '.log')).open('x') as log:
            child = subprocess.Popen(cmd, cwd=root, env=env, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            wait_ready(child, out / (key + '.log'),
                lambda row: row.get('event') == event or row.get(event) is True, timeout=900)
    print('fresh matched ' + a.condition + ' ' + a.case_id + ' starting', flush=True)
    with (out / 'launcher.log').open('x') as log:
        child = subprocess.Popen(episode_cmd, cwd=root, env=dict(env, OMNI_KIT_ACCEPT_EULA='YES'),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        children.append(child)
        code = child.wait(timeout=4800)
        result = out / 'episode/controller/result.json'
        if result.exists():
            print(result.read_text(), flush=True)
        if code:
            if result.exists() and load_json(result)['status'] == 'planner_stop_incomplete':
                print('semantic abstention retained as incomplete, not an operator fault', flush=True)
            else:
                raise RuntimeError('condition error retained; no automatic retry')
finally:
    for child in reversed(children):
        stop_child(child)
    if a.condition != 'motor_only':
        (root / 'configs/local/semantic-pi05-dev-001/relay-token').unlink(missing_ok=True)
