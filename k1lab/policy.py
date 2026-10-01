"""Frozen-policy wire protocol with explicit embodiment and action-space contracts.

FLUX DROID joint8 is deliberately not passed into LIBERO OSC7. The robot
sharing a Panda arm does not make its camera/action/normalization conventions match.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
import base64
import io
import time
import uuid
from urllib.parse import urlsplit
import numpy as np
import httpx
from .errors import ContractError,Unavailable,TransportUncertain
from .util import digest,sha,keys,vector,integer,number


@dataclass(frozen=True)
class PolicySpec:
    model_id: str
    checkpoint_sha256: str
    action_space: str
    control_hz: float
    cameras: tuple
    state_dim: int
    observation_convention: str
    adapter_revision: str
    max_chunk: int = 50
    def __post_init__(self):
        sha(self.checkpoint_sha256,'checkpoint manifest hash')
        if not self.model_id or not self.adapter_revision: raise ContractError('policy identity required')
        number(self.control_hz,1,1000,'control_hz'); integer(self.state_dim,1,100,'state_dim')
        integer(self.max_chunk,1,1000,'max_chunk')
    @classmethod
    def from_dict(cls,obj):
        keys(obj,cls.__dataclass_fields__,{'model_id','checkpoint_sha256','action_space','control_hz','cameras','state_dim','observation_convention','adapter_revision'})
        obj=dict(obj); obj['cameras']=tuple(obj['cameras']); return cls(**obj)
    def json(self): return asdict(self)
    @property
    def identity(self): return digest(self.json())
    def validate_port(self,port):
        if self.action_space!='libero_normalized_osc7':
            raise Unavailable(f'{self.action_space} has no qualified LIBERO action adapter; no implicit conversion')
        if self.action_space!=getattr(port,'action_space',None) or self.control_hz!=port.control_hz:
            raise ContractError('policy/control convention mismatch')
        expected=getattr(port,'policy_contract',{})
        if tuple(expected.get('cameras',()))!=self.cameras or expected.get('state_dim')!=self.state_dim or expected.get('observation_convention')!=self.observation_convention:
            raise ContractError('policy camera/state/observation mismatch')


def validate_actions(actions,spec):
    a=np.asarray(actions,dtype=np.float32)
    if a.ndim!=2 or a.shape[1]!=7 or not 1<=len(a)<=spec.max_chunk or not np.isfinite(a).all():
        raise ContractError('expected finite [chunk,7] action array')
    if np.max(np.abs(a))>1.000001: raise ContractError('normalized policy command outside [-1,1]; no silent clipping')
    return a


def pack_array(arr):
    a=np.ascontiguousarray(arr)
    if a.dtype not in (np.dtype('uint8'),np.dtype('float32')): raise ContractError('wire arrays use uint8/float32')
    if a.nbytes>8_000_000: raise ContractError('wire array too large')
    return {'dtype':a.dtype.str,'shape':list(a.shape),'data':base64.b64encode(a.tobytes()).decode()}


def unpack_array(value):
    keys(value,{'dtype','shape','data'},{'dtype','shape','data'})
    dtype=np.dtype(value['dtype'])
    if dtype not in (np.dtype('uint8'),np.dtype('float32')): raise ContractError('unsafe/unknown dtype')
    shape=value['shape']
    if not isinstance(shape,list) or not 1<=len(shape)<=4: raise ContractError('invalid shape')
    for d in shape: integer(d,1,10000,'dimension')
    if np.prod(shape,dtype=np.int64)*dtype.itemsize>8_000_000: raise ContractError('array too large')
    raw=base64.b64decode(value['data'],validate=True)
    if len(raw)!=int(np.prod(shape))*dtype.itemsize: raise ContractError('wire length mismatch')
    return np.frombuffer(raw,dtype=dtype).reshape(shape).copy()


class HTTPPolicy:
    def __init__(self,endpoint,spec,*,allow_network=False,timeout_s=120,client=None,journal=None):
        if not allow_network: raise Unavailable('policy network requires explicit --allow-policy')
        u=urlsplit(endpoint)
        if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.username or u.password:
            raise ContractError('policy bridge must be local loopback; use SSH forwarding for remote GPU')
        self.endpoint=endpoint.rstrip('/'); self.spec=spec; self.identity=spec.identity
        self.client=client or httpx.Client(timeout=timeout_s,trust_env=False,follow_redirects=False)
        self.journal=journal
    def validate_port(self,port): self.spec.validate_port(port)
    def reset_segment(self): pass  # stateless wire; no local action queue survives intervention
    def predict(self,packet):
        rid=uuid.uuid4().hex
        request={'request_id':rid,'spec_sha256':self.spec.identity,'observation':packet}
        request['request_sha256']=digest(request); t=time.monotonic()
        if self.journal:self.journal.append('policy_request',{'request_id':rid,'request_sha256':request['request_sha256'],'frame_id':packet['frame_id']})
        try:
            response=self.client.post(self.endpoint+'/predict',json=request)
            response.raise_for_status(); body=response.json()
        except Exception as e: raise TransportUncertain('policy call unresolved; no auto retry') from e
        if body.get('request_id')!=rid or body.get('request_sha256')!=request['request_sha256'] or body.get('spec_sha256')!=self.spec.identity:
            raise ContractError('policy response binding mismatch')
        if body.get('error'): raise Unavailable('policy bridge rejected request: '+str(body['error']))
        a=validate_actions(body['actions'],self.spec)
        if self.journal:self.journal.append('policy_response',{'request_id':rid,'latency_s':time.monotonic()-t,'native_prediction_count':len(a),'spec_sha256':self.spec.identity})
        return a
    def close(self): self.client.close()
