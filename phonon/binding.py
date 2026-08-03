"""Binding — connects a Trajectory's output to a Voice/source parameter.

Phase 0 hosts the `Mode` enum here (per design spec §17 module placement).
Substantive `Binding` dataclass lands in Phase 1.
"""

from enum import Enum

__all__ = ["Mode"]


class Mode(Enum):
    """How a Binding combines a Trajectory's value with the target parameter's base."""

    ABSOLUTE = "absolute"   # target.value = source.value
    OFFSET   = "offset"     # target.value = base + source.value
    MODULATE = "modulate"   # target.value = base * source.value
