#!/usr/bin/env python3
"""Bind existing G05 artifacts and freeze two ten-task conditions before execution."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.util import atomic_json, digest, load_json
from k1lab.multibench.manifest import resolved_config, seal
from k1lab.multibench.types import PolicyIdentity
from semantic_lab.motor_contract import motor_contract, validate_identity
from semantic_lab.protocol import freeze, verify_binding


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-preparation', type=Path, required=True)
    p.add_argument('--source-freeze', type=Path, required=True)
    p.add_argument('--source-provider', type=Path, required=True)
    p.add_argument('--artifacts', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    contract = motor_contract('g05')
    destination = ROOT / contract['provider']
    provider = load_json(args.source_provider)
    provider['artifact_manifest'] = str(args.artifacts.resolve())
    provider['model_config']['inference_batch_size'] = 10
    provider['identity']['adapter_config_sha256'] = None
    provider = resolved_config({'policy': provider})['policy']
    validate_identity(PolicyIdentity(**provider['identity']), 'g05')
    if destination.exists():
        if load_json(destination) != provider:
            raise ValueError('existing G05 provider differs; preserve it and use a fresh binding')
    else:
        destination.parent.mkdir(exist_ok=False)
        atomic_json(destination, provider, exclusive=True)
    panel = load_json(args.source_preparation / 'cases.json')
    original = deepcopy(load_json(args.source_preparation / 'original_only.json'))
    original['name'] = 'g05_full_ten_original_only001'
    semantic = deepcopy(load_json(args.source_preparation / 'semantic.json'))
    semantic.update(name='g05_full_ten_subtask_only_recovery001', prompt_mode='subtask_only')
    semantic['semantic_schedule']['allow_semantic_recovery'] = True
    configs = dict(original_only=original, semantic=semantic)
    plan = seal(dict(schema='semantic.g05_screen.v1', manifest_sha256=panel['sha256'],
        motor_identity=provider['identity'], provider_sha256=digest(provider),
        configs={label: digest(config) for label, config in configs.items()},
        slots=[dict(approach=label, condition=config['name'], case_id=case['case_id'], status='missing')
               for label, config in configs.items() for case in panel['cases']],
        scope='opened ten-task screen; not untouched-task generalization or official SR',
        tier_policy='flex_preferred_same_model_standard_capacity_fallback',
        cadence='source H32 underlying, returned/executed16; review target100 at next H16 boundary',
        native_reasoning=False, no_added_bbox_or_target_crop=True,
        independent_per_env_rng=False, singleton_numerical_parity=False,
        rng='source seed0 fixed B10 fused stream; inference-only padding as episodes leave'))
    selectors = [selector for selector in load_json(args.source_freeze)['execution_sources']['selectors']
                 if not selector.startswith('configs/local/pi05')
                 and not selector.startswith('external/GPT-as-Policy/hybrid_rollout/robodojo/pi05_server')]
    selectors += ['semantic_lab/g05_batch.py', 'semantic_lab/motor_contract.py',
        str(destination.relative_to(ROOT)), 'external/XPolicyLab/policy/G05/model.py',
        'external/XPolicyLab/policy/G05/__init__.py',
        'external/XPolicyLab/policy/G05/G05/src',
        'external/XPolicyLab/policy/G05/G05/scripts',
        'external/XPolicyLab/policy/G05/G05/configs',
        'external/XPolicyLab/model_template.py', 'external/XPolicyLab/utils',
        'model-artifacts/g05-bf16-torch-clip/.hydra',
        'model-artifacts/g05-bf16-torch-clip/hf_processor',
        'model-artifacts/g05-bf16-torch-clip/dataset_stats.json']
    selectors = sorted(set(selectors))
    frozen = freeze(ROOT, panel, list(configs.values()), execution_sources=selectors)
    for config in configs.values():
        verify_binding(ROOT, frozen, panel, config, require_execution_sources=True)
    args.output.mkdir(exist_ok=False)
    for name, document in dict(cases=panel, plan=plan, freeze=frozen, **configs).items():
        atomic_json(args.output / (name + '.json'), document, exclusive=True)
    print(dict(preparation=str(args.output), freeze_sha256=frozen['sha256'],
               robot_actions=0, paid_calls=0, native_admission_pending=True))


if __name__ == '__main__':
    main()
