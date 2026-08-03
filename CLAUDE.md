# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Phonon is a Python composition framework for experimental electronic music — continuous parametric processes whose discrete consequences emerge from threshold crossings. **Phase 0 complete (skeleton + validator + `describe` + test substrate + CI) as of 2026-05-01**: the `phonon` package installs editably, an empty `Score` validates and `describe()`s itself, the seeded RNG hierarchy `derive(seed, kind, name)` produces bit-identical output across runs, the `manual_server` pytest fixture and Pyo-Appendix-C audit are wired up, and the four-platform GitHub Actions matrix builds vendored Pyo from source. The next milestone is Phase 1 — the process primitive layer over `pyo.Thresh` and `pyo.SampHold`, plus seeded surrogates for noise, plus the offline scheduler driving `Server.process()` per block.

The design specification at `context/phonon-v1.md` is the authoritative source for type names, constructor signatures, semantics, and aesthetic refusals. Read it before proposing any framework code.

## Repository layout

- `context/phonon-v1.md` — v1.1 design specification, ~2000 lines. §1–2 and §21 are aesthetic commitments (load-bearing — refusals are creative choices, not omissions to fill in). §6, §14, §19 contain the implementation contract. Appendix C is the verified Pyo class reference (the canonical map between Phonon abstractions and Pyo classes). Appendix D is the source-vendoring policy.
- `context/threshold_study_1.py` — the canonical first piece written against the design. **It imports from a `phonon` package that does not yet exist; Pyright "Import 'phonon' could not be resolved" is expected and intentional.** Do not "fix" the import; this file is the Phase 2 integration-test target.
- `pyo-src/` — vendored Pyo 1.0.6 source. Patches land as commits affecting these files (no runtime monkey-patching). The vendored copy has its own `pyo-src/CLAUDE.md` documenting Pyo's C engine, build flags, and tests; consult it when making Pyo modifications.
- `.specify/` — GitHub Spec Kit scaffolding (templates, scripts, workflow registry). The constitution at `.specify/memory/constitution.md` is still template placeholder; the Phase 0 task is to author it from §1, §2, §14.1, and §21 of the design spec.
- `.claude/skills/speckit-*` — Spec Kit skills accessed via the Skill tool.
- `context/` is deliberately outside any Python package so design artifacts do not pollute the runtime path once `phonon/` exists.

## Three contracts that override defaults

These findings from the Pyo source audit (2026-04-28) shape the entire architecture and recur whenever an implementation question arises. They contradict naive assumptions about Pyo and should not be relitigated:

1. **Pyo has no separate control rate.** Every `PyoObject` runs at audio rate; `Sig`, `SigTo`, `Linseg` are all audio-rate envelope objects. Phonon's "control rate" (default 200 Hz) is a scheduler cadence at which the framework writes new values into Pyo `Sig`/`SigTo` slots. Block latency for parameter updates is `max(control_period, audio_block)`.
2. **Pyo's stock random objects are not bit-exact reproducible.** A single process-global LCG is mutated per-sample by every random object; `Server.setGlobalSeed()` only seeds at object construction. Phonon defaults to seeded surrogates: numpy seeded RNG → `DataTable` → `TableRead(loop=True)` for noise; numpy at control rate for trajectory `brown`/`pink`. Pyo's `Noise`/`PinkNoise`/`BrownNoise`/`Randi`/`Randh`/`Choice`/`Xnoise`/`LogiMap` are exposed via `phonon.pyo_compat.*` for live-mode only and emit validation warnings if used in deterministic paths.
3. **`Server(audio="manual")` + `Server.process()` is the deterministic-render primitive.** Single-threaded, pumped block-by-block by Phonon's scheduler. `audio="offline"` loses external pumping control; `audio="offline_nb"` spawns a worker thread (forbidden in deterministic paths). Pyo's own pytest fixture uses `Server(sr=48000, buffersize=512, audio="manual")`.

## Reproducibility contract

Bit-exact audio reproducibility (offline mode only) requires pinning `(seed, gesture_timeline, sample_rate, buffer_size, control_hz, pyo_precision)`. Default render contract: 48000 / 256 / 200 Hz / single precision. Single (`pyo._pyo`) and double (`pyo._pyo64`) produce different bit-exact outputs.

