# Implementation Plan: Phase 0 — Skeleton

**Branch**: `001-phase-0-skeleton` | **Date**: 2026-04-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification at `specs/001-phase-0-skeleton/spec.md`

## Summary

Phase 0 ships the substrate Phase 1 builds on: an installable `phonon` Python package whose only functional capability today is constructing, validating, and describing **empty** `Score` values; a deterministic seeded-RNG hierarchy `derive(seed, kind, name)` that future stochastic primitives will route through; a pytest fixture providing a booted `pyo.Server(audio="manual")` configured per the framework's render contract; a Pyo audit test that pins the constructor signatures of every Pyo class enumerated in design spec Appendix C; and a four-platform GitHub Actions matrix (macOS-arm64, macOS-x86_64, ubuntu-latest, windows-latest) that builds vendored Pyo from source, runs the audit first, and only then runs the rest of the suite.

The package is laid out per design spec §17 in full (every module exists), but `__init__.py` exports only types whose implementations are functional in Phase 0 — `Score`, `ScoreValidationError`, the five enums (`Scale`, `RenderMode`, `PyoPrecision`, `Mode`, `Role`), and the seedseq helper. Voice/Trajectory/Coupling/Binding/Event/Gesture/Rhetoric module files exist as docstring-only stubs to be filled in by their Phase 1+ specs. The CLI, the renderer, MIDI/OSC, the process primitive layer, and any audio output are explicitly out of scope.

## Technical Context

