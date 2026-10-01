"""Source-inspected XPolicyLab Model bridge. Run each model in its own environment.

WAM update_obs acknowledges pending actions. Deliver every actual ACK exactly
once, and reset pending actions BEFORE a correction/shortened prefix. Never
replay hypothetical policy steps to advance the model's internal state.
"""
from __future__ import annotations
import importlib
from pathlib import Path
import sys
import numpy as np
from k1lab.errors import ContractError,Unavailable
from ..types import Action,Proposal,PolicyIdentity
from .robodojo import check_checkout

REV='408b99d959a7b2207f5f785528fefcc019d7b131'
MODULES={'g05':'G05','xiaomi_r1':'Xiaomi_Robotics_1','internw0_delta':'InternW0_delta'}


def to_xpl(obs):
    if len(obs.state)!=14 or set(obs.eef)!= {'left','right'}:raise ContractError('dual X5 observation required')
    state={}
    for arm,i in (('left',0),('right',1)):
        pose=obs.eef[arm];q=np.asarray(pose['quaternion_xyzw'])
        state[f'{arm}_arm_joint_state']=obs.state[7*i:7*i+6].copy()
        state[f'{arm}_ee_joint_state']=obs.state[7*i+6:7*i+7].copy()
        state[f'{arm}_ee_pose']=np.r_[pose['xyz'],q[[3,0,1,2]]].astype(np.float32)
    return {'vision':{('cam_head' if c=='cam_high' else c):{'color':obs.rgb[c]}
                      for c in ('cam_high','cam_left_wrist','cam_right_wrist')},
            'state':state,'instruction':obs.instruction,'task_instruction':obs.instruction,'env_idx':0}


def decode_xpl(rows, space, gripper_clip=False):
    if not isinstance(rows,(list,tuple)) or not rows:raise ContractError('expected nonempty list of XPolicyLab command dictionaries')
    actions=[];clip_count=0
    for row in rows:
        vals=[]
        for arm in ('left','right'):
            key=f'{arm}_arm_joint_state' if space=='x5_joint14' else f'{arm}_ee_pose'
            vector=np.asarray(row[key],np.float32).reshape(-1)
            wanted=6 if space=='x5_joint14' else 7
            if vector.shape!=(wanted,):raise ContractError('XPolicyLab robot/action shape mismatch')
            grip=np.asarray(row[f'{arm}_ee_joint_state'],np.float32).reshape(-1)
            if grip.shape!=(1,) or not np.isfinite(grip).all():raise ContractError('invalid native gripper command')
            if gripper_clip:
                clip_count+=int(grip[0]<0 or grip[0]>1);grip=np.clip(grip,0,1)
            vals.extend(vector);vals.extend(grip)
        actions.append(Action(space,np.asarray(vals)))
    return actions,clip_count


class XPolicyModel:
    def __init__(self,config,model=None):
        self.config=dict(config);self.identity=PolicyIdentity(**config['identity'])
        name=config['policy']
        if name not in MODULES:raise ContractError('unsupported XPolicyLab policy')
        cfg=dict(config.get('model_config',{}))
        if cfg.get('allow_dummy_policy') or cfg.get('device')=='cpu':raise Unavailable('real policy bridge refuses dummy/CPU evaluation')
        if model is None:
            root=check_checkout(config['xpolicylab_root'],REV)
            sys.path.insert(0,str(root.parent))
            module=importlib.import_module('XPolicyLab.policy.'+MODULES[name]+'.model')
            model=module.Model(cfg)
        self.model=model;self.last_stamp=None;self.last_step=None;self.episode=None
        self.pending=0;self.last_diag={}

    def reset(self):
        self.model.reset();self.last_stamp=None;self.last_step=None;self.episode=None;self.pending=0

    def observe(self,obs):
        if obs.stamp==self.last_stamp:return
        if self.episode is not None and obs.episode!=self.episode:raise ContractError('policy session crossed episode')
        if self.pending and self.last_step is not None and obs.step!=self.last_step+1:
            raise ContractError('stateful policy requires exactly one observation per executed action')
        self.model.update_obs(to_xpl(obs))
        if self.pending:self.pending-=1
        self.last_stamp=obs.stamp;self.last_step=obs.step;self.episode=obs.episode

    def propose(self,obs):
        if self.pending:raise ContractError('unacknowledged actions: cancel or execute; never fake acknowledgements')
        self.observe(obs)
        rows=self.model.get_action()
        actions,clipped=decode_xpl(rows,self.identity.action_space,self.config.get('gripper_clip',False))
        grippers=np.concatenate([np.asarray(row[f'{arm}_ee_joint_state']).reshape(-1)
                                 for row in rows for arm in ('left','right')])
        clip_delta=np.abs(grippers-np.clip(grippers,0,1))
        self.pending=len(actions)
        return Proposal(obs.stamp,obs.step,self.identity.identity,actions,
                        {'gripper_clips':clipped,'native_returned_actions':len(actions),
                         'raw_gripper_min':float(grippers.min()),'raw_gripper_max':float(grippers.max()),
                         'max_gripper_clip_delta':float(clip_delta.max())})

    def invalidate(self,reason):
        # A source-defined generic cancel is not available. Reset and truthfully label
        # within-episode history loss; evaluate this overhead separately.
        self.model.reset();self.pending=0;self.last_stamp=None;self.last_step=None

    def synchronize(self):
        import torch
        if torch.cuda.is_available():torch.cuda.synchronize()

    def memory(self):
        import torch
        return {'allocated_bytes':torch.cuda.max_memory_allocated(),
                'reserved_bytes':torch.cuda.max_memory_reserved()} if torch.cuda.is_available() else {}
    def close(self):pass
