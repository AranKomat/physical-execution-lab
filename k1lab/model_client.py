"""K1 client_factory implementations: Responses, compatible chat, file, subprocess.

No network is performed on import. Requests are archived without credentials.
No automatic retry (including Flex fallback) after an uncertain request.
"""
from __future__ import annotations
import base64
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from .errors import ContractError,Unavailable,TransportUncertain
from .util import atomic_json,canonical,digest,integer,load_json


class JSONResponse:
    def __init__(self,body):self.body=body
    def raise_for_status(self):pass
    def json(self):return self.body


def chat_to_responses(request,options):
    inputs=[]
    for message in request['messages']:
        role=message['role']
        if role=='tool':
            inputs.append({'type':'function_call_output','call_id':message['tool_call_id'],
                           'output':message['content']})
            continue
        if role not in ('user','assistant','system','developer'):raise ContractError('unsupported message role')
        content=message.get('content')
        if isinstance(content,str) and content:
            inputs.append({'role':role,'content':content})
        elif isinstance(content,list):
            blocks=[]
            for b in content:
                if b.get('type')=='text':blocks.append({'type':'input_text','text':b['text']})
                elif b.get('type')=='image_url':
                    blocks.append({'type':'input_image','image_url':b['image_url']['url'],
                                   'detail':options.get('image_detail','auto')})
                else:raise ContractError('unsupported multimodal block')
            inputs.append({'role':role,'content':blocks})
        elif content is not None and not isinstance(content,str):raise ContractError('unsupported message content')
        for call in message.get('tool_calls',[]):
            inputs.append({'type':'function_call','call_id':call['id'],'name':call['function']['name'],
                           'arguments':call['function']['arguments']})
    body={'model':request['model'],'input':inputs,'tools':[
        {'type':'function',**s['function'],'strict':False} for s in request['tools']],
        'tool_choice':'required','parallel_tool_calls':False,
        'max_output_tokens':options.get('max_output_tokens',2048),'store':False}
    if options.get('reasoning_effort') is not None:body['reasoning']={'effort':options['reasoning_effort']}
    if options.get('service_tier'):body['service_tier']=options['service_tier']
    return body


def responses_to_chat(body):
    if body.get('status') not in (None,'completed'):raise ContractError('Responses request did not complete')
    calls=[]; content=[]
    for item in body.get('output',[]):
        if item.get('type')=='function_call':
            calls.append({'id':item['call_id'],'type':'function','function':{'name':item['name'],'arguments':item['arguments']}})
        elif item.get('type')=='message':
            for b in item.get('content',[]):
                if b.get('type')=='output_text':content.append(b['text'])
    if len(calls)!=1:raise ContractError('exactly one function call per decision is required')
    usage=body.get('usage') or {}
    return {'model':body.get('model'),'choices':[{'finish_reason':'tool_calls','message':{
        'role':'assistant','content':'\n'.join(content) or None,'tool_calls':calls}}],
        'service_tier':body.get('service_tier'),
        'usage':{'prompt_tokens':usage.get('input_tokens'),'completion_tokens':usage.get('output_tokens'),
                 'total_tokens':usage.get('total_tokens'),'prompt_tokens_details':usage.get('input_tokens_details',{}),
                 'completion_tokens_details':usage.get('output_tokens_details',{})}}


def one_call(body,available):
    try:
        calls=body['choices'][0]['message']['tool_calls']
        if len(calls)!=1:raise ContractError('exactly one tool per decision')
        c=calls[0]; name=c['function']['name']
        if name not in available:raise ContractError('unknown tool returned')
        a=json.loads(c['function']['arguments'])
        if not isinstance(a,dict):raise ContractError('tool arguments must be an object')
    except (KeyError,IndexError,TypeError,json.JSONDecodeError) as e:
        raise ContractError('malformed model tool response') from e
    return body


