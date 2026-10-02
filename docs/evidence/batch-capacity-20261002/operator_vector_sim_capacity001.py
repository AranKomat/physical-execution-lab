import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path('/root/physical-execution-lab')
sys.path[:0] = [str(root / 'external/RoboDojo'), str(root / 'external/GPT-as-Policy'),
    str(root / 'external/XPolicyLab')]
import cv2
from isaaclab.app import AppLauncher

p = argparse.ArgumentParser()
p.add_argument('--num-envs', type=int, choices=(2, 5), required=True)
p.add_argument('--tag', default='001')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.headless = True
a.enable_cameras = True
assert a.tag.isdigit()
out = root / ('runs/vector-sim-capacity-' + str(a.num_envs) + '-' + a.tag)
out.mkdir(exist_ok=False)

def memory():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.free',
        '--format=csv,noheader,nounits'], text=True)

before = memory()
start = time.perf_counter()
app = AppLauncher(a).app
env = None
report = {'num_envs_requested': a.num_envs, 'before': before,
    'scope': 'same-task vector reset/render capacity, not mixed-task evaluation or scored rollout',
    'control_actions': 0, 'paid_calls': 0, 'policy_calls': 0}
try:
    import importlib
    import numpy as np
    from omegaconf import OmegaConf
    from env.global_configs import ENV_CONFIG_PATH, ROOT_DIR, BENCHMARK
    from utils.load_file import load_yaml
    from utils.pipeline_utils import process_config, process_randomization
    from src.eval_client import eval_env
    from hybrid_rollout.robodojo.robodojo_server.server import NoPolicyConnection
    registry = importlib.import_module(f'task.{BENCHMARK}.task_registry')
    config_root = Path(ENV_CONFIG_PATH)
    evaluation = load_yaml(str(config_root / 'arx_x5.yml'))
    evaluation.update(task_name='classify_objects', num_envs=a.num_envs, device_id=0,
        eval_batch=True, policy_name='Pi_05', additional_info='capacity_only', seed=0,
        physx_monitor_enabled=False)
    values = {key: load_yaml(str(config_root / key / (evaluation['config'][key] + '.yml')))
        for key in ('sim', 'scene', 'camera', 'robot')}
    values.update(eval_cfg=evaluation, deploy_cfg=dict(port=1, policy_name='Pi_05'),
        task_env=load_yaml(registry.task_config_path(str(Path(ROOT_DIR) / 'task' / BENCHMARK / 'config'), 'classify_objects')))
    cfg = OmegaConf.create(values)
    cfg.sim.scene.num_envs = a.num_envs
    cfg = process_randomization(cfg)
    cfg, _ = process_config(cfg, task_name='classify_objects')
    cfg.eval_cfg.eval_num = a.num_envs
    cfg.camera.default_frequency = cfg.eval_cfg.observation.collect_freq
    cfg.sim.seed = [0] * a.num_envs
    for robot in cfg.robot.robots:
        robot.need_planner = False
    original = eval_env.WsModelClient
    try:
        eval_env.WsModelClient = NoPolicyConnection
        env = eval_env.create_eval_env(cfg, app)
    finally:
        eval_env.WsModelClient = original
    assert env.num_envs == a.num_envs
    seeds = [0, 1, 2, 0, 1][:a.num_envs]
    env.reset(seed=seeds)
    observations = env.get_obs_batch(env_idx_list=list(range(a.num_envs)))
    assert len(observations) == a.num_envs
    checks = []
    for index, observation in enumerate(observations):
        assert int(observation['env_idx']) == index
        cameras = {}
        for name in ('cam_head', 'cam_left_wrist', 'cam_right_wrist'):
            image = np.asarray(observation['vision'][name]['color'])
            assert image.ndim == 3 and image.shape[-1] == 3 and float(image.std()) > 1
            cameras[name] = {'shape': list(image.shape), 'std': float(image.std())}
        checks.append({'env_idx': index, 'seed': seeds[index], 'cameras': cameras})
    report.update(status='vector_reset_render_passed', reset_seeds=seeds,
        environment_count=env.num_envs, camera_checks=checks, loaded_memory=memory(),
        elapsed_s=time.perf_counter() - start)
except Exception as exc:
    report.update(status='error_stop_no_retry', error=type(exc).__name__ + ': ' + str(exc),
        loaded_memory=memory(), elapsed_s=time.perf_counter() - start)
    raise
finally:
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    if env is not None:
        env.close()
    app.close()
