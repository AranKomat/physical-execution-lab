"""Small fixed capability library, shared by nominal and dynamic execution.

These are independently implemented compositions over RPent, NOT the unreleased
DynaHarness capability library. They are simulator research procedures, not
collision-qualified or hardware-safe skills.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any
from .contracts import Observation, Stage
from .errors import ValidationError, Unavailable
from .util import vec, finite, integer, add, norm, sub, digest, plain


@dataclass(frozen=True)
class Spec:
    name: str
    description: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    effect_keys: tuple[str, ...]
    read_only: bool = False


SPECS = [
    Spec('observe', 'Read fresh legal observations without moving.', (), (), (), True),
    Spec('measure_pixel', 'Measure a visible RGB-D surface. Not an object center or grasp.',
         ('camera', 'pixel', 'observation_id'), ('coordinate_space',), (), True),
    Spec('fit_geometry', 'K1: fit a visible plane/axis in a current image ROI.',
         ('camera', 'roi', 'kind', 'observation_id'), (), (), True),
    Spec('move_to', 'Closed-loop Cartesian transit; NO general collision-free planner.',
         ('target',), ('offset', 'gripper', 'tol', 'step_clip', 'target_yaw', 'target_pitch'),
         ('target','offset')),
    Spec('set_gripper', 'Open/close jaws. Jaw width alone never certifies grasp.',
         ('gripper',), ('steps',), ('gripper',)),
    Spec('release', 'Open the jaws while holding tool pose; task verdict is separate.',
         (), ('steps',), ()),
    Spec('rotate_wrist', 'Bounded world-Z yaw; not arbitrary dexterous tool use.',
         ('delta_yaw',), ('gripper',), ('delta_yaw',)),
    Spec('pick', 'Analytic top-down pick or frozen VLA pick. Acquisition needs evidence.',
         ('target',), ('executor','instruction','clearance','grasp_offset','yaw'), ('target',)),
    Spec('place', 'Move a held item above a target, descend, release and retreat.',
         ('destination',), ('clearance','place_offset','yaw'), ('destination',)),
    Spec('pick_place', 'Compose top-down acquisition, corridor transport and placement.',
         ('target','destination'), ('clearance','grasp_offset','place_offset','yaw'),
         ('target','destination')),
    Spec('push', 'Bounded straight contact sweep; needs an explicit contact target.',
         ('target','direction','distance'), ('approach_offset','gripper'),
         ('target','direction','distance')),
    Spec('pull_handle', 'Grasp a measured handle and pull along an explicit direction.',
         ('target','direction','distance'), ('approach_offset','yaw'),
         ('target','direction','distance')),
    Spec('swing_handle', 'Grasp a handle and follow a bounded arc around a measured pivot.',
         ('target','pivot','axis','angle'), ('approach_offset','yaw'),
         ('target','pivot','axis','angle')),
    Spec('vla_contact', 'Run the frozen policy on a sub-instruction for bounded contact work.',
         ('instruction',), (), ('instruction',)),
    Spec('vla', 'Run the frozen policy with the original task. The E0 executor.',
         (), (), ()),
    Spec('finish', 'Request termination; NEVER substitutes for native success.', (), (), (), True),
]


class Registry:
    def __init__(self, *, max_target_age_steps=60, max_uncertainty_m=0.05,
                 workspace=((-0.8,-0.8,0.0),(0.8,0.8,1.5)), k1=False):
        self.specs = {s.name:s for s in SPECS if k1 or s.name!='fit_geometry'}
        self.max_target_age_steps = integer(max_target_age_steps,'max_target_age_steps',0)
        self.max_uncertainty_m = finite(max_uncertainty_m,'max_uncertainty_m',0)
        self.workspace = tuple(vec(list(v),'workspace') for v in workspace)
        if any(a>=b for a,b in zip(*self.workspace)):
            raise ValidationError('Workspace min must be below max on all axes')
        self.k1 = k1

    @property
    def fingerprint(self):
        return digest({'specs':list(self.specs.values()), 'implementation':'prl-basic-contact-v1',
                       'workspace':self.workspace})

    def catalog(self):
        return [plain(s) for s in self.specs.values()]

    def validate(self, name, args):
        if name not in self.specs:
            raise ValidationError(f'unknown_capability:{name}')
        if not isinstance(args, dict):
            raise ValidationError('arguments_not_object')
        s=self.specs[name]
        if set(s.required)-set(args):
            raise ValidationError(f'missing_arguments:{sorted(set(s.required)-set(args))}')
        if set(args)-set(s.required+s.optional):
            raise ValidationError(f'unknown_arguments:{sorted(set(args)-set(s.required+s.optional))}')
        for k in ('target','destination','pivot','camera','observation_id'):
            if k in args and (not isinstance(args[k],str) or not args[k] or len(args[k])>160):
                raise ValidationError(f'invalid_{k}')
        for k in ('offset','grasp_offset','place_offset','approach_offset'):
            if k in args:
                vec(args[k],k,lo=-0.30,hi=0.30)
        for k in ('direction','axis'):
            if k in args and norm(vec(args[k],k))<1e-8:
                raise ValidationError(f'zero_{k}')
        for k in ('delta_yaw','angle','yaw','target_yaw','target_pitch'):
            if k in args: finite(args[k],k,-math.pi,math.pi)
        if 'distance' in args: finite(args['distance'],'distance',0.001,0.30)
        if 'clearance' in args: finite(args['clearance'],'clearance',0.01,0.30)
        if 'gripper' in args: finite(args['gripper'],'gripper',-1,1)
        if 'tol' in args: finite(args['tol'],'tol',0.001,0.03)
        if 'step_clip' in args: finite(args['step_clip'],'step_clip',0.001,0.025)
        if 'steps' in args: integer(args['steps'],'steps',1,40)
        if 'executor' in args and args['executor'] not in ('analytic','vla'):
            raise ValidationError('executor_must_be_analytic_or_vla')
        if 'instruction' in args and (not isinstance(args['instruction'],str) or
                                      not 1<=len(args['instruction'])<=2000):
            raise ValidationError('invalid_instruction')
        if 'pixel' in args: vec(args['pixel'],'pixel',2)
        if 'roi' in args: vec(args['roi'],'roi',4)
        if 'kind' in args and args['kind'] not in ('axis','plane'):
            raise ValidationError('invalid_geometry_kind')
        if 'coordinate_space' in args and args['coordinate_space'] not in ('pixels','normalized_01','normalized_1000'):
            raise ValidationError('explicit_pixel_coordinate_space_required')
        return s

    def equivalent(self, name, args, alt):
        self.validate(alt['capability'], alt['arguments'])
        # Deliberately conservative. For v1 only executor changes within the SAME
        # operation are eligible, never silently replace a requested push by carry.
        if alt['capability'] != name:
            return False
        keys=self.specs[name].effect_keys
        return all(args.get(k)==alt['arguments'].get(k) for k in keys)

    def resolve(self, target_id, obs: Observation, *, dynamic=True):
        if target_id not in obs.targets:
            raise Unavailable(f'unresolved_target:{target_id}')
        t=obs.targets[target_id]
        if obs.source=='sensor' and t.source!='sensor':
            raise ValidationError('privileged_target_in_sensor_profile')
        if t.observed_step>obs.sim_step:
            raise ValidationError('future_target_evidence')
        if dynamic and obs.sim_step-t.observed_step>self.max_target_age_steps:
            raise Unavailable(f'stale_target:{target_id}')
        if dynamic and t.uncertainty_m is not None and t.uncertainty_m>self.max_uncertainty_m:
            raise Unavailable(f'uncertain_target:{target_id}')
        return t.xyz

    def _check_xyz(self, p):
        if not all(a<=v<=b for v,a,b in zip(p,*self.workspace)):
            raise ValidationError('target_outside_configured_workspace')
        return tuple(p)

    def compile(self, name, args, obs: Observation, max_steps, *, dynamic):
        self.validate(name,args)
        if self.specs[name].read_only:
            return []
        if max_steps<=0:
            raise ValidationError('motion_needs_positive_budget')
        def at(key, offset=(0,0,0)):
            return self._check_xyz(add(self.resolve(args[key],obs,dynamic=dynamic),offset))
        def move(p, grip=1.0, **extra):
            p=self._check_xyz(p)
            a={'xyz':list(p),'gripper':grip,'tol':0.006,'step_clip':0.02,**extra}
            op='move_pose' if 'target_pitch' in a else 'move_to'
            return Stage(op,a,max_steps,p,a['tol'])
        def jaw(g, steps=8):
            return Stage('set_gripper', {'gripper':g,'steps':steps}, steps)
        def rot(yaw):
            return Stage('rotate_wrist',{'target_yaw':yaw,'gripper':-1.0},max_steps)
        clearance=args.get('clearance',0.12)
        yaw=args.get('yaw')
        if name=='move_to':
            extras={k:args[k] for k in ('tol','step_clip','target_yaw','target_pitch') if k in args}
            return self._split_moves([move(at('target',args.get('offset',(0,0,0))),args.get('gripper',1),**extras)],obs.eef_xyz)
        if name=='set_gripper': return [jaw(args['gripper'],args.get('steps',8))]
        if name=='release': return [Stage('release',{'max_steps':args.get('steps',12)},args.get('steps',12))]
        if name=='rotate_wrist': return [Stage(name,args,max_steps)]
        if name in ('vla','vla_contact'):
            return [Stage('vla',{'instruction':args.get('instruction',obs.task)},max_steps)]
        if name=='pick' and args.get('executor')=='vla':
            return [Stage('vla_pick',{'instruction':args.get('instruction',f"pick up {args['target']}")},max_steps)]
        stages=[]
        if name in ('pick','pick_place'):
            p=at('target',args.get('grasp_offset',(0,0,0)))
            above=add(p,(0,0,clearance))
            if yaw is not None: stages.append(rot(yaw))
            stages += [jaw(-1),move(above,-1),move(p,-1),jaw(1),move(above,1)]
        if name in ('place','pick_place'):
            p=at('destination',args.get('place_offset',(0,0,0)))
            above=add(p,(0,0,clearance))
            stages += [move(above,1),move(p,1),jaw(-1),move(above,-1)]
        if name in ('push','pull_handle','swing_handle'):
            p=at('target')
            approach=add(p,args.get('approach_offset',(0,0,0.08)))
            if yaw is not None: stages.append(rot(yaw))
            stages += [jaw(-1),move(approach,-1),move(p,-1)]
            grip=args.get('gripper',1.0)
            stages.append(jaw(grip))
            if name in ('push','pull_handle'):
                d=vec(args['direction'],'direction')
                end=add(p,tuple(v/norm(d)*args['distance'] for v in d))
                stages.append(move(end,grip))
            else:
                # Axis/pivot are supplied explicitly from evidence, never read
                # from hidden fixture source geometry in the sensor condition.
                pivot=at('pivot'); axis=vec(args['axis'],'axis'); length=norm(axis)
                axis=tuple(x/length for x in axis); r=sub(p,pivot)
                n=max(2,int(abs(args['angle'])/0.12)+1)
                for i in range(1,n+1):
                    t=args['angle']*i/n; c,s=math.cos(t),math.sin(t)
                    cross=(axis[1]*r[2]-axis[2]*r[1],axis[2]*r[0]-axis[0]*r[2],axis[0]*r[1]-axis[1]*r[0])
                    dot=sum(a*b for a,b in zip(axis,r))
                    rr=tuple(r[j]*c+cross[j]*s+axis[j]*dot*(1-c) for j in range(3))
                    stages.append(move(add(pivot,rr),grip))
            stages.append(jaw(-1))
        if not stages:
            raise Unavailable(f'no_executor:{name}')
        # Segment long free-space translations consistently in BOTH conditions.
        # This is controller protection, not global collision avoidance.
        return self._split_moves(stages,obs.eef_xyz)

    @staticmethod
    def _split_moves(stages,previous):
        split=[]
        for stage in stages:
            if stage.progress_target is not None:
                d=sub(stage.progress_target,previous)
                n=max(1,math.ceil(norm(d[:2])/0.24))
                for i in range(1,n+1):
                    p=add(previous,tuple(v*i/n for v in d))
                    split.append(Stage(stage.operation,{**stage.arguments,'xyz':list(p)},
                                       stage.max_steps,p,stage.progress_tolerance))
                previous=stage.progress_target
            else: split.append(stage)
        return split
