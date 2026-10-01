#!/usr/bin/env python3
"""Create a one-case, no-model native smoke profile from an installed state catalog."""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import read_json,atomic_json
from prl.manifests import build_native_manifest,write_manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--catalog',required=True)
    p.add_argument('--output-dir',default='local');p.add_argument('--suite',default='libero_goal_task')
    p.add_argument('--task',type=int,default=0);p.add_argument('--state',type=int,default=0)
    p.add_argument('--cuda-device',type=int,default=0);a=p.parse_args()
    cat=read_json(a.catalog)
    cases=build_native_manifest(cat,'smoke',[a.state],[a.task]);cases=[c for c in cases if c['suite']==a.suite]
    if len(cases)!=1:raise SystemExit('Expected exactly one cataloged case')
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    for name in ('smoke.json','native-smoke.json'):
        if (out/name).exists():raise SystemExit(f'Refusing to overwrite {out/name}')
    write_manifest(out/'smoke.json','native','smoke',cases,'No-model native reset/render/one-action smoke.',cat['sha256'])
    config=read_json(ROOT/'configs/e2_dynamic.template.json')
    config.update(enable_policy=False,max_steps=10,max_decisions=2,max_wall_s=300,
                  cuda_device=a.cuda_device,rpent_root=str(ROOT/'external/RPent'))
    config['planner']={'kind':'command','command':[sys.executable,str(ROOT/'examples/hold_planner.py')],'timeout_s':30}
    atomic_json(out/'native-smoke.json',config)
    print(f'python run.py run --config {out}/native-smoke.json --manifest {out}/smoke.json --output runs/native-smoke --allow-native')
if __name__=='__main__':main()
