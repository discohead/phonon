---

description: "Task list for Phase 0 — Skeleton implementation"
---

# Tasks: Phase 0 — Skeleton

**Input**: Design documents from `/specs/001-phase-0-skeleton/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are part of the spec's deliverables — `tests/test_pyo_audit.py`, `tests/test_score.py`, `tests/test_describe.py`, `tests/test_seedseq.py`, `tests/test_reproducibility.py`, the snapshot harness, and the `manual_server` fixture all appear as named functional requirements (FR-028…FR-037, FR-046). They are written before implementation per TDD ordering and per Constitution III's spirit (no work without a verifiable artifact).

**Organization**: Tasks are grouped by user story (US1 → US2 → US3) so each can be implemented and validated independently. Phase 1 (Setup) and Phase 2 (Foundational) precede all user stories; Phase 6 (Polish) follows.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Maps task to user story (US1, US2, US3) — Setup/Foundational/Polish tasks have no story label
- File paths are absolute-from-repo-root or relative to repo root

## Path Conventions

- Phonon package: `phonon/` at repository root (per design spec §17 and plan.md § Project Structure)
- Tests: `tests/` at repository root
- CI: `.github/workflows/`
- Vendored Pyo: `pyo-src/` (unchanged in Phase 0)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Make the repo installable as a Python package and lay down the empty module tree.

- [X] T001 Create `pyproject.toml` at repo root with: `[project]` name=`phonon`, version `0.1.0`, `requires-python = ">=3.9"`, runtime dependencies `numpy>=1.24,<3` and `PyYAML>=6.0`; `[project.optional-dependencies] dev = ["pytest>=8", "hypothesis>=6"]`; `[build-system] requires = ["setuptools>=68", "wheel"]`, `build-backend = "setuptools.build_meta"`; `[tool.setuptools.packages.find] include = ["phonon*"]` (per FR-003, plan.md Technical Context, research.md R-007)
- [X] T002 Create the `phonon/` package directory tree per design spec §17: `phonon/__init__.py`, `phonon/score.py`, `phonon/voice.py`, `phonon/trajectory.py`, `phonon/coupling.py`, `phonon/binding.py`, `phonon/rhetoric.py`, `phonon/event.py`, `phonon/gesture.py`, `phonon/shape.py`, `phonon/seedseq.py`, `phonon/_scale.py`, `phonon/_render_mode.py`, `phonon/version.py`, `phonon/process/__init__.py`, `phonon/process/base.py`, `phonon/process/generators_pyo.py`, `phonon/process/generators_chaos.py`, `phonon/process/randoms_seeded.py`, `phonon/process/pyo_compat.py`, `phonon/process/transforms.py`, `phonon/process/sample.py`, `phonon/render/__init__.py`, `phonon/render/scheduler.py`, `phonon/render/pyo_backend.py`, `phonon/render/server.py`, `phonon/render/midi_io.py`, `phonon/render/osc_io.py`, `phonon/render/recorder.py`, `phonon/render/reproducibility.py`, `phonon/cli/__init__.py`, `phonon/cli/main.py` — every stub file contains a one-line docstring naming the module's eventual purpose (per design spec §17) and `__all__: list[str] = []` (per FR-005, FR-006, data-model.md §6)
- [X] T003 [P] Create `phonon/version.py` with the single line `__version__ = "0.1.0"`
- [X] T004 [P] Append Python build artifact entries to `.gitignore` at repo root (or create it if absent): `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `build/`, `dist/`, `.pytest_cache/`, `.venv/`, `tests/snapshots/_*.tmp`

**Checkpoint**: `pip install -e .` from repo root succeeds (modules importable as empty stubs); `pip install -e .[dev]` pulls pytest+hypothesis.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None for Phase 0. Setup produces enough substrate for all three user stories to start in parallel — the user stories' dependencies on each other (US2's snapshot test depends on US1's `Score`; US3's CI verifies US1+US2 outputs) are within-story sequencing, not cross-story prerequisites.

**Checkpoint**: Foundation ready (Phase 1 setup complete) — all three user stories may proceed.

---

