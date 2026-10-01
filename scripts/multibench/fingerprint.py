#!/usr/bin/env python3
"""Record runtime facts; no GPU import, environment mutation, or model invocation."""
import argparse,importlib.metadata,json,platform,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json


from k1lab.multibench.fingerprint import capture

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();atomic_json(a.output,capture(),exclusive=True)
