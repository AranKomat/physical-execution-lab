#!/usr/bin/env python3
"""Verify distributed bytes against RELEASE_MANIFEST.json (not a signature)."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest = json.loads((root / 'RELEASE_MANIFEST.json').read_text())
    missing, changed = [], []
    for name, expected in manifest['files'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise SystemExit('invalid relative path in release manifest')
        if not path.is_file():
            missing.append(name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            changed.append(name)
    result = {'checked_files': len(manifest['files']), 'missing': missing, 'changed': changed,
              'scope': 'packaged-byte integrity only; not authorship or native qualification'}
    print(json.dumps(result, indent=2))
    if missing or changed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
