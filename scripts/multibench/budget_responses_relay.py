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
STANDARD_PROVIDER={'only':['openai'],'allow_fallbacks':False,'require_parameters':True,
    'max_price':{'prompt':3,'completion':12}}


class FlexCapacityError(RuntimeError):
    def __init__(self, ident, reserve):
        super().__init__('explicit Flex capacity rejection; reservation retained')
        self.ident, self.reserve = ident, reserve


def explicit_flex_capacity(raw):
    error = raw.get('error') or {}
    return (raw.get('status') == 'failed' and not raw.get('output')
        and raw.get('usage') is None
        and raw.get('model') in ('gpt-6.1-sol', MODEL)
        and error.get('code') in ('server_error', 'resource_unavailable')
        and str(error.get('message', '')).startswith('Flex processing is temporarily unavailable.'))


def trial_limits(profile,max_calls,cap,wall_limit_s):
    ceiling={'pilot75':75,'comparison180':180,'full_panel1800':1800}.get(profile)
    if ceiling is None or not 1<=max_calls<=ceiling or not 0<cap<=3:
        raise ValueError('invalid trial scope')
    if not 0<wall_limit_s<=(3600 if profile in ('comparison180','full_panel1800') else 2400):
        raise ValueError('invalid trial wall limit')


def request_bound(body, tool_name='robot_decision', billing_tier='flex'):
    if tool_name not in ('robot_decision', 'semantic_goal'):
        raise ValueError('unreviewed function contract')
    if body.get('model')!='gpt-6.1-sol' or body.get('service_tier')!='flex':
        raise ValueError('only explicitly selected Sol 6.1 Flex is allowed')
    if body.get('reasoning')!={'effort':'medium'} or body.get('store') is not False:
        raise ValueError('medium reasoning and store=false required')
    if body.get('max_output_tokens')!=2048 or body.get('parallel_tool_calls') is not False:
        raise ValueError('unexpected output/tool budget')
    if (len(body.get('tools',[]))!=1 or body['tools'][0].get('type')!='function'
            or body['tools'][0].get('name')!=tool_name):
        raise ValueError('only the explicitly selected '+tool_name+' function is allowed')
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
    if billing_tier not in ('flex','default'):
        raise ValueError('unreviewed billing tier')
    multiplier=1 if billing_tier=='flex' else 2
    amount=(Decimal(tokens)*Decimal('0.0000015')+Decimal(2048)*Decimal('0.000006'))*multiplier
    return amount


