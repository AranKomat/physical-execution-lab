#!/usr/bin/env python3
"""Own a fresh pi0.5 source/bridge for recorded-input timing, without physics."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from k1lab.util import atomic_json, load_json
from scripts.multibench.launch_robodojo_case import stop_child
from scripts.multibench.run_pi05_native_pilot import wait_ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bound-root', 'observation', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--model-gpu', type=int, choices=(0, 1), default=0)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        parser.error('explicit --execute required; no robot or paid API calls')
    root = Path(__file__).resolve().parents[2]
    bound = Path(args.bound_root).resolve()
    provider = load_json(bound / 'provider.json')
    config = load_json(bound / 'robodojo_pi05_motor_only.json')
    if provider['backend'] != 'pi05' or config['mode'] != 'motor_only':
        raise ValueError('requires exact pi05 motor-only bundle')
    observation = Path(args.observation).resolve()
    if not observation.is_file():
        raise FileNotFoundError(observation)
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    atomic_json(out / 'remote-policy.json', config['policy'], exclusive=True)
    policy_python = str(root / '.venv-pi05/bin/python')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(args.model_gpu),
               XLA_PYTHON_CLIENT_PREALLOCATE='false',
               PYTHONPATH=str(root / 'external/GPT-as-Policy'))
    source = [policy_python, '-u', '-m', 'hybrid_rollout.robodojo.pi05_server.server',
              '--checkpoint', provider['checkpoint_path'], '--port', str(provider['port']),
              '--identity-output', str(out / 'source-identity.json')]
    bridge = [policy_python, '-u', str(root / 'run_bench.py'), 'serve-policy',
              '--config', str(bound / 'provider.json'),
              '--port', config['policy']['endpoint'].rsplit(':', 1)[1], '--allow-policy']
    measure = [str(root / '.venv/bin/python'), str(root / 'run_bench.py'), 'latency',
               '--config', str(out / 'remote-policy.json'), '--observations', str(observation),
               '--warmup', '3', '--repeats', '30', '--allow-policy',
               '--output', str(out / 'latency.json')]
    atomic_json(out / 'plan.json', {'source': source, 'bridge': bridge, 'measure': measure,
                                  'model_gpu': args.model_gpu, 'paid_calls': 0,
                                  'native_actions': 0}, exclusive=True)
    children = []
    try:
        with (out / 'source.log').open('x') as source_log, (out / 'bridge.log').open('x') as bridge_log:
            child = subprocess.Popen(source, cwd=root, env=env, stdout=source_log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            wait_ready(child, out / 'source.log', lambda row: row.get('event') == 'loaded')
            child = subprocess.Popen(bridge, cwd=root, env=env, stdout=bridge_log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            children.append(child)
            wait_ready(child, out / 'bridge.log', lambda row: row.get('ready') is True)
            with (out / 'measure.log').open('x') as log:
                child = subprocess.Popen(measure, cwd=root, env=env, stdout=log,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                children.append(child)
                if child.wait(timeout=600):
                    raise RuntimeError('recorded-input timing failed; retained evidence, no retry')
            print((out / 'latency.json').read_text(), flush=True)
    finally:
        for child in reversed(children):
            stop_child(child)


if __name__ == '__main__':
    main()
