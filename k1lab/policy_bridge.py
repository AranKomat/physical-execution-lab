"""Local stateless policy bridge for an actually loaded RPent Pi05 facade.

Run in the *policy* environment. It never creates/steps a simulator. Implements
this repo's wire protocol, not an invented FLUX service API.
"""
from __future__ import annotations
import json
import time
from http.server import BaseHTTPRequestHandler,HTTPServer
import numpy as np
from .policy import unpack_array,validate_actions
from .errors import ContractError
from .util import digest,keys


def decode_observation(packet,spec):
    contract=packet.get('contract',{})
    if tuple(contract.get('cameras',()))!=spec.cameras or contract.get('state_dim')!=spec.state_dim or contract.get('observation_convention')!=spec.observation_convention:
        raise ContractError('observation contract differs from loaded policy')
    images=packet['images']
    if set(images)!=set(spec.cameras):raise ContractError('camera mismatch')
    views={name:unpack_array(images[name]) for name in spec.cameras}
    for v in views.values():
        if v.dtype!=np.uint8 or v.shape!=(256,256,3):raise ContractError('policy images must be RGB180 256x256 uint8')
    state=unpack_array(packet['state'])
    if state.shape!=(spec.state_dim,) or not np.isfinite(state).all():raise ContractError('invalid policy state')
    if not isinstance(packet.get('subgoal'),str) or not packet['subgoal'].strip():raise ContractError('empty subgoal')
    return {'main_images':views['agentview'][None], 'wrist_images':views['robot0_eye_in_hand'][None],
            'extra_view_images':None,'states':state[None],'task_descriptions':[packet['subgoal']]}


def handle(request,spec,facade):
    keys(request,{'request_id','request_sha256','spec_sha256','observation'},
         {'request_id','request_sha256','spec_sha256','observation'})
    copy=dict(request);h=copy.pop('request_sha256')
    if digest(copy)!=h or request['spec_sha256']!=spec.identity:raise ContractError('request/spec hash mismatch')
    obs=decode_observation(request['observation'],spec);start=time.monotonic()
    # Source-inspected RPent Pi05VLAFacade.predict returns [B,chunk,7].
    a=np.asarray(facade.predict(obs,{'mode':'eval'}))
    if a.ndim!=3 or a.shape[0]!=1:raise ContractError('unexpected RPent output batch')
    a=validate_actions(a[0],spec)
    return {'request_id':request['request_id'],'request_sha256':h,'spec_sha256':spec.identity,
            'actions':a.tolist(),'inference_seconds':time.monotonic()-start}


def serve(facade,spec,port=8811):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_GET(self):
            if self.path!='/health':self.send_error(404);return
            raw=json.dumps({'status':'ready','spec':spec.json(),'spec_sha256':spec.identity}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            if self.path!='/predict':self.send_error(404);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 1<=length<=8_000_000:raise ContractError('body size')
                self.connection.settimeout(120)
                request=json.loads(self.rfile.read(length));response=handle(request,spec,facade)
                code=200
            except Exception as exc:
                response={'error':type(exc).__name__+': '+str(exc)[:400]};code=400
            raw=json.dumps(response,allow_nan=False).encode()
            self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.end_headers();self.wfile.write(raw)
    # Single request at a time: no concurrent mutable model execution.
    server=HTTPServer(('127.0.0.1',port),Handler)
    try:server.serve_forever()
    finally:server.server_close()
