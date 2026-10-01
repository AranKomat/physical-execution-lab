import dataclasses
import pytest
from prl.contracts import Proposal,Target
from prl.registry import Registry
from prl.errors import ValidationError,Unavailable,UncertainExecution,NativeTerminal
from prl.governor import GovernorConfig
from prl.util import norm,sub

def action(b,name,args,steps=100,pid='p0'):
    return Proposal(pid,b.observe().observation_id,name,args,steps)

def test_actor_does_not_leak_evaluator(runtime):
    b,g,j=runtime
    s=str(b.observe().actor_view())
    assert 'native_success' not in s and 'blocked' not in s and 'attached' not in s

def test_success_latched_no_further_motion(runtime):
    b,g,j=runtime
    p=action(b,'pick_place',{'target':'block','destination':'destination'},240)
    r=g.execute(p);assert b.native_success and g.terminal
    n=b.steps;g.execute(action(b,'set_gripper',{'gripper':1},10,pid='late'))
    assert b.steps==n and r.reason=='native_success'

def test_idempotency_no_second_execution(runtime):
    b,g,j=runtime;p=action(b,'set_gripper',{'gripper':-1,'steps':4})
    a=g.execute(p);n=b.steps;assert g.execute(p)==a and b.steps==n
    with pytest.raises(ValidationError):g.execute(dataclasses.replace(p,arguments={'gripper':1}))

def test_stale_observation_refuses(runtime):
    b,g,j=runtime;p=action(b,'set_gripper',{'gripper':1},5)
    g.execute(action(b,'set_gripper',{'gripper':-1,'steps':1},1,pid='first'))
    n=b.steps;r=g.execute(p);assert r.reason=='stale_observation' and n==b.steps

def test_strict_global_budget(runtime):
    b,g,j=runtime;g.budget.max_steps=13
    r=g.execute(action(b,'vla',{},100));assert b.steps==13 and not b.native_success
    assert r.reason=='episode_step_budget'

def test_command_budget_counts_native_actions(runtime):
    b,g,j=runtime;r=g.execute(action(b,'vla',{},7));assert b.steps==7
    assert r.reason=='command_step_budget'

def test_gripper_close_not_success(runtime):
    b,g,j=runtime;r=g.execute(action(b,'set_gripper',{'gripper':1,'steps':1},1))
    assert r.status=='unverified' and r.effect_verified is None and not b.native_success

def test_finish_never_success(runtime):
    b,g,j=runtime;r=g.execute(action(b,'finish',{},0))
    assert r.status=='unverified' and not b.native_success and b.steps==0

def test_analytic_motion_completion_not_object_success(runtime):
    b,g,j=runtime;r=g.execute(action(b,'move_to',{'target':'safe_stage'}))
    assert r.status=='unverified' and r.effect_verified is None

def test_stagnation(runtime):
    b,g,j=runtime;b.blocked=True
    r=g.execute(action(b,'move_to',{'target':'block'},100))
    assert r.reason=='stagnation' and b.steps<100
    assert any(e.get('kind')=='stagnation' for e in r.events)

def test_nominal_stall_consumes_more_steps(runtime):
    b,g,j=runtime;b.blocked=True;g.config=GovernorConfig(dynamic=False)
    r=g.execute(action(b,'move_to',{'target':'block'},100))
    assert r.reason=='target_not_reached' and b.steps==100

def test_no_vla_metric_is_not_made_up(runtime):
    b,g,j=runtime;r=g.execute(action(b,'vla',{},30));j.close()
    rows=j.verify(j.path);m=[e['data'] for e in rows if e['kind']=='monitor']
    assert m and all(e['progress']=='unavailable' for e in m)

def test_future_target_rejected(runtime):
    b,g,j=runtime;b.extra_targets['future']=Target('future',(0,0,.2),'synthetic','surface',9)
    r=g.execute(action(b,'move_to',{'target':'future'}));assert 'future_target' in r.reason

def test_stale_target_dynamic(runtime):
    b,g,j=runtime;b.steps=100;b.revision=100
    b.extra_targets['old']=Target('old',(0,0,.2),'synthetic','surface',0)
    r=g.execute(action(b,'move_to',{'target':'old'}));assert 'stale_target' in r.reason

def test_no_privilege_in_sensor_profile(runtime):
    b,g,j=runtime;o=b.observe();o.source='sensor'
    with pytest.raises(ValidationError):g.registry.resolve('block',o)

def test_unresolved_target(runtime):
    b,g,j=runtime;r=g.execute(action(b,'move_to',{'target':'absent'}))
    assert 'unresolved_target' in r.reason and b.steps==0

def test_substitution_same_effect_allowed(runtime):
    b,g,j=runtime
    p=action(b,'pick',{'target':'absent','executor':'analytic'},20)
    p=dataclasses.replace(p,alternatives=({'capability':'pick','arguments':{'target':'absent','executor':'vla'}},))
    r=g.execute(p);assert any(x['kind']=='substitution' for x in r.events)
    assert g.budget.vla_calls>0

def test_wrong_target_substitution_refused(runtime):
    b,g,j=runtime;p=action(b,'pick',{'target':'block'},20)
    p=dataclasses.replace(p,alternatives=({'capability':'pick','arguments':{'target':'destination','executor':'vla'}},))
    r=g.execute(p);assert r.status=='refused' and r.reason=='alternative_changes_semantic_effect'

def test_no_substitution_nominal(runtime):
    b,g,j=runtime;g.config=GovernorConfig(dynamic=False)
    p=action(b,'pick',{'target':'absent'},20)
    p=dataclasses.replace(p,alternatives=({'capability':'pick','arguments':{'target':'absent','executor':'vla'}},))
    r=g.execute(p);assert not r.events and g.budget.vla_calls==0

def test_uncertain_write_poison(runtime,monkeypatch):
    b,g,j=runtime
    def fail(stage):raise UncertainExecution('no_receipt')
    monkeypatch.setattr(b,'execute_stage',fail)
    with pytest.raises(UncertainExecution):g.execute(action(b,'set_gripper',{'gripper':1}))
    assert g.poisoned
    with pytest.raises(UncertainExecution):g.execute(action(b,'set_gripper',{'gripper':1},pid='later'))

def test_native_action_range_rejected(runtime):
    b,g,j=runtime;g.command_budget=10
    with pytest.raises(ValidationError):g.before_step([2,0,0,0,0,0,0])

def test_actuator_owner(runtime):
    b,g,j=runtime;g.busy=True
    with pytest.raises(ValidationError):g.execute(action(b,'observe',{},0))

def test_long_move_segmented_both_modes(runtime):
    b,g,j=runtime;b.extra_targets['far']=Target('far',(.7,0,.35),'synthetic','point',0)
    for mode in (True,False):
        stages=g.registry.compile('move_to',{'target':'far'},b.observe(),100,dynamic=mode)
        assert len(stages)==3
        prev=b.eef
        for s in stages:assert norm(sub(s.progress_target,prev)[:2])<=.24001;prev=s.progress_target

@pytest.mark.parametrize('args',[{'target':'block','offset':[2,0,0]}, {'target':'block','surprise':True},
 {'target':'block','step_clip':1}, {'target':'block','tol':0}])
def test_invalid_parameters(runtime,args):
    b,g,j=runtime;r=g.execute(action(b,'move_to',args));assert r.status=='refused' and b.steps==0
