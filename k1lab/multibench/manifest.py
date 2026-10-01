"""Case manifests, artifact hashes and preregistration; never infer missing states."""
from __future__ import annotations
from pathlib import Path
import random
from k1lab.util import digest,load_json,file_sha,atomic_json
from k1lab.errors import ContractError


def seal(data):
    d=dict(data);d.pop('sha256',None);return d|{'sha256':digest(d)}


def check(manifest):
    raw={k:v for k,v in manifest.items() if k!='sha256'}
    if digest(raw)!=manifest.get('sha256'):raise ContractError('manifest hash mismatch')
    cases=manifest.get('cases',[])
    if not cases:raise ContractError('empty manifest')
    ids=set();groups={}
    for c in cases:
        for key in ('case_id','task','benchmark','partition','task_group'):
            if not isinstance(c.get(key),str) or not c[key]:raise ContractError('case missing '+key)
        if c['case_id'] in ids:raise ContractError('duplicate case')
        ids.add(c['case_id'])
        if c['partition'] not in ('dev','test'):raise ContractError('invalid partition')
        key=(c['benchmark'],c['task_group'])
        if key in groups and groups[key]!=c['partition']:raise ContractError('task family crosses development/test')
        groups[key]=c['partition']
        if c['benchmark']=='robodojo':
            for k in ('eval_seed','layout_id'):
                if type(c.get(k)) is not int or c[k]<0:raise ContractError('RoboDojo needs explicit '+k)
            if manifest.get('formal') and not c.get('layout_sha256'):raise ContractError('formal RoboDojo cases need layout hashes')
        elif c['benchmark']=='robocasa365':
            if c.get('split') not in ('pretrain','target','all'):raise ContractError('explicit kitchen split required')
            if c['episode_seed']!=c['environment_seed']+c['global_episode_index']:
                raise ContractError('RoboCasa official global episode seed formula changed')
    return manifest


def group_split(cases,seed=20261001,dev_fraction=.25):
    groups=sorted(set(c['task_group'] for c in cases));random.Random(seed).shuffle(groups)
    n=max(1,min(len(groups)-1,round(len(groups)*dev_fraction))) if len(groups)>1 else 1
    dev=set(groups[:n])
    return [dict(c,partition='dev' if c['task_group'] in dev else 'test') for c in cases]


def robocasa_cases(tasks,horizons,trials=50,base_seed=7,split='pretrain',categories=None):
    if trials<1 or len(tasks)!=len(set(tasks)):raise ContractError('invalid task/trial roster')
    rows=[]
    for i,task in enumerate(tasks):
        for trial in range(trials):
            global_index=i*trials+trial
            rows.append({'case_id':f'{task}__e{trial:03d}','benchmark':'robocasa365','task':task,
                  'task_group':task,'horizon':int(horizons[task]),'split':split,
                  'category':(categories or {}).get(task,'unmapped'),
                  'environment_seed':base_seed,'episode_seed':base_seed+global_index,
                  'task_index':i,'global_episode_index':global_index,'trial':trial})
    return check(seal({'schema':'multibench.manifest.v1','formal':False,'task_set':'target50',
                       'trials_per_task':trials,'cases':group_split(rows),
                       'note':'Registry task order is preserved. pretrain kitchen split differs from held-out task categories.'}))


def artifacts(root):
    root=Path(root).resolve()
    files={str(p.relative_to(root)):file_sha(p) for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()}
    if not files:raise ContractError('artifact directory is empty')
    return seal({'schema':'multibench.artifacts.v1','root':str(root),'files':files,
                 'scope':'All regular files under supplied root. Include weights, processors and normalization.'})


def verify_artifacts(manifest):
    raw={k:v for k,v in manifest.items() if k!='sha256'}
    if digest(raw)!=manifest.get('sha256') or not manifest.get('files'):raise ContractError('artifact manifest corrupted')
    root=Path(manifest['root']).resolve()
    for rel,h in manifest['files'].items():
        p=(root/rel).resolve()
        if not p.is_relative_to(root) or not p.is_file() or file_sha(p)!=h:
            raise ContractError('artifact bytes changed: '+rel)
    return digest(manifest['files']) # content identity independent of installation path


