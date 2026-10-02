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
    def __init__(self):self.reserved=[];self.settled=[];self.finished=[]
    def reserve(self,*args):self.reserved.append(args)
    def settle(self,*args):self.settled.append(args)
    def finish_attempt(self,*args):self.finished.append(args)


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


def test_extended_comparison_limits_require_explicit_profile():
    relay.trial_limits('pilot75',75,Decimal(3),2400)
    relay.trial_limits('comparison180',180,Decimal(3),3600)
    for profile,calls,cap,wall in (
        ('pilot75',180,Decimal(3),2400),
        ('pilot75',75,Decimal(3),3600),
        ('comparison180',181,Decimal(3),3600),
        ('comparison180',180,Decimal('3.01'),3600),
        ('comparison180',180,Decimal(3),3601)):
        with pytest.raises(ValueError):relay.trial_limits(profile,calls,cap,wall)