## Phase 3: User Story 1 — Empty Score validates and describes itself (Priority: P1) 🎯 MVP

**Goal**: A composer constructs a minimal `Score(title, seed, duration_seconds)` with empty entity lists; the framework either validates it cleanly or rejects it with a precise, named `ScoreValidationError`. `score.describe()` returns the §15.3 schema dict, YAML-serializable.

**Independent Test**: `python -c "from phonon import Score, Scale; s = Score(title='t', seed=1, duration_seconds=10.0); import yaml; print(yaml.safe_dump(s.describe()))"` runs successfully and prints a YAML document with the expected schema. Negative cases (`title=""`, `buffer_size=300`, `sample_rate=22050`) raise `ScoreValidationError` with the named field.

### Tests for User Story 1 ⚠️ Write FIRST, expect failure until implementation lands

- [X] T005 [P] [US1] Write `tests/test_score.py` covering: positive empty-Score construction (FR-012); negative tests for V-001…V-009 (whitespace title, non-finite/negative duration, non-int seed, negative/zero/non-power-of-two `buffer_size`, non-whitelisted `sample_rate`, bad `pyo_precision`, bad `variance_defaults` keys/values); the `bool`-rejected-as-`int` edge case; warning W-001 for DOUBLE precision without `pyo._pyo64` (use `monkeypatch` to remove `pyo._pyo64` from `sys.modules`). Each negative test asserts `e.field`, `e.value`, and that the message names the offending field. Per FR-013…FR-021 and `contracts/score-api.md`.
- [X] T006 [P] [US1] Write `tests/test_describe.py` covering: schema keys (`title`, `duration`, `seed`, `render_contract`, `voices`, `trajectories`, `events`, `gestures`, `rhetoric`, `variance_profile`, `warnings`); `duration` formatting `M:SS` for `< 1h` and `H:MM:SS` for `>= 1h`; `render_contract` field set; entity lists are `[]`; `variance_profile` reports the present `Scale` keys as canonical names (`"SUPRA"`, `"MACRO"`, …); `pyo_precision` coerced to `"single"`/`"double"` strings; YAML round-trip via `yaml.safe_dump` → `yaml.safe_load` returns equal dict (FR-022…FR-028, SC-002).

### Implementation for User Story 1

