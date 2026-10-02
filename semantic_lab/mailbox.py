"""CPU-tested asynchronous semantic-result admission primitive, NOT native async execution.

A future runtime may use this mailbox to keep motor action generation independent.
No background worker here has actuator authority. The v5 runner uses synchronous
semantic checks at drained chunk boundaries; this utility is intentionally separate.
"""
from dataclasses import dataclass
from .contracts import check_decision
from k1lab.errors import ContractError

@dataclass
class SemanticMailbox:
    max_age_steps: int = 100
    pending_binding: tuple | None = None
    decision: object | None = None

    def submit(self, obs, context):
        if self.pending_binding is not None:
            raise ContractError('one in-flight semantic request at a time')
        self.pending_binding = (obs.episode, obs.step, obs.stamp, context.epoch)
        return self.pending_binding

    def complete(self, decision):
        if self.pending_binding != (decision.episode, decision.based_on_step,
                                    decision.based_on_stamp, decision.expected_epoch):
            raise ContractError('asynchronous response binding mismatch')
        self.decision = decision

    def take_at_boundary(self, obs, context, *, prefix_drained):
        if not prefix_drained:
            raise ContractError('asynchronous commit attempted during motor execution')
        if self.decision is None:
            return None
        d = self.decision
        self.decision = self.pending_binding = None
        check_decision(d, obs, context, max_age_steps=self.max_age_steps)
        if any(obs.signals.get(k) is True for k in ('controller_fault', 'tracking_lost', 'target_motion_contradicted')):
            raise ContractError('observation invalidates asynchronous semantic proposal')
        return d
