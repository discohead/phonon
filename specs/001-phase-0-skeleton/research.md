# Research: Phase 0 — Skeleton

This document resolves the implementation-choice unknowns surfaced while filling `plan.md`'s Technical Context. Each section follows the same structure: **Decision** (what was chosen), **Rationale** (why), **Alternatives considered** (what else was evaluated and why rejected). The spec at `spec.md` is technology-agnostic; this file is where the technology choices are nailed down so `data-model.md`, `contracts/`, and `tasks.md` can rely on them.

## R-001 — Deterministic seeded RNG hierarchy: `derive(seed, kind, name)`

**Decision**: Implement `derive` as

```python
import hashlib
import numpy as np

def derive(seed: int, kind: str, name: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{kind}\x1f{name}".encode("utf-8")).digest()
    spawn_int = int.from_bytes(digest[:16], "big")
    ss = np.random.SeedSequence(entropy=[seed, spawn_int])
    return np.random.default_rng(ss)
```

**Rationale**:

- `numpy.random.SeedSequence` is the official mechanism for deterministic Generator construction; the docs guarantee that the same `entropy` sequence produces the same Generator state across runs and across platforms (numpy hashes the entropy with a SipHash-derived stretch and spawns PCG64 from it).
- `hashlib.sha256` is bit-identical across CPython versions and OSes — unlike Python's built-in `hash()`, which is per-process-randomized when `PYTHONHASHSEED` is unset (the default since Python 3.3 for security against hash-DoS attacks).
- The unit-separator byte `\x1f` between `kind` and `name` makes the encoding injective: `("traj", "ab")` and `("traja", "b")` produce different digests. Without a separator, those two would collide.
- 128 bits of digest material as `spawn_int` is overkill — `SeedSequence` will whiten it back down to its internal 32-bit pool. Using 16 bytes (vs 8) is free and gives extra head-room if someone bumps to a stronger seed structure later.
- `np.random.default_rng(seq)` returns a PCG64-backed `Generator`; its byte-for-byte output is documented stable across numpy versions for the same `SeedSequence` (per numpy's NEP 19 commitment).

**Alternatives considered**:

- *Python's built-in `hash(kind, name)` for `spawn_key`*: rejected — randomized per process via `PYTHONHASHSEED` unless explicitly set. Setting `PYTHONHASHSEED=0` in CI would break the cross-CI ↔ local-dev determinism contract.
- *MD5 instead of SHA-256*: smaller digest, no security need, but no real upside — both are deterministic; SHA-256 is the modern default and same speed for short inputs.
- *Per-entity counter integers instead of name-derived digests*: would require maintaining a global counter at Score-construction time, which is fragile under refactor (renaming a trajectory should change *its* RNG without touching anyone else's; counters don't preserve that property).
- *`SeedSequence(entropy=seed, spawn_key=(int1, int2))`*: works but `spawn_key` is officially an internal detail of SeedSequence's tree-spawning behavior; mixing it into `entropy=[seed, spawn_int]` is the documented composition pattern.

## R-002 — Score is a frozen dataclass with eager validation in `__post_init__`

**Decision**: `Score` is `@dataclass(frozen=True, kw_only=True, slots=True)`. Validation runs in `__post_init__`. `Score.describe()` is a regular method.

**Rationale**:

- Constitution V calls for declarative, statically-analyzable values. A frozen dataclass *is* a declarative value — there's no setter surface to misuse.
- `kw_only=True` matches the "all named fields" call style in `threshold_study_1.py` (Appendix A) and prevents positional-arg foot-guns when fields are reordered or extended.
- `slots=True` shrinks the per-instance footprint and forbids accidental attribute assignment, reinforcing immutability.
- `__post_init__` is the canonical place for invariant validation in a dataclass; it runs after all fields are set and before the instance is returned to the caller, so `ScoreValidationError` raised from there appears at the constructor call site exactly as the spec acceptance scenarios describe.
- A `Score.warnings: list[str]` field is added with `default_factory=list`. The constructor mutates `warnings` *during validation* (allowed despite `frozen=True` because `list` is mutable internally — only attribute reassignment is forbidden). To stay disciplined we keep all mutation localized to `__post_init__` and surface warnings via `describe()`.

**Alternatives considered**:

- *Pydantic v2*: powerful but heavyweight (extra dependency) and its validator decorators encourage scattered validation logic. Phase 0's invariants are simple and best read in one block.
- *Hand-rolled `__init__`*: more code, equivalent power; loses the dataclass auto-generated `__repr__`, `__eq__`, and field iteration that `describe()` benefits from.
- *`attrs`*: similar to dataclass; rejected for the same dependency reason as Pydantic.
- *Mutable Score with a separate `validate()` call*: violates the constitutional preference for declarative values and would let invalid Scores escape into render time.

## R-003 — Snapshot test harness: in-tree, no third-party library

**Decision**: Implement snapshot comparison as a small in-tree helper in `tests/snapshots/_snapshot.py` (or inline in the test file): `assert_snapshot(actual: dict, snapshot_path: Path)` that reads the snapshot from disk, parses it as YAML, and asserts equality with `actual`. Updating the snapshot is a manual `pytest --update-snapshots`-style flag handled by an env var (`PHONON_UPDATE_SNAPSHOTS=1`) that the helper reads.

**Rationale**:

- Adds zero new dependencies. `syrupy` and `pytest-snapshot` are mature but bring their own DSLs and config surface that we don't need for a single snapshot.
- The snapshot is YAML (not pickle or JSON) so it diffs cleanly in PR review and a human can regenerate it by inspection.
- Wrap the env-var update path in a `pytest` warning when set so it never silently slips into a CI run.

**Alternatives considered**:

- *`syrupy`*: nice library, but for a single snapshot test it's overkill and the indirection (custom serializers) hurts more than it helps.
- *`pytest-regressions`*: similar; defers regeneration to a CLI flag. Same overkill argument.
- *No snapshot, raw assertions on dict keys*: brittle as the schema grows. Phase 1+ describe() output will be richer; a snapshot catches schema drift cheaply.

## R-004 — Sample-rate whitelist for Score validation

**Decision**: `phonon.score` enumerates the supported rates as `{44100, 48000, 88200, 96000, 176400, 192000}` and validates `Score.sample_rate` against this set. Rates outside this set raise `ScoreValidationError` even though Pyo would accept them.

**Rationale**:

- This is a **Phonon** render-contract whitelist, not a Pyo limitation. Pyo's `Server.setSamplingRate` C-side accepts any integer "supported by the sound card" — for `audio="manual"` there's no card, so it accepts arbitrary ints.
- The whitelist captures rates a listener is plausibly able to reproduce: integer multiples of 44.1 kHz (CD heritage) and 48 kHz (digital video / pro audio heritage). Rates like 22050 or 32000 are technically valid in Pyo but rare on contemporary hardware and would silently change the audible result of a piece if a listener "fixed" them.
- Phonon's reproducibility contract pins `sample_rate`. Rejecting weird rates at construction time is cheaper than discovering them at render time.

**Alternatives considered**:

- *Accept any positive int*: passes more validation but punts the constraint to render time and undermines the "render contract is enforceable" promise.
- *Accept only `{44100, 48000}` (two-rate gate)*: safest but unnecessarily restrictive; high-rate work (96k for hyper-precise grain timing) is a legitimate Roads-shaped use case.
- *Defer to vendored Pyo's accepted set*: Pyo doesn't expose a whitelist; querying the sound-card-supported rates is platform-specific runtime probing, useless at offline-render time.

## R-005 — macOS x86_64 GitHub Actions runner label

**Decision**: Use `macos-13` for the x86_64 leg of the matrix and `macos-14` for arm64. `macos-latest` aliases to arm64 (since 2024) so we use the explicit version labels to keep the matrix self-documenting.

**Rationale**:

- `macos-12` was the last GitHub-provided x86_64 runner that Pyo's Homebrew bottle ecosystem cleanly supports; it was deprecated in late 2024.
- `macos-13` is x86_64 (Intel) and is GitHub's only currently-supported x86_64 macOS runner. It's still available as of 2026-04-29 per GitHub's runner deprecation calendar.
- `macos-14` and `macos-15` are arm64 (Apple Silicon). `macos-latest` follows arm64.
- If GitHub deprecates `macos-13` (Intel macOS is on borrowed time), the workflow's `macos-x86_64` leg will need to be marked `continue-on-error` or removed — this is foreseen in spec FR-039 and Edge Cases.

**Alternatives considered**:

- *Skip macOS x86_64 entirely*: rejected — Constitution § Development Workflow mandates the four-platform matrix. Skipping requires an amendment.
- *`macos-latest` for both legs*: rejected — we lose architecture coverage and the matrix becomes meaningless.
- *Self-hosted x86_64 runner*: rejected — adds infrastructure burden disproportionate to Phase 0. If GitHub kills `macos-13`, revisit.

## R-006 — Windows CI native dependencies: vcpkg via Pyo's `scripts/win/`

**Decision**: The Windows CI job uses Pyo's vendored `scripts/win/` setup script to install portaudio, portmidi, libsndfile, liblo, libogg, libvorbis, flac, and opus via vcpkg + MSYS2 mingw64 (per design spec §19.5). The script is invoked from the workflow as a single setup step.

**Rationale**:

- Pyo upstream ships an inspection/setup script at `pyo-src/scripts/win/` specifically for Windows builds against MSYS2 mingw64. Reusing it tracks Pyo's upstream guidance and avoids us inventing a parallel install path that would need re-validation when the vendored Pyo is bumped.
- vcpkg + MSYS2 is the documented Pyo-on-Windows path. Alternatives (precompiled wheels, conda) sidestep the from-source build that Constitution VI's vendoring policy depends on.

**Alternatives considered**:

- *Conda environment on Windows*: works but introduces a non-pip toolchain just for Windows, fragmenting the install story. Rejected.
- *Precompiled portaudio/portmidi wheels (e.g., from Christoph Gohlke's archive)*: rejected — closes the source-build gate Constitution VI requires.
- *Skip Windows in Phase 0*: blocked by constitution.

The Windows leg is the highest-risk piece of Phase 0 CI; if its setup proves unreliable, we set `continue-on-error: true` for that leg and open a follow-up tasks.md item to harden it (rather than blocking Phase 0 merge).

## R-007 — Hypothesis dependency stance for Phase 0

**Decision**: `hypothesis` is in `[project.optional-dependencies].dev` from Phase 0. Phase 0 tests do not require it. Phase 1+ trajectory composition tests (per design spec §19.4) will use it without amending `pyproject.toml`.

**Rationale**:

- Adding a dependency once and leaving it unused for a phase is cheaper than amending the manifest twice.
- The dev-extras pattern is standard Python and well-understood: `pip install -e .[dev]` pulls Hypothesis along with pytest.
- Phase 0's positive-and-negative validation tests are structurally simple and don't benefit from property-based testing; saving Hypothesis for trajectory composition (where the input space is genuinely combinatorial) avoids "Hypothesis everywhere" anti-pattern.

**Alternatives considered**:

- *Defer Hypothesis until Phase 2*: trivial pyproject diff later; chosen against because Phase 0 is the moment we're touching pyproject.toml anyway.
- *Make Hypothesis a runtime dep*: rejected — composers don't need it.

## R-008 — Type-checker stance

**Decision**: Phonon ships with type hints throughout but does not run a type-checker in Phase 0 CI. `mypy` and `pyright` are *not* added to dev extras in Phase 0. Phase 4 reconsiders adding `mypy --strict` to CI.

**Rationale**:

- Pyo (the vendored substrate) lacks comprehensive type stubs. Type-checking Phonon-against-Pyo would produce a wall of `Any` warnings that obscure real Phonon-side regressions.
- The composer's workflow is editor-driven (Claude Code + LSP). Type hints in source benefit them via the editor; CI gating on type-checker output adds setup cost without proportional value at Phase 0.
- Constitution V (Agent-Readiness) is served by the *presence* of type hints in source, which Phase 0 commits to.

**Alternatives considered**:

- *`mypy --strict` in CI from day one*: blocked by Pyo's stub coverage; would force ignore-flags everywhere.
- *`pyright` with relaxed settings*: same problem, lighter pain. Defer to Phase 4 when the public API is mostly stable.

## R-009 — License header policy for new Python files

**Decision**: New Python files in `phonon/` carry no per-file license header. The repo-root `LICENSE` (MIT for Phonon source) covers them. Vendored Pyo files at `pyo-src/` retain their upstream LGPLv3+ headers.

**Rationale**:

- The repo-root `LICENSE` already documents this boundary per the existing `CLAUDE.md` § Licensing. Re-stating it per-file adds noise without improving licensing clarity.
- Per-file headers proliferate diff churn during refactors and are commonly skipped by modern Python projects (numpy, FastAPI, etc.).

**Alternatives considered**:

- *MIT header on every new file*: noisy; redundant with `LICENSE`.
- *SPDX-License-Identifier comment*: legitimate convention but not required and not currently used in the Phonon repo.

## R-010 — `__init__.py` export surface for Phase 0

**Decision**: `phonon/__init__.py` exports exactly:

```python
from phonon.score import Score, ScoreValidationError
from phonon._scale import Scale
from phonon._render_mode import RenderMode, PyoPrecision
from phonon.binding import Mode
from phonon.voice import Role
from phonon.seedseq import derive
from phonon.version import __version__

__all__ = [
    "Score", "ScoreValidationError",
    "Scale", "RenderMode", "PyoPrecision", "Mode", "Role",
    "derive", "__version__",
]
```

Names whose *implementations* are not functional in Phase 0 (`Voice`, `Trajectory`, `Coupling`, `Binding`, `Reference`, `Event`, `Crossing`, `Gesture`, `Midi`, `Osc`, all the rhetoric primitives, all the process generators, all the shape factories) are NOT re-exported by `phonon/__init__.py`. They appear in their respective modules as docstring stubs without classes.

**Rationale**:

- Spec FR-008: "the public surface grows phase-by-phase." A composer importing `from phonon import Voice` in Phase 0 should get a clean ImportError, not a half-baked stub.
- `threshold_study_1.py` (Appendix A) intentionally fails to fully resolve in Phase 0; CLAUDE.md notes this explicitly. Phase 2 brings Voice; Phase 3 brings Event/Gesture; etc.
- The five enums (`Scale`, `RenderMode`, `PyoPrecision`, `Mode`, `Role`) are re-exported even though some of them are referenced by types not yet implemented (`Mode` is for `Binding`; `Role` is for `Voice`). They are pure data and adding them now is harmless and lets Phase 1 specs reference them by canonical name.

**Alternatives considered**:

- *Export everything from §18, with stubs raising `NotImplementedError` on instantiation*: bait-and-switch; agents would generate code that imports successfully but breaks at construction. Worse signal than an ImportError.
- *Export only `Score`*: too narrow; the enums are useful even at Phase 0 (variance_defaults uses `Scale`).

## R-011 — Pyo audit test scope: full Appendix C, not just Phase 0 dependencies

**Decision**: `tests/test_pyo_audit.py` audits **every class** listed in design spec Appendix C, regardless of whether Phase 0 imports it. It also audits `Server`'s method surface (FR-033) and the audio-mode constant set (FR-034).

**Rationale**:

- Constitution VI explicitly requires the audit to cover "every Pyo class Phonon depends on (Appendix C of the design spec)." Phonon's design depends on the whole Appendix C set across phases; Phase 0 just happens to be the time the audit lands.
- Catching upstream signature drift early (when Pyo hasn't shipped a new release in a year) is cheap insurance for the entire Phase 1+ runway.
- Each audited class is one `inspect.signature` introspection — the audit is fast (single-digit seconds).

**Alternatives considered**:

- *Audit only classes Phase 0 imports* (basically just `Server`): rejected — defeats Constitution VI's purpose. Phase 1 would have to re-do the audit for the classes it pulls in.
- *Audit only required parameters, ignore optional ones*: implemented as a fallback for forward compatibility (Phonon-internal Pyo extensions per §23.8/23.9 may add optional parameters), but the default audit includes all parameters and reports mismatches.

## Cross-references

- Constitution: `.specify/memory/constitution.md` v1.0.0 (Principles II, V, VI especially).
- Design spec: `context/phonon-v1.md` §15 (Score), §17 (module layout), §18 (public API), §19 (implementation notes), §22 (phased plan), Appendix C (Pyo class reference), Appendix D (vendoring policy).
- Vendored Pyo: `pyo-src/pyproject.toml` (Python floor 3.9–3.13); `pyo-src/pyo/lib/server.py` (Server constructor + `PYO_SERVER_*` env-var fallback at lines ~684–774).
