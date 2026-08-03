"""Tests for `phonon.render.reproducibility`.

Phase 0 ships `sha256_audio_file()` and the skip-marked render-reproducibility
test stubs. The actual render tests are filled in by Phase 1's renderer.
"""

import hashlib

import pytest

from phonon.render.reproducibility import sha256_audio_file


def test_sha256_audio_file_returns_lowercase_hex(tmp_path):
    payload = b"the quick brown fox jumps over the lazy dog\n"
    p = tmp_path / "x.bin"
    p.write_bytes(payload)

    actual = sha256_audio_file(p)
    expected = hashlib.sha256(payload).hexdigest()
    assert actual == expected
    assert actual == actual.lower()


def test_sha256_audio_file_streams_large_files(tmp_path):
    """Verify hashing a multi-chunk file matches a single-shot hash."""
    payload = b"x" * (256 * 1024)  # 256 KiB → ≥ 4 chunks at 64 KiB
    p = tmp_path / "big.bin"
    p.write_bytes(payload)

    actual = sha256_audio_file(p)
    expected = hashlib.sha256(payload).hexdigest()
    assert actual == expected


def test_sha256_audio_file_empty_file(tmp_path):
    p = tmp_path / "empty.bin"
    p.write_bytes(b"")
    actual = sha256_audio_file(p)
    expected = hashlib.sha256(b"").hexdigest()
    assert actual == expected


def test_sha256_audio_file_missing_path_raises(tmp_path):
    p = tmp_path / "does-not-exist.bin"
    with pytest.raises(FileNotFoundError):
        sha256_audio_file(p)


# ---------------------------------------------------------------------------
# Phase 1 placeholders. Skip-marked until the renderer lands.
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="awaiting Phase 1 render")
def test_render_is_bit_exact():
    """Two renders of the same Score must produce byte-identical audio (FR-036)."""
    raise NotImplementedError("Phase 1")


@pytest.mark.skip(reason="awaiting Phase 1 render")
def test_changing_control_hz_changes_audio():
    """Bumping `control_hz` must change at least one byte of the rendered audio (FR-037)."""
    raise NotImplementedError("Phase 1")
