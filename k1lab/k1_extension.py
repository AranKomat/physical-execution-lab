"""Use K1's *actual* registry_class seam; no rewrite of its perception/model loop.

Native dependency is fetched at a pinned revision. Tests inject a contract double;
they do not imply that the external package or simulator was executed here.
"""
from __future__ import annotations
from copy import deepcopy
from .contracts import Limits
from .engine import ExecutionEngine
from .errors import ContractError,Unavailable


def tool(name,description,properties,required):
    return {'type':'function','function':{'name':name,'description':description,'parameters':{
        'type':'object','properties':properties,'required':required,'additionalProperties':False}}}


def extension_schemas(obs,limits,sparse,policy,grasp_macro=True):
    integer={'type':'integer'}; text={'type':'string'}; n={'type':'number'}
    vec={'type':'array','items':n,'minItems':3,'maxItems':3}
    quat={'type':'array','items':n,'minItems':4,'maxItems':4}
    common={'frame_id':integer,'arm':{'type':'string','enum':list(obs['arms'])},'command_id':text,
            'decision_note':{'type':'string','description':'Brief evidence-grounded action summary, not hidden reasoning.'}}
    schemas=[]
    if sparse:
        props={**common,'segments':{'type':'array','minItems':1,'maxItems':limits.max_segments,'items':{
            'type':'object','properties':{'kind':{'type':'string','enum':['pose','gripper']},
                'target_xyz_world_m':vec,'target_quaternion_xyzw':quat,'gripper':{'type':'number','minimum':0,'maximum':1},
                'profile':{'type':'string','enum':['transit','approach']},'settle_steps':{'type':'integer','minimum':1,'maximum':30}},
            'required':['kind'],'additionalProperties':False}},
            'max_native_steps':{'type':'integer','minimum':1,'maximum':limits.max_command_steps},
            'watch_points':{'type':'array','items':text,'maxItems':12}}
        schemas.append(tool('execute_motion_plan',
            'Execute a SHORT newly proposed sequence of generic pose/gripper operations without another VLM call between them. '
            'Use current measured evidence and known free space; no path planning or collision guarantee. Explicit pose steps '
            'preserve gripper. Stop on undertracking, budget, lease or watched point motion/loss. Gripper completion is not attachment. '
            'Use individual K1 tools for uncertain contact and new observation decisions. Each plan is per-episode, not a task recipe.',
            props,['frame_id','arm','command_id','segments','max_native_steps']))
        schemas.append(tool('grasp_from_candidate',
            'Attempt one CURRENT K1 grasp candidate: pregrasp, approach, close, 8..30mm probe lift. '
            'Jaws must already be open. Requires a CURRENT measured/tracked target point; uses only cached sensor-derived '
            'candidate geometry. No grasp, identity or collision certificate; co-motion can be supported/contradicted/unknown. '
            'After unknown or failure inspect current evidence; no hidden retry or transport follows.',
            {**common,'candidate_id':text,'point_id':text,'lift_delta_world_m':vec,
             'max_native_steps':{'type':'integer','minimum':1,'maximum':limits.max_command_steps}},
            ['frame_id','arm','command_id','candidate_id','point_id','lift_delta_world_m','max_native_steps']))
    if policy:
        schemas.append(tool('vla_act',
            'Execute the configured frozen policy for a bounded subgoal using CURRENT sensor inputs. '
            'No hidden task state, task-memory retrieval or model training. Analytic transit is usually cheaper. '
            'Use only within the policy embodiment and distribution; missing geometry is NOT automatically solved by a VLA. '
            'Returns actual steps and observations, not a subgoal-success certificate. Discards unexecuted actions at handoff.',
            {**common,'subgoal':text,'max_native_steps':{'type':'integer','minimum':1,'maximum':limits.max_policy_steps}},
            ['frame_id','arm','command_id','subgoal','max_native_steps']))
    if not grasp_macro:schemas=[s for s in schemas if s['function']['name']!='grasp_from_candidate']
    return schemas


class K1Port:
    def __init__(self,registry): self.registry=registry; self.adapter=registry.adapter
    @property
    def frame(self): return self.adapter.frame
    @property
    def horizon(self): return self.adapter.horizon
    @property
    def control_hz(self): return self.adapter.observe()['capabilities']['control_hz']
    @property
    def action_space(self): return getattr(self.adapter,'action_space',None)
    @property
    def policy_contract(self): return getattr(self.adapter,'policy_contract',{})
    def observe(self): return self.registry.observe()
    def points(self): return self.registry.tracked_points.context()
    def success(self): return bool(self.adapter.success())
    def servo(self,arm,xyz,q,gripper):
        self.registry.motion._record(arm,self.adapter.observe()['arms'][arm])
        return self.adapter.move_to_position(arm,xyz,q,gripper,1)
    def native_action(self,action):
        method=getattr(self.adapter,'execute_native_action7',None)
        if method is None:raise Unavailable('no qualified raw-action adapter')
        return method(action)
    def policy_observation(self,subgoal):
        method=getattr(self.adapter,'policy_observation',None)
        if method is None:raise Unavailable('no qualified policy observation encoder')
        return method(subgoal)


def registry_factory(*,sparse=False,policy=None,limits=None,journal=None,base_class=None,grasp_macro=True):
    if base_class is None:
        from robo_harness.runtime import ToolRegistry
        base_class=ToolRegistry
    limits=limits or Limits()
    class ExtendedRegistry(base_class):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw)
            self.extension_candidates={}
            self.extension_engine=ExecutionEngine(K1Port(self),limits,journal)
        def schemas(self,obs):
            return super().schemas(obs)+extension_schemas(obs,limits,sparse,policy is not None,grasp_macro)
        def execute(self,name,args,obs):
            if name in ('execute_motion_plan','grasp_from_candidate','vla_act'):
                if obs['frame_id']!=self.adapter.frame:raise ContractError('stale registry observation')
                try:
                    if name=='execute_motion_plan':
                        if not sparse:raise ContractError('sparse executor disabled')
                        result=self.extension_engine.execute(args)
                    elif name=='grasp_from_candidate':
                        if not sparse or not grasp_macro:raise ContractError('grasp macro disabled')
                        candidate=self.extension_candidates.get(args.get('candidate_id'))
                        if candidate is None:raise ContractError('unknown/unobserved grasp candidate')
                        result=self.extension_engine.grasp(args,candidate,self.tracked_points.context())
                    else:
                        if policy is None:raise Unavailable('policy disabled')
                        result=self.extension_engine.run_policy(args,policy)
                    self.adapter.last_feedback=result
                    return result
                finally:
                    # New native motions supersede legacy intentions, not saved target history.
                    arm=args.get('arm')
                    self.waypoints.pop(arm,None)
                    self.pose_targets.active.pop(arm,None)
                    self.motion.retreat_goals.pop(arm,None)
                    self.motion.low.pop(arm,None)
            result=super().execute(name,args,obs)
            if name=='grasp_candidates' and isinstance(result,dict):
                for c in result.get('candidates',[]):
                    # Do not copy hidden scoring/ranking diagnostics into the executor contract.
                    keep={k:deepcopy(c[k]) for k in ('candidate_id','target_quaternion_xyzw','pregrasp_tcp_world_m','candidate_tcp_world_m') if k in c}
                    keep.update(frame_id=obs['frame_id'],arm=args['arm'])
                    if len(keep)==6:self.extension_candidates[keep['candidate_id']]=keep
            return result
    return ExtendedRegistry
