"""Three executors sharing a capability library and one bounded robot seam.

A2static replans after nominal local completion ONLY. Failed steps get one
same-step retry, one replay, and one retry of that replay; no failure replanning.
A2seq freezes the initial sequence. A2ctrl permits refusal/substitution/recovery
and failure-triggered replanning. Thresholds not published in the PDF are explicit
reconstruction settings rather than alleged exact implementation details.
"""
from dataclasses import dataclass
from pathlib import Path
import time
import math
import numpy as np
from scipy.spatial.transform import Rotation, Slerp
from .scene import ExecutionMemory,v3,rotation
from .capabilities import PaperLibrary,Refusal,RECOVERY
from .planner import Advisory,context_for
from .protocol import PaperSettings,ARMS
from ..util import plain,atomic_json,digest
from ..errors import ValidationError,Unavailable,BudgetExceeded


class StopExecution(Exception):pass
class CommandFailure(Exception):pass


@dataclass
class VerdictLatch:
    enabled: bool=True
    accumulated: bool=False
    current: bool=False
    samples: int=0
    first_success_step: int|None=None
    def sample(self,value,step):
        if not isinstance(value,(bool,np.bool_)):raise ValidationError('verdict_must_be_boolean')
        self.current=bool(value);self.samples+=1
        if self.current and self.first_success_step is None:self.first_success_step=step
        self.accumulated=(self.accumulated or self.current) if self.enabled else self.current
    def read(self):return self.accumulated


