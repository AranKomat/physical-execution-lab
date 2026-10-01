"""Mocked RPent contract tests. These do NOT import/execute the real simulator."""
import numpy as np
import pytest
from prl.backends.rpent import CheckedEnv,MeteredPolicy,RPentBackend,state_fingerprint,load_rpent
from prl.errors import ValidationError,NativeTerminal,UncertainExecution,Unavailable

class Env:
    terminated=False;truncated=False
    def __init__(self,terminal_at=100,fail_at=None):self.calls=0;self.terminal_at=terminal_at;self.fail_at=fail_at
    def reset(self):return {'states':np.zeros(8)},{}
    def step(self,a):
        self.calls+=1
        if self.calls==self.fail_at:raise ConnectionError('broken')
        self.terminated=self.calls>=self.terminal_at
        return {'states':np.zeros(8)},0,self.terminated,False,{}
class Owner:
    def __init__(self):self.steps=0;self.native_success=False;self.native_truncated=False;self.before_calls=0;self.after_calls=0
    def before(self,a):self.before_calls+=1
    def after(self,o,a):
        self.after_calls+=1
        if self.native_success:raise NativeTerminal(True)
    def observe(self):return {'steps':self.steps}

def test_chunk_each_step_intercepted():
    e=Env();o=Owner();x=CheckedEnv(e,o);x.reset()
    obs,_,_,_,_=x.chunk_step(np.zeros((7,7)))
    assert len(obs)==7 and o.before_calls==o.after_calls==e.calls==7

def test_terminal_does_not_finish_chunk():
    e=Env(terminal_at=3);o=Owner();x=CheckedEnv(e,o);x.reset()
    with pytest.raises(NativeTerminal):x.chunk_step(np.zeros((10,7)))
    assert e.calls==3 and x.last_obs is not None and o.steps==3

def test_uncertain_native_write_never_retried():
    e=Env(fail_at=2);o=Owner();x=CheckedEnv(e,o);x.reset()
    with pytest.raises(UncertainExecution):x.chunk_step(np.zeros((10,7)))
    assert e.calls==2 and o.steps==1

def test_env_second_reset_forbidden():
    x=CheckedEnv(Env(),Owner());x.reset()
    with pytest.raises(ValidationError):x.reset()

@pytest.mark.parametrize('shape',[(7,),(1,8),(0,7),(1,1,7)])
def test_bad_vla_shapes(shape):
    x=CheckedEnv(Env(),Owner());x.reset()
    with pytest.raises(ValidationError):x.chunk_step(np.zeros(shape))

def test_state_fingerprint_exact():
    assert state_fingerprint(np.array([1.,2.]))!=state_fingerprint(np.array([1.,2.],dtype=np.float32))
    assert state_fingerprint(np.array([1.,2.]))==state_fingerprint(np.array([1.,2.]))

def test_missing_rpent_is_explicit(tmp_path):
    with pytest.raises(Unavailable):load_rpent(tmp_path/'none')

def test_after_interrupt_primitive_obs_is_synced():
    b=RPentBackend.__new__(RPentBackend);b.native_success=False;b.native_truncated=False
    b.env=type('E',(),{'last_obs':{'latest':True}})()
    class P:
        def set_gripper(self,**kwargs):raise NativeTerminal(True)
        def set_obs(self,o):self.updated=o
    b.primitives=P()
    from prl.contracts import Stage
    with pytest.raises(NativeTerminal):b.execute_stage(Stage('set_gripper',{'gripper':1,'steps':5},5))
    assert b.primitives.updated=={'latest':True}

def test_initial_cached_reset_reused():
    e=Env();e.last_obs={'states':np.ones(8)}
    e.reset=lambda:(_ for _ in ()).throw(AssertionError('Unnecessary second reset'))
    x=CheckedEnv(e,Owner());obs,_=x.reset()
    assert obs is e.last_obs
