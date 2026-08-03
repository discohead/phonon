# Feature Specification: Phase 0 — Skeleton

**Feature Branch**: `001-phase-0-skeleton`
**Created**: 2026-04-29
**Status**: Draft
**Input**: User description: "Phase 0"

Phase 0 is the first runnable, testable artifact of Phonon. It produces the Python package skeleton, the `Score` validator and `describe()` capability for empty scores, the test infrastructure (Server-manual fixture, Pyo audit test, snapshot harness), and the cross-platform CI matrix that builds vendored Pyo from source. Phase 0 does **not** render audio — that is Phase 1's milestone. It establishes the substrate Phase 1 can immediately build on.

The constitution at `.specify/memory/constitution.md` is already ratified at v1.0.0 (2026-04-28); this spec inherits its commitments and does not modify them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Empty Score validates and describes itself (Priority: P1)

A composer (or the Phonon agent) authors a minimal Phonon piece file: a `Score` with title, seed, and duration but no voices, trajectories, or other entities. The composer imports `phonon`, constructs the Score, and the framework either validates it cleanly or rejects it with a precise, named error. Calling `score.describe()` returns a structured summary the composer can read or pipe to YAML.

**Why this priority**: This is the smallest end-to-end vertical slice that exercises the whole Phase 0 substrate (package importable, validator working, describe walking the static graph). Without it, no other Phase 0 capability has a point. It is also the contract Phase 1 builds on top of — Phase 1 adds entities to Scores; the Score type itself must already work.

**Independent Test**: A test author writes `Score(title="empty", seed=1729, duration_seconds=10.0)`, asserts no exception is raised, asserts `score.describe()` returns a dict whose `title`, `seed`, `duration`, and `render_contract` keys match the input (with empty lists for `voices`, `trajectories`, etc.), and asserts `yaml.safe_dump(score.describe())` produces parseable YAML. Then asserts `Score(title="", seed=1, duration_seconds=10.0)` raises `ScoreValidationError` naming the `title` field. This passes without booting Pyo and without rendering audio.

**Acceptance Scenarios**:

1. **Given** an installed Phonon package and importable `pyo`, **When** the composer constructs `Score(title="t", seed=1, duration_seconds=1.0)`, **Then** the Score is created without exception and `score.describe()` returns a dict with `title="t"`, `seed=1`, `duration="0:01"`, empty entity lists, and a `render_contract` containing `sample_rate=48000`, `buffer_size=256`, `control_hz=200`, `pyo_precision="single"`, and a `framework_version` string.
2. **Given** a Score about to be constructed, **When** the composer passes `title=""`, **Then** `ScoreValidationError` is raised whose message names the `title` field and the value `""`.
3. **Given** a Score about to be constructed, **When** the composer passes `duration_seconds=-5`, `buffer_size=300`, or `sample_rate=22050`, **Then** `ScoreValidationError` is raised, each violation independently producing a precise message naming the offending field and value.
4. **Given** a successfully validated empty Score, **When** the composer calls `yaml.safe_dump(score.describe())`, **Then** the result parses round-trip via `yaml.safe_load` to a dict equal to the original `describe()` output.
5. **Given** a Score with `variance_defaults={Scale.SUPRA: 0.03}` (partial mapping), **When** validation runs, **Then** the Score is accepted and `describe()`'s `variance_profile` field reports `{SUPRA: 0.03}` with absent scales omitted (or zero-valued; the schema is consistent across runs).

---

### User Story 2 — Phase 1 inherits a ready test substrate (Priority: P2)

A Phase 1 implementer (composer or Claude) starts work and finds an installable dev environment, a pytest fixture that yields a booted `pyo.Server(audio="manual")` ready for offline-render tests, a Pyo audit test that has already verified Appendix C class signatures match the vendored Pyo, and a snapshot test for `Score.describe()` that catches schema regressions. They do not have to build any of this themselves.

**Why this priority**: Without this substrate, Phase 1 spends its first week rebuilding test infrastructure rather than implementing the process primitive layer. The user is the next implementer; the value is throughput.

**Independent Test**: A test author writes a new test file in `tests/` that uses the `manual_server` fixture, asserts `server.getCurrentTime() == 0` immediately after fixture entry, calls `server.process()` once, asserts `server.getCurrentTime()` advanced by exactly `buffer_size / sample_rate` seconds, and exits cleanly. Separately, the Pyo audit test runs alone (`pytest tests/test_pyo_audit.py`) and passes. Separately, the describe snapshot test runs alone and passes. None of these depends on Score-level entities being implemented.