Additional invariants the renderer enforces: `PYO_SERVER_AUDIO`/`PYO_SERVER_MIDI`/`PYO_SERVER_WINHOST` env vars cleared at Server construction; `Server.setGlobalSeed(seed)` called immediately after boot; single-threaded scheduler; no wall-clock time access in piece logic (only piece time, sample-counter-derived offline).

## Naming and imports

- Pyo exports a `Score` class (`pyo.lib.pattern.Score`) that collides with Phonon's central type. **Phonon never does `from pyo import *`** in framework code or example pieces; all Pyo references are qualified.
- Composers writing pieces use `from phonon import *`. Escape-hatch imports of Pyo objects (rare) are explicit.
- Pyo precision is selected at import time: plain `import pyo` is single, `import pyo64 as pyo` is double. Pyo cannot have both extensions live in one process.

## Licensing

Phonon's own source is **MIT** (`LICENSE` at repo root). The vendored Pyo at `pyo-src/` retains its upstream **LGPLv3+** license (`pyo-src/LICENSE`). Source-only distribution (the default — `pip install` from git) does not trigger Pyo's LGPL relink obligation because Pyo is built locally from source. Distributing built artifacts that bundle compiled Pyo binaries (wheels, frozen apps, Docker images with `_pyo.so`/`_pyo64.so` baked in) does trigger the relink obligation; see the `LICENSE` file for the boundary. New Phonon source files do not need a license header (the root `LICENSE` covers them).

## Workflow

This project uses GitHub Spec Kit for planning (constitution → specs → plans → tasks → implementation). The constitution is the next deliverable; nothing should be implemented before it is ratified. Spec Kit skills are invoked via the Skill tool (`speckit-constitution`, `speckit-specify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`, `speckit-clarify`, `speckit-analyze`).

The companion `phonon-claude` plugin is a parallel deliverable, not a follow-on — its skill, modes (scholar/scribe/analyst), slash commands, hooks, and subagents are designed alongside the library. See spec §20.

## Commands

The Phonon Python package does not yet exist. Until Phase 0 lands, the only buildable artifact is vendored Pyo:

```bash
# Build vendored Pyo (single precision)
pip install -e ./pyo-src/

# Build with double-precision extension (adds pyo._pyo64)
cd pyo-src && python -m pip install -e . --config-setting="--build-option=--use-double"

# Run Pyo's own test suite (Server(audio="manual") fixture, no real audio device)
cd pyo-src/tests/pytests && pytest
pytest test_baseObjects.py::TestPyoBaseObject::test_PyoObjectBase   # single test
```

Native dependencies (macOS via Homebrew):

```bash
brew install portaudio portmidi libsndfile liblo libogg libvorbis flac opus mpg123 lame
```

When Phonon's CLI exists (Phase 4), the user-facing commands will be `phonon render`, `phonon describe`, `phonon validate`, `phonon package`, `phonon repro`, `phonon midi-list`, `phonon osc-listen`, `phonon hash`. None of these are implemented yet.

<!-- SPECKIT START -->
## Active Spec Kit work

- **Constitution**: `.specify/memory/constitution.md` v1.0.0 (ratified 2026-04-28)
- **Active feature**: `specs/001-phase-0-skeleton/` — Phase 0 Skeleton (validator, describe, test infra, CI)
  - Spec: `specs/001-phase-0-skeleton/spec.md`
  - Plan: `specs/001-phase-0-skeleton/plan.md`
  - Research: `specs/001-phase-0-skeleton/research.md`
  - Data model: `specs/001-phase-0-skeleton/data-model.md`
  - Contracts: `specs/001-phase-0-skeleton/contracts/{score-api,seedseq-api,manual-server-fixture}.md`
  - Quickstart: `specs/001-phase-0-skeleton/quickstart.md`

When working on Phase 0 implementation, read `plan.md` first for the structure decision and then the specific contract for the surface you're touching.
<!-- SPECKIT END -->
