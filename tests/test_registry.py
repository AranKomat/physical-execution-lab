from types import SimpleNamespace
import pytest
from k1lab.k1_extension import registry_factory,extension_schemas
from k1lab.contracts import Limits
from k1lab.fixture import FixturePort
from k1lab.errors import ContractError

class Adapter(FixturePort):
    last_feedback={}
    def move_to_position(self,arm,xyz,q,gripper,steps):
        assert steps==1;return self.servo(arm,xyz,q,gripper)
class BaseRegistry:
    def __init__(self,adapter,**kw):
        self.adapter=adapter;self.waypoints={'arm':[9,9,9]}
        self.pose_targets=SimpleNamespace(active={'arm':'T1'})
        self.motion=SimpleNamespace(_record=lambda *a:None,retreat_goals={},low={})
        self.tracked_points=SimpleNamespace(context=adapter.points)
    def schemas(self,obs):return [{'function':{'name':'done'}}]
    def observe(self):return self.adapter.observe()
    def execute(self,name,args,obs):
        if name=='grasp_candidates':return {'frame_id':obs['frame_id'],'candidates':[{
            'candidate_id':'S1-Hx','target_quaternion_xyzw':[0,0,0,1],
            'pregrasp_tcp_world_m':[0,0,.53],'candidate_tcp_world_m':[0,0,.5],'score':.8}],
            'grasp_diagnostics':{'secret_rank':1}}
        return {'base':True}

def test_base_passthrough_and_no_duplicate_tools():
    R=registry_factory(base_class=BaseRegistry);r=R(Adapter());assert r.execute('done',{},r.observe())=={'base':True}
    assert [s['function']['name'] for s in r.schemas(r.observe())]==['done']

def test_extension_registry_integration():
    R=registry_factory(sparse=True,base_class=BaseRegistry);r=R(Adapter())
    a={'frame_id':0,'arm':'arm','command_id':'x','max_native_steps':50,'segments':[
        {'kind':'pose','target_xyz_world_m':[.05,0,.5],'target_quaternion_xyzw':[0,0,0,1]}]}
    result=r.execute('execute_motion_plan',a,r.observe())
    assert result['motion_plan_completed'] and not r.pose_targets.active and not r.waypoints
    assert r.adapter.last_feedback['command_id']=='x'

def test_candidate_cache_only_observed_sensor_fields():
    R=registry_factory(sparse=True,base_class=BaseRegistry);r=R(Adapter());r.execute('grasp_candidates',{'arm':'arm'},r.observe())
    c=r.extension_candidates['S1-Hx'];assert 'score' not in c and 'grasp_diagnostics' not in c
    assert c['frame_id']==0 and c['arm']=='arm'

def test_no_unknown_candidate():
    R=registry_factory(sparse=True,base_class=BaseRegistry);r=R(Adapter())
    with pytest.raises(ContractError):r.execute('grasp_from_candidate',{'candidate_id':'invented'},r.observe())

def test_existing_tool_schemas_preserved():
    R=registry_factory(sparse=True,base_class=BaseRegistry);r=R(Adapter())
    names=[s['function']['name'] for s in r.schemas(r.observe())]
    assert names==['done','execute_motion_plan','grasp_from_candidate']

def test_policy_tool_only_when_supplied():
    obs=Adapter().observe()
    names=[s['function']['name'] for s in extension_schemas(obs,Limits(),False,True)]
    assert names==['vla_act']
