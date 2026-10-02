import importlib.util
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import json
import pytest

spec=importlib.util.spec_from_file_location('budget_relay',Path(__file__).resolve().parents[2]/'scripts/multibench/budget_responses_relay.py')
relay=importlib.util.module_from_spec(spec);spec.loader.exec_module(relay)


def body():
    return {'model':'gpt-6.1-sol','service_tier':'flex','reasoning':{'effort':'medium'},
        'store':False,'max_output_tokens':2048,'parallel_tool_calls':False,
        'tools':[{'type':'function','name':'robot_decision'}],
        'input':[{'role':'user','content':'current robot observation'}]}


class Ledger:
    def __init__(self):self.reserved=[];self.settled=[];self.finished=[];self.events=[]
    def reserve(self,*args):self.reserved.append(args)
    def settle(self,*args):self.settled.append(args)
    def finish_attempt(self,*args):self.finished.append(args)
    def append(self,item):self.events.append(item)


def test_relay_binds_route_and_accounts_cost(tmp_path):
    ledger=Ledger();calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs))
        raw={'status':'completed','model':'openai/gpt-6.1-sol','service_tier':'flex','usage':{'cost':.001}}
        return SimpleNamespace(status_code=200,content=json.dumps(raw).encode(),json=lambda:raw)
    r=relay.Relay(ledger,'key','token',tmp_path,'trial',2,Decimal(1),SimpleNamespace(post=post))
    assert r.forward(body())['service_tier']=='flex'
    assert calls[0][0]=='https://openrouter.ai/api/v1/responses'
    assert calls[0][1]['json']['provider']['allow_fallbacks'] is False
    assert 'parallel_tool_calls' not in calls[0][1]['json']
    assert len(ledger.reserved)==len(ledger.settled)==1 and r.spent==Decimal('.001')


@pytest.mark.parametrize('error',['http','cost','tier','capacity'])
def test_relay_does_not_retry_uncertain_or_invalid_response(tmp_path,error):
    ledger=Ledger()
    raw={'status':'completed','model':'openai/gpt-6.1-sol','service_tier':'flex','usage':{'cost':.001}}
    if error=='cost':raw['usage']={}
    if error=='tier':raw['service_tier']='default'
    if error=='capacity':raw.update(status='failed',usage=None,error={'message':'Flex temporarily unavailable'})
    response=SimpleNamespace(status_code=500 if error=='http' else 200,
        content=json.dumps(raw).encode(),json=lambda:raw)
    r=relay.Relay(ledger,'key','token',tmp_path,'trial',2,Decimal(1),SimpleNamespace(post=lambda *a,**k:response))
    with pytest.raises(RuntimeError):r.forward(body())
    with pytest.raises(ValueError,match='unresolved'):r.forward(body())
    assert len(ledger.reserved)==1 and len(ledger.finished)==1
    assert len(ledger.settled)==(1 if error=='tier' else 0)


def test_relay_rejects_tier_fallback_before_reserving(tmp_path):
    b=body();b['service_tier']='default'
    with pytest.raises(ValueError):relay.request_bound(b)


def test_semantic_tool_requires_explicit_selection():
    b=body();b['tools'][0]['name']='semantic_goal'
    with pytest.raises(ValueError):relay.request_bound(b)
    assert relay.request_bound(b,'semantic_goal')>0
    with pytest.raises(ValueError):relay.request_bound(body(),'semantic_goal')
    with pytest.raises(ValueError):relay.request_bound(b,'arbitrary_tool')


def test_actual_semantic_schema_fits_existing_responses_bounds():
    from semantic_lab.planner import tool_schema
    from k1lab.model_client import chat_to_responses
    b=chat_to_responses({'model':'gpt-6.1-sol',
        'messages':[{'role':'user','content':'current observation'}],
        'tools':[tool_schema()]}, {'service_tier':'flex','reasoning_effort':'medium',
        'max_output_tokens':2048})
    assert relay.request_bound(b,'semantic_goal')>0
    assert b['tools'][0]['parameters']['additionalProperties'] is False


def test_semantic_route_rejects_wrong_tool_before_reservation(tmp_path):
    ledger=Ledger()
    def forbidden(*args,**kwargs):raise AssertionError('must not call provider')
    r=relay.Relay(ledger,'key','token',tmp_path,'semantic',2,Decimal(1),
        SimpleNamespace(post=forbidden),tool_name='semantic_goal')
    with pytest.raises(ValueError):r.forward(body())
    assert not ledger.reserved