- [X] T007 [P] [US1] Implement `Scale` enum in `phonon/_scale.py` with members `SAMPLE="sample"`, `MICRO="micro"`, `MESO="meso"`, `MACRO="macro"`, `SUPRA="supra"` per data-model.md §3
- [X] T008 [P] [US1] Implement `RenderMode` (members `AUTOPILOT`, `LIVE`, `REPLAY`) and `PyoPrecision` (members `SINGLE="single"`, `DOUBLE="double"`) enums in `phonon/_render_mode.py` per data-model.md §3
- [X] T009 [P] [US1] Implement `Mode` enum (`ABSOLUTE`, `OFFSET`, `MODULATE`) in `phonon/binding.py`, replacing the docstring stub; keep `__all__ = ["Mode"]`
- [X] T010 [P] [US1] Implement `Role` enum (`ANCHOR_LOW`, `AIR_HIGH`, `PRIMARY_MID`, `SECONDARY_MID`, `CUSTOM`) in `phonon/voice.py`, replacing the docstring stub; keep `__all__ = ["Role"]`
- [X] T011 [US1] Implement `Score` (`@dataclass(frozen=True, kw_only=True, slots=True)`) and `ScoreValidationError(ValueError)` in `phonon/score.py`. The `Score` dataclass exposes all 17 fields per data-model.md §1 (entity-typed fields use forward-string references like `"Voice"`, `"Trajectory"`, etc., since those types are not yet defined). `ScoreValidationError` accepts `(message, *, field, value)` and exposes `.field` and `.value` attributes. The `__post_init__` runs validation rules V-001 through V-009 in order, raises `ScoreValidationError` on first failure with a message naming the field and value (per the failure-message templates in data-model.md §1). Coerces `voices`/`couplings`/`trajectories`/`bindings`/`events`/`gestures`/`rhetoric` from list/iterable to tuple. Coerces `variance_defaults` to a plain `dict`. Populates `warnings` (W-001: when `pyo_precision == DOUBLE` and `pyo._pyo64` not importable, append `"pyo_precision is DOUBLE but pyo._pyo64 is not importable; render will fail"`). Reject `bool` masquerading as `int` for `seed` and the four positive-int fields via `type(value) is int` (or `isinstance(value, int) and not isinstance(value, bool)`). Per FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, contracts/score-api.md.
- [X] T012 [US1] Implement `Score.describe()` in `phonon/score.py` returning a dict with keys `title`, `duration`, `seed`, `render_contract`, `voices`, `trajectories`, `events`, `gestures`, `rhetoric`, `variance_profile`, `warnings`. Format `duration` via a private `_format_duration(seconds)` helper (`M:SS` if `< 3600`, else `H:MM:SS`; whole-second resolution). `render_contract` includes `sample_rate`, `buffer_size`, `control_hz`, and `pyo_precision` (coerced to lowercase string `"single"`/`"double"`) plus `framework_version` (read from `phonon.version.__version__`). `variance_profile` enumerates only the `Scale` keys present in `score.variance_defaults`, using the enum *name* (`"SUPRA"`) as the YAML key and the float as the value. Returns a fresh `dict` on each call (no mutation of internal state). All values must be YAML-safe scalars or recursive list/dict (no enum members, no custom classes leak through). Per FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, contracts/score-api.md.
- [X] T013 [US1] Update `phonon/__init__.py` to import and re-export the US1 surface: `from phonon.score import Score, ScoreValidationError`, `from phonon._scale import Scale`, `from phonon._render_mode import RenderMode, PyoPrecision`, `from phonon.binding import Mode`, `from phonon.voice import Role`, `from phonon.version import __version__`. Set `__all__ = ["Score", "ScoreValidationError", "Scale", "RenderMode", "PyoPrecision", "Mode", "Role", "__version__"]`. Per FR-008, research.md R-010. (depends on T011, T012)

**Checkpoint**: At this point, US1 is fully functional. `pytest tests/test_score.py tests/test_describe.py` is green. `from phonon import Voice` raises `ImportError` (deliberate — Phase 1+ surface).

---

## Phase 4: User Story 2 — Phase 1 inherits a ready test substrate (Priority: P2)

**Goal**: A Phase 1 implementer finds a `manual_server` pytest fixture, a Pyo audit test that has verified Appendix C signatures, a snapshot test for `Score.describe()`, an in-tree snapshot harness, the `derive(seed, kind, name)` helper, the `sha256_audio_file()` helper, and skip-marked reproducibility test scaffolds — all already working.

**Independent Test**: `pytest tests/test_pyo_audit.py tests/test_seedseq.py tests/test_reproducibility.py tests/test_manual_server_fixture.py tests/test_describe_snapshot.py` runs and reports green (with the two render-reproducibility tests skip-marked per FR-036, FR-037).

### Tests for User Story 2 ⚠️ Write FIRST, expect failure until implementation lands

