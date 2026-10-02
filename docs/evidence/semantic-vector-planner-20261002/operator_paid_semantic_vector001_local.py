"""Own one bounded planner-vector pilot and its existing budget relay."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/Users/macbookpro/Developer/random/gpu/physical-execution-lab')
sys.path.insert(0, str(root))
from scripts.multibench.run_pi05_native_pilot import wait_ready
from scripts.multibench.launch_robodojo_case import stop_child

name = 'semantic-vector-planner-pilot001'
out = root / 'runs' / (name + '_api')
campaign = root.parent / 'internal/inference-experiments-hy-embodied/campaigns/visual-planners-2026-09'
ledger = root.parent / 'internal/inference-experiments-hy-embodied/runs/hy-025-openrouter-development/budget.jsonl'
count = sum(json.loads(s)['event'] == 'reserved' for s in ledger.read_text().splitlines())
relay = [str(root / '.venv/bin/python'), '-u', str(root / 'scripts/multibench/budget_responses_relay.py'),
    '--campaign-root', str(campaign), '--key-file', str(root.parent / '.env'),
    '--output', str(out), '--name', name, '--expected-calls', str(count),
    '--tool-name', 'semantic_goal', '--max-calls', '10', '--wall-limit-s', '1800', '--cap-usd', '0.25']
for ident in ('g05-sparse-sol-flex-dev-001-0', 'g05-sparse-sol-flex-dev-002-0', 'xr1-supervision-kettle-001-1'):
    relay.extend(['--acknowledge-failed-request', ident])
ssh = ['ssh', '-p', '53210', '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10',
    '-o', 'ServerAliveCountMax=3', 'root@92.180.27.84']
remote = '/root/physical-execution-lab'
token_path = remote + '/runs/semantic-vector-planner-pilot001-token'
children = []
try:
    with (root / 'runs' / (name + '_relay.log')).open('x') as log:
        child = subprocess.Popen(relay, cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        children.append(child)
        wait_ready(child, root / 'runs' / (name + '_relay.log'),
            lambda r: r.get('event') == 'relay_ready', timeout=60)
        tunnel = subprocess.Popen(ssh[:-1] + ['-o', 'ExitOnForwardFailure=yes', '-N',
            '-R', '19861:127.0.0.1:19861', ssh[-1]], start_new_session=True)
        children.append(tunnel)
        os.chmod(out / 'relay-token', 0o600)
        subprocess.run(['scp', '-P', '53210', str(out / 'relay-token'),
            'root@92.180.27.84:' + token_path], check=True)
        if tunnel.poll() is not None:
            raise RuntimeError('owned tunnel exited before vector pilot')
        command = remote + '/.venv/bin/python -u ' + remote + '/runs/operator_launch_paid_vector001.py'
        child = subprocess.Popen(ssh + [command], start_new_session=True)
        children.append(child)
        if child.wait(timeout=2400):
            raise RuntimeError('vector pilot error retained; no automatic retry')
finally:
    for child in reversed(children):
        stop_child(child)
    (out / 'relay-token').unlink(missing_ok=True)
