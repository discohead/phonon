# NOTICE

Phonon's own source code (everything outside `pyo-src/`) is licensed under the **MIT License** (see `LICENSE`).

## Vendored dependency: Pyo

`pyo-src/` contains a copy of [Pyo](https://github.com/belangeo/pyo) by Olivier Belanger, licensed under **LGPLv3+** (see `pyo-src/LICENSE`). Phonon does not relicense Pyo; the vendored copy retains its upstream license.

## Distribution boundary

Source-only distribution (the default — `pip install git+https://github.com/discohead/phonon`, conda recipes that build Pyo from source) does **not** trigger Pyo's LGPL relink obligation, because the recipient builds Pyo locally from `pyo-src/`.

Distribution that bundles compiled Pyo binaries (wheels with `pyo._pyo.so` / `pyo._pyo64.pyd` included, PyInstaller frozen apps, Docker images with Pyo pre-built) **does** trigger LGPL's relink obligation: the recipient must be able to relink the artifact against a modified Pyo. In practice this means shipping object files or a build script alongside the binary, per LGPLv3 §4(d).
