"""Within-episode state only. Semantic progress is a claim, never reward truth."""
from __future__ import annotations
from dataclasses import asdict
from .contracts import SemanticContext, ScheduleConfig, check_decision
from k1lab.errors import ContractError

SOFT_EVENTS = ('tracking_lost', 'target_motion_contradicted', 'execution_failed')


class SemanticState:
    def __init__(self, original_task, prompt_mode, schedule=None):
        self.context = SemanticContext(original_task, prompt_mode=prompt_mode)
        self.schedule = schedule or ScheduleConfig()
        if (prompt_mode == 'task_plus_correction') != self.schedule.mistake_only_coaching:
            raise ContractError('correction prompt mode requires mistake-only coaching and vice versa')
        self.memory = {'completed_claims': [], 'uncertain_or_invalidated': [], 'claims_not_verified_truth': True}
        self.last_review = None
        self.goal_started_at = 0
        self.last_event_review = -10**12
        self.last_signals = set()
        self.pending_events = set()
        self.visited_evidence = set()

    def observe(self, obs):
        if obs.instruction != self.context.original_task:
            raise ContractError('native task changed; do not overwrite original instruction')
        self.visited_evidence.add(obs.step)
        active = {name for name in SOFT_EVENTS if obs.signals.get(name) is True}
        self.pending_events.update(active - self.last_signals)
        self.last_signals = active

    def due(self, obs):
        if self.last_review is None:
            return ['initial_semantic_goal']
        reasons = []
        if obs.step - self.last_review >= self.schedule.review_interval_steps:
            reasons.append('periodic_semantic_check_at_native_boundary')
        if self.pending_events and obs.step - self.last_event_review >= self.schedule.event_cooldown_steps:
            reasons.extend(sorted(self.pending_events))
        return reasons

    def apply(self, d, obs, *, shadow=False, max_age_steps=0):
        age = check_decision(d, obs, self.context, max_age_steps=max_age_steps)
        self.last_review = obs.step
        if self.pending_events:
            self.last_event_review = obs.step
        self.pending_events.clear()
        if any(s not in self.visited_evidence for c in d.completed_claims for s in c.evidence_steps):
            raise ContractError('claim cites evidence not observed in this episode')
        if self.schedule.mistake_only_coaching:
            if d.operation == 'set_subtask':
                raise ContractError('mistake-only coaching forbids proactive stage assignment')
            if d.operation == 'clear_feedback' and (not self.context.subtask or d.assessment != 'complete'):
                raise ContractError('clear_feedback needs active correction and observed completion')
        elif d.operation == 'clear_feedback':
            raise ContractError('clear_feedback is restricted to mistake-only coaching')
        self.memory = {'completed_claims': [dict(text=c.text, evidence_steps=list(c.evidence_steps)) for c in d.completed_claims],
                       'uncertain_or_invalidated': list(d.uncertain_or_invalidated),
                       'claims_not_verified_truth': True}
        if shadow:
            return {'changed': False, 'shadow_only': True, 'stop': False, 'age_steps': age}
        if d.operation == 'stop':
            # A model thinks it is finished; this is not native task success.
            return {'changed': False, 'stop': True, 'age_steps': age}
        if d.operation == 'recover':
            if not self.schedule.allow_semantic_recovery or d.assessment != 'failed':
                raise ContractError('semantic recovery must be enabled and evidence-supported')
        if d.operation == 'continue':
            return {'changed': False, 'stop': False, 'age_steps': age}
        if d.subtask == self.context.subtask:
            return {'changed': False, 'stop': False, 'age_steps': age}
        if self.context.subtask and obs.step - self.goal_started_at < self.schedule.minimum_dwell_steps:
            if d.operation not in ('recover', 'clear_feedback'):
                # Defer a too-early switch without touching the motor stream.
                return {'changed': False, 'stop': False, 'deferred': 'minimum_semantic_dwell', 'age_steps': age}
        self.context = SemanticContext(self.context.original_task, d.subtask,
                                       self.context.epoch + 1, self.context.prompt_mode)
        self.goal_started_at = obs.step
        return {'changed': True, 'stop': False, 'age_steps': age}

    def packet(self):
        return {'context': asdict(self.context), 'memory': self.memory,
                'goal_started_at': self.goal_started_at, 'last_semantic_review_step': self.last_review}
