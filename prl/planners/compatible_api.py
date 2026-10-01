"""Opt-in image + function-tool client for an OpenAI-compatible chat endpoint.

No particular provider/model is assumed. Provider-specific reasoning fields can
be supplied in config.extra_request after review. No network tests were made here.
"""
from __future__ import annotations
import base64
import json
import os
import urllib.request
import urllib.parse
from pathlib import Path
from .base import bind_response
from ..errors import ValidationError, Unavailable
from ..util import atomic_json, canonical, digest, file_digest


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


class CompatibleAPIPlanner:
    def __init__(self,config,ledger,*,allow_api=False,decoder=bind_response):
        if not allow_api: raise Unavailable('Model API calls require --allow-api')
        self.config=config; self.ledger=ledger; self.decoder=decoder
        self.model=config.get('model') or os.environ.get('PRL_MODEL')
        self.base=config.get('base_url') or os.environ.get('PRL_BASE_URL')
        if not self.model or not self.base:
            raise Unavailable('Set explicit PRL_MODEL and PRL_BASE_URL; no default model/provider')
        u=urllib.parse.urlsplit(self.base)
        if u.username or u.password or u.query or u.fragment:
            raise ValidationError('No credentials/query/fragment in base URL')
        if u.scheme!='https' and not (u.scheme=='http' and u.hostname in ('127.0.0.1','localhost','::1')):
            raise ValidationError('HTTPS required except local loopback')
        self.key=os.environ.get(config.get('api_key_env','PRL_API_KEY'),'')
        if not self.key and u.hostname not in ('localhost','127.0.0.1','::1'):
            raise Unavailable('Missing API key environment variable')
        self.identity='compatible_api:'+self.model+':'+digest(self.base)[:12]
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        extra=config.get('extra_request',{})
        if set(extra)&{'model','messages','tools','tool_choice','stream','max_tokens','max_completion_tokens'}:
            raise ValidationError('extra_request cannot override protocol or budget fields')

    def decide(self,context,output_dir):
        out=Path(output_dir)
        content=[{'type':'text','text':canonical(context)}]
        for image in context['observation']['images']:
            path=Path(image['path'])
            if path.stat().st_size>8_000_000: raise ValidationError('image_too_large')
            image_bytes=path.read_bytes()
            import hashlib
            if hashlib.sha256(image_bytes).hexdigest()!=image['sha256']:
                raise ValidationError('image_changed_after_observation')
            content.append({'type':'text','text':f"Camera {image['camera']}; original {image['width']}x{image['height']}; observation {image['observation_id']}"})
            content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(image_bytes).decode()}})
        schema={'type':'object','properties':{
            'capability':{'type':'string','enum':[c['name'] for c in context['capabilities']]},
            'arguments':{'type':'object'},'max_steps':{'type':'integer','minimum':0,'maximum':2000},
            'decision_summary':{'type':'string'},'objective':{'type':'string'},
            'alternatives':{'type':'array','maxItems':3,'items':{'type':'object'}}},
            'required':['capability','arguments','max_steps'],'additionalProperties':False}
        schema=context.get('json_schema',schema)
        body={'model':self.model,'messages':[{'role':'system','content':context['system']},
                                           {'role':'user','content':content}],
              'tools':[{'type':'function','function':{'name':'propose_capability',
                   'description':'Submit one bounded action proposal, never a native motor command.',
                   'parameters':schema}}],
              'tool_choice':{'type':'function','function':{'name':'propose_capability'}},
              'stream':False,**self.config.get('extra_request',{})}
        output_cap=int(self.config.get('max_output_tokens',2048))
        input_cap=int(self.config.get('input_token_reservation',20000))
        # Conservative text byte-count ceiling plus explicit image allowance. This
        # is a reservation convention, NOT an exact tokenizer/currency meter.
        projected=len(canonical(context).encode())+len(context['observation']['images'])*4096
        if projected>input_cap: raise ValidationError('context_exceeds_input_reservation')
        field=self.config.get('token_limit_field','max_tokens')
        if field not in ('max_tokens','max_completion_tokens'): raise ValidationError('invalid_token_limit_field')
        body[field]=output_cap
        atomic_json(out/'wire_request.json',body)
        rid=context['proposal_id']
        self.ledger.reserve(rid,input_cap,output_cap)
        req=urllib.request.Request(self.base.rstrip('/')+'/chat/completions',
            data=canonical(body).encode(),headers={'Content-Type':'application/json',
                **({'Authorization':'Bearer '+self.key} if self.key else {})},method='POST')
        try:
            with self.opener.open(req,timeout=float(self.config.get('timeout_s',120))) as response:
                raw=response.read(8_000_001)
                if len(raw)>8_000_000: raise ValidationError('response_too_large')
                data=json.loads(raw)
        except Exception as e:
            self.ledger.journal.append('model_call_unresolved',{'request_id':rid,'error_type':type(e).__name__,
                'note':'Reservation preserved; no automatic retry.'})
            raise Unavailable(f'model_request_unresolved:{type(e).__name__}') from e
        atomic_json(out/'wire_response.json',data)
        usage=data.get('usage',{}).get('total_tokens')
        self.ledger.finish(rid,usage)
        try:
            m=data['choices'][0]['message']; calls=m.get('tool_calls',[])
            if len(calls)!=1 or calls[0]['function']['name']!='propose_capability':
                raise ValidationError('expected_exactly_one_propose_capability_call')
            answer=json.loads(calls[0]['function']['arguments'])
        except (KeyError,ValueError,IndexError) as e:
            raise ValidationError('malformed_model_tool_response') from e
        atomic_json(out/'response.json',answer)
        return self.decoder(answer,context)
