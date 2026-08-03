"""Phonon — composition framework for experimental electronic music.

Phase 0 surface: a declarative `Score` value plus the five enums (`Scale`,
`RenderMode`, `PyoPrecision`, `Mode`, `Role`) and the framework version. The
substrate types (`Voice`, `Trajectory`, `Coupling`, `Binding`, `Event`,
`Gesture`, rhetoric primitives, process generators, shape factories) come
online phase-by-phase per design spec §22.
"""

from phonon._render_mode import PyoPrecision, RenderMode
from phonon._scale import Scale
from phonon.binding import Mode
from phonon.score import Score, ScoreValidationError
from phonon.seedseq import derive
from phonon.version import __version__
from phonon.voice import Role

__all__ = [
    "Score",
    "ScoreValidationError",
    "Scale",
    "RenderMode",
    "PyoPrecision",
    "Mode",
    "Role",
    "derive",
    "__version__",
]
