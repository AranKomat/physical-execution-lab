import math
import time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from prl.dyna.protocol import PaperSettings,suite_budget,REFERENCE_RESULTS
from prl.dyna.scene import Entity,Articulation,ExecutionMemory
from prl.dyna.capabilities import PaperLibrary,Refusal,CONTACT,RECOVERY,destination_position,corridor_height,top_down
from prl.dyna.engine import Engine,VerdictLatch,CommandFailure
from prl.dyna.planner import Advisory,Plan,decode_plan,context_for
from prl.dyna.fixture import FixtureBackend,FixturePlanner
from prl.journal import Journal
from prl.errors import ValidationError

@pytest.mark.parametrize('name,expected', [('libero_goal_task',300),('libero_goal_swap',300),
 ('libero_10_task',520),('libero_10_swap',520),('libero_spatial_task',220),('libero_object_swap',280)])
def test_paper_suite_budgets(name,expected):assert suite_budget(name)==expected

def test_unknown_suite_not_silently_long():
    with pytest.raises(ValidationError):suite_budget('not_libero')

def test_table4_cost_is_accounted():assert PaperSettings().pick_place_cost==211

def test_source_results_are_separate_blocks():
    assert REFERENCE_RESULTS['development']['bare']==130
    assert REFERENCE_RESULTS['new_states_C']['bare']==140
    assert REFERENCE_RESULTS['development']['A2ctrl']==592

@pytest.mark.parametrize('field,value',[('control_hz',0),('governor_hz',3),('max_ticks',0),('command_lease_s',-1),('serialization_repairs',2)])
def test_settings_reject_bad_bounds(field,value):
    with pytest.raises(ValidationError):PaperSettings(**{field:value})

@pytest.mark.parametrize('enabled,expected',[(True,True),(False,False)])
def test_transient_completion_separate_from_schedule(enabled,expected):
    latch=VerdictLatch(enabled)
    for i in range(1,11):latch.sample(i==4,i)
    assert latch.read()==expected
    assert latch.first_success_step==4 and latch.samples==10


def make_scene():return FixtureBackend().scene()

def test_symbolic_actor_cannot_see_geometry_or_predicate():
    s=make_scene();text=str(s.symbolic_view())
    assert 'half_size' not in text and 'native_success' not in text
    assert 'state_index' not in text and 'finger_contacts' not in text
    assert 'block' in text and 'privileged_sim' not in text

@pytest.mark.parametrize('name,args',[
 ('pick_and_place',{'object':'block','destination':'tray','offset':[1,2,3]}),
 ('slide_drawer',{'object':'handle','state':'open','distance':.2}),
 ('turn_knob',{'object':'knob','state':1}),
 ('vla_act',{'instruction':{'task':'x'}})])
def test_numeric_slow_brain_rejected(name,args):
    with pytest.raises(ValidationError):PaperLibrary().validate(name,args)

def test_grounding_private_geometry():
    s=make_scene();m=ExecutionMemory();lib=PaperLibrary()
    c=lib.ground('pick_and_place',{'object':'block','destination':'tray'},s,m,300)
    assert c.expected_steps==230
    assert [p.name for p in c.phases]==['approach','guarded_descent','close','lift','corridor_climb','corridor','lower','release','retreat']
    assert c.effect['goal_xyz'][2]==pytest.approx(.054)

def test_affordability_preflight_moves_nothing():
    b=FixtureBackend();lib=PaperLibrary()
    with pytest.raises(Refusal,match='cannot_afford_completion'):
        lib.ground('pick_and_place',{'object':'block','destination':'tray'},b.scene(),ExecutionMemory(),229)
    assert b.steps==0

def test_flat_hob_is_not_cavity():
    s=make_scene();s.entities['hob']=Entity('hob',(.1,0,.02),(.1,.1,.0025),kind='region',
        source='synthetic',attributes={'region_type':'cavity'})
    with pytest.raises(Refusal,match='height'):
        destination_position(s,s.entities['block'],s.entities['hob'],'in',ExecutionMemory(),.03)

def test_fixture_without_cavity_not_inferred():
    s=make_scene()
    with pytest.raises(Refusal,match='cavity'):
        destination_position(s,s.entities['block'],s.entities['tray'],'in',ExecutionMemory(),.03)

def test_receptacle_selects_unoccupied_slot():
    s=make_scene();s.entities['basket']=Entity('basket',(.15,0,.1),(.1,.1,.06),kind='region',source='synthetic',attributes={'region_type':'receptacle'})
    s.entities['occupied']=Entity('occupied',(.15,0,.065),(.02,.02,.02),source='synthetic')
    p=destination_position(s,s.entities['block'],s.entities['basket'],'in',ExecutionMemory(),.03)
    assert abs(p[0]-.15)>.04 or abs(p[1])>.04

