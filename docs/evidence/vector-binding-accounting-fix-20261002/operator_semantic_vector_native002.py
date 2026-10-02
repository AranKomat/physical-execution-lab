"""Native callbacks for the experimental coordinator; evaluator stays outside prompts."""
import hashlib
import json
from pathlib import Path
import time
import uuid
import fcntl
import numpy as np

from k1lab.multibench.types import Action, Observation, PolicyIdentity, Proposal, StepResult
from k1lab.util import digest
from semantic_lab.planner import SemanticPlanner
from semantic_lab.report import summarize_wave_results
from operator_semantic_vector_coordinator001 import Coordinator
from operator_vector_pi05_rollout001 import wait_file, write_json, memory


class SerializedPlanner:
    def __init__(self, planner, lock_path):
        self.planner = planner
        self.lock_path = lock_path
        self.client = planner.client

    def reset(self):
        self.planner.reset()

    def close(self):
        self.planner.close()

    def decide(self, *args):
        # Separate descriptors make this lock shared across threads and families.
        with self.lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                return self.planner.decide(*args)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


def run_wave(env, out, args, report, child):
    root = Path('/root/physical-execution-lab')
    config = json.loads(args.semantic_config.read_text())
    assert config['mode'] in ('motor_only', 'semantic_shadow', 'semantic_subtask_hierarchy')
    assert args.policy == 'pi05' and args.inference_mode == 'native_singleton'
    assert config['mode'] == 'motor_only' or args.allow_api
    provider = json.loads((root / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
    identity = PolicyIdentity(**provider['identity'])
    assert identity.execute_steps == 15 and identity.prediction_horizon == 50 and not identity.stateful
    ready = json.loads((out / 'worker-ready.json').read_text())
    assert ready['identity']['checkpoint_sha256'] == provider['native_checkpoint_sha256']
    episodes = {idx: uuid.uuid4().hex for idx in range(args.num_envs)}
    call_counts = {idx: 0 for idx in episodes}
    prediction = 0

    def observe(raw):
        idx = int(raw['env_idx'])
        native = raw['state']
        state = np.concatenate([np.r_[native[f'{arm}_arm_joint_state'], native[f'{arm}_ee_joint_state']]
            for arm in ('left', 'right')]).astype(np.float32)
        eef = {}
        for arm, offset in (('left', 0), ('right', 7)):
            pose = np.asarray(native[f'{arm}_ee_pose'], np.float32)
            eef[arm] = {'xyz': pose[:3].tolist(), 'quaternion_xyzw': pose[[4, 5, 6, 3]].tolist(),
                'gripper_opening_command': float(state[offset+6]), 'gripper_is_measurement': False}
        rgb = {key: np.asarray(raw['vision'][native_name]['color'], np.uint8)[..., :3].copy()
            for key, native_name in (('cam_high', 'cam_head'), ('cam_left_wrist', 'cam_left_wrist'),
                ('cam_right_wrist', 'cam_right_wrist'))}
        return Observation(episodes[idx], int(env.take_action_cnt[idx]), raw['instruction'],
            rgb, state, eef, float(env.obs_manager.collect_freq))

    initial = {int(row['env_idx']): observe(row) for row in env.get_obs_batch(env_idx_list=list(episodes))}
    raw_proposals = out / 'source-policy-proposals'
    raw_proposals.mkdir(exist_ok=False)
    journal = (out / 'actions.jsonl').open('x')

    def infer(values):
        nonlocal prediction
        ids = sorted(values)
        request = out / f'request-{prediction:04d}.npz'
        with request.with_suffix('.tmp').open('xb') as stream:
            np.savez_compressed(stream, states=np.stack([values[idx].state for idx in ids]),
                prompts=np.array([values[idx].instruction for idx in ids]), env_ids=np.array(ids),
                steps=np.array([values[idx].step for idx in ids]),
                **{key: np.stack([values[idx].rgb[key] for idx in ids])
                    for key in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')})
        request.with_suffix('.tmp').replace(request)
        wait_file(out / f'prediction-{prediction:04d}.json', child)
        with np.load(out / f'prediction-{prediction:04d}.npz', allow_pickle=False) as source:
            assert source['env_ids'].tolist() == ids
            proposals = source['actions'].copy()
        result = {}
        for row, idx in enumerate(ids):
            directory = raw_proposals / str(idx)
            directory.mkdir(exist_ok=True)
            np.savez_compressed(directory / f'proposal_{call_counts[idx]:06d}.npz', actions=proposals[row])
            result[idx] = Proposal(values[idx].stamp, values[idx].step, identity.identity,
                [Action('x5_joint14', vector) for vector in proposals[row]],
                {'inference_index': call_counts[idx], 'vector_prediction_index': prediction,
                    'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest()})
            call_counts[idx] += 1
        prediction += 1
        return result

    def step(values):
        ids = sorted(values)
        commands = [{key: value for arm, offset in (('left', 0), ('right', 7))
            for key, value in ((f'{arm}_arm_joint_state', values[idx].values[offset:offset+6]),
                (f'{arm}_ee_joint_state', values[idx].values[offset+6:offset+7]))} for idx in ids]
        before = list(env.take_action_cnt)
        env.take_action_batch(commands, env_idx_list=ids)
        after = list(env.take_action_cnt)
        assert all(after[idx] == before[idx] + int(idx in ids) for idx in episodes)
        rows = env.get_obs_batch(env_idx_list=ids, last_frame=True)
        assert [int(row['env_idx']) for row in rows] == ids
        result = {}
        for row in rows:
            idx = int(row['env_idx'])
            obs = observe(row)
            ended = bool(env.end_flag[idx])
            success = bool(ended and env.success[idx])
            truncated = bool(ended and not success and after[idx] >= env.step_lim)
            score = (1. if success else float(env.reward_manager.get_score()[idx]) / 100
                if hasattr(env, 'get_score') else 0.) if ended else None
            result[idx] = StepResult(obs, ended and not truncated, success, truncated, score)
            journal.write(json.dumps({'env_idx': idx, 'step': after[idx],
                'action': values[idx].values.tolist(), 'observation_sha256': obs.stamp,
                'ended': ended, 'success': success}) + '\n')
        journal.flush()
        return result

    cases = {idx: {'case_id': f'{args.task}__layout{report["reset_seeds"][idx]}__vectorrow{idx}',
        'task': args.task, 'benchmark': 'robodojo', 'partition': 'dev', 'task_group': args.task,
        'layout_id': report['reset_seeds'][idx], 'capacity_repeat_not_independent_case': True}
        for idx in episodes}
    outputs = {idx: out / 'episodes' / str(idx) / 'controller' for idx in episodes}
    planners = {idx: None if config['mode'] == 'motor_only' else SerializedPlanner(
        SemanticPlanner(config['model'], out / 'episodes' / str(idx) / 'planner', allow_api=args.allow_api),
        root / 'runs/semantic-vector-planner.lock') for idx in episodes}
    coordinator = Coordinator(initial, identity,
        {idx: min(args.steps, env.step_lim) for idx in episodes},
        lambda idx: {'simulator': 'RoboDojo', 'robot': 'dual_arx_x5', 'env_idx': idx,
            'shared_physics': True, 'retired_env_physics': 'continues globally; terminal score frozen',
            'cameras': list(initial[idx].rgb)}, infer, step, timeout_s=config.get('wall_limit_s', 3600))
    start = time.perf_counter()
    try:
        results = coordinator.run(cases, config, outputs, planners)
    finally:
        journal.close()
    report.update(summarize_wave_results(results))
    report.update(
        action_counts=list(env.take_action_cnt), predictions=prediction, semantic_config_sha256=digest(config),
        controller_results=results, dispatches=coordinator.dispatches, native_calls_per_env=call_counts,
        wall_s=time.perf_counter()-start, memory=memory(), unstable_envs=list(env.unstable_envs),
        paid_calls=sum(r['metrics']['semantic_calls'] for r in results.values()))
    write_json(out / 'report.json', report)
    return report
