#!/usr/bin/env python3
"""Explicit network bootstrap, no model/data downloads or pip installation."""
import argparse,json,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--group',choices=['core','policy','transfer','robodojo','robocasa','all'],default='core')
    p.add_argument('--allow-network',action='store_true');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];lock=json.loads((root/'upstream.lock.json').read_text())
    if not a.allow_network:raise SystemExit('Review upstream.lock.json, then pass --allow-network')
    for item in lock['repositories']:
        if a.group!='all' and item['group']!=a.group:continue
        dest=root/'external'/item['name'];dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            head=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
            if head!=item['revision']:raise SystemExit('existing checkout differs: '+str(dest))
            print('already pinned:',dest);continue
        subprocess.run(['git','init',str(dest)],check=True)
        subprocess.run(['git','-C',str(dest),'remote','add','origin',item['url']],check=True)
        subprocess.run(['git','-C',str(dest),'fetch','--depth','1','origin',item['revision']],check=True)
        subprocess.run(['git','-C',str(dest),'checkout','--detach','FETCH_HEAD'],check=True)
if __name__=='__main__':main()
