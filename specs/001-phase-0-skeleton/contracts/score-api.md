# Contract: `phonon.Score` and `phonon.Score.describe()`

The Phase 0 public Python API surface for piece authoring. This is the contract Phase 1+ implementers extend (by adding fields to entity lists) and that the agent generates code against.

## Imports

```python
from phonon import (
    Score, ScoreValidationError,
    Scale, RenderMode, PyoPrecision, Mode, Role,
)
```

These are the *only* names exported from `phonon` in Phase 0 (plus `derive` and `__version__`, covered in `seedseq-api.md` and elsewhere). Importing anything else (`Voice`, `Trajectory`, etc.) MUST raise `ImportError`.

## `Score(...)`

### Signature

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class Score:
    title: str
    seed: int
    duration_seconds: float
    corpus: Corpus | None = None
    voices: tuple[Voice, ...] = ()
    couplings: tuple[Coupling, ...] = ()
    trajectories: tuple[Trajectory, ...] = ()
    bindings: tuple[Binding, ...] = ()
    events: tuple[Event, ...] = ()
    gestures: tuple[Gesture, ...] = ()
    rhetoric: tuple[RhetoricPrimitive, ...] = ()
    variance_defaults: Mapping[Scale, float] = field(default_factory=dict)
    control_hz: int = 200
    sample_rate: int = 48000
    buffer_size: int = 256
    nchnls: int = 2
    pyo_precision: PyoPrecision = PyoPrecision.SINGLE
    warnings: list[str] = field(default_factory=list)
```

The entity types (`Corpus`, `Voice`, `Coupling`, `Trajectory`, `Binding`, `Event`, `Gesture`, `RhetoricPrimitive`) are forward-referenced in Phase 0 — they exist as type names but cannot be instantiated. In Phase 0, all entity lists are `()` (empty tuple) or `[]` (the constructor accepts any iterable and coerces to tuple).

### Behavior

- **Eager validation**: `Score(...)` runs every invariant check in `__post_init__` and raises `ScoreValidationError` on the first failure.
- **No side effects**: construction does not touch the filesystem, the network, the audio backend, or any global state. It does not boot a Pyo Server.
- **Immutability**: after construction succeeds, no attribute can be reassigned. Attempting `score.title = "x"` raises `dataclasses.FrozenInstanceError`.

### Validation errors

`ScoreValidationError` (subclass of `ValueError`) is raised with `field` and `value` attributes, and a message naming the field and the offending value. See `data-model.md` § V-001 through V-009 for the full table.

Example:

```python
>>> Score(title="", seed=1, duration_seconds=10.0)
Traceback (most recent call last):
  ...
ScoreValidationError: title must be non-empty (got '')
>>> err.field
'title'
>>> err.value
''
```

### Warnings (non-fatal)

A successfully-constructed Score may carry strings in `score.warnings`. Phase 0 emits exactly one warning condition (W-001):

- `pyo_precision == PyoPrecision.DOUBLE` and `pyo._pyo64` is not importable in the current process → `"pyo_precision is DOUBLE but pyo._pyo64 is not importable; render will fail"` is appended to `warnings`.

Phase 1+ will add more warnings (e.g., for non-deterministic source use). The contract: warnings are advisory; they never raise.

## `Score.describe()`

### Signature

```python
def describe(self) -> dict[str, Any]: ...
```

### Behavior

- Walks the static graph only. Does **not** boot Pyo, **not** read files, **not** evaluate any trajectory.
- Returns a plain `dict` (not a typed object) so it can be serialized to YAML or JSON without further coercion.
- Idempotent: calling `describe()` twice on the same Score returns equal dicts.

### Output schema

```yaml
title: str
duration: str       # "M:SS" if < 1 hour, else "H:MM:SS"
seed: int
render_contract:
  sample_rate: int
  buffer_size: int
  control_hz: int
  pyo_precision: str       # "single" | "double"
  framework_version: str   # phonon.__version__
