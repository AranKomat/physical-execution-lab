#!/usr/bin/env python3
"""Export a decision-boundary, lossless sensor capture for policy-only timing.

Do not reconstruct policy inputs from JPEG previews. Both files must come from
one runner observation directory; no scene/object state is loaded.
"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from k1lab.util import load_json,atomic_json
from k1lab.errors import ContractError
from k1lab.multibench.types import Observation
from k1lab.multibench.transport import encode_obs


def export(directory,output):
    d=Path(directory);s=load_json(d/'state.json')
    with np.load(d/'sensors.npz',allow_pickle=False) as data:
        o=Observation(s['episode'],s['step'],s['instruction'],{k:data[k].copy() for k in data.files if k!='state'},
            data['state'].copy(),s['eef'],s['control_hz'],s.get('sensor_signals',{}))
    if o.stamp!=s['observation_sha256']:raise ContractError('capture identity mismatch')
    atomic_json(output,encode_obs(o),exclusive=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');p.add_argument('--output',required=True)
    a=p.parse_args();export(a.directory,a.output)
