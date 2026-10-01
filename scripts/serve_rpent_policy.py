#!/usr/bin/env python3
"""Launch only after preparing the pinned RPent/RLinf/openpi GPU environment."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from k1lab.sources import checked_checkout,RPENT_REV
from k1lab.util import file_sha,digest,atomic_json
from k1lab.policy import PolicySpec
from k1lab.native import POLICY_CONTRACT


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rpent',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--model-id',required=True)
    p.add_argument('--spec-output',required=True);p.add_argument('--port',type=int,default=8811)
    p.add_argument('--cuda-device',default='0');p.add_argument('--allow-gpu',action='store_true')
    a=p.parse_args()
    if not a.allow_gpu:raise SystemExit('--allow-gpu required; this loads real weights')
    root=checked_checkout(a.rpent,RPENT_REV,'rpent/robots/components/pi05_vla_server.py')
    sys.path.insert(0,str(root));os.environ['CUDA_VISIBLE_DEVICES']=a.cuda_device
    checkpoint=Path(a.checkpoint).resolve()
    files={str(p.relative_to(checkpoint)):file_sha(p) for p in sorted(checkpoint.rglob('*')) if p.is_file()}
    if not files:raise SystemExit('empty checkpoint directory')
    atomic_json(str(a.spec_output)+'.weights.json',{'files':files,'sha256':digest(files)},exclusive=True)
    from rpent.robots.components.pi05_vla_server import Pi05VLAFacade
    # No environment import. Embodiment "libero" config selects upstream 5-action chunks.
    facade=Pi05VLAFacade(model_path=str(checkpoint),embodiment='libero')
    spec=PolicySpec(model_id=a.model_id,checkpoint_sha256=digest(files),action_space='libero_normalized_osc7',
            control_hz=20,cameras=POLICY_CONTRACT['cameras'],state_dim=8,
            observation_convention=POLICY_CONTRACT['observation_convention'],adapter_revision=RPENT_REV)
    atomic_json(a.spec_output,spec.json(),exclusive=True)
    from k1lab.policy_bridge import serve
    print('Loaded frozen policy; loopback /health and /predict; spec:',spec.identity,flush=True)
    serve(facade,spec,a.port)

if __name__=='__main__':main()
