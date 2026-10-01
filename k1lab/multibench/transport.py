"""Separate policy Python/CUDA environments via a loopback-only service.

Exactly one owner token, request hash binding, no automatic retries/reconnections.
HTTP localhost is not a security boundary: deploy only on a trusted machine or
an authenticated SSH tunnel; do not expose this server on a public interface.
"""
from __future__ import annotations
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler,HTTPServer
from urllib.parse import urlsplit
import json
import secrets
import time
import numpy as np
import httpx
from k1lab.errors import ContractError,TransportUncertain,Unavailable
from k1lab.util import digest,plain
from k1lab.policy import pack_array,unpack_array
from .types import Observation,Action,Proposal,PolicyIdentity


def encode_obs(obs):
    return {'episode':obs.episode,'step':obs.step,'instruction':obs.instruction,
            'rgb':{k:pack_array(a) for k,a in obs.rgb.items()},'state':pack_array(obs.state),
            'eef':obs.eef,'control_hz':obs.control_hz,'signals':obs.actor_state()['sensor_signals']}


def decode_obs(data):
    allowed={'episode','step','instruction','rgb','state','eef','control_hz','signals'}
    if set(data)!=allowed:raise ContractError('unknown observation fields')
    return Observation(data['episode'],data['step'],data['instruction'],
        {k:unpack_array(v) for k,v in data['rgb'].items()},unpack_array(data['state']),
        data['eef'],data['control_hz'],data['signals'])


class RemotePolicy:
    def __init__(self,config,*,allow_policy=False,client=None):
        if not allow_policy:raise Unavailable('policy transport requires --allow-policy')
        self.identity=PolicyIdentity(**config['identity']);self.config=config
        url=urlsplit(config['endpoint'])
        if url.scheme!='http' or url.hostname not in ('localhost','127.0.0.1','::1') or url.username or url.password or url.query or url.fragment:
            raise ContractError('policy endpoint must be local loopback; tunnel explicitly')
        self.endpoint=config['endpoint'].rstrip('/');self.owner=secrets.token_hex(16);self.seq=0;self.poisoned=False
        self.client=client or httpx.Client(timeout=config.get('timeout_s',300),trust_env=False,follow_redirects=False)
        ready=self._call('acquire',{})
        if ready['identity']!=self.identity.identity:raise ContractError('policy server identity differs')
        self.server_info=ready
    def _call(self,op,args):
        if self.poisoned:raise TransportUncertain('policy session poisoned')
        request={'owner':self.owner,'seq':self.seq,'op':op,'args':args};h=digest(request)
        try:
            response=self.client.post(self.endpoint+'/rpc',json={'request':request,'request_sha256':h})
            response.raise_for_status();body=response.json()
            if body.get('request_sha256')!=h or body.get('error'):
                raise ContractError(body.get('error','response binding mismatch'))
            self.seq+=1;return body['result']
        except Exception as e:
            self.poisoned=True;raise TransportUncertain(f'policy {op} unresolved: no retry') from e
    def reset(self):self._call('reset',{})
    def observe(self,obs):self._call('observe',{'observation':encode_obs(obs)})
    def invalidate(self,reason):self._call('invalidate',{'reason':reason})
    def propose(self,obs):
        data=self._call('propose',{'observation':encode_obs(obs)})
        return Proposal(data['observation_sha256'],data['step'],data['policy_identity'],
                        [Action(a['space'],a['values']) for a in data['actions']],data.get('diagnostics',{}))
    def synchronize(self):self._call('synchronize',{})
    def memory(self):return self._call('memory',{})
    def close(self):
        if not self.poisoned:
            try:self._call('release',{})
            except Exception:pass
        self.client.close()


class PolicyDispatcher:
    def __init__(self,policy,load_seconds=None):
        self.policy=policy;self.owner=None;self.seq=0;self.poisoned=False;self.load_seconds=load_seconds
        from .fingerprint import capture
        self.runtime_fingerprint=capture()
    def dispatch(self,envelope):
        request=envelope['request'];h=digest(request)
        if h!=envelope['request_sha256']:raise ContractError('request digest mismatch')
        op=request['op'];owner=request['owner'];seq=request['seq'];args=request['args']
        if self.poisoned:raise ContractError('server state uncertain; restart process')
        if op=='acquire':
            if self.owner is not None or seq!=0:raise ContractError('policy already owned')
            self.owner=owner;self.seq=1
            return {'request_sha256':h,'result':{'identity':self.policy.identity.identity,
                    'policy':asdict(self.policy.identity),'load_seconds':self.load_seconds,'runtime_fingerprint':self.runtime_fingerprint}}
        if owner!=self.owner or seq!=self.seq:raise ContractError('owner/sequence mismatch; no replay')
        try:
            if op=='reset':self.policy.reset();result={'reset':True}
            elif op=='observe':self.policy.observe(decode_obs(args['observation']));result={'ack':True}
            elif op=='invalidate':self.policy.invalidate(args['reason']);result={'invalidated':True}
            elif op=='propose':
                p=self.policy.propose(decode_obs(args['observation']))
                result={'observation_sha256':p.observation_sha256,'step':p.step,'policy_identity':p.policy_identity,
                        'actions':[a.json() for a in p.actions],'diagnostics':p.diagnostics}
            elif op=='synchronize':self.policy.synchronize();result={}
            elif op=='memory':result=self.policy.memory()
            elif op=='release':self.policy.reset();self.owner=None;result={'released':True}
            else:raise ContractError('unsupported operation')
            self.seq+=1
            return {'request_sha256':h,'result':plain(result)}
        except Exception:
            self.poisoned=True;raise


def serve(policy,port,load_seconds=None):
    state=PolicyDispatcher(policy,load_seconds)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path!='/rpc':self.send_error(404);return
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=24_000_000:raise ContractError('request length bound')
                request=json.loads(self.rfile.read(n));body=state.dispatch(request);code=200
            except Exception as exc:
                body={'error':type(exc).__name__+': '+str(exc)[:400]};code=409
            data=json.dumps(plain(body),allow_nan=False).encode()
            self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def log_message(self,*_):pass
    # Single threaded server: no concurrent mutation/model calls.
    with HTTPServer(('127.0.0.1',int(port)),Handler) as server:
        print(json.dumps({'ready':True,'port':port,'identity':policy.identity.identity}),flush=True)
        try:server.serve_forever()
        finally:policy.close()