class Relay:
    def __init__(self,ledger,key,token,output,name,max_calls,cap,http,tool_name='robot_decision',
                 allow_standard_fallback=False):
        self.ledger=ledger;self.key=key;self.token=token;self.output=output
        self.name=name;self.max_calls=max_calls;self.cap=cap;self.http=http
        self.attempts=0;self.spent=Decimal(0);self.unresolved=False
        self.allow_standard_fallback=allow_standard_fallback
        self.standard_active=False;self.capacity_holds={};self.held=Decimal(0)
        if tool_name not in ('robot_decision','semantic_goal'):
            raise ValueError('unreviewed function contract')
        self.tool_name=tool_name

    def forward(self,body):
        tier='default' if self.standard_active else 'flex'
        try:
            return self._attempt(body,tier)
        except FlexCapacityError as exc:
            if not self.allow_standard_fallback:
                raise
            # Only a recognized no-output capacity rejection can cross tiers.
            # Never release its hold, or replay any robot action.
            self.capacity_holds[exc.ident]=str(exc.reserve);self.held+=exc.reserve
            self.ledger.acknowledged_unknown_ids=frozenset(
                getattr(self.ledger,'acknowledged_unknown_ids',())) | {exc.ident}
            self.ledger.append({'event':'operator_same_model_standard_fallback','time':time.time(),
                'failed_flex_id':exc.ident,'hold_retained_usd':str(exc.reserve),
                'model':MODEL,'service_tier':'default',
                'authorization':'owner permits regular version whenever Flex is unavailable'})
            self.unresolved=False;self.standard_active=True
            return self._attempt(body,'default')

    def _attempt(self,body,tier):
        reserve=request_bound(body,self.tool_name,tier)
        if self.unresolved or self.attempts>=self.max_calls or self.spent+self.held+reserve>self.cap:
            raise ValueError('trial budget exhausted or unresolved request; no retry')
        ident=f'{self.name}-{self.attempts}'
        self.ledger.reserve(ident,MODEL,reserve)
        self.attempts+=1;self.unresolved=True
        provider=STANDARD_PROVIDER if tier=='default' else PROVIDER
        wire=dict(body,model=MODEL,provider=provider,service_tier=tier)
        # This provider does not advertise parallel_tool_calls. The recipient
        # still rejects anything except one explicitly selected function call.
        wire.pop('parallel_tool_calls')
        root=self.output/ident;root.mkdir()
        (root/'request.json').write_text(json.dumps(wire))
        try:
            response=self.http.post('https://openrouter.ai/api/v1/responses',json=wire,
                headers={'Authorization':'Bearer '+self.key})
            (root/'response.json').write_bytes(response.content)
            raw=response.json()
            if tier=='flex' and self.allow_standard_fallback and explicit_flex_capacity(raw):
                raise FlexCapacityError(ident,reserve)
            if response.status_code!=200:raise RuntimeError(f'provider HTTP {response.status_code}; audit retained')
            cost=(raw.get('usage') or {}).get('cost')
            if raw.get('status')!='completed' and cost is None:
                detail=(raw.get('error') or {}).get('message','incomplete response')
                raise RuntimeError('provider failed without usage; reservation retained: '+detail)
            if cost is None:raise RuntimeError('missing actual cost; reservation retained')
            self.ledger.settle(ident,cost);self.spent+=Decimal(str(cost))
            if raw.get('status')!='completed' or raw.get('service_tier')!=tier:
                raise RuntimeError('response incomplete or served tier mismatch; no further requests')
            if raw.get('model') not in ('gpt-6.1-sol',MODEL):
                raise RuntimeError('served model mismatch; no further requests')
            self.unresolved=False
            (self.output/'summary.json').write_text(json.dumps({
                'attempts':self.attempts,'cost_usd':str(self.spent),
                'no_automatic_retry':not self.allow_standard_fallback,
                'generic_retry_enabled':False,
                'authorized_retry_exception':('same_model_standard_after_explicit_flex_capacity'
                    if self.allow_standard_fallback else None),
                'requested_model':MODEL,'provider':provider,'service_tier':tier,
                'allow_standard_fallback':self.allow_standard_fallback,
                'standard_active':self.standard_active,'flex_capacity_holds':self.capacity_holds,
                'charged_with_local_holds_usd':str(self.spent+self.held),
                'tool_name':self.tool_name},indent=2))
            return raw
        finally:self.ledger.finish_attempt(ident)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('campaign-root','key-file','output','name'):p.add_argument('--'+name,required=True)
    p.add_argument('--port',type=int,default=19861);p.add_argument('--expected-calls',type=int,required=True)
    p.add_argument('--max-calls',type=int,default=75);p.add_argument('--cap-usd',type=Decimal,default=Decimal(3))
    p.add_argument('--shared-cap-usd',type=Decimal,choices=(Decimal(85),Decimal(95)),default=Decimal(85))
    p.add_argument('--profile',choices=('pilot75','comparison180','full_panel1800'),default='pilot75')
    p.add_argument('--tool-name',choices=('robot_decision','semantic_goal'),default='robot_decision')
    p.add_argument('--wall-limit-s',type=int,default=2400)
    p.add_argument('--acknowledge-failed-request',action='append',default=[])
    p.add_argument('--allow-standard-fallback',action='store_true')
    p.add_argument('--offline-request',help='One retained legal request for route qualification only; no motion')
    a=p.parse_args()
    trial_limits(a.profile,a.max_calls,a.cap_usd,a.wall_limit_s)
    if '/' in a.name:raise ValueError('invalid trial name')
    sys.path.insert(0,a.campaign_root)
    from openrouter_pilot import Ledger,RUN,load_key
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    token=secrets.token_urlsafe(32);path=out/'relay-token';path.write_text(token);path.chmod(0o600)
    with (RUN/'runner.lock').open('a') as lock,httpx.Client(timeout=900,trust_env=False) as http:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ledger=Ledger(RUN/'budget.jsonl',max_calls=4209,limit_usd=a.shared_cap_usd,
            resumed_at=time.time(),wall_limit_seconds=min(a.wall_limit_s,2400),
            acknowledged_unknown_ids=a.acknowledge_failed_request)
        count=sum(e['event']=='reserved' for e in ledger.read())
        if count!=a.expected_calls:raise ValueError('shared call count changed; inspect ledger')
        ledger.max_calls=count+a.max_calls
        ledger.append({'event':'operator_robodojo_supervision_scope','time':time.time(),
            'name':a.name,'max_calls':ledger.max_calls,'local_cap_usd':str(a.cap_usd),
            'trial_profile':a.profile,'trial_call_limit':a.max_calls,'wall_limit_s':a.wall_limit_s,
            'paid_ledger_window_s':min(a.wall_limit_s,2400),
            'shared_cap_usd':str(a.shared_cap_usd),'model':MODEL,'provider':'openai/flex','tool_name':a.tool_name,
            'authorization':'standing low-budget physical-lab approval; owner selected Sol 6.1 Flex'})
        relay=Relay(ledger,load_key(a.key_file),token,out,a.name,a.max_calls,a.cap_usd,http,a.tool_name,
                    allow_standard_fallback=a.allow_standard_fallback)
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
            'allow_standard_fallback':a.allow_standard_fallback,
            'profile':a.profile,'wall_limit_s':a.wall_limit_s,
            'paid_ledger_window_s':min(a.wall_limit_s,2400),
            'local_cap_usd':str(a.cap_usd),'shared_cap_usd':str(a.shared_cap_usd)}),flush=True)
        HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()


if __name__=='__main__':main()
