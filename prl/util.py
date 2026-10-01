from __future__ import annotations
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any
from .errors import ValidationError


def plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if isinstance(value, Path):
        return str(value)
    return value


def canonical(value: Any) -> str:
    return json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(tmp, path)


def read_json(path: str | Path) -> Any:
    def invalid(s):
        raise ValidationError(f"Non-finite JSON number: {s}")
    return json.loads(Path(path).read_text(), parse_constant=invalid)


def finite(x: Any, name: str, lo: float = -math.inf, hi: float = math.inf) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValidationError(f"{name}: expected a finite number")
    if not math.isfinite(x) or not lo <= x <= hi:
        raise ValidationError(f"{name}: value outside [{lo}, {hi}]")
    return float(x)


def integer(x: Any, name: str, lo: int = 0, hi: int = 10**9) -> int:
    if isinstance(x, bool) or not isinstance(x, int) or not lo <= x <= hi:
        raise ValidationError(f"{name}: expected integer in [{lo}, {hi}]")
    return x


def vec(x: Any, name: str, n: int = 3, lo: float = -math.inf, hi: float = math.inf) -> tuple:
    if not isinstance(x, (tuple, list)) or len(x) != n:
        raise ValidationError(f"{name}: expected {n} numbers")
    return tuple(finite(v, name, lo, hi) for v in x)


def norm(a) -> float:
    return math.sqrt(sum(float(x)**2 for x in a))


def sub(a, b) -> tuple:
    return tuple(x-y for x, y in zip(a, b))


def add(a, b) -> tuple:
    return tuple(x+y for x, y in zip(a, b))


def safe_id(s: Any, name: str = "id") -> str:
    import re
    if not isinstance(s, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,159}", s):
        raise ValidationError(f"{name}: invalid identifier")
    return s
