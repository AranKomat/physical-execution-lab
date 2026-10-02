#!/usr/bin/env python3
"""Reuse the LIVE owned-process launcher; substitute only the controller entrypoint.

No stale v4 launcher replaces the native fixes in the external checkout.
"""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from semantic_lab.protocol import require_live_base


def main():
    if '--execute' in sys.argv:
        require_live_base(ROOT)
    path = ROOT / 'scripts/multibench/launch_robodojo_case.py'
    spec = importlib.util.spec_from_file_location('_live_native_launcher', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    original = mod.plan
    def plan(args):
        value = original(args)
        command = value['controller_argv']
        old = str(ROOT / 'run_bench.py')
        if old not in command:
            raise RuntimeError('live launcher API changed; review before using this shim')
        command[command.index(old)] = str(ROOT / 'run_semantic.py')
        value['semantic_entrypoint'] = True
        return value
    mod.plan = plan  # Process-local function injection, no file modification.
    mod.main()

if __name__ == '__main__': main()
