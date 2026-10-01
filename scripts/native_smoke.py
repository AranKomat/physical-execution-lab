#!/usr/bin/env python3
"""Snapshot + optional ONE zero-displacement native tick; no model call."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from k1lab.util import load_json,atomic_json
from k1lab.native import make_adapter
from k1lab.journal import Journal
from k1lab.manifests import validate

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--case',required=True);p.add_argument('--output',required=True);p.add_argument('--move-one-step',action='store_true')
    a=p.parse_args();cfg=load_json(a.config);m=validate(load_json(a.manifest));case=next(c for c in m['cases'] if c['id']==a.case)
    root=Path(a.output);root.mkdir(parents=True,exist_ok=False)
    with Journal(root/'events.jsonl') as j:
        adapter=make_adapter(cfg['native']|{'resolution':cfg.get('resolution',384)},case,j)
        try:
            obs=adapter.observe()
            import numpy as np
            from PIL import Image
            for name,camera in obs['vision'].items():
                Image.fromarray(camera['color']).save(root/(name+'.png'))
                np.savez(root/(name+'.npz'),**{k:v for k,v in camera.items() if not k.startswith('_')})
            atomic_json(root/'proprioception.json',{k:v for k,v in obs.items() if k!='vision'})
            if a.move_one_step:
                arm=obs['arms']['arm'];adapter.move_to_position('arm',arm['xyz_world_m'],arm['quaternion_xyzw'],None,1)
                assert adapter.frame==1
            atomic_json(root/'smoke_result.json',{'reset_render':True,'one_native_tick':a.move_one_step,
                 'frame':adapter.frame,'native_success':adapter.success(),
                 'qualification':'smoke only, not calibration/grasp/policy qualification'})
        finally:adapter.close()
if __name__=='__main__':main()
