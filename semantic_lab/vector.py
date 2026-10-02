"""Single-owner batched dispatch for independently journaled episode loops.

The driver alone owns physics/model dispatch. Each episode retains an ordinary
InstructionPolicy and run_episode journal. No task-specific control is added.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Condition
import time

from k1lab.errors import ContractError
from k1lab.multibench.types import Proposal
from semantic_lab.policy import InstructionPolicy
from semantic_lab.runner import run_episode


class Coordinator:
    def __init__(self, initial, identity, horizons, describe, infer_batch, step_batch, *,
            timeout_s=3600, evidence_kind='native_unqualified', mixed_operations=False,
            preview_batch=None):
        self.initial = dict(initial)
        self.identity = identity
        self.horizons = dict(horizons)
        self.describe = describe
        self.infer_batch = infer_batch
        self.step_batch = step_batch
        self.timeout_s = timeout_s
        self.evidence_kind = evidence_kind
        self.mixed_operations = mixed_operations
        self.preview_batch = preview_batch
        self.cv = Condition()
        self.active = set(initial)
        self.pending = {}
        self.last_results = {}
        self.error = None
        self.dispatches = []

    def submit(self, idx, operation, value=None):
        request = {'operation': operation, 'value': value, 'done': False}
        with self.cv:
            if self.error is not None:
                raise self.error
            if idx not in self.active or idx in self.pending:
                raise ContractError('duplicate or retired vector episode operation')
            self.pending[idx] = request
            self.cv.notify_all()
            self.cv.wait_for(lambda: request['done'] or self.error is not None)
            if self.error is not None:
                raise self.error
            return request.get('reply')

    def _resolve(self, idx, reply):
        request = self.pending.pop(idx)
        request.update(done=True, reply=reply)

    def run(self, cases, config, outputs, planners, *, episode_runner=run_episode,
            env_factory=None, policy_factory=None):
        if set(cases) != self.active or set(outputs) != self.active or set(planners) != self.active:
            raise ContractError('vector roster must bind every episode exactly once')
        pool = ThreadPoolExecutor(max_workers=len(self.active))
        env_factory = env_factory or EpisodeEnv
        policy_factory = policy_factory or (lambda owner, idx:
            InstructionPolicy(EpisodePolicy(owner, idx), kind='pi05'))
        def execute(idx):
            env = None
            try:
                env = env_factory(self, idx)
                return episode_runner(env, policy_factory(self, idx), planners[idx],
                    cases[idx], config, outputs[idx])
            finally:
                # Retire even if a runner rejects its config before its own try block.
                if env is None:
                    self.submit(idx, 'finish', 'environment_factory_failed')
                elif not env.finished:
                    env.finish('controller_returned')
        futures = {idx: pool.submit(execute, idx) for idx in sorted(self.active)}
        deadline = time.monotonic() + self.timeout_s
        try:
            while self.active:
                with self.cv:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('semantic vector coordinator wall limit')
                    self.cv.wait_for(lambda: bool(self.pending)
                        and (any(r['operation'] == 'finish' for r in self.pending.values())
                            or self.active.issubset(self.pending)), timeout=remaining)
                    for idx in list(self.pending):
                        if self.pending[idx]['operation'] == 'finish':
                            last = self.last_results.get(idx)
                            final = {'success': bool(last and last.success),
                                'score': last.score if last else None}
                            self.active.remove(idx)
                            self._resolve(idx, final)
                    self.cv.notify_all()
                    if not self.active or not self.active.issubset(self.pending):
                        continue
                    ids = sorted(self.active)
                    kinds = {self.pending[idx]['operation'] for idx in ids}
                    allowed = {'infer', 'action'} | ({'preview'} if self.preview_batch else set())
                    if not kinds.issubset(allowed) or (len(kinds) != 1 and not self.mixed_operations):
                        raise ContractError('episodes crossed native prefix barriers')
                    # Pure requests resolve first; parked actions never advance
                    # physics while another episode awaits a policy/preview reply.
                    operation = next(kind for kind in ('preview', 'infer', 'action') if kind in kinds)
                    ids = [idx for idx in ids if self.pending[idx]['operation'] == operation]
                    values = {idx: self.pending[idx]['value'] for idx in ids}
                # No episode can submit another operation until its result resolves.
                callback = {'infer': self.infer_batch, 'action': self.step_batch,
                            'preview': self.preview_batch}[operation]
                replies = callback(values)
                if set(replies) != set(ids):
                    raise ContractError('vector dispatch replied to wrong episodes')
                self.dispatches.append({'operation': operation, 'env_ids': ids})
                with self.cv:
                    for idx in ids:
                        if operation == 'action':
                            self.last_results[idx] = replies[idx]
                        self._resolve(idx, replies[idx])
                    self.cv.notify_all()
            return {idx: future.result(timeout=30) for idx, future in futures.items()}
        except BaseException as exc:
            with self.cv:
                self.error = exc
                self.cv.notify_all()
            raise
        finally:
            pool.shutdown(wait=True)


class EpisodeEnv:
    evidence_kind = 'native_unqualified'

    def __init__(self, owner, idx):
        self.owner, self.idx = owner, idx
        self.horizon = owner.horizons[idx]
        self.evidence_kind = owner.evidence_kind
        self.reset_done = False
        self.finished = False

    def reset(self, case):
        if self.reset_done:
            raise ContractError('one reset observation per episode; no physics reset')
        self.reset_done = True
        return self.owner.initial[self.idx]

    def describe(self):
        return self.owner.describe(self.idx)

    def step(self, action, correction=False):
        if correction or self.finished:
            raise ContractError('native vector semantic execution has no action corrections')
        return self.owner.submit(self.idx, 'action', action)

    def finish(self, reason):
        if self.finished:
            return {}
        result = self.owner.submit(self.idx, 'finish', reason)
        self.finished = True
        return result

    def close(self):
        pass


class ControlEpisodeEnv(EpisodeEnv):
    """Numeric/direct facade; source controller conversion stays with the owner."""
    correction_space = 'x5_eef16_wxyz'
    pose_frame = 'environment_origin/link6'
    correction_description = 'Both arms xyz metres, quaternion wxyz and continuous opening; source robot-only DLS per actual ACK.'

    def __init__(self, owner, idx):
        super().__init__(owner, idx)
        self.obs = owner.initial[idx]

    def step(self, action, correction=False):
        if self.finished:
            raise ContractError('cannot step retired vector episode')
        result = self.owner.submit(self.idx, 'action', {'action': action, 'correction': correction})
        self.obs = result.observation
        return result

    def preview(self, proposal):
        return self.owner.submit(self.idx, 'preview', proposal)

    def correction_reached(self, action):
        from k1lab.multibench.adapters.robodojo import RoboDojoRPC
        return RoboDojoRPC.correction_reached(self, action)


class EpisodePolicy:
    def __init__(self, owner, idx):
        self.owner, self.idx = owner, idx
        self.identity = owner.identity
        self.observation = None
        self.reset_done = False

    def reset(self):
        if self.reset_done:
            raise ContractError('shared policy episode cannot reset within an episode')
        self.reset_done = True

    def observe(self, obs):
        self.observation = obs

    def propose(self, obs):
        result = self.owner.submit(self.idx, 'infer', obs)
        if not isinstance(result, Proposal):
            raise ContractError('shared inference must return source-bound proposals')
        result.validate(obs, self.identity)
        return result

    def invalidate(self, reason):
        # Pi0.5 is stateless apart from its per-episode RNG; no shared reset.
        pass

    def close(self):
        pass
