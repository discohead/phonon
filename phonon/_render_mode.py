"""RenderMode and PyoPrecision enums.

Defined in Phase 0; consumed by the renderer in Phase 1+.
"""

from enum import Enum

__all__ = ["RenderMode", "PyoPrecision"]


class RenderMode(Enum):
    """How `Score.render(mode=...)` evaluates the piece."""

    AUTOPILOT = "autopilot"   # offline, no MIDI/OSC, deterministic
    LIVE      = "live"        # real-time backend, controllers active
    REPLAY    = "replay"      # offline, .gestures timeline drives gestures


class PyoPrecision(Enum):
    """Which Pyo extension module backs the Server."""

    SINGLE = "single"   # pyo._pyo (default)
    DOUBLE = "double"   # pyo._pyo64 (requires --use-double build)
