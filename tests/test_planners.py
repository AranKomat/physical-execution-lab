import json,sys,threading,time,types
from pathlib import Path
import pytest
from prl.planners.base import make_context,bind_response
from prl.planners.local import CommandPlanner,FilePlanner,ReferencePlanner
from prl.planners.compatible_api import CompatibleAPIPlanner
from prl.budget import CallLedger
from prl.journal import Journal
from prl.util import read_json,atomic_json
from prl.errors import ValidationError,Unavailable

@pytest.fixture
def context(runtime):
    b,g,j=runtime;return make_context(b.observe(),g.registry,[],g.budget,'unique:d0')


def test_bind_cannot_change_observation(context):
    with pytest.raises(ValidationError):bind_response({'capability':'observe','arguments':{},'observation_id':'elsewhere'},context)

def test_reference_forbidden_native(context,tmp_path):
    context['observation']['information_profile']='sensor'
    with pytest.raises(ValidationError):ReferencePlanner().decide(context,tmp_path)

def test_command_roundtrip(context,tmp_path):
    p=CommandPlanner([sys.executable,'-c','import sys,json;json.load(sys.stdin);print(json.dumps({"capability":"observe","arguments":{},"max_steps":0}))'])
    answer=p.decide(context,tmp_path);assert answer.capability=='observe'

def test_command_timeout(context,tmp_path):
    p=CommandPlanner([sys.executable,'-c','import time;time.sleep(10)'],timeout_s=.05)
    with pytest.raises(Unavailable):p.decide(context,tmp_path)

def test_command_bad_json(context,tmp_path):
    p=CommandPlanner([sys.executable,'-c','print("not json")'])
    with pytest.raises(ValidationError):p.decide(context,tmp_path)

def test_command_secrets_removed(context,tmp_path,monkeypatch):
    monkeypatch.setenv('VERY_SECRET_TOKEN','1234')
    script='import os,json; print(json.dumps({"capability":"observe","arguments":{},"max_steps":0,"decision_summary":str("VERY_SECRET_TOKEN" in os.environ)}))'
    p=CommandPlanner([sys.executable,'-c',script]);assert p.decide(context,tmp_path).decision_summary=='False'

def test_file_roundtrip(context,tmp_path):
    q=tmp_path/'queue';out=tmp_path/'turn';out.mkdir()
    def respond():
        for _ in range(100):
            found=list(q.glob('*__unique_d0/request.json'))
            if found:break
            time.sleep(.01)
        request=found[0]
        d=read_json(request)
        atomic_json(request.parent/'response.json',{'request_sha256':d['request_sha256'],
            'proposal':{'capability':'observe','arguments':{},'max_steps':0}})
    t=threading.Thread(target=respond);t.start()
    answer=FilePlanner(q,timeout_s=3).decide(context,out);t.join()
    assert answer.capability=='observe'

def test_expired_file_request(context,tmp_path):
    p=FilePlanner(tmp_path/'queue',timeout_s=.01)
    with pytest.raises(Unavailable):p.decide(context,tmp_path)
    assert len(list((tmp_path/'queue').glob('*__unique_d0/EXPIRED.json')))==1

@pytest.fixture
def ledger(tmp_path):
    j=Journal(tmp_path/'calls.jsonl');l=CallLedger(j,max_calls=10,max_reserved_tokens=1000000)
    yield l
    j.close()


def test_api_disabled_by_default(ledger):
    with pytest.raises(Unavailable):CompatibleAPIPlanner({},ledger)

@pytest.mark.parametrize('url',['http://external.example/v1','https://user:pw@host/v1','https://host/v1?q=secret'])
def test_api_endpoint_validation(ledger,url,monkeypatch):
    monkeypatch.setenv('PRL_API_KEY','private')
    with pytest.raises(ValidationError):CompatibleAPIPlanner({'model':'test-model','base_url':url},ledger,allow_api=True)

def test_api_protocol_cannot_be_overridden(ledger):
    with pytest.raises(ValidationError):CompatibleAPIPlanner({'model':'m','base_url':'http://127.0.0.1:1/v1','extra_request':{'messages':[]}},ledger,allow_api=True)

class Response:
    def __init__(self,data):self.data=json.dumps(data).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data

def test_api_mocked_roundtrip(context,tmp_path,ledger):
    p=CompatibleAPIPlanner({'model':'m','base_url':'http://127.0.0.1:1/v1','input_token_reservation':50000},ledger,allow_api=True)
    calls=[]
    def fake(req,timeout):
        calls.append(json.loads(req.data))
        return Response({'choices':[{'message':{'tool_calls':[{'function':{'name':'propose_capability','arguments':json.dumps({'capability':'observe','arguments':{},'max_steps':0})}}]}}],'usage':{'total_tokens':99}})
    p.opener=types.SimpleNamespace(open=fake)
    ans=p.decide(context,tmp_path)
    assert ans.capability=='observe' and ledger.tokens==99
    assert calls[0]['model']=='m' and 'Authorization' not in (tmp_path/'wire_request.json').read_text()

def test_api_failure_holds_reservation(context,tmp_path,ledger):
    p=CompatibleAPIPlanner({'model':'m','base_url':'http://127.0.0.1:1/v1','input_token_reservation':50000},ledger,allow_api=True)
    def fake(*a,**kw):raise TimeoutError()
    p.opener=types.SimpleNamespace(open=fake)
    with pytest.raises(Unavailable):p.decide(context,tmp_path)
    assert ledger.calls==1 and 'unique:d0' in ledger.pending

def test_api_missing_usage_retains_hold(context,tmp_path,ledger):
    p=CompatibleAPIPlanner({'model':'m','base_url':'http://127.0.0.1:1/v1','input_token_reservation':50000},ledger,allow_api=True)
    data={'choices':[{'message':{'tool_calls':[{'function':{'name':'propose_capability','arguments':'{"capability":"observe","arguments":{},"max_steps":0}'}}]}}]}
    p.opener=types.SimpleNamespace(open=lambda *a,**kw:Response(data))
    p.decide(context,tmp_path);assert ledger.pending
