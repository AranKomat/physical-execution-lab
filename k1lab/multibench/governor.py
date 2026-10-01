"""Task-agnostic sparse review schedule, not a semantic safety oracle.

An ACCEPT is a short lease, not permission to run the remainder of an episode.
Periodic review remains mandatory: smooth, valid motions may pursue a wrong goal.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from k1lab.errors import ContractError


@dataclass(frozen=True)
class MonitorConfig:
    max_unreviewed_steps: int = 50
    max_unreviewed_chunks: int = 4
    stall_window: int = 25
    stall_displacement_m: float = .001
    joint_jump_rad: float = .30
    gripper_event_review: bool = True
    boundary_cooldown_steps: int = 5

    def __post_init__(self):
        for name in ('max_unreviewed_steps','max_unreviewed_chunks','stall_window','boundary_cooldown_steps'):
            if type(getattr(self,name)) is not int or getattr(self,name) < 1:
                raise ContractError(f'positive integer {name} required')
        for name in ('stall_displacement_m','joint_jump_rad'):
            if not np.isfinite(getattr(self,name)) or getattr(self,name) <= 0:
                raise ContractError(f'positive {name} required')


class SparseGovernor:
    def __init__(self, config=None):
        self.cfg = config or MonitorConfig()
        self.reset()

    def reset(self):
        self.last_review = None
        self.chunks = 0
        self.history = []
        self.pending = []
        self.gripper_state = None

    def reviewed(self, step):
        self.last_review = step
        self.chunks = 0
        self.pending.clear()
        self.history.clear()

    def observe(self, obs, *, executed_action=None):
        # This observes robot motion only. A still robot can be intentionally waiting;
        # the monitor requests review rather than labelling the task as a failure.
        signature=[]
        for arm in sorted(obs.eef):
            p=obs.eef[arm]
            signature.extend(p['xyz'])
            # Account for rotation: a pure rotation is real motion, not a Cartesian stall.
            q=np.asarray(p['quaternion_xyzw'],float)
            if q[3] < 0:q=-q
            signature.extend((q*.1).tolist())
        if signature:
            self.history.append((obs.step,np.asarray(signature)))
            self.history=[r for r in self.history if obs.step-r[0] <= self.cfg.stall_window]
            if len(self.history)>1 and obs.step-self.history[0][0]>=self.cfg.stall_window:
                delta=max(float(np.linalg.norm(x-self.history[0][1])) for _,x in self.history)
                if delta < self.cfg.stall_displacement_m:self.pending.append('robot_motion_stagnation_requires_review')
        for name in ('controller_fault','execution_failed','tracking_lost','target_motion_contradicted'):
            if obs.signals.get(name) is True:self.pending.append(name)
        if executed_action is not None and self.cfg.gripper_event_review:
            a=executed_action
            slots={'x5_joint14':[6,13],'x5_eef16_wxyz':[7,15]}.get(a.space)
            if slots:
                state=tuple((a.values[slots]>.5).tolist())
                if self.gripper_state is not None and state!=self.gripper_state:
                    if self.last_review is not None and obs.step-self.last_review >= self.cfg.boundary_cooldown_steps:
                        self.pending.append('gripper_command_transition_not_grasp_confirmation')
                self.gripper_state=state

    def proposal_risks(self, proposal, obs):
        reasons=[]
        if proposal.actions[0].space=='x5_joint14' and len(obs.state)==14:
            a=proposal.actions[0].values
            idx=[0,1,2,3,4,5,7,8,9,10,11,12]
            if np.max(np.abs(a[idx]-obs.state[idx]))>self.cfg.joint_jump_rad:
                reasons.append('large_first_joint_target_jump')
        return reasons

    def review_reasons(self, mode, step, proposal=None, obs=None):
        if mode=='motor_only':return []
        if mode not in ('review_every_chunk','sparse'):raise ContractError('unknown hybrid mode')
        if mode=='review_every_chunk':return ['scheduled_every_chunk']
        reasons=list(dict.fromkeys(self.pending))
        if self.last_review is None:reasons.append('initial_semantic_review')
        else:
            if step-self.last_review>=self.cfg.max_unreviewed_steps:reasons.append('periodic_semantic_review')
            if self.chunks>=self.cfg.max_unreviewed_chunks:reasons.append('chunk_lease_expired')
        if proposal is not None and obs is not None:reasons+=self.proposal_risks(proposal,obs)
        return list(dict.fromkeys(reasons))

    def allowance(self, step, requested, mode):
        if mode!='sparse':return requested
        if self.last_review is None:return 0
        return max(0,min(requested,self.cfg.max_unreviewed_steps-(step-self.last_review)))

    def chunk_finished(self):self.chunks+=1
