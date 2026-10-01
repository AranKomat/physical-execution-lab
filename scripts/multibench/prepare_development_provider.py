#!/usr/bin/env python3
"""Prepare fresh seeded runtime configurations; does not launch GPU work."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json,load_json,file_sha
from k1lab.multibench.manifest import seal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',choices=('g05-fla','intern'),required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();root=Path(__file__).resolve().parents[2];out=Path(a.output).resolve()
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    if a.variant=='g05-fla':
        cfg=load_json(root/'configs/local/g05-prepared/provider-unbound.json')
        cfg['identity']['preprocessing_id']='g05_qwen35_fm_bf16_fla051_clip_frequency30_native25_seed0'
        cfg['model_config']['hydra_overrides']=['model.model_weights_to_bf16=true',
                                               'model.model_arch.vlm.linear_attn_backend=fla']
    else:
        cfg=load_json(root/'configs/multibench/policies/internw0_delta.json')
        base=root/'external/XPolicyLab/policy/InternW0_delta'
        files={}
        for folder in ('config','checkpoints','assets'):
            for path in sorted((base/folder).rglob('*')):
                if path.is_file() and '.cache' not in path.parts:
                    files[str(path.relative_to(base))]=file_sha(path)
        if not files:raise FileNotFoundError('Intern artifacts absent')
        manifest=seal({'schema':'multibench.artifacts.v1','root':str(base),'files':files,
                       'scope':'Released config, checkpoint and local base assets; cache excluded'})
        atomic_json(out/'artifacts.json',manifest,exclusive=True)
        cfg['artifact_manifest']=str(out/'artifacts.json')
        cfg['xpolicylab_root']=str(root/'external/XPolicyLab')
        cfg['model_config'].update(checkpoint_path=str(base/'checkpoints/robodojo.pt'),seed=0)
        cfg['identity']['preprocessing_id']='xpl_wam_three_view_canvas_actual_ack_seed0'
    cfg['policy_rng_seed']=0
    atomic_json(out/'provider-unbound.json',cfg,exclusive=True)
    print(out/'provider-unbound.json',flush=True)


if __name__=='__main__':main()
