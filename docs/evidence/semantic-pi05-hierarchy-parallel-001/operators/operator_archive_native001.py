"""Pack terminal native evidence, or verify its complete compressed backup."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def sha(stream):
    value = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        value.update(chunk)
    return value.hexdigest()


p = argparse.ArgumentParser()
p.add_argument('mode', choices=('pack', 'verify'))
p.add_argument('--source', type=Path)
p.add_argument('--archive', type=Path, required=True)
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--verification', type=Path)
p.add_argument('--kind', choices=('native', 'vector'), default='native')
a = p.parse_args()
if a.mode == 'pack':
    source = a.source.resolve()
    assert not a.archive.exists() and not a.manifest.exists()
    assert not a.archive.resolve().is_relative_to(source)
    result = json.loads((source / ('report.json' if a.kind == 'vector' else 'episode/controller/result.json')).read_text())
    if a.kind == 'vector':
        assert result['status'] == 'native_terminal_wave'
    else:
        assert result['status'] in ('native_completed', 'planner_stop_incomplete')
        assert result['metrics']['unresolved_policy_actions'] == 0
    audit = json.loads((source / 'offline-audit.json').read_text())
    if a.kind == 'vector':
        assert audit['source_actions_match_journal'] and audit['H50_15_prefix_cadence']
    else:
        assert audit['source_npz_proposals_match_journal'] and audit['prefix_cadence_verified']
    paths = sorted(path for path in source.rglob('*') if path.is_file())
    assert all(not path.is_symlink() for path in paths)
    expected = {}
    for path in paths:
        with path.open('rb') as stream:
            expected[str(path.relative_to(source))] = sha(stream)
    with tarfile.open(a.archive, 'x:gz', compresslevel=1) as tar:
        for path in paths:
            tar.add(path, arcname=str(path.relative_to(source)), recursive=False)
    for path in paths:
        with path.open('rb') as stream:
            assert sha(stream) == expected[str(path.relative_to(source))], 'source changed during packing'
    with a.archive.open('rb') as stream:
        archive_hash = sha(stream)
    manifest = {'source': str(source), 'files': expected, 'archive_sha256': archive_hash,
        'compressed_bytes': a.archive.stat().st_size, 'terminal_status': result['status'],
        'native_steps': result['action_counts'] if a.kind == 'vector' else result['native_steps'], 'file_count': len(expected)}
    with a.manifest.open('x') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in manifest.items() if key != 'files'}))
else:
    manifest = json.loads(a.manifest.read_text())
    with a.archive.open('rb') as stream:
        assert sha(stream) == manifest['archive_sha256']
    seen = set()
    with tarfile.open(a.archive, 'r|gz') as tar:
        for member in tar:
            assert member.isfile(), 'refusing links, directories and special members'
            name = member.name
            assert name in manifest['files'] and name not in seen
            with tar.extractfile(member) as stream:
                assert sha(stream) == manifest['files'][name], name
            seen.add(name)
    assert seen == manifest['files'].keys()
    result = {'archive_sha256': manifest['archive_sha256'], 'verified_files': len(seen),
        'compressed_bytes': a.archive.stat().st_size,
        'verification': 'archive digest and every original per-file hash, no extraction',
        'source': manifest['source'], 'no_source_retirement': True}
    if a.verification:
        with a.verification.open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result))