def resolved_config(config):
    from copy import deepcopy
    c=deepcopy(config)
    if c.get('no_task_memory') is False or c.get('no_task_demonstrations') is False:
        raise ContractError('main protocol excludes target-task memory/demonstrations')
    if any(c.get(k) for k in ('task_memory','exploration_memory','oracle_geometry','task_skill_library')):
        raise ContractError('forbidden main-protocol context or skill source')
    p=c.get('policy')
    if p:
        manifest=load_json(p['artifact_manifest']);h=verify_artifacts(manifest)
        old=p['identity'].get('checkpoint_sha256')
        if old is not None and old!=h:raise ContractError('configured checkpoint identity changed')
        p['identity']['checkpoint_sha256']=h
        if p['backend']=='remote':
            if not p['identity'].get('adapter_config_sha256'):
                raise ContractError('bind remote identity to resolved provider config with scripts/multibench/bind_policy.py')
        else:
            runtime={k:v for k,v in p.items() if k not in ('identity','artifact_manifest','artifact_dir')}
            expected=digest(runtime)
            previous=p['identity'].get('adapter_config_sha256')
            if previous is not None and previous!=expected:raise ContractError('provider configuration changed after binding')
            p['identity']['adapter_config_sha256']=expected
    return c


def code_fingerprint(root):
    root=Path(root)
    paths=list((root/'k1lab').rglob('*.py'))+list((root/'scripts').rglob('*.py'))+[root/'run_bench.py',root/'upstream.lock.json']
    return digest({str(p.relative_to(root)):file_sha(p) for p in sorted(paths) if p.is_file()})


def freeze(root,manifest,configs):
    check(manifest)
    if not configs or len({c['name'] for c in configs})!=len(configs):raise ContractError('nonempty unique config names required')
    return seal({'schema':'multibench.freeze.v1','code_sha256':code_fingerprint(root),
                 'manifest_sha256':manifest['sha256'],'configs':{c['name']:digest(c) for c in configs},
                 'protocol':'No target-task solutions/demonstrations; current-episode context allowed.',
                 'evidence':'Freeze is preregistration/integrity, NOT proof of real-world safety or generalization.'})


def verify_freeze(root,freeze_doc,manifest,config):
    raw={k:v for k,v in freeze_doc.items() if k!='sha256'}
    if digest(raw)!=freeze_doc.get('sha256') or freeze_doc['code_sha256']!=code_fingerprint(root):raise ContractError('source/freeze changed')
    if freeze_doc['manifest_sha256']!=manifest['sha256'] or freeze_doc['configs'].get(config['name'])!=digest(config):raise ContractError('test configuration not frozen')


def import_robodojo(public_results,source_panel=None):
    """Copy case identities only; published successes/trajectories never enter actor inputs."""
    data=load_json(public_results);unique={}
    for r in data['cases']:
        c={'case_id':r['case_id'],'benchmark':'robodojo','task':r['task'],
           'runtime_task':r['task']+('_random' if r['variant']=='random' else ''),
           'task_group':r['task'],'variant':r['variant'],'eval_seed':r['seeds']['eval_seed'],
           'layout_id':r['seeds']['layout_id'],'horizon':r['limit'],'native_hz':1/r['dt']}
        if c['case_id'] in unique and unique[c['case_id']]!=c:
            raise ContractError('published methods disagree about selected case identity')
        unique[c['case_id']]=c
    if source_panel:
        panel=load_json(source_panel)
        mapping={r['case_id']:r for r in panel['cases']}
        for cid,c in unique.items():
            if cid not in mapping:raise ContractError('case missing from source frozen panel')
            original=mapping[cid]
            for field in ('task','runtime_task','variant','eval_seed','layout_id'):
                if field in original and original[field]!=c[field]:raise ContractError('source panel disagrees on '+field)
            layout=original.get('layout',{})
            if not layout.get('sha256'):raise ContractError('source panel lacks concrete layout hash')
            c.update(layout_sha256=layout['sha256'],layout_path=layout['path'],source_case=original)
    return check(seal({'schema':'multibench.manifest.v1','formal':bool(source_panel),
         'source_case_file_sha256':file_sha(public_results),
         'source_panel_sha256':file_sha(source_panel) if source_panel else None,
         'cases':group_split(list(unique.values())),
         'training_examples_loaded':False,'reference_scores_loaded_into_actor':False}))


def verify_qualification(document,config):
    if document.get('config_sha256')!=digest(config):raise ContractError('qualification does not bind this resolved config')
    required=('native_reset_render','action_space_verified','native_completion_not_vacuous',
              'current_sensor_only_actor','policy_observation_ack_verified','controller_timing_verified')
    if any(document.get('checks',{}).get(k) is not True for k in required):raise ContractError('native qualification incomplete')
    evidence=document.get('evidence',[])
    if not evidence:raise ContractError('qualification needs hashed native evidence artifacts')
    for row in evidence:
        if file_sha(row['path'])!=row['sha256']:raise ContractError('qualification evidence changed')
    return document
