import hashlib
import json
from pathlib import Path
import re
import sys

run = Path(sys.argv[1]).resolve()
manifest = Path(sys.argv[2])
assert run.is_relative_to(Path('/root/physical-execution-lab/runs'))
result = json.loads((run / 'episode/controller/result.json').read_text())
assert result['status'] in ('native_completed','incomplete','infrastructure_or_contract_error','budget_exhausted',
    'planner_stop_incomplete')
if result['status'] == 'planner_stop_incomplete':
    assert result['termination'] == 'semantic_abstention_not_native_success'
    assert result['metrics']['unresolved_policy_actions'] == 0
selected = []
for line in manifest.read_text().splitlines():
    expected, name = line.split('  ', 1)
    if not re.fullmatch(r'\./episode/native/[0-9a-f]{16,64}/observations/[0-9]{6}\.npz', name):
        continue
    path = (run / name).resolve()
    assert path.is_relative_to(run) and path.is_file()
    with path.open('rb') as f:
        hashed = hashlib.sha256()
        for chunk in iter(lambda:f.read(1024 * 1024), b''): hashed.update(chunk)
        assert hashed.hexdigest() == expected, str(path)
    selected.append((path,path.stat().st_size))
assert selected
# Delete only after every selected remote byte matches the verified local manifest.
for path, _ in selected: path.unlink()
record = {'run':str(run),'removed_redundant_native_sensor_files':len(selected),
    'reclaimed_bytes':sum(n for _,n in selected), 'verified_remote_hashes_before_delete':True,
    'verified_local_backup_manifest':manifest.name,
    'retained':'results, journal, action receipts, controller captures, audits, configs and qualification evidence'}
(run / 'native-payload-retirement.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
