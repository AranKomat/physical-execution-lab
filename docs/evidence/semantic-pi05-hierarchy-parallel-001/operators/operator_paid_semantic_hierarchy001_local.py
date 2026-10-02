import json
import argparse
from pathlib import Path
import subprocess
import sys

root = Path('/Users/macbookpro/Developer/random/gpu/physical-execution-lab')
sys.path.insert(0, str(root))
from scripts.multibench.run_pi05_native_pilot import wait_ready
from scripts.multibench.launch_robodojo_case import stop_child

p = argparse.ArgumentParser()
p.add_argument('--case-id', required=True)
p.add_argument('--name', required=True)
p.add_argument('--worker-gpu', type=int, choices=(0, 1), default=0)
a = p.parse_args()
name = a.name
out = root / 'runs' / (name + '_api')
campaign = root.parent / 'internal/inference-experiments-hy-embodied/campaigns/visual-planners-2026-09'
ledger = root.parent / 'internal/inference-experiments-hy-embodied/runs/hy-025-openrouter-development/budget.jsonl'
count = sum(json.loads(s)['event'] == 'reserved' for s in ledger.read_text().splitlines())
relay = [str(root / '.venv/bin/python'), '-u', str(root / 'scripts/multibench/budget_responses_relay.py'),
    '--campaign-root', str(campaign), '--key-file', str(root.parent / '.env'),
    '--output', str(out), '--name', name, '--expected-calls', str(count),
    '--tool-name', 'semantic_goal', '--max-calls', '16', '--wall-limit-s', '2400', '--cap-usd', '1']
for ident in ('g05-sparse-sol-flex-dev-001-0', 'g05-sparse-sol-flex-dev-002-0', 'xr1-supervision-kettle-001-1'):
    relay.extend(['--acknowledge-failed-request', ident])
ssh = ['ssh', '-p', '53210', '-o', 'ConnectTimeout=15', 'root@92.180.27.84']
remote = '/root/physical-execution-lab'
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
        subprocess.run(ssh + ['umask 077; cat > ' + remote +
            '/configs/local/semantic-pi05-dev-001/relay-token'],
            input=(out / 'relay-token').read_bytes(), check=True)
        if tunnel.poll() is not None:
            raise RuntimeError('owned tunnel exited before episode')
        child = subprocess.Popen(ssh + [remote + '/.venv/bin/python -u ' + remote +
            '/runs/operator_semantic_matched_baseline001.py --condition task_plus_subtask --case-id ' +
            a.case_id + ' --worker-gpu ' + str(a.worker_gpu)], start_new_session=True)
        children.append(child)
        if child.wait(timeout=6000):
            raise RuntimeError('condition error retained; no automatic retry')
finally:
    for child in reversed(children):
        stop_child(child)
    (out / 'relay-token').unlink(missing_ok=True)
