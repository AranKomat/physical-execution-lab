#!/usr/bin/env python3
"""Run explicitly supplied conditions sequentially on the same manifest.

No automatic retry or parallel GPU oversubscription. Each config has its own API
budget: allocate these so their SUM respects your actual campaign budget.
"""
import argparse,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.runner import run_experiment
from prl.util import read_json,atomic_json
from prl.evaluation import compare_runs

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--configs',nargs='+',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    p.add_argument('--allow-native',action='store_true');p.add_argument('--allow-api',action='store_true')
    a=p.parse_args();root=Path(a.output);root.mkdir(parents=True,exist_ok=False)
    runs={}
    for path in a.configs:
        cfg=read_json(path);mode=cfg['mode']
        if mode in runs:raise SystemExit('Duplicate mode output')
        out=root/mode
        summary=run_experiment(cfg,a.manifest,out,allow_native=a.allow_native,allow_api=a.allow_api)
        runs[mode]=out
        if not summary['fully_completed']:
            raise SystemExit(f'Stopped after incomplete {mode}; inspect {out}')
    if {'nominal','dynamic'}<=set(runs):
        atomic_json(root/'nominal_vs_dynamic.json',compare_runs(runs['nominal'],runs['dynamic'],'governor'))
    if {'dynamic','dynamic_k1'}<=set(runs):
        atomic_json(root/'dynamic_vs_k1.json',compare_runs(runs['dynamic'],runs['dynamic_k1'],'perception'))
    print(json.dumps({'runs':{k:str(v) for k,v in runs.items()}},indent=2))
if __name__=='__main__':main()
