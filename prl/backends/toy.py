"""Deterministic synthetic contract fixture. NOT MuJoCo, LIBERO, or a robot policy.

Its purpose is to execute the same software path without a GPU and test interrupt,
substitution, measurement, bookkeeping and failure semantics. Its scores are not
valid robotics evidence and may not be pooled with native runs.
"""
from __future__ import annotations
from pathlib import Path
from ..contracts import Observation, Target
from ..errors import Unavailable
from ..util import norm, sub, add, digest


class ToyBackend:
    source='synthetic'
    def __init__(self, case, output_dir: Path, config=None):
        self.case=case; self.output_dir=Path(output_dir); self.config=config or {}
        self.steps=0; self.revision=0
        self.eef=(0.0,0.0,0.35); self.width=0.08
        self.block=(0.10,0.0,0.06); self.goal=(0.24,0.15,0.06)
        self.attached=False; self.native_success=False; self.native_truncated=False
        self.before=lambda a: None; self.after=lambda o,a: None; self.before_vla=lambda:None
        self.extra_targets={}; self.blocked=(case.fixture=='blocked')
        self.task='Pick up the block and place it at the destination, then release it.'
        self.metadata={'backend':'synthetic-contract-fixture','policy':'scripted_toy_not_VLA',
                       'information_profile':'synthetic','physics':'none',
                       'state_sha256':case.state_sha256,'control_hz':20,
                       'policy_rng_control':'deterministic_fixture'}

    def set_hooks(self,before,after,before_vla):
        self.before,self.after,self.before_vla=before,after,before_vla

    def observe(self):
        targets={
            'block':Target('block',self.block,'synthetic','fixture_point',self.steps,
                           evidence_id=f'toy:{self.steps}:block'),
            'destination':Target('destination',self.goal,'synthetic','fixture_point',self.steps,
                                 evidence_id=f'toy:{self.steps}:goal'),
            'safe_stage':Target('safe_stage',(0.0,0.0,0.35),'synthetic','fixture_point',self.steps),
        }
        targets.update(self.extra_targets)
        return Observation(self.case.case_id,self.revision,self.steps,self.task,self.eef,self.width,
                           'synthetic',targets,signals={})

    def _step(self,action):
        self.before(action)
        delta=tuple(float(a)*0.05 for a in action[:3])
        candidate=add(self.eef,delta)
        if self.blocked and candidate[0]>0.07 and candidate[2]<0.20:
            candidate=self.eef
        self.eef=candidate
        if action[6]>0:
            self.width=0.025 if self.attached or norm(sub(self.eef,self.block))<0.035 else 0.0
            if norm(sub(self.eef,self.block))<0.035: self.attached=True
        elif action[6]<0:
            self.width=0.08; self.attached=False
        if self.attached: self.block=self.eef
        self.steps+=1; self.revision+=1
        self.native_success=not self.attached and norm(sub(self.block,self.goal))<0.015
        self.after(self.observe(),list(action))

    def execute_stage(self,stage):
        op,a=stage.operation,stage.arguments
        if op in ('move_to','move_pose'):
            for _ in range(stage.max_steps):
                d=sub(a['xyz'],self.eef)
                if norm(d)<=a.get('tol',.006): break
                c=a.get('step_clip',.02)
                action=[max(-c,min(c,x))/.05 for x in d]+[0,0,0,a.get('gripper',1)]
                self._step(action)
        elif op in ('set_gripper','release'):
            for _ in range(a.get('steps',a.get('max_steps',8))):
                self._step([0,0,0,0,0,0,-1 if op=='release' else a['gripper']])
        elif op=='rotate_wrist':
            for _ in range(min(4,stage.max_steps)): self._step([0,0,0,0,0,.2,a.get('gripper',1)])
        elif op in ('vla','vla_pick'):
            # Intentional no-op surrogate: tests no-progress/budget semantics only.
            for i in range(stage.max_steps):
                if i%10==0: self.before_vla()
                self._step([0,0,0,0,0,0,-1])
        else: raise Unavailable(f'unknown_toy_stage:{op}')
        return {'executor':'synthetic_fixture','eef_xyz':list(self.eef)}

    def query(self,name,args,registry):
        if name=='observe': return self.observe().actor_view()
        if name=='measure_pixel':
            if args['observation_id']!=self.observe().observation_id:
                raise Unavailable('stale_image')
            from ..geometry import measure_pixel
            import numpy as np
            cam={'depth':np.full((20,20),.5),'intrinsic_matrix':[[100,0,10],[0,100,10],[0,0,1]],
                 'extrinsic_matrix':np.eye(4).tolist()}
            r=measure_pixel(cam,args['pixel'],args.get('coordinate_space','pixels'))
            key=f'measurement_{len(self.extra_targets)}'
            self.extra_targets[key]=Target(key,tuple(r['xyz_world_m']),'synthetic',
                                          'visible_surface',self.steps,evidence_id=key)
            return {**r,'target_id':key}
        raise Unavailable(f'{name}_not_available_in_synthetic_fixture')

    def verify_effect(self,name,args):
        # Gripper closure is not a grasp verifier. Preserve uncertainty.
        return None

    def capture(self): return self.observe()
    def close(self): pass
