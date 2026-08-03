"""Snapshot test for `Score.describe()` — pins the Phase 0 schema (FR-035).

If the `Score.describe()` schema changes intentionally, regenerate via
`PHONON_UPDATE_SNAPSHOTS=1 pytest tests/test_describe_snapshot.py` and review
the YAML diff in the same PR.
"""

from pathlib import Path

from phonon import Scale, Score

from tests.snapshots import assert_snapshot


SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "empty_score_describe.yaml"


def test_empty_score_describe_matches_snapshot():
    score = Score(
        title="empty",
        seed=1729,
        duration_seconds=420.0,
        variance_defaults={
            Scale.SUPRA: 0.04,
            Scale.MACRO: 0.06,
            Scale.MESO:  0.15,
            Scale.MICRO: 0.20,
        },
    )
    assert_snapshot(score.describe(), SNAPSHOT_PATH)
