#!/usr/bin/env python3
"""Prepare a fresh, hash-bound G05 inference bundle without loading a GPU model."""
import argparse
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, load_json
from k1lab.multibench.manifest import artifacts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir', required=True)
    p.add_argument('--processor', required=True)
    p.add_argument('--bundle', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--xpolicylab', required=True)
    args = p.parse_args()
    source, processor, bundle, out, xpl = (Path(x).resolve() for x in
        (args.run_dir, args.processor, args.bundle, args.output, args.xpolicylab))
    if bundle.exists() or out.exists():
        raise FileExistsError('bundle and configuration output must be fresh')
    import yaml
    source_config = source / '.hydra/config.yaml'
    cfg = yaml.safe_load(source_config.read_text())
    if cfg['model']['model_arch']['_target_'] != 'g05.models.g05.g05_policy_qwen35.G05PolicyQwen35':
        raise ValueError('this preparation is for the released Qwen3.5 RoboDojo FM checkpoint')
    if not (processor / 'tokenizer.json').is_file():
        raise FileNotFoundError('processor must include tokenizer.json')
    bundle.mkdir(parents=True)
    (bundle / '.hydra').mkdir()
    (bundle / 'checkpoints').mkdir()
    shutil.copy2(source_config, bundle / '.hydra/published_config.yaml')
    shutil.copy2(source / 'checkpoints/inference.pt', bundle / 'checkpoints/inference.pt')
    shutil.copy2(source / 'action_tokenizer.pt', bundle / 'action_tokenizer.pt')
    shutil.copy2(source / 'dataset_stats.json', bundle / 'dataset_stats.json')
    shutil.copytree(processor, bundle / 'hf_processor')
    # Resolve deployment-only paths, leaving the processor and model conventions intact.
    cfg['model']['model_arch']['hf_processor_path'] = str(bundle / 'hf_processor')
    cfg['model']['processor']['tokenizer_params']['pretrained_model_name_or_path'] = str(bundle / 'hf_processor')
    for dataset in cfg['data']['embodiment_datasets'].values():
        for group in dataset.get('dataset_groups', []):
            group['dataset_dirs'] = []  # Training data is not consumed during inference.
    (bundle / '.hydra/config.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    out.mkdir(parents=True)
    manifest_path = out / 'artifacts.json'
    atomic_json(manifest_path, artifacts(bundle), exclusive=True)
    root = Path(__file__).resolve().parents[2]
    provider = load_json(root / 'configs/multibench/policies/g05.json')
    provider['artifact_manifest'] = str(manifest_path)
    provider['xpolicylab_root'] = str(xpl)
    provider['gripper_clip'] = True
    provider['identity']['prediction_horizon'] = 32
    provider['identity']['preprocessing_id'] = 'g05_qwen35_fm_bf16_torch_clip_frequency30_native25'
    provider['model_config'].update({
        'g05_root': str(xpl / 'policy/G05/G05'),
        'ckpt_path': str(bundle / 'checkpoints/inference.pt'),
        'inference_batch_size': 1,
        'hydra_overrides': ['model.model_weights_to_bf16=true',
                           'model.model_arch.vlm.linear_attn_backend=torch'],
    })
    atomic_json(out / 'provider-unbound.json', provider, exclusive=True)
    atomic_json(out / 'preparation.json', {
        'source_run_dir': str(source), 'source_processor': str(processor),
        'bundle': str(bundle), 'model_weights': 'unchanged inference-export tensors',
        'config_changes': ['absolute HF processor paths', 'empty unused training dataset dirs'],
        'runtime_variant': 'BF16, documented torch linear attention, explicit gripper clipping',
        'qualification': 'not yet native-qualified',
    }, exclusive=True)
    print(out / 'provider-unbound.json', flush=True)


if __name__ == '__main__':
    main()
