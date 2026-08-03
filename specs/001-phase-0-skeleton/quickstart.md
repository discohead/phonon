# Quickstart: Phase 0 — Skeleton

This is the first-ten-minutes onboarding for a contributor (human or agent) reaching the Phase 0 deliverable for the first time. After Phase 0 merges, running these steps end-to-end on a fresh macOS-arm64 clone should reach a green test suite in under 10 minutes wall time (SC-001).

## Prerequisites

- Git, Python 3.9+ (3.11+ recommended), Homebrew (macOS) or apt (Linux) or vcpkg+MSYS2 (Windows).
- About 1 GB of free disk for the vendored Pyo build.

## 1. Clone

```bash
git clone <phonon repo URL>
cd phonon
git checkout 001-phase-0-skeleton   # or main, after Phase 0 merges
```

## 2. Install native dependencies

### macOS (arm64 or x86_64)

```bash
brew install portaudio portmidi libsndfile liblo libogg libvorbis flac opus mpg123 lame
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install -y \
    portaudio19-dev libportmidi-dev libsndfile1-dev liblo-dev \
    libogg-dev libvorbis-dev libflac-dev libopus-dev libmpg123-dev libmp3lame-dev
```

### Windows

Follow `pyo-src/scripts/win/` for vcpkg + MSYS2 mingw64 setup. The `pyo-src/CLAUDE.md` walks through the toolchain.

## 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

## 4. Build vendored Pyo from source

```bash
pip install -e ./pyo-src/
```

This compiles Pyo's C extensions against the native deps installed in step 2. Single-precision (`pyo._pyo`) only — Phase 0 does not exercise double-precision. Build time on macOS-arm64 is ~30–60 s.

Verify:

```bash
python -c "import pyo; print(pyo.__version__)"
# expected: 1.0.6 (or matching the vendored copy's version.py)
```

## 5. Install Phonon (editable, with dev extras)

```bash
pip install -e ".[dev]"
```

This pulls Phonon's runtime deps (`numpy`, `PyYAML`) and dev extras (`pytest`, `hypothesis`).

Verify:

```bash
python -c "from phonon import Score, Scale, __version__; print(__version__)"
# expected: 0.1.0
# Note: `derive` is added to the public surface in US2 (Phase 0's test substrate); see step 8.
```

## 6. Run the test suite

```bash
pytest
```

Expected output sketch (numbers approximate; exact counts may evolve):

```
tests/test_pyo_audit.py ............ [audit pass]
tests/test_score.py .................. [validation positive + negative]
tests/test_describe.py ........ [schema + YAML round-trip]
tests/test_seedseq.py .... [determinism]
tests/test_reproducibility.py s s [skip-marked, awaiting Phase 1]
======================== N passed, 2 skipped in M.MMs ========================
```

The two skipped tests are deliberate Phase 1 placeholders (FR-036, FR-037).

If anything fails, the most likely causes:

1. **`Pyo audit failed` and rest skipped** — vendored Pyo has drifted from Appendix C. Run `pytest tests/test_pyo_audit.py -v` for the named class. This is the audit doing its job.
2. **`pyo` import error** — native deps missing or vendored Pyo not built. Re-run step 4 with `--verbose`.
3. **`numpy` version mismatch** — the determinism tests rely on `numpy.random.SeedSequence` semantics; `pyproject.toml` pins a numpy major version.

## 7. Construct your first Score

```python
# scratch.py — not committed; just for orientation
from phonon import Score, Scale

score = Score(
    title="Hello, Phonon",
    seed=1729,
    duration_seconds=420.0,                 # 7 minutes
    variance_defaults={
        Scale.SUPRA: 0.04,
        Scale.MACRO: 0.06,
        Scale.MESO:  0.15,
        Scale.MICRO: 0.20,
    },
)

import yaml
print(yaml.safe_dump(score.describe()))
```

Expected output (modulo dict-key order, which YAML preserves from Python 3.7+):

