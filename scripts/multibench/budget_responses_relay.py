#!/usr/bin/env python3
"""Single-owner loopback Responses relay; credentials and shared ledger stay local."""
import argparse
import base64
import fcntl
from http.server import BaseHTTPRequestHandler,HTTPServer
import io
import json
from pathlib import Path
import secrets
import sys
import time
from decimal import Decimal

import httpx
from PIL import Image

MODEL='openai/gpt-6.1-sol'
PROVIDER={'only':['openai/flex'],'allow_fallbacks':False,'require_parameters':True,
    'max_price':{'prompt':1.5,'completion':6}}


def request_bound(body):
    if body.get('model')!='gpt-6.1-sol' or body.get('service_tier')!='flex':
        raise ValueError('only explicitly selected Sol 6.1 Flex is allowed')
    if body.get('reasoning')!={'effort':'medium'} or body.get('store') is not False:
        raise ValueError('medium reasoning and store=false required')
    if body.get('max_output_tokens')!=2048 or body.get('parallel_tool_calls') is not False:
        raise ValueError('unexpected output/tool budget')
    if len(body.get('tools',[]))!=1 or body['tools'][0].get('name')!='robot_decision':
        raise ValueError('only the local robot_decision function is allowed')
    copy=json.loads(json.dumps(body));images=0
    for message in copy['input']:
        content=message.get('content')
        if not isinstance(content,list):continue
        for block in content:
            if block.get('type')!='input_image':continue
            uri=block['image_url']
            if not uri.startswith('data:image/jpeg;base64,'):
                raise ValueError('only inline JPEG sensor previews are allowed')
            data=base64.b64decode(uri.split(',',1)[1],validate=True)
            with Image.open(io.BytesIO(data)) as image:
                if image.format!='JPEG' or max(image.size)>480:
                    raise ValueError('image exceeds the qualified preview bound')
            block['image_url']='[image omitted for text bound]';images+=1
    if images>6:raise ValueError('at most six current/historical camera previews')
    # UTF-8 bytes conservatively bound text; each <=480px image reserves 4096 tokens.
    tokens=len(json.dumps(copy,ensure_ascii=False).encode())+4096*images+2048
    if tokens>100000:raise ValueError('request exceeds conservative context bound')
    amount=Decimal(tokens)*Decimal('0.0000015')+Decimal(2048)*Decimal('0.000006')
    return amount


