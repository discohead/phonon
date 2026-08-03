# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`pyo` is a Python module written in C for digital signal processing. It is a CPython extension exposing audio synthesis, processing, MIDI, and OSC primitives to Python. The package is structured as a thin Python layer (in `pyo/lib/`) that wraps two compiled C extensions (`pyo._pyo`, single precision, and `pyo._pyo64`, double precision). The `pyo64` top-level package is a tiny shim that flips a flag (`builtins.pyo_use_double = True`) and re-exports `pyo`, so that `import pyo64` selects the double-precision extension at import time.

Public version is defined in two places that must stay in sync: `pyproject.toml` (`version`) and `include/pyomodule.h` (`PYO_VERSION`).

## Build & install

The project is built with `setuptools`/`pyproject.toml` (no PEP 517 build isolation issues, but the build invokes a custom `setup.py` for the extension and platform-specific dylib bundling). Building requires native deps: portaudio, portmidi, libsndfile (1.0.30+), liblo (0.32+), and (Linux/macOS) a working C compiler. On macOS, dependencies are expected from Homebrew, resolved through the version-independent `opt` symlinks (`/opt/homebrew/opt/<pkg>` on arm64, `/usr/local/opt/<pkg>` on Intel; override the root with `BREW_PACKAGES_ROOT`), so Homebrew version bumps need no `setup.py` edits — the version strings in `pkgs_3rdpary` are informational (the wheel release scripts under `scripts/` still reference them). On Windows, deps come from `vcpkg` (`VCPKG_ROOT` env var) and MSYS2 mingw64.

```bash
# In-place dev build (most common when iterating on C sources)
python setup.py build_ext --inplace

# Full wheel build (modern path)
python -m pip install build
python -m build

# Pass build flags via --config-setting (one per flag)
python -m build --config-setting="--build-option=--use-double" \
                --config-setting="--build-option=--use-jack"
```

Important `setup.py` flags (consumed and stripped from `sys.argv` before setuptools sees them):
- `--use-double` — also build `pyo._pyo64` (double-precision extension). Without it, only single-precision `_pyo` is built and `import pyo64` will fail.
- `--use-jack` / `--jack-force-old-api` — JACK audio backend (Linux/macOS).
- `--use-coreaudio` — CoreAudio backend (macOS).
- `--minimal` — drop portaudio, portmidi, and liblo deps (libsndfile remains required).
- `--no-messages` — suppress most stdout chatter from C code.
- `--debug` — `-g3 -UNDEBUG` (default is `-g0 -DNDEBUG`).
- `--fast-compile` — `-O0` (default is `-O3`).
- `--compile-externals` — pull `externals/externalmodule.{c,h}` and `externals/external.py` into the build (see "Adding C objects" below).

Editor entry point: `epyo` console script, defined in `pyproject.toml` → `pyo.editor.EPyo:main`.

## Tests

Two distinct test surfaces live under `tests/`:

1. **`tests/pytests/`** — modern pytest suite. Run from inside that directory:
   ```bash
   cd tests/pytests
   pytest                              # all tests
   pytest test_baseObjects.py          # one file
   pytest test_baseObjects.py::TestPyoBaseObject::test_PyoObjectBase
   ```
   Tests boot a `Server(audio="manual")` via the `audio_server` fixture in `conftest.py` (no real audio device required). Most test classes use `@pytest.mark.usefixtures("audio_server")`. Anything that touches a `PyoObject` requires a booted Server in the current process — `Sine()` etc. raise `PyoServerStateException` otherwise.

2. **Top-level `tests/*.py`** — older standalone scripts (e.g. `test_math_ops.py`, `play_all_manual_examples.py`, `test_portaudio_functions.py`). These are run directly with `python tests/<file>.py` and may open real audio output. They are **not** pytest-collected.

Memory checking lives under `tests/valgrind/`. The `bébêtte/` and `test_Expr_object/` directories contain manual / interactive test fixtures.

## Documentation

Sphinx docs live under `documentation/source/`. The build is custom (`documentation/build.py`):

```bash
cd documentation
python build.py            # html → ../docs/
python build.py --latex    # PDF
python build.py --man      # man pages
```

