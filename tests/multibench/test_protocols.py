from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import httpx
import numpy as np
import pytest
from k1lab.errors import ContractError,TransportUncertain
from k1lab.util import atomic_json,file_sha,load_json,digest
from k1lab.multibench import manifest as mf
from k1lab.multibench.report import aggregate,paired,render
from k1lab.model_client import Client
from k1lab.multibench.catalog import configs,MODEL


def cases():return mf.robocasa_cases(['A','B','C','D'],{t:10 for t in 'ABCD'},2)


def test_all_17_conditions_and_four_motor_models():
    c=configs();assert len(c)==17
    assert len({x['name'] for x in c})==17
    assert all(x['no_task_memory'] and x['no_task_demonstrations'] for x in c)
    assert all(x['model']['model']=='gpt-6.1-sol' and x['model']['transport']=='responses' for x in c)
    assert sum(x['mode']=='motor_only' for x in c)==5


def test_rc_seed_formula_uses_global_registry_index():
    m=cases();last=m['cases'][-1]
    assert last['episode_seed']==7+7 and last['global_episode_index']==7
    assert m['cases'][2]['task']=='B' and m['cases'][2]['episode_seed']==9


def test_grouped_split_not_new_seed_claim():
    m=cases();splits={}
    for c in m['cases']:splits.setdefault(c['task_group'],set()).add(c['partition'])
    assert all(len(v)==1 for v in splits.values())
    assert len({c['partition'] for c in m['cases']})==2


def test_task_partition_leak_rejected():
    m=cases();m['cases'][1]['partition']='dev' if m['cases'][0]['partition']=='test' else 'test'
    with pytest.raises(ContractError):mf.check(mf.seal(m))


def test_manifest_tamper_rejected():
    m=cases();m['cases'][0]['task']='bad'
    with pytest.raises(ContractError):mf.check(m)


def test_empty_duplicate_cases_rejected():
    with pytest.raises(ContractError):mf.check(mf.seal({'cases':[]}))
    m=cases();m['cases'].append(m['cases'][0])
    with pytest.raises(ContractError):mf.check(mf.seal(m))


def public_source():
    return {'cases':[dict(case_id=f'{t}__{variant}__g0__l0',task=t,variant=variant,
       seeds={'eval_seed':0,'layout_id':0},limit=10,dt=.04,score=1.,success=True,secret='hidden')
       for t in ('taskA','taskB') for variant in ('standard','random')]}


def test_import_no_scores_recipes(tmp_path):
    p=tmp_path/'source.json';atomic_json(p,public_source());m=mf.import_robodojo(p)
    assert len(m['cases'])==4
    for c in m['cases']:assert not any(k in c for k in ('score','success','secret'))
    assert m['cases'][1]['runtime_task']=='taskA_random'
    assert m['cases'][0]['partition']==m['cases'][1]['partition']


def test_import_pairs_deduplicate_samecase(tmp_path):
    p=tmp_path/'source.json';d=public_source();d['cases']+=deepcopy(d['cases']);atomic_json(p,d)
    assert len(mf.import_robodojo(p)['cases'])==4


def test_import_disagreement_not_silently_reconciled(tmp_path):
    p=tmp_path/'source.json';d=public_source();r=deepcopy(d['cases'][0]);r['seeds']['eval_seed']=1;d['cases'].append(r);atomic_json(p,d)
    with pytest.raises(ContractError):mf.import_robodojo(p)


def test_import_sourcepanel_identity_binding(tmp_path):
    p=tmp_path/'source.json';atomic_json(p,public_source())
    q=tmp_path/'panel.json';atomic_json(q,{'cases':[{'case_id':c['case_id'],'layout':{'path':'p.json','sha256':'c'*64}} for c in public_source()['cases']]})
    m=mf.import_robodojo(p,q);assert m['formal'] and m['source_panel_sha256']==file_sha(q)
    assert m['cases'][0]['layout_sha256']=='c'*64


def test_artifacts_hash_actualbytes_and_changed(tmp_path):
    a=tmp_path/'models';a.mkdir();(a/'weights').write_bytes(b'abc');m=mf.artifacts(a)
    assert len(mf.verify_artifacts(m))==64
    (a/'weights').write_bytes(b'abd')
    with pytest.raises(ContractError):mf.verify_artifacts(m)


