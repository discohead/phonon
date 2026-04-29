"""
threshold_study_1.py — first piece in the framework.

A seven-minute study in two mid-voices passing through coupling.
The piece moves along a single supra trajectory `order` from chaos
toward synchronicity. Two structural events reshape topology as it
ascends; one captured motif returns near the end, distorted by the
local order value. Anchor (low) persists; secondary (mid) is
introduced by event; air (high) drifts on a brown random walk
biased by order.

Render modes:
    autopilot     defaults flow; the system performs itself
    live          MIDI/OSC controllers drive declared gestures
    replay        a recorded gesture timeline drives them

Author: Jared (composer) + Claude (scribe)
"""

from phonon import (
    Score, Voice, Role, Band, Coupling, CouplingKind,
    Trajectory, Variance, Crossing, Scale,
    Binding, Mode, Reference,
    Gesture, Midi,
    Event, IntroduceVoice, RewireCoupling,
    Persistence, Recurrence, Distortion,
    RenderMode, vdp, pink_noise, lorenz, brown, linear, sigmoid,
)


SEED = 1729


# ── Voices ────────────────────────────────────────────────────────

anchor = Voice(
    role=Role.ANCHOR_LOW,
    band=Band(20, 120),
    source=vdp(rate=2.13),  # van der Pol relaxation oscillator, ~128 BPM
)

air = Voice(
    role=Role.AIR_HIGH,
    band=Band(4000, 18000),
    source=pink_noise(),
)

primary = Voice(
    role=Role.PRIMARY_MID,
    band=Band(200, 2000),
    source=lorenz(component="x", rho=28),
)

secondary = Voice(
    role=Role.SECONDARY_MID,
    band=Band(300, 3000),
    source=lorenz(component="y", rho=15.5),
    entrance=Crossing(Reference("order"), value=0.30, rising=True),
)


# ── Trajectories ──────────────────────────────────────────────────

# Central control variable: 0 = chaos / decoupled, 1 = order / phase-locked.
order = Trajectory(
    name="order",
    scale=Scale.SUPRA,
    shape=sigmoid(start=0.15, end=0.70, midpoint=0.55),
    variance=Variance(0.04),
)

# Coupling strength at macro scale, reshaped by the supra trajectory.
# As `order` rises, the macro arc's curvature itself sharpens.
coupling_strength = Trajectory(
    name="coupling_strength",
    scale=Scale.MACRO,
    shape=linear(start=0.0, end=0.85),
    reshape_by=Reference("order"),
    variance=Variance(0.06),
)

# Air-band intensity at meso scale; brownian walk whose mean drifts
# toward the current value of `order` (less random as order rises).
air_intensity = Trajectory(
    name="air_intensity",
    scale=Scale.MESO,
    shape=brown(rate=0.05, amplitude=0.3),
    drift_toward=Reference("order"),
    variance=Variance(0.15),
)


# ── Couplings ─────────────────────────────────────────────────────

mid_pair = Coupling(
    a=primary,
    b=secondary,
    strength=Reference("coupling_strength"),
    kind=CouplingKind.PHASE,  # rewired to AMPLITUDE by event below
)


# ── Bindings ──────────────────────────────────────────────────────

bindings = [
    # ANCHOR_LOW and PRIMARY_MID expose `event_rate` per role contract.
    Binding(Reference("order"), anchor.event_rate,  mode=Mode.MODULATE),
    Binding(Reference("order"), primary.event_rate, mode=Mode.MODULATE),
    # AIR_HIGH exposes `intensity` per role contract.
    Binding(Reference("air_intensity"), air.intensity, mode=Mode.ABSOLUTE),
]


# ── Rhetoric ──────────────────────────────────────────────────────

# Anchor persists across all structural events; nothing dissolves it.
anchor_persistence = Persistence(voice=anchor)

# Capture a meso-scale fragment of `primary` from 1:20–1:50.
# After coupling has shifted, the fragment returns, distorted by
# whatever value `order` holds at the moment of return.
echoed_motif = Recurrence(
    capture=primary,
    window_seconds=(80, 110),
    scale=Scale.MESO,
    return_at=Crossing(Reference("order"), value=0.65, rising=True),
    distortion=Distortion(
        density_scale=Reference("order"),
        spectral_shift=1.05,
    ),
)


# ── Structural Events (closed, typed set) ─────────────────────────

events = [
    Event(
        when=Crossing(Reference("order"), value=0.55, rising=True),
        action=RewireCoupling(mid_pair, kind=CouplingKind.AMPLITUDE),
    ),
]


# ── Gestures (live input; defaults flow under autopilot) ──────────

warp = Gesture(
    name="warp",
    range=(-0.3, 0.3),
    default=0.0,
    mapping=Midi.cc(74, channel=1),
    target=Reference("order"),
    mode=Mode.OFFSET,
)

tighten = Gesture(
    name="tighten",
    range=(0.0, 1.0),
    default=0.0,
    mapping=Midi.cc(75, channel=1),
    target=Reference("coupling_strength").variance,
    mode=Mode.MODULATE,
)


# ── Score ─────────────────────────────────────────────────────────

score = Score(
    title="Threshold (study no. 1)",
    seed=SEED,
    duration_seconds=420,  # 7:00
    corpus=None,  # synthesis-only; no Sample() references
    voices=[anchor, air, primary, secondary],
    couplings=[mid_pair],
    trajectories=[order, coupling_strength, air_intensity],
    bindings=bindings,
    events=events,
    gestures=[warp, tighten],
    rhetoric=[anchor_persistence, echoed_motif],
    variance_defaults={
        Scale.SUPRA: 0.03,
        Scale.MACRO: 0.05,
        Scale.MESO:  0.10,
        Scale.MICRO: 0.20,
    },
)


if __name__ == "__main__":
    score.render(mode=RenderMode.AUTOPILOT, output="threshold_study_1.flac")
