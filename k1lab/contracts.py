"""Task-independent, closed schemas. No task names or simulator geometry."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
from .errors import ContractError
from .util import vector,number,integer,keys,text,digest


@dataclass(frozen=True)
class Limits:
    max_command_steps: int = 160
    max_segments: int = 6
    lease_s: float = 120.0
    max_translation_m: float = 0.50
    position_tolerance_m: float = 0.004
    angle_tolerance_deg: float = 3.0
    settled_frames: int = 3
    stall_steps: int = 24
    progress_m: float = 0.0005
    progress_deg: float = 0.5
    max_probe_lift_m: float = 0.03
    transit_m_s: float = 0.15
    approach_m_s: float = 0.025
    angular_deg_s: float = 60.0
    gripper_settle_steps: int = 10
    observation_period: int = 1
    workspace_low: tuple = (-1.0,-1.0,0.0)
    workspace_high: tuple = (1.0,1.0,2.0)
    max_policy_steps: int = 40
    max_policy_calls: int = 256
    def __post_init__(self):
        for k in ('max_command_steps','max_segments','settled_frames','stall_steps','gripper_settle_steps','observation_period','max_policy_steps','max_policy_calls'):
            integer(getattr(self,k),1,10000,k)
        for k in ('lease_s','max_translation_m','position_tolerance_m','angle_tolerance_deg','progress_m','progress_deg','max_probe_lift_m','transit_m_s','approach_m_s','angular_deg_s'):
            number(getattr(self,k),1e-8,10000,k)
        lo=vector(self.workspace_low,3); hi=vector(self.workspace_high,3)
        if np.any(hi<=lo): raise ContractError('invalid workspace box')
        if self.observation_period!=1: raise ContractError('v0.3 requires per-native-step observation')
    @classmethod
    def from_dict(cls,obj):
        keys(obj,cls.__dataclass_fields__)
        return cls(**obj)
    def as_dict(self): return asdict(self)


@dataclass(frozen=True)
class Segment:
    kind: str
    xyz: tuple | None = None
    quaternion: tuple | None = None
    gripper: float | None = None
    profile: str = 'transit'
    steps: int = 10
    def json(self): return asdict(self)


def parse_segment(obj,limits):
    keys(obj,{'kind','target_xyz_world_m','target_quaternion_xyzw','gripper','profile','settle_steps'}, {'kind'})
    if obj['kind']=='pose':
        if 'gripper' in obj or 'settle_steps' in obj: raise ContractError('pose preserves gripper')
        xyz=vector(obj.get('target_xyz_world_m'),3,'target_xyz_world_m')
        q=vector(obj.get('target_quaternion_xyzw'),4,'quaternion_xyzw')
        if abs(np.linalg.norm(q)-1)>0.01: raise ContractError('quaternion must be normalized')
        if np.any(xyz<limits.workspace_low) or np.any(xyz>limits.workspace_high):
            raise ContractError('target outside configured workspace (not a collision check)')
        profile=obj.get('profile','transit')
        if profile not in ('transit','approach'): raise ContractError('unknown motion profile')
        return Segment('pose',tuple(xyz),tuple(q/np.linalg.norm(q)),profile=profile)
    if obj['kind']=='gripper':
        if any(k in obj for k in ('target_xyz_world_m','target_quaternion_xyzw','profile')):
            raise ContractError('gripper step holds current pose')
        g=number(obj.get('gripper'),0,1,'gripper')
        n=integer(obj.get('settle_steps',limits.gripper_settle_steps),1,30,'settle_steps')
        return Segment('gripper',gripper=g,steps=n)
    raise ContractError('only pose and gripper segments are allowed')


def parse_plan(args,limits):
    keys(args,{'frame_id','arm','command_id','segments','max_native_steps','watch_points','decision_note'},
         {'frame_id','arm','command_id','segments','max_native_steps'})
    integer(args['frame_id'],0,10**9,'frame_id'); text(args['arm'],'arm',40); text(args['command_id'],'command_id',120)
    if not isinstance(args['segments'],list) or not 1<=len(args['segments'])<=limits.max_segments:
        raise ContractError('invalid segment count')
    segments=[parse_segment(x,limits) for x in args['segments']]
    budget=integer(args['max_native_steps'],1,limits.max_command_steps,'max_native_steps')
    if sum(s.steps if s.kind=='gripper' else limits.settled_frames for s in segments)>budget:
        raise ContractError('cannot afford minimum settle steps')
    points=args.get('watch_points',[])
    if not isinstance(points,list) or len(points)>12: raise ContractError('invalid watch_points')
    for p in points: text(p,'point ID',80)
    return segments,budget,points


def envelope(args):
    return digest({k:v for k,v in args.items() if k!='decision_note'})
