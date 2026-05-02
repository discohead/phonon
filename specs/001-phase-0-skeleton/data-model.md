# Data Model: Phase 0 — Skeleton

This document is the canonical reference for the data shapes Phase 0 implements. It is the bridge between the technology-agnostic spec (`spec.md`) and the concrete contracts (`contracts/`). Every type, field, validation rule, and state transition documented here must be implementable in pure Python with `numpy`, `PyYAML`, and the standard library — no Pyo Server boot, no audio I/O.

Phase 0 implements **all 17 fields** of `Score` (entity lists may be empty), **the `ScoreValidationError` exception type**, **five enums**, **the `derive()` function**, **the `sha256_audio_file()` helper**, and **module-level docstring stubs** for entity types that come online in later phases. Voice, Trajectory, Coupling, Binding, Reference, Event, Crossing, Gesture, Midi, Osc, all rhetoric primitives, all process generators, and all shape factories are NOT modeled here — they belong to Phase 1+.

---

## 1. `Score`

The single declarative value representing a Phonon piece. Frozen dataclass, eager validation in `__post_init__`, keyword-only construction.

### Fields

| Field | Type | Default | Validation rule |
|---|---|---|---|
| `title` | `str` | (required) | `len(title.strip()) >= 1` (FR-013) |
| `seed` | `int` | (required) | must be `int` (FR-015); negative and zero accepted |
| `duration_seconds` | `float` | (required) | `> 0`, finite (FR-014) |
| `corpus` | `Corpus \| None` | `None` | None in Phase 0 (Corpus deferred to Phase 1) |
| `voices` | `tuple[Voice, ...]` | `()` | empty in Phase 0 |
| `couplings` | `tuple[Coupling, ...]` | `()` | empty in Phase 0 |
| `trajectories` | `tuple[Trajectory, ...]` | `()` | empty in Phase 0 |
| `bindings` | `tuple[Binding, ...]` | `()` | empty in Phase 0 |
| `events` | `tuple[Event, ...]` | `()` | empty in Phase 0 |
| `gestures` | `tuple[Gesture, ...]` | `()` | empty in Phase 0 |
| `rhetoric` | `tuple[RhetoricPrimitive, ...]` | `()` | empty in Phase 0 |
| `variance_defaults` | `Mapping[Scale, float]` | `{}` | keys must be `Scale` enum values; values in `[0.0, 1.0]`; partial mappings accepted (FR-020) |
| `control_hz` | `int` | `200` | positive integer (FR-016) |
| `sample_rate` | `int` | `48000` | one of `{44100, 48000, 88200, 96000, 176400, 192000}` (FR-018) |
| `buffer_size` | `int` | `256` | positive integer, power of two (FR-016, FR-017) |
| `nchnls` | `int` | `2` | positive integer (FR-016) |
| `pyo_precision` | `PyoPrecision` | `PyoPrecision.SINGLE` | enum value (FR-019) |
| `warnings` | `list[str]` | `field(default_factory=list)` | populated during `__post_init__`; see §1.3 |

**Notes on collection types**: spec §15.1 documents the entity lists as `list[...]`. Implementation uses `tuple[...]` internally to preserve `frozen=True` semantics; the constructor coerces lists/iterables to tuples in `__post_init__`. From the composer's perspective, passing a list works (Python's iterable contract); the stored attribute is a tuple.

### Construction & validation lifecycle

```text
caller invokes Score(...)
        │
        ▼
@dataclass __init__ assigns all fields
        │
        ▼
__post_init__ runs:
    1. coerce list/iterable fields to tuples
    2. validate every invariant (FR-013 through FR-021)
       on first violation → raise ScoreValidationError
    3. populate self.warnings (warnings are non-fatal)
        │
        ▼
Score instance returned to caller
```

After return, the Score is immutable (`frozen=True`). The internal `warnings` list is mutated only in `__post_init__`; downstream code reads it but never mutates it.

### Validation rules (formal table)

