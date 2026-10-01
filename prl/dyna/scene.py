"""Geometry kept behind the symbolic planner interface.

Simulation-state geometry is intentional in the paper-reproduction profile
(Appendix A, p14). It is NOT a sensor-only robotics result.
"""
from dataclasses import dataclass, field
from typing import Any
import numpy as np
from ..errors import ValidationError, Unavailable
from ..util import finite, vec, integer, plain


def v3(v):
    return np.asarray(vec(list(v), 'xyz'), dtype=float)


def rotation(q):
    from scipy.spatial.transform import Rotation
    a=np.asarray(q,float)
    if a.shape!=(4,) or not np.isfinite(a).all() or np.linalg.norm(a)<1e-8:
        raise ValidationError('invalid_xyzw_quaternion')
    return Rotation.from_quat(a).as_matrix()


@dataclass(frozen=True)
class Entity:
    name: str
    xyz: tuple[float,float,float]
    half_size: tuple[float,float,float]
    quat_xyzw: tuple[float,float,float,float] = (0,0,0,1)
    kind: str = 'object'
    parent: str | None = None
    source: str = 'privileged_sim'
    observed_step: int = 0
    attributes: dict[str,Any] = field(default_factory=dict)

    def __post_init__(self):
        v3(self.xyz); size=v3(self.half_size); rotation(self.quat_xyzw)
        if np.any(size<0): raise ValidationError('negative_geometry_extent')
        if self.source not in ('privileged_sim','sensor','synthetic'):
            raise ValidationError('unknown_geometry_source')
        integer(self.observed_step,'observed_step',0)

    @property
    def R(self): return rotation(self.quat_xyzw)
    @property
    def aabb_half(self): return np.abs(self.R) @ v3(self.half_size)
    @property
    def top(self): return float(self.xyz[2]+self.aabb_half[2])
    @property
    def bottom(self): return float(self.xyz[2]-self.aabb_half[2])
    def local(self, point): return self.R.T @ (v3(point)-v3(self.xyz))
    def world(self, point): return v3(self.xyz)+self.R @ v3(point)


@dataclass(frozen=True)
class Articulation:
    name: str
    parent: str
    handle: str
    kind: str  # slide or hinge
    pivot: tuple[float,float,float]
    axis: tuple[float,float,float]
    position: float
    lower: float
    upper: float
    # Positions are derived from asset mechanism metadata, NOT native goal clauses.
    open_position: float | None = None
    closed_position: float | None = None
    source: str = 'privileged_sim'
    observed_step: int = 0
    def __post_init__(self):
        v3(self.pivot); axis=v3(self.axis)
        if self.kind not in ('slide','hinge') or np.linalg.norm(axis)<1e-8:
            raise ValidationError('invalid_articulation')
        for k in ('position','lower','upper'): finite(getattr(self,k),k)
        if self.lower>=self.upper: raise ValidationError('invalid_joint_range')


@dataclass
class Scene:
    episode_id: str
    step: int
    task: str
    entities: dict[str,Entity]
    articulations: dict[str,Articulation]
    eef_xyz: tuple[float,float,float]
    eef_quat: tuple[float,float,float,float]
    gripper_width: float
    # Contact between actual finger geoms and an object's physical geoms.
    finger_contacts: dict[str,tuple[bool,bool]] = field(default_factory=dict)
    joint_velocity: tuple[float,...] = ()
    images: list[dict] = field(default_factory=list)
    information_profile: str = 'privileged_sim'
    scene_epoch: int = 0
    task_epoch: int = 0
    simulation_time: float = 0.0

    @property
    def observation_id(self):
        return f'{self.episode_id}:{self.scene_epoch}:{self.task_epoch}:{self.step}'

    def entity(self, name, max_age=10):
        if name not in self.entities: raise Unavailable(f'unresolved_entity:{name}')
        e=self.entities[name]
        if e.observed_step>self.step or self.step-e.observed_step>max_age:
            raise Unavailable(f'stale_geometry:{name}')
        if self.information_profile=='sensor' and e.source!='sensor':
            raise ValidationError('simulator_geometry_in_sensor_track')
        return e

    def articulation(self,name):
        if name in self.articulations:return self.articulations[name]
        candidates=[j for j in self.articulations.values() if j.handle==name or j.parent==name]
        if len(candidates)!=1: raise Unavailable(f'ambiguous_or_missing_articulation:{name}')
        return candidates[0]

    def symbolic_view(self):
        # Numeric object geometry does not go to Qwen; the grounder resolves it.
        # No goal predicates, native verdict, reward, init-state index or task ID.
        return {'observation_id':self.observation_id, 'task':self.task,
                'sim_step':self.step,'scene_epoch':self.scene_epoch,'task_epoch':self.task_epoch,
                'information_profile':self.information_profile,
                'images':self.images,
                'entities':[{'name':e.name,'kind':e.kind,'parent':e.parent,
                             'description':e.attributes.get('description',e.name.replace('_',' '))}
                            for e in self.entities.values()],
                'articulations':[{'name':j.name,'parent':j.parent,'handle':j.handle,'kind':j.kind,
                                  'state':('open' if j.open_position is not None and
                                           abs(j.position-j.open_position)<0.03 else
                                           'closed' if j.closed_position is not None and
                                           abs(j.position-j.closed_position)<0.03 else 'intermediate')}
                                 for j in self.articulations.values()],
                'robot':{'eef_xyz_m':list(self.eef_xyz),'gripper_width_m':self.gripper_width}}


class ExecutionMemory:
    """Within-episode physical state only. No cross-test trace reuse."""
    def __init__(self):
        self.held_object=None
        self.object_to_tcp=None
        self.keyframes={}
        self.placement_reservations={}
        self.completed=[]
        self.failures=[]

    def record_keyframe(self,label,scene):
        self.keyframes[label]={'episode_id':scene.episode_id,'scene_epoch':scene.scene_epoch,
            'task_epoch':scene.task_epoch,'step':scene.step,'xyz':tuple(scene.eef_xyz),
            'quat':tuple(scene.eef_quat),'held_object':self.held_object}

    def keyframe(self,label,scene):
        k=self.keyframes.get(label)
        if k is None: raise Unavailable('unknown_keyframe')
        if (k['episode_id'],k['scene_epoch'],k['task_epoch'])!=(scene.episode_id,scene.scene_epoch,scene.task_epoch):
            raise Unavailable('keyframe_epoch_mismatch')
        return k

    def summary(self):
        return {'held_object':self.held_object,'completed_operations':self.completed[-12:],
                'recent_failures':self.failures[-6:], 'keyframes':list(self.keyframes)}