def test_artifacts_no_path_traversal(tmp_path):
    p=tmp_path/'weights';p.write_bytes(b'abc')
    m=mf.seal({'root':str(tmp_path/'child'),'files':{'../weights':file_sha(p)}})
    with pytest.raises(ContractError):mf.verify_artifacts(m)


def test_freeze_source_and_config_changes(tmp_path):
    (tmp_path/'k1lab').mkdir();p=tmp_path/'k1lab/a.py';p.write_text('a=1')
    m=cases();c={'name':'x','model':MODEL}
    f=mf.freeze(tmp_path,m,[c]);assert mf.verify_freeze(tmp_path,f,m,c) is None
    with pytest.raises(ContractError):mf.verify_freeze(tmp_path,f,m,c|{'foo':1})
    p.write_text('a=2')
    with pytest.raises(ContractError):mf.verify_freeze(tmp_path,f,m,c)


def test_freeze_no_duplicate_names(tmp_path):
    with pytest.raises(ContractError):mf.freeze(tmp_path,cases(),[{'name':'x'},{'name':'x'}])


def test_qualification_must_bind_native_evidence(tmp_path):
    c={'name':'x'};p=tmp_path/'native.json';p.write_text('{}')
    keys=('native_reset_render','action_space_verified','native_completion_not_vacuous','current_sensor_only_actor','policy_observation_ack_verified','controller_timing_verified')
    d={'config_sha256':digest(c),'checks':dict.fromkeys(keys,True),'evidence':[{'path':str(p),'sha256':file_sha(p)}]}
    assert mf.verify_qualification(d,c)==d
    d['checks']['native_reset_render']=False
    with pytest.raises(ContractError):mf.verify_qualification(d,c)


def row(c,condition='a',success=True,kind='synthetic'):
    return {'case_id':c['case_id'],'condition':condition,'success':success,'native_score':None,
      'elapsed_s':1.,'native_steps':10,'metrics':{'review_calls':1,'policy_calls':1},'usage':{},
      'case_sha256':digest(c),'environment_contract_sha256':'e','runtime_fingerprint':{},'policy_identity':'p',
      'planner_config':MODEL,'evidence_kind':kind}


def test_report_missing_full_denominator():
    c=cases()['cases'];r=aggregate(c,[row(c[0])],'a')
    assert r['successes']==1 and r['scheduled']==8 and r['missing']==7
    assert r['success_rate_full_denominator']==1/8 and r['score_coverage']==0
    assert r['token_totals']['input_tokens'] is None


def test_missing_whole_condition_report(tmp_path):
    c=cases()['cases'];a=render(c,[row(c[0])],tmp_path,conditions=['a','b'])
    assert a[1]['condition']=='b' and a[1]['missing']==8


def test_native_synthetic_never_mixed(tmp_path):
    c=cases()['cases']
    with pytest.raises(ContractError):render(c,[row(c[0]),row(c[1],kind='native_unqualified')],tmp_path)


def test_paired_detects_model_difference():
    c=cases()['cases'];rows=[]
    for v in c:
        x=row(v);y=row(v,'b');y['planner_config']=MODEL|{'service_tier':'default'};rows.extend([x,y])
    p=paired(c,rows,'a','b');assert not p['matched_contract'] and 'planner model/tier/config differs' in p['warnings']


def test_paired_detects_missing():
    c=cases()['cases'];p=paired(c,[row(c[0])],'a','b')
    assert not p['matched_contract']


def test_paired_complete_and_identical():
    c=cases()['cases'];p=paired(c,[row(x,cnd) for x in c for cnd in ('a','b')],'a','b')
    assert p['matched_contract'] and p['delta_success']==0


def test_duplicate_result_not_cherrypicked():
    c=cases()['cases'];r=row(c[0])
    with pytest.raises(ContractError):aggregate(c,[r,r],'a')


def req():return {'model':'gpt-6.1-sol','messages':[{'role':'user','content':'Use a tool'}],
    'tools':[{'type':'function','function':{'name':'robot_decision','parameters':{'type':'object','properties':{}},'description':'bounded'}}]}