| ID | Rule | FR | Failure message template |
|---|---|---|---|
| V-001 | `title` is non-empty after `.strip()` | FR-013 | `"title must be non-empty (got {value!r})"` |
| V-002 | `duration_seconds > 0` and `math.isfinite(duration_seconds)` | FR-014 | `"duration_seconds must be a finite positive number (got {value!r})"` |
| V-003 | `seed` is `int` (not bool) | FR-015 | `"seed must be int (got {type})"` |
| V-004 | `sample_rate`, `buffer_size`, `control_hz`, `nchnls` are `int` and `> 0` | FR-016 | `"{field} must be a positive int (got {value!r})"` |
| V-005 | `buffer_size` is a power of two (`buffer_size & (buffer_size - 1) == 0`) | FR-017 | `"buffer_size must be a power of two (got {value})"` |
| V-006 | `sample_rate` is in `{44100, 48000, 88200, 96000, 176400, 192000}` | FR-018 | `"sample_rate must be one of {allowed} (got {value})"` |
| V-007 | `pyo_precision` is `PyoPrecision.SINGLE` or `PyoPrecision.DOUBLE` | FR-019 | `"pyo_precision must be PyoPrecision (got {type})"` |
| V-008 | `variance_defaults` keys are `Scale` enum members | FR-020 | `"variance_defaults key must be Scale (got {value!r})"` |
| V-009 | `variance_defaults` values are floats in `[0.0, 1.0]` | FR-020 | `"variance_defaults[{key}] must be in [0.0, 1.0] (got {value!r})"` |
| W-001 | `pyo_precision == DOUBLE` and `pyo._pyo64` not importable → warning, not error | FR-021 | `"pyo_precision is DOUBLE but pyo._pyo64 is not importable; render will fail"` |

`bool` rejection in V-003 and V-004 is deliberate: in Python `True` is `int` per the type system, but allowing `seed=True` would silently coerce to `1`. The check is `type(value) is int` (or `isinstance(value, int) and not isinstance(value, bool)`).

### Accessor: `Score.describe()`

Returns a Python `dict` with the schema below. Walks the static graph only — never boots a Pyo Server.

```python
{
    "title": str,                           # the original title, stripped
    "duration": str,                        # "M:SS" or "H:MM:SS"
    "seed": int,                            # the original seed
    "render_contract": {
        "sample_rate": int,                 # Hz
        "buffer_size": int,                 # samples
        "control_hz": int,                  # Hz
        "pyo_precision": str,               # "single" | "double"
        "framework_version": str,           # phonon.__version__
    },
    "voices": list,                         # [] in Phase 0
    "trajectories": list,                   # [] in Phase 0
    "events": list,                         # [] in Phase 0
    "gestures": list,                       # [] in Phase 0
    "rhetoric": list,                       # [] in Phase 0
    "variance_profile": dict[str, float],   # {"SUPRA": 0.04, ...} — keys are Scale enum names
    "warnings": list[str],                  # copy of self.warnings
}
```

Constraints:
- All values are JSON/YAML-serializable scalars or recursive dict/list structures (FR-024).
- Enums are coerced to lowercase or canonical-name strings (`PyoPrecision.SINGLE` → `"single"`; `Scale.SUPRA` → `"SUPRA"`). The choice is per-enum and stable.
- `duration` is formatted by `_format_duration(seconds: float) -> str`:
  - `< 3600` seconds → `"M:SS"` (e.g., `"7:00"`, `"0:01"`)
  - `>= 3600` seconds → `"H:MM:SS"` (e.g., `"1:23:45"`)
  - Fractional seconds round down to the nearest whole second.

### Immutability

`frozen=True` forbids `score.attr = value`. The internal `warnings` list is mutable container under an immutable attribute; `describe()` returns a copy (`list(self.warnings)`) to prevent external callers from mutating the source.

---

## 2. `ScoreValidationError`

```python
class ScoreValidationError(ValueError):
    """Raised by Score construction on invariant violation."""

    def __init__(self, message: str, *, field: str, value: object):
        super().__init__(message)
        self.field = field
        self.value = value
```

Subclasses `ValueError` so callers using `except ValueError:` still catch it. The `field` and `value` attributes let the caller (or a higher-level validator) introspect which invariant was violated.

