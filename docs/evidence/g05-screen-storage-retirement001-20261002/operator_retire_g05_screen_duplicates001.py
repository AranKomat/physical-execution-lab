"""Retire only remote native sensors already retained byte-for-byte locally."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

names = ('g05-screen-sort-l1', 'g05-screen-sort-l2', 'g05-screen-tower-l0', 'g05-screen-tower-l1')

def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--prepare-local', action='store_true')
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
if args.prepare_local:
    assert not args.apply
    root = Path('/Users/macbookpro/Developer/random/gpu/physical-execution-lab')
    records = []
    for name in names:
        source = root / 'runs/native-evidence' / name
        result = json.loads((source / 'controller/result.json').read_text())
        assert result['status'] == 'native_completed'
        files = {}
        for path in sorted(source.glob('native/*/observations/*.npz')):
            assert path.is_file() and not path.is_symlink()
            relative = path.relative_to(source).as_posix()
            assert re.fullmatch(r'native/[0-9a-f]{32}/observations/[0-9]{6}\.npz', relative)
            files[relative] = {'sha256': sha(path), 'bytes': path.stat().st_size}
        assert len(files) == result['native_steps'] + 1
        records.append({'name': name, 'result_sha256': sha(source / 'controller/result.json'), 'files': files})
    with (root / 'runs/g05-screen-duplicate-retirement001-manifest.json').open('x') as stream:
        json.dump({'scope': 'local full sensor copies verified before remote preflight', 'runs': records}, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'runs': len(records), 'files': sum(len(row['files']) for row in records)}))
else:
    root = Path('/root/physical-execution-lab')
    usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True)
    assert all(int(value) == 0 for value in usage.splitlines()), 'preserve active GPU work'
    manifest_path = root / 'runs/g05-screen-duplicate-retirement001-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert tuple(row['name'] for row in manifest['runs']) == names
    selected = []
    for row in manifest['runs']:
        source = root / 'runs' / row['name']
        assert sha(source / 'controller/result.json') == row['result_sha256']
        assert json.loads((source / 'controller/result.json').read_text())['status'] == 'native_completed'
        assert not (source / 'verified-duplicate-retirement001.json').exists()
        actual = {path.relative_to(source).as_posix() for path in source.glob('native/*/observations/*.npz')}
        assert actual == set(row['files']), 'require full exact remote sensor set'
        for relative, expected in row['files'].items():
            assert re.fullmatch(r'native/[0-9a-f]{32}/observations/[0-9]{6}\.npz', relative)
            path = source / relative
            assert not path.is_symlink() and path.resolve().is_relative_to(source.resolve())
            assert path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256']
            selected.append((path, expected))
    if args.apply:
        for path, expected in selected:
            assert sha(path) == expected['sha256'], 'changed since preflight'
            path.unlink()
        for row in manifest['runs']:
            record = {'manifest_sha256': sha(manifest_path), 'retired_files': len(row['files']),
                      'bytes_freed': sum(item['bytes'] for item in row['files'].values()),
                      'local_copy': 'runs/native-evidence/' + row['name'],
                      'retained': 'local full native sensors; remote controller captures, video, actions, scores and bindings'}
            with (root / 'runs' / row['name'] / 'verified-duplicate-retirement001.json').open('x') as stream:
                json.dump(record, stream, indent=2)
                stream.write('\n')
    print(json.dumps({'applied': args.apply, 'files': len(selected), 'bytes': sum(row['bytes'] for _, row in selected),
                      'manifest_sha256': sha(manifest_path)}))
