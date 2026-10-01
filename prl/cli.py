from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path
from .util import read_json,atomic_json,plain,digest
from .errors import PRLError


def main(argv=None):
    p=argparse.ArgumentParser(description='CPU-testable physical runtime experiment; native/API actions are opt-in.')
    s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('doctor'); q.add_argument('--rpent-root',default='external/RPent')
    q=s.add_parser('run'); q.add_argument('--config',required=True);q.add_argument('--manifest',required=True)
    q.add_argument('--output',required=True);q.add_argument('--allow-native',action='store_true')
    q.add_argument('--allow-api',action='store_true');q.add_argument('--resume',action='store_true')
    q=s.add_parser('summary');q.add_argument('run')
    q=s.add_parser('compare');q.add_argument('a');q.add_argument('b');q.add_argument('--contrast',default='governor',choices=['governor','system','perception','evolution']);q.add_argument('--output')
    q=s.add_parser('audit-journal');q.add_argument('path')
    q=s.add_parser('catalog');q.add_argument('--rpent-root',default='external/RPent');q.add_argument('--output',required=True)
    q.add_argument('--suites',nargs='+')
    q=s.add_parser('manifest');q.add_argument('--catalog',required=True);q.add_argument('--output',required=True)
    q.add_argument('--split',choices=['dev','test','smoke'],required=True);q.add_argument('--states',nargs='+',type=int,required=True)
    q.add_argument('--tasks',nargs='+',type=int);q.add_argument('--policy-repeats',type=int,default=1)
    q=s.add_parser('check-splits');q.add_argument('dev');q.add_argument('test')
    q=s.add_parser('attribute');q.add_argument('run')
    q=s.add_parser('gate');q.add_argument('baseline');q.add_argument('candidate');q.add_argument('--policy-reference');q.add_argument('--output')
    q=s.add_parser('protocol-audit');q.add_argument('--protocol',default='configs/paper_protocol.json')
    args=p.parse_args(argv)
    try:
        if args.cmd=='doctor':
            packages=['numpy','PIL','pytest','rpent','robo_harness','mujoco','torch']
            result={'python':sys.version.split()[0],
                'native_python_compatible':(3,10)<=sys.version_info[:2]<(3,13),
                'packages':{n:importlib.util.find_spec(n) is not None for n in packages},
                'rpent_checkout':(Path(args.rpent_root)/'robots/libero/tools.py').exists(),
                'network_requests':0,'model_loads':0,'native_runs':0,
                'note':'Presence checks only; no GPU/runtime qualification.'}
        elif args.cmd=='run':
            from .runner import run_experiment
            result=run_experiment(read_json(args.config),args.manifest,args.output,
                allow_native=args.allow_native,allow_api=args.allow_api,resume=args.resume)
            result={k:v for k,v in result.items() if k!='episodes'}
        elif args.cmd=='summary':
            from .evaluation import summarize_run
            result=summarize_run(args.run)
        elif args.cmd=='compare':
            from .evaluation import compare_runs
            result=compare_runs(args.a,args.b,args.contrast)
            if args.output:atomic_json(Path(args.output),result)
        elif args.cmd=='audit-journal':
            from .journal import Journal
            rows=Journal.verify(Path(args.path));result={'valid':True,'events':len(rows),'tail':rows[-1]['hash'] if rows else None}
        elif args.cmd=='catalog':
            from .backends.rpent import catalog_states
            from .manifests import DYNA_SUITES
            result={'source':'installed_RPent_LIBERO-PRO_states',
                    'states':catalog_states(args.rpent_root,args.suites or DYNA_SUITES)}
            result['sha256']=digest(result);atomic_json(Path(args.output),result)
        elif args.cmd=='manifest':
            from .manifests import build_native_manifest,write_manifest
            cat=read_json(args.catalog)
            rows=build_native_manifest(cat,args.split,args.states,args.tasks,args.policy_repeats)
            result=write_manifest(args.output,'native',args.split,rows,
                'Stored official initial-state indices; NOT a reproduction of newly sampled DynaHarness states.',cat['sha256'])
        elif args.cmd=='check-splits':
            from .manifests import load_manifest,assert_disjoint
            a,_=load_manifest(args.dev);b,_=load_manifest(args.test);assert_disjoint(a,b);result={'disjoint':True}
        elif args.cmd=='attribute':
            from .evaluation import read_run
            from .evolution import attribute
            result=[attribute(r) for r in read_run(args.run)[3].values()]
        elif args.cmd=='gate':
            from .evolution import regression_gate
            result=regression_gate(args.baseline,args.candidate,args.policy_reference)
            if args.output:atomic_json(Path(args.output),result)
        elif args.cmd=='protocol-audit':
            d=read_json(args.protocol);missing=[k for k,v in d['exact_replication_requirements'].items() if v is None]
            result={'exact_reproduction_ready':not missing,'missing':missing,
                    'supported_claim':'PDF-grounded reconstruction; run paper_run.py audit for current scope. Native parity and gains remain unmeasured.'}
        print(json.dumps(plain(result),indent=2,allow_nan=False))
        return 0
    except (PRLError,FileExistsError,FileNotFoundError,KeyError,ValueError) as e:
        print(json.dumps({'error':type(e).__name__,'message':str(e)}),file=sys.stderr)
        return 2
