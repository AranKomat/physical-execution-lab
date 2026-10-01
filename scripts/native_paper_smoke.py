#!/usr/bin/env python3
"""Native diagnostic: inspect first; optional bounded 1 cm motion; no slow model.

Creates a NEW simulator episode. It never attaches to an existing robot or held
remote episode. These are calibration diagnostics, not benchmark outcomes.
"""
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import read_json,atomic_json,plain
from prl.manifests import load_manifest
from prl.journal import Journal
from prl.dyna.protocol import PaperSettings
from prl.dyna.native import NativeBackend
from prl.dyna.engine import Engine,StopExecution
from prl.dyna.capabilities import Phase,GroundedCommand


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--case-index',type=int,default=0)
    p.add_argument('--output',required=True);p.add_argument('--allow-native',action='store_true')
    p.add_argument('--move-up-1cm',action='store_true');p.add_argument('--policy-probe',action='store_true')
    a=p.parse_args()
    if not a.allow_native:raise SystemExit('--allow-native is required')
    config=read_json(a.config);_,cases=load_manifest(a.manifest);case=cases[a.case_index]
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    s=PaperSettings(**{**config.get('settings',{}),'policy_enabled':a.policy_probe})
    b=None;j=Journal(out/'events.jsonl')
    try:
        b=NativeBackend(case,out,{**config,'allow_native':True},s)
        start=b.capture();atomic_json(out/'initial_scene.json',plain(start))
        atomic_json(out/'backend.json',b.metadata)
        if a.policy_probe:
            import numpy as np
            actions=b.policy_actions(start.task)
            if np.asarray(actions).shape!=(10,7):raise ValueError('policy chunk must be [10,7]')
            np.savez_compressed(out/'policy_probe_NOT_EXECUTED.npz',actions=actions)
        if a.move_up_1cm:
            e=Engine(b,None,j,s,'A2ctrl',30,out)
            target=list(start.eef_xyz);target[2]+=.01
            ph=Phase('diagnostic_1cm','move',20,tuple(target),start.eef_quat,-1)
            cmd=GroundedCommand('diagnostic',{},[ph],20,start.observation_id,{})
            try:e.phase(ph,cmd)
            except StopExecution as ex:j.append('diagnostic_stop',{'reason':str(ex)})
            atomic_json(out/'motion_receipt.json',{'requested_target':target,'actual_eef':b.scene().eef_xyz,
                'actions':e.steps,'watchdog_callbacks':e.safety_checks,'not_benchmark_result':True})
        atomic_json(out/'geometry_warnings.json',b.geometry_warnings)
    finally:
        if b:b.close()
        j.close()
if __name__=='__main__':main()
