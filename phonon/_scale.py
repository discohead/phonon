"""Scale enum — Roads' five-scale temporal hierarchy.

Per Constitution IV (Roads' multiscale time is canonical) and design spec §15.1.
Lives in a private module to avoid forcing `phonon.trajectory` to import on `from phonon import Scale`.
"""

from enum import Enum

__all__ = ["Scale"]


class Scale(Enum):
    """Composer-addressable temporal scales (Roads, *Microsound* §1)."""

    SAMPLE = "sample"   # < 100 µs   (audio rate; not directly addressed in pieces)
    MICRO  = "micro"    # 100 µs – 100 ms
    MESO   = "meso"     # 100 ms – 5 s
    MACRO  = "macro"    # 5 s – several minutes
    SUPRA  = "supra"    # whole-piece duration
