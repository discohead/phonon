# Contract: `phonon.derive(seed, kind, name)`

The Phase 0 deterministic seeded-RNG hierarchy. Phase 1+ wires this into Process, Trajectory, Event, and Coupling construction so every stochastic decision in Phonon flows from `Score.seed` through `derive` to a per-entity `numpy.random.Generator`.

## Imports

```python
from phonon import derive
import numpy as np
```

`derive` is also accessible as `phonon.seedseq.derive` for code that wants the qualified path.

## Signature

```python
def derive(seed: int, kind: str, name: str) -> np.random.Generator: ...
```

## Behavior

### Determinism guarantees (FR-044, FR-045)

| Property | Guarantee |
|---|---|
| **Same arguments → same Generator state** | `derive(s, k, n)` and `derive(s, k, n)` return Generators that produce byte-identical output for any pure-Generator method (`standard_normal`, `random`, `bytes`, `integers`, ...) over the same number of calls. |
| **Bit-identical across runs** | The first 1024 bytes of `derive(s, k, n).bytes(1024)` match across separate Python processes on the same machine. (Verified by `test_seedseq.py::test_cross_run_determinism`.) |
| **Bit-identical across platforms** | Same bytes on macOS-arm64, macOS-x86_64, ubuntu-latest, windows-latest. (Verified in CI by SC-009.) |
| **Bit-identical across numpy versions** | Per numpy NEP 19, `default_rng` + `SeedSequence` is part of the API stability contract. Phonon pins a numpy major version in `pyproject.toml` to bound this. |

### Independence guarantees (FR-046)

- `derive(s, k, "a")` and `derive(s, k, "b")` produce **statistically independent** streams (in the sense that `SeedSequence` documents).
- `derive(s, "trajectory", "x")` and `derive(s, "voice", "x")` produce statistically independent streams (kind segregates).
- `derive(s, k, "ab")` and `derive(s, k, "a") + derive(s, k, "b")` produce different streams — the `\x1f` separator forbids the "concatenation collision" anti-pattern.

### Renaming an entity changes its RNG

This is by design (per design spec §14.2): a renamed entity is, for randomness purposes, a new entity. `derive(s, k, "order")` and `derive(s, k, "Order")` produce different Generators because their digests differ.

### What `seed` accepts

Any Python `int`. Negative ints, zero, and very large ints (uint64+) are all accepted. The implementation uses `numpy.random.SeedSequence(entropy=[seed, spawn_int])`; SeedSequence accepts arbitrary Python ints.

`seed=True` or `seed=1.5` raises `TypeError` from inside SeedSequence — Phonon does not catch this in `derive` itself; the caller (typically `Score.__post_init__`) is responsible for type-checking before calling.

## Implementation

```python
import hashlib
import numpy as np

def derive(seed: int, kind: str, name: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{kind}\x1f{name}".encode("utf-8")).digest()
    spawn_int = int.from_bytes(digest[:16], "big")
    seq = np.random.SeedSequence(entropy=[seed, spawn_int])
    return np.random.default_rng(seq)
```

This implementation is treated as part of the contract — changing it (a different hash function, a different separator byte, a different bit-width) is a **major** version bump for Phonon because it changes every stochastic output of every existing piece.

## Acceptance examples

```python
import numpy as np
from phonon import derive

# Reproducibility
g1 = derive(1729, "trajectory", "order")
g2 = derive(1729, "trajectory", "order")
assert g1.bytes(1024) == g2.bytes(1024)

# Independence
ga = derive(1729, "trajectory", "a")
gb = derive(1729, "trajectory", "b")
assert ga.bytes(1024) != gb.bytes(1024)

# Kind segregation
gtraj = derive(1729, "trajectory", "x")
gvoice = derive(1729, "voice", "x")
assert gtraj.bytes(1024) != gvoice.bytes(1024)

# Concatenation collisions are impossible
g_ab = derive(1729, "k", "ab")
g_a_then_b = derive(1729, "k", "a")  # not concatenated; checking digest distinctness
assert g_ab.bytes(1024) != g_a_then_b.bytes(1024)

# Different seed → different output
gA = derive(1, "k", "n")
gB = derive(2, "k", "n")
assert gA.bytes(1024) != gB.bytes(1024)
```

## Cross-platform verification

A CI step in `.github/workflows/ci.yml` (added in Phase 0):

1. On every platform job, run `python -c "from phonon import derive; import sys; sys.stdout.buffer.write(derive(1729, 'cross', 'platform').bytes(1024))"` and capture the bytes.
2. Hash the captured bytes to a SHA-256 hex string.
3. Upload the hash as a job artifact.
4. After all platform jobs complete, a final job downloads all artifacts and asserts every hash is identical. If any differ, fail the build with a clear message naming the divergent platforms.

## What this contract does NOT promise

- `derive` does NOT return a stream that is cryptographically secure. PCG64 is a fast statistical RNG, not a CSPRNG. Don't use it for keys or tokens.
- `derive` does NOT memoize. Calling it twice with the same arguments creates two independent Generator instances; they happen to produce the same output, but they hold independent state.
- `derive` does NOT consume from the parent process's `numpy.random` state. It does not interact with the global `numpy.random.default_rng()` or any module-level RNG.
- The `entropy` and `spawn_int` derivation is not exposed; callers see only `(seed, kind, name) → Generator`.
