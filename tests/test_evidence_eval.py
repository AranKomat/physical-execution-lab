import copy,json,dataclasses
from pathlib import Path
import pytest
from prl.journal import Journal
from prl.budget import Budget,CallLedger
from prl.errors import ValidationError,BudgetExceeded,UncertainExecution
from prl.util import digest,read_json,atomic_json
from prl.manifests import write_manifest,load_manifest,assert_disjoint,build_native_manifest
from prl.evaluation import wilson,mcnemar_exact,cluster_bootstrap,read_run,compare_runs,summarize_run
from prl.runner import run_experiment
from prl.evolution import regression_gate,attribute

ROOT=Path(__file__).resolve().parents[1]

def test_journal_hash_and_resume(tmp_path):
    p=tmp_path/'trace.jsonl';j=Journal(p);j.append('a',{'x':1});j.close()
    j=Journal(p,resume=True);j.append('b',{'x':2});j.close()
    assert len(Journal.verify(p))==2
    with pytest.raises(FileExistsError):Journal(p)

def test_journal_tampering(tmp_path):
    p=tmp_path/'trace.jsonl';j=Journal(p);j.append('a',{'x':1});j.close()
    p.write_text(p.read_text().replace('"x":1','"x":2'))
    with pytest.raises(ValidationError):Journal.verify(p)

def test_journal_truncated(tmp_path):
    p=tmp_path/'trace.jsonl';p.write_text('{"seq":0')
    with pytest.raises(ValidationError):Journal.verify(p)

def test_model_ledger_retains_unknown(tmp_path):
    j=Journal(tmp_path/'calls');l=CallLedger(j,max_calls=3,max_reserved_tokens=100)
    l.reserve('r1',30,10);l.finish('r1',None)
    assert l.tokens==40 and 'r1' in l.pending
    with pytest.raises(UncertainExecution):l.reserve('r1',5,5)
    with pytest.raises(BudgetExceeded):l.reserve('r2',60,10)
    j.close()

def test_ledger_known_usage_and_limit(tmp_path):
    j=Journal(tmp_path/'calls');l=CallLedger(j,max_calls=1,max_reserved_tokens=100)
    l.reserve('r1',60,10);l.finish('r1',12)
    assert l.tokens==12 and not l.pending
    with pytest.raises(BudgetExceeded):l.reserve('r2',1,1)
    j.close()

def test_budget_each_axis():
    b=Budget(max_steps=1,max_decisions=1,max_vla_calls=1,max_wall_s=100)
    b.before_step();b.record_step()
    with pytest.raises(BudgetExceeded):b.before_step()
    b.take_decision()
    with pytest.raises(BudgetExceeded):b.take_decision()
    b.take_vla_call()
    with pytest.raises(BudgetExceeded):b.take_vla_call()
    b.started-=101
    with pytest.raises(BudgetExceeded):b.check_wall()

def test_manifest_hash_and_duplicate(tmp_path,case):
    p=tmp_path/'m.json';d=write_manifest(p,'synthetic','dev',[dataclasses.asdict(case)])
    assert load_manifest(p)[1][0].identity==case.identity
    d['cases'][0]['state_index']=8;atomic_json(p,d)
    with pytest.raises(ValidationError):load_manifest(p)
    with pytest.raises(ValidationError):write_manifest(p,'synthetic','dev',[dataclasses.asdict(case)]*2)

def test_dev_test_disjoint_ignore_policy_seed(case):
    a={'cases':[dataclasses.asdict(case)]};b=copy.deepcopy(a)
    b['cases'][0]['policy_seed']=33;b['cases'][0]['case_id']='renamed'
    with pytest.raises(ValidationError):assert_disjoint(a,b)

def test_catalog_invalid_and_state_range():
    c={'states':{'libero_goal_task':{'0':[digest('s')]}}};c['sha256']=digest(c)
    assert len(build_native_manifest(c,'dev',[0]))==1
    with pytest.raises(ValidationError):build_native_manifest(c,'test',[1])
    c['sha256']='bad'
    with pytest.raises(ValidationError):build_native_manifest(c,'dev',[0])

def test_stats():
    assert wilson(0,0)==[None,None]
    assert wilson(50,100)==pytest.approx([.403831530,.596168470])
    assert mcnemar_exact(10,0)==pytest.approx(2/1024)
    assert mcnemar_exact(0,0)==1
    assert mcnemar_exact(1000,1000)==pytest.approx(1)
    assert cluster_bootstrap([{'task_cluster':'a','delta':1}])==[None,None]
    assert cluster_bootstrap([{'task_cluster':'a','delta':1},{'task_cluster':'b','delta':1}])==[1,1]

