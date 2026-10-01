import copy
import numpy as np
import pytest
from k1lab.errors import ContractError
from k1lab.util import load_json
from k1lab.multibench.calibration import measured_target,probe_eef
from k1lab.multibench.types import Observation,StepResult


def observation():
    return Observation('probe',0,'public task',{'camera':np.zeros((2,2,3),np.uint8)},
        np.zeros(14),{arm:{'xyz':[0,0,.5],'quaternion_xyzw':[0,0,0,1],
            'gripper_opening_command':1.0} for arm in ('left','right')},25)


class Native:
    def __init__(self,wrong_ack=False):self.obs=observation();self.wrong_ack=wrong_ack
    def step(self,target,correction=False):
        assert correction
        obs=copy.deepcopy(self.obs);obs.step+=2 if self.wrong_ack else 1
        for arm,off in (('left',0),('right',8)):
            obs.eef[arm]['xyz']=target.values[off:off+3].tolist()
        self.obs=obs
        return StepResult(obs,False,False)
    def correction_reached(self,target):return True


def test_probe_is_bounded_and_robot_only(tmp_path):
    native=Native();report=probe_eef(native,native.obs,tmp_path/'probe')
    assert report['passed'] and report['actual_actions']==80
    assert [p['steps'] for p in report['phases']]==[5,25,25,25]
    assert np.allclose(measured_target(native.obs).values,measured_target(observation()).values)
    assert len(list((tmp_path/'probe').glob('ack-*.json')))==80


def test_probe_retains_failed_ack_without_retry(tmp_path):
    native=Native(wrong_ack=True)
    with pytest.raises(ContractError,match='counter'):probe_eef(native,native.obs,tmp_path/'probe')
    report=load_json(tmp_path/'probe/result.json')
    assert not report['passed'] and report['phases'][0]['steps']==1