voices: []                 # always [] in Phase 0
trajectories: []           # always [] in Phase 0
events: []                 # always [] in Phase 0
gestures: []               # always [] in Phase 0
rhetoric: []               # always [] in Phase 0
variance_profile:
  SUPRA: 0.04              # only scales present in score.variance_defaults appear
  MACRO: 0.06
  ...
warnings: []               # copy of score.warnings
```

In Phase 0, the entity-list keys are always `[]`. The schema for non-empty lists (which fields each list element exposes) is defined by the corresponding entity type's contract in their phase specs (e.g., `voices` schema lands in Phase 2).

### YAML serialization round-trip

The output dict MUST round-trip through `yaml.safe_dump` / `yaml.safe_load`:

```python
import yaml
data = score.describe()
serialized = yaml.safe_dump(data)
deserialized = yaml.safe_load(serialized)
assert deserialized == data   # required by FR-024 and SC-002
```

Any value type that doesn't round-trip cleanly through `yaml.safe_dump` (e.g., enum members, custom classes) MUST be coerced to a string scalar before being placed into the dict. The implementation is responsible for the coercion; callers see only YAML-safe scalars/lists/dicts.

## Acceptance examples

### Empty Score: validates and describes

```python
from phonon import Score, Scale

score = Score(
    title="empty",
    seed=1729,
    duration_seconds=420.0,
    variance_defaults={Scale.SUPRA: 0.04, Scale.MACRO: 0.06},
)

assert score.title == "empty"
assert score.warnings == []

d = score.describe()
assert d["title"] == "empty"
assert d["duration"] == "7:00"
assert d["seed"] == 1729
assert d["voices"] == []
assert d["render_contract"]["sample_rate"] == 48000
assert d["render_contract"]["pyo_precision"] == "single"
assert d["variance_profile"]["SUPRA"] == 0.04
assert d["variance_profile"]["MACRO"] == 0.06
```

### Validation: empty title rejected

```python
from phonon import Score, ScoreValidationError

try:
    Score(title="   ", seed=1, duration_seconds=10.0)
except ScoreValidationError as e:
    assert e.field == "title"
    assert "title must be non-empty" in str(e)
```

### Validation: bad buffer_size rejected

```python
try:
    Score(title="x", seed=1, duration_seconds=10.0, buffer_size=300)
except ScoreValidationError as e:
    assert e.field == "buffer_size"
    assert "power of two" in str(e)
    assert e.value == 300
```

### Validation: bad sample_rate rejected

```python
try:
    Score(title="x", seed=1, duration_seconds=10.0, sample_rate=22050)
except ScoreValidationError as e:
    assert e.field == "sample_rate"
    assert "44100" in str(e)        # the allowed set is in the message
```

### Warning: DOUBLE precision without `pyo._pyo64`

```python
import sys
sys.modules.pop("pyo._pyo64", None)   # ensure not importable

score = Score(
    title="x", seed=1, duration_seconds=10.0,
    pyo_precision=PyoPrecision.DOUBLE,
)
assert any("pyo._pyo64" in w for w in score.warnings)
# but the Score itself is valid:
assert score.pyo_precision == PyoPrecision.DOUBLE
```

## What this contract does NOT promise (Phase 0)

- No `Score.render(...)`, `Score.validate_full(...)`, `Score.update(...)`, or any mutator. (Render comes in Phase 1; deeper static analysis comes with Reference resolution in Phase 2.)
- No describe() schema for non-empty entity lists. Calling `describe()` on a Phase 0 Score whose entity lists are non-empty is undefined behavior — but Phase 0 cannot construct such a Score (entity types are not instantiable).
- No CLI integration. `phonon describe piece.py` is a Phase 4 deliverable.
- No incremental describe (e.g., `describe(scale="MACRO")`); the whole dict is built each call.
- No promise about ordering of `variance_profile` keys (consume the dict by lookup, not iteration).
