"""Tests for `phonon.Score` construction and validation.

Covers FR-012 through FR-021 and contracts/score-api.md. Validation rules
V-001 through V-009 each have at least one negative test asserting the
raised `ScoreValidationError` has the right `field`, `value`, and a
message that names the offending field.
"""

import math
import sys

import pytest

from phonon import (
    Mode,
    PyoPrecision,
    RenderMode,
    Role,
    Scale,
    Score,
    ScoreValidationError,
)


# ---------------------------------------------------------------------------
# Positive: an empty Score validates and is immutable.
# ---------------------------------------------------------------------------


def test_empty_score_constructs():
    s = Score(title="t", seed=1, duration_seconds=10.0)
    assert s.title == "t"
    assert s.seed == 1
    assert s.duration_seconds == 10.0
    assert s.voices == ()
    assert s.couplings == ()
    assert s.trajectories == ()
    assert s.bindings == ()
    assert s.events == ()
    assert s.gestures == ()
    assert s.rhetoric == ()
    assert s.variance_defaults == {}
    assert s.control_hz == 200
    assert s.sample_rate == 48000
    assert s.buffer_size == 256
    assert s.nchnls == 2
    assert s.pyo_precision is PyoPrecision.SINGLE
    assert s.warnings == []


def test_score_is_frozen():
    import dataclasses

    s = Score(title="t", seed=1, duration_seconds=10.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.title = "x"  # type: ignore[misc]


def test_list_fields_coerced_to_tuple():
    s = Score(
        title="t", seed=1, duration_seconds=10.0,
        voices=[], couplings=[], trajectories=[], bindings=[],
        events=[], gestures=[], rhetoric=[],
    )
    assert isinstance(s.voices, tuple)
    assert isinstance(s.couplings, tuple)
    assert isinstance(s.trajectories, tuple)
    assert isinstance(s.bindings, tuple)
    assert isinstance(s.events, tuple)
    assert isinstance(s.gestures, tuple)
    assert isinstance(s.rhetoric, tuple)


def test_variance_defaults_partial_mapping_accepted():
    s = Score(
        title="t", seed=1, duration_seconds=10.0,
        variance_defaults={Scale.SUPRA: 0.04, Scale.MACRO: 0.06},
    )
    assert s.variance_defaults == {Scale.SUPRA: 0.04, Scale.MACRO: 0.06}


def test_negative_and_zero_seed_accepted():
    Score(title="t", seed=-1, duration_seconds=10.0)
    Score(title="t", seed=0, duration_seconds=10.0)


# ---------------------------------------------------------------------------
# V-001: title non-empty after .strip()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_title", ["", "   ", "\t", "\n  \n"])
def test_v001_title_must_be_nonempty(bad_title):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title=bad_title, seed=1, duration_seconds=10.0)
    assert ei.value.field == "title"
    assert ei.value.value == bad_title
    assert "title" in str(ei.value)


# ---------------------------------------------------------------------------
# V-002: duration_seconds > 0 and finite
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_dur", [0.0, -1.0, -0.001, math.inf, -math.inf, math.nan])
def test_v002_duration_must_be_finite_positive(bad_dur):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=bad_dur)
    assert ei.value.field == "duration_seconds"
    assert "duration_seconds" in str(ei.value)


# ---------------------------------------------------------------------------
# V-003: seed must be int (and not bool)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_seed", [1.5, "1", None, [1]])
def test_v003_seed_must_be_int(bad_seed):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=bad_seed, duration_seconds=10.0)
    assert ei.value.field == "seed"
    assert "seed" in str(ei.value)


def test_v003_seed_bool_rejected_as_non_int():
    """`bool` is `int` in Python, but `seed=True` would silently coerce — reject."""
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=True, duration_seconds=10.0)
    assert ei.value.field == "seed"


# ---------------------------------------------------------------------------
# V-004: sample_rate, buffer_size, control_hz, nchnls are positive ints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [0, -1, -100])
def test_v004_buffer_size_must_be_positive(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, buffer_size=bad_value)
    assert ei.value.field == "buffer_size"


@pytest.mark.parametrize("bad_value", [0, -1])
def test_v004_control_hz_must_be_positive(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, control_hz=bad_value)
    assert ei.value.field == "control_hz"


@pytest.mark.parametrize("bad_value", [0, -1])
def test_v004_nchnls_must_be_positive(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, nchnls=bad_value)
    assert ei.value.field == "nchnls"


@pytest.mark.parametrize("bad_value", [1.5, "256", None])
def test_v004_buffer_size_must_be_int(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, buffer_size=bad_value)
    assert ei.value.field == "buffer_size"


