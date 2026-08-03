"""Voice — registers a piece's instrumental cast (role, band, source, entrance).

Phase 0 hosts the `Role` enum here (per design spec §17 module placement).
Substantive `Voice` dataclass lands in Phase 2.
"""

from enum import Enum

__all__ = ["Role"]


class Role(Enum):
    """A Voice's structural role in the piece (informs default band assignment)."""

    ANCHOR_LOW    = "anchor_low"
    AIR_HIGH      = "air_high"
    PRIMARY_MID   = "primary_mid"
    SECONDARY_MID = "secondary_mid"
    CUSTOM        = "custom"
