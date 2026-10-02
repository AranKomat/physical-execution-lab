"""New freezes cover semantic code as well as legacy code. Old approvals do not transfer."""
from pathlib import Path
import hashlib
from k1lab.errors import ContractError
from k1lab.util import digest, file_sha, load_json
from k1lab.multibench import manifest as mf

BASE_REVIEW_COMMIT = 'dc2e704064bc8e997f64d7978bb9714e995e65f2'
REVIEWED_BLOBS = {
    'k1lab/multibench/adapters/pi05.py': 'f8363f8b9bd2676779e0b24bd74c1f0c09119f16',
    'k1lab/multibench/adapters/xpolicylab.py': '68a334ba1a80fb756f45ac9dee80ff1b5aa5ace9',
    'k1lab/multibench/adapters/robocasa.py': '3ccadc36b31a6a387eaf27cda7ab9557f58bd51c',
    'k1lab/multibench/adapters/robodojo.py': '5486b2e975508d8ea90776db5b42824b65d173ce',
}


def git_blob(path):
    data = Path(path).read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def compatibility(root):
    root = Path(root)
    rows = {p: {'expected': h, 'actual': git_blob(root / p) if (root / p).is_file() else None}
            for p, h in REVIEWED_BLOBS.items()}
    return {'reviewed_commit': BASE_REVIEW_COMMIT, 'files': rows,
            'matches_reviewed_base': all(v['actual'] == v['expected'] for v in rows.values())}


def require_live_base(root):
    report = compatibility(root)
    if not report['matches_reviewed_base']:
        raise ContractError('native source differs from inspected base. Apply additive overlay to the live checkout/worktree, '
                            'not bundled v4. Review drift before updating semantic_lab.protocol.REVIEWED_BLOBS.')
    return report


def code_fingerprint(root):
    root = Path(root)
    paths = []
    for folder in ('k1lab', 'semantic_lab', 'scripts'):
        paths += list((root / folder).rglob('*.py'))
    paths += [root / 'run_semantic.py', root / 'run_bench.py', root / 'upstream.lock.json']
    return digest({p.relative_to(root).as_posix(): file_sha(p) for p in sorted(set(paths)) if p.is_file()})


def execution_snapshot(root, selectors):
    """Bind explicitly selected executor/native source trees, including membership."""
    root = Path(root).resolve()
    if (not isinstance(selectors, (list, tuple)) or not selectors
            or not all(isinstance(selector, str) and selector for selector in selectors)
            or len(set(selectors)) != len(selectors)):
        raise ContractError('nonempty unique execution source selectors required')
    files = {}
    suffixes = {'.py', '.json', '.yaml', '.yml', '.toml'}
    for selector in sorted(selectors):
        relative = Path(selector)
        if relative.is_absolute() or '..' in relative.parts or str(relative) == '.':
            raise ContractError('execution source selector must stay inside repository')
        path = root / relative
        linked = any(root.joinpath(*relative.parts[:index]).is_symlink()
                     for index in range(1, len(relative.parts) + 1))
        if linked or not path.resolve().is_relative_to(root) or not path.exists():
            raise ContractError('missing or unsafe execution source: ' + selector)
        candidates = [path] if path.is_file() else list(path.rglob('*'))
        selected = 0
        for candidate in sorted(candidates):
            if candidate.is_symlink():
                raise ContractError('execution source symlink: ' + str(candidate))
            if not candidate.is_file() or candidate.suffix not in suffixes:
                continue
            name = candidate.relative_to(root).as_posix()
            files[name] = file_sha(candidate)
            selected += 1
        if not selected:
            raise ContractError('execution source selector contains no source/config files: ' + selector)
    return mf.seal({'schema': 'semantic.execution_sources.v1', 'selectors': sorted(selectors),
                    'files': files, 'scope': 'selected project/native source and config bytes; not installed binary integrity'})


def freeze(root, manifest, configs, *, execution_sources=None):
    mf.check(manifest)
    if not configs or len({c['name'] for c in configs}) != len(configs):
        raise ContractError('unique nonempty conditions required')
    document = {'schema': 'semantic.freeze.v1', 'source_sha256': code_fingerprint(root),
                'manifest_sha256': manifest['sha256'], 'configs': {c['name']: digest(c) for c in configs},
                'native_review': compatibility(root), 'qualifies_hardware_or_models': False}
    if execution_sources is not None:
        document['execution_sources'] = execution_snapshot(root, execution_sources)
    return mf.seal(document)


def verify(root, frozen, manifest, config, qualification):
    mf.check(manifest)
    if frozen.get('schema') != 'semantic.freeze.v1' or frozen.get('sha256') != mf.seal(frozen)['sha256']:
        raise ContractError('invalid semantic freeze')
    if frozen['source_sha256'] != code_fingerprint(root) or frozen['manifest_sha256'] != manifest['sha256']:
        raise ContractError('source/manifest changed after semantic freeze')
    if frozen['configs'].get(config['name']) != digest(config):
        raise ContractError('semantic configuration is not frozen')
    if qualification.get('schema') != 'semantic.qualification.v1' or qualification.get('source_sha256') != frozen['source_sha256']:
        raise ContractError('new semantic qualification required; old motor-only approval does not transfer')
    if qualification.get('config_sha256') != digest(config):
        raise ContractError('qualification configuration changed')
    if 'execution_sources' in frozen:
        snapshot = frozen['execution_sources']
        if execution_snapshot(root, snapshot['selectors']) != snapshot:
            raise ContractError('execution source bytes or membership changed after freeze')
        if qualification.get('execution_sources_sha256') != snapshot['sha256']:
            raise ContractError('qualification does not bind frozen execution sources')
    required = ['native_motor_only_parity', 'effective_prompt_seen_at_model_boundary',
                'continue_preserves_cadence', 'context_switch_preserves_ack_history',
                'native_terminal_scoring_separate', 'source_bound_model_identity', 'tokenizer_subtask_not_truncated']
    if any(qualification.get('checks', {}).get(k) is not True for k in required):
        raise ContractError('semantic qualification incomplete')
    if not qualification.get('evidence'):
        raise ContractError('qualification requires native evidence')
    for row in qualification['evidence']:
        if file_sha(row['path']) != row['sha256']:
            raise ContractError('qualification evidence bytes changed')
    return True