class Engine:
    def __init__(self,backend,planner,journal,settings=None,arm='A2ctrl',budget=300,out=None):
        if arm not in ARMS:raise ValidationError('unknown_paper_arm')
        self.backend,self.planner,self.journal=backend,planner,journal
        self.s=settings or PaperSettings();self.arm=arm
        self.library=PaperLibrary(self.s,arm);self.memory=ExecutionMemory()
        self.max_steps=budget;self.steps=0;self.ticks=0;self.success=False
        self.verdict=VerdictLatch(enabled=arm!='unlatched')
        self.started=time.monotonic();self.deadline=None;self.command_epoch=None
        self.out=Path(out) if out else None
        self.planner_calls=0;self.vla_calls=0;self.fast_decisions=0;self.refusals=0
        self.substitutions=0;self.recovery_insertions=0;self.failure_replans=0
        self.fixed_retries=0;self.fixed_replays=0;self.effects=[];self.receipts=[]
        self.cached_commands={};self.keyframe_counter=0
        self.current_phase=None;self.phase_best=None;self.stall_ticks=0
        self.dynamic=arm not in ('bare','A2static','A2seq')
        self.safety_checks=0;self.last_safety_time=None;self.pre_action_checks=0
        self.step_shares={"analytic":0,"policy":0,"gripper":0,"recovery":0}
        self.current_capability=None
        self.backend.set_safety_check(self.safety_check,self.s.safety_hz)

    def log(self,kind,data):return self.journal.append(kind,{'step':self.steps,**plain(data)})

    def safety_check(self,scene,*,pre_action=False):
        # Called at physics substeps by the direct LIBERO adapter. Counts are
        # recorded separately from 20 Hz actions and 2 Hz governor decisions.
        if pre_action:self.pre_action_checks+=1
        else:self.safety_checks+=1;self.last_safety_time=scene.simulation_time
        if time.monotonic()-self.started>=self.s.episode_wall_s:raise StopExecution('wall_limit')
        if self.deadline is not None and time.monotonic()>=self.deadline:raise CommandFailure('command_lease_expired')
        if scene.joint_velocity and max(abs(v) for v in scene.joint_velocity)>self.s.joint_velocity_rad_s:
            raise CommandFailure('measured_joint_velocity_envelope')
        if self.command_epoch and (scene.scene_epoch,scene.task_epoch)!=self.command_epoch:
            raise CommandFailure('command_epoch_invalidated')

    def tick(self,reason,scene=None):
        self.ticks+=1
        if reason=='continue':self.fast_decisions+=1
        if self.verdict.read():
            self.success=True;self.log('task_verdict_read',{'success':True,'first_detected_step':self.verdict.first_success_step})
            raise StopExecution('native_success')
        if self.ticks>=self.s.max_ticks:raise StopExecution('tick_limit')
        self.log('fast_decision' if reason=='continue' else 'scheduler_boundary',{'decision':reason,'tick':self.ticks,'governor_hz':self.s.governor_hz})

    def action(self,action):
        if self.steps>=self.max_steps:raise StopExecution('environment_step_budget')
        self.safety_check(self.backend.scene(),pre_action=True)
        scene,verdict=self.backend.step(action)
        self.steps+=1
        category=('policy' if self.current_phase and self.current_phase.kind=='vla' else
                  'recovery' if self.current_capability in RECOVERY else
                  'gripper' if self.current_phase and self.current_phase.kind=='jaw' else 'analytic')
        self.step_shares[category]+=1
        if scene.step!=self.steps:raise ValidationError('backend_step_accounting_mismatch')
        self.verdict.sample(verdict,self.steps)
        self.log('native_action',{'action':plain(action),'native_predicate':bool(verdict),
                                 'latched_verdict':self.verdict.read(),
                                 'phase':self.current_phase.name if self.current_phase else None,
                                 'eef_xyz':scene.eef_xyz})
        if self.steps % self.s.decision_stride==0:
            self.tick('continue',scene)
            if self.dynamic and self.current_phase and self.current_phase.kind=='move':
                # EEF metric only; zero displacement is not a force/contact estimate.
                target=self._phase_target
                error=float(np.linalg.norm(v3(scene.eef_xyz)-target))
                if self.phase_best is None or self.phase_best-error>=self.s.progress_delta_m:
                    self.phase_best=error;self.stall_ticks=0
                elif error>self.s.movement_tolerance_m:self.stall_ticks+=1
                self.log('progress_monitor',{'position_error_m':error,'stagnation_ticks':self.stall_ticks,
                                            'scope':'EEF_target_not_task_progress'})
                if self.stall_ticks>=self.s.stall_ticks:raise CommandFailure('verifier_stagnation')
        return scene

    def phase(self,phase,command):
        self.current_phase=phase;self.phase_best=None;self.stall_ticks=0
        start=self.backend.scene();p0=v3(start.eef_xyz);q0=tuple(start.eef_quat)
        target=v3(phase.xyz) if phase.xyz is not None else p0.copy()
        qtarget=phase.quat or q0
        if phase.object_target:
            if self.memory.held_object!=command.initial.get('object') or self.memory.object_to_tcp is None:
                raise CommandFailure('held_object_transform_unverified')
            target-=rotation(qtarget)@self.memory.object_to_tcp
        self._phase_target=target
        self.log('phase_started',{'phase':plain(phase),'resolved_tcp_target':target.tolist()})
        if phase.kind=='vla':
            used=0
            while used<phase.steps:
                self.vla_calls+=1
                actions=np.asarray(self.backend.policy_actions(phase.metadata['instruction']),float)
                if actions.shape!=(self.s.policy_chunk_actions,7) or not np.isfinite(actions).all():
                    raise ValidationError(f'paper_requires_10_action_chunks_received:{actions.shape}')
                self.log('vla_query',{'returned_actions':len(actions),'invocation':self.vla_calls})
                for a in actions[:min(len(actions),phase.steps-used)]:
                    self.action(a);used+=1
        else:
            slerp=Slerp([0,1],Rotation.from_quat([q0,qtarget]))
            for i in range(phase.steps):
                # Smooth approach; final steps settle under feedback. Paper gives
                # a four-step wrist ramp but not this interpolation law.
                fraction=min(1.,(i+1)/max(1,phase.steps-3))
                desired=p0+(target-p0)*fraction
                quat=tuple(slerp(fraction).as_quat())
                if phase.kind=='arc':
                    axis=v3(phase.metadata['axis']);axis/=np.linalg.norm(axis)
                    ramp=min(1.,(i+1)/phase.metadata['ramp_steps'])
                    f=fraction*ramp
                    rot=Rotation.from_rotvec(axis*phase.metadata['angle']*f)
                    pivot=v3(phase.metadata['pivot'])
                    desired=pivot+rot.apply(v3(phase.xyz)-pivot)
                    quat=tuple((rot*Rotation.from_quat(qtarget)).as_quat())
                if phase.kind=='jaw':desired=p0;quat=q0
                self.action(self.backend.pose_action(desired,quat,phase.gripper))
            scene=self.backend.scene()
            if phase.kind=='move':
                error=float(np.linalg.norm(v3(scene.eef_xyz)-target))
                angle=float((Rotation.from_quat(qtarget)*Rotation.from_quat(scene.eef_quat).inv()).magnitude())
                if error>self.s.movement_tolerance_m or angle>self.s.rotation_tolerance_rad:
                    raise CommandFailure(f'pose_not_reached:{error:.6f}:{angle:.6f}')
            ok,evidence=self.library.verify(command,phase,scene,self.memory)
            self.log('local_verification',{'phase':phase.name,'ok':ok,'evidence':evidence,
                                           'is_native_task_verdict':False})
            if not ok:raise CommandFailure(evidence.get('reason','local_effect_not_verified'))
            if phase.kind=='jaw' and phase.gripper<0:
                self.memory.held_object=None;self.memory.object_to_tcp=None
        self.log('phase_finished',{'phase':phase.name})
        self.current_phase=None

    def execute(self,intent,command_id):
        payload=digest(plain(intent))
        if command_id in self.cached_commands:
            ph,old=self.cached_commands[command_id]
            if ph!=payload:raise ValidationError('command_id_payload_conflict')
            return old
        scene=self.backend.scene();start=self.steps;self.refusal=None
        self.command_epoch=(scene.scene_epoch,scene.task_epoch)
        self.deadline=time.monotonic()+self.s.command_lease_s
        result={'capability':intent.capability,'arguments':intent.arguments,'status':'failed','reason':''}
        self.current_capability=intent.capability
        self.log('advisory',plain(intent))
        try:
            try:
                cmd=self.library.ground(intent.capability,intent.arguments,scene,self.memory,self.max_steps-self.steps)
            except Refusal:
                raise
            except Unavailable as e:
                # An unbound / stale physical entity is a grounding refusal,
                # not an infrastructure failure and not a dispatched motion.
                raise Refusal(str(e),kind='grounding') from e
            self.log('grounded_command',plain(cmd))
            if intent.capability=='finish':raise StopExecution('planner_requested_finish')
            if intent.capability=='perception':
                self.backend.capture();result.update(status='completed',reason='fresh_context')
            else:
                self.memory.record_keyframe(f'command_{self.keyframe_counter}',scene);self.keyframe_counter+=1
                for ph in cmd.phases:self.phase(ph,cmd)
                # A policy segment ending is NOT automatically a nominal skill
                # success: no local semantic effect verifier is published for it.
                result.update(status='completed' if intent.capability!='vla_act' else 'failed',
                              reason='local_completion' if intent.capability!='vla_act' else 'policy_segment_unverified')
                if result['status']=='completed':self.memory.completed.append(plain(intent))
        except Refusal as e:
            self.refusals+=1;self.refusal=e
            result.update(status='refused',reason=str(e),refusal_kind=e.kind,
                          alternatives=list(e.alternatives))
        except CommandFailure as e:
            result.update(status='failed',reason=str(e))
            if hasattr(self.backend,'save_failure_state') and self.out:
                self.backend.save_failure_state(self.out/f'failure_state_{command_id}')
        except StopExecution:
            result.update(status='terminal',reason='native_success' if self.success else 'execution_stopped')
            raise
        finally:
            result['native_steps']=self.steps-start
            self.log('command_receipt',result);self.receipts.append(result)
            self.cached_commands[command_id]=(payload,result)
            self.current_phase=None;self.deadline=None;self.command_epoch=None;self.current_capability=None
        if result['status']!='completed':self.memory.failures.append(result)
        return result

    def ask(self,reason,sequence=False):
        if self.planner_calls>=self.s.max_planner_calls:raise StopExecution('planner_call_ceiling')
        self.planner_calls+=1
        scene=self.backend.capture();pid=f'{scene.episode_id}:p{self.planner_calls}'
        c=context_for(scene,self.library,self.memory,self.max_steps-self.steps,pid,sequence=sequence,reason=reason)
        out=self.out/'turns'/f'{self.planner_calls:04d}' if self.out else Path('/tmp')/pid
        out.mkdir(parents=True,exist_ok=False);atomic_json(out/'context.json',c)
        t=time.monotonic();plan=self.planner.decide(c,out)
        self.log('slow_brain_completed',{'call':self.planner_calls,'reason':reason,'wall_s':time.monotonic()-t,
                                         'plan':plain(plan),'request_sha256':digest(c)})
        now=self.backend.scene()
        if (plan.scene_epoch,plan.task_epoch)!=(now.scene_epoch,now.task_epoch):
            raise ValidationError('stale_plan_epoch')
        if plan.observation_id!=scene.observation_id:raise ValidationError('stale_plan_observation')
        if time.monotonic()-plan.created_at>self.s.plan_validity_s:raise StopExecution('plan_expired')
        return plan

    def run(self):
        reason='not_started'; pending=[];nominal_failures=0;counter=0;recovery_for=set()
        plan=None;last_intent=None
        try:
            if self.arm=='A2seq':
                plan=self.ask('initial',True);pending=list(plan.steps)
            while self.steps<self.max_steps:
                self.tick('dispatch_boundary')
                if time.monotonic()-self.started>=self.s.episode_wall_s:raise StopExecution('wall_limit')
                if self.arm=='bare':intent=Advisory('vla_act',{})
                elif pending:intent=pending.pop(0)
                elif self.arm=='A2seq':raise StopExecution('frozen_sequence_exhausted')
                else:
                    plan=self.ask('initial' if self.planner_calls==0 else
                                  'failure' if nominal_failures else 'nominal_completion')
                    if nominal_failures:self.failure_replans+=1
                    intent=plan.steps[0];nominal_failures=0
                if plan and time.monotonic()-plan.created_at>self.s.plan_validity_s:
                    if self.arm=='A2seq':raise StopExecution('plan_expired')
                    pending=[];plan=None;continue
                counter+=1;receipt=self.execute(intent,str(counter));last_intent=intent
                if self.arm=='bare':continue
                if receipt['status']=='completed':
                    nominal_failures=0;continue
                nominal_failures+=1
                if self.arm in ('A2static','A2seq'):
                    if receipt['status']=='refused':
                        if receipt.get('refusal_kind')=='precondition':
                            # No model call while nominal execution waits for a
                            # precondition. No fictitious physical time advancement.
                            for _ in range(self.s.blocked_ticks):self.tick('blocked_precondition')
                        else:raise StopExecution('unresolvable_binding')
                    if nominal_failures>=4:raise StopExecution('fixed_retry_exhaustion')
                    pending.insert(0,intent)
                    if nominal_failures==2:
                        self.fixed_replays+=1;self.log('fixed_plan_reexecution',plain(intent))
                    else:
                        self.fixed_retries+=1;self.log('fixed_step_retry',plain(intent))
                    continue
                if self.dynamic:
                    if intent.capability=='vla_act':
                        # No trustworthy intermediate policy-effect predicate.
                        # Retain this route under the same episode budget.
                        pending.insert(0,intent);continue
                    alternatives=receipt.get('alternatives',[])
                    if alternatives:
                        alt=alternatives[0]
                        self.substitutions+=1;self.log('capability_substitution',{'from':plain(intent),'to':alt,
                                                                               'reason':receipt['reason']})
                        pending.insert(0,Advisory(alt['capability'],alt['arguments']));continue
                    # The documented drawer reseat is isolated from other skills.
                    signature=digest([intent.capability,intent.arguments])
                    if intent.capability=='slide_drawer' and self.s.drawer_reseat_enabled and \
                       'reseat' in self.library.names and signature not in recovery_for and receipt['status']=='failed':
                        recovery_for.add(signature);self.recovery_insertions+=1
                        pending=[Advisory('reseat',{'object':intent.arguments['object']}),intent]+pending
                        self.log('recovery_insertion',{'family':'reseat','for':plain(intent)})
                    elif (receipt.get('refusal_kind')=='budget' or self.max_steps-self.steps<80) and 'vla_act' in self.library.names:
                        pending=[Advisory('vla_act',{})]+pending
                        self.log('remaining_budget_policy_route',{'remaining':self.max_steps-self.steps})
                    elif receipt.get('refusal_kind')=='budget':
                        raise StopExecution('no_affordable_capability')
                    # Else next iteration calls the slow brain with current evidence.
            reason='environment_step_budget'
        except StopExecution as e:reason=str(e)
        # Final read is an evaluation boundary, not a dense goal signal to planner.
        # In unlatched mode only the final/current sample is available.
        if self.verdict.read():self.success=True;reason='native_success'
        return {'native_success':self.success,'reason':reason,'native_steps':self.steps,
                'ticks':self.ticks,'fast_decisions':self.fast_decisions,'planner_calls':self.planner_calls,
                'vla_calls':self.vla_calls,'refusals':self.refusals,'substitutions':self.substitutions,
                'recovery_insertions':self.recovery_insertions,'failure_replans':self.failure_replans,
                'fixed_retries':self.fixed_retries,'fixed_replays':self.fixed_replays,
                'success_first_sample_step':self.verdict.first_success_step,
                'predicate_samples':self.verdict.samples,'safety_checks':self.safety_checks,
                'pre_action_checks':self.pre_action_checks,
                'actual_model_calls':getattr(self.planner,'calls',0),
                'steps_by_executor':dict(self.step_shares),
                'wall_s':time.monotonic()-self.started}