@pytest.fixture
def experiment_pair(tmp_path):
    cfg=read_json(ROOT/'configs/synthetic_nominal.json')
    a=tmp_path/'a';b=tmp_path/'b';manifest=ROOT/'manifests/synthetic_dev.json'
    run_experiment(cfg,manifest,a)
    run_experiment({**cfg,'mode':'dynamic'},manifest,b)
    return a,b,cfg

def test_complete_fixture_run_and_comparison(experiment_pair):
    a,b,c=experiment_pair
    result=compare_runs(a,b)
    assert result['source']=='synthetic' and result['complete_pairs']==4
    assert result['wins_b_only']==result['wins_a_only']==0
    assert 'SYNTHETIC ONLY' in result['warning']
    assert (b/'report.html').exists()

def test_unmatched_model_settings_refused(experiment_pair):
    a,b,c=experiment_pair;d=read_json(b/'run.json');d['planner_identity']='OTHER';atomic_json(b/'run.json',d)
    with pytest.raises(ValidationError):compare_runs(a,b)

def test_incomplete_not_silently_removed(experiment_pair):
    a,b,c=experiment_pair
    p=next((b/'episodes').glob('*/result.json'));p.unlink()
    s=summarize_run(b);assert s['missing']==1 and not s['fully_completed']
    comp=compare_runs(a,b);assert not comp['complete'] and len(comp['missing_pairs'])==1

def test_result_tamper_detected(experiment_pair):
    a,b,c=experiment_pair;p=next((a/'episodes').glob('*/result.json'))
    d=read_json(p);d['native_success']=not d['native_success'];atomic_json(p,d)
    with pytest.raises(ValidationError):read_run(a)

def test_resume_no_duplicate_steps(experiment_pair):
    a,b,c=experiment_pair
    before=[p.read_bytes() for p in sorted(a.glob('episodes/*/events.jsonl'))]
    run_experiment(c,ROOT/'manifests/synthetic_dev.json',a,resume=True)
    assert before==[p.read_bytes() for p in sorted(a.glob('episodes/*/events.jsonl'))]

def test_regression_gate_is_not_deployment(experiment_pair):
    a,b,c=experiment_pair;r=regression_gate(a,b)
    assert r['decision']=='eligible_for_broader_regression' and r['source']=='synthetic'

def test_native_needs_explicit_optin(tmp_path,case):
    p=tmp_path/'native.json';write_manifest(p,'native','dev',[dataclasses.asdict(case)])
    from prl.errors import Unavailable
    with pytest.raises(Unavailable):run_experiment({'mode':'frozen','backend':'rpent'},p,tmp_path/'out')

def test_misnamed_backend_rejected(tmp_path):
    with pytest.raises(ValidationError):run_experiment({'mode':'frozen','backend':'isaac'},ROOT/'manifests/synthetic_dev.json',tmp_path/'out')

def test_infrastructure_failfast_retains_denominator(tmp_path):
    c=read_json(ROOT/'configs/synthetic_dynamic.json')
    c['planner']={'kind':'command','command':['/no-such-program'],'timeout_s':1}
    s=run_experiment(c,ROOT/'manifests/synthetic_dev.json',tmp_path/'out')
    assert s['started']==1 and s['missing']==3 and s['infrastructure_or_protocol_errors']==1
    assert (tmp_path/'out/STOPPED.json').exists()

def test_attribution_is_explicit_hypothesis():
    r=attribute({'case':{'case_id':'x'},'status':'completed','reason':'stagnation','native_success':False})
    assert r['causal_status']=='hypothesis_only' and r['candidate_layer']=='local_control_or_geometry'

def test_campaign_budget_stops_without_fake_task_failures(tmp_path,monkeypatch):
    class P:
        identity='test-budget'
        def decide(self,*args):raise BudgetExceeded('model_reservation_budget')
    import prl.runner as runner
    monkeypatch.setattr(runner,'planner_factory',lambda *args:P())
    c=read_json(ROOT/'configs/synthetic_dynamic.json')
    s=run_experiment(c,ROOT/'manifests/synthetic_dev.json',tmp_path/'out')
    assert s['completed']==0 and s['started']==1 and s['missing']==3
    assert s['status_counts']=={'campaign_budget_exhausted':1}
