"""Reproducibility helpers used by Phase 1+ render-time tests.

Phase 0 ships only `sha256_audio_file()`; the render-config pinning helpers
(env-var clearing, single-precision/double-precision selection, sample-counter
piece-time derivation) land in Phase 1 alongside the renderer.
"""

import hashlib
from pathlib import Path

__all__ = ["sha256_audio_file"]


_CHUNK_BYTES = 64 * 1024


def sha256_audio_file(path: Path) -> str:
    """Return the lowercase-hex SHA-256 digest of the file at `path`.

    Streams the file in 64 KiB chunks so memory stays bounded regardless of
    file size. Matches `shasum -a 256 path` byte-for-byte. Raises
    `FileNotFoundError` if the path does not exist.
    """
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_BYTES)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()
