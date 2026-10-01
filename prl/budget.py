from __future__ import annotations
from dataclasses import dataclass
import time
from .errors import BudgetExceeded, UncertainExecution
from .util import integer, finite


@dataclass
class Budget:
    max_steps: int = 520
    max_decisions: int = 30
    max_wall_s: float = 1800
    max_vla_calls: int = 100
    steps: int = 0
    decisions: int = 0
    vla_calls: int = 0
    started: float = 0

    def __post_init__(self):
        integer(self.max_steps, 'max_steps', 1)
        integer(self.max_decisions, 'max_decisions', 1)
        integer(self.max_vla_calls, 'max_vla_calls', 1)
        finite(self.max_wall_s, 'max_wall_s', 0.001)
        self.started = time.monotonic()

    def check_wall(self):
        if time.monotonic()-self.started >= self.max_wall_s:
            raise BudgetExceeded('wall_budget')

    def before_step(self):
        self.check_wall()
        if self.steps >= self.max_steps:
            raise BudgetExceeded('episode_step_budget')

    def record_step(self):
        self.steps += 1

    def take_decision(self):
        self.check_wall()
        if self.decisions >= self.max_decisions:
            raise BudgetExceeded('decision_budget')
        self.decisions += 1

    def take_vla_call(self):
        self.check_wall()
        if self.vla_calls >= self.max_vla_calls:
            raise BudgetExceeded('vla_call_budget')
        self.vla_calls += 1


class CallLedger:
    """Durable reservations. Unknown billing stays reserved; no implicit retry.

    A shared instance is used across an experiment process. Parallel workers must
    use separate explicitly apportioned budgets, not independent copies of one cap.
    """
    def __init__(self, journal, max_calls=100, max_reserved_tokens=1000000):
        self.journal = journal
        self.max_calls = integer(max_calls, 'max_calls', 1)
        self.max_reserved_tokens = integer(max_reserved_tokens, 'max_reserved_tokens', 1)
        self.calls = 0
        self.tokens = 0
        self.pending = {}

    def reserve(self, request_id, input_token_ceiling, output_token_ceiling):
        n = integer(input_token_ceiling, 'input_token_ceiling', 1) + integer(
            output_token_ceiling, 'output_token_ceiling', 1)
        if request_id in self.pending:
            raise UncertainExecution('Duplicate pending model request; reconcile first')
        if self.calls >= self.max_calls or self.tokens+n > self.max_reserved_tokens:
            raise BudgetExceeded('model_reservation_budget')
        self.calls += 1
        self.tokens += n
        self.pending[request_id] = n
        self.journal.append('model_reservation', {'request_id': request_id, 'tokens': n})

    def finish(self, request_id, usage):
        reserved = self.pending[request_id]
        if usage is None:
            self.journal.append('model_usage_unknown', {'request_id': request_id})
            return
        used = integer(usage, 'usage', 0)
        self.tokens += used-reserved
        del self.pending[request_id]
        self.journal.append('model_usage', {'request_id': request_id, 'tokens': used})
        if self.tokens > self.max_reserved_tokens:
            raise BudgetExceeded('provider_usage_exceeded_reservation')
