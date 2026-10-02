#!/usr/bin/env python3
"""Copy only new semantic files into a separate live worktree. Dry-run by default.

Never copy legacy k1lab/, previous results, credentials, model assets or configs.
Existing identical new files are allowed; differing destinations fail before writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

SOURCE = Path(__file__).resolve().parents[2]
ALLOWED_DIRS = ('semantic_lab/', 'scripts/semantic/', 'configs/semantic/', 'tests/semantic/', 'docs/semantic/')
ALLOWED_FILES = {'run_semantic.py', 'HANDOFF_V5.md', 'TAKEOVER_V5.md', 'START_HERE_V5.md', 'OVERLAY_V5.json'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plan(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or not (target / 'k1lab/multibench').is_dir():
        raise ValueError('target must be a different existing Physical Execution Lab checkout')
    manifest = json.loads((source / 'OVERLAY_V5.json').read_text())
    rows = []
    for rel, expected in manifest['files'].items():
        if rel not in ALLOWED_FILES and not rel.startswith(ALLOWED_DIRS):
            raise ValueError('overlay contains a forbidden destination: ' + rel)
        src, dst = source / rel, target / rel
        if not src.resolve().is_relative_to(source) or not dst.resolve().is_relative_to(target):
            raise ValueError('path escapes source/target')
        if not src.is_file() or src.is_symlink() or sha(src) != expected:
            raise ValueError('overlay source checksum mismatch: ' + rel)
        if dst.exists() and (not dst.is_file() or dst.is_symlink() or sha(dst) != expected):
            raise FileExistsError('would overwrite a different file: ' + rel)
        rows.append((src, dst, not dst.exists()))
    # The checksum manifest is copied separately; it cannot hash itself.
    manifest_src, manifest_dst = source / 'OVERLAY_V5.json', target / 'OVERLAY_V5.json'
    if manifest_dst.exists() and (manifest_dst.is_symlink() or not manifest_dst.is_file() or sha(manifest_dst) != sha(manifest_src)):
        raise FileExistsError('would overwrite a different overlay manifest')
    if not any(dst == manifest_dst for _, dst, _ in rows):
        rows.append((manifest_src, manifest_dst, not manifest_dst.exists()))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target', required=True)
    p.add_argument('--apply', action='store_true')
    a = p.parse_args()
    rows = plan(SOURCE, a.target)
    print(json.dumps({'target': str(Path(a.target).resolve()), 'files': len(rows),
                      'new_files': sum(new for _,_,new in rows),
                      'legacy_files_overwritten': 0, 'apply': a.apply}, indent=2))
    if a.apply:
        for src, dst, new in rows:
            if new:
                dst.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation means a concurrent agent cannot be overwritten.
                with dst.open('xb') as f:
                    f.write(src.read_bytes())
                shutil.copymode(src, dst)
        print('Applied additive files only. Run python run_semantic.py doctor in target.')

if __name__ == '__main__': main()
