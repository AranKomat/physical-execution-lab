#!/usr/bin/env python3
"""Run concurrent distinct native tasks in one physically compatible scene group."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'external/RoboDojo'), str(ROOT / 'external/GPT-as-Policy'),
                str(ROOT / 'external/XPolicyLab'), str(ROOT)]
from semantic_lab.native_io import memory, wait_file, write_json


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cases', type=Path, required=True)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--allow-api', action='store_true')
    p.add_argument('--freeze', type=Path)
    p.add_argument('--panel', type=Path)
    p.add_argument('--baseline-group', type=Path)
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args()
    cases = json.loads(args.cases.read_text())
    treatment = json.loads(args.config.read_text())
    methods = {'motor_only': 'original_only', 'direct_sparse': 'direct',
               'sparse': 'numeric', 'semantic_subtask_hierarchy': 'semantic'}
    if treatment['mode'] not in methods or args.allow_api != (treatment['mode'] != 'motor_only'):
        raise ValueError('unsupported condition or mismatched explicit API enablement')
    direct = treatment['mode'] == 'direct_sparse'
    frozen = panel = None
    if args.allow_api:
        if args.freeze is None or args.panel is None or args.baseline_group is None:
            raise ValueError('paid task groups require the complete panel and execution-source freeze')
        from semantic_lab.protocol import verify_binding
        frozen, panel = json.loads(args.freeze.read_text()), json.loads(args.panel.read_text())
        verify_binding(ROOT, frozen, panel, treatment, require_execution_sources=True)
        fixed = {case['case_id']: case for case in panel['cases']}
        if any(fixed.get(case['case_id']) != case for case in cases):
            raise ValueError('task group differs from the frozen panel')
    if not cases or len({case['task_group'] for case in cases}) != len(cases):
        raise ValueError('scene group requires distinct fixed tasks')
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'runs') or not out.is_dir():
        raise ValueError('output must be a precreated cohort run directory')
    if (out / 'report.json').exists():
        raise ValueError('existing group result; no automatic restart')
    args.headless, args.enable_cameras = True, True
    os.environ['ROBODOJO_RUN_ID'] = out.name
    app = env = None
    started = time.perf_counter()
    report = dict(status='starting', method=methods[treatment['mode']], paid_calls=0,
        distinct_tasks=[case['task_group'] for case in cases],
        scope='full fixed-task execution integration; native-equivalence admission pending',
        benchmark_qualified=False, automatic_retry=False)
    write_json(out / 'report.json', report)
    try:
        app = AppLauncher(args).app
        from omegaconf import OmegaConf
        from env.global_configs import ENV_CONFIG_PATH, ROOT_DIR, BENCHMARK
        from utils.load_file import load_yaml
        from utils.pipeline_utils import process_config, process_randomization
        from src.eval_client import eval_env
        from hybrid_rollout.robodojo.robodojo_server.server import NoPolicyConnection
        from semantic_lab.task_rows import create_mixed_eval_env
        registry = importlib.import_module(f'task.{BENCHMARK}.task_registry')
        config_root = Path(ENV_CONFIG_PATH)
        configs = []
        for case in cases:
            evaluation = load_yaml(str(config_root / 'arx_x5.yml'))
            evaluation.update(task_name=case['runtime_task'], num_envs=len(cases), device_id=0,
                eval_batch=True, policy_name='Pi_05', additional_info='distinct_task_cohort',
                seed=case['eval_seed'], physx_monitor_enabled=True)
            values = {key: load_yaml(str(config_root / key / (evaluation['config'][key] + '.yml')))
                      for key in ('sim', 'scene', 'camera', 'robot')}
            values.update(eval_cfg=evaluation, deploy_cfg=dict(port=1, policy_name='Pi_05'),
                task_env=load_yaml(registry.task_config_path(
                    str(Path(ROOT_DIR) / 'task' / BENCHMARK / 'config'), case['runtime_task'])))
            cfg = OmegaConf.create(values)
            cfg.sim.scene.num_envs = len(cases)
            cfg = process_randomization(cfg)
            cfg, _ = process_config(cfg, task_name=case['runtime_task'])
            cfg.eval_cfg.eval_num = len(cases)
            cfg.camera.default_frequency = cfg.eval_cfg.observation.collect_freq
            cfg.sim.seed = [0] * len(cases)
            for robot in cfg.robot.robots:
                robot.need_planner = False
            configs.append(cfg)
            layout = ROOT / 'external/RoboDojo' / case['layout_path']
            if hashlib.sha256(layout.read_bytes()).hexdigest() != case['layout_sha256']:
                raise ValueError('fixed layout hash mismatch')
        original = eval_env.WsModelClient
        try:
            eval_env.WsModelClient = NoPolicyConnection
            env = create_mixed_eval_env(configs, app)
        finally:
            eval_env.WsModelClient = original
        # Retain exact requests/actions instead of unbounded RGB movie buffers.
        env._stream_vision = lambda *args, **kwargs: None
        env.reset(seed=[0] * len(cases))
        if env.step_limits != [case['horizon'] for case in cases]:
            raise ValueError('native per-task horizons differ from the fixed roster')
        bindings = []
        for idx, (directory, case) in enumerate(zip(env.task_seed_managers, cases)):
            path = Path(directory.seed_info[0]['scene_layout'])
            if path.resolve() != (ROOT / 'external/RoboDojo' / case['layout_path']).resolve():
                raise ValueError('native row selected another task/layout')
            bindings.append(dict(env_idx=idx, case_id=case['case_id'], path=str(path),
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        write_json(out / 'resolved-configs.json', [OmegaConf.to_container(cfg, resolve=True) for cfg in configs])
        write_json(out / 'task-bindings.json', bindings)
        env.run_reward()
        env.get_score()
        if env.interact:
            for idx in range(len(cases)):
                env.query_support_arm_traj(idx)
        report.update(status='native_ready', startup_s=time.perf_counter()-started,
                      memory=memory(), native_horizons=env.step_limits, layout_bindings=bindings)
        write_json(out / 'report.json', report)
        if not direct:
            wait_file(out / 'worker-ready.json')
        if frozen:
            verify_binding(ROOT, frozen, panel, treatment, require_execution_sources=True)
        args.semantic_config, args.num_envs = args.config, len(cases)
        args.policy, args.inference_mode = 'pi05', 'vmap_source_singleton_sampling'
        args.controller_probe = False
        args.steps = max(case['horizon'] for case in cases)
        args.reference_cases = cases
        if args.allow_api:
            import numpy as np
            from types import SimpleNamespace
            from semantic_lab.cohort_admission import check_reset
            observations = {}
            for raw in env.get_obs_batch(env_idx_list=list(range(len(cases)))):
                state = raw['state']
                idx = int(raw['env_idx'])
                observations[idx] = SimpleNamespace(step=int(env.take_action_cnt[idx]),
                    instruction=raw['instruction'], state=np.concatenate([
                        np.r_[state[f'{arm}_arm_joint_state'], state[f'{arm}_ee_joint_state']]
                        for arm in ('left', 'right')]).astype(np.float32))
            admission = check_reset(args.baseline_group, cases,
                [OmegaConf.to_container(cfg, resolve=True) for cfg in configs],
                bindings, env.step_limits, observations)
            if treatment['mode'] in ('direct_sparse', 'sparse'):
                from semantic_lab.robot_controls import SourceRobotControls
                from hybrid_rollout.robodojo.robodojo_server.kinematics import DualKinematics
                controls = SourceRobotControls(env.robot_manager, range(len(cases)), DualKinematics)
                admission['initial_fk_checks'] = controls.initial_fk_checks
            write_json(out / 'pre-action-admission.json', admission)
            wait_file(out / 'cohort-admitted.json')
        from semantic_lab.native_execution import run_wave
        run_wave(env, out, args, report, None)
    except BaseException as exc:
        report.update(status='error_stop_no_retry', error=f'{type(exc).__name__}: {exc}')
        write_json(out / 'report.json', report)
        raise
    finally:
        (out / 'stop-worker').touch()
        if env is not None:
            env.close()
        if app is not None:
            app.close()


if __name__ == '__main__':
    main()
