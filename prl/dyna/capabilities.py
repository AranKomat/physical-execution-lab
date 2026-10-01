"""Reconstruct the paper's geometric/contact competence, not just its scheduler.

Appendix A/Table 4 and D.4 provide stages, costs and selected revisions, but not
all controllers, tolerances or the exact seven-entry removal roster. The library
below is an explicit implementation of the documented capability families.
The paper map labels inferred details. Native success is never set by these skills.
"""
from dataclasses import dataclass, field
import math
import numpy as np
from scipy.spatial.transform import Rotation
from .scene import Scene, ExecutionMemory, v3, rotation
from .protocol import PaperSettings
from ..errors import ValidationError, Unavailable
from ..util import plain, digest

CONTACT = ('pick_and_place','execute_insertion','push_object','slide_drawer',
           'turn_knob','swing_door','handle_turn')
RECOVERY = ('keyframe_return','release_and_retreat','regrasp','reseat')
# The paper names six recovery/intervention entries but does not enumerate their
# exact IDs. Four documented families are reconstructed here; do not call the
# local no_recovery arm an exact six-entry removal.
SCHEMAS = {
 'perception': ((),()),
 'pick_and_place': (('object','destination'),('relation',)),
 'execute_insertion': (('object','destination'),()),
 'push_object': (('object','destination'),('relation','method_constraint')),
 'slide_drawer': (('object','state'),()),
 'turn_knob': (('object','state'),()),
 'swing_door': (('object','state'),()),
 'handle_turn': (('object','state'),()),
 'keyframe_return': (('keyframe',),()),
 'release_and_retreat': ((),()),
 'regrasp': (('object',),()),
 'reseat': (('object',),()),
 'vla_act': ((),('instruction',)),
 'finish': ((),()),
}
RELATIONS=('on','in','left_of','right_of','front_of','behind','next_to')


@dataclass
class Phase:
    name: str
    kind: str
    steps: int
    xyz: tuple | None = None
    quat: tuple | None = None
    gripper: float = 1.0
    object_target: bool = False
    verify: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class GroundedCommand:
    capability: str
    arguments: dict
    phases: list[Phase]
    expected_steps: int
    scene_id: str
    effect: dict
    initial: dict = field(default_factory=dict)
    grounding_source: str = 'privileged_sim'


class Refusal(Unavailable):
    def __init__(self, reason, *, kind='grounding', alternatives=()):
        super().__init__(reason)
        self.kind=kind
        self.alternatives=tuple(alternatives)


def top_down(yaw=0.0):
    return tuple((Rotation.from_euler('z',yaw)*Rotation.from_euler('x',math.pi)).as_quat())


def tool_orientation(direction, jaw_axis):
    z=v3(direction); z/=np.linalg.norm(z)
    x=v3(jaw_axis); x-=z*np.dot(x,z)
    if np.linalg.norm(x)<1e-6:
        x=np.cross(z, [0,0,1] if abs(z[2])<0.9 else [0,1,0])
    x/=np.linalg.norm(x); y=np.cross(z,x)
    return tuple(Rotation.from_matrix(np.column_stack((x,y,z))).as_quat())


def corridor_height(scene, a, b, carried, clearance, workspace_max_z=1.6):
    """Swept object AABBs -> conservative overhead height. Not full-arm planning."""
    a,b=v3(a),v3(b); radius=max(carried.aabb_half[:2])
    lo=np.minimum(a[:2],b[:2])-radius; hi=np.maximum(a[:2],b[:2])+radius
    h=max(a[2],b[2])+clearance
    for obj in scene.entities.values():
        if obj.name==carried.name or obj.kind in ('region','handle'): continue
        p=v3(obj.xyz); e=obj.aabb_half
        if np.all(p[:2]+e[:2]>=lo) and np.all(p[:2]-e[:2]<=hi):
            h=max(h,obj.top+carried.aabb_half[2]+clearance)
    if h>workspace_max_z: raise Refusal('transport_corridor_exceeds_workspace')
    return float(h)


