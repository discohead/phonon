"""Tests for `phonon.derive(seed, kind, name)`.

Covers FR-044, FR-045, FR-046 and contracts/seedseq-api.md. The contract is
treated as part of Phonon's reproducibility guarantee — changing it is a
major version bump.
"""

import numpy as np

from phonon import derive


def test_same_args_produce_byte_identical_output():
    g1 = derive(1729, "trajectory", "order")
    g2 = derive(1729, "trajectory", "order")
    assert g1.bytes(1024) == g2.bytes(1024)


def test_different_names_produce_different_streams():
    ga = derive(1729, "trajectory", "a")
    gb = derive(1729, "trajectory", "b")
    assert ga.bytes(1024) != gb.bytes(1024)


def test_kind_segregates_streams():
    """`derive(s, "trajectory", "x")` and `derive(s, "voice", "x")` are independent."""
    gtraj = derive(1729, "trajectory", "x")
    gvoice = derive(1729, "voice", "x")
    assert gtraj.bytes(1024) != gvoice.bytes(1024)


def test_concatenation_collisions_are_blocked():
    """The `\\x1f` separator forbids `("k","ab")` colliding with `("ka","b")`."""
    g1 = derive(1729, "k", "ab")
    g2 = derive(1729, "ka", "b")
    assert g1.bytes(1024) != g2.bytes(1024)


def test_different_seeds_produce_different_streams():
    gA = derive(1, "k", "n")
    gB = derive(2, "k", "n")
    assert gA.bytes(1024) != gB.bytes(1024)


def test_renaming_an_entity_changes_its_rng():
    """Per design spec §14.2: renaming is, for randomness purposes, a new entity."""
    g_lower = derive(1729, "trajectory", "order")
    g_capitalized = derive(1729, "trajectory", "Order")
    assert g_lower.bytes(1024) != g_capitalized.bytes(1024)


def test_negative_and_zero_seeds_accepted():
    derive(-1, "k", "n")
    derive(0, "k", "n")
    derive(2**63, "k", "n")  # large seed


def test_returns_numpy_generator():
    g = derive(1729, "k", "n")
    assert isinstance(g, np.random.Generator)


def test_independent_state_for_two_calls():
    """Two `derive` calls with same args produce independent Generator instances.

    Their byte output is identical (because state is identical), but advancing
    one does not advance the other.
    """
    g1 = derive(1729, "k", "n")
    g2 = derive(1729, "k", "n")
    g1.bytes(1024)  # advance g1
    # g2 should still be at the start
    assert g2.bytes(16) == derive(1729, "k", "n").bytes(16)
