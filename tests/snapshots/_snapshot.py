"""Tiny in-tree snapshot helper — no third-party dependency.

Snapshots are stored as YAML under `tests/snapshots/`. To regenerate after an
intentional schema change:

    PHONON_UPDATE_SNAPSHOTS=1 pytest tests/test_describe_snapshot.py

The update path emits a `pytest.PytestWarning` so the regeneration is never
silent in CI logs.
"""

import os
import warnings
from pathlib import Path
from typing import Any

import pytest
import yaml

__all__ = ["assert_snapshot"]


_UPDATE_ENV = "PHONON_UPDATE_SNAPSHOTS"


def assert_snapshot(actual: Any, snapshot_path: Path) -> None:
    """Assert that `actual` equals the YAML-deserialized contents of `snapshot_path`.

    If the env var `PHONON_UPDATE_SNAPSHOTS=1` is set, write `yaml.safe_dump(actual)`
    to `snapshot_path` (creating parent directories) and emit a `pytest.PytestWarning`
    so the regeneration is visible in test output.
    """
    snapshot_path = Path(snapshot_path)
    if os.environ.get(_UPDATE_ENV) == "1":
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(yaml.safe_dump(actual, sort_keys=True))
        warnings.warn(
            f"Snapshot updated: {snapshot_path} (PHONON_UPDATE_SNAPSHOTS=1)",
            pytest.PytestWarning,
            stacklevel=2,
        )
        return

    if not snapshot_path.exists():
        raise AssertionError(
            f"Snapshot file does not exist: {snapshot_path}\n"
            f"Generate it with PHONON_UPDATE_SNAPSHOTS=1 pytest <this test>"
        )

    expected = yaml.safe_load(snapshot_path.read_text())
    assert actual == expected, (
        f"Snapshot mismatch at {snapshot_path}:\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {actual!r}\n"
        f"If the change is intentional, regenerate with "
        f"PHONON_UPDATE_SNAPSHOTS=1 pytest <this test>"
    )