def destination_position(scene, obj, dst, relation, memory, clearance):
    """Choose distinct receptacle slots; never treat every fixture as a cavity."""
    if relation not in RELATIONS: raise Refusal('unsupported_goal_relation')
    p=v3(dst.xyz); ext=dst.aabb_half; own=obj.aabb_half
    if relation=='in':
        region_type=dst.attributes.get('region_type')
        if region_type not in ('cavity','receptacle'):
            # Named region IDs may be explicit. Do not infer inside from fixture.
            children=[e for e in scene.entities.values() if e.parent==dst.name and
                      e.attributes.get('region_type') in ('cavity','receptacle')]
            if len(children)!=1: raise Refusal('destination_has_no_unambiguous_cavity')
            dst=children[0]; p=v3(dst.xyz); ext=dst.aabb_half
        # Guard the exact failure described in Appendix D.4 (flat 5 mm hob).
        if 2*ext[2] < 2*own[2]+0.005:
            raise Refusal('cavity_height_cannot_contain_object')
        span=ext[:2]-own[:2]-0.005
        if np.any(span<=0): raise Refusal('receptacle_slot_too_small')
        occupied=[]
        for e in scene.entities.values():
            if e.name in (obj.name,dst.name,dst.parent) or e.kind!='object':continue
            if np.all(np.abs(v3(e.xyz)[:2]-p[:2]) < ext[:2]+e.aabb_half[:2]):
                occupied.append(e)
        # Deterministic center-first candidates; no task-index coordinate tables.
        candidates=[(0,0),(-0.65,0),(0.65,0),(0,-0.65),(0,0.65),
                    (-0.65,-0.65),(0.65,0.65),(-0.65,0.65),(0.65,-0.65)]
        for x,y in candidates:
            q=p.copy(); q[:2]+=[x*span[0],y*span[1]]
            q[2]=dst.bottom+own[2]+0.004
            if any(np.all(np.abs(q[:2]-v3(o.xyz)[:2]) < own[:2]+o.aabb_half[:2]+0.006)
                   for o in occupied): continue
            return q
        raise Refusal('no_free_receptacle_slot')
    if relation=='on':
        children=[e for e in scene.entities.values() if e.parent==dst.name and
                  e.attributes.get('region_type')=='support']
        if len(children)==1: dst=children[0]; p=v3(dst.xyz)
        p[2]=dst.top+own[2]+0.004
        return p
    # Axes follow explicit shared world coordinates, not changing camera views.
    axis,sign={'left_of':(1,1),'right_of':(1,-1),'front_of':(0,-1),
               'behind':(0,1),'next_to':(1,-1)}[relation]
    p[axis]+=sign*(ext[axis]+own[axis]+clearance)
    # The tabletop height is geometric support, not dst's cavity or goal reward.
    supports=[e.top for e in scene.entities.values() if e.attributes.get('region_type')=='support'
              and e.top<=obj.bottom+0.03]
    p[2]=(max(supports) if supports else obj.bottom)+own[2]+0.004
    return p


