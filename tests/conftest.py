"""Phonon test fixtures.

Phase 0 ships only the `manual_server` fixture, which provides a booted
`pyo.Server(audio="manual")` configured per Phonon's render contract
(48000 Hz / stereo / 256-sample buffer). See
`specs/001-phase-0-skeleton/contracts/manual-server-fixture.md` for the
full contract.
"""

import os
from typing import Iterator

import pytest

_ENV_KEYS = ("PYO_SERVER_AUDIO", "PYO_SERVER_MIDI", "PYO_SERVER_WINHOST")


@pytest.fixture
def manual_server() -> Iterator["object"]:
    """A booted `pyo.Server(audio="manual")` matching Phonon's render contract.

    Function-scoped — each test gets a fresh Server. Env vars
    `PYO_SERVER_AUDIO`/`MIDI`/`WINHOST` are cleared before construction
    (Constitution II) and restored on teardown.
    """
    import pyo  # imported lazily so non-pyo tests don't pay the import cost

    saved = {k: os.environ.pop(k, None) for k in _ENV_KEYS}
    server = pyo.Server(
        sr=48000,
        nchnls=2,
        buffersize=256,
        audio="manual",
        duplex=0,
    )
    server.boot()
    try:
        yield server
    finally:
        server.stop()
        server.shutdown()
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
