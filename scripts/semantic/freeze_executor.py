#!/usr/bin/env python3
"""Prepare a source-bound executor freeze; never create native qualification."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from k1lab.util import atomic_json, load_json
from semantic_lab.protocol import freeze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--config', type=Path, action='append', required=True)
    parser.add_argument('--execution-source', action='append', required=True,
                        help='repository-relative source file or source/config directory; repeat for the reviewed dependency graph')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    document = freeze(args.root, load_json(args.manifest), [load_json(path) for path in args.config],
                      execution_sources=args.execution_source)
    atomic_json(args.output, document, exclusive=True)
    print(f"Prepared {len(document['execution_sources']['files'])} execution source/config bindings; "
          'native qualification and pre-action enforcement remain separate requirements.')


if __name__ == '__main__':
    main()
