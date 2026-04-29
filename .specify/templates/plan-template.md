# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Source: `.specify/memory/constitution.md` (Phonon Constitution v1.0.0). Each gate
below maps to one principle. A "PASS" requires either (a) the feature complies,
or (b) a justified entry in the Complexity Tracking section.

- **I. Aesthetic Refusals Are Load-Bearing** — Does the feature add anything from
  the §21 refusal list (song-form scaffolding, diatonic helpers, MIDI-file
  authoring, fixed-channel tracks, event-list authoring, psychoacoustic shaping,
  loudness normalization, undo/redo, GUIs over the core, in-flight hot-swap)? If
  yes, this is a constitutional amendment, not a feature. Stop and re-run
  `/speckit-constitution` first.
- **II. Bit-Exact Reproducibility (Offline)** — If the feature touches randomness,
  audio rendering, or Pyo objects: does it route every stochastic decision
  through a per-entity `numpy.random.Generator`? Does it use `phonon.pyo_compat.*`
  Pyo randoms only in live-mode code paths? Does it preserve the pinned render
  contract `(sr, buffer, control_hz, pyo_precision)`?
- **III. Process-First, Threshold-Driven** — Does any new event arise from a
  threshold crossing on a continuous signal? If the feature exposes a way to
  author timed events directly (lists, arrays, schedules), this is a violation.
- **IV. Roads' Multiscale Time Is Canonical** — If the feature involves
  Trajectories or temporal structure, does it use the existing five `Scale`
  values? Does it respect scale-asymmetric composition (lower scales reshapeable
  by higher; never reverse)?
- **V. Agent-Readiness Is The Primary API Driver** — Are new entities referenced
  by string name? Is the new surface declarative (data, not imperative
  construction)? Is `Score.describe()` extended to summarize the new surface
  without execution?
- **VI. Vendored Pyo, Patches As Commits** — If the feature requires Pyo changes,
  do they land as commits to `pyo-src/`? Does it avoid `from pyo import *`? Does
  it avoid `pyo.lib.events` and `pyo.lib.pattern.Score`? Does the Pyo audit test
  still pass?
- **VII. The Piece File Is The Composition** — Does the feature introduce any
  persistence outside the piece source or the §16.3 release artifact? If yes,
  this violates Principle VII unless explicitly amended.

Record any violations and their justifications below in **Complexity Tracking**.
Unjustified violations block plan completion.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