def test_push_substitution_preserves_final_relation():
    s=make_scene();s.entities['block']=replace(s.entities['block'],attributes={'push_contact_span_m':.15})
    with pytest.raises(Refusal) as ex:
        PaperLibrary().ground('push_object',{'object':'block','destination':'tray','relation':'front_of'},s,ExecutionMemory(),300)
    a=ex.value.alternatives[0]
    assert a['capability']=='pick_and_place' and a['arguments']['relation']=='front_of'

def test_push_only_constraint_disallows_carry():
    s=make_scene();s.entities['block']=replace(s.entities['block'],attributes={'push_contact_span_m':.15})
    with pytest.raises(Refusal) as ex:
        PaperLibrary().ground('push_object',{'object':'block','destination':'tray','method_constraint':'push_only'},s,ExecutionMemory(),300)
    assert ex.value.alternatives==()

def test_sensor_track_rejects_sim_geometry():
    s=make_scene();s.information_profile='sensor'
    with pytest.raises(ValidationError):s.entity('block')

def test_stale_geometry_refused():
    s=make_scene();s.step=100
    with pytest.raises(Refusal.__bases__[0],match='stale'):s.entity('block')

def test_keyframe_is_episode_scoped():
    m=ExecutionMemory();s=make_scene();m.record_keyframe('home',s)
    assert m.keyframe('home',s)['xyz']==s.eef_xyz
    s.scene_epoch+=1
    with pytest.raises(Refusal.__bases__[0],match='epoch'):m.keyframe('home',s)

@pytest.mark.parametrize('arm', ['no_contact','no_groups'])
def test_contact_removal_catalog_enforced(arm):
    lib=PaperLibrary(arm=arm)
    assert not set(CONTACT)&set(lib.names)
    with pytest.raises(Refusal):lib.validate('pick_and_place',{'object':'block','destination':'tray'})

@pytest.mark.parametrize('arm',['no_recovery','no_groups'])
def test_recovery_removal_enforced(arm):assert not set(RECOVERY)&set(PaperLibrary(arm=arm).names)

def test_all_nominal_dynamic_skills_identical():assert PaperLibrary(arm='A2ctrl').fingerprint==PaperLibrary(arm='A2static').fingerprint

def test_vla_removed_from_catalog():assert 'vla_act' not in PaperLibrary(arm='no_vla').names

def test_drawer_recipe_and_source_shift():
    s=make_scene();s.entities['handle']=Entity('handle',(0,.15,.1),(.035,.008,.008),kind='handle',source='synthetic')
    s.articulations['drawer']=Articulation('drawer','cabinet','handle','slide',(0,0,.1),(0,-1,0),0,-.2,0,-.2,0,source='synthetic')
    c=PaperLibrary().ground('slide_drawer',{'object':'drawer','state':'open'},s,ExecutionMemory(),300)
    assert c.expected_steps==239
    assert c.initial['grasp_xyz'][0]==pytest.approx(.02)

@pytest.mark.parametrize('cap',['turn_knob','swing_door','handle_turn'])
def test_hinge_capabilities_have_real_arc_phases(cap):
    s=make_scene();s.entities['knob']=Entity('knob',(0,.15,.1),(.02,.008,.008),kind='handle',source='synthetic')
    s.articulations['joint']=Articulation('joint','stove','knob','hinge',(0,.1,.1),(0,0,1),0,0,1.57,1.57,0,source='synthetic')
    c=PaperLibrary().ground(cap,{'object':'joint','state':'open'},s,ExecutionMemory(),300)
    assert any(p.kind=='arc' for p in c.phases)
    assert c.initial['desired']==1.57

def test_no_grasp_from_jaw_width_alone():
    s=make_scene();lib=PaperLibrary();m=ExecutionMemory()
    c=lib.ground('pick_and_place',{'object':'block','destination':'tray'},s,m,300)
    s.gripper_width=.03
    ok,_=lib.verify(c,c.phases[3],s,m)
    assert not ok and m.held_object is None

def test_no_grasp_from_contacts_without_lift():
    s=make_scene();lib=PaperLibrary();m=ExecutionMemory();c=lib.ground('pick_and_place',{'object':'block','destination':'tray'},s,m,300)
    s.finger_contacts={'block':(True,True)}
    assert not lib.verify(c,c.phases[3],s,m)[0]

