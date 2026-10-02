"""Instruction conditioning below the model server, without fake physical ACKs.

Supported source seams: Pi05Policy, XPolicyModel and XiaomiRoboCasaPolicy.
The original environment instruction and actor evidence are never rewritten.
A local 'rebind' at a drained boundary is NOT a sensor sample or action ACK.
"""
from __future__ import annotations
from dataclasses import asdict, replace
from k1lab.errors import ContractError
from k1lab.util import digest
from k1lab.multibench.types import Proposal
from .contracts import SemanticContext


class InstructionPolicy:
    semantic_protocol = 'semantic-policy.v1'

    def __init__(self, base, *, kind):
        if kind not in ('pi05', 'xpolicylab', 'xiaomi_robocasa', 'test'):
            raise ContractError('unsupported source conditioning seam')
        self.base = base
        self.identity = base.identity
        self.kind = kind
        self.server_info = getattr(base, 'server_info', {})
        self.context = None
        self.last_raw = None
        self.last_conditioned_stamp = None
        self.open_prefix = None
        self.ack_count = 0
        self.cancel_history_loss = False

    def reset(self):
        if self.open_prefix is not None:
            raise ContractError('cannot reset an unaccounted policy prefix')
        self.base.reset()
        self.context = self.last_raw = self.last_conditioned_stamp = None
        self.ack_count = 0

    def set_context(self, context):
        if not isinstance(context, SemanticContext):
            context = SemanticContext(**context)
        if self.open_prefix is not None:
            raise ContractError('semantic context cannot change inside a motor prefix')
        if self.last_raw is not None and context.original_task != self.last_raw.instruction:
            raise ContractError('context cannot replace the original task')
        if self.context is not None:
            if context.original_task != self.context.original_task or context.prompt_mode != self.context.prompt_mode:
                raise ContractError('episode task/prompt mode is immutable')
            if context.epoch < self.context.epoch:
                raise ContractError('semantic epoch regressed')
            if context.subtask != self.context.subtask and context.epoch != self.context.epoch + 1:
                raise ContractError('changed goal needs exactly the next semantic epoch')
            if context.subtask == self.context.subtask and context.epoch != self.context.epoch:
                raise ContractError('unchanged goal cannot advance epoch')
        changed = self.context is None or context.identity != self.context.identity
        self.context = context
        return {'context_sha256': context.identity, 'changed': changed,
                'physical_steps': 0, 'policy_resampled': False, 'history_reset': False}

    def _view(self, obs):
        if self.context is None:
            self.context = SemanticContext(obs.instruction)
        if obs.instruction != self.context.original_task:
            raise ContractError('native instruction changed')
        return replace(obs, instruction=self.context.effective_prompt)

    def observe(self, obs):
        # Identity compares physical observation stamp, not the policy prompt view.
        if self.last_raw is not None:
            if obs.stamp == self.last_raw.stamp:
                return
            if obs.episode != self.last_raw.episode or obs.step != self.last_raw.step + 1:
                raise ContractError('exactly one fresh observation per actual action required')
            if self.open_prefix is None:
                raise ContractError('unexpected action ACK without an open prefix')
            if self.ack_count >= self.open_prefix['execute_steps']:
                raise ContractError('too many physical ACKs')
        elif obs.step != 0:
            raise ContractError('episode must start from its reset observation')
        view = self._view(obs)
        self.base.observe(view)
        if self.last_raw is not None:
            self.ack_count += 1
        self.last_raw = obs
        self.last_conditioned_stamp = view.stamp

    def _rebind_without_ack(self, view):
        if self.last_conditioned_stamp == view.stamp:
            return False
        if self.kind == 'xpolicylab':
            if getattr(self.base, 'pending', 0):
                raise ContractError('source actions pending at language rebind')
            # The inspected Intern _ingest calls session.update_obs ONLY while
            # pending_model_actions is nonempty. Require it empty before refresh.
            model = self.base.model
            session = getattr(model, 'session', None)
            if session is not None and getattr(session, 'pending_model_actions', None):
                raise ContractError('native WAM has unacknowledged actions')
            from k1lab.multibench.adapters.xpolicylab import to_xpl
            model.update_obs(to_xpl(view))
            # Cache rewrite prevents base.propose from delivering the same sample twice.
            self.base.last_stamp = view.stamp
        elif self.kind == 'xiaomi_robocasa':
            if self.base.last_step != view.step:
                raise ContractError('XR1 observation history is not current')
            # XR1 infer takes instruction separately; do not append another image/state.
            self.base.last_stamp = view.stamp
        elif self.kind == 'test':
            self.base.rebind_instruction(view)
        # Pi05 has no observation history and reads instruction directly in propose.
        self.last_conditioned_stamp = view.stamp
        return True

    def propose(self, obs):
        if self.open_prefix is not None:
            raise ContractError('previous prefix must be executed/accounted before inference')
        if self.last_raw is None or obs.stamp != self.last_raw.stamp:
            raise ContractError('propose requires the last actual ACK/reset observation')
        view = self._view(obs)
        rebound = self._rebind_without_ack(view)
        p = self.base.propose(view)
        p.validate(view, self.identity)
        n = self.identity.execute_steps
        if len(p.actions) < n:
            raise ContractError('policy returned less than its native execution prefix')
        # XPolicyModel.pending counts all exposed actions, not just a caller slice.
        # Never silently reset a stateful source to imitate full cadence.
        if self.kind == 'xpolicylab' and len(p.actions) != n:
            raise ContractError('XPolicyLab exposed-prefix contract changed; qualify explicitly')
        self.open_prefix = {'start_step': obs.step, 'predicted': len(p.actions), 'execute_steps': n}
        self.ack_count = 0
        diagnostics = dict(p.diagnostics)
        diagnostics['semantic'] = {
            'context': asdict(self.context), 'context_sha256': self.context.identity,
            'effective_prompt': self.context.effective_prompt,
            'effective_prompt_sha256': digest(self.context.effective_prompt),
            'original_observation_sha256': obs.stamp,
            'conditioned_observation_sha256': view.stamp,
            'prompt_rebound_without_physical_ack': rebound,
            'natural_execute_steps': n,
            'history_reset': False,
        }
        return Proposal(obs.stamp, obs.step, p.policy_identity, p.actions, diagnostics)

    def finish_prefix(self, executed, reason='natural_boundary'):
        if self.open_prefix is None or type(executed) is not int or executed != self.ack_count:
            raise ContractError('prefix receipt does not match actual ACK count')
        expected = self.open_prefix['execute_steps']
        if reason not in ('natural_boundary', 'native_terminal', 'resource_limit', 'controller_fault', 'abort'):
            raise ContractError('semantic shortening is not a valid prefix completion')
        if reason == 'natural_boundary' and executed != expected:
            raise ContractError('cannot shorten a natural motor prefix')
        if not 0 <= executed <= expected:
            raise ContractError('prefix action count invalid')
        lost = False
        if executed < expected:
            # Terminal/abort only. Never continue after this cancellation in this runner.
            self.base.invalidate(reason)
            lost = self.kind == 'xpolicylab'
        receipt = {**self.open_prefix, 'executed': executed, 'reason': reason,
                   'natural_unexecuted_prediction_suffix': self.open_prefix['predicted'] - expected,
                   'unexecuted_prefix': expected - executed, 'history_reset_on_abort': lost}
        self.open_prefix = None
        self.cancel_history_loss |= lost
        return receipt

    def memory(self):
        return self.base.memory()

    def synchronize(self):
        return self.base.synchronize()

    def close(self):
        self.base.close()
