#!/usr/bin/env python3
"""Validate a real DROID observation, then invoke FLUX's documented offline CLI.

Does NOT turn FLUX into a LIBERO policy. No fabricated third camera or joint map.
"""
import argparse
import subprocess
from pathlib import Path
import numpy as np


def validate(path):
    with np.load(path,allow_pickle=False) as obs:
        for name in ('images.wrist','images.left','images.right'):
            if name not in obs or obs[name].shape!=(360,640,3) or obs[name].dtype!=np.uint8:
                raise ValueError('DROID requires three synchronized uint8 360x640 views: '+name)
        if 'state' not in obs or obs['state'].shape!=(8,) or not np.isfinite(obs['state']).all():
            raise ValueError('DROID needs seven measured joints (rad) + gripper closed fraction')

def main():
    p=argparse.ArgumentParser();p.add_argument('--observation',required=True);p.add_argument('--checkpoint',required=True)
    p.add_argument('--task',required=True);p.add_argument('--output',required=True);p.add_argument('--flux-executable',default='flux-action')
    p.add_argument('--execute',action='store_true');a=p.parse_args();validate(a.observation)
    command=[a.flux_executable,'infer','--checkpoint',a.checkpoint,'--observation',a.observation,'--task',a.task,'--output',a.output]
    if not a.execute:print('Observation valid. No GPU command run.\n',command);return
    if Path(a.output).exists():raise SystemExit('fresh output required')
    subprocess.run(command,check=True)
    actions=np.load(Path(a.output)/'actions.npy',allow_pickle=False)
    if actions.shape!=(1,32,8):raise SystemExit('unexpected action shape; inspect checkpoint convention')
    print('Saved joint8 predictions ONLY. No simulator or robot execution was performed.')
if __name__=='__main__':main()