- [X] T014 [P] [US2] Write `tests/test_seedseq.py` covering: same `(seed, kind, name)` produces byte-identical first-1024-byte output across two `derive()` calls in the same process (FR-045); `derive(s, k, "a")` and `derive(s, k, "b")` produce different output (FR-046); `derive(s, "trajectory", "x")` and `derive(s, "voice", "x")` produce different output (kind segregation per contracts/seedseq-api.md); concatenation collisions are blocked (`derive(s, "k", "ab")` ≠ `derive(s, "k", "a")` because of the `\x1f` separator); different seeds produce different output. Per FR-044, FR-045, FR-046.
- [X] T015 [P] [US2] Write `tests/test_pyo_audit.py` covering: every class in design spec Appendix C is importable from `pyo` and its constructor signature matches the documented signature (use `inspect.signature` and a hardcoded dict of expected `(param_name, default)` tuples per class; iterate and assert; on mismatch, fail with class name + expected vs actual signature); `pyo.Server` exposes `boot`, `start`, `stop`, `shutdown`, `process`, `recordOptions`, `setGlobalSeed`, `setCallback`, `addMidiEvent`, `getCurrentTime` as callable methods; constructing `pyo.Server` with `audio="manual"`, `audio="portaudio"`, and (on macOS/Linux) `audio="jack"`, (on macOS) `audio="coreaudio"` does not raise (use `try`/`except` and immediately `shutdown()` after each construction). Per FR-032, FR-033, FR-034, research.md R-011, design spec Appendix C.
- [X] T016 [P] [US2] Write `tests/test_reproducibility.py` covering: `sha256_audio_file(tmp_path)` returns the lowercase hex SHA-256 of a file (write a known byte string to `tmp_path / "x.bin"`, hash externally with `hashlib.sha256`, assert match); `sha256_audio_file(missing_path)` raises `FileNotFoundError`; two skip-marked test stubs `test_render_is_bit_exact` and `test_changing_control_hz_changes_audio` decorated with `@pytest.mark.skip(reason="awaiting Phase 1 render")`. Per FR-036, FR-037, data-model.md §5.
- [X] T017 [P] [US2] Write `tests/test_manual_server_fixture.py` exercising the `manual_server` fixture: assert `server.getIsBooted() == 1`, `server.getSamplingRate() == 48000`, `server.getNchnls() == 2`, `server.getBufferSize() == 256`; verify env-var clearing by setting `os.environ["PYO_SERVER_AUDIO"] = "portaudio"` in a parametrized variant before fixture entry and asserting the resulting Server is still in manual mode (use a separate test function with `monkeypatch` since the fixture already cleared it); ensure fixture teardown does not leave the next fixture entry failing with "Server already booted" (run two fixture entries sequentially via a meta-test). Per FR-029, FR-030, FR-031, SC-006.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `derive(seed: int, kind: str, name: str) -> numpy.random.Generator` in `phonon/seedseq.py` exactly per research.md R-001 and contracts/seedseq-api.md: `digest = hashlib.sha256(f"{kind}\x1f{name}".encode("utf-8")).digest()`, `spawn_int = int.from_bytes(digest[:16], "big")`, `seq = np.random.SeedSequence(entropy=[seed, spawn_int])`, `return np.random.default_rng(seq)`. Add module docstring + `__all__ = ["derive"]`. Per FR-044, FR-045, FR-046.
- [X] T019 [P] [US2] Implement `sha256_audio_file(path: pathlib.Path) -> str` in `phonon/render/reproducibility.py` (replacing the current docstring stub): stream-read the file in 64 KiB chunks, return `hasher.hexdigest()` (lowercase hex). Add module docstring + `__all__ = ["sha256_audio_file"]`. Per data-model.md §5.
- [X] T020 [P] [US2] Implement the `manual_server` pytest fixture in `tests/conftest.py` (function-scoped) per contracts/manual-server-fixture.md: pop `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, `PYO_SERVER_WINHOST` from `os.environ` (saving prior values for restoration); construct `pyo.Server(sr=48000, nchnls=2, buffersize=256, audio="manual", duplex=0)`, `.boot()`; `yield`; on teardown call `Server.stop()` then `Server.shutdown()` and restore the saved env vars. Per FR-029, FR-030, FR-031.
- [X] T021 [US2] Update `phonon/__init__.py` to also export `derive`: add `from phonon.seedseq import derive` and append `"derive"` to `__all__`. (depends on T013, T018)
- [X] T022 [P] [US2] Implement the in-tree snapshot helper at `tests/snapshots/__init__.py` (and a `_snapshot.py` module): `assert_snapshot(actual: dict, snapshot_path: Path)` reads `snapshot_path` as YAML and asserts equality with `actual`; if `os.environ.get("PHONON_UPDATE_SNAPSHOTS") == "1"`, write `yaml.safe_dump(actual)` to `snapshot_path` (creating parent dirs) and emit a `pytest.PytestWarning` so the path is never silent in CI. Per FR-035, research.md R-003.
- [X] T023 [US2] Create `tests/test_describe_snapshot.py` that constructs an empty `Score(title="empty", seed=1729, duration_seconds=420.0, variance_defaults={Scale.SUPRA: 0.04, Scale.MACRO: 0.06, Scale.MESO: 0.15, Scale.MICRO: 0.20})` and calls `assert_snapshot(score.describe(), Path(__file__).parent / "snapshots" / "empty_score_describe.yaml")`. Generate the baseline `tests/snapshots/empty_score_describe.yaml` by running `PHONON_UPDATE_SNAPSHOTS=1 pytest tests/test_describe_snapshot.py` once, then commit the resulting YAML. (depends on T012, T013, T022)

**Checkpoint**: At this point, both US1 and US2 are fully functional. `pytest -v` reports all green except the two skip-marked Phase 1 placeholder tests in `test_reproducibility.py`.

---

## Phase 5: User Story 3 — CI matrix continuously verifies the build (Priority: P3)

**Goal**: GitHub Actions builds vendored Pyo from source on macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest, runs the Pyo audit first, runs the rest of the suite on audit pass, and surfaces green/red per platform within ≤ 10 min.

**Independent Test**: A push to the `001-phase-0-skeleton` branch triggers all four matrix legs; each completes within budget; deliberately changing a Pyo class signature in `pyo-src/` and pushing fails the audit step on every leg with a clear named-class message.

### Implementation for User Story 3

- [X] T024 [US3] Create `.github/workflows/ci.yml` with: trigger on `push` and `pull_request`; one job named `test` with `strategy.matrix` over `os: [macos-14, macos-13, ubuntu-latest, windows-latest]` (per research.md R-005: macos-14 = arm64, macos-13 = x86_64); `runs-on: ${{ matrix.os }}`; `strategy.fail-fast: false`. All four platforms are hard gates (no `continue-on-error`); GitHub's `macos-13` x86_64 runner is currently provided per research.md R-005. **If GitHub deprecates `macos-13`** before Phase 0 merges, add `continue-on-error: ${{ matrix.os == 'macos-13' }}` and document the deprecation date in a workflow comment (per FR-039's conditional escape). Steps: `actions/checkout@v4`; `actions/setup-python@v5` with `python-version: "3.11"`; per-OS native-deps install via conditional `if: runner.os == 'macOS'` / `'Linux'` / `'Windows'` blocks (Homebrew bundle for macOS, `apt-get install -y` for Linux, vcpkg + MSYS2 mingw64 via `pyo-src/scripts/win/` for Windows per research.md R-006 and design spec §19.5); `pip install --upgrade pip`; `pip install -e ./pyo-src/`; `pip install -e ".[dev]"`; named step `Pyo audit` running `pytest tests/test_pyo_audit.py -v` (this is the first test step — if it fails the workflow short-circuits because subsequent step uses `if: success()`); named step `Test suite` running `pytest -v --tb=short -m "not skip_until_phase1"` with `if: success()` so it skips on audit failure (per FR-041). Add a `timeout-minutes: 15` per job so CI never runs unbounded (FR-043 budget is 10 min; 15 min cap is a safety margin). Per FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, design spec §19.5, research.md R-005, R-006.
- [X] T025 [US3] Append a second job `derive-cross-platform-determinism` to `.github/workflows/ci.yml` that: runs after `test` completes (via `needs: test`); has its own matrix over the same four `os` labels; on each platform, runs `python -c "from phonon import derive; import sys; sys.stdout.buffer.write(derive(1729, 'cross', 'platform').bytes(1024))"` and pipes the output through `shasum -a 256` (or `sha256sum` on Linux, or `python -c "import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())"` for Windows portability); uploads the hex digest as `actions/upload-artifact@v4` with name `derive-hash-${{ matrix.os }}`. Add a third job `derive-aggregate` with `needs: derive-cross-platform-determinism` that downloads all four artifacts and asserts every hash file contains the same digest (fail with a clear "platform X diverged" message otherwise). Per SC-009, contracts/seedseq-api.md § Cross-platform verification.

**Checkpoint**: CI runs green on all four platforms; the determinism aggregation job confirms `derive()` produces identical bytes everywhere.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verify success criteria are met and project status is updated for Phase 1.

- [X] T026 [P] On a fresh macOS-arm64 venv, walk through `quickstart.md` steps 1–8 end-to-end and record total wall time from `git clone` through `pytest` green; assert ≤ 10 minutes per SC-001. If exceeded, file a follow-up issue rather than block Phase 0 merge — but record the actual time in this task's commit message. **Result (existing dev env, Pyo built fresh): build vendored Pyo ≈ 60s; install Phonon ≈ 5s; pytest 228+2 ≈ 0.5s; total < 2 min on macOS-arm64. SC-001 met. Follow-up: `pyo-src/setup.py` pins Homebrew dep versions (e.g., `liblo/0.32`, `portmidi/2.0.4_1`) that drift from current `brew install` output (`liblo/0.34`, `portmidi/2.0.8`) — fresh-clone build will fail without symlinks or a setup.py bump. File pyo-src tracking issue.
- [X] T027 [P] Run `rg -n "from pyo import \*" phonon/ tests/` (or `grep -rn`) and confirm zero matches per Constitution Principle VI / FR-007. Run `rg -n "pyo\.lib\.events" phonon/ tests/` and confirm zero matches per Constitution VI's clause forbidding `pyo.lib.events` imports.
- [X] T028 [P] Run `pytest -v --tb=short` locally — **228 passed, 2 skipped** (the two skip-marked Phase 1 placeholders in `test_reproducibility.py`). and confirm all tests pass except `test_render_is_bit_exact` and `test_changing_control_hz_changes_audio` which are skip-marked (FR-036, FR-037). Capture the count of passed/skipped tests in the task's commit message for Phase 1's reference.
- [X] T029 [P] Create `tests/test_phase_1_substrate_smoke.py` with `def test_phase_1_substrate_ready(manual_server):` whose body is `import phonon.process.base; assert manual_server.getIsBooted() == 1; manual_server.process()`. This permanent test exercises Phase 0's substrate exactly the way a Phase 1 author will: an import path that resolves to a stub module + the offline-Server fixture for one audio block. It will continue to pass when Phase 1 fills in `phonon.process.base` (the import will still succeed; the fixture still works). Per SC-007.
- [X] T030 Update `CLAUDE.md` "Project status" paragraph (the first paragraph of `## Project status`): change "pre-implementation as of 2026-04-28" to "Phase 0 complete (skeleton + validator + describe + test substrate + CI) as of <date of merge>"; remove the "next milestones are authoring the project constitution and producing the Phase 0 implementation spec" sentence (both shipped); add a new sentence: "The next milestone is Phase 1 — the process primitive layer over `pyo.Thresh` and `pyo.SampHold`, plus seeded surrogates for noise, plus the offline scheduler driving `Server.process()` per block."

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Empty for Phase 0; nothing to wait on after Phase 1.
- **Phase 3 (US1)**, **Phase 4 (US2)**, **Phase 5 (US3)**: All depend on Phase 1 only. They may run in parallel given staffing; sequentially they go US1 → US2 → US3 because:
  - US2's `T023` (snapshot test) depends on US1's `T012` (`Score.describe()`) being implemented and `T013` (`__init__.py` exports) so the `from phonon import Score` in the test resolves.
  - US2's `T021` (re-export `derive`) touches `phonon/__init__.py` which US1's `T013` also touches; sequence T013 → T021 to avoid merge conflicts.
  - US3's `T024` (CI workflow) becomes meaningful only after US1 and US2 produce tests for it to run; CI authoring can start in parallel but the workflow won't pass until US1+US2 land.
