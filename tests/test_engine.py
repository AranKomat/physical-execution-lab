from dataclasses import replace
import numpy as np
import pytest
from k1lab.fixture import FixturePort
from k1lab.engine import ExecutionEngine
from k1lab.contracts import Limits
from k1lab.errors import ContractError


def pose(x=.10,z=.5):return {'kind':'pose','target_xyz_world_m':[x,0,z],'target_quaternion_xyzw':[0,0,0,1]}
def plan(frame=0,segments=None,budget=160,**kw):return {'frame_id':frame,'arm':'arm','command_id':'c1','segments':segments or [pose()], 'max_native_steps':budget,**kw}

def test_one_call_full_target_with_receipt():
    p=FixturePort();e=ExecutionEngine(p);r=e.execute(plan())
    assert r['motion_plan_completed'] and p.frame>1
    assert np.linalg.norm(p.xyz-[.10,0,.5])<=.004
    assert not r['native_success']

def test_rotation_is_bounded_and_held():
    p=FixturePort();e=ExecutionEngine(p)
    s=pose(.02);s['target_quaternion_xyzw']=[0,0,.70710678,.70710678]
    r=e.execute(plan(segments=[s]))
    assert r['motion_plan_completed'];assert abs(p.q[2]-.7071)<.03

def test_stale_before_motion():
    p=FixturePort();e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.execute(plan(frame=1))
    assert p.frame==0

def test_idempotency_historical_receipt():
    p=FixturePort();e=ExecutionEngine(p);a=plan();r=e.execute(a);n=p.frame
    again=e.execute(a);assert again['replayed_receipt'] and p.frame==n
    p.servo('arm',p.xyz,p.q,None)
    again=e.execute(a);assert again['receipt_is_historical']
    with pytest.raises(ContractError):e.execute(plan(segments=[pose(.2)]))

def test_stall_stops_before_closing():
    p=FixturePort(blocked=True);e=ExecutionEngine(p,Limits(stall_steps=6))
    r=e.execute(plan(segments=[pose(),{'kind':'gripper','gripper':0}]))
    assert r['stop_reason']=='pose_stagnation' and p.gripper==1 and p.frame==6

def test_terminal_capture_stops_remaining_stages():
    p=FixturePort(terminal_at=4);e=ExecutionEngine(p)
    r=e.execute(plan(segments=[pose(),{'kind':'gripper','gripper':0}]))
    assert r['native_success'] and p.frame==4 and p.gripper==1

def test_command_budget_not_renewed():
    p=FixturePort();e=ExecutionEngine(p)
    r=e.execute(plan(segments=[pose(.45)],budget=4))
    assert r['stop_reason']=='command_step_budget' and p.frame==4

def test_episode_budget_shared():
    p=FixturePort(horizon=6);e=ExecutionEngine(p)
    r=e.execute(plan(budget=100));assert p.frame==6 and r['stop_reason']=='episode_step_budget'

def test_underfunded_plan_refuses_before_action():
    p=FixturePort(horizon=4);e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.execute(plan(segments=[{'kind':'gripper','gripper':0,'settle_steps':10}]))
    assert p.frame==0

def test_overlong_plan_refuses_before_action():
    p=FixturePort();e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.execute(plan(segments=[pose(.8)]))
    assert p.frame==0

def test_lease_expiry():
    t=[0.]
    def clock():t[0]+=.2;return t[0]
    p=FixturePort();e=ExecutionEngine(p,Limits(lease_s=.1),clock=clock)
    r=e.execute(plan());assert r['stop_reason']=='command_lease_expired' and p.frame==0

def test_watch_lost():
    p=FixturePort(lost_at=3);e=ExecutionEngine(p)
    r=e.execute(plan(watch_points=['P1']))
    assert r['stop_reason']=='watched_feature_lost' and p.frame==3

def test_watch_requires_current_evidence():
    p=FixturePort();e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.execute(plan(watch_points=['invented']))
    assert p.frame==0

def test_gripper_completion_not_grasp():
    p=FixturePort();e=ExecutionEngine(p)
    r=e.execute(plan(segments=[{'kind':'gripper','gripper':0,'settle_steps':3}]))
    assert r['stages'][0]['attachment_verified'] is False and not r['native_success']

def candidate(frame=0):return {'candidate_id':'S1-Habc','frame_id':frame,'arm':'arm',
    'pregrasp_tcp_world_m':[0,0,.53],'candidate_tcp_world_m':[0,0,.5],'target_quaternion_xyzw':[0,0,0,1]}
def grasp_args():return {'frame_id':0,'arm':'arm','command_id':'g1','candidate_id':'S1-Habc','point_id':'P1','max_native_steps':160,'lift_delta_world_m':[0,0,.02]}

def test_grasp_sensor_comotion_supported_not_certified():
    p=FixturePort();e=ExecutionEngine(p);r=e.grasp(grasp_args(),candidate(),p.points())
    assert r['motion_plan_completed'];assert r['co_motion']['status']=='supported'
    assert not r['co_motion']['attachment_verified'];assert not r['native_success']

def test_grasp_failed_comotion_stops():
    p=FixturePort(point_moves=False);e=ExecutionEngine(p);r=e.grasp(grasp_args(),candidate(),p.points())
    assert r['co_motion']['status']=='contradicted' and r['stop_reason']=='co_motion_contradicted'

@pytest.mark.parametrize('mutation',[{'frame_id':1},{'arm':'other'},{'candidate_id':'bad'}])
def test_candidate_binding(mutation):
    p=FixturePort();e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.grasp(grasp_args(),candidate()|mutation,p.points())
    assert p.frame==0

def test_grasp_requires_open_jaws():
    p=FixturePort();p.gripper=0;e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.grasp(grasp_args(),candidate(),p.points())

def test_grasp_probe_not_transport():
    p=FixturePort();e=ExecutionEngine(p)
    with pytest.raises(ContractError):e.grasp(grasp_args()|{'lift_delta_world_m':[0,0,.3]},candidate(),p.points())

def test_native_no_advance_stops():
    p=FixturePort();p.servo=lambda *a:None;e=ExecutionEngine(p)
    assert e.execute(plan())['stop_reason']=='native_step_accounting_mismatch'

def test_actuator_ownership():
    p=FixturePort();e=ExecutionEngine(p);e.active=True
    with pytest.raises(ContractError):e.execute(plan())
