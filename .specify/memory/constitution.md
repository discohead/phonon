<!--
SYNC IMPACT REPORT — 2026-04-28
================================
Version change: template (uninitialized) → 1.0.0
Bump rationale: Initial ratification of the Phonon constitution. No prior
principles to break, so a single MAJOR-equivalent baseline.

Modified principles:
  • (none — first version)
Added principles (all new):
  I.   Aesthetic Refusals Are Load-Bearing
  II.  Bit-Exact Reproducibility (Offline)
  III. Process-First, Threshold-Driven
  IV.  Roads' Multiscale Time Is Canonical
  V.   Agent-Readiness Is The Primary API Driver
  VI.  Vendored Pyo, Patches As Commits
  VII. The Piece File Is The Composition

Added sections:
  • Render Contract (formerly placeholder Section 2)
  • Development Workflow (formerly placeholder Section 3)
  • Governance (filled out)

Removed sections:
  • All [PLACEHOLDER] tokens replaced.

Templates requiring updates:
  ✅ .specify/templates/plan-template.md   — Constitution Check section rewritten with the 7 principle gates
  ⚠ .specify/templates/spec-template.md    — generic; no principle-specific changes required (verified)
  ⚠ .specify/templates/tasks-template.md   — generic; no principle-specific changes required (verified)
  ⚠ CLAUDE.md                              — already aligned (root CLAUDE.md was rewritten 2026-04-28 to encode the same commitments)
  ⚠ pyo-src/CLAUDE.md                      — vendored upstream guidance; no Phonon-side changes needed

Follow-up TODOs:
  • None. All principles derive from the v1.1 design specification at
    context/phonon-v1.md; no placeholders deferred.
-->

# Phonon Constitution

Phonon is a Python composition framework for experimental electronic music — continuous parametric processes whose discrete consequences emerge from threshold conditions in the medium. This constitution captures the immutable commitments that override every downstream design and implementation decision. The v1.1 design specification at `context/phonon-v1.md` is the authoritative elaboration of these commitments; this document is the smallest set of rules that may not be relaxed without amendment.

## Core Principles

### I. Aesthetic Refusals Are Load-Bearing

Phonon's non-goals (design spec §21) are creative commitments, not omissions to be filled in under feature pressure. The framework MUST refuse: song-form scaffolding (verse/chorus/bridge primitives), diatonic or key-signature helpers, MIDI-file authoring, fixed-channel "tracks", event-list authoring APIs, psychoacoustic modeling or perceptual weighting, automatic loudness normalization or mastering, undo/redo machinery, GUIs over the core, and live-coding-style hot-swap of individual entities. Live hot-reload of whole piece files is permitted; in-flight surgical mutation of running pieces is not.

Adding any of these capabilities — at any layer of the framework or its plugin — requires a constitutional amendment with explicit rationale. The default answer to "should we add X to make this easier?" is "no, that is the point."

**Rationale**: The framework is shaped to be excellent at the music of Roads, Fell, Ikeda, Alva Noto, Radigue, Hennix, Kayn, and Autechre. Each refusal removes a path that would soften the framework into something else. Refusals are the discipline that hardware previously imposed on the composer; relaxing them dilutes the work.

### II. Bit-Exact Reproducibility (Offline)

Given the same `(piece source, seed, gesture timeline, sample_rate, buffer_size, control_hz, pyo_precision)`, an offline render MUST produce bit-identical audio. This is non-negotiable for the AUTOPILOT and REPLAY render modes. LIVE mode is exempt; reproducibility is impossible against real-time controllers and audio backends and Phonon does not pretend otherwise.

The framework MUST: route every stochastic decision through a per-entity `numpy.random.Generator` derived from the Score seed via `numpy.random.SeedSequence`; provide seeded surrogates for any non-deterministic Pyo objects it depends on (noise, randoms, granular density); pin `(sample_rate, buffer_size, control_hz, pyo_precision)` in every release artifact; clear `PYO_SERVER_AUDIO`/`PYO_SERVER_MIDI`/`PYO_SERVER_WINHOST` at Server construction; call `Server.setGlobalSeed(seed)` at boot; run the scheduler single-threaded; and forbid wall-clock time access in piece logic.

The framework MUST NOT use Pyo's stock `Noise`, `PinkNoise`, `BrownNoise`, `Randi`, `Randh`, `Choice`, `Xnoise`, `LogiMap`, `RandInt`, `RandDur`, `XnoiseDur`, `Urn`, or `PadSynthTable` in deterministic code paths. These are exposed under `phonon.pyo_compat.*` for live-mode use only and MUST emit a Score validation warning if present in a Score intended for archival.