def test_extended_comparison_limits_require_explicit_profile():
    relay.trial_limits('pilot75',75,Decimal(3),2400)
    relay.trial_limits('comparison180',180,Decimal(3),3600)
    relay.trial_limits('full_panel1800',1800,Decimal(3),3600)
    for profile,calls,cap,wall in (
        ('pilot75',180,Decimal(3),2400),
        ('pilot75',75,Decimal(3),3600),
        ('comparison180',181,Decimal(3),3600),
        ('comparison180',180,Decimal('3.01'),3600),
        ('comparison180',180,Decimal(3),3601),
        ('full_panel1800',1801,Decimal(3),3600),
        ('full_panel1800',1800,Decimal('3.01'),3600),
        ('full_panel1800',1800,Decimal(3),3601)):
        with pytest.raises(ValueError):relay.trial_limits(profile,calls,cap,wall)


def capacity_response():
    return dict(status='failed', model=relay.MODEL, usage=None, output=[],
        error=dict(code='server_error',
                   message='Flex processing is temporarily unavailable. Please try again later or use standard processing.'))


def test_authorized_capacity_fallback_retains_hold_and_pins_same_model(tmp_path):
    ledger, calls = Ledger(), []
    responses = [capacity_response(), dict(status='completed', model=relay.MODEL,
                                          service_tier='default', usage=dict(cost=.002))]

    def post(url, **kwargs):
        calls.append(kwargs['json'])
        raw = responses.pop(0)
        return SimpleNamespace(status_code=200, content=json.dumps(raw).encode(), json=lambda: raw)

    r = relay.Relay(ledger,'key','token',tmp_path,'trial',3,Decimal(1),SimpleNamespace(post=post),
                    allow_standard_fallback=True)
    assert r.forward(body())['service_tier'] == 'default'
    assert [row['service_tier'] for row in calls] == ['flex', 'default']
    assert calls[1]['provider']['only'] == ['openai']
    assert all(row['model'] == relay.MODEL for row in calls)
    assert len(ledger.reserved) == 2 and len(ledger.settled) == 1
    assert ledger.reserved[1][2] == ledger.reserved[0][2] * 2
    assert r.held == ledger.reserved[0][2] and not r.unresolved
    assert 'trial-0' in ledger.acknowledged_unknown_ids and r.standard_active
    summary = json.loads((tmp_path/'summary.json').read_text())
    assert summary['no_automatic_retry'] is False
    assert summary['generic_retry_enabled'] is False
    assert summary['authorized_retry_exception'] == 'same_model_standard_after_explicit_flex_capacity'


def test_fallback_hold_counts_against_local_cap(tmp_path):
    ledger, calls = Ledger(), []
    raw = capacity_response()

    def post(*args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status_code=200, content=json.dumps(raw).encode(), json=lambda: raw)

    reserve = relay.request_bound(body())
    r = relay.Relay(ledger,'key','token',tmp_path,'trial',3,reserve*Decimal('2.5'),
                    SimpleNamespace(post=post), allow_standard_fallback=True)
    with pytest.raises(ValueError, match='budget'):
        r.forward(body())
    assert len(calls) == len(ledger.reserved) == 1
    assert r.held == reserve and not ledger.settled


@pytest.mark.parametrize('kind', ['generic_error', 'output_present', 'wrong_model', 'network'])
def test_fallback_never_retries_other_or_uncertain_failures(tmp_path, kind):
    ledger, calls = Ledger(), []
    raw = capacity_response()
    if kind == 'generic_error':raw['error']['message'] = 'Internal server error'
    if kind == 'output_present':raw['output'] = [{'type':'function_call'}]
    if kind == 'wrong_model':raw['model'] = 'another-model'

    def post(*args, **kwargs):
        calls.append(kwargs)
        if kind == 'network':raise TimeoutError('uncertain provider request')
        return SimpleNamespace(status_code=200, content=json.dumps(raw).encode(), json=lambda: raw)

    r = relay.Relay(ledger,'key','token',tmp_path,'trial',3,Decimal(1),SimpleNamespace(post=post),
                    allow_standard_fallback=True)
    with pytest.raises((RuntimeError, TimeoutError)):
        r.forward(body())
    with pytest.raises(ValueError, match='unresolved'):
        r.forward(body())
    assert len(calls) == len(ledger.reserved) == 1 and not r.standard_active