```yaml
title: Hello, Phonon
duration: 7:00
seed: 1729
render_contract:
  sample_rate: 48000
  buffer_size: 256
  control_hz: 200
  pyo_precision: single
  framework_version: 0.1.0
voices: []
trajectories: []
events: []
gestures: []
rhetoric: []
variance_profile:
  SUPRA: 0.04
  MACRO: 0.06
  MESO: 0.15
  MICRO: 0.2
warnings: []
```

Phase 0's user-facing capability ends here. Adding voices, trajectories, events, gestures, or rhetoric requires Phase 1+.

## 8. Try the determinism contract

```python
from phonon import derive

g1 = derive(1729, "trajectory", "order")
g2 = derive(1729, "trajectory", "order")

print(g1.bytes(16).hex())   # same on every run, every platform
print(g2.bytes(16).hex())   # same as g1
```

Both `print` lines should produce identical output. The Phase 0 CI cross-platform consistency check (SC-009) verifies this.

## 9. Inspect the substrate Phase 1 builds on

A Phase 1 author opens `phonon/process/base.py`, `phonon/render/scheduler.py`, or `phonon/voice.py` and finds a one-line docstring stub. Their Phase 1 spec says what to fill in. The infrastructure (test fixtures, CI, audit) already works.

```python
# tests/test_my_phase_1_thing.py — hypothetical Phase 1 test
def test_pyo_sine_emits_audio(manual_server):
    from pyo import Sine
    s = Sine(freq=440).out()
    manual_server.process()                       # one block
    assert manual_server.getCurrentTime() > 0
```

The `manual_server` fixture is provided by Phase 0's `tests/conftest.py`. The Phase 1 author writes the test logic; they do not write any infrastructure.

## 10. CI

After pushing your branch, GitHub Actions runs the four-platform matrix. Each leg installs native deps, builds vendored Pyo, runs the Pyo audit, and (on audit pass) runs the rest of the suite. Total wall time per leg: ≤ 10 min (SC-005).

If the audit fails on any leg, the rest of the suite is skipped on that leg with a clear "Pyo audit failed; skipping remaining tests" message in the GitHub Actions log (FR-041).

---

## Troubleshooting

### `RuntimeError: Server already booted` mid-test

The previous test's Server didn't shut down cleanly. The `manual_server` fixture handles teardown; if you booted a Server outside the fixture, you must `.stop().shutdown()` yourself.

### `ScoreValidationError: sample_rate must be one of {44100, ...}`

You passed a sample rate Phonon doesn't accept (per R-004). Use one of the whitelisted rates or amend the constitution.

### Snapshot test fails after intentional schema change

Phase 0's `test_describe.py` includes a snapshot. To regenerate:

```bash
PHONON_UPDATE_SNAPSHOTS=1 pytest tests/test_describe.py
```

Review the diff of `tests/snapshots/empty_score_describe.yaml` carefully — schema changes cascade into `Score.describe()`'s contract.

### `ImportError: cannot import name 'Voice' from 'phonon'`

`Voice` lands in Phase 2. Phase 0's public surface is intentionally minimal (R-010); Phase 1+ specs add to `phonon/__init__.py` as their types come online.

### `from pyo import *` warning from a linter

Don't. Constitution VI forbids it. Use qualified imports: `from pyo import Sine, SigTo, Server`.

---

## Where to go next

- **Reading**: `context/phonon-v1.md` (the design spec; ~2000 lines but skim §1–§2 + §15 + §17 + Appendix C first), `.specify/memory/constitution.md` (the seven principles).
- **Phase 1 spec**: when ready, run `/speckit-specify "Phase 1"` to draft the next phase's spec. The constitution check there will rely on the substrate Phase 0 just shipped.
- **Phase 0 plan**: this directory (`specs/001-phase-0-skeleton/`).

If anything in this quickstart drifts from reality after a future change, that is a signal that Phase 0's contract has changed; either revert the change or amend this file in the same PR.
