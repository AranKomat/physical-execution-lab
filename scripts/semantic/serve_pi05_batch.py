#!/usr/bin/env python3
"""One fused pi0.5 service for a fixed cohort of concurrent simulator groups."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'external/GPT-as-Policy')]


def write_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cohort', type=Path, required=True,
                   help='JSON list of absolute simulator output directories')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--capacity', type=int, default=10)
    p.add_argument('--wait-seconds', type=float, default=900)
    args = p.parse_args()
    import jax
    import numpy as np
    from openpi.models.model import Observation
    from openpi.models.tokenizer import PaligemmaTokenizer
    from openpi.policies.policy_config import create_trained_policy
    from hybrid_rollout.robodojo.pi05_server.checkpoint import data_contract, checkpoint_identity
    from semantic_lab.pi05_batch import Pi05Batch
    from semantic_lab.token_retention import PromptRetentionGuard
    from k1lab.errors import ContractError

    waves = [Path(path).resolve() for path in json.loads(args.cohort.read_text())]
    if (not waves or len(set(waves)) != len(waves) or args.capacity < 1
            or any(not path.is_relative_to(ROOT / 'runs') or not path.is_dir() for path in waves)):
        raise ContractError('batch cohort must bind unique existing run directories')
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'runs'):
        raise ContractError('worker output must be inside runs')
    out.mkdir(exist_ok=False)
    provider = json.loads((ROOT / 'configs/local/pi05-exact-bound-001/provider.json').read_text())
    checkpoint = Path(provider['checkpoint_path'])
    cfg, _ = data_contract(checkpoint)
    policy = create_trained_policy(cfg, checkpoint)
    prompt_records = []
    decoder = PaligemmaTokenizer(cfg.model.max_token_len)._tokenizer.decode
    policy._input_transform = PromptRetentionGuard(policy._input_transform, decoder, prompt_records.append)
    executor = Pi05Batch(policy, Observation)
    ready = dict(identity=checkpoint_identity(checkpoint), inference_mode='vmap_source_singleton_sampling',
                 capacity=args.capacity, cohort=[str(path) for path in waves],
                 rng='independent source seed0 streams per wave/environment',
                 numerical_singleton_parity=False, padding='inference-only; no simulator actions')
    for wave in waves:
        if (wave / 'worker-ready.json').exists():
            raise ContractError('cohort already has worker output; no automatic restart')
        write_json(wave / 'worker-ready.json', ready)
    write_json(out / 'ready.json', ready)
    indices = {wave: 0 for wave in waves}
    pending_since = None
    batch = 0
    try:
        while not (out / 'stop-service').exists():
            for wave in waves:
                report = wave / 'report.json'
                if report.exists() and json.loads(report.read_text())['status'] == 'error_stop_no_retry':
                    raise ContractError('failed simulator group invalidates the full cohort')
            active = [wave for wave in waves if not (wave / 'stop-worker').exists()]
            if not active:
                break
            paths = {wave: wave / f'request-{indices[wave]:04d}.npz' for wave in active}
            if not all(path.exists() for path in paths.values()):
                if any(path.exists() for path in paths.values()):
                    pending_since = pending_since or time.monotonic()
                    if time.monotonic() - pending_since > args.wait_seconds:
                        raise TimeoutError('cohort inference barrier timed out; no retry')
                time.sleep(.05)
                continue
            pending_since = None
            started = time.perf_counter()
            raws, episode_ids, slices = [], [], {}
            for wave, path in paths.items():
                start = len(raws)
                with np.load(path, allow_pickle=False) as data:
                    ids = data['env_ids'].tolist()
                    if not ids or len(ids) != len(set(ids)):
                        raise ContractError('request requires unique environment IDs')
                    for row, idx in enumerate(ids):
                        if type(idx) is not int or idx < 0:
                            raise ContractError('invalid environment index')
                        episode_ids.append(f'{wave.name}/{idx}')
                        raws.append(dict(state=data['states'][row].copy(), prompt=str(data['prompts'][row]),
                            images={name: np.transpose(data[name][row], (2, 0, 1)).copy()
                                    for name in ('cam_high', 'cam_left_wrist', 'cam_right_wrist')}))
                slices[wave] = (slice(start, len(raws)), ids)
            count = len(raws)
            if count > args.capacity:
                raise ContractError('cohort exceeded its fixed inference capacity')
            # Keep one compiled shape as completed environments leave the cohort.
            # Padding rows never become simulator commands or task results.
            for idx in range(args.capacity - count):
                episode_ids.append(f'__padding__/{idx}')
                raws.append(raws[0])
            prompt_records.clear()
            result = executor.infer(episode_ids, raws)
            elapsed = time.perf_counter() - started
            for wave, (selection, ids) in slices.items():
                index = indices[wave]
                prediction = wave / f'prediction-{index:04d}.npz'
                with prediction.with_suffix('.tmp').open('xb') as stream:
                    np.savez_compressed(stream, actions=result['actions'][selection],
                        raw_actions=result['raw_actions'][selection], env_ids=np.array(ids))
                prediction.with_suffix('.tmp').replace(prediction)
                write_json(wave / f'prediction-{index:04d}.json', dict(
                    inference_s=elapsed, cohort_batch_index=batch, cohort_active_rows=count,
                    padded_rows=args.capacity-count, env_ids=ids,
                    request_sha256=hashlib.sha256(paths[wave].read_bytes()).hexdigest(),
                    inference_mode=ready['inference_mode'],
                    native_calls_per_env={str(idx): executor.calls[f'{wave.name}/{idx}'] for idx in ids},
                    rng_keys_after={str(idx): jax.random.key_data(executor.keys[f'{wave.name}/{idx}']).tolist()
                                    for idx in ids}, live_prompt_retention=prompt_records[selection]))
                indices[wave] += 1
            with (out / 'batches.jsonl').open('a') as stream:
                stream.write(json.dumps(dict(batch=batch, active_rows=count, padded_rows=args.capacity-count,
                                             inference_s=elapsed)) + '\n')
            batch += 1
    except BaseException as exc:
        error = dict(error=f'{type(exc).__name__}: {exc}', automatic_retry=False)
        write_json(out / 'error.json', error)
        for wave in waves:
            write_json(wave / 'worker-error.json', error)
        raise
    finally:
        write_json(out / 'result.json', dict(batches=batch, requests={wave.name: idx for wave, idx in indices.items()},
            status='error_stop_no_retry' if (out / 'error.json').exists() else 'stopped'))


if __name__ == '__main__':
    main()