The message format always names the offending field and the offending value (FR-011). Templates are listed in the V-001…V-009 table above.

---

## 3. Enums

All enums are `enum.Enum` subclasses (not `IntEnum` — value identity, not numeric ordering, is what matters).

### `Scale` (in `phonon/_scale.py`, re-exported as `phonon.Scale`)

```python
class Scale(Enum):
    SAMPLE = "sample"   # < 100µs   (audio-rate; not directly addressed in pieces)
    MICRO  = "micro"    # 100µs – 100ms
    MESO   = "meso"     # 100ms – 5s
    MACRO  = "macro"    # 5s – several minutes
    SUPRA  = "supra"    # whole piece duration
```

Required by Constitution IV. Used in Phase 0 as the key type of `Score.variance_defaults`. Phase 2+ uses it on every `Trajectory`.

### `PyoPrecision` (in `phonon/_render_mode.py`, re-exported as `phonon.PyoPrecision`)

```python
class PyoPrecision(Enum):
    SINGLE = "single"   # pyo._pyo (the default)
    DOUBLE = "double"   # pyo._pyo64 (opt-in; requires --use-double build)
```

Used in `Score.pyo_precision`. Validation surfaces a warning if DOUBLE and `pyo._pyo64` is not importable (W-001).

### `RenderMode` (in `phonon/_render_mode.py`, re-exported as `phonon.RenderMode`)

```python
class RenderMode(Enum):
    AUTOPILOT = "autopilot"   # offline, no MIDI/OSC, deterministic
    LIVE      = "live"        # real-time backend, controllers active
    REPLAY    = "replay"      # offline, .gestures timeline drives gestures
```

Defined in Phase 0 but not consumed (the renderer is Phase 1+). Composers may reference `RenderMode.AUTOPILOT` in their piece's `if __name__ == "__main__"` block; the actual `score.render(mode=...)` method exists in Phase 1.

### `Mode` (in `phonon/binding.py`, re-exported as `phonon.Mode`)

```python
class Mode(Enum):
    ABSOLUTE = "absolute"   # target.value = source.value
    OFFSET   = "offset"     # target.value = base + source.value
    MODULATE = "modulate"   # target.value = base * source.value
```

Defined in Phase 0 but not consumed (Binding and Gesture come online in Phase 1 / Phase 3 respectively). The enum module is otherwise a docstring stub.

### `Role` (in `phonon/voice.py`, re-exported as `phonon.Role`)

```python
class Role(Enum):
    ANCHOR_LOW    = "anchor_low"
    AIR_HIGH      = "air_high"
    PRIMARY_MID   = "primary_mid"
    SECONDARY_MID = "secondary_mid"
    CUSTOM        = "custom"
```

Defined in Phase 0 but not consumed (Voice comes online in Phase 2). The enum module is otherwise a docstring stub.

---

## 4. `derive(seed, kind, name) -> numpy.random.Generator`

Pure function in `phonon/seedseq.py`. The root of Phonon's deterministic stochastic hierarchy.

```python
def derive(seed: int, kind: str, name: str) -> numpy.random.Generator: ...
```

### Properties (FR-044, FR-045, FR-046)

