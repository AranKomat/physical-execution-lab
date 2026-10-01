from __future__ import annotations
import random
from pathlib import Path
from .contracts import Case
from .errors import ValidationError
from .util import digest, atomic_json, read_json

DYNA_SUITES=['libero_goal_task','libero_goal_swap','libero_10_task','libero_10_swap']


def load_manifest(path):
    d=read_json(path)
    if d.get('version')!=1 or d.get('source') not in ('synthetic','native'):
        raise ValidationError('invalid_manifest_header')
    cases=[Case.from_dict(x) for x in d['cases']]
    if not cases or len({c.case_id for c in cases})!=len(cases):
        raise ValidationError('empty_or_duplicate_case_ids')
    if len({c.identity for c in cases})!=len(cases): raise ValidationError('duplicate_state_policy_trials')
    if any(c.split!=d['split'] for c in cases): raise ValidationError('mixed_splits')
    body={k:v for k,v in d.items() if k!='sha256'}
    if d.get('sha256')!=digest(body): raise ValidationError('manifest_hash_mismatch')
    return d,cases


def write_manifest(path,source,split,cases,notes='',catalog_sha256=None):
    d={'version':1,'source':source,'split':split,'notes':notes,
       'catalog_sha256':catalog_sha256,'cases':cases}
    d['sha256']=digest(d)
    atomic_json(Path(path),d)
    load_manifest(path)
    return d


def build_native_manifest(catalog,split,indices,task_ids=None,policy_repeats=1):
    from .util import integer
    if any(isinstance(i,bool) or not isinstance(i,int) or i<0 for i in indices):
        raise ValidationError('state_indices_must_be_nonnegative_integers')
    integer(policy_repeats,'policy_repeats',1,100)
    if catalog.get('sha256')!=digest({k:v for k,v in catalog.items() if k!='sha256'}):
        raise ValidationError('catalog_hash_mismatch')
    cases=[]
    for suite,tasks in sorted(catalog['states'].items()):
        for task,hashes in sorted(tasks.items(),key=lambda x:int(x[0])):
            if task_ids is not None and int(task) not in task_ids: continue
            for idx in indices:
                if idx>=len(hashes): raise ValidationError(f'{suite}/{task}: state {idx} missing')
                for seed in range(policy_repeats):
                    cases.append(dict(case_id=f'{suite}.t{task}.i{idx}.p{seed}',suite=suite,
                        task_id=int(task),state_index=idx,policy_seed=seed,split=split,
                        state_sha256=hashes[idx]))
    return cases


def assert_disjoint(dev,test):
    # Disjoint INITIAL STATES, regardless of a different policy seed or renamed case.
    def keys(d):
        return {(c['suite'],c['task_id'],c['state_sha256']) for c in d['cases']}
    overlap=keys(dev)&keys(test)
    if overlap: raise ValidationError(f'development_test_state_leakage:{len(overlap)}')


def split_manifest(path,shards):
    d,cases=load_manifest(path)
    if shards<1: raise ValidationError('shards must be positive')
    return [[c for i,c in enumerate(cases) if i%shards==s] for s in range(shards)]
