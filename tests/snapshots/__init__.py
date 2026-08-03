"""In-tree YAML snapshot harness for Phonon tests.

See `_snapshot.py` for the implementation. Re-exported here so tests can write
`from tests.snapshots import assert_snapshot` (or, more commonly,
`from .snapshots import assert_snapshot` when test modules are siblings).
"""

from tests.snapshots._snapshot import assert_snapshot

__all__ = ["assert_snapshot"]
