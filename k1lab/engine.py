"""Bounded generic execution over a calibrated robot port.

No scene handles, object poses, task predicates beyond stop, or task-specific
routines. It never runs model calls while moving to an accepted pose target.
This is not a safety-rated controller or a collision-free planner.
"""
from __future__ import annotations
import time
import numpy as np
from scipy.spatial.transform import Rotation
from .contracts import Segment,Limits,envelope,parse_plan
from .evidence import CoMotion,point_at
from .errors import ContractError,StopExecution
from .util import vector,integer,number,keys,text,plain,digest


class ExecutionEngine:
    def __init__(self,port,limits=None,journal=None,clock=time.monotonic):
        self.port=port; self.limits=limits or Limits(); self.journal=journal; self.clock=clock
        self.receipts={}; self.active=False; self.policy_calls=0
    def log(self,event,value):
        if self.journal: self.journal.append(event,value)
    def _pose(self,obs,arm):
        try:
            s=obs['arms'][arm]
            return vector(s['xyz_world_m'],3),Rotation.from_quat(vector(s['quaternion_xyzw'],4))
        except (KeyError,ValueError) as e: raise ContractError('invalid robot proprioception') from e
    def _check(self):
        if self.port.success(): raise StopExecution('native_success')
        if self.port.frame>=self.port.horizon: raise StopExecution('episode_step_budget')
        if self.port.frame-self.begin>=self.step_budget: raise StopExecution('command_step_budget')
        if self.clock()>=self.deadline: raise StopExecution('command_lease_expired')
    def _tick(self,arm,xyz,rotation,gripper=None,watch=None,motion_evidence=None):
        self._check(); frame=self.port.frame
        xyz=vector(xyz,3)
        if np.any(xyz<self.limits.workspace_low) or np.any(xyz>self.limits.workspace_high):
            raise StopExecution('workspace_limit')
        self.port.servo(arm,xyz.tolist(),rotation.as_quat().tolist(),gripper)
        if self.port.frame != frame+1: raise StopExecution('native_step_accounting_mismatch')
        obs=self.port.observe(); self._pose(obs,arm)
        if obs['frame_id']!=self.port.frame: raise StopExecution('stale_native_observation')
        if motion_evidence: motion_evidence.update(obs,self.port.points())
        self.log('servo_tick',{'frame_id':self.port.frame,'target_xyz_world_m':xyz,
                              'actual':obs['arms'][arm],'gripper':gripper})
        if self.port.success(): raise StopExecution('native_success')
        if motion_evidence:
            feedback=motion_evidence.result()
            if feedback['reason']=='correspondence_or_depth_unavailable':raise StopExecution('co_motion_evidence_lost')
            if feedback['status']=='contradicted':raise StopExecution('co_motion_contradicted')
        for point_id,original in (watch or {}).items():
            current=point_at(self.port.points(),point_id,self.port.frame)
            if current is None: raise StopExecution('watched_feature_lost')
            if np.linalg.norm(current-original)>0.01: raise StopExecution('watched_feature_moved')
        return obs
    def _move(self,arm,segment,watch=None,motion_evidence=None):
        start_obs=self.port.observe(); start,_=self._pose(start_obs,arm)
        goal=vector(segment.xyz,3); goal_r=Rotation.from_quat(segment.quaternion)
        if np.linalg.norm(goal-start)>self.limits.max_translation_m:
            raise StopExecution('translation_bound_exceeded')
        hz=float(self.port.control_hz)
        if not np.isfinite(hz) or hz<=0: raise ContractError('invalid control rate')
        speed=self.limits.transit_m_s if segment.profile=='transit' else self.limits.approach_m_s
        best_distance=float('inf'); best_angle=float('inf'); progress_frame=self.port.frame; settled=0
        while True:
            self._check(); obs=self.port.observe(); pos,rot=self._pose(obs,arm)
            delta=goal-pos; distance=float(np.linalg.norm(delta))
            relative=goal_r*rot.inv(); angle=float(np.degrees(relative.magnitude()))
            if distance<=self.limits.position_tolerance_m and angle<=self.limits.angle_tolerance_deg:
                settled+=1
                if settled>=self.limits.settled_frames:
                    return {'status':'target_reached','remaining_distance_m':distance,'remaining_angle_deg':angle}
            else: settled=0
            if best_distance-distance>=self.limits.progress_m or best_angle-angle>=self.limits.progress_deg:
                progress_frame=self.port.frame; best_distance=distance; best_angle=angle
            if not settled and self.port.frame-progress_frame>=self.limits.stall_steps:
                raise StopExecution('pose_stagnation')
            # Physical velocity caps, not playback acceleration. Same underlying native controller.
            xyz=pos+delta*min(1.0,(speed/hz)/max(distance,1e-12))
            rv=relative.as_rotvec(); scale=min(1.0,(self.limits.angular_deg_s/hz)/max(angle,1e-12))
            q=Rotation.from_rotvec(rv*scale)*rot
            self._tick(arm,xyz,q,watch=watch,motion_evidence=motion_evidence)
    def _gripper(self,arm,value,steps,motion_evidence=None):
        xyz,r=self._pose(self.port.observe(),arm)
        for _ in range(steps): self._tick(arm,xyz,r,value,motion_evidence=motion_evidence)
        return {'status':'gripper_command_completed','opening_command':value,
                'attachment_verified':False}
    def _preflight(self,args,segments,budget):
        if self.active: raise ContractError('actuator_already_owned')
        if args['frame_id']!=self.port.frame: raise ContractError('stale_plan_frame')
        obs=self.port.observe()
        if obs['frame_id']!=self.port.frame: raise ContractError('stale_port_frame')
        position,_=self._pose(obs,args['arm'])
        for s in segments:
            if s.kind=='pose':
                target=vector(s.xyz,3)
                if np.linalg.norm(target-position)>self.limits.max_translation_m:
                    raise ContractError('plan contains overlong single motion')
                position=target
        if budget>self.port.horizon-self.port.frame:
            # Clamp shared budget, do not create a new episode budget.
            budget=self.port.horizon-self.port.frame
        minimum=sum(s.steps if s.kind=='gripper' else self.limits.settled_frames for s in segments)
        if minimum>budget: raise ContractError('episode cannot afford minimum plan steps')
        return obs,budget
    def _cached(self,args):
        key=args['command_id']; encoded=envelope(args)
        if key not in self.receipts: return None
        old=self.receipts[key]
        if old['request_sha256']!=encoded: raise ContractError('command_id_reused_with_different_request')
        return {**old,'replayed_receipt':True,'current_frame_id':self.port.frame,
                'receipt_is_historical':old['end_frame_id']!=self.port.frame}
    def execute(self,args):
        segments,budget,point_ids=parse_plan(args,self.limits)
        cached=self._cached(args)
        if cached: return cached
        obs,budget=self._preflight(args,segments,budget)
        watch={}
        for pid in point_ids:
            point=point_at(self.port.points(),pid,self.port.frame)
            if point is None: raise ContractError('watch point is not currently measured/tracked')
            watch[pid]=point
        return self._run(args,segments,budget,watch=watch)
    def _run(self,args,segments,budget,watch=None,comotion=None,lift_index=None):
        self.active=True; self.begin=self.port.frame; self.step_budget=budget
        self.deadline=self.clock()+self.limits.lease_s
        stages=[]; reason='completed'; evidence=None
        self.log('command_begin',{'command_id':args['command_id'],'frame_id':self.begin,
                                 'segments':[s.json() for s in segments],'budget':budget,
                                 'target_provenance':args.get('_provenance','actor_pose_proposal_not_geometry_certificate')})
        try:
            for i,s in enumerate(segments):
                if lift_index==i and comotion:
                    evidence=CoMotion(comotion,self.port.observe(),self.port.points(),args['arm'])
                stage_begin=self.port.frame
                self.log('stage_begin',{'index':i,'kind':s.kind,'frame_id':stage_begin})
                result=(self._move(args['arm'],s,watch,evidence) if s.kind=='pose'
                        else self._gripper(args['arm'],s.gripper,s.steps,evidence))
                stages.append({'index':i,'kind':s.kind,'steps':self.port.frame-stage_begin,**result})
        except StopExecution as exc:
            reason=exc.reason
        except Exception as exc:
            reason='executor_exception:'+type(exc).__name__
            self.log('executor_exception',{'type':type(exc).__name__,'message':str(exc)[:500]})
            # Return an authoritative partial receipt, never replay an uncertain command automatically.
        finally:
            self.active=False
        receipt={'command_id':args['command_id'],'request_sha256':envelope(args),
                 'start_frame_id':self.begin,'end_frame_id':self.port.frame,
                 'native_steps':self.port.frame-self.begin,'stop_reason':reason,'stages':stages,
                 'native_success':bool(self.port.success()),'automatic_retry':False,
                 'motion_plan_completed':reason=='completed',
                 'meaning':'Completed robot commands are not verified object attachment or task success.'}
        if comotion:
            receipt['co_motion']=evidence.result() if evidence else {'status':'unknown','reason':'probe_not_reached','attachment_verified':False}
            # A completed motion with unknown attachment must return to the planner.
            receipt['requires_visual_review']=receipt['co_motion']['status']!='supported'
        self.receipts[args['command_id']]=plain(receipt)
        self.log('command_end',receipt)
        return plain(receipt)
    def grasp(self,args,candidate,point_ids):
        keys(args,{'frame_id','arm','command_id','candidate_id','point_id','max_native_steps','lift_delta_world_m','decision_note'},
             {'frame_id','arm','command_id','candidate_id','point_id','max_native_steps','lift_delta_world_m'})
        integer(args['frame_id'],0,10**9,'frame_id'); text(args['command_id'],'command_id',120)
        cached=self._cached(args)
        if cached: return cached
        if candidate['frame_id']!=args['frame_id'] or candidate['arm']!=args['arm']:
            raise ContractError('candidate_frame_or_arm_mismatch')
        if candidate['candidate_id']!=args['candidate_id']: raise ContractError('candidate ID mismatch')
        if point_at(point_ids,args['point_id'],self.port.frame) is None:
            raise ContractError('a current tracked target feature is required before grasp macro')
        lift=vector(args['lift_delta_world_m'],3)
        if not 0.008<=np.linalg.norm(lift)<=self.limits.max_probe_lift_m+1e-9:
            raise ContractError('lift must be an 8..30mm evidence probe, not transport')
        obs=self.port.observe(); _,_=self._pose(obs,args['arm'])
        if obs['arms'][args['arm']].get('gripper_command_open',0)<0.9:
            raise ContractError('open jaws and reobserve before selecting a grasp candidate')
        q=vector(candidate['target_quaternion_xyzw'],4)
        contact=vector(candidate['candidate_tcp_world_m'],3)
        pre=vector(candidate['pregrasp_tcp_world_m'],3)
        values=[{'kind':'pose','target_xyz_world_m':pre.tolist(),'target_quaternion_xyzw':q.tolist()},
                {'kind':'pose','target_xyz_world_m':contact.tolist(),'target_quaternion_xyzw':q.tolist(),'profile':'approach'},
                {'kind':'gripper','gripper':0.0,'settle_steps':self.limits.gripper_settle_steps},
                {'kind':'pose','target_xyz_world_m':(contact+lift).tolist(),'target_quaternion_xyzw':q.tolist(),'profile':'approach'}]
        segments=[__import__('k1lab.contracts',fromlist=['parse_segment']).parse_segment(v,self.limits) for v in values]
        budget=integer(args['max_native_steps'],1,self.limits.max_command_steps,'max_native_steps')
        _,budget=self._preflight(args,segments,budget)
        # Candidate is a hypothesis. No collision-free or grasp guarantee is implied.
        result=self._run(args,segments,budget,comotion=args['point_id'],lift_index=3)
        return result

    def run_policy(self,args,provider):
        keys(args,{'frame_id','arm','command_id','subgoal','max_native_steps','decision_note'},
             {'frame_id','arm','command_id','subgoal','max_native_steps'})
        integer(args['frame_id'],0,10**9,'frame_id'); text(args['command_id'],'command_id',120)
        text(args['subgoal'],'subgoal',1000)
        cap=integer(args['max_native_steps'],1,self.limits.max_policy_steps,'max_native_steps')
        cached=self._cached(args)
        if cached:return cached
        if self.active or args['frame_id']!=self.port.frame: raise ContractError('busy_or_stale_policy_request')
        if args['arm'] not in self.port.observe()['arms']: raise ContractError('unknown arm')
        provider.validate_port(self.port)
        self.active=True; self.begin=self.port.frame; self.step_budget=cap; self.deadline=self.clock()+self.limits.lease_s
        reason='command_step_budget'; queries=0
        self.log('policy_command_begin',{'command_id':args['command_id'],'provider':provider.identity,'frame_id':self.begin})
        try:
            # No hidden analytic fallback and no task-specific policy memory.
            provider.reset_segment()
            while True:
                self._check()
                if self.policy_calls>=self.limits.max_policy_calls: raise StopExecution('policy_call_budget')
                packet=self.port.policy_observation(args['subgoal'])
                self.policy_calls+=1; queries+=1
                actions=provider.predict(packet)
                for action in actions:
                    self._check(); before=self.port.frame
                    self.port.native_action(action)
                    if self.port.frame!=before+1: raise StopExecution('native_step_accounting_mismatch')
                    self.log('policy_tick',{'frame_id':self.port.frame,'action':action})
                    if self.port.success():raise StopExecution('native_success')
        except StopExecution as exc: reason=exc.reason
        except Exception as exc:
            reason='policy_exception:'+type(exc).__name__
            self.log('policy_error',{'type':type(exc).__name__,'message':str(exc)[:500]})
        finally:
            self.active=False
            provider.reset_segment()  # discard unexecuted predictions, not the simulator state
        receipt={'command_id':args['command_id'],'request_sha256':envelope(args),'start_frame_id':self.begin,
                 'end_frame_id':self.port.frame,'native_steps':self.port.frame-self.begin,'policy_calls':queries,
                 'stop_reason':reason,'native_success':bool(self.port.success()),'policy_identity':provider.identity,
                 'meaning':'Policy actions executed within a bound; no local subgoal success is inferred.'}
        self.receipts[args['command_id']]=plain(receipt); self.log('policy_command_end',receipt)
        return plain(receipt)
