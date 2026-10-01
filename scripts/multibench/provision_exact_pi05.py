#!/usr/bin/env python3
"""Download only the exact published seed-0 RoboDojo pi0.5 inference assets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

REPO = 'RoboDojo-Benchmark/RoboDojo'
REVISION = '35efbc7dedfdbeeb6e95fb749bd885d73d483e41'
PREFIX = 'ckpt/RoboDojo/Pi_05/RoboDojo-sim-arx_x5-joint-0/59999'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--allow-network', action='store_true')
    args = parser.parse_args()
    if not args.allow_network:
        parser.error('explicit --allow-network required')
    from huggingface_hub import HfApi, snapshot_download
    destination = Path(args.destination).resolve()
    evidence = Path(args.evidence).resolve()
    if evidence.exists():
        raise FileExistsError('fresh evidence output required')
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for entry in HfApi().list_repo_tree(REPO, path_in_repo=PREFIX, recursive=True,
                                       repo_type='dataset', revision=REVISION):
        path = entry.path
        if (path.startswith(PREFIX + '/params/') or
                path.startswith(PREFIX + '/assets/') or
                path == PREFIX + '/_CHECKPOINT_METADATA') and hasattr(entry, 'size'):
            if entry.lfs is None or not entry.lfs.sha256:
                raise ValueError('publisher SHA-256 unavailable: ' + path)
            files.append((path, entry.size, entry.lfs.sha256))
    if not files or not any(p.endswith('/assets/arx_x5_sim/norm_stats.json') for p, _, _ in files):
        raise ValueError('exact checkpoint/normalizer incomplete')
    total = sum(size for _, size, _ in files)
    if shutil.disk_usage(destination).free < total + 5 * 1024**3:
        raise RuntimeError('insufficient disk headroom for selected inference files')
    print(json.dumps({'event': 'download_plan', 'revision': REVISION,
                      'files': len(files), 'bytes': total}), flush=True)
    snapshot_download(REPO, repo_type='dataset', revision=REVISION,
                      local_dir=str(destination), allow_patterns=[p for p, _, _ in files],
                      max_workers=4)
    verified = []
    for name, size, expected in files:
        path = destination / name
        checksum = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                checksum.update(block)
        actual = checksum.hexdigest()
        if path.stat().st_size != size or actual != expected:
            raise ValueError('published artifact hash mismatch: ' + name)
        verified.append({'path': name[len(PREFIX) + 1:], 'size': size, 'sha256': actual})
    record = {'repository': REPO, 'revision': REVISION, 'prefix': PREFIX,
              'checkpoint_path': str(destination / PREFIX), 'files': verified,
              'total_bytes': total, 'all_publisher_hashes_match': True,
              'qualification': 'Provisioning only; native load/inference/competence untested.'}
    evidence.parent.mkdir(parents=True, exist_ok=True)
    with evidence.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'event': 'checkpoint_verified', 'files': len(verified),
                      'checkpoint_path': record['checkpoint_path']}), flush=True)


if __name__ == '__main__':
    main()
