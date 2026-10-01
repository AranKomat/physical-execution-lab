#!/usr/bin/env python3
"""Own one fresh pi0.5 source server, policy bridge and development episode."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.multibench.launch_robodojo_case import stop_child
from k1lab.util import atomic_json, load_json


def wait_ready(child, log, predicate, timeout=600):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError('owned server exited; inspect ' + str(log))
        for line in log.read_text(errors='replace').splitlines():
            try:
                if predicate(json.loads(line)):
                    return
            except (ValueError, TypeError, AttributeError):
                pass
        time.sleep(1)
    raise TimeoutError('owned server readiness timeout: ' + str(log))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('bound-root', 'manifest', 'case-id', 'source-panel', 'sim-python', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        parser.error('explicit --execute required; development only, no paid API')
    root = Path(__file__).resolve().parents[2]
    bound = Path(args.bound_root).resolve()
    config = load_json(bound / 'robodojo_pi05_motor_only.json')
    provider = load_json(bound / 'provider.json')
    if config['mode'] != 'motor_only' or provider['backend'] != 'pi05':
        raise ValueError('requires exact pi0.5 motor-only bundle')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    policy_python = str(root / '.venv-pi05/bin/python')
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='1', XLA_PYTHON_CLIENT_PREALLOCATE='false',
               PYTHONPATH=str(root / 'external/GPT-as-Policy'))
    source = [policy_python, '-u', '-m', 'hybrid_rollout.robodojo.pi05_server.server',
              '--checkpoint', provider['checkpoint_path'], '--port', str(provider['port']),
              '--identity-output', str(out / 'source-identity.json')]
    port = config['policy']['endpoint'].rsplit(':', 1)[1]
    bridge = [policy_python, '-u', str(root / 'run_bench.py'), 'serve-policy',
              '--config', str(bound / 'provider.json'), '--port', port, '--allow-policy']
    episode = [str(root / '.venv/bin/python'), '-u',
               str(root / 'scripts/multibench/launch_robodojo_case.py'),
               '--config', str(bound / 'robodojo_pi05_motor_only.json'),
               '--manifest', str(Path(args.manifest).resolve()), '--case-id', args.case_id,
               '--source-panel', str(Path(args.source_panel).resolve()),
               '--sim-python', args.sim_python, '--robodojo-root', str(root / 'external/RoboDojo'),
               '--sim-port', '19117', '--output', str(out / 'episode'),
               '--development', '--allow-policy', '--execute']
    atomic_json(out / 'plan.json', {'source': source, 'bridge': bridge, 'episode': episode,
                                  'model_gpu': 1, 'simulator_gpu': 0, 'paid_calls': 0}, exclusive=True)
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
            print(json.dumps({'event': 'native_episode_start', 'case_id': args.case_id}), flush=True)
            native_env = dict(os.environ, CUDA_VISIBLE_DEVICES='0', OMNI_KIT_ACCEPT_EULA='YES')
            with (out / 'launch.log').open('x') as launch_log:
                child = subprocess.Popen(episode, cwd=root, env=native_env, stdout=launch_log,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                children.append(child)
                code = child.wait(timeout=4500)
                if code:
                    raise RuntimeError('native launcher failed; retained evidence, no retry')
            print((out / 'episode/controller/result.json').read_text(), flush=True)
    finally:
        for child in reversed(children):
            stop_child(child)


if __name__ == '__main__':
    main()
