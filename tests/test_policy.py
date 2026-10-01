import json
import numpy as np
import pytest
import httpx
from k1lab.policy import PolicySpec,HTTPPolicy,pack_array,unpack_array,validate_actions
from k1lab.policy_bridge import handle,decode_observation
from k1lab.fixture import FixturePort
from k1lab.engine import ExecutionEngine
from k1lab.contracts import Limits
from k1lab.errors import ContractError,Unavailable,TransportUncertain
from k1lab.util import digest


def spec():return PolicySpec('local-test','a'*64,'libero_normalized_osc7',20,('agentview','robot0_eye_in_hand'),8,
                           'rpent_pi05_libero_rgb180_256_eef_axisangle_gripper2','mock-version')
def packet():return {'frame_id':0,'subgoal':'transport test','contract':FixturePort.policy_contract,
    'images':{name:pack_array(np.zeros((256,256,3),np.uint8)) for name in FixturePort.policy_contract['cameras']},
    'state':pack_array(np.zeros(8,np.float32))}

@pytest.mark.parametrize('shape',[(0,7),(5,8),(1,5,7),(70,7)])
def test_bad_action_shape(shape):
    with pytest.raises(ContractError):validate_actions(np.zeros(shape),spec())

@pytest.mark.parametrize('value',[float('nan'),float('inf'),1.1,-2.])
def test_bad_action_value(value):
    a=np.zeros((5,7));a[0,0]=value
    with pytest.raises(ContractError):validate_actions(a,spec())

def test_array_roundtrip():
    a=np.arange(64,dtype=np.float32).reshape(8,8)
    assert np.array_equal(a,unpack_array(pack_array(a)))

def test_array_object_unsafe():
    with pytest.raises(ContractError):pack_array(np.array(['x'],object))
    with pytest.raises(ContractError):unpack_array({'dtype':'O','shape':[1],'data':'AAAA'})

def test_array_length_mismatch():
    p=pack_array(np.zeros(8,np.float32));p['shape']=[9]
    with pytest.raises(ContractError):unpack_array(p)

def test_camera_contract_mismatch():
    p=packet();p['contract']=p['contract']|{'cameras':['wrist','left','right']}
    with pytest.raises(ContractError):decode_observation(p,spec())

def test_policy_spec_not_droid_alias():
    s=PolicySpec('flux','a'*64,'droid_absolute_joint8',15,('wrist','left','right'),8,'droid','source')
    with pytest.raises(Unavailable):s.validate_port(FixturePort())

def test_policy_hz_mismatch():
    s=PolicySpec(**(spec().json()|{'control_hz':15}))
    with pytest.raises(ContractError):s.validate_port(FixturePort())

def test_bridge_exact_observation_and_response_binding():
    class Facade:
        def predict(self,o,options):
            assert o['states'].shape==(1,8) and o['main_images'].shape==(1,256,256,3)
            assert options=={'mode':'eval'}
            return np.zeros((1,5,7),np.float32)
    s=spec();request={'request_id':'r','spec_sha256':s.identity,'observation':packet()};request['request_sha256']=digest(request)
    out=handle(request,s,Facade())
    assert len(out['actions'])==5 and out['request_sha256']==request['request_sha256']
    request['observation']['subgoal']='changed'
    with pytest.raises(ContractError):handle(request,s,Facade())

def test_http_default_off():
    with pytest.raises(Unavailable):HTTPPolicy('http://127.0.0.1:8811',spec())

def test_http_no_remote_machine_control():
    with pytest.raises(ContractError):HTTPPolicy('http://example.com',spec(),allow_network=True)

def test_http_wrong_binding():
    c=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'request_id':'wrong'})))
    p=HTTPPolicy('http://127.0.0.1',spec(),allow_network=True,client=c)
    with pytest.raises(ContractError):p.predict(packet())

def test_policy_action_budget_queue_discard():
    class Provider:
        identity='mock';resets=0;calls=0
        def validate_port(self,p):spec().validate_port(p)
        def reset_segment(self):self.resets+=1
        def predict(self,p):self.calls+=1;return np.zeros((5,7),np.float32)
    p=FixturePort();e=ExecutionEngine(p);v=Provider()
    r=e.run_policy({'frame_id':0,'arm':'arm','command_id':'v','subgoal':'test','max_native_steps':8},v)
    assert p.frame==8 and v.calls==2 and v.resets==2 and r['native_steps']==8
    assert r['stop_reason']=='command_step_budget'

def test_policy_terminal_interrupts_midchunk():
    class Provider:
        identity='mock'
        def validate_port(self,p):spec().validate_port(p)
        def reset_segment(self):pass
        def predict(self,p):return np.zeros((5,7),np.float32)
    p=FixturePort(terminal_at=2);e=ExecutionEngine(p)
    r=e.run_policy({'frame_id':0,'arm':'arm','command_id':'v','subgoal':'test','max_native_steps':8},Provider())
    assert r['native_success'] and p.frame==2

def test_policy_no_implicit_geometric_rescue():
    class Broken:
        identity='mock'
        def validate_port(self,p):pass
        def reset_segment(self):pass
        def predict(self,p):raise RuntimeError('inference failed')
    p=FixturePort();r=ExecutionEngine(p).run_policy({'frame_id':0,'arm':'arm','command_id':'v','subgoal':'test','max_native_steps':8},Broken())
    assert p.frame==0 and 'policy_exception' in r['stop_reason']
