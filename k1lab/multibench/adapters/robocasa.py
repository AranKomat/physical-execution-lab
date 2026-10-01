"""Use Xiaomi's actual RoboCasa365 evaluator preprocessing and official converter.

Only inference scheduling/correction is replaced; no replacement task definitions.
Native experiments must qualify the installed simulator/controller/assets first.
"""
from __future__ import annotations
import collections
import importlib.util
from pathlib import Path
import uuid
import numpy as np
from ..types import Observation,Action,Proposal,PolicyIdentity,StepResult
from k1lab.errors import ContractError
from .robodojo import check_checkout

XR_REV='0dd7aef8dc87296246aae812a1f59ccb708e5546'
RC_REV='456174f62b89b8fca99eaaf33949c29fec9cfc2a'


def load_evaluator(root):
    root=check_checkout(root,XR_REV)
    path=root/'eval_robocasa365/entry.py'
    spec=importlib.util.spec_from_file_location('_k1lab_xiaomi_rc365_entry',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class RoboCasaEnv:
    correction_space='robocasa12'
    pose_frame='robot_base_relative; NOT world coordinates'
    correction_description=('12 normalized controls: arm translation[0:3], arm rotation[3:6], '
       'gripper_close[6] threshold .5, base+torso[7:11], mode[11] threshold .5. '
       'Teacher corrections are arm-only, |arm|<=.25, base=0, mode=-1. Not Cartesian meters.')
    evidence_kind='native_unqualified'
    def __init__(self,config,env=None,evaluator=None):
        self.config=config;self.runtime_fingerprint=config.get('runtime_fingerprint',{})
        self.helper=evaluator or load_evaluator(config['xiaomi_root'])
        self.env=env;self._step=0;self._success=False;self._done=False;self.horizon=0
        if env is None:
            check_checkout(config['robocasa_root'],RC_REV)
            import gymnasium as gym
            import robocasa
            from robocasa.utils.env_utils import convert_action
            from robocasa.utils.dataset_registry_utils import get_task_horizon
            self.make=gym.make;self.convert=convert_action;self.task_horizon=get_task_horizon
        else:
            self.convert=config['convert_action'];self.task_horizon=config['task_horizon']
        self.episode=None

    def _observation(self,raw):
        state=self.helper.observation_to_state(raw)
        pose={'arm':{'xyz':np.asarray(raw['state.end_effector_position_relative']).tolist(),
              'quaternion_xyzw':np.asarray(raw['state.end_effector_rotation_relative']).tolist(),
              'gripper_qpos':np.asarray(raw['state.gripper_qpos']).tolist(),
              'pose_frame':self.pose_frame}}
        self.obs=Observation(self.episode,self._step,str(raw['annotation.human.task_description']),
                  self.helper.collect_images(raw),state,pose,self.hz,native=raw)
        return self.obs
    def reset(self,case):
        if self.episode is not None:raise ContractError('fresh environment per case required')
        self.horizon=int(self.task_horizon(case['task']))
        if case.get('horizon') is not None and int(case['horizon'])!=self.horizon:
            raise ContractError('case horizon differs from native task registry')
        if self.env is None:
            self.env=self.make('robocasa/'+case['task'],split=case['split'],seed=int(case['environment_seed']))
        raw,_=self.env.reset(seed=int(case['episode_seed']))
        native=getattr(getattr(self.env,'unwrapped',self.env),'env',None)
        self.hz=float(getattr(native,'control_freq',self.config.get('control_hz',20)))
        self.episode=uuid.uuid4().hex
        return self._observation(raw)
    def step(self,action,correction=False):
        if action.space!='robocasa12' or self._done:raise ContractError('invalid action or terminated episode')
        if not np.isfinite(action.values).all():raise ContractError('nonfinite RoboCasa action')
        raw,_,done,truncated,info=self.env.step(self.convert(action.values.copy()))
        self._step+=1;self._success=bool(info.get('success',False));self._done=bool(self._success or done or truncated)
        return StepResult(self._observation(raw),bool(self._success or done),self._success,bool(truncated),None)
    def preview(self,proposal):
        return {'kind':'normalized_12D_controls','not_metric_trajectory':True,
                'description':self.correction_description}
    def finish(self,reason):return {'success':self._success,'score':None}
    def close(self):
        if self.env is not None:self.env.close()
    def describe(self):
        return {'benchmark':'robocasa365','xiaomi_revision':XR_REV,'robocasa_revision':RC_REV,
                'control_hz':self.hz,'horizon':self.horizon,'depth':False,'object_state_to_actor':False,
                'controller':'official convert_action + installed RoboCasa controller',
                'split_warning':'target50 task set is not the target kitchen split'}


class XiaomiRoboCasaPolicy:
    def __init__(self,config,client=None,evaluator=None):
        self.config=config;self.identity=PolicyIdentity(**config['identity'])
        self.helper=evaluator or load_evaluator(config['xiaomi_root'])
        if self.identity.action_space!='robocasa12':raise ContractError('wrong XR1 RoboCasa contract')
        self.client=client or self.helper.EvalClient(config['checkpoint_path'],config.get('host','127.0.0.1'),
                           int(config.get('port',10086)),'robocasa365',float(config.get('crop_ratio',.95)))
        self.length=int(config.get('obs_history',4));self.interval=int(config.get('obs_interval',2))
        if self.length<1 or self.interval<1:raise ContractError('positive observation history contract')
        self.reset()
    def reset(self):
        self.states=collections.deque(maxlen=(self.length-1)*self.interval+1)
        self.images={k:collections.deque(maxlen=self.states.maxlen) for k in self.helper.CAMERA_KEYS}
        self.last_stamp=None;self.last_step=None;self.episode=None
    def observe(self,obs):
        if obs.stamp==self.last_stamp:return
        if self.episode is not None and self.episode!=obs.episode:raise ContractError('policy episode changed without reset')
        if self.last_step is not None and obs.step!=self.last_step+1:raise ContractError('RoboCasa history requires every actual control observation')
        self.states.append(obs.state.copy())
        for key in self.images:self.images[key].append(obs.rgb[key].copy())
        self.last_stamp=obs.stamp;self.last_step=obs.step;self.episode=obs.episode
    def propose(self,obs):
        self.observe(obs)
        states=self.helper.sample_history(self.states,self.length,self.interval)
        images={k:self.helper.sample_history(q,self.length,self.interval) for k,q in self.images.items()}
        array=self.client.infer(states,images,obs.instruction)
        if len(array)<self.identity.execute_steps:raise ContractError('short model horizon relative to source prefix')
        # Source entry.py executes 16 and discards remainder. Export that exact prefix.
        actions=[Action('robocasa12',a) for a in array[:self.identity.execute_steps]]
        return Proposal(obs.stamp,obs.step,self.identity.identity,actions,
                        {'raw_predicted_horizon':len(array),'exposed_source_prefix':len(actions)})
    def invalidate(self,reason):
        # Model receives full measured history. No hidden action queue; preserve
        # actual observations through interventions instead of inventing a reset.
        pass
    def synchronize(self):pass # socket client returns CPU arrays
    def memory(self):return {'scope':'VRAM belongs to external Xiaomi model server'}
    def close(self):self.client.close()
