#!/usr/bin/env python3
"""Freeze code, configs and task-state manifest *before* viewing test outcomes."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from k1lab.util import load_json,atomic_json,file_sha
from k1lab.manifests import validate
from k1lab.runner import source_hash,validate_config
from k1lab.qualification import config_identity

def main():
    p=argparse.ArgumentParser();p.add_argument('--configs',nargs='+',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--output',required=True);a=p.parse_args()
    m=validate(load_json(a.manifest));configs=[load_json(x) for x in a.configs]
    for c in configs:
        # Bind the effective model now, rather than letting an environment variable
        # silently change the frozen actor between development and evaluation.
        c["model"] = validate_config(c)
    if len({c["condition"] for c in configs}) != len(configs):
        raise ValueError("duplicate condition in freeze")
    frozen={'source_sha256':source_hash(),'manifest_sha256':m['sha256'],
            'actor_memory_scope':'current_episode_only','configs':{c['condition']:config_identity(c) for c in configs},
            'note':'Do not inspect test results then regenerate this freeze and call the same conditions held-out.'}
    atomic_json(a.output,frozen,exclusive=True);h=file_sha(a.output)
    for path,c in zip(a.configs,configs):
        c['freeze_manifest_path']=str(Path(a.output).resolve());c['freeze_manifest_sha256']=h
        atomic_json(path,c)
    print('Frozen:',a.output,h)
if __name__=='__main__':main()
