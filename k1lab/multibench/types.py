"""No simulator object state or evaluator reward crosses the actor boundary.

These schemas deliberately keep native commands distinct. A dual X5 joint action,
an X5 EEF pose, and a RoboCasa12 command are not interchangeable arrays.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import numpy as np
from k1lab.util import digest
from k1lab.errors import ContractError

SPACES = {'x5_joint14': 14, 'x5_eef16_wxyz': 16, 'robocasa12': 12}


def finite(value: Any, shape: tuple[int, ...], label: str) -> np.ndarray:
    raw=np.asarray(value)
    if raw.dtype.kind not in 'fiu':raise ContractError(f'{label}: numeric values required, not strings/booleans')
    a = raw.astype(np.float64)
    if a.shape != shape or not np.isfinite(a).all():
        raise ContractError(f'{label}: expected finite {shape}, got {a.shape}')
    return a


@dataclass
class Observation:
    episode: str
    step: int
    instruction: str
    rgb: dict[str, np.ndarray]
    state: np.ndarray
    eef: dict[str, dict[str, Any]]
    control_hz: float
    signals: dict[str, Any] = field(default_factory=dict)
    # Private native wire data is permitted only in policy adapters, never prompts.
    native: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if type(self.step) is not int or self.step < 0 or not self.episode or not self.instruction.strip():
            raise ContractError('invalid observation identity/instruction')
        self.state = np.asarray(self.state, dtype=np.float32)
        if self.state.ndim != 1 or not np.isfinite(self.state).all():
            raise ContractError('finite 1D robot state required')
        if not np.isfinite(self.control_hz) or self.control_hz <= 0:
            raise ContractError('positive native control_hz required')
        for key, image in self.rgb.items():
            if not key or image.dtype != np.uint8 or image.ndim != 3 or image.shape[-1] != 3:
                raise ContractError('RGB must be uint8 HWC3; no synthetic missing views')
        for arm, pose in self.eef.items():
            finite(pose['xyz'], (3,), arm+' xyz')
            q = finite(pose['quaternion_xyzw'], (4,), arm+' quaternion')
            if abs(np.linalg.norm(q)-1) > .01:
                raise ContractError('quaternion must be normalized')

    @property
    def stamp(self):
        # Hash pixels and proprio, not hidden simulator state. Record scope accurately.
        return digest({'episode': self.episode, 'step': self.step, 'instruction': self.instruction,
                       'state': self.state.tolist(), 'eef': self.eef,
                       'rgb': {k: digest({'shape': a.shape, 'bytes': __import__('hashlib').sha256(a.tobytes()).hexdigest()})
                               for k, a in sorted(self.rgb.items())}})

    def actor_state(self):
        # Fixed whitelist avoids reward/privileged signals injected by integrations.
        allowed = {'tracking_lost', 'target_motion_contradicted', 'controller_fault',
                   'execution_failed', 'controller_residual_m', 'unknown_geometry'}
        return {'episode': self.episode, 'step': self.step, 'instruction': self.instruction,
                'robot_state': self.state.tolist(), 'eef': self.eef, 'control_hz': self.control_hz,
                'sensor_signals': {k: v for k, v in self.signals.items() if k in allowed},
                'observation_sha256': self.stamp}


@dataclass(frozen=True)
class PolicyIdentity:
    name: str
    checkpoint_sha256: str
    revision: str
    action_space: str
    benchmark_training: str
    native_hz: float
    execute_steps: int
    preprocessing_id: str
    prediction_horizon: int | None = None
    stateful: bool = False
    adapter_config_sha256: str | None = None

    def __post_init__(self):
        if self.action_space not in SPACES or self.native_hz <= 0 or self.execute_steps < 1:
            raise ContractError('invalid policy contract')
        if len(self.checkpoint_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.checkpoint_sha256):
            raise ContractError('hash actual checkpoint manifest; no placeholder at runtime')
        if self.adapter_config_sha256 is not None and (len(self.adapter_config_sha256)!=64 or any(x not in '0123456789abcdef' for x in self.adapter_config_sha256)):
            raise ContractError('invalid adapter configuration hash')
        if not self.revision or not self.preprocessing_id:
            raise ContractError('source revision and preprocessing identity required')

    @property
    def identity(self):
        return digest(asdict(self))


@dataclass
class Action:
    space: str
    values: np.ndarray

    def __post_init__(self):
        if self.space not in SPACES:
            raise ContractError('unknown action space')
        self.values = finite(self.values, (SPACES[self.space],), 'action').astype(np.float32)
        if self.space == 'x5_joint14':
            grippers = self.values[[6,13]]
        elif self.space == 'x5_eef16_wxyz':
            grippers = self.values[[7,15]]
            for off in (3,11):
                if abs(np.linalg.norm(self.values[off:off+4])-1) > .01:
                    raise ContractError('EEF quaternions are unit wxyz')
        else:
            grippers = None
        if grippers is not None and np.any((grippers < 0) | (grippers > 1)):
            raise ContractError('opening outside [0,1]; no implicit gripper clipping')

    def json(self):
        return {'space': self.space, 'values': self.values.tolist()}


@dataclass
class Proposal:
    observation_sha256: str
    step: int
    policy_identity: str
    actions: list[Action]
    diagnostics: dict = field(default_factory=dict)

    def validate(self, obs, identity):
        if self.observation_sha256 != obs.stamp or self.step != obs.step:
            raise ContractError('stale policy proposal')
        if self.policy_identity != identity.identity or not self.actions:
            raise ContractError('wrong policy identity or empty proposal')
        if any(a.space != identity.action_space for a in self.actions):
            raise ContractError('mixed action conventions')
        if abs(identity.native_hz-obs.control_hz) > 1e-6:
            raise ContractError('policy/native timing mismatch; explicit qualification required')


@dataclass
class StepResult:
    observation: Observation
    terminated: bool
    success: bool
    truncated: bool = False
    score: float | None = None # evaluator-only; never included in prompts

    def __post_init__(self):
        if self.success and not self.terminated:
            raise ContractError('success must be terminal under this experiment contract')
        if self.score is not None and (not np.isfinite(self.score) or not 0 <= self.score <= 1):
            raise ContractError('native score must be normalized to [0,1]')
