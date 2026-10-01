#!/usr/bin/env python3
"""Create an UNAPPROVED qualification record. It cannot authorize a scored run."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json,load_json,digest
from k1lab.multibench.manifest import resolved_config

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    cfg=resolved_config(load_json(a.config))
    atomic_json(a.output,{'schema':'multibench.qualification.v1','config_sha256':digest(cfg),
        'checks':{k:False for k in ('native_reset_render','action_space_verified','native_completion_not_vacuous',
          'current_sensor_only_actor','policy_observation_ack_verified','controller_timing_verified')},
        'evidence':[],'operator_notes':'Not qualified. Fill checks ONLY after native tests, attach actual evidence paths and SHA256s.'},exclusive=True)