**Acceptance Scenarios**:

1. **Given** the test suite is run via `pytest`, **When** a test requests the `manual_server` fixture, **Then** the fixture provides a `pyo.Server` whose `audio == "manual"`, `sr == 48000`, `buffersize == 256`, `nchnls == 2`, and is booted; on test teardown `Server.shutdown()` is called.
2. **Given** the fixture is constructing the Server, **When** environment variables `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, `PYO_SERVER_WINHOST` are present in the test process environment, **Then** they are cleared before `Server()` is invoked (so they cannot silently change the backend).
3. **Given** the Pyo audit test runs, **When** every class listed in design spec Appendix C is introspected, **Then** each class is importable from `pyo` and its constructor signature matches the documented signature; any mismatch produces a single failure naming the class, the expected signature, and the actual signature.
4. **Given** the `Server` audit subtest runs, **When** `Server` is introspected, **Then** all of `boot`, `start`, `stop`, `shutdown`, `process`, `recordOptions`, `setGlobalSeed`, `setCallback`, `addMidiEvent`, `getCurrentTime` are present as methods.
5. **Given** the describe-snapshot test runs, **When** an empty Score's `describe()` output is compared to the snapshot stored in the test directory, **Then** they match exactly; intentional schema changes are explicit (the developer regenerates the snapshot in a separate commit).

---

### User Story 3 — CI matrix continuously verifies the build on four platforms (Priority: P3)

A contributor opens a pull request. GitHub Actions builds vendored Pyo from source on macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest, runs the Pyo audit test first, and then runs the rest of the Phonon test suite. The contributor sees green checks before merging — or, on failure, sees exactly which platform and which test broke.

**Why this priority**: The constitution (§ Development Workflow) mandates this matrix. The framework's reproducibility promise is hollow if it only works on one platform. Without CI, regressions silently land. P3 because P1 and P2 are local-developer-observable and could ship to a single-platform demo first; CI is the formal guarantee that makes the project mergeable as a whole.

**Independent Test**: A developer pushes a commit on a feature branch; GitHub Actions runs the workflow; all four platforms report green within a budget. Separately, deliberately breaking a Pyo class signature (e.g., editing `pyo-src/pyo/lib/generators.py` to rename `Sine`'s `freq` parameter) and pushing produces a clean, named failure on the Pyo audit test on every platform; reverting restores green.

**Acceptance Scenarios**:

1. **Given** a push or pull request to any branch, **When** CI runs, **Then** the workflow matrix dispatches one job per platform (macOS-arm64, macOS-x86_64, ubuntu-latest, windows-latest), each installing native deps, building vendored Pyo, and running tests.
2. **Given** a CI job is running, **When** the test sequence begins, **Then** `tests/test_pyo_audit.py` runs first; if it fails, all subsequent test files are skipped with a single clear "Pyo audit failed; skipping remaining tests" notice.
3. **Given** a CI run completes, **When** the result is reported, **Then** failures cite the platform, the test file, the test name, and the assertion that failed; success reports per-platform timing.
4. **Given** a clean repo on a fresh CI runner, **When** the full build-and-test pipeline runs, **Then** it completes within 10 minutes per platform.

---

### Edge Cases

- **Empty title with whitespace** (`title="   "`): Validation rejects whitespace-only titles. Trimmed length must be > 0.
- **Very small duration** (`duration_seconds=0.001`): Accepted; smaller than one block but Score-level validation does not rule it out (Phase 1 may surface a warning).
- **Very large duration** (`duration_seconds=86400`): Accepted; no upper bound at the validator layer.
- **Negative seed** (`seed=-1`): Accepted; passed through to numpy's `SeedSequence` which accepts arbitrary integers.
- **Zero seed** (`seed=0`): Accepted; the constitution does not reserve any seed values.
- **`buffer_size=1`** (technically a power of two): Accepted at validator; below this the audio block becomes degenerate, but Phase 0's role is structural validation, not performance gate-keeping.
- **`pyo_precision=PyoPrecision.DOUBLE` when only `pyo._pyo` is importable**: Phase 0 validation does NOT check this; the constitution requires a hard error at *render* time, which is Phase 1+. Phase 0 surfaces a warning (attached to `Score.warnings`) if the precision is DOUBLE and `pyo._pyo64` is not importable.
- **`variance_defaults` keys not in the `Scale` enum**: Validation rejects with a message naming the offending key.
- **Pyo audit test against a vendored Pyo that has been patched** (e.g., per § 23.8 of the design spec): The audit test must accept Phonon-internal extensions provided their constructor signatures still match the documented baseline; if Phonon adds optional parameters, the audit test must verify the *required* parameters are unchanged. (This is forward-looking; Phase 0 vendored Pyo is unmodified.)
- **CI on Windows**: Native deps (`portaudio`, `portmidi`, `libsndfile`, `liblo`) require vcpkg + MSYS2 mingw64 per design spec §19.5. The workflow must script this; failing to install a native dep is reported as an environment-setup failure distinct from test failure.
- **macOS-x86_64 runner availability**: GitHub Actions deprecated `macos-12` (last x86_64) in 2024; current x86_64 builds run on macos-13. The matrix must use a runner that GitHub still provides; if x86_64 is unavailable, the gap is documented in the workflow comments and surfaced to the constitution-amendment process.

## Requirements *(mandatory)*

### Functional Requirements

#### Repository, Packaging, and Build

- **FR-001**: The Phonon package MUST be installable in editable mode (`pip install -e .` from the repo root) and MUST produce an importable `phonon` module.
- **FR-002**: The vendored Pyo at `pyo-src/` MUST be installable (`pip install -e ./pyo-src/`) and MUST produce an importable `pyo` module on macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest.
- **FR-003**: A `pyproject.toml` at the repo root MUST declare the Phonon package, its runtime dependencies (numpy, PyYAML), its dev extras (pytest, hypothesis), and a Python version floor consistent with vendored Pyo's pyproject.
- **FR-004**: A development-environment install (`pip install -e .[dev]` after the vendored Pyo is installed) MUST produce a working `pytest` invocation with no missing-dependency errors.

#### Module Skeleton

- **FR-005**: The package layout under `phonon/` MUST match design spec §17 (modules: `score.py`, `voice.py`, `trajectory.py`, `coupling.py`, `binding.py`, `rhetoric.py`, `event.py`, `gesture.py`, `shape.py`, `seedseq.py`; subpackages: `process/`, `render/`, `cli/`; plus `version.py` and `__init__.py`).
- **FR-006**: Every module in the layout MUST be importable; modules whose substantive contents are deferred to a later phase MAY be limited to docstrings, type stubs, and `__all__ = []`, but the file MUST exist.
- **FR-007**: Phonon framework code MUST NOT execute `from pyo import *` anywhere; all Pyo references MUST be qualified imports (per Constitution Principle VI).
- **FR-008**: The package's `__init__.py` MUST export only names whose implementations are functional in Phase 0 (`Score`, `Scale`, `RenderMode`, `PyoPrecision`, `Mode`, `Role`, `ScoreValidationError`, plus the small set of enums needed for empty-Score construction). Names whose implementation is deferred to a later phase MUST NOT be exported in Phase 0; the public surface grows phase-by-phase.

#### Score Type and Validation

- **FR-009**: The `Score` type MUST expose all fields listed in design spec §15.1 (`title`, `seed`, `duration_seconds`, `corpus`, `voices`, `couplings`, `trajectories`, `bindings`, `events`, `gestures`, `rhetoric`, `variance_defaults`, `control_hz`, `sample_rate`, `buffer_size`, `nchnls`, `pyo_precision`).
- **FR-010**: Score construction MUST run validation eagerly and MUST raise `ScoreValidationError` on invariant violations.
- **FR-011**: `ScoreValidationError` messages MUST name the offending field and include the invalid value (e.g., `"buffer_size must be a power of two; got 300"`).
- **FR-012**: For an otherwise-valid empty Score (entity lists empty, only metadata and render-contract fields populated), validation MUST succeed.
- **FR-013**: Validation MUST reject empty `title`, including titles consisting only of whitespace (after trim, length must be ≥ 1).
- **FR-014**: Validation MUST reject `duration_seconds` ≤ 0, `NaN`, or infinity.
- **FR-015**: Validation MUST require `seed` to be an integer (any int, including negative and zero).
- **FR-016**: Validation MUST require `sample_rate`, `buffer_size`, `control_hz`, and `nchnls` to be positive integers.
- **FR-017**: Validation MUST require `buffer_size` to be a power of two.
- **FR-018**: Validation MUST require `sample_rate` to be one of the standard Pyo-supported rates: 44100, 48000, 88200, 96000, 176400, 192000.
- **FR-019**: Validation MUST require `pyo_precision` to be a `PyoPrecision` enum value (SINGLE or DOUBLE).
- **FR-020**: Validation MUST require `variance_defaults` keys to be `Scale` enum values and values to be floats in `[0.0, 1.0]`; partial mappings (a subset of scales) MUST be accepted.
- **FR-021**: Validation MUST surface a non-fatal warning (attached to `Score.warnings: list[str]`) when `pyo_precision == PyoPrecision.DOUBLE` and the `pyo._pyo64` extension is not importable.

#### Score.describe()

- **FR-022**: `Score.describe()` MUST return a Python dict whose keys match design spec §15.3: `title`, `duration`, `seed`, `render_contract`, `voices`, `trajectories`, `events`, `gestures`, `rhetoric`, `variance_profile`, `warnings`.
- **FR-023**: `Score.describe()` MUST execute without booting any Pyo Server (it walks the static Score graph only; this serves Constitution Principle V).
- **FR-024**: `Score.describe()` output MUST be YAML-serializable via `yaml.safe_dump`; any value type that cannot round-trip (e.g., enum members) MUST be coerced to a string scalar before insertion into the dict.
- **FR-025**: For an empty Score, the entity-list keys (`voices`, `trajectories`, `events`, `gestures`, `rhetoric`) MUST contain empty lists.
- **FR-026**: `duration` MUST be formatted as `M:SS` for durations under one hour and `H:MM:SS` for one hour or more.
- **FR-027**: `render_contract` MUST contain the keys `sample_rate`, `buffer_size`, `control_hz`, `pyo_precision`, and `framework_version`.
- **FR-028**: `variance_profile` MUST report the `Scale` keys present in `variance_defaults` (each as a string identifier such as `"SUPRA"`); missing scales MAY be omitted or reported as `0.0` consistently.

#### Test Infrastructure

- **FR-029**: A pytest fixture (default name: `manual_server`) MUST yield a booted `pyo.Server(sr=48000, nchnls=2, buffersize=256, audio="manual", duplex=0)`.
- **FR-030**: The fixture MUST clear `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, and `PYO_SERVER_WINHOST` from the process environment before constructing the Server (per Constitution Principle II).
- **FR-031**: The fixture MUST call `Server.shutdown()` on teardown.
- **FR-032**: A Pyo audit test (`tests/test_pyo_audit.py`) MUST verify, for every class listed in design spec Appendix C, that the class is importable from `pyo` and that its constructor signature (from `inspect.signature`) matches the documented signature; mismatches MUST produce a single failure per class, naming the class, the expected signature, and the actual signature.
- **FR-033**: The Pyo audit test MUST verify `pyo.Server` exposes the methods `boot`, `start`, `stop`, `shutdown`, `process`, `recordOptions`, `setGlobalSeed`, `setCallback`, `addMidiEvent`, `getCurrentTime` (per Constitution Principle VI's audit clause and design spec §19.4).
- **FR-034**: The Pyo audit test MUST verify the audio-mode constants Phonon depends on (`"manual"`, `"portaudio"`, plus the platform-equivalent of `"jack"` on Linux/macOS or `"coreaudio"` on macOS) are accepted by `Server` (constructor does not raise on these values).
- **FR-035**: A snapshot test MUST capture an empty Score's `describe()` output and detect regressions; the snapshot file MUST live under `tests/snapshots/empty_score_describe.yaml`.
- **FR-036**: A reproducibility-test scaffold MUST exist: a `tests/test_reproducibility.py` file containing a `sha256_audio_file(path) -> str` helper (functional in Phase 0) plus a placeholder `test_render_is_bit_exact` test that is `pytest.skip`-marked with reason `"awaiting Phase 1 render"` until Phase 1 implements rendering.
- **FR-037**: A differential-reproducibility test scaffold MUST exist analogously: a `test_changing_control_hz_changes_audio` test that is also skip-marked until Phase 1.

#### CI Pipeline

- **FR-038**: A GitHub Actions workflow at `.github/workflows/ci.yml` MUST run on every push and pull request.
- **FR-039**: The workflow matrix MUST include macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest (per Constitution § Development Workflow); macOS-x86_64 MAY be temporarily marked `continue-on-error` if the GitHub-provided runner is unavailable, with the gap documented in the workflow comments.
- **FR-040**: Each platform job MUST install native dependencies as documented in design spec §19.5 (Homebrew on macOS, apt on Linux, vcpkg+MSYS2 on Windows), build vendored Pyo from source via `pip install -e ./pyo-src/`, install Phonon with dev extras, and run the test suite.
- **FR-041**: The Pyo audit test (`tests/test_pyo_audit.py`) MUST run as a dedicated step before the rest of the test suite; if it fails, the subsequent test step MUST be skipped (not run-and-fail), with a clear summary message in the GitHub Actions log.
- **FR-042**: CI failures MUST report the platform, the failed test file, the failed test name, and the assertion error context.
- **FR-043**: A clean CI run MUST complete within 10 minutes per platform under normal GitHub Actions conditions.

#### Determinism and Reproducibility Foundations

- **FR-044**: Phonon's seeded-RNG hierarchy `derive(seed, kind, name)` (design spec §14.2) MUST be implemented in `phonon/seedseq.py` using `numpy.random.SeedSequence` with `entropy=seed` and `spawn_key=hash(kind, name)` semantics. (Phase 0 implements the function and unit-tests it with synthetic kind/name pairs; Phase 1 wires it into Process construction.)
- **FR-045**: `derive(seed, kind, name)` MUST return a `numpy.random.Generator`; the same `(seed, kind, name)` triple MUST produce a Generator whose first 1024 bytes of `standard_normal` output are identical across runs and across platforms.
- **FR-046**: A unit test MUST verify FR-045 (cross-run determinism) and a separate unit test MUST verify uncorrelated streams: `derive(seed, "trajectory", "a")` and `derive(seed, "trajectory", "b")` produce statistically distinct sequences.

### Key Entities

- **Score**: The single declarative value representing a Phonon piece. Phase 0 implements its type, validator, and `describe()` method; entity lists may be empty. Fields per design spec §15.1.
- **Scale (enum)**: The five Roads time scales — `SAMPLE`, `MICRO`, `MESO`, `MACRO`, `SUPRA` — required by Constitution Principle IV. Phase 0 ships the enum and uses it as the key type for `variance_defaults`.
- **PyoPrecision (enum)**: `SINGLE`, `DOUBLE`. Used in render-contract validation; the matching Pyo extension (`pyo._pyo` vs `pyo._pyo64`) is checked at warning-only level in Phase 0 (hard error at render time is a Phase 1+ concern).
- **RenderMode (enum)**: `AUTOPILOT`, `LIVE`, `REPLAY`. Phase 0 defines the enum but does not consume it (rendering is Phase 1+).
- **Mode (enum)**: `ABSOLUTE`, `OFFSET`, `MODULATE`. Phase 0 defines the enum (referenced in the design spec for `Binding` and `Gesture`) but does not consume it.
- **Role (enum)**: `ANCHOR_LOW`, `AIR_HIGH`, `PRIMARY_MID`, `SECONDARY_MID`, `CUSTOM`. Phase 0 defines the enum but voices are not constructible until Phase 2.
- **ScoreValidationError**: Exception raised by `Score.__init__` (or equivalent constructor pathway) on invariant violation. Carries the offending field name and the invalid value in its message.
- **`derive(seed, kind, name)`**: Pure function in `phonon/seedseq.py` returning a seeded `numpy.random.Generator`. The root of Phonon's stochastic determinism (Constitution Principle II).
- **Pyo class reference (Appendix C)**: The list of vendored-Pyo classes Phonon will depend on. Phase 0 audits each one's constructor signature; Phase 1+ consumes them.
- **Vendored Pyo (`pyo-src/`)**: Upstream `belangeo/pyo` 1.0.6 source, vendored verbatim. Phase 0 verifies it builds on every platform; modifications (if ever needed) land as commits per Constitution Principle VI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A composer or contributor on a freshly-cloned macOS-arm64 machine can run `brew install portaudio portmidi libsndfile liblo libogg libvorbis flac opus mpg123 lame && pip install -e ./pyo-src/ && pip install -e .[dev] && pytest`, reach a green test suite, and see the empty-Score describe snapshot pass — all in under 10 minutes total wall time.
- **SC-002**: An empty Score's `describe()` output round-trips through `yaml.safe_dump` → `yaml.safe_load` to a dict equal to the original; the round-trip is exercised in CI on every push.
- **SC-003**: 100% of Phase 0's documented validation invariants (FR-013 through FR-021) are covered by at least one passing positive test (valid input accepted) and one passing negative test (invalid input rejected with the named-field error message).
- **SC-004**: The Pyo audit test passes against vendored Pyo 1.0.6 with zero false positives and zero unexplained skips; introducing a deliberate signature change to any Appendix C class causes the audit test to fail with a message naming the changed class.
- **SC-005**: CI runs on all four platforms (macOS-arm64, macOS-x86_64, ubuntu-latest, windows-latest) reach green within 10 minutes per platform on at least one push to the Phase 0 branch.
- **SC-006**: The `manual_server` fixture is exercised by at least one test, that test passes, and the fixture's teardown is observable (a follow-up test in the same session reaches `Server` state cleanly without leaked file descriptors or Pyo streams).
- **SC-007**: Phase 1's first commit can begin within one working day of Phase 0's merge — measured by absence of "I had to set up X first" notes in the Phase 1 retrospective. Operationalized as: a Phase 1 author can add a new test importing `phonon.process.base` and using the `manual_server` fixture, and the test runs (passing or failing on its own logic, not on missing infrastructure) without any further setup.
- **SC-008**: A deliberate Pyo upstream signature break (e.g., renaming `Sine`'s `freq` parameter in vendored source) causes CI to fail the audit step and skip the rest of the suite on every platform within a single CI run.
- **SC-009**: `derive(seed, kind, name)` produces bit-identical first-1024-byte output across runs on the same platform, and across platforms (verified by a CI step comparing platform-job outputs).

## Assumptions

- The constitution at `.specify/memory/constitution.md` is already ratified at v1.0.0 (2026-04-28); this spec inherits its principles and does not modify them. Phase 0 deliverables therefore exclude "author the constitution" (as the design spec §22 originally listed) — that work has shipped.
- Vendored Pyo at `pyo-src/` is upstream `belangeo/pyo` tag 1.0.6 (committed 2025-03-04), unmodified. Phase 0 does not patch it; if Phase 1+ amends Pyo per design spec §23.8 or §23.9, the audit test bounds the impact.
- Single-precision Pyo (`pyo._pyo`) is the Phase 0 default. Double-precision (`pyo._pyo64`) builds are not exercised by Phase 0 CI; building it adds a `--use-double` flag to the install step and is deferred unless a Phase 1+ piece requires it.
- Native dependencies are installed via the platform's standard package manager (Homebrew on macOS, apt on Linux, vcpkg+MSYS2 on Windows) per design spec §19.5. Phase 0 does not ship a Phonon-specific installer.
- The Python version floor matches vendored Pyo's `pyproject.toml` floor; Phonon does not impose a tighter constraint in Phase 0.
- macOS-arm64 is the primary development platform; macOS-x86_64, ubuntu-latest, and windows-latest are CI cross-checks. If a GitHub-provided x86_64 macOS runner is temporarily unavailable, that matrix entry MAY be marked `continue-on-error` with a workflow comment until the runner is available again.
- Phase 0 produces no audio output. The reproducibility tests (`test_render_is_bit_exact`, `test_changing_control_hz_changes_audio`) are scaffolded with `pytest.skip` reasons until Phase 1 implements rendering. Their *helpers* (`sha256_audio_file`, the `manual_server` fixture) are functional in Phase 0.
- The `phonon` public-API surface in Phase 0's `__init__.py` is *intentionally minimal* — only types whose implementations are functional are exported. Adding new types as their phases land is a normal `__init__.py` edit, not a breaking change.
- `context/threshold_study_1.py` is **expected** to fail import resolution at the end of Phase 0; its types come online in Phases 2 and 3. The Pyright "Import 'phonon' could not be resolved" warning recorded in CLAUDE.md will become "Import resolves but symbols undefined" after Phase 0 — neither state blocks Phase 0's done definition.
- The `phonon` CLI (`phonon render`, `phonon describe`, etc.) is not part of Phase 0; it is Phase 4. Phase 0 does not produce a `phonon` shell entry point.
- Hypothesis (property-based testing) is in dev extras for Phase 1+ trajectory-composition tests; Phase 0 may use it but does not require it.
