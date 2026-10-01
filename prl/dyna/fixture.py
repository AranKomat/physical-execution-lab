"""Deterministic contract fixture, NOT MuJoCo, robotics, or a learned policy."""
from dataclasses import replace
from pathlib import Path
import time
import numpy as np
from scipy.spatial.transform import Rotation
from .scene import Scene,Entity,Articulation,v3
from .planner import Plan,Advisory
from ..errors import ValidationError


class FixtureBackend:
    source='synthetic'
    def __init__(self,episode_id='fixture',blocked=False):
        self.episode_id=episode_id;self.steps=0;self.blocked=blocked
        self.xyz=np.array([-.1,0,.23]);self.quat=np.array([1.,0,0,0]);self.width=.08
        self.held=None;self.offset=None;self.clock=0.;self.guard=None;self.next_guard=0
        self.entities={
            'block':Entity('block',(-.1,0,.06),(.02,.02,.02),source='synthetic'),
            'tray':Entity('tray',(.14,0,.02),(.09,.09,.01),kind='fixture',source='synthetic',attributes={'region_type':'support'}),
            'table_support':Entity('table_support',(0,0,0),(.5,.4,.01),kind='fixture',source='synthetic',attributes={'region_type':'support'}),
        }
        self.contacts={};self.joints={}
        self.metadata={'backend':'deterministic_contract_fixture','native_physics':False,
                       'learned_policy':False,'information_profile':'synthetic'}
    def set_safety_check(self,guard,hz):self.guard=guard;self.guard_period=1/hz
    def scene(self):
        ents={n:replace(e,observed_step=self.steps) for n,e in self.entities.items()}
        return Scene(self.episode_id,self.steps,'put the block on the tray',ents,self.joints,
                     tuple(self.xyz),tuple(self.quat),self.width,self.contacts,(0,)*7,[],
                     'synthetic',simulation_time=self.clock)
    def capture(self):return self.scene()
    def pose_action(self,xyz,quat,gripper):
        return np.r_[(v3(xyz)-self.xyz)/.05,
                     (Rotation.from_quat(quat)*Rotation.from_quat(self.quat).inv()).as_rotvec()/.5,gripper]
    def step(self,action):
        a=np.asarray(action,float)
        old=self.xyz.copy()
        if not self.blocked:
            self.xyz += a[:3]*.05
            self.quat=(Rotation.from_rotvec(a[3:6]*.5)*Rotation.from_quat(self.quat)).as_quat()
        if self.held:
            obj=self.entities[self.held]
            p=self.xyz+Rotation.from_quat(self.quat).apply(self.offset)
            self.entities[self.held]=replace(obj,xyz=tuple(p))
        if a[6]>0:
            self.width=.03
            if self.held is None:
                for n,e in self.entities.items():
                    if e.kind=='object' and np.linalg.norm(v3(e.xyz)-self.xyz)<.03:
                        self.held=n;self.offset=Rotation.from_quat(self.quat).inv().apply(v3(e.xyz)-self.xyz)
                        self.contacts[n]=(True,True);break
        else:
            self.width=.08;self.held=None;self.contacts={}
        # Fixture schedules guard callbacks; this is a clock test, not a physics run.
        end=self.clock+.05
        while self.guard and self.next_guard<end-1e-10:
            self.clock=self.next_guard;self.guard(self.scene());self.next_guard+=self.guard_period
        self.clock=end;self.steps+=1
        obj=self.entities['block'];dst=self.entities['tray']
        goal=np.array([*dst.xyz[:2],dst.top+obj.aabb_half[2]+.004])
        success=self.held is None and np.linalg.norm(v3(obj.xyz)-goal)<.01
        return self.scene(),bool(success)
    def policy_actions(self,instruction):return np.tile([0,0,0,0,0,0,-1],(10,1))
    def close(self):pass


class FixturePlanner:
    identity='AUTHORED_CONTRACT_FIXTURE_NOT_MODEL'
    def __init__(self,steps=None):
        self.calls=0
        self.steps=steps or [Advisory('pick_and_place',{'object':'block','destination':'tray','relation':'on'})]
    def decide(self,c,out):
        if c['observation']['information_profile']!='synthetic':raise ValidationError('fixture_planner_on_native_forbidden')
        self.calls+=1
        items=self.steps if c['output_mode']=='sequence' else [self.steps[0]]
        o=c['observation']
        return Plan(tuple(items),o['observation_id'],time.monotonic(),o['scene_epoch'],o['task_epoch'])
