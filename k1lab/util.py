from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np
from .errors import ContractError


def plain(value):
    if isinstance(value, np.ndarray): return plain(value.tolist())
    if isinstance(value, np.generic): return plain(value.item())
    if isinstance(value, Path): return str(value)
    if isinstance(value, dict): return {str(k): plain(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [plain(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError('non-finite JSON value')
    return value


def canonical(value):
    return json.dumps(plain(value),sort_keys=True,separators=(',',':'),allow_nan=False)


def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def atomic_json(path,value,exclusive=False):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(plain(value),indent=2,sort_keys=True,allow_nan=False)+'\n'
    if exclusive:
        with path.open('x') as f: f.write(data)
        return
    temp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    temp.write_text(data); os.replace(temp,path)


def load_json(path):
    return json.loads(Path(path).read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ContractError(x)))


def vector(value,n,label='vector'):
    try: a=np.asarray(value,dtype=float)
    except (ValueError,TypeError) as e: raise ContractError(label) from e
    if a.shape!=(n,) or not np.isfinite(a).all(): raise ContractError(f'{label}: expected finite [{n}]')
    return a


def integer(v,lo,hi,label):
    if type(v) is not int or not lo<=v<=hi: raise ContractError(f'{label}: integer {lo}..{hi}')
    return v


def number(v,lo,hi,label):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
        raise ContractError(f'{label}: finite {lo}..{hi}')
    return float(v)


def keys(obj,allowed,required=()):
    if not isinstance(obj,dict): raise ContractError('expected object')
    extra=set(obj)-set(allowed); missing=set(required)-set(obj)
    if extra or missing: raise ContractError(f'unknown fields={sorted(extra)} missing={sorted(missing)}')


def text(value,label,maximum=1000):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:
        raise ContractError(f'invalid {label}')
    return value


def sha(value,label='sha256'):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
        raise ContractError(f'invalid {label}')
    return value


def array_sha(a):
    a=np.ascontiguousarray(a)
    return digest({'dtype':str(a.dtype),'shape':list(a.shape),'bytes':hashlib.sha256(a.tobytes()).hexdigest()})
