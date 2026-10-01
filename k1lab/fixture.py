"""Small kinematic fixture for SOFTWARE TESTS. No robotics benchmark claim."""
from __future__ import annotations
import numpy as np
from scipy.spatial.transform import Rotation
from .policy import pack_array


class FixturePort:
    action_space='libero_normalized_osc7'
    policy_contract={'cameras':('agentview','robot0_eye_in_hand'),'state_dim':8,
                     'observation_convention':'rpent_pi05_libero_rgb180_256_eef_axisangle_gripper2'}
    def __init__(self,*,horizon=300,blocked=False,lost_at=None,point_moves=True,terminal_at=None):
        self.frame=0;self.horizon=horizon;self.control_hz=20;self.xyz=np.array([0.,0.,0.5])
        self.q=np.array([0.,0.,0.,1.]);self.gripper=1.;self.blocked=blocked;self.lost_at=lost_at
        self.point_moves=point_moves;self.terminal_at=terminal_at;self.actions=[]
        self.feature=np.array([0.,0.,0.52]);self.previous=self.xyz.copy();self.latch=False
    def observe(self):
        return {'frame_id':self.frame,'instruction':'synthetic contract exercise',
                'arms':{'arm':{'xyz_world_m':self.xyz.tolist(),'quaternion_xyzw':self.q.tolist(),
                   'gripper_command_open':self.gripper,'gripper_opening_m':0.02 if self.gripper<0.5 else 0.08}},
                'capabilities':{'control_hz':20},'vision':{}}
    def points(self):
        if self.lost_at is not None and self.frame>=self.lost_at:return [{'id':'P1','frame_id':self.frame,'status':'lost_remeasure'}]
        return [{'id':'P1','frame_id':self.frame,'status':'tracked_estimate','xyz_world_m':self.feature.tolist()}]
    def success(self):
        self.latch=self.latch or (self.terminal_at is not None and self.frame>=self.terminal_at)
        return bool(self.latch)
    def servo(self,arm,xyz,q,gripper):
        if self.success() or self.frame>=self.horizon:return
        old=self.xyz.copy();oldr=Rotation.from_quat(self.q)
        if not self.blocked:self.xyz=np.asarray(xyz,float);self.q=np.asarray(q,float)
        if gripper is not None:self.gripper=float(gripper)
        if self.gripper<0.5 and self.point_moves:
            self.feature=self.xyz+(Rotation.from_quat(self.q)*oldr.inv()).apply(self.feature-old)
        self.frame+=1;self.actions.append((self.frame,self.xyz.copy(),self.gripper));self.success()
    def native_action(self,action):
        a=np.asarray(action);self.servo('arm',self.xyz+a[:3]*0.02,self.q,(1-a[6])/2)
    def policy_observation(self,subgoal):
        return {'frame_id':self.frame,'subgoal':subgoal,'images':{},'state':pack_array(np.zeros(8,np.float32))}