The test suite MUST include a bit-exact reproducibility test (render → hash → render → hash → assert equal) and a differential test (vary `control_hz` at otherwise identical settings → assert outputs differ).

**Rationale**: A piece file is the composition. The same source must produce the same sound on any machine, indefinitely, or the source is not the composition. Bit-exactness is also the foundation of the seed-modification ritual: a different seed produces a recognizable variant precisely because the exact same algorithm ran with different randomness.

### III. Process-First, Threshold-Driven

A piece is a system of continuous parametric processes. All discrete musical consequences — rhythm, melody, structural events, voice introductions, recurrences — MUST emerge from threshold crossings on continuous signals. The framework MUST NOT expose event-list authoring at any layer: no timed-event arrays, no note-list APIs, no step sequencers as first-class composition primitives.

Threshold crossings, sample-and-hold, and probabilistic firing within crossing-eligible regions are the only mechanisms by which continuous flow becomes discrete event. Helpers that *generate* clock-like processes (`Metro`, `Beat`, `Euclide` wrappers) are permitted; helpers that *author* fixed event lists are not.

**Rationale**: This is the framework's metaphysics in miniature — the phonon's wave-particle duality. A composer who reaches for a step list has stopped composing inside the framework's grain. The discipline of routing every event through a continuous signal is the source of the perceptual phenomenon the composer chases.

### IV. Roads' Multiscale Time Is Canonical

Curtis Roads' five time scales — `Scale.SAMPLE`, `Scale.MICRO`, `Scale.MESO`, `Scale.MACRO`, `Scale.SUPRA` — MUST be first-class citizens of the type system. Every `Trajectory` MUST declare its scale; the validator MUST enforce scale-asymmetric composition (lower-scale trajectories MAY be `reshape_by` or `drift_toward` higher-scale trajectories, never the reverse); scale-default variance MUST flow downward through `Score.variance_defaults`.

The five-scale model may not be replaced, renumbered, or supplemented with non-Roads scales without amendment.

**Rationale**: Roads' multiscale claim — that musical phenomena at different scales are asymmetrically nested, with macro shapes legitimately reshaping meso behavior but not vice versa — is the structural skeleton on which trajectory composition rests. Allowing upward composition produces ill-posed feedback loops and dissolves the form.

### V. Agent-Readiness Is The Primary API Driver

The public API MUST be designed for authoring by Claude Code first and reading by humans second, on the working hypothesis that what is good for an agent is also good for a human reading code months later. Concretely:

- Entities MUST be referenced by string name via `Reference("name")`, not by Python object identity, so that Score fragments can be authored independently and dependency graphs are statically analyzable.
- The Score MUST be a declarative value, not a sequence of imperative construction calls.
- `Score.describe()` MUST return a structured summary derivable from the static graph alone, without executing the piece.
- Every public type MUST have stable, semantic names; renames are MAJOR-version events for Phonon itself.
- Closed action sets (e.g., the six v1 structural-event actions) MUST be implemented as Protocols using only the public Score-mutation API, so user-defined extensions slot in identically; "closed" is a documentation choice, not a sealed-type prison.

**Rationale**: The framework's value proposition is that an agent can produce volumes of work the composer alone cannot. Optimizing the API for agent ergonomics — declarative, name-referenced, statically analyzable — is the lever. Verbosity costs from explicit `Reference("...")` are accepted in exchange for graph analyzability.

### VI. Vendored Pyo, Patches As Commits

