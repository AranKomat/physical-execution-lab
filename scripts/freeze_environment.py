#!/usr/bin/env python3
"""Snapshot package/git metadata only. Does not read keys or start CUDA models."""
import argparse,subprocess,sys,platform,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prl.util import atomic_json,digest

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    rows={}
    for x in (ROOT/'external').glob('*'):
        if (x/'.git').exists():
            rows[x.name]={
                'head':subprocess.check_output(['git','-C',str(x),'rev-parse','HEAD'],text=True).strip(),
                'tracked_dirty':bool(subprocess.check_output(['git','-C',str(x),'status','--porcelain','--untracked-files=no'],text=True).strip())}
    # pip freeze can contain credential-bearing URLs; redact sensitive userinfo.
    import re
    freeze=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True)
    freeze=re.sub(r'(https?://)[^/@\s]+:[^/@\s]+@',r'\1<REDACTED>@',freeze)
    d={'python':sys.version,'platform':platform.platform(),'repositories':rows,'pip_freeze':freeze,
       'note':'Review before publication. No driver/kernel/hardware qualification implied.'}
    d['sha256']=digest(d);atomic_json(Path(a.output),d)
    print(json.dumps({'environment_sha256':d['sha256']},indent=2))
if __name__=='__main__':main()
