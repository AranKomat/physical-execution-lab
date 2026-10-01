from __future__ import annotations
from dataclasses import dataclass
import time
from .contracts import Proposal, Receipt, Stage
from .errors import ValidationError, Unavailable, BudgetExceeded, Interrupted, NativeTerminal, UncertainExecution
from .util import digest, norm, sub, plain, integer, finite


@dataclass(frozen=True)
class GovernorConfig:
    dynamic: bool = True
    check_every_steps: int = 10  # 2 Hz at a qualified 20 Hz environment rate.
    stall_checks: int = 4
    min_progress_m: float = 0.001
    stage_warmup_steps: int = 20
    allow_substitution: bool = True

    def __post_init__(self):
        integer(self.check_every_steps,'check_every_steps',1,1000)
        integer(self.stall_checks,'stall_checks',1,1000)
        integer(self.stage_warmup_steps,'stage_warmup_steps',0,10000)
        finite(self.min_progress_m,'min_progress_m',0,1)


class Governor:
    """Deterministic simulator execution governor. NOT a certified safety controller.

    Every backend must call before_step and after_step for EACH native action,
    including actions inside VLA chunks. Terminal verdicts are latched before any
    more motion. Nominal and dynamic share numeric guards and global budgets;
    only dynamic enables intra-command stagnation and eligible substitutions.
    """
    def __init__(self, backend, registry, budget, journal, config: GovernorConfig):
        self.backend,self.registry,self.budget,self.journal=backend,registry,budget,journal
        self.config=config
        self.cache={}
        self.terminal=False
        self.poisoned=False
        self.busy=False
        self.command_start=0
        self.command_budget=0
        self.stage=None
        self.stage_start=0
        self.best_error=None
        self.stalls=0
        self.events=[]
        backend.set_hooks(self.before_step,self.after_step,self.before_vla)

    def before_vla(self):
        if self.terminal or self.poisoned:
            raise UncertainExecution('executor_not_available')
        self.budget.take_vla_call()
        self.journal.append('vla_query',{'index':self.budget.vla_calls,'sim_step':self.backend.steps})

    def before_step(self, action):
        if self.poisoned:
            raise UncertainExecution('unresolved_prior_write')
        if self.terminal:
            raise NativeTerminal(self.backend.native_success)
        self.budget.before_step()
        if self.budget.steps-self.command_start>=self.command_budget:
            raise Interrupted('command_step_budget')
        if self.stage is not None and self.budget.steps-self.stage_start>=self.stage.max_steps:
            raise Interrupted('stage_step_budget')
        # Validated again by native backend, never silently clips learned outputs.
        from .util import vec
        vec(list(action),'native_action',7,-1.000001,1.000001)

    def after_step(self, observation, action):
        self.budget.record_step()
        self.journal.append('native_step',{'sim_step':observation.sim_step,
            'observation_id':observation.observation_id,'action':list(action),
            'eef_xyz':list(observation.eef_xyz),'gripper_width':observation.gripper_width,
            'executor':self.stage.operation if self.stage else None})
        # Native predicate is evaluator/termination authority in EVERY arm. It is
        # not a dense planner feature and not a geometry oracle.
        if self.backend.native_success or self.backend.native_truncated:
            self.terminal=True
            self.journal.append('terminal_latched',{'native_success':self.backend.native_success,
                                                    'sim_step':observation.sim_step})
            raise NativeTerminal(self.backend.native_success)
        if not self.config.dynamic or self.stage is None:
            return
        step_delta=self.budget.steps-self.stage_start
        if step_delta % self.config.check_every_steps:
            return
        if self.stage.progress_target is None:
            # EEF motion or jaw gap is not reliable task progress for contact VLA.
            # No suitable measured metric => bounded execution, not invented score.
            self.journal.append('monitor',{'decision':'continue','progress':'unavailable',
                                           'sim_step':observation.sim_step})
            return
        err=norm(sub(self.stage.progress_target,observation.eef_xyz))
        if self.best_error is None or self.best_error-err>=self.config.min_progress_m:
            self.best_error,self.stalls=err,0
        elif step_delta>=self.config.stage_warmup_steps and err>self.stage.progress_tolerance:
            self.stalls+=1
        event={'decision':'interrupt' if self.stalls>=self.config.stall_checks else 'continue',
               'metric':'eef_position_error_m','value':err,'stall_checks':self.stalls,
               'sim_step':observation.sim_step}
        self.journal.append('monitor',event)
        if self.stalls>=self.config.stall_checks:
            self.events.append({'kind':'stagnation',**event})
            raise Interrupted('stagnation')

    def execute(self,p: Proposal):
        ph=digest(p)
        if p.proposal_id in self.cache:
            old_hash,receipt=self.cache[p.proposal_id]
            if ph!=old_hash:
                raise ValidationError('idempotency_key_payload_conflict')
            return receipt
        obs=self.backend.observe()
        start_id=obs.observation_id
        start_steps=self.budget.steps
        self.events=[]
        if self.busy:
            raise ValidationError('actuator_already_owned')
        if self.poisoned:
            raise UncertainExecution('unresolved_prior_write')
        if self.terminal:
            return Receipt(p.proposal_id,'refused','episode_terminal',p.capability,
                           start_id,start_id,0)
        def close(status,reason,details=None,effect=None):
            end=self.backend.observe()
            r=Receipt(p.proposal_id,status,reason,p.capability,start_id,end.observation_id,
                      self.budget.steps-start_steps,effect,details or {},list(self.events))
            self.journal.append('receipt',plain(r))
            self.cache[p.proposal_id]=(ph,r)
            return r
        self.journal.append('proposal',plain(p))
        if p.observation_id!=start_id:
            return close('refused','stale_observation')
        self.command_start=self.budget.steps
        self.command_budget=min(p.max_steps,self.budget.max_steps-self.budget.steps)
        self.busy=True
        try:
            spec=self.registry.validate(p.capability,p.arguments)
            for alt in p.alternatives:
                if not self.registry.equivalent(p.capability,p.arguments,alt):
                    raise ValidationError('alternative_changes_semantic_effect')
            if spec.read_only:
                if p.capability=='finish':
                    return close('unverified','agent_finish_without_native_success')
                result=self.backend.query(p.capability,p.arguments,registry=self.registry)
                return close('completed','observation_returned',result,True)
            candidates=[{'capability':p.capability,'arguments':p.arguments}]
            if self.config.dynamic and self.config.allow_substitution:
                candidates+=list(p.alternatives)
            last_reason='no_candidate'
            results=[]
            for index,candidate in enumerate(candidates):
                if index:
                    self.events.append({'kind':'substitution','candidate':index,
                                        'reason':last_reason,'to':candidate})
                    self.journal.append('substitution',self.events[-1])
                current=self.backend.observe()
                try:
                    stages=self.registry.compile(candidate['capability'],candidate['arguments'],
                        current,self.command_budget,dynamic=self.config.dynamic)
                    self.journal.append('command',{'proposal_id':p.proposal_id,'candidate':index,
                                                  'stages':plain(stages)})
                    for stage in stages:
                        self.stage=stage
                        self.stage_start=self.budget.steps
                        self.best_error=None; self.stalls=0
                        self.journal.append('stage_start',plain(stage))
                        result=self.backend.execute_stage(stage)
                        results.append(result)
                        if stage.operation in ('vla','vla_pick') and not self.backend.native_success:
                            if self.budget.steps>=self.budget.max_steps:
                                raise BudgetExceeded('episode_step_budget')
                            if self.budget.steps-self.command_start>=self.command_budget:
                                raise Interrupted('command_step_budget')
                        # Same command-end check in both conditions. A reached TCP
                        # is kinematic evidence, never proof the object is seated.
                        if stage.progress_target is not None:
                            err=norm(sub(stage.progress_target,self.backend.observe().eef_xyz))
                            if err>stage.progress_tolerance:
                                raise Interrupted('target_not_reached')
                        self.journal.append('stage_end',{'result':result})
                    effect=self.backend.verify_effect(candidate['capability'],candidate['arguments'])
                    return close('completed' if effect is True else 'unverified',
                                 'effect_verified' if effect is True else 'execution_finished_effect_unverified',
                                 {'stage_results':results},effect)
                except (Unavailable,Interrupted) as e:
                    if isinstance(e,NativeTerminal): raise
                    last_reason=str(e)
                    self.journal.append('candidate_failed',{'candidate':index,'reason':last_reason})
                    if self.budget.steps-self.command_start>=self.command_budget:
                        break
            return close('interrupted',last_reason,{'stage_results':results},False)
        except NativeTerminal as e:
            self.terminal=True
            return close('completed' if e.success else 'interrupted',str(e),effect=None)
        except BudgetExceeded as e:
            return close('interrupted',str(e))
        except (ValidationError,Unavailable) as e:
            return close('refused',str(e))
        except UncertainExecution:
            self.poisoned=True
            self.journal.append('execution_uncertain',{'proposal_id':p.proposal_id,
                'action':'No automatic retry; this episode requires reconciliation.'})
            raise
        finally:
            self.busy=False; self.stage=None
