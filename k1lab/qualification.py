from pathlib import Path
from .util import load_json,file_sha,digest,sha
from .errors import ContractError,Unavailable


def config_identity(config):
    return digest({k:v for k,v in config.items() if k not in ('freeze_manifest_path','freeze_manifest_sha256')})


def verify_freeze(config,manifest):
    from .runner import source_hash
    if config.get('condition') != 'policy_only' and not config.get('model'):
        raise ContractError('formal freeze must bind a concrete model, not K1_MODEL')
    path=config.get('freeze_manifest_path')
    if not path or not Path(path).is_file():raise Unavailable('formal test needs a saved pre-evaluation freeze')
    if file_sha(path)!=config.get('freeze_manifest_sha256'):raise ContractError('freeze file changed')
    f=load_json(path)
    if f.get('source_sha256')!=source_hash() or f.get('manifest_sha256')!=manifest['sha256']:
        raise ContractError('code or task-state manifest changed after freeze')
    if f.get('configs',{}).get(config['condition'])!=config_identity(config):
        raise ContractError('condition config changed after freeze')
    if f.get('actor_memory_scope')!='current_episode_only':raise ContractError('freeze allows unsupported memory')


def verify_policy_qualification(config,spec):
    path=config.get('native_qualification_path')
    if not path or not Path(path).is_file():raise Unavailable('formal hybrid needs native policy qualification evidence')
    if file_sha(path)!=config.get('native_qualification_sha256'):raise ContractError('qualification file hash mismatch')
    q=load_json(path)
    required={'pixel_orientation','proprioception_units','action_sign_scale','reset_queue_isolation','one_policy_chunk'}
    if q.get('spec_sha256')!=spec.identity or not all(q.get('checks',{}).get(k) is True for k in required):
        raise ContractError('policy qualification missing required checks')
    # This is an operator-attested gate backed by native artifacts, not an independent safety certification.
    if not q.get('artifacts'):raise ContractError('qualification must reference measured artifacts')
    for entry in q['artifacts']:
        p=Path(path).parent/entry['path']
        if not p.is_file() or file_sha(p)!=entry['sha256']:raise ContractError('qualification artifact missing/changed')