class PaperLibrary:
    def __init__(self, settings=None, arm='A2ctrl'):
        self.settings=settings or PaperSettings(); self.arm=arm
        removed=set()
        if arm in ('no_contact','no_groups'): removed.update(CONTACT)
        if arm in ('no_recovery','no_groups'): removed.update(RECOVERY)
        if arm=='no_vla' or not self.settings.policy_enabled: removed.add('vla_act')
        self.names=tuple(n for n in SCHEMAS if n not in removed)

    @property
    def fingerprint(self):
        return digest({'version':'pdf-reconstruction-v2','catalog':self.names,
                       'settings':self.settings.fingerprint})

    def catalog(self):
        return [{'name':n,'required_symbolic_arguments':list(SCHEMAS[n][0]),
                 'optional_symbolic_arguments':list(SCHEMAS[n][1])} for n in self.names]

    def validate(self,name,args):
        if name not in self.names: raise Refusal('capability_not_in_catalog:'+name,kind='dispatch')
        required,optional=SCHEMAS[name]
        if not isinstance(args,dict) or set(required)-set(args) or set(args)-set(required+optional):
            raise ValidationError('symbolic_argument_schema:'+name)
        for k,v in args.items():
            if not isinstance(v,str) or not v or len(v)>2000:
                raise ValidationError('slow_brain_may_not_supply_geometry:'+k)
        if 'relation' in args and args['relation'] not in RELATIONS:
            raise ValidationError('invalid_relation')
        if 'state' in args and args['state'] not in ('open','closed','on','off'):
            raise ValidationError('invalid_mechanism_state')
        if 'method_constraint' in args and args['method_constraint'] not in ('final_relation','push_only'):
            raise ValidationError('invalid_method_constraint')

    def ground(self,name,args,scene:Scene,memory:ExecutionMemory,remaining:int):
        self.validate(name,args)
        s=self.settings
        E=lambda key:scene.entity(args[key],s.max_geometry_age_steps)
        phases=[]; initial={}; effect={'capability':name,**args}
        def move(n,xyz,steps,quat=None,grip=1,**kw):
            return Phase(n,'move',steps,tuple(v3(xyz)),quat,grip,**kw)
        def jaw(g,n,verify=None):return Phase('close' if g>0 else 'release','jaw',n,gripper=g,verify=verify)
        if name in ('perception','finish'):
            return GroundedCommand(name,args,[],0,scene.observation_id,effect)
        if name=='vla_act':
            if remaining<=0:raise Refusal('budget_exhausted',kind='budget')
            phases=[Phase('policy','vla',min(remaining,s.policy_command_actions),
                          metadata={'instruction':args.get('instruction',scene.task)})]
        elif name in ('pick_and_place','execute_insertion','push_object','regrasp'):
            obj=E('object'); initial={'object_xyz':obj.xyz,'object':obj.name}
            dst=E('destination') if 'destination' in args else None
            relation='in' if name=='execute_insertion' else args.get('relation','on')
            goal=destination_position(scene,obj,dst,relation,memory,s.minimum_clearance_m) if dst else None
            if name=='push_object':
                need=float(obj.attributes.get('push_contact_span_m',2*min(obj.half_size[:2])))
                if need>s.jaw_span_m:
                    alternatives=()
                    if args.get('method_constraint','final_relation')=='final_relation' and 'pick_and_place' in self.names:
                        alternatives=({'capability':'pick_and_place','arguments':{
                            'object':obj.name,'destination':dst.name,'relation':relation}},)
                    raise Refusal('push_contact_span_exceeds_jaw',kind='precondition',alternatives=alternatives)
                effect.update(goal_xyz=goal.tolist(),relation=relation,destination=dst.name)
                d=goal-v3(obj.xyz); d[2]=0
                if np.linalg.norm(d)<0.002:
                    return GroundedCommand(name,args,[],0,scene.observation_id,effect,initial)
                u=d/np.linalg.norm(d); contact=v3(obj.xyz)-u*(max(obj.aabb_half[:2])+0.012)
                phases=[move('push_approach',contact+[0,0,0.10],s.approach_steps,top_down(),-1),
                        move('push_contact',contact,s.descend_steps,top_down(),1),
                        move('push_sweep',contact+d,60,top_down(),1,verify='object_relation')]
            else:
                if memory.held_object not in (None,obj.name):
                    raise Refusal('held_object_mismatch',kind='precondition')
                # Use an explicit handle/grasp feature when available; an object's
                # bounding-box center is only a fallback reconstruction heuristic.
                features=[e for e in scene.entities.values() if e.parent==obj.name and e.kind=='handle']
                grasp=features[0] if len(features)==1 else obj
                gp=v3(grasp.xyz)
                yaw=math.atan2(grasp.R[1,0],grasp.R[0,0])
                q=top_down(yaw)
                if memory.held_object is None:
                    phases=[move('approach',gp+[0,0,0.12],s.approach_steps,q,-1),
                            move('guarded_descent',gp,s.descend_steps,q,-1),
                            jaw(1,s.close_steps),
                            move('lift',gp+[0,0,0.12],s.lift_steps,q,1,verify='grasp')]
                if goal is not None:
                    h=corridor_height(scene,gp,goal,obj,s.minimum_clearance_m)
                    carry=goal.copy(); carry[2]=h
                    climb=v3(obj.xyz);climb[2]=h
                    climb_steps=max(1,s.carry_steps//3)
                    # Climb before horizontal transport (paper Fig.19), rather
                    # than drawing a diagonal through an obstacle to the corridor.
                    phases += [move('corridor_climb',climb,climb_steps,q,object_target=True),
                               move('corridor',carry,s.carry_steps-climb_steps,q,object_target=True),
                               move('lower',goal,s.lower_steps,q,object_target=True),
                               jaw(-1,s.release_steps),
                               move('retreat',goal+[0,0,0.12],s.retreat_steps,q,-1,
                                    verify='object_relation')]
                    effect.update(goal_xyz=goal.tolist(),relation=relation,destination=dst.name)
        elif name in ('slide_drawer','turn_knob','swing_door','handle_turn','reseat'):
            j=scene.articulation(args['object']); h=scene.entity(j.handle,s.max_geometry_age_steps)
            desired=(j.open_position if args.get('state','open') in ('open','on') else j.closed_position)
            if desired is None:raise Refusal('mechanism_state_mapping_unresolved')
            delta=desired-j.position
            if abs(delta)<(0.01 if j.kind=='slide' else 0.04):
                return GroundedCommand(name,args,[],0,scene.observation_id,effect,
                                       {'joint':j.name,'desired':desired})
            axis=v3(j.axis);axis/=np.linalg.norm(axis)
            gp=v3(h.xyz)
            handle_axis=h.R[:,int(np.argmax(h.half_size))]
            if name=='slide_drawer':gp += handle_axis*s.drawer_handle_shift_m
            approach=axis*np.sign(delta) if j.kind=='slide' else h.R[:,2]
            q=tool_orientation(-approach,handle_axis)
            initial={'joint':j.name,'desired':float(desired),'start_joint':j.position,
                     'handle':j.handle,'grasp_xyz':gp.tolist()}
            phases=[move('handle_approach',gp+approach*0.10,30,q,-1),
                    move('handle_contact',gp,30,q,-1),jaw(1,s.close_steps)]
            if name=='reseat':
                # D.4 documents reseating after contact, but not this offset.
                phases=[jaw(-1,10),move('reseat',gp-h.R[:,2]*0.008,20,q,-1),jaw(1,10)]
            elif j.kind=='slide':
                phases += [move('pull',gp+axis*delta,136,q,verify='joint'),jaw(-1,10),
                           move('handle_retreat',gp+axis*delta+approach*0.06,23,q,-1)]
            else:
                phases += [Phase('wrist_turn' if name in ('turn_knob','handle_turn') else 'door_arc',
                    'arc',109 if name=='swing_door' else 109,tuple(gp),q,1,verify='joint',
                    metadata={'pivot':j.pivot,'axis':j.axis,'angle':float(delta),
                              'ramp_steps':s.wrist_ramp_steps}),jaw(-1,10),
                    move('handle_retreat',gp+approach*0.08,23,q,-1)]
        elif name=='keyframe_return':
            k=memory.keyframe(args['keyframe'],scene)
            if k['held_object']!=memory.held_object:raise Refusal('keyframe_grasp_state_mismatch')
            phases=[move('keyframe_return',k['xyz'],60,k['quat'],1 if memory.held_object else -1)]
        elif name=='release_and_retreat':
            phases=[jaw(-1,10),move('retreat',v3(scene.eef_xyz)+[0,0,0.10],23,None,-1)]
        else:raise Refusal('unimplemented_capability:'+name)
        cost=sum(p.steps for p in phases)
        if name in ('pick_and_place','execute_insertion') and memory.held_object is None:
            # Table 4 says about 230 overall; the listed stage midpoints sum to
            # 211. Reserve conservatively without inventing executed actions.
            cost=max(cost,s.pick_place_budget_floor)
        if cost>remaining:
            raise Refusal(f'cannot_afford_completion:need={cost}:remaining={remaining}',kind='budget')
        return GroundedCommand(name,dict(args),phases,cost,scene.observation_id,effect,initial,
                               scene.information_profile)

    def verify(self,command,phase,scene,memory):
        """Local effect evidence, distinct from the native benchmark verdict."""
        s=self.settings
        if phase.verify=='grasp':
            obj=scene.entity(command.initial['object'])
            pair=scene.finger_contacts.get(obj.name,(False,False))
            moved=float(obj.xyz[2]-command.initial['object_xyz'][2])
            if not all(pair) or moved<s.grasp_translation_m:
                return False,{'reason':'grasp_not_verified','both_finger_contacts':all(pair),'object_lift_m':moved}
            memory.held_object=obj.name
            memory.object_to_tcp=rotation(scene.eef_quat).T @ (v3(obj.xyz)-v3(scene.eef_xyz))
            return True,{'reason':'contact_and_object_lift_verified','object_lift_m':moved}
        if phase.verify=='joint':
            j=scene.articulations[command.initial['joint']]
            error=abs(j.position-command.initial['desired'])
            return error<(0.012 if j.kind=='slide' else 0.06),{'joint_error':error,'joint':j.name}
        if phase.verify=='object_relation':
            obj=scene.entity(command.initial['object'])
            err=float(np.linalg.norm(v3(obj.xyz)-v3(command.effect['goal_xyz'])))
            # Geometric local predicate, no fabricated force/contact certificate.
            return err<=s.release_tolerance_m,{'object_position_error_m':err,'predicate':'geometric_position_only'}
        return True,{'reason':'phase_executed'}