Pyo is vendored at `pyo-src/` and treated as a maintained subproject of the Phonon repository. Modifications to Pyo MUST land as commits affecting `pyo-src/` files; runtime monkey-patching of Pyo from Phonon code is forbidden. Phonon code MUST NOT execute `from pyo import *` (the `pyo.lib.pattern.Score` class collides with Phonon's central type); all Pyo references MUST be qualified.

Pyo precision (single `pyo._pyo` vs double `pyo._pyo64`) is selected at import time per process; the choice is part of the reproducibility contract. The `pyo.lib.events` module's `Events`/`EventScale`/etc. MUST NOT be used (they would import event-list authoring through the back door, violating Principle III).

The `tests/test_pyo_audit.py` audit test MUST verify, on every CI run, that every Pyo class Phonon depends on (Appendix C of the design spec) is importable with the expected constructor signature. A bumped vendored Pyo that fails this test fails CI.

**Rationale**: Vendoring gives Phonon source-level control over a substrate whose upstream development is effectively frozen, lets Phonon patch Pyo's RNG isolation or add custom externals (chaotic integrators) without forking publicly, and pins exact behavior per Phonon commit. The audit test guards against silent regression when the vendored copy is bumped.

### VII. The Piece File Is The Composition

A piece is one Python file. Diffs of the file are diffs of the composition. There is no sidecar metadata file, no per-piece database, no project-state directory beyond the release-artifact format defined in design spec §16.3. The framework MUST NOT introduce any persistence mechanism that lets a piece's identity drift from its source code.

Git is the undo. The release artifact (piece source + corpus manifest + version pins + per-performance subdirectories) is the only sanctioned persisted form.

A composer's interaction with their own piece is: edit, save, render. A listener's interaction is: clone, build, run. Neither involves a tool that writes to the piece outside the composer's editor.

**Rationale**: This guarantees the framework can be small and the piece can be reasoned about as a value. It is also the only honest way to make pieces reproducible — anything that lets state accumulate outside the source eventually drifts.

## Render Contract

Every Phonon Score declares an explicit render contract: `sample_rate`, `buffer_size`, `control_hz`, and `pyo_precision`. Defaults are 48000 Hz / 256 samples / 200 Hz / single precision. Together with the seed and gesture timeline, this contract determines bit-exact output (Principle II).

The release-artifact format (design spec §16.3) MUST include `render-contract.json` per performance, recording the contract values used. A listener re-rendering a released piece on a different machine MUST be able to reproduce the exact audio by passing the recorded contract.

The framework MUST refuse to render an autopilot or replay piece whose `pyo_precision` does not match the importable Pyo extension (`pyo._pyo` vs `pyo._pyo64`); this is a hard error, not a warning, because silently degrading precision violates Principle II.

## Development Workflow

Phonon is developed using GitHub Spec Kit (`speckit-constitution`, `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`, `speckit-analyze`). The pipeline is constitution → specifications → plans → tasks → implementation. No code is written before its enclosing specification has been ratified through `/speckit-specify` and its plan generated through `/speckit-plan`.

Every implementation phase ends in a runnable, testable artifact (design spec §22). Phase 2 specifically MUST end with `context/threshold_study_1.py` rendering end-to-end in autopilot mode and the bit-exact reproducibility test passing on it. This piece is the framework's first integration test and MUST remain runnable through every subsequent phase.

The companion `phonon-claude` Claude Code plugin (design spec §20) is a parallel deliverable, not a follow-on. Its skill, scholar/scribe/analyst modes, slash commands, hooks, and subagents are designed alongside the library and ship in Phase 4.

The vendored Pyo at `pyo-src/` is built with `pip install -e ./pyo-src/`. CI matrix MUST build Pyo from source on macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest, run the Pyo audit test (`tests/test_pyo_audit.py`) first, and only then run the rest of the Phonon test suite.

## Governance

This constitution supersedes all other practices. Any plan, specification, task, or implementation that conflicts with a principle MUST either resolve the conflict or amend the constitution. There is no third option.

**Amendment procedure**: Amendments are made by re-running `/speckit-constitution` with the proposed change in the user input, which (a) updates this document, (b) bumps the version per the rules below, (c) propagates the change through dependent templates, and (d) writes a Sync Impact Report at the top of this file. Amendments MUST cite which principle is being modified, why, and what downstream artifacts require updates.

**Versioning policy** — `MAJOR.MINOR.PATCH`:

- **MAJOR**: backward-incompatible governance or principle removal/redefinition. Renaming a Principle is MAJOR.
- **MINOR**: new principle added or existing principle materially expanded.
- **PATCH**: clarifying language, typo fixes, non-semantic refinement.

**Compliance review**: Every `/speckit-plan` invocation MUST run a Constitution Check gate before research begins and re-run it after design. Violations MUST be either resolved or recorded in the plan's Complexity Tracking section with explicit justification ("simpler alternative rejected because…"). Unjustified violations block plan completion.

**Runtime guidance**: `CLAUDE.md` at the repository root encodes day-to-day operational guidance for Claude Code. It is not part of this constitution and may evolve freely; it must, however, remain consistent with the principles here.

**Version**: 1.0.0 | **Ratified**: 2026-04-28 | **Last Amended**: 2026-04-28
