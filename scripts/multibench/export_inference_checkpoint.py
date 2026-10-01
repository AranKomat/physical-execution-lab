#!/usr/bin/env python3
"""Repack a trusted training checkpoint without optimizer tensors; no weight edits.

The G05 source loader maps the entire checkpoint to CUDA. Removing training-only
state avoids allocating optimizer memory during inference. The original remains
untouched, and source/output hashes and tensor dtypes are recorded separately.
"""
import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, file_sha


def inference_payload(checkpoint):
    state = checkpoint['model_state_dict']
    if not isinstance(state, dict) or not state:
        raise ValueError('nonempty model_state_dict required')
    payload = {'model_state_dict': state}
    for key in ('step', 'epoch', 'batch_idx', 'action_batch_idx'):
        value = checkpoint.get(key)
        if value is None or type(value) in (int, float, str, bool):
            payload[key] = value
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--receipt', required=True)
    args = parser.parse_args()
    source, output, receipt = map(Path, (args.source, args.output, args.receipt))
    if output.exists() or receipt.exists() or source.resolve() == output.resolve():
        raise FileExistsError('output/receipt must be fresh; source is never overwritten')
    import torch
    # Only use this on an explicitly trusted publisher checkpoint.
    checkpoint = torch.load(source, map_location='cpu', mmap=True, weights_only=False)
    payload = inference_payload(checkpoint)
    state = payload['model_state_dict']
    if not all(isinstance(value, torch.Tensor) for value in state.values()):
        raise ValueError('model state must contain tensors only')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        torch.save(payload, stream)
    atomic_json(receipt, {
        'schema': 'multibench.inference_export.v1',
        'source': str(source.resolve()), 'source_sha256': file_sha(source),
        'output': str(output.resolve()), 'output_sha256': file_sha(output),
        'dropped_keys': sorted(set(checkpoint) - set(payload)),
        'tensor_count': len(state),
        'tensor_bytes': sum(v.numel() * v.element_size() for v in state.values()),
        'dtypes': dict(Counter(str(v.dtype) for v in state.values())),
        'weight_transformation': 'none; model_state_dict tensors saved unchanged',
        'purpose': 'inference container only; not a new trained policy',
    }, exclusive=True)


if __name__ == '__main__':
    main()