class Relay:
    def __init__(self,ledger,key,token,output,name,max_calls,cap,http):
        self.ledger=ledger;self.key=key;self.token=token;self.output=output
        self.name=name;self.max_calls=max_calls;self.cap=cap;self.http=http
        self.attempts=0;self.spent=Decimal(0);self.unresolved=False

    def forward(self,body):
        reserve=request_bound(body)
        if self.unresolved or self.attempts>=self.max_calls or self.spent+reserve>self.cap:
            raise ValueError('trial budget exhausted or unresolved request; no retry')
        ident=f'{self.name}-{self.attempts}'
        self.ledger.reserve(ident,MODEL,reserve)
        self.attempts+=1;self.unresolved=True
        wire=dict(body,model=MODEL,provider=PROVIDER)
        # This provider does not advertise parallel_tool_calls. The recipient
        # still rejects anything except one robot_decision function call.
        wire.pop('parallel_tool_calls')
        root=self.output/ident;root.mkdir()
        (root/'request.json').write_text(json.dumps(wire))
        try:
            response=self.http.post('https://openrouter.ai/api/v1/responses',json=wire,
                headers={'Authorization':'Bearer '+self.key})
            (root/'response.json').write_bytes(response.content)
            if response.status_code!=200:raise RuntimeError(f'provider HTTP {response.status_code}; audit retained')
            raw=response.json();cost=(raw.get('usage') or {}).get('cost')
            if raw.get('status')!='completed' and cost is None:
                detail=(raw.get('error') or {}).get('message','incomplete response')
                raise RuntimeError('provider failed without usage; reservation retained: '+detail)
            if cost is None:raise RuntimeError('missing actual cost; reservation retained')
            self.ledger.settle(ident,cost);self.spent+=Decimal(str(cost))
            if raw.get('status')!='completed' or raw.get('service_tier')!='flex':
                raise RuntimeError('response incomplete or served tier not flex; no further requests')
            if raw.get('model') not in ('gpt-6.1-sol',MODEL):
                raise RuntimeError('served model mismatch; no further requests')
            self.unresolved=False
            (self.output/'summary.json').write_text(json.dumps({
                'attempts':self.attempts,'cost_usd':str(self.spent),'no_automatic_retry':True,
                'requested_model':MODEL,'provider':PROVIDER,'service_tier':'flex'},indent=2))
            return raw
        finally:self.ledger.finish_attempt(ident)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('campaign-root','key-file','output','name'):p.add_argument('--'+name,required=True)
    p.add_argument('--port',type=int,default=19861);p.add_argument('--expected-calls',type=int,required=True)
    p.add_argument('--max-calls',type=int,default=75);p.add_argument('--cap-usd',type=Decimal,default=Decimal(3))
    p.add_argument('--acknowledge-failed-request',action='append',default=[])
    p.add_argument('--offline-request',help='One retained legal request for route qualification only; no motion')
    a=p.parse_args()
    if not 1<=a.max_calls<=75 or not 0<a.cap_usd<=3 or '/' in a.name:raise ValueError('invalid trial scope')
    sys.path.insert(0,a.campaign_root)
    from openrouter_pilot import Ledger,RUN,load_key
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    token=secrets.token_urlsafe(32);path=out/'relay-token';path.write_text(token);path.chmod(0o600)
    with (RUN/'runner.lock').open('a') as lock,httpx.Client(timeout=900,trust_env=False) as http:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ledger=Ledger(RUN/'budget.jsonl',max_calls=4209,limit_usd=Decimal(85),
            resumed_at=time.time(),wall_limit_seconds=2400,
            acknowledged_unknown_ids=a.acknowledge_failed_request)
        count=sum(e['event']=='reserved' for e in ledger.read())
        if count!=a.expected_calls:raise ValueError('shared call count changed; inspect ledger')
        ledger.max_calls=count+a.max_calls
        ledger.append({'event':'operator_robodojo_supervision_scope','time':time.time(),
            'name':a.name,'max_calls':ledger.max_calls,'local_cap_usd':str(a.cap_usd),
            'shared_cap_usd':'85','model':MODEL,'provider':'openai/flex',
            'authorization':'standing low-budget approval; owner selected Sol 6.1 Flex'})
        relay=Relay(ledger,load_key(a.key_file),token,out,a.name,a.max_calls,a.cap_usd,http)
        if a.offline_request:
            if a.max_calls!=1:raise ValueError('offline qualification requires exactly one call')
            body=json.loads(Path(a.offline_request).read_text())
            body['model']='gpt-6.1-sol';body.pop('provider',None)
            body['parallel_tool_calls']=False
            raw=relay.forward(body)
            print(json.dumps({'event':'offline_route_qualified','model':raw['model'],
                'service_tier':raw['service_tier'],'output_types':[x['type'] for x in raw.get('output',[])]}),flush=True)
            return

        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                status=200
                try:
                    if self.path!='/responses' or not secrets.compare_digest(
                        self.headers.get('Authorization',''),'Bearer '+token):
                        raise ValueError('invalid relay endpoint or authorization')
                    size=int(self.headers.get('Content-Length','0'))
                    if not 0<size<=12000000:raise ValueError('request byte cap')
                    result=relay.forward(json.loads(self.rfile.read(size)))
                except Exception as exc:
                    status=503;result={'error':{'message':str(exc),'retry':False}}
                    print(json.dumps({'event':'relay_rejected','type':type(exc).__name__,'detail':str(exc)}),flush=True)
                data=json.dumps(result).encode();self.send_response(status)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)))
                self.end_headers();self.wfile.write(data)

        print(json.dumps({'event':'relay_ready','port':a.port,'max_calls':a.max_calls,
            'local_cap_usd':str(a.cap_usd),'shared_cap_usd':'85'}),flush=True)
        HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()


if __name__=='__main__':main()