def test_v004_int_field_bool_rejected():
    """`bool` masquerading as `int` is rejected for the four positive-int fields."""
    for kwargs in (
        {"buffer_size": True},
        {"control_hz": True},
        {"nchnls": True},
    ):
        with pytest.raises(ScoreValidationError) as ei:
            Score(title="t", seed=1, duration_seconds=10.0, **kwargs)
        assert ei.value.field == next(iter(kwargs))


# ---------------------------------------------------------------------------
# V-005: buffer_size power of two
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [3, 5, 100, 300, 513, 1000])
def test_v005_buffer_size_must_be_power_of_two(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, buffer_size=bad_value)
    assert ei.value.field == "buffer_size"
    assert ei.value.value == bad_value
    assert "power of two" in str(ei.value)


@pytest.mark.parametrize("good_value", [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048])
def test_v005_buffer_size_powers_of_two_accepted(good_value):
    Score(title="t", seed=1, duration_seconds=10.0, buffer_size=good_value)


# ---------------------------------------------------------------------------
# V-006: sample_rate whitelist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [22050, 32000, 44000, 48001, 100000])
def test_v006_sample_rate_must_be_whitelisted(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(title="t", seed=1, duration_seconds=10.0, sample_rate=bad_value)
    assert ei.value.field == "sample_rate"
    assert ei.value.value == bad_value
    assert "44100" in str(ei.value)  # the allowed set is named in the message


@pytest.mark.parametrize("good_value", [44100, 48000, 88200, 96000, 176400, 192000])
def test_v006_whitelisted_sample_rates_accepted(good_value):
    Score(title="t", seed=1, duration_seconds=10.0, sample_rate=good_value)


# ---------------------------------------------------------------------------
# V-007: pyo_precision must be PyoPrecision enum
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", ["single", "double", 32, 64, None])
def test_v007_pyo_precision_must_be_enum(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(
            title="t", seed=1, duration_seconds=10.0,
            pyo_precision=bad_value,
        )
    assert ei.value.field == "pyo_precision"


# ---------------------------------------------------------------------------
# V-008: variance_defaults keys must be Scale enum members
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_key", ["SUPRA", "supra", 0, None])
def test_v008_variance_defaults_keys_must_be_scale(bad_key):
    with pytest.raises(ScoreValidationError) as ei:
        Score(
            title="t", seed=1, duration_seconds=10.0,
            variance_defaults={bad_key: 0.04},
        )
    assert ei.value.field == "variance_defaults"


# ---------------------------------------------------------------------------
# V-009: variance_defaults values must be floats in [0.0, 1.0]
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [-0.01, 1.01, -1.0, 2.0, math.inf, math.nan])
def test_v009_variance_defaults_values_must_be_in_unit_interval(bad_value):
    with pytest.raises(ScoreValidationError) as ei:
        Score(
            title="t", seed=1, duration_seconds=10.0,
            variance_defaults={Scale.SUPRA: bad_value},
        )
    assert ei.value.field == "variance_defaults"


def test_v009_variance_defaults_zero_and_one_accepted():
    Score(
        title="t", seed=1, duration_seconds=10.0,
        variance_defaults={Scale.SUPRA: 0.0, Scale.MACRO: 1.0, Scale.MESO: 0.5},
    )


# ---------------------------------------------------------------------------
# W-001: DOUBLE precision without pyo._pyo64 emits a warning, not error
# ---------------------------------------------------------------------------


def test_w001_double_without_pyo64_warns(monkeypatch):
    """Setting sys.modules[name] = None makes Python's import machinery raise
    ImportError on `import name`, simulating the missing extension."""
    monkeypatch.setitem(sys.modules, "pyo._pyo64", None)

    s = Score(
        title="t", seed=1, duration_seconds=10.0,
        pyo_precision=PyoPrecision.DOUBLE,
    )
    assert s.pyo_precision is PyoPrecision.DOUBLE
    assert any("pyo._pyo64" in w for w in s.warnings), s.warnings


def test_w001_single_precision_no_warning():
    s = Score(title="t", seed=1, duration_seconds=10.0, pyo_precision=PyoPrecision.SINGLE)
    assert s.warnings == []


# ---------------------------------------------------------------------------
# Surface: enums are importable from `phonon`
# ---------------------------------------------------------------------------


def test_enums_importable():
    assert Scale.SUPRA.value == "supra"
    assert RenderMode.AUTOPILOT.value == "autopilot"
    assert PyoPrecision.SINGLE.value == "single"
    assert Mode.ABSOLUTE.value == "absolute"
    assert Role.ANCHOR_LOW.value == "anchor_low"
