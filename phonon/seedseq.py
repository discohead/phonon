"""Deterministic seeded RNG hierarchy for stochastic primitives.

Phonon's bit-exact reproducibility contract (Constitution II) demands that
every stochastic decision flow from `Score.seed` through `derive(seed, kind, name)`
to a per-entity `numpy.random.Generator` whose output is bit-identical across
runs, platforms, and (within numpy's NEP 19 stability contract) numpy versions.

The implementation hashes `(kind, name)` with SHA-256 (deterministic, unlike
Python's built-in `hash`) and feeds the digest into `numpy.random.SeedSequence`
alongside the integer `seed`. The unit-separator byte `\\x1f` between `kind` and
`name` makes the encoding injective: `("traj", "ab")` and `("traja", "b")` cannot
collide.
"""

import hashlib

import numpy as np

__all__ = ["derive"]


def derive(seed: int, kind: str, name: str) -> np.random.Generator:
    """Return a deterministic per-entity `numpy.random.Generator`.

    Same `(seed, kind, name)` always yields the same Generator state, across
    runs, processes, and supported platforms. Different names (or different
    kinds, or different seeds) yield statistically independent streams.

    Negative seeds are mapped to their two's-complement uint128 representation
    before being passed to numpy's `SeedSequence` (which requires non-negative
    integers). For non-negative seeds this is a no-op, so the contract's
    bit-exact-output guarantee is preserved for all seeds in the spec's
    intended range.
    """
    digest = hashlib.sha256(f"{kind}\x1f{name}".encode("utf-8")).digest()
    spawn_int = int.from_bytes(digest[:16], "big")
    seed_normalized = seed & ((1 << 128) - 1)
    seq = np.random.SeedSequence(entropy=[seed_normalized, spawn_int])
    return np.random.default_rng(seq)
