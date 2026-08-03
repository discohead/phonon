"""Phase 1 substrate smoke test.

A permanent test that exercises Phase 0's substrate the way a Phase 1 author
will: a stub-module import path that resolves to an empty module, plus the
offline-Server fixture pumping one audio block. This test will continue to
pass when Phase 1 fills in `phonon.process.base` (the import will still
succeed; the fixture still works).

Per SC-007 and tasks T029.
"""


def test_phase_1_substrate_ready(manual_server):
    import phonon.process.base  # noqa: F401 — the import itself is the test

    assert manual_server.getIsBooted() == 1
    manual_server.process()
