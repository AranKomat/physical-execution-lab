"""Semantic goals are language data, never task-specific executable skills."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import math
from k1lab.errors import ContractError
from k1lab.util import digest

PROMPT_MODES = ('original_only', 'task_plus_subtask', 'subtask_only', 'task_plus_correction')
MODES = ('motor_only', 'semantic_shadow', 'semantic_subtask_hierarchy')


def bounded_text(value, name, limit, *, empty=False):
    if not isinstance(value, str) or len(value) > limit or (not empty and not value.strip()):
        raise ContractError(f'{name} must be a bounded string, at most {limit} characters')
    if '\x00' in value:
        raise ContractError(f'{name} contains NUL')
    return value


@dataclass(frozen=True)
class SemanticContext:
    original_task: str
    subtask: str = ''
    epoch: int = 0
    prompt_mode: str = 'original_only'

    def __post_init__(self):
        bounded_text(self.original_task, 'original_task', 16000)
        bounded_text(self.subtask, 'subtask', 600, empty=True)
        if type(self.epoch) is not int or self.epoch < 0:
            raise ContractError('nonnegative integer semantic epoch required')
        if self.prompt_mode not in PROMPT_MODES:
            raise ContractError('unknown prompt mode')

    @property
    def effective_prompt(self):
        # Original baseline is byte-for-byte unchanged, including whitespace.
        if self.prompt_mode == 'original_only' or not self.subtask:
            return self.original_task
        if self.prompt_mode == 'subtask_only':
            return self.subtask
        if self.prompt_mode == 'task_plus_correction':
            return f'{self.original_task}\n\nCorrection:\n{self.subtask}'
        return f'Overall task:\n{self.original_task}\n\nCurrent subtask:\n{self.subtask}'

    @property
    def identity(self):
        return digest(asdict(self))


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_steps: tuple[int, ...]

    def __post_init__(self):
        bounded_text(self.text, 'claim', 400)
        if not 1 <= len(self.evidence_steps) <= 12 or any(type(s) is not int or s < 0 for s in self.evidence_steps):
            raise ContractError('claims need 1..12 nonnegative evidence steps')


@dataclass(frozen=True)
class SemanticDecision:
    episode: str
    based_on_step: int
    based_on_stamp: str
    expected_epoch: int
    operation: str
    subtask: str
    assessment: str
    evidence: str
    completed_claims: tuple[Claim, ...] = field(default_factory=tuple)
    uncertain_or_invalidated: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        bounded_text(self.episode, 'episode', 200)
        if type(self.based_on_step) is not int or self.based_on_step < 0:
            raise ContractError('invalid decision observation step')
        if type(self.expected_epoch) is not int or self.expected_epoch < 0:
            raise ContractError('invalid decision epoch')
        if not isinstance(self.based_on_stamp, str) or len(self.based_on_stamp) != 64:
            raise ContractError('decision requires observation SHA256')
        if self.operation not in ('continue', 'set_subtask', 'recover', 'clear_feedback', 'stop'):
            raise ContractError('no action arrays, shortening, or executable skill calls are accepted')
        if self.assessment not in ('not_started', 'progressing', 'complete', 'failed', 'uncertain'):
            raise ContractError('invalid semantic assessment')
        bounded_text(self.evidence, 'evidence', 1800)
        bounded_text(self.subtask, 'subtask', 600, empty=True)
        if self.operation in ('set_subtask', 'recover') and not self.subtask.strip():
            raise ContractError('a semantic goal is required')
        if self.operation in ('stop', 'clear_feedback') and self.subtask:
            raise ContractError('stop/clear_feedback requires empty goal')
        if len(self.completed_claims) > 12 or any(not isinstance(c, Claim) for c in self.completed_claims):
            raise ContractError('invalid completed claims')
        if len(self.uncertain_or_invalidated) > 12:
            raise ContractError('too many invalidations')
        for text in self.uncertain_or_invalidated:
            bounded_text(text, 'invalidation', 400)
        if any(s > self.based_on_step for c in self.completed_claims for s in c.evidence_steps):
            raise ContractError('future evidence cannot support a claim')

    @classmethod
    def from_wire(cls, data):
        expected = set(cls.__dataclass_fields__)
        if not isinstance(data, dict) or set(data) != expected:
            raise ContractError('semantic decision field mismatch')
        d = dict(data)
        if not isinstance(d['completed_claims'], list) or not isinstance(d['uncertain_or_invalidated'], list):
            raise ContractError('lists required')
        claims = []
        for c in d['completed_claims']:
            if not isinstance(c, dict) or set(c) != {'text', 'evidence_steps'} or not isinstance(c['evidence_steps'], list):
                raise ContractError('claim schema mismatch')
            claims.append(Claim(c['text'], tuple(c['evidence_steps'])))
        d['completed_claims'] = tuple(claims)
        d['uncertain_or_invalidated'] = tuple(d['uncertain_or_invalidated'])
        return cls(**d)

    def wire(self):
        value = asdict(self)
        value['completed_claims'] = [dict(text=c.text, evidence_steps=list(c.evidence_steps)) for c in self.completed_claims]
        value['uncertain_or_invalidated'] = list(self.uncertain_or_invalidated)
        return value


@dataclass(frozen=True)
class ScheduleConfig:
    review_interval_steps: int = 100
    minimum_dwell_steps: int = 30
    event_cooldown_steps: int = 30
    max_decision_age_steps: int = 100
    allow_semantic_recovery: bool = False
    mistake_only_coaching: bool = False

    def __post_init__(self):
        for k in ('review_interval_steps', 'minimum_dwell_steps', 'event_cooldown_steps', 'max_decision_age_steps'):
            if type(getattr(self, k)) is not int or getattr(self, k) < 1:
                raise ContractError(f'{k}: positive integer required')
        if type(self.allow_semantic_recovery) is not bool or type(self.mistake_only_coaching) is not bool:
            raise ContractError('schedule switches are booleans')
        if self.mistake_only_coaching and not self.allow_semantic_recovery:
            raise ContractError('mistake-only coaching requires recovery enabled')


def check_decision(d, obs, context, *, max_age_steps=0):
    if d.episode != obs.episode or d.expected_epoch != context.epoch:
        raise ContractError('stale episode or semantic epoch')
    age = obs.step - d.based_on_step
    if age < 0 or age > max_age_steps:
        raise ContractError('stale/future semantic decision')
    if age == 0 and d.based_on_stamp != obs.stamp:
        raise ContractError('decision is bound to different current evidence')
    if d.operation == 'continue' and d.subtask not in ('', context.subtask):
        raise ContractError('continue cannot silently change the goal')
    return age