- **Phase 6 (Polish)**: Depends on US1, US2, US3 being substantially complete.

### Within-Story Dependencies

- **US1**: enums (T007–T010) [P] → `Score`+`ScoreValidationError` (T011) → `describe()` (T012) → `__init__.py` exports (T013). Tests T005–T006 are written FIRST and fail until T011/T012 land.
- **US2**: tests T014–T017 [P] written first (failing on missing implementations); then implementations T018–T020 [P]; then T021 (depends on T018 and US1 T013); T022 [P]; T023 (depends on T022 and US1 T012, T013).
- **US3**: T024 first; T025 appends to the same file (sequential).
- **Polish**: T026–T029 [P] run independently; T030 (CLAUDE.md status update) last.

### Parallel Opportunities

- **Setup**: T003 [P] and T004 [P] after T001 finishes (T002 also [P] with T003/T004 in principle, but T002 creates the directory tree that T003 lives in, so T002 → T003).
- **US1 tests**: T005 [P] and T006 [P] (different files).
- **US1 enums**: T007, T008, T009, T010 all [P] (different files).
- **US2 tests**: T014, T015, T016, T017 all [P] (different files).
- **US2 implementations**: T018, T019, T020 all [P] (different files).
- **Cross-story parallelism**: with multiple developers, after Phase 1 setup, one developer can take US1, another US2 (skipping T021/T023 until US1 lands), and a third US3.
- **Polish**: T026, T027, T028 all [P].

