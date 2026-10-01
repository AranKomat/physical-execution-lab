from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .errors import ValidationError
from .util import finite, integer, safe_id, vec, plain, digest

SOURCES = {"sensor", "privileged_sim", "synthetic"}
MODES = {"frozen", "nominal", "dynamic", "dynamic_k1"}


@dataclass(frozen=True)
class Case:
    case_id: str
    suite: str
    task_id: int
    state_index: int
    policy_seed: int
    split: str
    state_sha256: str
    fixture: str | None = None

    @classmethod
    def from_dict(cls, d):
        if set(d) - set(cls.__dataclass_fields__):
            raise ValidationError("Unknown case fields")
        c = cls(**d)
        safe_id(c.case_id)
        safe_id(c.suite)
        for name in ("task_id", "state_index", "policy_seed"):
            integer(getattr(c, name), name)
        if c.split not in {"dev", "test", "smoke"}:
            raise ValidationError("Case split must be dev/test/smoke")
        if len(c.state_sha256) != 64 or any(x not in '0123456789abcdef' for x in c.state_sha256):
            raise ValidationError("Case must carry an exact state hash, not a seed-only identity")
        return c

    @property
    def identity(self):
        return digest([self.suite, self.task_id, self.state_index, self.state_sha256,
                       self.policy_seed])


@dataclass(frozen=True)
class Target:
    target_id: str
    xyz: tuple[float, float, float]
    source: str
    kind: str
    observed_step: int
    frame: str = "world"
    uncertainty_m: float | None = None
    evidence_id: str = ""

    def __post_init__(self):
        safe_id(self.target_id, "target_id")
        vec(list(self.xyz), "target.xyz")
        integer(self.observed_step, "observed_step")
        if self.source not in SOURCES or self.frame != "world":
            raise ValidationError("Unsupported target source/frame")
        if self.uncertainty_m is not None:
            finite(self.uncertainty_m, "uncertainty_m", 0, 100)


@dataclass
class Observation:
    episode_id: str
    revision: int
    sim_step: int
    task: str
    eef_xyz: tuple[float, float, float]
    gripper_width: float
    source: str
    targets: dict[str, Target] = field(default_factory=dict)
    images: list[dict] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)

    @property
    def observation_id(self):
        return f"{self.episode_id}:{self.revision}"

    def actor_view(self):
        # No native reward, task-success predicate, simulator object-state dict,
        # serialized simulator state, or latent synthetic failure code is exposed.
        return {
            "observation_id": self.observation_id,
            "sim_step": self.sim_step,
            "task": self.task,
            "robot": {"eef_xyz_m": list(self.eef_xyz), "gripper_width_m": self.gripper_width},
            "information_profile": self.source,
            "targets": plain(self.targets),
            "images": self.images,
            "signals": self.signals,
        }


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    observation_id: str
    capability: str
    arguments: dict
    max_steps: int = 80
    decision_summary: str = ""
    alternatives: tuple[dict, ...] = ()
    objective: str = ""

    @classmethod
    def from_dict(cls, d: dict):
        if not isinstance(d, dict):
            raise ValidationError("Proposal must be a JSON object")
        allowed = set(cls.__dataclass_fields__)
        if set(d)-allowed:
            raise ValidationError(f"Unexpected proposal fields: {sorted(set(d)-allowed)}")
        try:
            args = dict(d)
            args['alternatives'] = tuple(args.get('alternatives', ()))
            p = cls(**args)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Invalid proposal: {e}") from e
        safe_id(p.proposal_id, "proposal_id")
        safe_id(p.observation_id, "observation_id")
        safe_id(p.capability, "capability")
        if not isinstance(p.arguments, dict):
            raise ValidationError("arguments must be an object")
        integer(p.max_steps, "max_steps", 0, 2000)
        if not isinstance(p.decision_summary, str) or len(p.decision_summary)>2000:
            raise ValidationError("decision_summary must be short observable reasoning")
        if not isinstance(p.objective, str) or len(p.objective)>2000:
            raise ValidationError("invalid objective")
        if len(p.alternatives)>3:
            raise ValidationError("At most three predeclared alternatives")
        for a in p.alternatives:
            if not isinstance(a, dict) or set(a)!={'capability','arguments'}:
                raise ValidationError("Alternative requires capability and arguments")
        # Enforce JSON serializability and finite values recursively.
        try:
            digest(p)
        except (TypeError, ValueError) as e:
            raise ValidationError("Proposal contains non-JSON/non-finite data") from e
        return p


@dataclass
class Stage:
    operation: str
    arguments: dict
    max_steps: int
    progress_target: tuple | None = None
    progress_tolerance: float = 0.006


@dataclass
class Receipt:
    proposal_id: str
    status: str
    reason: str
    capability: str
    start_observation_id: str
    end_observation_id: str
    native_steps: int
    effect_verified: bool | None = None
    details: dict = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)

    def actor_view(self):
        return plain(self)
