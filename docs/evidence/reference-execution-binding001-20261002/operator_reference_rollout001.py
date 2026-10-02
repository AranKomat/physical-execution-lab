"""Experimental native vector rollout; not the frozen semantic runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/root/physical-execution-lab')


def write_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def wait_file(path, child=None, timeout=300):
    start = time.monotonic()
    while not path.exists():
        if (path.parent / 'worker-error.json').exists():
            raise RuntimeError((path.parent / 'worker-error.json').read_text())
        if child is not None and child.poll() is not None:
            raise RuntimeError('policy worker exited; no retry')
        if time.monotonic() - start > timeout:
            raise TimeoutError(str(path))
        time.sleep(.05)


def memory():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,memory.free',
        '--format=csv,noheader,nounits'], text=True)


def worker(out, inference_mode):
    sys.path[:0] = [str(ROOT), str(ROOT / 'external/GPT-as-Policy')]
    import jax
    import jax.numpy as jnp
    import numpy as np
    from openpi.models.model import Observation
    from openpi.policies.policy_config import create_trained_policy
    from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract, checkpoint_identity
    provider = json.loads((ROOT / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
    checkpoint = Path(provider['checkpoint_path'])
    cfg, _ = data_contract(checkpoint)
    policy = create_trained_policy(cfg, checkpoint)
    write_json(out / 'worker-ready.json', {'identity': checkpoint_identity(checkpoint),
        'inference_mode': inference_mode,
        'rng': 'separate native seed0 streams per env' if inference_mode == 'native_singleton'
            else 'one seed0 JAX stream per fused wave; not isolated per-episode parity',
        'memory': memory()})
    rng = jax.random.key(0)
    keys = {}
    calls = {}
    index = 0
    while not (out / 'stop-worker').exists():
        request = out / f'request-{index:04d}.npz'
        if not request.exists():
            time.sleep(.05)
            continue
        start = time.perf_counter()
        with np.load(request, allow_pickle=False) as data:
            env_ids = data['env_ids'].copy()
            raws = [{'state': data['states'][i].copy(),
                'prompt': str(data['prompts'][i]), 'images': {
                    name: np.transpose(data[name][i], (2, 0, 1)).copy()
                    for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}}
                for i in range(len(env_ids))]
        if inference_mode == 'native_singleton':
            values = []
            for idx, raw in zip(env_ids.tolist(), raws):
                policy._rng = keys.get(idx, jax.random.key(0))
                values.append(np.asarray(policy.infer(raw)['actions'], np.float32))
                keys[idx] = policy._rng
                calls[idx] = calls.get(idx, 0) + 1
            result = np.stack(values)
        else:
            rows = [policy._input_transform(raw) for raw in raws]
            inputs = jax.tree.map(lambda *x: jnp.asarray(np.stack(x)), *rows)
            rng, sample_rng = jax.random.split(rng)
            actions = policy._sample_actions(sample_rng, Observation.from_dict(inputs), **policy._sample_kwargs)
            actions.block_until_ready()
            result = np.stack([policy._output_transform({'state': np.asarray(inputs['state'][i]),
                'actions': np.asarray(actions[i])})['actions'] for i in range(len(env_ids))])
        assert result.shape == (len(env_ids), 50, 14) and np.isfinite(result).all()
        raw = np.asarray(result, np.float32)
        result = raw.copy()
        # Match the pinned Pi05Client's continuous-opening conversion.
        result[:, :, [6, 13]] = np.clip(result[:, :, [6, 13]], 0., 1.)
        np.savez_compressed(out / f'prediction-{index:04d}.npz', actions=result,
            raw_actions=raw, env_ids=env_ids)
        write_json(out / f'prediction-{index:04d}.json', {'inference_s': time.perf_counter() - start,
            'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
            'env_ids': env_ids.tolist(), 'memory': memory(), 'inference_mode': inference_mode,
            'native_calls_per_env': calls,
            'rng_keys_after': {str(idx): jax.random.key_data(key).tolist() for idx, key in keys.items()}})
        index += 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--worker', type=Path)
    p.add_argument('--policy', choices=('pi05', 'g05'), default='pi05')
    p.add_argument('--worker-gpu', choices=(0, 1), type=int, default=1)
    p.add_argument('--shared-worker-root', type=Path)
    p.add_argument('--semantic-config', type=Path)
    p.add_argument('--execution-freeze', type=Path)
    p.add_argument('--allow-api', action='store_true')
    p.add_argument('--tag', default='001')
    p.add_argument('--steps', type=int, default=150)
    p.add_argument('--num-envs', type=int, choices=(1, 2, 3, 4, 5), default=5)
    p.add_argument('--task')
    p.add_argument('--case-manifest', type=Path)
    p.add_argument('--case-ids', nargs='+')
    p.add_argument('--inference-mode', choices=('native_singleton', 'fused'), default='native_singleton')
    if '--worker' in sys.argv:
        args = p.parse_args()
        if args.policy == 'g05':
            from operator_vector_g05_worker001 import worker as g05_worker
            g05_worker(args.worker, args.inference_mode)
        else:
            worker(args.worker, args.inference_mode)
        return
    sys.path[:0] = [str(ROOT / 'external/RoboDojo'), str(ROOT / 'external/GPT-as-Policy'),
        str(ROOT / 'external/XPolicyLab'), str(ROOT)]
    import cv2
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(p)
    args = p.parse_args()
    from semantic_lab.reference import bind_reference_wave
    assert args.case_manifest is not None and args.case_ids is not None
    args.reference_cases = bind_reference_wave(json.loads(args.case_manifest.read_text()), args.case_ids, args.task)
    assert len(args.reference_cases) == args.num_envs
    assert all(row['task_group'] in ('classify_objects', 'build_tower', 'arrange_largest_number') for row in args.reference_cases), 'untouched tasks require a separately qualified frozen executor'
    assert args.tag.isdigit() and 1 <= args.steps <= args.reference_cases[0]['horizon']
    assert args.policy == 'pi05' and args.semantic_config is not None
    from semantic_lab.protocol import verify_binding
    assert args.execution_freeze is not None, 'reference execution-source freeze required'
    frozen = json.loads(args.execution_freeze.read_text())
    manifest = json.loads(args.case_manifest.read_text())
    semantic_config = json.loads(args.semantic_config.read_text())
    verify_binding(ROOT, frozen, manifest, semantic_config, require_execution_sources=True)
    args.headless = True
    args.enable_cameras = True
    prefix_steps = 16 if args.policy == 'g05' else 15
    out = ROOT / f'runs/reference-{args.policy}-{args.num_envs}-{args.tag}'
    out.mkdir(exist_ok=False)
    log = (out / 'worker.log').open('x')
    python = ROOT / ('.venv-g05-fla/bin/python' if args.policy == 'g05' else '.venv-pi05/bin/python')
    child = None
    if args.shared_worker_root is not None:
        assert args.policy == 'pi05' and args.inference_mode == 'native_singleton'
        broker = args.shared_worker_root.resolve()
        assert broker.is_relative_to(ROOT / 'runs') and broker.is_dir()
        assert not (broker / 'stop-service').exists()
        write_json(broker / (out.name + '.registration.json'), {'output': str(out)})
    else:
        child = subprocess.Popen([str(python), '-u', __file__, '--worker', str(out),
            '--policy', args.policy, '--inference-mode', args.inference_mode],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(args.worker_gpu), XLA_PYTHON_CLIENT_PREALLOCATE='false'),
            stdout=log, stderr=subprocess.STDOUT)
    app = env = None
    report = {'status': 'started', 'scope': 'experimental vector motor rollout, separate execution cohort',
        'paid_calls': 0, 'resets': 1, 'task': args.task, 'requested_envs': args.num_envs,
        'budget_steps_per_env': args.steps, 'physics_of_completed_envs': 'continues globally; terminal score frozen',
        'rng_parity': False, 'inference_mode': args.inference_mode, 'scored_benchmark_qualified': False}
    report.update(policy=args.policy, execute_steps=prefix_steps,
        returned_action_steps=16 if args.policy == 'g05' else 50,
        native_prediction_horizon=32 if args.policy == 'g05' else 50)
    report['shared_worker_root'] = str(args.shared_worker_root) if args.shared_worker_root else None
    report['execution_freeze_sha256'] = frozen['sha256']
    report['execution_sources_sha256'] = frozen['execution_sources']['sha256']
    report['execution_binding_is_native_qualification'] = False
    report['reference_cases'] = args.reference_cases
    report['reference_manifest_file_sha256'] = hashlib.sha256(args.case_manifest.read_bytes()).hexdigest()
    report['scope'] = 'reference-bound historical-opened task execution; not untouched held-out qualification'
    bound_sources = [Path(__file__), ROOT / 'runs/operator_reference_native001.py',
        ROOT / 'runs/operator_semantic_vector_coordinator001.py', ROOT / 'semantic_lab/reference.py',
        ROOT / 'semantic_lab/planner.py', ROOT / 'semantic_lab/report.py']
    write_json(out / 'pre-action-binding.json', {'report': report,
        'semantic_config_file_sha256': hashlib.sha256(args.semantic_config.read_bytes()).hexdigest(),
        'sources': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in bound_sources}})
    try:
        app = AppLauncher(args).app
        import importlib
        import numpy as np
        from omegaconf import OmegaConf
        from env.global_configs import ENV_CONFIG_PATH, ROOT_DIR, BENCHMARK
        from utils.load_file import load_yaml
        from utils.pipeline_utils import process_config, process_randomization
        from src.eval_client import eval_env
        from hybrid_rollout.robodojo.robodojo_server.server import NoPolicyConnection
        from hybrid_rollout.robodojo.robodojo_server.session import register_native_evaluation
        registry = importlib.import_module(f'task.{BENCHMARK}.task_registry')
        config_root = Path(ENV_CONFIG_PATH)
        evaluation = load_yaml(str(config_root / 'arx_x5.yml'))
        evaluation.update(task_name=args.task, num_envs=args.num_envs, device_id=0, eval_batch=True,
            policy_name='G05' if args.policy == 'g05' else 'Pi_05',
            additional_info='vector_motor_probe', seed=0, physx_monitor_enabled=False)
        values = {key: load_yaml(str(config_root / key / (evaluation['config'][key] + '.yml')))
            for key in ('sim', 'scene', 'camera', 'robot')}
        values.update(eval_cfg=evaluation, deploy_cfg=dict(port=1, policy_name='Pi_05'),
            task_env=load_yaml(registry.task_config_path(str(Path(ROOT_DIR) / 'task' / BENCHMARK / 'config'), args.task)))
        cfg = OmegaConf.create(values)
        cfg.sim.scene.num_envs = args.num_envs
        cfg = process_randomization(cfg)
        cfg, _ = process_config(cfg, task_name=args.task)
        cfg.eval_cfg.eval_num = args.num_envs
        cfg.camera.default_frequency = cfg.eval_cfg.observation.collect_freq
        cfg.sim.seed = [0] * args.num_envs
        for robot in cfg.robot.robots:
            robot.need_planner = False
        original = eval_env.WsModelClient
        try:
            eval_env.WsModelClient = NoPolicyConnection
            env = eval_env.create_eval_env(cfg, app)
        finally:
            eval_env.WsModelClient = original
        env._stream_vision = lambda *a, **k: None
        seeds = [case['layout_id'] for case in args.reference_cases]
        env.reset(seed=seeds)
        report['native_registration'] = register_native_evaluation(env)
        report['reset_seeds'] = seeds
        report['layout_bindings'] = [{'env_idx': idx, 'layout_id': seed,
            'path': str(env.seed_manager.seed_info[seed]['scene_layout']),
            'sha256': hashlib.sha256(Path(env.seed_manager.seed_info[seed]['scene_layout']).read_bytes()).hexdigest()}
            for idx, seed in enumerate(seeds)]
        assert env.step_lim == args.reference_cases[0]['horizon']
        for actual, expected in zip(report['layout_bindings'], args.reference_cases):
            assert actual['sha256'] == expected['layout_sha256']
            assert Path(actual['path']).resolve() == (ROOT / 'external/RoboDojo' / expected['layout_path']).resolve()
        write_json(out / 'resolved-config.json', OmegaConf.to_container(cfg, resolve=True))
        wait_file(out / 'worker-ready.json', child, timeout=900)
        verify_binding(ROOT, frozen, json.loads(args.case_manifest.read_text()),
            json.loads(args.semantic_config.read_text()), require_execution_sources=True)
        if args.semantic_config is not None:
            from operator_reference_native001 import run_wave
            report = run_wave(env, out, args, report, child)
            return
        start = time.perf_counter()
        terminal = {}
        active = list(range(args.num_envs))
        prediction = 0
        with (out / 'actions.jsonl').open('x') as journal:
            while active and max(env.take_action_cnt) < args.steps:
                raw = env.get_obs_batch(env_idx_list=active)
                assert [int(row['env_idx']) for row in raw] == active
                states = np.stack([np.concatenate([np.r_[row['state'][f'{arm}_arm_joint_state'],
                    row['state'][f'{arm}_ee_joint_state']] for arm in ('left', 'right')]).astype(np.float32)
                    for row in raw])
                camera_data = {name: np.stack([np.asarray(row['vision'][native]['color'], np.uint8)[..., :3]
                    for row in raw]) for name, native in (('cam_high', 'cam_head'),
                    ('cam_left_wrist', 'cam_left_wrist'), ('cam_right_wrist', 'cam_right_wrist'))}
                assert states.shape == (len(active), 14) and np.isfinite(states).all()
                request = out / f'request-{prediction:04d}.npz'
                with request.with_suffix('.tmp').open('xb') as stream:
                    np.savez_compressed(stream, states=states,
                        prompts=np.array([row['instruction'] for row in raw]), env_ids=np.array(active),
                        steps=np.array([env.take_action_cnt[i] for i in active]), **camera_data)
                request.with_suffix('.tmp').replace(request)
                wait_file(out / f'prediction-{prediction:04d}.json', child)
                with np.load(out / f'prediction-{prediction:04d}.npz') as data:
                    assert data['env_ids'].tolist() == active
                    proposed = data['actions'].copy()
                admitted = {idx: proposed[row] for row, idx in enumerate(active)}
                for prefix_index in range(prefix_steps):
                    if not active or max(env.take_action_cnt) >= args.steps:
                        break
                    commands = [{key: value for arm, offset in (('left', 0), ('right', 7))
                        for key, value in ((f'{arm}_arm_joint_state', admitted[idx][prefix_index, offset:offset+6]),
                            (f'{arm}_ee_joint_state', admitted[idx][prefix_index, offset+6:offset+7]))}
                        for idx in active]
                    before = list(env.take_action_cnt)
                    step_start = time.perf_counter()
                    env.take_action_batch(commands, env_idx_list=active)
                    after = list(env.take_action_cnt)
                    assert all(after[i] == before[i] + (1 if i in active else 0) for i in range(args.num_envs))
                    post = env.get_obs_batch(env_idx_list=active, last_frame=True)
                    assert [int(row['env_idx']) for row in post] == active
                    post_states = []
                    for row in post:
                        idx = int(row['env_idx'])
                        state = np.concatenate([np.r_[row['state'][f'{arm}_arm_joint_state'],
                            row['state'][f'{arm}_ee_joint_state']] for arm in ('left', 'right')])
                        assert np.isfinite(state).all()
                        post_states.append(state)
                        journal.write(json.dumps({'env_idx': idx, 'step': after[idx],
                            'prediction': prediction, 'prefix_index': prefix_index,
                            'action': admitted[idx][prefix_index].tolist(), 'state': state.tolist(),
                            'ended': bool(env.end_flag[idx]), 'success': bool(env.end_flag[idx] and env.success[idx])}) + '\n')
                        if env.end_flag[idx]:
                            score = 1.0 if env.success[idx] else (float(env.reward_manager.get_score()[idx]) / 100
                                if hasattr(env, 'get_score') else 0.0)
                            terminal[idx] = {'step': after[idx], 'success': bool(env.success[idx]),
                                'native_score': score, 'unstable': idx in env.unstable_envs}
                    journal.flush()
                    np.savez_compressed(out / f'ack-{max(after):04d}.npz', env_ids=np.array(active),
                        states=np.stack(post_states))
                    active = [idx for idx in active if not env.end_flag[idx]]
                prediction += 1
                report.update(status='running', action_counts=list(env.take_action_cnt),
                    predictions=prediction, terminal=terminal, memory=memory(), wall_s=time.perf_counter() - start)
                write_json(out / 'report.json', report)
                print(json.dumps(report), flush=True)
        report.update(status='native_terminal_wave' if not active else 'bounded_wave_incomplete',
            active_envs=active, unstable_envs=list(env.unstable_envs))
    except BaseException as exc:
        report.update(status='error_stop_no_retry', error=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        write_json(out / 'report.json', report)
        (out / 'stop-worker').touch()
        if child is not None:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait(timeout=30)
        log.close()
        if env is not None:
            env.close()
        if app is not None:
            app.close()


if __name__ == '__main__':
    main()