1. **Deterministic across runs**: `derive(seed, kind, name)` produces a Generator whose first 1024 bytes of `standard_normal()` (or `bytes(1024)`) output are bit-identical across runs of the same Python+numpy on the same platform.
2. **Deterministic across platforms**: same property holds across macOS-arm64, macOS-x86_64, ubuntu-latest, windows-latest. Verified by a CI step that hashes the first-1024-byte output and compares across platforms.
3. **Uncorrelated streams**: `derive(seed, "trajectory", "a")` and `derive(seed, "trajectory", "b")` produce statistically distinct sequences (chi-square or KS test on first N samples; the implementation just relies on `SeedSequence`'s spawning behavior, which is documented to produce statistically independent streams).
4. **Renaming a name produces a new RNG**: `derive(seed, "trajectory", "ord")` and `derive(seed, "trajectory", "order")` produce distinct sequences. (See §14.2 of the design spec — renaming an entity is, for randomness purposes, defining a new entity. This is intentional.)

### Implementation (per R-001)

```python
import hashlib
import numpy as np

def derive(seed: int, kind: str, name: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{kind}\x1f{name}".encode("utf-8")).digest()
    spawn_int = int.from_bytes(digest[:16], "big")
    seq = np.random.SeedSequence(entropy=[seed, spawn_int])
    return np.random.default_rng(seq)
```

The `\x1f` separator byte enforces injectivity of the `(kind, name)` encoding.

---

## 5. `sha256_audio_file(path) -> str`

Pure function in `phonon/render/reproducibility.py`. Functional in Phase 0 as a building block for Phase 1's reproducibility tests.

```python
def sha256_audio_file(path: pathlib.Path) -> str:
    """Return the SHA-256 hex digest of the file at `path`."""
```

### Properties

- Streams the file in 64 KiB chunks (constant memory regardless of file size).
- Returns lowercase hex; matches `shasum -a 256 path`.
- Raises `FileNotFoundError` if the path doesn't exist (default `open()` behavior).

Phase 1+ uses this to assert two render outputs hash-match (positive test) or hash-differ (negative test for the reproducibility contract).

---

## 6. Module stubs (Phase 0 placeholders)

The following module files exist in Phase 0 but contain only:

```python
"""<one-line description from design spec §17>

Substantive implementation lands in Phase <N>; see specs/00<N>-*/spec.md.
"""

__all__: list[str] = []
```

…except where this document specifies otherwise (e.g., `voice.py` and `binding.py` host `Role` and `Mode` respectively).

| Module | Phase that fills it |
|---|---|
| `phonon/voice.py` | Phase 2 (currently: hosts `Role` enum) |
| `phonon/trajectory.py` | Phase 2 |
| `phonon/coupling.py` | Phase 2 |
| `phonon/binding.py` | Phase 1 (currently: hosts `Mode` enum) |
| `phonon/rhetoric.py` | Phase 3 |
| `phonon/event.py` | Phase 3 |
| `phonon/gesture.py` | Phase 3 |
| `phonon/shape.py` | Phase 1 |
| `phonon/process/*.py` | Phase 1 (Phase 2 for chaos generators) |
| `phonon/render/scheduler.py` | Phase 1 |
| `phonon/render/pyo_backend.py` | Phase 1 |
| `phonon/render/server.py` | Phase 1 |
| `phonon/render/midi_io.py` | Phase 3 |
| `phonon/render/osc_io.py` | Phase 3 |
| `phonon/render/recorder.py` | Phase 3 |
| `phonon/render/reproducibility.py` | Phase 0 (`sha256_audio_file`); fuller helpers Phase 1 |
| `phonon/cli/*.py` | Phase 4 |

---

## 7. Out-of-scope (Phase 1+ data)

Explicitly NOT modeled in Phase 0:

- `Voice` fields (role, band, source, entrance, name, role-specific parameters)
- `Trajectory` fields (name, scale, shape, variance, reshape_by, drift_toward, output)
- `Coupling` fields (a, b, strength, kind, name)
- `Binding` fields (source, target, mode, glide_seconds, transform, name)
- `Reference` (and reference-resolution logic)
- `Crossing` (and threshold-test logic)
- `Event` (and the six closed-set actions)
- `Gesture` (and Midi/Osc factories)
- `Persistence`, `Recurrence`, `Departure`, `Quotation`, `Latency`, `Distortion`
- `Process` and all its concrete subclasses
- `Shape` factories (`linear`, `sigmoid`, `brown`, `pink`, `arc`, `step`, `composite`)
- `Corpus`, `Sample`, `SamplePath`
- `Performance`
- The control loop and the renderer

These have their own data models in their respective phase specs.

---

## 8. State transitions

`Score` has exactly two states:

```
[uninitialized] --construct--> [valid]
[uninitialized] --construct--> [error: ScoreValidationError raised]
```

There is no `score.start()`, `score.render()` body, no transition to a "rendering" or "rendered" state in Phase 0. `describe()` is pure-functional on `[valid]`.

`derive()` is stateless; calling it does not change anything observable (pure function).

`sha256_audio_file()` is stateless; reads a file and returns a digest.