class Client:
    def __init__(self,config,output,journal=None,allow_api=False,http_client=None,**_):
        self.config=dict(config); self.output=Path(output); self.output.mkdir(parents=True,exist_ok=True)
        self.journal=journal; self.mode=self.config.get('transport','file'); self.n=0
        self.output_spent=0; self.reserved=0; self.input_observed=0; self.unknown_usage_calls=0
        self.max_calls=integer(config.get('max_requests',100),1,100000,'max_requests')
        self.cap=integer(config.get('max_output_tokens',2048),1,100000,'max_output_tokens')
        self.output_budget=integer(config.get('max_total_output_tokens',204800),1,100000000,'max_total_output_tokens')
        self.timeout=float(config.get('timeout_s',180));self.http=http_client;self.key=''
        self.usages=[]; self.served_models=[]; self.served_tiers=[]
        if self.mode in ('responses','chat'):
            if not allow_api:raise Unavailable('model network requires --allow-api')
            base=config.get('base_url')
            if not base:raise ContractError('explicit provider base_url required')
            url=urlsplit(base)
            if url.username or url.password or url.query or url.fragment:raise ContractError('invalid base_url')
            if url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('127.0.0.1','localhost','::1')):
                raise ContractError('TLS required except loopback')
            self.key=os.environ.get(config.get('api_key_env','OPENAI_API_KEY'),'')
            if not self.key and url.hostname not in ('127.0.0.1','localhost','::1'):raise Unavailable('missing API key environment variable')
            self.http=self.http or httpx.Client(timeout=self.timeout,trust_env=False,follow_redirects=False)
        elif self.mode=='subprocess':
            if not config.get('trust_subprocess'):raise Unavailable('subprocess runs trusted local code, not a sandbox; opt in explicitly')
        elif self.mode!='file':raise ContractError('unknown planner transport')
    def __enter__(self):return self
    def __exit__(self,*_):
        if self.http:self.http.close()
    def _log(self,event,data):
        if self.journal:self.journal.append(event,data)
    def _response_envelope(self,value,request,request_hash,rid):
        if value.get('request_sha256')!=request_hash:raise ContractError('stale/mismatched external reply')
        if 'chat_response' in value:return value['chat_response']
        if not isinstance(value.get('arguments'),dict) or not isinstance(value.get('tool'),str):
            raise ContractError('reply needs tool and arguments')
        return {'model':request['model'],'choices':[{'finish_reason':'tool_calls','message':{'role':'assistant',
            'content':None,'tool_calls':[{'type':'function','id':rid,'function':{'name':value['tool'],
            'arguments':canonical(value['arguments'])}}]}}], 'usage':value.get('usage')}
    def post(self,_url,*,headers,json):
        request=json
        if request.get('model')=='gpt-6.1-sol':
            if self.mode=='chat':raise ContractError('gpt-6.1-sol tool calling requires Responses, not Chat Completions')
            if self.config.get('reasoning_effort') in ('none','minimal'):
                raise ContractError('gpt-6.1-sol does not support none/minimal effort')
        if self.n>=self.max_calls or self.output_spent+self.reserved+self.cap>self.output_budget:
            raise Unavailable('model call/output reservation limit')
        if len(canonical(request).encode())>self.config.get('max_request_bytes',12_000_000):
            raise ContractError('request byte limit; not a token estimate')
        rid=f'{self.n:06d}-{uuid.uuid4().hex[:10]}'; self.n+=1; self.reserved+=self.cap
        root=self.output/rid;root.mkdir()
        reqhash=digest(request)
        atomic_json(root/'request.json',{'request_sha256':reqhash,'chat_request':request},exclusive=True)
        self._log('model_request',{'id':rid,'sha256':reqhash,'transport':self.mode,'output_reserved':self.cap})
        start=time.monotonic()
        try:
            if self.mode in ('chat','responses'):
                wire=chat_to_responses(request,self.config) if self.mode=='responses' else dict(request)
                if self.mode=='chat':
                    wire.pop('max_tokens',None);wire.pop('temperature',None)
                    wire['max_completion_tokens']=self.cap
                    if self.config.get('reasoning_effort'):wire['reasoning_effort']=self.config['reasoning_effort']
                    if self.config.get('service_tier'):wire['service_tier']=self.config['service_tier']
                atomic_json(root/'wire_request.json',wire,exclusive=True)
                endpoint=self.config['base_url'].rstrip('/')+('/responses' if self.mode=='responses' else '/chat/completions')
                response=self.http.post(endpoint,headers={'Authorization':'Bearer '+self.key},json=wire)
                response.raise_for_status();raw=response.json()
                atomic_json(root/'wire_response.json',raw,exclusive=True)
                body=responses_to_chat(raw) if self.mode=='responses' else raw
            elif self.mode=='file':
                # Preserve exact image inputs; readable sidecar for a supervised external actor.
                image_lines=[]; image_index=0
                for m in request['messages']:
                    if not isinstance(m.get('content'),list):continue
                    for b in m['content']:
                        if b.get('type')=='image_url' and b['image_url']['url'].startswith('data:'):
                            uri=b['image_url']['url']; extension='jpg' if 'jpeg' in uri[:40] else 'png'
                            path=root/f'image_{image_index:03d}.{extension}'
                            path.write_bytes(base64.b64decode(uri.split(',',1)[1]));image_lines.append(path.name);image_index+=1
                (root/'ACTOR_REQUEST.md').write_text(
                    '# One decision, current episode only\n\nRead request.json and its camera images. Do not read evaluation '
                    'state files, other task recipes or simulator source geometry. Reply to response.json atomically with '
                    '`{"request_sha256":"'+reqhash+'","tool":"...","arguments":{...}}`. '
                    'Use supplied tools only.\n\nImages: '+', '.join(image_lines)+'\n')
                atomic_json(self.output/'PENDING.json',{'directory':str(root.resolve()),'request_sha256':reqhash,'state':'awaiting_response'})
                deadline=time.monotonic()+self.timeout
                while not (root/'response.json').exists():
                    if time.monotonic()>=deadline:raise TimeoutError('external actor did not reply')
                    time.sleep(0.05)
                value=load_json(root/'response.json'); body=self._response_envelope(value,request,reqhash,rid)
            else:
                argv=self.config.get('command')
                if not isinstance(argv,list) or not argv or any(not isinstance(x,str) for x in argv):
                    raise ContractError('subprocess command must be argv list, never shell text')
                env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('KEY','TOKEN','SECRET','PASSWORD'))}
                child=subprocess.run(argv,input=canonical({'request_sha256':reqhash,'chat_request':request}),
                                     text=True,capture_output=True,timeout=self.timeout,env=env,check=True)
                if len(child.stdout)>4_000_000:raise ContractError('subprocess response too large')
                body=self._response_envelope(__import__('json').loads(child.stdout),request,reqhash,rid)
            atomic_json(root/'chat_response.json',body,exclusive=True)
            usage=body.get('usage') or {}; used=usage.get('completion_tokens')
            self.usages.append(usage); self.served_models.append(body.get('model')); self.served_tiers.append(body.get('service_tier'))
            if type(used) is int and used>=0:
                self.reserved-=self.cap;self.output_spent+=used
                if used>self.cap:raise ContractError('provider exceeded output cap')
            else:self.unknown_usage_calls+=1  # reservation retained
            inp=usage.get('prompt_tokens')
            if type(inp) is int and inp>=0:self.input_observed+=inp
            self._log('model_response',{'id':rid,'latency_s':time.monotonic()-start,'usage':usage,
                       'served_model':body.get('model'),'served_service_tier':body.get('service_tier'),
                       'output_accounted':self.output_spent,'output_unresolved_reservation':self.reserved})
            checked=one_call(body,{s['function']['name'] for s in request['tools']})
            if self.mode=='file':
                atomic_json(self.output/'PENDING.json',{'directory':str(root.resolve()),'request_sha256':reqhash,'state':'completed'})
            return JSONResponse(checked)
        except Exception as exc:
            if self.mode=='file':
                atomic_json(self.output/'PENDING.json',{'directory':str(root.resolve()),'request_sha256':reqhash,'state':'failed_no_retry'})
            self._log('model_request_failed',{'id':rid,'type':type(exc).__name__,'automatic_retry':False,
                      'reservation_retained_unless_usage_reported':True})
            # K1 retries httpx exceptions. Deliberately raise a distinct error to prevent that.
            raise TransportUncertain(f'model request failed: {type(exc).__name__}; inspect archive; no automatic retry') from exc


def client_factory(config,output,journal=None,allow_api=False):
    return lambda **kwargs:Client(config,output,journal,allow_api,**kwargs)
