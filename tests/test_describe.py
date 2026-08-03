"""Tests for `phonon.Score.describe()`.

Covers FR-022 through FR-028 and contracts/score-api.md (Output schema +
YAML round-trip + entity-list and variance_profile shape).
"""

import yaml

from phonon import PyoPrecision, Scale, Score, __version__


def _empty_score(**overrides):
    kwargs = dict(title="t", seed=1, duration_seconds=10.0)
    kwargs.update(overrides)
    return Score(**kwargs)


# ---------------------------------------------------------------------------
# Schema keys (FR-022, FR-023)
# ---------------------------------------------------------------------------


def test_describe_returns_dict_with_required_keys():
    d = _empty_score().describe()
    assert isinstance(d, dict)
    expected = {
        "title", "duration", "seed", "render_contract",
        "voices", "trajectories", "events", "gestures", "rhetoric",
        "variance_profile", "warnings",
    }
    missing = expected - set(d.keys())
    assert missing == set(), f"missing keys: {missing}"


def test_describe_passes_through_title_and_seed():
    s = _empty_score(title="Hello, Phonon", seed=1729)
    d = s.describe()
    assert d["title"] == "Hello, Phonon"
    assert d["seed"] == 1729


def test_describe_does_not_mutate_internal_state():
    s = _empty_score()
    d1 = s.describe()
    d2 = s.describe()
    assert d1 == d2
    # mutating the returned dict must not affect a subsequent call
    d1["voices"].append("x")
    d3 = s.describe()
    assert d3["voices"] == []


# ---------------------------------------------------------------------------
# Duration formatting (FR-026)
# ---------------------------------------------------------------------------


def test_describe_duration_under_one_hour_uses_M_SS():
    s = _empty_score(duration_seconds=420.0)  # 7:00
    assert s.describe()["duration"] == "7:00"


def test_describe_duration_one_second():
    s = _empty_score(duration_seconds=1.0)
    assert s.describe()["duration"] == "0:01"


def test_describe_duration_under_one_minute():
    s = _empty_score(duration_seconds=42.0)
    assert s.describe()["duration"] == "0:42"


def test_describe_duration_at_one_hour_uses_H_MM_SS():
    # 3600 seconds = 1:00:00 boundary; per data-model.md, ">= 3600" uses H:MM:SS
    s = _empty_score(duration_seconds=3600.0)
    assert s.describe()["duration"] == "1:00:00"


def test_describe_duration_long_form():
    # 1h 23m 45s
    s = _empty_score(duration_seconds=5025.0)
    assert s.describe()["duration"] == "1:23:45"


def test_describe_duration_fractional_rounds_down():
    s = _empty_score(duration_seconds=10.9)
    assert s.describe()["duration"] == "0:10"


# ---------------------------------------------------------------------------
# render_contract (FR-027)
# ---------------------------------------------------------------------------


def test_describe_render_contract_fields():
    s = _empty_score(
        sample_rate=96000, buffer_size=512, control_hz=400,
        pyo_precision=PyoPrecision.DOUBLE,
    )
    rc = s.describe()["render_contract"]
    assert rc["sample_rate"] == 96000
    assert rc["buffer_size"] == 512
    assert rc["control_hz"] == 400
    assert rc["pyo_precision"] == "double"
    assert rc["framework_version"] == __version__


def test_describe_render_contract_default_precision_is_single():
    rc = _empty_score().describe()["render_contract"]
    assert rc["pyo_precision"] == "single"


def test_describe_render_contract_framework_version_is_string():
    rc = _empty_score().describe()["render_contract"]
    assert isinstance(rc["framework_version"], str)


# ---------------------------------------------------------------------------
# Entity lists are [] in Phase 0 (FR-022)
# ---------------------------------------------------------------------------


def test_describe_entity_lists_are_empty():
    d = _empty_score().describe()
    for key in ("voices", "trajectories", "events", "gestures", "rhetoric"):
        assert d[key] == [], f"{key!r} expected empty list, got {d[key]!r}"
        assert isinstance(d[key], list), f"{key!r} must be a list, got {type(d[key])}"


# ---------------------------------------------------------------------------
# variance_profile (FR-025)
# ---------------------------------------------------------------------------


def test_describe_variance_profile_uses_enum_names_as_keys():
    s = _empty_score(
        variance_defaults={
            Scale.SUPRA: 0.04,
            Scale.MACRO: 0.06,
            Scale.MESO: 0.15,
        },
    )
    vp = s.describe()["variance_profile"]
    assert vp == {"SUPRA": 0.04, "MACRO": 0.06, "MESO": 0.15}


def test_describe_variance_profile_only_contains_present_scales():
    s = _empty_score(variance_defaults={Scale.SUPRA: 0.04})
    vp = s.describe()["variance_profile"]
    assert vp == {"SUPRA": 0.04}
    assert "MICRO" not in vp


def test_describe_variance_profile_empty_when_unset():
    vp = _empty_score().describe()["variance_profile"]
    assert vp == {}


# ---------------------------------------------------------------------------
# warnings field (FR-024 — copy semantics)
# ---------------------------------------------------------------------------


def test_describe_warnings_default_empty():
    assert _empty_score().describe()["warnings"] == []


# ---------------------------------------------------------------------------
# YAML round-trip (FR-024, SC-002)
# ---------------------------------------------------------------------------


def test_describe_yaml_round_trip_empty_score():
    s = _empty_score()
    d = s.describe()
    serialized = yaml.safe_dump(d)
    restored = yaml.safe_load(serialized)
    assert restored == d


def test_describe_yaml_round_trip_with_variance_profile():
    s = _empty_score(
        title="Hello, Phonon",
        seed=1729,
        duration_seconds=420.0,
        variance_defaults={
            Scale.SUPRA: 0.04,
            Scale.MACRO: 0.06,
            Scale.MESO: 0.15,
            Scale.MICRO: 0.20,
        },
    )
    d = s.describe()
    serialized = yaml.safe_dump(d)
    restored = yaml.safe_load(serialized)
    assert restored == d


def test_describe_no_enum_leakage():
    """Every value must be YAML-safe: no enum members, no custom classes."""
    s = _empty_score(
        pyo_precision=PyoPrecision.DOUBLE,
        variance_defaults={Scale.SUPRA: 0.04, Scale.MACRO: 0.06},
    )
    d = s.describe()

    def assert_yaml_safe(value, path="root"):
        if isinstance(value, dict):
            for k, v in value.items():
                assert isinstance(k, (str, int, float, bool)) or k is None, (
                    f"non-scalar key at {path}: {k!r}"
                )
                assert_yaml_safe(v, f"{path}.{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                assert_yaml_safe(v, f"{path}[{i}]")
        else:
            assert isinstance(value, (str, int, float, bool)) or value is None, (
                f"non-scalar value at {path}: {value!r} (type={type(value).__name__})"
            )

    assert_yaml_safe(d)
