#!/usr/bin/env python3
"""Own a bounded local relay, reverse tunnel and one complete remote task method."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.multibench.run_pi05_native_pilot import wait_ready
from scripts.multibench.launch_robodojo_case import stop_child


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--approach', choices=('direct', 'numeric', 'semantic'), required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--campaign-root', type=Path, required=True)
    p.add_argument('--key-file', type=Path, required=True)
    p.add_argument('--ledger', type=Path, required=True)
    p.add_argument('--ssh-host', required=True)
    p.add_argument('--ssh-port', type=int, required=True)
    p.add_argument('--remote-root', default='/root/physical-execution-lab')
    p.add_argument('--prepared', required=True)
    p.add_argument('--freeze', required=True)
    p.add_argument('--baseline-run', required=True)
    p.add_argument('--native-reference-freeze', required=True)
    p.add_argument('--controller-run', required=True)
    p.add_argument('--acknowledge-failed-request', action='append', default=[])
    p.add_argument('--allow-standard-fallback', action='store_true')
    p.add_argument('--shared-cap-usd', choices=('85', '95'), default='85')
    p.add_argument('--simulator-libstdcxx', help='Remote host runtime library; simulator-only preload')
    args = p.parse_args()
    if not args.name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.name):
        raise ValueError('name must be a fresh lowercase run identifier')
    out = ROOT / 'runs' / (args.name + '_api')
    remote = args.remote_root.rstrip('/')
    token_path = remote + '/runs/' + args.name + '-token'
    count = sum(json.loads(s)['event'] == 'reserved' for s in args.ledger.read_text().splitlines())
    relay = [str(ROOT / '.venv/bin/python'), '-u',
        str(ROOT / 'scripts/multibench/budget_responses_relay.py'),
        '--campaign-root', str(args.campaign_root), '--key-file', str(args.key_file),
        '--output', str(out), '--name', args.name, '--expected-calls', str(count),
        '--tool-name', 'semantic_goal' if args.approach == 'semantic' else 'robot_decision',
        '--max-calls', '1800', '--profile', 'full_panel1800',
        '--wall-limit-s', '3600', '--cap-usd', '3', '--shared-cap-usd', args.shared_cap_usd]
    for ident in args.acknowledge_failed_request:
        relay.extend(['--acknowledge-failed-request', ident])
    if args.allow_standard_fallback:
        relay.append('--allow-standard-fallback')
    ssh = ['ssh', '-p', str(args.ssh_port), '-o', 'ConnectTimeout=15',
           '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3', args.ssh_host]
    children = []
    try:
        with (ROOT / 'runs' / (args.name + '_relay.log')).open('x') as log:
            child = subprocess.Popen(relay, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            children.append(child)
            wait_ready(child, ROOT / 'runs' / (args.name + '_relay.log'),
                       lambda row: row.get('event') == 'relay_ready', timeout=60)
            tunnel = subprocess.Popen(ssh[:-1] + ['-o', 'ExitOnForwardFailure=yes', '-N',
                '-R', '19861:127.0.0.1:19861', ssh[-1]], start_new_session=True)
            children.append(tunnel)
            os.chmod(out / 'relay-token', 0o600)
            subprocess.run(['scp', '-P', str(args.ssh_port), str(out / 'relay-token'),
                            args.ssh_host + ':' + token_path], check=True)
            if tunnel.poll() is not None:
                raise RuntimeError('owned tunnel exited before full-panel startup')
            # Read the short-lived token on the remote host; never put it in argv/logs.
            command = [remote + '/.venv-pi05/bin/python', '-u',
                remote + '/scripts/semantic/run_full_panel_baseline.py',
                '--approach', args.approach, '--allow-api', '--prepared', args.prepared,
                '--freeze', args.freeze, '--baseline-run', args.baseline_run,
                '--native-reference-freeze', args.native_reference_freeze,
                '--controller-run', args.controller_run, '--output', remote + '/runs/' + args.name]
            if args.allow_standard_fallback:
                command.append('--allow-standard-fallback')
            if args.simulator_libstdcxx:
                command.extend(['--simulator-libstdcxx', args.simulator_libstdcxx])
            wire = 'K1_RELAY_TOKEN=$(cat ' + shlex.quote(token_path) + ') ' + shlex.join(command)
            child = subprocess.Popen(ssh + [wire], start_new_session=True)
            children.append(child)
            if child.wait(timeout=4800):
                raise RuntimeError('full-panel error retained; no automatic retry')
    finally:
        for child in reversed(children):
            stop_child(child)
        (out / 'relay-token').unlink(missing_ok=True)
        subprocess.run(ssh + ['rm -f -- ' + shlex.quote(token_path)], timeout=30, check=False)


if __name__ == '__main__':
    main()
