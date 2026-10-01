#!/usr/bin/env python3
"""Inspect by default; --execute downloads source ONLY at explicit reviewed pins.

Does not install packages, download weights, run upstream code or start services.
Existing repositories are checked but never reset/cleaned behind the user's back.
"""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def plan(group='core',destination=None):
    d=Path(destination) if destination else ROOT/'external'
    lock=json.loads((ROOT/'upstream.lock.json').read_text())
    return [(row,d/row['name']) for row in lock['repositories'] if group=='all' or row['group']==group]

def materialize(row,path):
    if path.exists():
        if not (path/'.git').exists():raise RuntimeError(f'Not an owned git checkout: {path}')
        rev=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        dirty=subprocess.check_output(['git','-C',str(path),'status','--porcelain','--untracked-files=no'],text=True)
        if rev!=row['revision'] or dirty.strip():raise RuntimeError(f'Existing checkout differs: {path}; no automatic reset')
        return
    path.mkdir(parents=True)
    try:
        subprocess.run(['git','init',str(path)],check=True)
        subprocess.run(['git','-C',str(path),'remote','add','origin',row['url']],check=True)
        subprocess.run(['git','-C',str(path),'fetch','--depth','1','origin',row['revision']],check=True)
        subprocess.run(['git','-C',str(path),'checkout','--detach',row['revision']],check=True)
    except Exception:
        print(f'Incomplete checkout retained at {path}; inspect manually.',file=sys.stderr)
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--group',choices=['core','k1','all'],default='core')
    p.add_argument('--destination');p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    rows=plan(a.group,a.destination)
    print(json.dumps([{'url':r['url'],'revision':r['revision'],'path':str(d)} for r,d in rows],indent=2))
    if a.execute:
        for row,path in rows:materialize(row,path)
    else:print('PLAN ONLY. Add --execute to download pinned source. No model or native execution.')
if __name__=='__main__':main()
