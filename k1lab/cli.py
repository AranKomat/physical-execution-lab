from __future__ import annotations
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from .util import load_json,atomic_json


def main(argv=None):
    p=argparse.ArgumentParser(description='K1 memory-free sparse execution lab')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    demo=sub.add_parser('synthetic');demo.add_argument('--output',required=True)
    audit=sub.add_parser('audit');audit.add_argument('path')
    mf=sub.add_parser('make-manifest');mf.add_argument('--native-config',required=True);mf.add_argument('--suites',nargs='+',required=True)
    mf.add_argument('--indices',nargs='+',type=int,default=[0,1,2]);mf.add_argument('--output',required=True)
    mf.add_argument('--trust-local-state-archives',action='store_true')
    run=sub.add_parser('run');run.add_argument('--configs',nargs='+',required=True);run.add_argument('--manifest',required=True);run.add_argument('--output',required=True)
    run.add_argument('--partition',choices=['dev','test'],default='dev')
    for name in ('allow-native','allow-api','allow-policy','pilot'):run.add_argument('--'+name,action='store_true')
    args=p.parse_args(argv)
    if args.command=='doctor':
        print(json.dumps({'python':sys.version,'native_tested_here':False,'modules':{m:importlib.util.find_spec(m) is not None
            for m in ('numpy','scipy','httpx','mujoco','robosuite','robo_harness')},
            'network_defaults':'off','memory':'current_episode_only','real_hardware_backend':False},indent=2));return
    if args.command=='synthetic':
        from .synthetic import run
        print(json.dumps(run(args.output),indent=2));return
    if args.command=='audit':
        from .journal import verify
        print(json.dumps(verify(args.path),indent=2));return
    if args.command=='make-manifest':
        if not args.trust_local_state_archives:raise SystemExit('Official/local state archives use pickle. Explicit trust required.')
        from .sources import load_k1,checked_checkout,LIBERO_REV
        from .manifests import build_native
        c=load_json(args.native_config)
        c=c.get('native',c)
        load_k1(c['k1_root']);checked_checkout(c['libero_root'],LIBERO_REV,'libero/libero/__init__.py')
        os.environ['LIBERO_ROOT']=str(Path(c['libero_root']).resolve())
        os.environ['LIBERO_CONFIG_PATH']=str(Path(c['libero_config']).resolve())
        atomic_json(args.output,build_native(args.suites,args.indices),exclusive=True);return
    if args.command=='run':
        from .runner import run_matrix
        run_matrix(args.configs,args.manifest,args.output,args.partition,args.allow_native,args.allow_api,args.allow_policy,args.pilot)

if __name__=='__main__':main()
