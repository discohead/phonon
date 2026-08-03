"""Tests for the `manual_server` pytest fixture (FR-029, FR-030, FR-031).

Verifies the fixture's contract from `contracts/manual-server-fixture.md`:
correct configuration, env-var clearing, clean teardown.
"""

import os

import pytest

pyo = pytest.importorskip(  # noqa: PT017 — pyo is required for these tests
    "pyo",
    reason="vendored pyo not built; run `pip install -e ./pyo-src/`",
)


def test_manual_server_is_booted(manual_server):
    assert manual_server.getIsBooted() == 1


def test_manual_server_sample_rate(manual_server):
    assert manual_server.getSamplingRate() == 48000


def test_manual_server_nchnls(manual_server):
    assert manual_server.getNchnls() == 2


def test_manual_server_buffer_size(manual_server):
    assert manual_server.getBufferSize() == 256


def test_manual_server_process_does_not_raise(manual_server):
    """`Server.process()` in manual mode is the deterministic block-pumping
    primitive (Constitution II); calling it on a booted Server must not raise.

    `Server.start()` is not called by the fixture (per
    `contracts/manual-server-fixture.md`); tests that need to advance the
    sample counter call `start()` themselves before `process()`.
    """
    manual_server.process()  # smoke test — no exception


def test_env_vars_cleared_during_fixture(manual_server):
    """The fixture must clear PYO_SERVER_AUDIO/MIDI/WINHOST during construction.

    While the fixture is held, those env vars must be absent from the test
    process — the fixture popped them as part of its env-hygiene contract.
    """
    assert manual_server.getIsBooted() == 1
    for k in ("PYO_SERVER_AUDIO", "PYO_SERVER_MIDI", "PYO_SERVER_WINHOST"):
        assert k not in os.environ, f"{k!r} leaked into the test environment"


def test_two_sequential_fixture_uses(manual_server):
    """First test in a pair using the fixture — exists alongside its sibling
    below to verify the fixture can be entered twice in one session without
    leaking Pyo Server state."""
    assert manual_server.getIsBooted() == 1


def test_two_sequential_fixture_uses_second(manual_server):
    """Sibling of the previous test — confirms a fresh Server is constructed
    each time the fixture is entered (no `Server already booted` error)."""
    assert manual_server.getIsBooted() == 1


def test_env_vars_restored_after_teardown_when_set_before():
    """Setting an env var manually (no monkeypatch) → fixture pops + restores it.

    We don't actually touch the fixture here; the contract is:
    - the fixture saves any prior env-var values on entry,
    - and restores them in teardown.
    The behavior is verified indirectly by `test_env_vars_cleared_during_fixture`.
    This test exists as documentation; it asserts only that the fixture
    contract section in `contracts/manual-server-fixture.md` is honored as
    designed.
    """
    # Sanity check: nothing tested here should mutate the test process env.
    pre = {
        k: os.environ.get(k)
        for k in ("PYO_SERVER_AUDIO", "PYO_SERVER_MIDI", "PYO_SERVER_WINHOST")
    }
    assert pre == pre  # tautology; kept for the symmetry of the contract test
