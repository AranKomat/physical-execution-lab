from copy import deepcopy
import pytest
from prl.dyna.admission import paired_gate,admission,diagnose,LAYERS
from prl.errors import ValidationError


def row(i,success,cell=0,harness=True):
    return {'identity':str(i),'case':{'suite':'goal_task','task_id':cell},
            'status':'completed','native_success':success,'contamination_flags':[],
            'attribution':{'status':'reviewed','harness_attributed':harness}}

def test_eq5_not_individual_seed_preservation():
    old=[row(0,True),row(1,False)];new=[row(0,False),row(1,True)];pi=[row(0,True),row(1,False)]
    # Same success COUNT in the protected cell is allowed by Eq5.
    assert paired_gate(old,new,pi)['decision']=='eligible_for_broader_regression'

def test_eq5_protects_policy_winning_cells():
    old=[row(0,True,0),row(1,False,1)];new=[row(0,False,0),row(1,True,1)];pi=[row(0,True,0),row(1,False,1)]
    assert paired_gate(old,new,pi)['decision']=='reject'

def test_no_promotion_from_targeted_win_only():
    gate={'decision':'eligible_for_broader_regression'}
    r=admission(gate,None,candidate_hash='abc',target_hash='abc',broad_hash='abc',required_cells=['a','b'],covered_cells=['a'])
    assert r['decision']=='reject'

def test_broader_gate_and_frozen_revision_required():
    gate={'decision':'eligible_for_broader_regression'}
    r=admission(gate,gate,candidate_hash='abc',target_hash='abc',broad_hash='abc',required_cells=['a','b'],covered_cells=['a','b'])
    assert r['decision']=='admit_offline_candidate' and not r['deployment_authorized']

def test_incomplete_attribution_blocks_admission():
    old=[row(0,False)];new=[row(0,False)];new[0]['attribution']=None
    assert paired_gate(old,new,[row(0,False)])['decision']=='reject'

def test_contamination_is_not_deleted():
    old=[row(0,False)];new=[row(0,True)];new[0]['contamination_flags']=['tick_limit']
    assert 'candidate_contamination' in paired_gate(old,new,[row(0,False)])['reasons']

def test_test_set_never_promotes():
    with pytest.raises(ValidationError):paired_gate([row(0,True)],[row(0,True)],[row(0,True)],split='test')

def test_unknown_diagnosis_is_error_not_causal_claim():
    r=diagnose([{'kind':'other','data':{}}])
    assert r['status']=='attribution_error' and r['harness_attributed'] is None

def test_ordered_thirteen_reconstruction_layers():
    assert len(LAYERS)==13
    r=diagnose([{'kind':'error','hash':'a','data':{'reason':'transport error + stale epoch'}}])
    assert r['candidate_layer']==1 and r['status']=='unreviewed'
