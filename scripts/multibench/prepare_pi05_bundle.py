#!/usr/bin/env python3
"""Bind the downloaded exact pi0.5 files; no inference or simulator launch."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, load_json
from k1lab.multibench.manifest import artifacts, resolved_config

NATIVE_HASH = 'd15fb8bd1d29cb30b69f01b71c66596cb0293c1a8a94111b343c1580dd3e3e5b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source-port', type=int, default=19114)
    parser.add_argument('--policy-port', type=int, default=19603)
    args = parser.parse_args()
    if any(not 1 <= p <= 65535 for p in (args.source_port, args.policy_port)):
        raise ValueError('invalid policy port')
    root = Path(__file__).resolve().parents[2]
    checkpoint = Path(args.checkpoint).resolve()
    manifest = artifacts(checkpoint)
    native_files = {name: value for name, value in manifest['files'].items()
                    if name.startswith(('params/', 'assets/'))}
    native_hash = hashlib.sha256(json.dumps(native_files, sort_keys=True).encode()).hexdigest()
    if native_hash != NATIVE_HASH:
        raise ValueError('checkpoint differs from donor-recorded exact pi0.5 identity')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out / 'artifacts.json', manifest, exclusive=True)
    provider = load_json(root / 'configs/multibench/policies/pi05.json')
    provider.update(checkpoint_path=str(checkpoint), artifact_manifest=str(out / 'artifacts.json'),
                    artifact_dir=str(out / 'policy-proposals'), port=args.source_port,
                    gpt_as_policy_root=str(root / 'external/GPT-as-Policy'),
                    native_checkpoint_sha256=native_hash)
    provider = resolved_config({'policy': provider})['policy']
    atomic_json(out / 'provider.json', provider, exclusive=True)
    for mode in ('motor_only', 'review_every_chunk', 'sparse'):
        name = 'robodojo_pi05_' + mode
        config = load_json(root / 'configs/multibench' / (name + '.json'))
        config['environment']['gpt_as_policy_root'] = str(root / 'external/GPT-as-Policy')
        config['policy'].update(identity=provider['identity'],
                                artifact_manifest=provider['artifact_manifest'],
                                endpoint='http://127.0.0.1:' + str(args.policy_port))
        atomic_json(out / (name + '.json'), resolved_config(config), exclusive=True)
    print(json.dumps({'event': 'bound', 'native_checkpoint_sha256': native_hash,
                      'provider_identity': provider['identity'], 'output': str(out)}), flush=True)


if __name__ == '__main__':
    main()
