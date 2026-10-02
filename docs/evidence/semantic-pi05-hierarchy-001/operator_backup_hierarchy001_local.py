import json
import argparse
from pathlib import Path
import subprocess

root = Path('/Users/macbookpro/Developer/random/gpu/physical-execution-lab')
remote = '/root/physical-execution-lab'
p = argparse.ArgumentParser()
p.add_argument('--condition', choices=('motor_only', 'task_plus_subtask'), default='task_plus_subtask')
p.add_argument('--case-id', default='build_tower__standard__g0__l0')
p.add_argument('--cohort', choices=('semantic-pi05-hierarchy-001', 'semantic-pi05-hierarchy-parallel-001'), default='semantic-pi05-hierarchy-001')
a = p.parse_args()
condition = a.condition
relative = a.cohort + '/' + condition + '/' + a.case_id
source = remote + '/runs/' + relative
ssh = ['ssh', '-p', '53210', '-o', 'ConnectTimeout=15', 'root@92.180.27.84']
subprocess.run(['scp', '-P', '53210', str(root / 'runs/operator_harvest_hierarchy001.py'),
    'root@92.180.27.84:' + remote + '/runs/operator_harvest_hierarchy001.py'], check=True)
subprocess.run(ssh + [remote + '/.venv/bin/python ' + remote +
    '/runs/operator_harvest_hierarchy001.py --condition ' + condition + ' --case-id ' + a.case_id + ' --cohort ' + a.cohort], check=True)
target = root / 'runs/native-evidence' / relative
target.mkdir(parents=True, exist_ok=False)
manifest = target.parent / (target.name + '.sha256')
with manifest.open('xb') as stream:
    subprocess.run(ssh + ['cd ' + source + ' && find . -type f -print0 | sort -z | xargs -0 sha256sum'],
        stdout=stream, check=True)
subprocess.run(['rsync', '-az', '-e', 'ssh -p 53210 -o ConnectTimeout=15',
    'root@92.180.27.84:' + source + '/', str(target) + '/'], check=True)
with (target.parent / (target.name + '.verify.txt')).open('xb') as stream:
    subprocess.run(['shasum', '-a', '256', '--check', '../' + manifest.name],
        cwd=target, stdout=stream, check=True)
remote_manifest = remote + '/runs/' + a.cohort + '-' + condition + '-' + a.case_id + '.sha256'
subprocess.run(['scp', '-P', '53210', str(manifest),
    'root@92.180.27.84:' + remote_manifest], check=True)
retired = subprocess.run(ssh + [remote + '/.venv/bin/python ' + remote +
    '/runs/operator_retire_verified_native_payloads.py ' + source + ' ' + remote_manifest],
    capture_output=True, text=True, check=True)
(target.parent / (target.name + '.retirement.json')).write_text(retired.stdout)
print(json.dumps({'event': 'backup_verified', 'files': len(manifest.read_text().splitlines()),
    'local': str(target)}), flush=True)
