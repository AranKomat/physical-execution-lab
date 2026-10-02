import importlib.util
from pathlib import Path
import json
import pytest
from k1lab.errors import ContractError
from k1lab.util import digest, atomic_json, file_sha
from k1lab.multibench.manifest import seal
from semantic_lab import protocol
from semantic_lab.cli import configurations


def manifest():
    return seal({'cases': [dict(case_id='a', task='x', task_group='x', benchmark='synthetic', partition='dev')]})


def test_freeze_binds_semantic_source_not_just_legacy(tmp_path):
    (tmp_path/'semantic_lab').mkdir(); (tmp_path/'semantic_lab/a.py').write_text('a=1')
    cfg = {'name': 'cfg'}; doc = protocol.freeze(tmp_path, manifest(), [cfg])
    (tmp_path/'semantic_lab/a.py').write_text('a=2')
    with pytest.raises(ContractError): protocol.verify(tmp_path, doc, manifest(), cfg, {})


def test_old_motor_qualification_does_not_transfer(tmp_path):
    cfg={'name':'cfg'}; doc=protocol.freeze(tmp_path, manifest(), [cfg])
    with pytest.raises(ContractError): protocol.verify(tmp_path, doc, manifest(), cfg, {'config_sha256':digest(cfg)})


def test_new_qualification_requires_tokenizer_evidence(tmp_path):
    cfg={'name':'cfg'}; doc=protocol.freeze(tmp_path, manifest(), [cfg])
    artifact=tmp_path/'evidence.json'; artifact.write_text('{}')
    q={'schema':'semantic.qualification.v1','source_sha256':doc['source_sha256'], 'config_sha256':digest(cfg),
       'checks':{key:True for key in ('native_motor_only_parity','effective_prompt_seen_at_model_boundary',
               'continue_preserves_cadence','context_switch_preserves_ack_history','native_terminal_scoring_separate',
               'source_bound_model_identity')}, 'evidence':[{'path':str(artifact),'sha256':file_sha(artifact)}]}
    with pytest.raises(ContractError): protocol.verify(tmp_path,doc,manifest(),cfg,q)
    q['checks']['tokenizer_subtask_not_truncated']=True
    assert protocol.verify(tmp_path,doc,manifest(),cfg,q)
    artifact.write_text('changed')
    with pytest.raises(ContractError): protocol.verify(tmp_path,doc,manifest(),cfg,q)


def test_prepare_preserves_provider_and_route_no_old_shortening():
    c={'name':'old','benchmark':'robodojo','policy':{'identity':{'name':'pi05'},'endpoint':'http://127.0.0.1:1'},
       'model':{'model':'user-model','service_tier':'flex','base_url':'http://127.0.0.1:9999'},
       'monitor':{'max_unreviewed_steps':50},'max_decision_steps':15,
       'paid_route':{'trial_call_limit':180,'local_cap_usd':'3','trial_profile':'comparison180'}}
    rows=configurations(c,11)
    assert len(rows)==4 and len({r['name'] for r in rows})==4
    for r in rows:
        assert r['policy']==c['policy'] and r['model']['model']=='user-model'
        assert r['model']['base_url']==c['model']['base_url']
        assert r['model']['max_requests']==11 and 'monitor' not in r and 'max_decision_steps' not in r
        assert 'paid_route' not in r  # old reviewer budgets are not semantic authorizations
    assert c['monitor']  # no mutation of source


def installer():
    path=Path(__file__).parents[2]/'scripts/semantic/apply_overlay.py'
    spec=importlib.util.spec_from_file_location('_installer_test',path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def test_overlay_no_overwrite_and_no_base_copy(tmp_path):
    m=installer(); src=tmp_path/'src'; dst=tmp_path/'dst'
    (src/'semantic_lab').mkdir(parents=True); (dst/'k1lab/multibench').mkdir(parents=True)
    f=src/'semantic_lab/a.py'; f.write_text('safe')
    atomic_json(src/'OVERLAY_V5.json',{'files':{'semantic_lab/a.py':file_sha(f)}})
    rows=m.plan(src,dst); assert len(rows)==2 and rows[0][2]
    (dst/'semantic_lab').mkdir(); (dst/'semantic_lab/a.py').write_text('different')
    with pytest.raises(FileExistsError): m.plan(src,dst)


def test_overlay_rejects_legacy_and_path_escape(tmp_path):
    m=installer(); src=tmp_path/'src'; dst=tmp_path/'dst';src.mkdir();(dst/'k1lab/multibench').mkdir(parents=True)
    for rel in ('k1lab/multibench/runner.py','semantic_lab/../../escape.py'):
        atomic_json(src/'OVERLAY_V5.json',{'files':{rel:'a'*64}})
        with pytest.raises((ValueError,FileNotFoundError)): m.plan(src,dst)


def test_native_refuses_bundled_baseline_without_false_qualification(tmp_path):
    with pytest.raises(ContractError): protocol.require_live_base(tmp_path)
