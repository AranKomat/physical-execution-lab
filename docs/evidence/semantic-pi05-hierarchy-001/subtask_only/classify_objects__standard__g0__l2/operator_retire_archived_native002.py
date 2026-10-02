"""Retire narrow remote sensor duplicates only against a verified local archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--verification', type=Path, required=True)
a = p.parse_args()
source = a.source.resolve()
assert source.is_relative_to(Path('/root/physical-execution-lab/runs'))
record = source / 'archived-native-retirement.json'
assert not record.exists()
manifest = json.loads(a.manifest.read_text())
verification = json.loads(a.verification.read_text())
assert Path(manifest['source']).resolve() == source
assert verification['source'] == manifest['source']
assert verification['archive_sha256'] == manifest['archive_sha256']
assert verification['verified_files'] == manifest['file_count'] == len(manifest['files'])
result = json.loads((source / 'episode/controller/result.json').read_text())
assert result['status'] in ('native_completed', 'planner_stop_incomplete')
assert result['metrics']['unresolved_policy_actions'] == 0
assert (source / 'offline-audit.json').is_file()

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()

selected = []
for name, expected in manifest['files'].items():
    if not re.fullmatch(r'episode/native/[0-9a-f]{16,64}/observations/[0-9]{6}\.npz', name):
        continue
    path = source / name
    assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(source)
    assert digest(path) == expected, name
    selected.append((path, name, expected, path.stat().st_size))
assert selected
retired = []
for path, name, expected, size in selected:
    assert digest(path) == expected, 'source changed after preflight'
    path.unlink()
    retired.append({'path': name, 'sha256': expected, 'bytes': size})
report = {'source': str(source), 'archive_sha256': manifest['archive_sha256'],
    'verified_local_archive_files': verification['verified_files'],
    'retired_native_sensor_files': len(retired),
    'bytes_freed': sum(row['bytes'] for row in retired), 'retired': retired,
    'scope': 'only duplicate native sensor NPZ; complete verified local archive retained',
    'retained_remote': 'results, journals, controller captures, policy proposals, audits and bindings'}
with record.open('x') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps({key: value for key, value in report.items() if key != 'retired'}))
