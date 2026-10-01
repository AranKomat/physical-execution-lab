import json
from pathlib import Path
import pytest
from k1lab.journal import Journal,verify
from k1lab.errors import ContractError,Unavailable
from k1lab.util import atomic_json,file_sha,digest
from k1lab.runner import validate_config,source_hash
from k1lab.qualification import config_identity,verify_freeze
from k1lab.manifests import seal
from k1lab.synthetic import run


def test_journal_roundtrip_and_tamper(tmp_path):
    p=tmp_path/'journal.jsonl'
    with Journal(p) as j:j.append('one',{'x':1});j.append('two',{'x':2})
    assert verify(p)['events']==2
    p.write_text(p.read_text().replace('"x": 1','"x": 9'))
    with pytest.raises(ContractError):verify(p)

def test_fresh_journal_only(tmp_path):
    with Journal(tmp_path/'j') as j:pass
    with pytest.raises(FileExistsError):Journal(tmp_path/'j')

def config():return {'condition':'k1_sparse','model':'test','memory_scope':'current_episode_only','planner':{}}

@pytest.mark.parametrize('field',['memory_dir','task_memory','exploration_memory','oracle_geometry','task_skill_library'])
def test_no_task_memory_config(field):
    with pytest.raises(ContractError):validate_config(config()|{field:'bad'})

def test_no_vla_in_pure_harness_comparison():
    with pytest.raises(ContractError):validate_config(config()|{'policy':{'foo':1}})

def test_no_unset_model():
    with pytest.raises(ContractError):validate_config(config()|{'model':'SET_MODEL_ID'})

def test_freeze_rejects_config_drift(tmp_path):
    c=config();m=seal({'format':1,'cases':[]});p=tmp_path/'freeze.json'
    atomic_json(p,{'source_sha256':source_hash(),'manifest_sha256':m['sha256'],'actor_memory_scope':'current_episode_only',
                   'configs':{'k1_sparse':config_identity(c)}})
    c.update(freeze_manifest_path=str(p),freeze_manifest_sha256=file_sha(p));verify_freeze(c,m)
    c['model']='different'
    with pytest.raises(ContractError):verify_freeze(c,m)

def test_synthetic_pipeline_labels_and_archive(tmp_path):
    out=tmp_path/'run';r=run(out)
    assert r['episodes']==8 and r['status']=='synthetic_software_test_only'
    assert 'SYNTHETIC SOFTWARE CHECK' in (out/'report.html').read_text()
    comparison=json.loads((out/'comparison.json').read_text())
    assert comparison['difference_pp']==0  # no invented accuracy gain
    for p in out.rglob('events.jsonl'):assert verify(p)['events']>0
    with pytest.raises(FileExistsError):run(out)


def test_no_completion_query_oracle():
    with pytest.raises(ContractError,match="completion queries"):
        validate_config(config()|{'registry_options':{'completion_feedback':True}})
