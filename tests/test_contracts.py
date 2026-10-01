import numpy as np
import pytest
from k1lab.contracts import Limits,parse_segment,parse_plan
from k1lab.errors import ContractError
from k1lab.util import vector,integer,canonical,sha

@pytest.mark.parametrize('value',[float('nan'),float('inf'),None,'bad',True])
def test_bad_gripper(value):
    with pytest.raises((ContractError,ValueError)):
        parse_segment({'kind':'gripper','gripper':value},Limits())

@pytest.mark.parametrize('value',[None,[1,2],[1,2,3,4],[1,2,float('inf')],[[1,2,3]]])
def test_bad_vector(value):
    with pytest.raises(ContractError):vector(value,3)

@pytest.mark.parametrize('q',[[0,0,0,0],[0,0,0,2],[0,0,float('nan'),1]])
def test_bad_quaternion(q):
    with pytest.raises(ContractError):parse_segment({'kind':'pose','target_xyz_world_m':[0,0,.5],'target_quaternion_xyzw':q},Limits())

def test_unknown_kind_and_field():
    with pytest.raises(ContractError):parse_segment({'kind':'solve_task'},Limits())
    with pytest.raises(ContractError):parse_segment({'kind':'gripper','gripper':0,'task_id':5},Limits())

def test_pose_preserves_gripper():
    with pytest.raises(ContractError):parse_segment({'kind':'pose','target_xyz_world_m':[0,0,.5],'target_quaternion_xyzw':[0,0,0,1],'gripper':0},Limits())

def test_workspace():
    with pytest.raises(ContractError):parse_segment({'kind':'pose','target_xyz_world_m':[2,0,.5],'target_quaternion_xyzw':[0,0,0,1]},Limits())

@pytest.mark.parametrize('kw',[{'max_command_steps':0},{'stall_steps':True},{'lease_s':-1},{'transit_m_s':float('nan')},{'workspace_high':[-2,-2,-2]},{'observation_period':2}])
def test_invalid_limits(kw):
    with pytest.raises(ContractError):Limits(**kw)

def test_closed_config():
    with pytest.raises(ContractError):Limits.from_dict({'secret_task_hack':1})

def test_sha_and_json():
    with pytest.raises(ContractError):sha('foo')
    with pytest.raises(ContractError):canonical({'x':float('nan')})
    assert canonical({'a':np.array([1,2])})=='{"a":[1,2]}'

def test_minimum_budget_and_count():
    p={'frame_id':0,'arm':'arm','command_id':'a','segments':[{'kind':'gripper','gripper':0,'settle_steps':10}],'max_native_steps':3}
    with pytest.raises(ContractError):parse_plan(p,Limits())
    p['max_native_steps']=150;p['segments']*=7
    with pytest.raises(ContractError):parse_plan(p,Limits())
