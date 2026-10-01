#!/usr/bin/env python3
"""Bind official XR1 artifacts and a fixed development roster; launch nothing."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.errors import ContractError
from k1lab.multibench.manifest import check, resolved_config, seal
from k1lab.util import atomic_json, file_sha, load_json

ROSTER = ('OpenDrawer', 'TurnOnElectricKettle', 'RinseSinkBasin',
          'StoreLeftoversInBowl', 'CategorizeCondiments', 'PanTransfer')


def development_roster(reference, categories):
    reference = check(reference)
    full = deepcopy(reference)
    for case in full['cases']:
        if case['task'] == 'CloseBlenderLid':
            case['partition'] = 'dev'
        case['category'] = categories[case['task']]
    full['development_exclusions'] = {
        'CloseBlenderLid': 'whole task quarantined after official bring-up used episode 0'}
    full = check(seal(full))
    selected = []
    for task in ROSTER:
        case = next(c for c in full['cases'] if c['task'] == task and c['trial'] == 0)
        if case['partition'] != 'dev':
            raise ContractError('fixed development task is not in the existing development split')
        selected.append(case)
    if sorted(c['category'] for c in selected) != sorted(
            ['atomic_seen', 'composite_seen', 'composite_unseen'] * 2):
        raise ContractError('development roster must have two tasks per official category')
    pilot = check(seal({**full, 'cases': selected,
        'reference_manifest_sha256': reference['sha256'],
        'full_manifest_sha256': full['sha256'],
        'note': 'Fixed development subset before harness results; source indices/seeds unchanged.'}))
    return full, pilot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint-dir', required=True)
    p.add_argument('--reference-manifest', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--policy-port', type=int, default=19611)
    a = p.parse_args()
    if not 1 <= a.policy_port <= 65535:
        raise ContractError('invalid policy port')
    root = Path(__file__).resolve().parents[2]
    checkpoint = Path(a.checkpoint_dir).resolve()
    files = {str(path.relative_to(checkpoint)): file_sha(path)
             for path in sorted(checkpoint.rglob('*'))
             if path.is_file() and '.cache' not in path.relative_to(checkpoint).parts}
    if not all(f'model-{i:05d}-of-00003.safetensors' in files for i in range(1, 4)):
        raise ContractError('official three-shard XR1 checkpoint required')
    from robocasa.utils.dataset_registry import TARGET_TASKS
    categories = {task: category for category in
                  ('atomic_seen', 'composite_seen', 'composite_unseen')
                  for task in TARGET_TASKS[category]}
    full, pilot = development_roster(load_json(a.reference_manifest), categories)
    out = Path(a.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out / 'artifacts.json', seal({'schema': 'multibench.artifacts.v1',
        'root': str(checkpoint), 'files': files,
        'scope': 'Released XR1 RoboCasa365 checkpoint, processor and custom code; cache excluded'}))
    atomic_json(out / 'full-manifest.json', full)
    atomic_json(out / 'development-manifest.json', pilot)
    for mode in ('motor_only', 'review_every_chunk', 'sparse'):
        cfg = load_json(root / f'configs/multibench/robocasa365_xiaomi_{mode}.json')
        cfg['environment'].update(xiaomi_root=str(root / 'external/Xiaomi-Robotics-1'),
                                  robocasa_root=str(root / 'external/RoboCasa'))
        cfg['policy'].update(checkpoint_path=str(checkpoint),
            artifact_manifest=str(out / 'artifacts.json'), port=a.policy_port,
            xiaomi_root=str(root / 'external/Xiaomi-Robotics-1'), server_rng_seed=7,
            checkpoint_hf_revision='3a6d0293bfa90759d34a7fc48c2c62413cd7bcf4')
        cfg['policy']['identity']['preprocessing_id'] += '_server_seed7'
        atomic_json(out / f'robocasa365_xiaomi_{mode}.json', resolved_config(cfg))
    print(out)


if __name__ == '__main__':
    main()
