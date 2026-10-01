#!/usr/bin/env python3
"""Verify packaged source/evidence bytes against SOURCE_MANIFEST.json."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text());bad=[]
    for entry in m['files']:
        p=ROOT/entry['path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
            bad.append(entry['path'])
    print(json.dumps({'verified':not bad,'files':len(m['files']),'mismatches':bad},indent=2))
    return 1 if bad else 0
if __name__=='__main__':raise SystemExit(main())
