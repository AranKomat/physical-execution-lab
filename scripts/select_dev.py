#!/usr/bin/env python3
"""Create a small, explicitly development-only pilot manifest."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from k1lab.manifests import validate, seal
from k1lab.util import load_json, atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--count', type=int, default=2)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    manifest = validate(load_json(args.manifest))
    cases = [case for case in manifest['cases'] if case['partition'] == 'dev']
    if not 1 <= args.count <= len(cases):
        raise SystemExit('count must be within the development partition')
    subset = {key: value for key, value in manifest.items() if key not in ('cases', 'sha256')}
    subset.update(cases=cases[:args.count], parent_manifest_sha256=manifest['sha256'],
                  scope='development-only bring-up subset, not a test result')
    atomic_json(args.output, validate(seal(subset)), exclusive=True)
    print('\n'.join(case['id'] for case in subset['cases']))


if __name__ == '__main__':
    main()
