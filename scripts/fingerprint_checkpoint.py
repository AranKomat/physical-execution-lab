#!/usr/bin/env python3
"""Hash an explicit local model directory, excluding no files by default.

Download weights without optimizer state first. No keys or model bytes are output.
The manifest fingerprint can be used in config.checkpoint_sha256. This records
bytes, not proof that a remote service loaded those bytes.
"""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import digest,file_digest,atomic_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path');p.add_argument('--output',required=True)
    a=p.parse_args();root=Path(a.path).resolve();out=Path(a.output).resolve()
    if not root.is_dir():raise SystemExit('Model directory missing')
    rows=[]
    for x in sorted(root.rglob('*')):
        if x.is_file() and x.resolve()!=out and '.cache' not in x.relative_to(root).parts:
            rows.append({'path':str(x.relative_to(root)),'size':x.stat().st_size,'sha256':file_digest(x)})
    if not rows:raise SystemExit('No model files')
    body={'format':1,'files':rows};body['sha256']=digest(body);atomic_json(out,body)
    print(json.dumps({'files':len(rows),'checkpoint_sha256':body['sha256']},indent=2))
if __name__=='__main__':main()
