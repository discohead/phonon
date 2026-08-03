"""Score — declarative value representing a Phonon piece.

Frozen dataclass with eager validation in `__post_init__`. The Phase 0 surface
exposes all 17 fields per data-model.md §1; entity-typed fields (`Voice`,
`Trajectory`, `Coupling`, `Binding`, `Event`, `Gesture`, `RhetoricPrimitive`)
are typed as `tuple` (Phase 0 cannot construct any of those types) and remain
empty. `Score.describe()` walks this static graph and returns a YAML-safe dict.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from phonon._render_mode import PyoPrecision
from phonon._scale import Scale
from phonon.version import __version__

__all__ = ["Score", "ScoreValidationError"]


_ALLOWED_SAMPLE_RATES: frozenset[int] = frozenset(
    {44100, 48000, 88200, 96000, 176400, 192000}
)

_TUPLE_FIELDS: tuple[str, ...] = (
    "voices", "couplings", "trajectories", "bindings",
    "events", "gestures", "rhetoric",
)

_POSITIVE_INT_FIELDS: tuple[str, ...] = (
    "sample_rate", "buffer_size", "control_hz", "nchnls",
)


class ScoreValidationError(ValueError):
    """Raised by `Score(...)` construction when an invariant is violated.

    Subclasses `ValueError` so callers using `except ValueError:` still catch it.
    The `field` and `value` attributes let the caller introspect which invariant
    was violated and on what input.
    """

    def __init__(self, message: str, *, field: str, value: object) -> None:
        super().__init__(message)
        self.field = field
        self.value = value


def _is_strict_int(value: object) -> bool:
    # `bool` is a subclass of `int`; we exclude it so `seed=True` does not silently
    # coerce to 1 and `buffer_size=True` does not silently coerce to a power of two.
    return type(value) is int


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _format_duration(seconds: float) -> str:
    total = int(seconds)  # round down to whole seconds (per data-model.md §1.4)
    if total < 3600:
        m, s = divmod(total, 60)
        return f"{m}:{s:02d}"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


@dataclass(frozen=True, kw_only=True, slots=True)
class Score:
    """A declarative value representing a Phonon piece (Constitution V).

    All fields are keyword-only. Construction runs eager validation
    in `__post_init__`; the first invariant violation raises
    `ScoreValidationError`. After construction, attributes are immutable.
    """

    title: str
    seed: int
    duration_seconds: float
    corpus: Any = None
    voices: tuple = ()
    couplings: tuple = ()
    trajectories: tuple = ()
    bindings: tuple = ()
    events: tuple = ()
    gestures: tuple = ()
    rhetoric: tuple = ()
    variance_defaults: Mapping[Scale, float] = field(default_factory=dict)
    control_hz: int = 200
    sample_rate: int = 48000
    buffer_size: int = 256
    nchnls: int = 2
    pyo_precision: PyoPrecision = PyoPrecision.SINGLE
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Coerce list/iterable entity fields to tuples. `frozen=True` forbids
        # plain `self.x = ...` reassignment; `object.__setattr__` is the
        # documented escape hatch for `__post_init__` mutation.
        for fname in _TUPLE_FIELDS:
            current = getattr(self, fname)
            if not isinstance(current, tuple):
                object.__setattr__(self, fname, tuple(current))

        # Coerce variance_defaults to a plain dict.
        if not isinstance(self.variance_defaults, dict):
            object.__setattr__(
                self, "variance_defaults", dict(self.variance_defaults)
            )

        # V-001: title non-empty after .strip()
        if not isinstance(self.title, str) or len(self.title.strip()) < 1:
            raise ScoreValidationError(
                f"title must be non-empty (got {self.title!r})",
                field="title", value=self.title,
            )

        # V-002: duration_seconds > 0 and finite
        d = self.duration_seconds
        if (not isinstance(d, (int, float))
                or isinstance(d, bool)
                or not math.isfinite(d)
                or d <= 0):
            raise ScoreValidationError(
                f"duration_seconds must be a finite positive number (got {d!r})",
                field="duration_seconds", value=d,
            )

        # V-003: seed is int (and not bool)
        if not _is_strict_int(self.seed):
            raise ScoreValidationError(
                f"seed must be int (got {type(self.seed).__name__})",
                field="seed", value=self.seed,
            )

        # V-004: positive int fields
        for fname in _POSITIVE_INT_FIELDS:
            value = getattr(self, fname)
            if not _is_strict_int(value) or value <= 0:
                raise ScoreValidationError(
                    f"{fname} must be a positive int (got {value!r})",
                    field=fname, value=value,
                )

        # V-005: buffer_size is a power of two
        if not _is_power_of_two(self.buffer_size):
            raise ScoreValidationError(
                f"buffer_size must be a power of two (got {self.buffer_size})",
                field="buffer_size", value=self.buffer_size,
            )

        # V-006: sample_rate is whitelisted
        if self.sample_rate not in _ALLOWED_SAMPLE_RATES:
            allowed = sorted(_ALLOWED_SAMPLE_RATES)
            raise ScoreValidationError(
                f"sample_rate must be one of {allowed} (got {self.sample_rate})",
                field="sample_rate", value=self.sample_rate,
            )

        # V-007: pyo_precision is a PyoPrecision enum member
        if not isinstance(self.pyo_precision, PyoPrecision):
            raise ScoreValidationError(
                f"pyo_precision must be PyoPrecision (got {type(self.pyo_precision).__name__})",
                field="pyo_precision", value=self.pyo_precision,
            )

        # V-008 and V-009: variance_defaults keys/values
        for key, value in self.variance_defaults.items():
            if not isinstance(key, Scale):
                raise ScoreValidationError(
                    f"variance_defaults key must be Scale (got {key!r})",
                    field="variance_defaults", value=key,
                )
            if (not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not math.isfinite(value)
                    or not (0.0 <= value <= 1.0)):
                raise ScoreValidationError(
                    f"variance_defaults[{key.name}] must be in [0.0, 1.0] (got {value!r})",
                    field="variance_defaults", value=value,
                )

        # W-001: DOUBLE precision selected but pyo._pyo64 is not importable
        if self.pyo_precision is PyoPrecision.DOUBLE:
            try:
                importlib.import_module("pyo._pyo64")
            except ImportError:
                self.warnings.append(
                    "pyo_precision is DOUBLE but pyo._pyo64 is not importable; render will fail"
                )

    def describe(self) -> dict[str, Any]:
        """Return a YAML-safe dict describing the static piece graph.

        Walks the static graph only — never boots a Pyo Server (Constitution V).
        Returns a fresh dict on each call; mutating the returned dict has no
        effect on the Score.
        """
        return {
            "title": self.title,
            "duration": _format_duration(self.duration_seconds),
            "seed": self.seed,
            "render_contract": {
                "sample_rate": self.sample_rate,
                "buffer_size": self.buffer_size,
                "control_hz": self.control_hz,
                "pyo_precision": self.pyo_precision.value,
                "framework_version": __version__,
            },
            "voices": [],
            "trajectories": [],
            "events": [],
            "gestures": [],
            "rhetoric": [],
            "variance_profile": {
                k.name: float(v) for k, v in self.variance_defaults.items()
            },
            "warnings": list(self.warnings),
        }
