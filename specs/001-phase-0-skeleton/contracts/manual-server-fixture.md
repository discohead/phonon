# Contract: `manual_server` pytest fixture

The Phase 0 test infrastructure that Phase 1+ tests consume to exercise offline rendering against a real `pyo.Server`. Lives at `tests/conftest.py`.

## Usage from a test

```python
def test_some_phase_1_feature(manual_server):
    # manual_server is a booted pyo.Server, audio="manual", duplex=0
    sr = manual_server.getSamplingRate()        # 48000
    assert sr == 48000

    # Pump one audio block:
    manual_server.process()
    elapsed = manual_server.getCurrentTime()
    assert elapsed == pytest.approx(256 / 48000, rel=1e-9)
```

The fixture is `@pytest.fixture` (function-scoped) so each test gets a fresh Server. Boot is fast on `audio="manual"` (no real device probe) — single-test overhead is acceptable.

## Provided Server configuration

The fixture yields `pyo.Server(...).boot()` with these arguments:

| Argument | Value | Why |
|---|---|---|
| `sr` | `48000` | Phonon default sample rate (per Score render contract default) |
| `nchnls` | `2` | stereo (Phase 0 / v1 default) |
| `buffersize` | `256` | Phonon default buffer size |
| `audio` | `"manual"` | offline, externally pumped (per Constitution II / R-005) |
| `duplex` | `0` | output-only; no input device probed |

Other Server arguments (`jackname`, `ichnls`, `winhost`, `midi`, `verbosity`) take Pyo's defaults. The fixture does NOT call `setMidiInputDevice` or `recordOptions` — those are test-specific concerns and stay in the consuming test.

## Environment hygiene (Constitution II)

Before constructing the Server, the fixture clears these process environment variables (per Pyo's `lib/server.py` constructor at lines ~684–697, which falls back to env vars if set):

- `PYO_SERVER_AUDIO`
- `PYO_SERVER_MIDI`
- `PYO_SERVER_WINHOST`

This guarantees the developer's shell environment cannot silently change the audio backend mid-test (which would break determinism). The clearing is non-destructive: the fixture saves the prior values (if any) and restores them on teardown.

```python
@pytest.fixture
def manual_server():
    saved = {k: os.environ.pop(k, None) for k in
             ("PYO_SERVER_AUDIO", "PYO_SERVER_MIDI", "PYO_SERVER_WINHOST")}
    server = pyo.Server(sr=48000, nchnls=2, buffersize=256, audio="manual", duplex=0)
    server.boot()
    try:
        yield server
    finally:
        server.stop()
        server.shutdown()
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
```

## Teardown guarantee

On test exit (success, failure, or exception), the fixture calls `Server.stop()` then `Server.shutdown()`. Subsequent tests get a fresh Server — there is no shared global state across tests beyond what Pyo holds at the C-extension level (Pyo allows multiple boot/shutdown cycles in one process, per its own pytest fixture at `pyo-src/tests/pytests/conftest.py`).

## Properties (FR-029, FR-030, FR-031)

| Property | Verified by |
|---|---|
| Server is booted on entry | `manual_server.getIsBooted() == 1` |
| Server is `audio="manual"` | (configuration is fixed; not introspectable from Python — verified by absence of audio thread, see below) |
| `sr == 48000`, `nchnls == 2`, `buffersize == 256` | `getSamplingRate()`, `getNchnls()`, `getBufferSize()` |
| Env vars are cleared during boot | a meta-test sets `PYO_SERVER_AUDIO=portaudio` in the test process, asks for the fixture, and asserts the resulting Server is still in manual mode |
| Teardown cleans up | a follow-up test in the same session boots its own Server without leaked Pyo state (no `Server already booted` error) |

## What this contract does NOT promise

- The fixture does NOT call `Server.start()`. In manual mode, `start()` arms recording (if `recordOptions` was called) but does not begin audio computation; tests that need recording configure `recordOptions` themselves and call `start()` explicitly.
- The fixture does NOT pre-build any Pyo graph. Tests build their own.
- The fixture does NOT auto-process blocks. Tests that want audio computation call `manual_server.process()` themselves.
- The fixture does NOT seed `Server.setGlobalSeed`. That is a piece-rendering concern (Phase 1+ renderer wires it). Tests that need a known global seed set it explicitly inside the test body.
- The fixture does NOT support `audio="portaudio"` or live mode. A separate `live_server` fixture may land in Phase 3 alongside the live-mode renderer; Phase 0 only ships the offline fixture.
- The fixture is function-scoped, not session-scoped. Tests that share a Server across many cases must use a different fixture (out of Phase 0 scope).

## Cross-references

- `pyo-src/tests/pytests/conftest.py` — Pyo's own pytest fixture; uses `Server(sr=48000, buffersize=512, audio="manual")`. We use `buffersize=256` to match the Phonon render contract.
- `pyo-src/pyo/lib/server.py` lines 684–697 — env-var fallback logic that motivates our env-clearing.
- Constitution II — bit-exact reproducibility, env-var clearing.
- Spec FR-029, FR-030, FR-031.