def test_pick_completion_records_object_to_tcp():
    s=make_scene();lib=PaperLibrary();m=ExecutionMemory();c=lib.ground('pick_and_place',{'object':'block','destination':'tray'},s,m,300)
    s.entities['block']=replace(s.entities['block'],xyz=(-.1,0,.18));s.finger_contacts={'block':(True,True)}
    ok,_=lib.verify(c,c.phases[3],s,m)
    assert ok and m.held_object=='block' and m.object_to_tcp.shape==(3,)

@pytest.mark.parametrize('sequence',[False,True])
def test_symbolic_plan_decode(sequence):
    c=context_for(make_scene(),PaperLibrary(),ExecutionMemory(),300,'req',sequence=sequence)
    x={'capability':'pick_and_place','arguments':{'object':'block','destination':'tray'}}
    plan=decode_plan({'steps':[x]} if sequence else x,c)
    assert plan.steps[0].capability=='pick_and_place'

def test_symbolic_plan_no_numeric_coordinates():
    c=context_for(make_scene(),PaperLibrary(),ExecutionMemory(),300,'req')
    with pytest.raises(ValidationError):decode_plan({'capability':'pick_and_place','arguments':{'object':'block','destination':[1,2,3]}},c)

@pytest.mark.parametrize('arm',['A2static','A2seq','A2ctrl'])
def test_full_geometry_pipeline_runs_in_fixture(arm,tmp_path):
    b=FixtureBackend();p=FixturePlanner();j=Journal(tmp_path/'events.jsonl')
    e=Engine(b,p,j,arm=arm,out=tmp_path,budget=300);r=e.run();j.close()
    assert r['native_success'] and r['native_steps']<=300
    assert r['safety_checks']>r['native_steps']
    if arm in ('A2static','A2seq'):
        assert r['failure_replans']==0 and r['substitutions']==0 and r['recovery_insertions']==0
    if arm=='A2seq':assert p.calls==1

def test_fixed_failure_does_not_call_planner_again(tmp_path):
    # Use a budget large enough for four whole groundings. The arm is deliberately
    # stalled so the comparison concerns retry semantics, not physical competence.
    b=FixtureBackend(blocked=True);p=FixturePlanner();j=Journal(tmp_path/'events.jsonl')
    e=Engine(b,p,j,arm='A2static',budget=1000,out=tmp_path);r=e.run();j.close()
    assert not r['native_success'] and p.calls==1
    assert r['fixed_retries']==2 and r['fixed_replays']==1
    assert r['failure_replans']==0 and r['reason']=='fixed_retry_exhaustion'

def test_idempotency_does_not_repeat_robot_action(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl');e=Engine(b,FixturePlanner(),j,out=tmp_path)
    a=Advisory('perception',{})
    one=e.execute(a,'same');two=e.execute(a,'same')
    assert one==two and b.steps==0
    with pytest.raises(ValidationError):e.execute(Advisory('release_and_retreat',{}),'same')
    j.close()

def test_measured_velocity_guard(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl');e=Engine(b,None,j)
    s=b.scene();s.joint_velocity=(2.1,)
    with pytest.raises(CommandFailure,match='velocity'):e.safety_check(s)
    j.close()

def test_command_lease_guard(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl');e=Engine(b,None,j)
    e.deadline=time.monotonic()-1
    with pytest.raises(CommandFailure,match='lease'):e.safety_check(b.scene())
    j.close()

def test_exact_10_action_policy_chunks(tmp_path):
    b=FixtureBackend();b.policy_actions=lambda _:np.zeros((5,7))
    j=Journal(tmp_path/'events.jsonl');e=Engine(b,None,j,arm='bare',out=tmp_path)
    with pytest.raises(ValidationError,match='10_action'):e.run()
    j.close()

def test_insufficient_remainder_routes_to_vla_not_endless_refusals(tmp_path):
    b=FixtureBackend(blocked=True);p=FixturePlanner();j=Journal(tmp_path/'events.jsonl')
    e=Engine(b,p,j,arm='A2ctrl',budget=300,out=tmp_path);r=e.run();j.close()
    assert r['planner_calls']<10 and r['vla_calls']>0 and r['native_steps']==300

def test_safety_and_governor_clocks_are_separate(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl');e=Engine(b,None,j,arm='bare',budget=40,out=tmp_path)
    r=e.run();j.close()
    assert r['fast_decisions']==4
    assert r['safety_checks']==100
    assert r['pre_action_checks']==40

def test_executor_step_share_accounts_every_action(tmp_path):
    b=FixtureBackend();j=Journal(tmp_path/'events.jsonl')
    e=Engine(b,FixturePlanner(),j,out=tmp_path);result=e.run();j.close()
    assert sum(result['steps_by_executor'].values())==result['native_steps']
    assert result['steps_by_executor']['analytic']>0
    assert result['steps_by_executor']['policy']==0
