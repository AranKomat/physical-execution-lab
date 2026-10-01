#!/usr/bin/env python3
"""Bounded G05 inference on a retained legal observation; no simulator or API.

This is bring-up evidence, not bound policy qualification or task success.
"""
import argparse
import importlib
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, load_json
from k1lab.errors import ContractError
from k1lab.multibench.adapters.robodojo import check_checkout
from k1lab.multibench.adapters.xpolicylab import REV, decode_xpl, to_xpl
from k1lab.multibench.transport import decode_obs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', required=True)
    p.add_argument('--processor', required=True)
    p.add_argument('--observation', required=True)
    p.add_argument('--xpolicylab', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--cuda-device', default='1')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--linear-attention-backend', choices=('fla', 'torch'), default='fla')
    args = p.parse_args()
    if not 1 <= args.repeats <= 10:
        p.error('repeats must be between 1 and 10')
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(output)
    checkpoint = str(Path(args.checkpoint).resolve())
    processor = str(Path(args.processor).resolve())
    root = check_checkout(args.xpolicylab, REV)
    observation = decode_obs(load_json(args.observation))
    os.environ['CUDA_VISIBLE_DEVICES'] = args.cuda_device
    os.environ['G05_HF_PROCESSOR_PATH'] = processor
    # The full training config resolves this variable before filtering datasets.
    # Inference does not load a dataset; this path is intentionally nonexistent.
    os.environ['ROBODOJO_LEROBOT_V30_ROOT'] = '/nonexistent/inference-does-not-load-datasets'
    sys.path.insert(0, str(root.parent))
    import torch
    cfg = {'action_type': 'joint', 'env_cfg_type': 'arx_x5', 'eval_embodiment': 'robodojo',
           'action_steps': 16, 'frequency': 30, 'inference_batch_size': 1,
           'ckpt_path': checkpoint, 'action_source': 'fm',
           'hydra_overrides': ['model.model_weights_to_bf16=true',
                              'model.model_arch.vlm.linear_attn_backend=' + args.linear_attention_backend]}
    start = time.perf_counter()
    model = importlib.import_module('XPolicyLab.policy.G05.model').Model(cfg)
    torch.cuda.synchronize()
    load_seconds = time.perf_counter() - start
    timings, lengths, validation_errors, raw_chunks = [], [], [], []
    for _ in range(1 + args.repeats):
        model.reset()
        torch.cuda.synchronize()
        start = time.perf_counter()
        model.update_obs(to_xpl(observation))
        rows = model.get_action()
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        raw_chunks.append([{key: value.tolist() for key, value in row.items()} for row in rows])
        try:
            actions, clipped = decode_xpl(rows, 'x5_joint14', gripper_clip=False)
            validation_errors.append(None)
        except ContractError as exc:
            actions, clipped = [], 0
            validation_errors.append(str(exc))
        timings.append(elapsed)
        lengths.append(len(rows))
    atomic_json(output, {
        'schema': 'multibench.g05_bringup.v1', 'model_config': cfg,
        'processor': processor, 'source_revision': REV,
        'observation_stamp': observation.stamp,
        'load_seconds': load_seconds, 'cold_inference_seconds': timings[0],
        'warm_inference_seconds': timings[1:], 'returned_action_lengths': lengths,
        'gripper_clips': clipped,
        'last_action_chunk': [action.json() for action in actions],
        'raw_action_chunks': raw_chunks, 'validation_errors': validation_errors,
        'action_contract_passed': not any(validation_errors),
        'peak_allocated_bytes': torch.cuda.max_memory_allocated(),
        'peak_reserved_bytes': torch.cuda.max_memory_reserved(),
        'native_actions_executed': 0, 'paid_calls': 0,
        'temporal_mode': 'reset per independent saved observation',
        'qualification': 'bring-up only; artifact binding/native timing remain required',
    }, exclusive=True)
    if any(validation_errors):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
