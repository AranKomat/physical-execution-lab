#!/usr/bin/env python3
"""Run a predeclared paper-track matrix in isolated processes, sequentially.

Plan-only unless --execute. Each arm must already have its own reviewed config.
No implicit model downloads, model calls, or GPU launch. Global provider/service
concurrency and financial budgets remain the operator's responsibility.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from prl.util import read_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configs',nargs='+',required=True)
    p.add_argument('--manifest',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--allow-native',action='store_true')
    p.add_argument('--allow-api',action='store_true')
    a=p.parse_args()
    arms=[read_json(c)['arm'] for c in a.configs]
    if len(arms)!=len(set(arms)):raise SystemExit('One unique arm per matrix; use separate matrices for model variants.')
    commands=[]
    for config,arm in zip(a.configs,arms):
        command=[sys.executable,str(ROOT/'paper_run.py'),'run','--config',str(Path(config).resolve()),
                 '--manifest',str(Path(a.manifest).resolve()),'--output',str(Path(a.output).resolve()/arm)]
        if a.allow_native:command.append('--allow-native')
        if a.allow_api:command.append('--allow-api')
        commands.append(command)
    print(json.dumps({'execute':a.execute,'commands':commands},indent=2),flush=True)
    if a.execute:
        for command in commands:
            subprocess.run(command,cwd=ROOT,check=True)
            out=Path(command[command.index('--output')+1])
            summary=read_json(out/'summary.json')
            if not summary['complete_manifest'] or summary['errors']:
                raise SystemExit('Matrix stopped: incomplete/error arm. Inspect before resuming; no automatic reruns.')
    return 0
if __name__=='__main__':raise SystemExit(main())
