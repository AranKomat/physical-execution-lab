#!/usr/bin/env python3
"""Prepare fixed cases/configs; no model downloads, API requests or simulator actions."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from semantic_lab.comparison import prepare
from k1lab.util import atomic_json, load_json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--provider', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-standard-fallback', action='store_true')
    args = parser.parse_args()
    panel, configs, plan = prepare(load_json(args.manifest), load_json(args.provider),
                                  allow_standard_fallback=args.allow_standard_fallback)
    args.output.mkdir(parents=True, exist_ok=False)
    atomic_json(args.output/'cases.json', panel, exclusive=True)
    for name, config in configs.items():
        atomic_json(args.output/(name+'.json'), config, exclusive=True)
    atomic_json(args.output/'plan.json', plan, exclusive=True)
    print('Prepared 40 missing slots; native admission, source freeze and budget binding still required.')
