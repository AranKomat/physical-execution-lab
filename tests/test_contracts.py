import dataclasses,json,math
import pytest
from prl.contracts import Proposal,Case,Target
from prl.util import digest,finite,integer,safe_id,read_json,atomic_json
from prl.errors import ValidationError

BASE=dict(proposal_id='episode:d0',observation_id='episode:0',capability='observe',arguments={},max_steps=0)

@pytest.mark.parametrize('value',[float('nan'),float('inf'),-float('inf'),True,'2',None])
def test_finite_rejects(value):
    with pytest.raises(ValidationError):finite(value,'x')

@pytest.mark.parametrize('value',[-1,True,1.1,'3',None])
def test_integer_rejects(value):
    with pytest.raises(ValidationError):integer(value,'n')

@pytest.mark.parametrize('value',['../escape','x/y','',None,'x\nq','.','..'])
def test_identifier_rejects(value):
    with pytest.raises(ValidationError):safe_id(value)

@pytest.mark.parametrize('patch',[{'max_steps':True},{'max_steps':2001},{'arguments':[]},
 {'unexpected':1},{'alternatives':[{'capability':'x'}]},
 {'arguments':{'x':float('nan')}},{'decision_summary':'x'*2001},
 {'proposal_id':'../secret'}])
def test_proposal_rejects(patch):
    with pytest.raises(ValidationError):Proposal.from_dict({**BASE,**patch})

def test_proposal_roundtrip():
    x=Proposal.from_dict(BASE);assert x.capability=='observe'
    assert digest(x)==digest(dataclasses.asdict(x))

def test_case_requires_content_hash(case):
    d=dataclasses.asdict(case);d['state_sha256']='seed-0'
    with pytest.raises(ValidationError):Case.from_dict(d)

def test_target_frame_validation():
    with pytest.raises(ValidationError):Target('p',(0,0,0),'sensor','surface',0,frame='camera')

def test_json_nan_rejected(tmp_path):
    p=tmp_path/'x.json';p.write_text('{"x":NaN}')
    with pytest.raises(ValidationError):read_json(p)

def test_atomic_json(tmp_path):
    p=tmp_path/'nested/x.json';atomic_json(p,{'x':2});assert read_json(p)=={'x':2}
