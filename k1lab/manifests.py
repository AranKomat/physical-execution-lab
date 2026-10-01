"""Disjoint task-condition splits, immutable state/BDDL fingerprints, full denominator."""
from __future__ import annotations
import random
from pathlib import Path
import numpy as np
from .errors import ContractError
from .util import digest,array_sha,file_sha,sha,integer,load_json


def base_task_key(suite,task_id):
    base=suite.removesuffix('_task').removesuffix('_swap')
    return f'{base}:{task_id}'


def seal(manifest):
    m=dict(manifest);m.pop('sha256',None);m['sha256']=digest(m);return m


def validate(manifest):
    m=dict(manifest); actual=m.pop('sha256',None)
    if digest(m)!=actual:raise ContractError('manifest hash mismatch')
    if m.get('format')!=1 or not isinstance(m.get('cases'),list) or not m['cases']:
        raise ContractError('empty/unknown manifest')
    seen=set();partitions={}
    for c in m['cases']:
        if c['id'] in seen:raise ContractError('duplicate case')
        seen.add(c['id'])
        if c['partition'] not in ('dev','test'):raise ContractError('bad partition')
        key=base_task_key(c['suite'],c['task_id'])
        if key in partitions and partitions[key]!=c['partition']:raise ContractError('task-condition leaks across dev/test')
        partitions[key]=c['partition']
        for field in ('state_sha256','state_file_sha256','bddl_sha256'):sha(c[field],field)
        integer(c['state_index'],0,10**7,'state index');integer(c['horizon'],1,10000,'horizon')
    return manifest


def state_sha(value):
    if hasattr(value,'detach'):value=value.detach().cpu().numpy()
    return array_sha(np.asarray(value))


def horizon(suite):
    if '_10' in suite:return 520
    if 'goal' in suite:return 300
    if 'object' in suite:return 280
    if 'spatial' in suite:return 220
    raise ContractError('unknown suite budget; specify and record an explicit profile')


def build_native(suites,indices,dev_fraction=0.25,seed=20261001):
    from robo_harness.libero_adapter import load_libero
    import torch
    benchmark,_=load_libero()
    from libero.libero import get_libero_path
    catalog=[]
    for suite_name in suites:
        suite=benchmark.get_benchmark_dict()[suite_name]()
        for task_id in range(suite.n_tasks):
            task=suite.get_task(task_id)
            state_path=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
            bddl=Path(suite.get_task_bddl_file_path(task_id))
            if not state_path.is_file() or not bddl.is_file():raise ContractError('missing trusted benchmark assets')
            states=torch.load(state_path,map_location='cpu',weights_only=False)
            selected=[]
            for i in indices:
                if not 0<=i<len(states):raise ContractError('state index absent; modulo reset forbidden')
                selected.append({'id':f'{suite_name}_t{task_id}_s{i}','suite':suite_name,'task_id':task_id,
                    'state_index':i,'state_sha256':state_sha(states[i]),'state_file_sha256':file_sha(state_path),
                    'bddl_sha256':file_sha(bddl),'horizon':horizon(suite_name)})
            catalog.append(selected)
    # Split entire task/perturbation conditions. This is not new object-family transfer.
    grouped={}
    for group in catalog:
        first=group[0]
        grouped.setdefault(base_task_key(first['suite'],first['task_id']),[]).extend(group)
    catalog=list(grouped.values())
    if len(catalog)<2:raise ContractError('need at least two base tasks for a held-out split')
    random.Random(seed).shuffle(catalog)
    dev_n=max(1,min(len(catalog)-1,round(len(catalog)*dev_fraction)))
    cases=[]
    for j,group in enumerate(catalog):
        for c in group:cases.append({**c,'partition':'dev' if j<dev_n else 'test'})
    return validate(seal({'format':1,'domain':'native_libero_pro','split_unit':'base_task_across_perturbations',
                          'seed':seed,'cases':cases,'memory_scope':'current_episode_only'}))


def check_case(adapter,case):
    from libero.libero import get_libero_path
    import torch
    task=adapter.task
    p=Path(get_libero_path('init_states'))/task.problem_folder/task.init_states_file
    b=Path(adapter.benchmark.get_task_bddl_file_path(case['task_id']))
    if file_sha(p)!=case['state_file_sha256'] or file_sha(b)!=case['bddl_sha256']:
        raise ContractError('benchmark file fingerprint changed')
    states=torch.load(p,map_location='cpu',weights_only=False)
    idx=case['state_index']
    if not 0<=idx<len(states) or state_sha(states[idx])!=case['state_sha256']:
        raise ContractError('state fingerprint mismatch')
