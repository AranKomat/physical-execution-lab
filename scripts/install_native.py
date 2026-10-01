#!/usr/bin/env python3
"""Display/install pinned local native dependencies in an isolated Python 3.10-3.12 venv.

This installation recipe is source-derived, NOT end-to-end tested here. It avoids
RPent's moving branch extras by installing its native distributions explicitly.
Inspect output and upstream packaging changes. Freeze the solved environment.
"""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
    p.add_argument('--k1',action='store_true');a=p.parse_args()
    paths=[ROOT/'external'/n for n in ('RPent','RLinf','openpi','LIBERO','LIBERO-PRO')]
    cmd=[sys.executable,'-m','pip','install',*map(str,paths[1:]),'-e',str(paths[0]),
         'mujoco==3.3.0','numpy<2','omegaconf','gymnasium','h5py','Pillow','imageio[ffmpeg]']
    if a.k1:cmd.extend(['-e',str(ROOT/'external/k1')])
    print(json.dumps(cmd,indent=2))
    if a.execute:
        if not (3,10)<=sys.version_info[:2]<(3,13):raise SystemExit('Native RPent requires Python 3.10-3.12; use a separate venv.')
        if any(not x.exists() for x in paths):raise SystemExit('Run bootstrap first.')
        subprocess.run(cmd,check=True)
        subprocess.run([sys.executable,'-m','pip','check'],check=True)
    else:print('PLAN ONLY. Solver compatibility and transitive runtime requirements still need native qualification.')
if __name__=='__main__':main()
