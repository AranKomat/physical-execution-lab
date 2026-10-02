"""Serialized paid review and a task-free, robot-proprioception-only calibration."""
import fcntl
from k1lab.errors import ContractError
from k1lab.multibench.actor import Decision
from k1lab.multibench.types import Action


class SerializedReviewer:
    def __init__(self, reviewer, lock_path):
        self.reviewer = reviewer
        self.lock_path = lock_path
        self.client = reviewer.client

    def reset(self):
        self.reviewer.reset()

    def close(self):
        self.reviewer.close()

    def note_execution_start(self, obs):
        self.reviewer.note_execution_start(obs)

    def review(self, *args, **kwargs):
        with self.lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                return self.reviewer.review(*args, **kwargs)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)


class CalibrationReviewer:
    """At most 15 steps toward a 5mm offset, then 15 toward the initial pose."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.origin = None
        self.phase = 0

    def close(self):
        pass

    def review(self, obs, proposal, reasons, receipt, contract, direct=False):
        if not direct or proposal is not None or contract['correction_space'] != 'x5_eef16_wxyz':
            raise ContractError('calibration requires policy-free native EEF control')
        progress = dict(completed_claims=[], currently_attempting='robot-only controller calibration',
                        uncertain_or_invalidated=['external clearance unknown; exploratory simulator check'])
        if self.phase >= 2:
            return Decision('stop', evidence='Bounded controller calibration ended; no task claim.', progress=progress)
        if min(contract['max_decision_steps'], contract['max_correction_steps']) < 15:
            raise ContractError('calibration requires a frozen 15-step correction lease')
        if self.origin is None:
            self.origin = []
            for arm in ('left', 'right'):
                eef = obs.eef[arm]
                q = eef['quaternion_xyzw']
                self.origin.extend([*eef['xyz'], q[3], *q[:3], eef['gripper_opening_command']])
        target = self.origin.copy()
        if self.phase == 0:
            target[2] += .005
        self.phase += 1
        return Decision('correct', 15, [Action('x5_eef16_wxyz', target)],
                        evidence='Hold initial orientation/grippers; 5mm left EEF offset then return.',
                        progress=progress)


class InterleavingReviewer:
    """Accept, robot-only offset, accept; never a task-solving actor."""
    def __init__(self, arm):
        if arm not in ('left', 'right'):
            raise ContractError('explicit calibration arm required')
        self.arm = arm
        self.reset()

    def reset(self):
        self.phase = 0

    def close(self):
        pass

    def review(self, obs, proposal, reasons, receipt, contract, direct=False):
        if direct or proposal is None or contract['correction_space'] != 'x5_eef16_wxyz':
            raise ContractError('interleaving check requires native joint policy and EEF corrections')
        if 'robot_preview' not in proposal.diagnostics:
            raise ContractError('native source FK preview required before scripted review')
        progress = dict(completed_claims=[], currently_attempting='execution-path integration check',
                        uncertain_or_invalidated=['unknown external clearance; not a task-performance trial'])
        phase = self.phase
        self.phase += 1
        if phase != 1:
            return Decision('accept', 15, evidence='Unmodified source policy prefix for integration check.',
                            progress=progress)
        target = []
        for arm in ('left', 'right'):
            eef = obs.eef[arm]
            xyz = list(eef['xyz'])
            if arm == self.arm:
                xyz[2] += .005
            q = eef['quaternion_xyzw']
            target.extend([*xyz, q[3], *q[:3], eef['gripper_opening_command']])
        # This forced correction is a calibration fixture, not an LLM failure diagnosis.
        return Decision('correct', 15, [Action('x5_eef16_wxyz', target)],
                        execution='failed', evidence='Forced calibration fixture; no observed task failure claimed.',
                        progress=progress)