`build.py` does three non-obvious things before invoking `sphinx-build`: (1) generates `source/api/alphabetical.rst` by walking `OBJECTS_TREE` from the live Python module, (2) regenerates the `source/examples/` tree from `pyo/examples/x*` directories (each example's leading docstring becomes its `.rst`), and (3) when building HTML, copies output to the repo's top-level `docs/` directory (which is the GitHub Pages source — committed). The `source/examples/` tree is removed at the end of the run; do not edit it by hand.

## Architecture

### Layered design

- **C engine** (`src/engine/`) — server, streams, tables, matrices, FFT, the platform audio drivers (`ad_portaudio.c`, `ad_jack.c`, `ad_coreaudio.c`), MIDI driver (`md_portmidi.c`), OSC (`oscmodule.c`), and the module entry point (`pyomodule.c`). Headers live in `include/`.
- **C objects** (`src/objects/`) — one `*module.c` per family of DSP objects (e.g. `filtremodule.c`, `granulatormodule.c`, `phasevocmodule.c`). Each defines `PyTypeObject`s exposed to Python. Files starting with `ad_` or `md_` and any with `listener` in the name are conditionally included based on the audio/midi backend — see the file-list construction in `setup.py` (around the `path = "src/engine"` block).
- **Python layer** (`pyo/lib/`) — user-facing classes that wrap the C objects, handle multi-channel expansion, GUIs, and Pythonic ergonomics. Organized by domain: `generators.py`, `filters.py`, `effects.py`, `dynamics.py`, `tables.py`, `matrix.py`, `midi.py`, `opensndctrl.py`, `events.py`, `expression.py`, etc. `_core.py` defines the base classes (`PyoObject`, `PyoTableObject`, `PyoMatrixObject`, `PyoPVObject`) and is where `pyo.lib._core` decides which compiled extension to import based on `builtins.pyo_use_double`.
- **GUI widgets** (`pyo/lib/_widgets.py`, `_wxwidgets.py`, `_tkwidgets.py`) — wxPython is the primary toolkit; tkinter is a fallback for control windows.
- **Editor** (`pyo/editor/EPyo.py`) — the bundled IDE shipped as the `epyo` console script.
- **Examples** (`pyo/examples/x01-intro` through `x23-expression`) — these are part of the package (listed in `pyproject.toml`'s `[tool.setuptools] packages`) and are also the source of truth for the docs' Examples section.

### Single vs. double precision

Two parallel extensions are built from the **same** C sources, with `USE_DOUBLE` macro toggling `MYFLT` between `float` and `double` (see `include/pyomodule.h`). The Python side picks one at import: if `pyo` is imported plain, `pyo.lib._core` does `from .._pyo import *`; if `pyo64` is imported (which sets `builtins.pyo_use_double = True` before re-exporting `pyo`), it does `from .._pyo64 import *`. Both extensions cannot be live at the same time inside one process. When changing C code that crosses the `MYFLT`/`Py_ssize_t` boundary, build with `--use-double` and re-run tests against both, or you'll only catch issues in one precision.

### Audio server lifecycle

Nothing audio-related works without a `Server` instance that has been booted. `Server` owns the audio backend, the stream registry, and the GIL-aware callback. Most user-visible classes are `PyoObject` subclasses that register `Stream`s with the server on construction. A common foot-gun (called out in `TODO.md`) is creating a `PyoObject` inside a function that returns — when the local goes out of scope, the streams are GC'd and audio stops. Tests sidestep this with module-level references and the `audio_server` fixture.

### Embedded API

`embedded/m_pyo.h` is the single-header C API for hosting pyo inside other applications (Pure Data, JUCE, Bela, openFrameworks — each has a subdir under `embedded/`). It spins up a private CPython interpreter per pyo instance so multiple pyo servers can coexist in one host process. Treat changes to `m_pyo.h` as ABI changes for these hosts.

## Adding C objects

Adding a new built-in DSP object means: (1) write a `*module.c` under `src/objects/` and any header it needs in `include/`, (2) register the type in `src/engine/pyomodule.c` (look for `PyModule_AddObject` calls and the `Py*Type` table additions), (3) add a Python wrapper class in the appropriate `pyo/lib/*.py` so the user-facing API handles multichannel expansion (`mul`, `add`, list-of-frequencies, etc.). The pattern is consistent across families — pick the closest existing object and copy its structure.

For out-of-tree experimentation, use the `externals/` template flow: copy `externalmodule-template.{c,h}` → `externalmodule.{c,h}` and `external-template.py` → `external.py`, then build with `--compile-externals`. Only those three filenames are wired up; multi-file externals are not supported.

## Platform notes

- **macOS wheels**: `scripts/release_wheels_OSX_arm64.sh` and `release_wheels_OSX.sh` post-process built wheels with `install_name_tool` to rewrite `/opt/homebrew/...` paths to `@loader_path/...` and bundle the dylibs (FLAC, ogg, vorbis, sndfile, opus, mpg123, lame, portaudio, portmidi, liblo). The dylib version numbers in those scripts must match what's actually present in `pkgs_3rdpary` in `setup.py`.
- **Linux wheels**: built via the manylinux2014 GitHub Actions workflow (`.github/workflows/build_manylinux_wheels.yml`), which uploads to **Test PyPI**. Production PyPI uploads are manual.
- **Windows**: `setup.py` no longer supports 32-bit builds. The build expects `vcpkg` and an MSYS2 mingw64 toolchain; relevant DLLs are copied into `pyo/` during `setup.py` and removed afterward. See `scripts/win/windows-10-64bit-build-routine.txt` for the maintainer's procedure.

## Don't edit by hand

- `docs/` (top level) — generated by `documentation/build.py`.
- `documentation/source/api/alphabetical.rst` and `documentation/source/examples/**` — generated.
- `setup.cfg` — only created/destroyed transiently on Windows builds.
- `pyo/lib/external.py` — copied in/out by `setup.py` only when `--compile-externals` is set.