**Language/Version**: Python 3.9+ (matching vendored Pyo's `pyproject.toml` floor; supported through 3.13)
**Primary Dependencies**: `numpy` (seeded RNG via `SeedSequence` + `default_rng`); `PyYAML` (`describe()` → YAML serialization); vendored `pyo` 1.0.6 at `pyo-src/` (built locally, single-precision `pyo._pyo` only in Phase 0)
**Storage**: None. Phase 0 produces no audio files, no caches, no databases. The piece file is the composition (Constitution VII).
**Testing**: `pytest` (test runner), `pytest`-style snapshot comparisons rolled in-tree (no third-party snapshot lib), `hypothesis` carried in dev extras for Phase 1+ (Phase 0 may use it but does not require it)
**Target Platform**: macOS-arm64 (primary dev), macOS-x86_64 (`macos-13` runner), ubuntu-latest, windows-latest. Native deps via Homebrew on macOS, apt on Linux, vcpkg+MSYS2 mingw64 on Windows per design spec §19.5.
**Project Type**: Python library (single package). CLI entry point is deferred to Phase 4. Layout follows design spec §17 in full.
**Performance Goals**: developer bootstrap ≤ 10 min wall on a fresh macOS-arm64 clone (SC-001); per-platform CI ≤ 10 min (SC-005); `Score(...)` + `Score.describe()` runs in well under a second for any Phase 0 input (no boot, no I/O); Pyo audit test runs in seconds. No audio-rate performance to budget yet.
**Constraints**: Constitution II (bit-exact RNG via numpy `SeedSequence`; env vars cleared at Server construction); VI (no `from pyo import *`, no `pyo.lib.events`, qualified imports only); V (`describe()` walks the static graph, never boots a Server); VII (no persistence outside the piece source). No audio I/O permitted.
**Scale/Scope**: ~14 module files (mostly stub docstrings), ~150–250 SLOC of substantive Python, ~10 test files, 1 GitHub Actions workflow with 4 matrix legs, ~46 functional requirements, ~9 success criteria.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Source: `.specify/memory/constitution.md` (Phonon Constitution v1.0.0).

| Principle | Phase 0 disposition | Verdict |
|---|---|---|
| **I. Aesthetic Refusals Are Load-Bearing** | Phase 0 has no piece-authoring surface beyond an empty `Score`. Nothing on the §21 refusal list is added or even hinted at — no song-form, no diatonic helpers, no MIDI-file authoring, no event lists, no mastering, no GUI, no hot-swap. | **PASS** |
| **II. Bit-Exact Reproducibility (Offline)** | Phase 0 lays the foundations. `derive(seed, kind, name)` (FR-044–046) routes every future stochastic decision through `numpy.random.SeedSequence` + `default_rng` — bit-identical across runs and platforms (verified by SC-009). The `manual_server` fixture clears `PYO_SERVER_AUDIO`/`MIDI`/`WINHOST` env vars before construction (FR-030). No Pyo random objects are constructed in Phase 0. The render contract `(sr, buffer, control_hz, pyo_precision)` is enforced as a Score-construction invariant (FR-018, FR-019, FR-027). Reproducibility tests are scaffolded with `pytest.skip` markers awaiting Phase 1 (FR-036, FR-037). | **PASS** |
| **III. Process-First, Threshold-Driven** | No event surface in Phase 0. Voice/Trajectory/Coupling/Event are stub modules; nothing authors timed events. | **PASS** |
| **IV. Roads' Multiscale Time Is Canonical** | The five-scale `Scale` enum (`SAMPLE`, `MICRO`, `MESO`, `MACRO`, `SUPRA`) is first-class in Phase 0 and used as the key type of `variance_defaults` (FR-009 via design spec §15.1, key entity). Trajectories (which carry `scale`) are deferred to Phase 2; scale-asymmetry validation will land then. | **PASS** |
| **V. Agent-Readiness Is The Primary API Driver** | `Score` is a declarative value (frozen dataclass with eager validation). `Score.describe()` walks the static graph alone, never boots a Server (FR-023). Every public type has a stable, semantic name. `Reference` and the closed action sets are deferred to later phases — Phase 0 does not introduce any imperative-construction or object-identity-based shortcuts. | **PASS** |
| **VI. Vendored Pyo, Patches As Commits** | Phase 0 does not modify `pyo-src/`. All Pyo references use qualified imports (FR-007). The Pyo audit test lands in Phase 0 and runs first in CI (FR-032, FR-033, FR-041), guarding against signature drift. `pyo.lib.events` and `pyo.lib.pattern.Score` are not imported anywhere. | **PASS** |
| **VII. The Piece File Is The Composition** | No persistence is introduced — no caches, no project-state directory beyond `specs/` (which is git-tracked and is the spec workflow's output, not piece state). Test snapshots live in `tests/snapshots/` and describe the empty-Score schema, not any composer-authored material. | **PASS** |

All gates **PASS**. Complexity Tracking is empty.

### Post-design re-check (after `data-model.md` + `contracts/` + `research.md`)

The Phase 1 design artifacts (data model, contracts, research decisions) reaffirm the pre-design verdict. Specifically:

- **R-001** (`derive` via `hashlib.sha256` + `SeedSequence`): satisfies Principle II's bit-exact guarantee across runs and platforms (SC-009 verifies this in CI).
- **R-002** (`Score` as `frozen=True kw_only=True slots=True` dataclass with `__post_init__` validation): satisfies Principle V's "declarative value, not imperative construction" requirement.
- **R-003** (in-tree snapshot harness, no third-party lib): no new dependency surface; nothing additional to audit for vendoring or LGPL contagion (Constitution VI).
- **R-010** (`__init__.py` exports only Phase 0-functional names): satisfies Principle V's "every public type has a stable, semantic name" by ensuring `from phonon import X` either succeeds with a working type or raises a clean `ImportError` — no half-baked stubs leak into the public surface.
- **R-011** (Pyo audit covers all of Appendix C, not just Phase 0 imports): directly satisfies Constitution VI's audit-test clause.

No new violations, no new justifications. **Post-design check: PASS.**

## Project Structure

### Documentation (this feature)

```text
specs/001-phase-0-skeleton/
├── plan.md                  # this file
├── research.md              # Phase 0 research (resolves implementation choices)
├── data-model.md            # Phase 1 design (Score, enums, error type, derive())
├── contracts/
│   ├── score-api.md         # Score(...) and Score.describe() contract
│   ├── seedseq-api.md       # derive(seed, kind, name) contract
│   └── manual-server-fixture.md  # pytest fixture contract for Phase 1+ consumers
├── quickstart.md            # bootstrap + first-test walkthrough
├── checklists/
│   └── requirements.md      # spec quality checklist (already passed)
└── tasks.md                 # generated by /speckit-tasks (not by /speckit-plan)
```

### Source Code (repository root)

Faithful to design spec §17. Every module exists in Phase 0; substantive code lives only in `score.py`, `seedseq.py`, the enum modules, `version.py`, and `render/reproducibility.py` (the `sha256_audio_file` helper).

```text
phonon/
├── __init__.py                       # exports: Score, ScoreValidationError, Scale, RenderMode,
│                                     #          PyoPrecision, Mode, Role, derive, __version__
├── version.py                        # __version__ = "0.1.0"
├── score.py                          # Score (frozen dataclass), ScoreValidationError,
│                                     # describe(), eager validation, render-contract check
├── voice.py                          # docstring stub; defines Role enum (re-exported)
├── trajectory.py                     # docstring stub
├── coupling.py                       # docstring stub
├── binding.py                        # docstring stub; defines Mode enum (re-exported)
├── rhetoric.py                       # docstring stub
├── event.py                          # docstring stub
├── gesture.py                        # docstring stub
├── shape.py                          # docstring stub
├── seedseq.py                        # derive(seed, kind, name) -> Generator
├── _scale.py                         # Scale enum (separate to avoid trajectory.py import cost)
├── _render_mode.py                   # RenderMode + PyoPrecision enums
└── process/
│   ├── __init__.py                   # docstring stub
│   ├── base.py                       # docstring stub (Process, Threshold, SampleAndHold)
│   ├── generators_pyo.py             # docstring stub
│   ├── generators_chaos.py           # docstring stub
│   ├── randoms_seeded.py             # docstring stub
│   ├── pyo_compat.py                 # docstring stub
│   ├── transforms.py                 # docstring stub
│   └── sample.py                     # docstring stub
├── render/
│   ├── __init__.py                   # docstring stub
│   ├── scheduler.py                  # docstring stub
│   ├── pyo_backend.py                # docstring stub
│   ├── server.py                     # docstring stub
│   ├── midi_io.py                    # docstring stub
│   ├── osc_io.py                     # docstring stub
│   ├── recorder.py                   # docstring stub
│   └── reproducibility.py            # sha256_audio_file (functional); rest stub
└── cli/
    ├── __init__.py                   # docstring stub
    └── main.py                       # docstring stub (Phase 4)

tests/
├── conftest.py                       # manual_server fixture (FR-029–031), env-clearing
├── test_pyo_audit.py                 # FR-032–034: Appendix C signatures + Server methods
├── test_score.py                     # US1: validation positive + negative cases
├── test_describe.py                  # US1: describe() schema + YAML round-trip
├── test_seedseq.py                   # FR-045–046: cross-run determinism + uncorrelated streams
├── test_reproducibility.py           # sha256_audio_file (functional); render tests skip-marked
└── snapshots/
    └── empty_score_describe.yaml     # FR-035

.github/workflows/
└── ci.yml                            # 4-platform matrix; Pyo audit step first

pyo-src/                              # vendored, unchanged in Phase 0
context/                              # design spec; unchanged in Phase 0
.specify/                             # constitution + spec workflow; unchanged in Phase 0

pyproject.toml                        # FR-003: phonon package, deps, dev extras
README.md                             # touched only if explicitly requested
```

**Structure Decision**: Single Python package mirroring design spec §17 verbatim, with explicit module stubs for phases not yet authored. Two private modules `_scale.py` and `_render_mode.py` host the foundation enums to keep `score.py` from importing trajectory/render modules unnecessarily; the canonical names `Scale`, `RenderMode`, `PyoPrecision` are re-exported from `phonon/__init__.py`. The `voice.py` and `binding.py` stubs host the `Role` and `Mode` enums respectively (because §17 places them there) — their substantive types come online in later phases. Tests live at `tests/` (not `phonon/tests/`); CI lives at `.github/workflows/ci.yml`.

## Complexity Tracking

> *Empty — all Constitution Check gates PASS. No deviations from any principle, so no justifications are required. The Phase 0 surface is intentionally narrow precisely to avoid forcing any constitutional trade-off.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)*  | *(none)*   | *(none)*                             |
