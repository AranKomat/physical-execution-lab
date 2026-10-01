"""Exercise run bookkeeping with contract doubles, not K1/native simulation."""
import json
from types import SimpleNamespace
import pytest
from k1lab import runner
from k1lab.errors import ContractError
from k1lab.util import digest
from k1lab.journal import verify
from k1lab.qualification import verify_freeze


def configuration():
    return {'condition':'k1_baseline','model':'test-model','memory_scope':'current_episode_only',
            'native':{'k1_root':'not-installed'},'planner':{'transport':'file'}}


def case():
    return {'id':'unit-case','suite':'libero_goal_task','task_id':1,'state_index':0,
            'state_sha256':digest('test'),'horizon':300,'partition':'dev'}


class Adapter:
    def __init__(self):self.frame=0;self.horizon=300;self.closed=False
    def success(self):return self.frame==4
    def close(self):self.closed=True


def test_native_absence_counts_full_row(monkeypatch,tmp_path):
    def fail(*a):raise RuntimeError('dependency missing')
    monkeypatch.setattr(runner,'load_k1',fail)
    r=runner.run_case(configuration(),case(),tmp_path/'run',allow_native=True,pilot=True)
    assert r['native_success'] is False and r['termination']=='infrastructure_failure'
    assert r['domain']=='native_libero_pro' and r['native_steps']==0
    assert verify(tmp_path/'run/events.jsonl')['events']>=2


def test_no_native_without_explicit_optin(tmp_path):
    with pytest.raises(Exception,match='allow-native'):
        runner.run_case(configuration(),case(),tmp_path/'run')
    assert not (tmp_path/'run').exists()


def test_stock_registry_is_untouched(monkeypatch,tmp_path):
    adapter=Adapter();seen={}
    def run_agent(a,output,*args,**kw):
        seen.update(kw);a.frame=4
        return {'elapsed_seconds':0.125,'llm_calls':0}
    monkeypatch.setattr(runner,'load_k1',lambda *a:SimpleNamespace(run_agent=run_agent))
    monkeypatch.setattr(runner,'make_adapter',lambda *a:adapter)
    r=runner.run_case(configuration(),case(),tmp_path/'run',allow_native=True,pilot=True)
    assert seen['registry_class'] is None
    assert adapter.closed and r['native_success'] and r['native_steps']==4
    assert r['upstream_agent_elapsed_s']==0.125


def test_cleanup_does_not_erase_native_outcome(monkeypatch,tmp_path):
    adapter=Adapter()
    def close():raise RuntimeError('cleanup issue')
    adapter.close=close
    def run_agent(a,*args,**kw):a.frame=4;return {}
    monkeypatch.setattr(runner,'load_k1',lambda *a:SimpleNamespace(run_agent=run_agent))
    monkeypatch.setattr(runner,'make_adapter',lambda *a:adapter)
    r=runner.run_case(configuration(),case(),tmp_path/'run',allow_native=True,pilot=True)
    assert r['native_success'] and (tmp_path/'run/evaluation_result.json').exists()
    events=[json.loads(x) for x in (tmp_path/'run/events.jsonl').read_text().splitlines()]
    assert any(x['event']=='cleanup_error' for x in events)


@pytest.mark.parametrize('key',['api_key','access_token','authorization'])
def test_inline_credentials_rejected(key):
    c=configuration();c['planner'][key]='private'
    with pytest.raises(ContractError,match='environment'):runner.validate_config(c)


def test_formal_freeze_cannot_depend_on_current_env(monkeypatch):
    monkeypatch.setenv('K1_MODEL','test-model')
    c=configuration();c['model']=None
    with pytest.raises(ContractError,match='concrete model'):
        verify_freeze(c,{'sha256':'0'*64})