def test_sol_responses_tier_and_usage_accounting(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','DUMMY');sent=[]
    def f(r):
        sent.append(json.loads(r.content));return httpx.Response(200,json={'status':'completed','model':'gpt-6.1-sol',
          'service_tier':'default','output':[{'type':'function_call','call_id':'t','name':'robot_decision','arguments':'{}'}],
          'usage':{'input_tokens':100,'input_tokens_details':{'cached_tokens':90},'output_tokens':10,'output_tokens_details':{'reasoning_tokens':5}}})
    with Client(MODEL,tmp_path,allow_api=True,http_client=httpx.Client(transport=httpx.MockTransport(f))) as c:
        c.post('',headers={},json=req());assert c.served_tiers==['default'] and c.output_spent==10
        assert sent[0]['service_tier']=='flex' and sent[0]['reasoning']['effort']=='medium'


@pytest.mark.parametrize('cfg',[{'transport':'chat'},{'reasoning_effort':'none'},{'reasoning_effort':'minimal'}])
def test_sol_unsupported_requests_fail_before_network(tmp_path,monkeypatch,cfg):
    monkeypatch.setenv('OPENAI_API_KEY','X');calls=[]
    c=Client(MODEL|cfg,tmp_path,allow_api=True,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:calls.append(r))))
    with pytest.raises(ContractError):c.post('',headers={},json=req())
    assert calls==[]


def test_no_flex_fallback_on_capacity(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','X');sent=[]
    def f(r):sent.append(json.loads(r.content));return httpx.Response(429,json={'error':'capacity'})
    c=Client(MODEL|{'service_tier':'flex'},tmp_path,allow_api=True,http_client=httpx.Client(transport=httpx.MockTransport(f)))
    with pytest.raises(TransportUncertain):c.post('',headers={},json=req())
    assert len(sent)==1 and sent[0]['service_tier']=='flex'


def script_module(filename):
    p=Path(__file__).resolve().parents[2]/'scripts'/'multibench'/filename
    spec=importlib.util.spec_from_file_location('test_script_'+p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_native_ready_from_json_logs_not_connection(tmp_path):
    m=script_module('launch_robodojo_case.py');p=tmp_path/'server.log'
    p.write_text('Loading GPU\nnot json\n{"event": "ready", "port": 1}\n')
    assert m.source_ready(p)
    p.write_text('{"ready":false}\n');assert not m.source_ready(p)

@pytest.mark.parametrize('field',['task_memory','exploration_memory','oracle_geometry','task_skill_library'])
def test_new_protocol_rejects_task_solution_or_oracle(field):
    with pytest.raises(ContractError):mf.resolved_config({'name':'x',field:'enabled'})

def test_launcher_keeps_virtualenv_interpreter_symlink(tmp_path):
    m=script_module('launch_robodojo_case.py')
    target=tmp_path/'system-python';target.touch()
    python=tmp_path/'venv'/'bin'/'python';python.parent.mkdir(parents=True)
    python.symlink_to(target)
    assert m.interpreter_path(python)==str(python)
    assert m.interpreter_path(python)!=str(target)


def test_new_protocol_rejects_ambiguous_memory_label():
    with pytest.raises(ContractError):mf.resolved_config({'no_task_memory':False})


def test_provider_binding_hash_changes_with_model_settings(tmp_path):
    root=tmp_path/'weights';root.mkdir();(root/'w').write_bytes(b'data')
    path=tmp_path/'artifacts.json';atomic_json(path,mf.artifacts(root))
    raw={'backend':'xpolicylab','policy':'g05','artifact_manifest':str(path),'model_config':{'frequency':30},
         'identity':{'checkpoint_sha256':None}}
    resolved=mf.resolved_config({'policy':raw})['policy'];assert len(resolved['identity']['adapter_config_sha256'])==64
    resolved['model_config']['frequency']=20
    with pytest.raises(ContractError):mf.resolved_config({'policy':resolved})


def test_unbound_remote_identity_not_allowed(tmp_path):
    root=tmp_path/'weights';root.mkdir();(root/'w').write_bytes(b'data');p=tmp_path/'a.json';atomic_json(p,mf.artifacts(root))
    with pytest.raises(ContractError):mf.resolved_config({'policy':{'backend':'remote','artifact_manifest':str(p),'identity':{'checkpoint_sha256':None}}})
