import json,threading,time,sys
from pathlib import Path
import httpx
import pytest
from k1lab.model_client import Client,chat_to_responses,responses_to_chat,one_call
from k1lab.errors import ContractError,Unavailable,TransportUncertain
from k1lab.util import atomic_json,load_json


def request():return {'model':'test-model','messages':[{'role':'system','content':'Use tools.'},{'role':'user','content':[
        {'type':'text','text':'CURRENT frame 0'},{'type':'image_url','image_url':{'url':'data:image/png;base64,YQ=='}}]}],
        'tools':[{'type':'function','function':{'name':'done','description':'Request end','parameters':{'type':'object','properties':{}}}}],
        'tool_choice':'required','max_tokens':1800}
def response():return {'model':'test-model','status':'completed','output':[{'type':'function_call','call_id':'a','name':'done','arguments':'{}'}],
                       'usage':{'input_tokens':20,'output_tokens':4,'total_tokens':24}}

def test_responses_translation_vision_and_tools():
    r=chat_to_responses(request(),{'service_tier':'flex','reasoning_effort':'medium'})
    assert r['input'][1]['content'][1]['type']=='input_image'
    assert r['tools'][0]['name']=='done' and r['parallel_tool_calls'] is False
    assert 'temperature' not in r and r['store'] is False and r['service_tier']=='flex'

def test_response_translation_tool_history():
    r=request();r['messages']+=[{'role':'assistant','content':None,'tool_calls':[{'id':'a','function':{'name':'done','arguments':'{}'}}]},
                                {'role':'tool','tool_call_id':'a','content':'not complete'}]
    out=chat_to_responses(r,{})
    assert out['input'][-2]['type']=='function_call' and out['input'][-1]['type']=='function_call_output'

def test_response_output_excludes_internal_reasoning():
    r=response();r['output'].insert(0,{'type':'reasoning','summary':[{'text':'not an actor action'}]})
    c=responses_to_chat(r);assert c['choices'][0]['message']['content'] is None
    assert c['usage']['completion_tokens']==4

@pytest.mark.parametrize('mutation',[{'status':'incomplete'},{'output':[]},{'output':response()['output']*2}])
def test_malformed_response_rejected(mutation):
    with pytest.raises(ContractError):responses_to_chat(response()|mutation)

def test_network_opt_in(tmp_path):
    with pytest.raises(Unavailable):Client({'transport':'responses','base_url':'https://api.openai.com/v1'},tmp_path)

def test_tls_and_credentials_not_url(tmp_path):
    with pytest.raises(ContractError):Client({'transport':'responses','base_url':'http://test.com/v1'},tmp_path,allow_api=True)

def test_exactly_once_network_and_no_credentials_archive(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','SECRET-DO-NOT-LOG');sent=[]
    def handler(req):sent.append(json.loads(req.content));return httpx.Response(200,json=response())
    http=httpx.Client(transport=httpx.MockTransport(handler))
    with Client({'transport':'responses','base_url':'https://api.openai.com/v1'},tmp_path,allow_api=True,http_client=http) as c:
        body=c.post('',headers={},json=request()).json();assert c.n==1 and c.output_spent==4
    assert len(sent)==1 and body['choices'][0]['message']['tool_calls'][0]['function']['name']=='done'
    assert not any('SECRET-DO-NOT-LOG' in p.read_text() for p in tmp_path.rglob('*.json'))

def test_network_failure_does_not_retry(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','X');n=[]
    def handler(req):n.append(1);return httpx.Response(429,json={'error':'capacity'})
    c=Client({'transport':'responses','base_url':'https://api.openai.com/v1','max_output_tokens':50},tmp_path,
             allow_api=True,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(TransportUncertain):c.post('',headers={},json=request())
    assert len(n)==1 and c.reserved==50

def test_reservation_blocks_next_request(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','X')
    c=Client({'transport':'responses','base_url':'https://api.openai.com/v1','max_output_tokens':50,'max_total_output_tokens':50},tmp_path,
             allow_api=True,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(500,json={})) ))
    with pytest.raises(TransportUncertain):c.post('',headers={},json=request())
    with pytest.raises(Unavailable):c.post('',headers={},json=request())

def test_file_queue_complete_payload(tmp_path):
    c=Client({'transport':'file','timeout_s':2},tmp_path)
    def actor():
        while not (tmp_path/'PENDING.json').exists():time.sleep(.01)
        pending=load_json(tmp_path/'PENDING.json');root=Path(pending['directory'])
        assert (root/'image_000.png').read_bytes()==b'a'
        atomic_json(root/'response.json',{'request_sha256':pending['request_sha256'],'tool':'done','arguments':{}})
    t=threading.Thread(target=actor);t.start()
    out=c.post('',headers={},json=request()).json();t.join()
    assert out['choices'][0]['message']['tool_calls'][0]['function']['name']=='done'
    assert c.unknown_usage_calls==1 and c.reserved==c.cap

def test_stale_file_reply(tmp_path):
    c=Client({'transport':'file','timeout_s':2},tmp_path)
    def actor():
        while not (tmp_path/'PENDING.json').exists():time.sleep(.01)
        p=load_json(tmp_path/'PENDING.json');atomic_json(Path(p['directory'])/'response.json',{'request_sha256':'wrong','tool':'done','arguments':{}})
    t=threading.Thread(target=actor);t.start()
    with pytest.raises(TransportUncertain):c.post('',headers={},json=request())
    t.join()

def test_subprocess_trust_required(tmp_path):
    with pytest.raises(Unavailable):Client({'transport':'subprocess'},tmp_path)

def test_subprocess_transport(tmp_path):
    c=Client({'transport':'subprocess','trust_subprocess':True,'command':[sys.executable,'examples/respond_once.py']},tmp_path)
    body=c.post('',headers={},json=request()).json();assert body['choices'][0]['message']['tool_calls'][0]['function']['name']=='done'

def test_invalid_tool_not_accepted():
    with pytest.raises(ContractError):one_call(responses_to_chat(response()),{'other'})