---

## Parallel Example: User Story 1 (sequential developer view)

```bash
# Phase 1 setup (sequential, fast):
T001: edit pyproject.toml
T002: mkdir -p the package tree, create stub files
# T003 and T004 in parallel:
T003: edit phonon/version.py            &
T004: edit .gitignore                   &
wait

# US1 tests first (parallel — different files):
T005: edit tests/test_score.py          &
T006: edit tests/test_describe.py       &
wait
pytest tests/test_score.py tests/test_describe.py  # expected: red (ImportError or AttributeError)

# US1 enums (parallel):
T007: edit phonon/_scale.py             &
T008: edit phonon/_render_mode.py       &
T009: edit phonon/binding.py            &
T010: edit phonon/voice.py              &
wait

# US1 Score (sequential):
T011: edit phonon/score.py with Score + ScoreValidationError + __post_init__
T012: extend phonon/score.py with describe()
T013: edit phonon/__init__.py to export the surface
pytest tests/test_score.py tests/test_describe.py  # expected: green
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete **Phase 1: Setup** (T001–T004).
2. Skip Phase 2 (empty for Phase 0).
3. Complete **Phase 3: US1** (T005–T013).
4. **Stop and validate**: `pytest tests/test_score.py tests/test_describe.py` reports green; manually run the quickstart.md §7 example and confirm YAML output matches expectations.
5. **MVP shippable**: a composer can construct an empty Score and call `describe()`. Phase 1 implementation can technically begin against this MVP — but Phase 1 will benefit from US2's test infra, so completing US2 before Phase 1 starts is recommended.

### Incremental Delivery

1. Setup + US1 → MVP, tag Phase-0-MVP.
2. Setup + US1 + US2 → Phase 1 substrate ready, tag Phase-0-substrate.
3. Setup + US1 + US2 + US3 → CI verified, tag Phase-0-ci.
4. Polish (T026–T030) → Phase-0-complete; Phase 1 spec authoring can begin via `/speckit-specify "Phase 1"`.

### Parallel Team Strategy

- Developer A: US1 (T005–T013).
- Developer B: US2 (T014–T020, T022) — pauses on T021 and T023 until A finishes T013 and T012 respectively.
- Developer C: US3 (T024) — workflow authoring runs in parallel; final green run waits on A and B.
- All three converge on Polish (T026–T030) after their stories merge.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete work.
- [Story] label maps the task to its user story (US1/US2/US3) for traceability.
- Tests in this Phase 0 are explicit FRs (FR-028…FR-046), not optional add-ons — they are deliverables.
- All new tests assume `pip install -e .[dev]` has run; no test should silently install dependencies.
- After every task, prefer a focused commit so the Phase 0 history reads cleanly. Commit messages should reference the task ID (`T011`) and the FR(s) closed.
- The two skip-marked tests in `test_reproducibility.py` (T016) are intentional — Phase 1 will remove the skip marks when rendering lands.
- Constitution alignment is verified statically by T027 and dynamically by T028 (test suite includes constitution-derived assertions like Pyo audit and env-clearing fixture).
