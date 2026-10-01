#!/usr/bin/env python3
"""Bind remote experiment configurations to actual provider settings and artifact bytes.

Writes NEW files only. Does not load a model, start a service, or change endpoints.
Resolve model/config locations first. Rebinding after tuning requires a new freeze.
"""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import load_json,atomic_json
from k1lab.errors import ContractError
from k1lab.multibench.manifest import resolved_config

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--provider-config',required=True)
    p.add_argument('--experiments',nargs='+',required=True);p.add_argument('--output',required=True)
    p.add_argument('--policy-port',type=int);a=p.parse_args()
    if a.policy_port is not None and not 1<=a.policy_port<=65535:raise ContractError('invalid policy port')
    provider=resolved_config({'policy':load_json(a.provider_config)})['policy'];out=Path(a.output)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True);atomic_json(out/'provider.json',provider,exclusive=True)
    for i,path in enumerate(a.experiments):
        cfg=load_json(path);remote=cfg.get('policy')
        if not remote or remote['backend']!='remote' or remote['identity']['name']!=provider['identity']['name']:
            raise ContractError('experiment is not a remote configuration for this policy')
        remote['identity']=provider['identity'];remote['artifact_manifest']=provider['artifact_manifest']
        if a.policy_port is not None:remote['endpoint']=f'http://127.0.0.1:{a.policy_port}'
        if i==0:atomic_json(out/'policy-remote.json',remote,exclusive=True)
        atomic_json(out/Path(path).name,resolved_config(cfg),exclusive=True)
