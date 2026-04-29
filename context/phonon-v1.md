# Phonon

**A composition framework for continuous parametric processes, designed for human–agent collaboration.**

Version: v1 design specification
Author: Jared (composer) and Claude (collaborator)
Status: Design complete, implementation pending
License intent: Open source (license TBD)

---

## Table of contents

1. [Spirit and vision](#1-spirit-and-vision)
2. [Aesthetic foundations](#2-aesthetic-foundations)
3. [Core concepts](#3-core-concepts)
4. [Architecture overview](#4-architecture-overview)
5. [Time model](#5-time-model)
6. [The process primitive layer](#6-the-process-primitive-layer)
7. [Voices and role contracts](#7-voices-and-role-contracts)
8. [Trajectories](#8-trajectories)
9. [Couplings](#9-couplings)
10. [Bindings and references](#10-bindings-and-references)
11. [Rhetoric](#11-rhetoric)
12. [Structural events](#12-structural-events)
13. [Gestures](#13-gestures)
14. [Variance and determinism](#14-variance-and-determinism)
15. [The Score](#15-the-score)
16. [Render modes and performance artifacts](#16-render-modes-and-performance-artifacts)
17. [Module layout](#17-module-layout)
18. [Public API surface](#18-public-api-surface)
19. [Implementation notes](#19-implementation-notes)
20. [The Claude Code plugin](#20-the-claude-code-plugin)
21. [Non-goals](#21-non-goals)
22. [Phased implementation plan](#22-phased-implementation-plan)
23. [Open questions](#23-open-questions)
24. [Appendix A — Complete first piece](#24-appendix-a--complete-first-piece)
25. [Appendix B — Glossary](#25-appendix-b--glossary)

---

## 1. Spirit and vision

Phonon is a Python framework for composing experimental electronic music as **continuous parametric processes whose discrete consequences emerge from threshold conditions in the medium**. The framework's name is taken from physics: a phonon is the smallest unit of acoustic-mechanical vibration in a medium, and its wave–particle duality — continuous wave behavior, discrete events arising from threshold conditions — is the framework's metaphysics in miniature.

A piece in Phonon is not a pattern, a sequence, a loop, or a note list. A piece is a single Python file containing a `Score`: a seed, a corpus, a small set of voices, the couplings between them, the trajectories that govern parameter evolution across nested time scales, the bindings from trajectories to parameters, the closed set of typed structural events that reshape topology at threshold crossings, the gestures that allow live physical input, and a small rhetorical vocabulary for long-form work.

The framework is opinionated. It refuses song-form scaffolding, diatonic helpers, MIDI-file authoring, fixed-channel tracks, and event-list authoring APIs. It treats the listener as agnostic — it does not perform psychoacoustic shaping, perceptual weighting, or quality-of-life DSP that would tame the conditions under which the composer's intended phenomena arise. It is built from the ground up to be authored by a human composer in dialogue with a coding agent, primarily Claude Code; the API is designed for agent-readiness first and human-readability second, on the working hypothesis that what is good for an agent is also good for a human reading code months later.

Audio is rendered through Pyo. Phonon is a thin, opinionated abstraction over Pyo's signal graph that adds scale-aware time, role-bearing voices, hierarchical trajectory composition, and the rhetorical machinery long-form work needs.

### 1.1 Why this framework now

The composer comes to this framework after extended hardware-mediated work (Elektron Octatrack, Digitakt II, Analog Four MK2) and previous abstraction efforts (a Digitakt II agentic composition framework; a CLI DAW built on continuous dynamical systems; live coding studies in Sonic Pi against Curtis Roads' microsound theory and Mark Fell's pattern synthesis). Phonon synthesizes those threads into a system unburdened by hardware constraints, where the composer's opinions and aesthetic commitments provide the creative discipline that hardware previously imposed.

The hypothesis that motivates the work: pure software, when given sharp opinions and tight refusals, can produce music more fluidly and with less effort than hardware allows, and the agentic interface (Claude Code as primary author, the composer as listener-and-director) can produce volumes and depths of work that hands-on programming cannot match.

### 1.2 What success looks like

- A composer writes pieces in dialogue with Claude Code, in 80–150 lines per piece.
- A piece file is the composition. Diffs of the file are diffs of the composition.
- Rendering the same file with the same seed produces bit-identical audio.
- Rendering with a different seed produces a recognizable variant of the same piece.
- A listener can re-render any released piece on their own machine in a single command.
- Live performance and offline rendering use the same piece file, with no special-cased branching.
- The framework is small enough that a composer can read its source in a weekend and a senior engineer can audit it in a day.

---

## 2. Aesthetic foundations

The framework is designed to be good at what specific composers and traditions do well. The list is given here because every API decision should be checkable against it.

**Curtis Roads** — multiscale time, microsound, granular synthesis, the continuous evolution of grain clouds across nested temporal scales. The five-scale time model (sample, micro, meso, macro, supra) is taken directly from *Microsound* and *Composing Electronic Music*. The framework treats Roads' time scales as canonical and reflects them in the type system.

**Mark Fell** — pattern synthesis, productive constraints, irregular meters, the dialectic between algorithmic generation and timbral selection, non-teleological flat forms. The framework's coupling-and-variance machinery is shaped by Fell's pattern density work and his explicit interest in the threshold between texture and rhythm.

**Ryoji Ikeda** — pure tones, sine-wave clarity, microsound at extreme densities, the perceptual collapse of grain density into rhythm and back. The framework's bias toward simple sources and complex evolution is Ikeda-shaped.

**Alva Noto / Carsten Nicolai** — clicks, grids, the aesthetic of signal as material, the mathematical surface as composition.

**Curtis Roads' lineage in long-form continuous music**: Eliane Radigue (continuous tape evolution), Catherine Christer Hennix (long-duration psychoacoustic work), Roland Kayn (cybernetic music — continuous feedback systems with no human-imposed sectional structure). The long-form rhetorical primitives in §11 are designed to make this lineage tractable.

**Autechre** — late work especially, where structure emerges from the continuous evolution of dynamical systems and the listener's relationship to memory and recurrence is itself the rhetorical material.

The framework is **explicitly bad** at: verse-chorus song forms, tonal harmony, key-signature reasoning, melodic counterpoint in the traditional sense, music structured around a vocalist or melodic lead, anything that wants a click track.

### 2.1 The phenomenon being chased

The composer's stated goal is to listen for, and move toward, the perceptual phenomenon of "almost hearing something but not being sure, then losing it, then hearing it again" — the sense of patterns and presences that appear, dissolve, and recur in the listener's hearing as a coincidental byproduct of the system's behavior. This phenomenon is not designed into the system. It is the residue of the system being designed correctly. The framework's job is to make systems whose conditions favor it; it does not model or target it directly. No psychoacoustic modeling, no perceptual weighting, no smoothing DSP. The phenomenon belongs to the listener.

### 2.2 Voice topology

A piece is composed of four voices, organized roughly by frequency band:

- **anchor-low** — kick/bass; the floor; usually persistent across structural events.
- **air-high** — hi-hat/cymbal/air; stochastic high-frequency texture.
- **primary-mid** — one of two interactive mid voices.
- **secondary-mid** — the other; symmetric to primary, distinguished only by its place in the coupling declaration.

The four-voice topology is **default but not enforced**. A piece may use fewer voices, or define voices outside the standard roles via a generic `CUSTOM` role; the framework provides defaults for the four standard roles and treats them as the path of least resistance.

### 2.3 The chaos–synchronicity axis

The conceptual frame named by the composer: a continuous spectrum between chaos and synchronicity, complexity and simplicity, the unfolding of interconnected discrete processes whose interactions and emergent properties produce the listener's sense of pattern. This spectrum is canonical in the framework; pieces typically declare a single supra-scale trajectory named `order` (or equivalent) that drives coupling strengths, noise-to-signal ratios, and the variance of stochastic processes. Variance can itself be modulated, which lets the same piece be tight in early passages and loose in late ones, or vice versa.

---

## 3. Core concepts

This section is the high-level mental model. Subsequent sections specify each concept in detail.

| Concept | One-line definition |
|---|---|
| **Process** | A continuous signal source or transformation. |
| **Threshold** | A device that converts a continuous signal into discrete trigger events at crossings. |
| **SampleAndHold** | Latches a signal's value at trigger times into a held value. |
| **Voice** | A named carrier of sound with a role, a band, and a source process; bears a role-specific parameter contract. |
| **Coupling** | A declared relationship between two voices, with a kind (phase, amplitude, etc.) and a strength signal. |
| **Trajectory** | A control-rate signal living at a declared Roads scale, governing parameter evolution across that scale. |
| **Binding** | A connection from a source signal to a target parameter, under a mode (absolute, offset, modulate). |
| **Reference** | A first-class deferred reference to a named entity (typically a trajectory) by string name. |
| **Crossing** | A predicate that fires when a referenced signal crosses a value with declared direction. |
| **Event** | A structural change to the score, fired when its trigger condition becomes true. |
| **Rhetoric** | A small vocabulary of long-form structural primitives: Persistence, Recurrence, Departure, Quotation, Latency. |
| **Gesture** | A named external input slot (MIDI/OSC) bound to a parameter or trigger, with a default value. |
| **Score** | The whole piece: seed, corpus, voices, couplings, trajectories, bindings, events, rhetoric, gestures, variance defaults. |
| **Performance** | A specific render: `(score, seed, gesture_timeline | autopilot)` producing audio. |

The framework's central commitment, which all of the above serve: **a piece is a system whose continuous parametric evolution produces discrete musical consequences, and the same source code can produce a space of related performances.**

---

## 4. Architecture overview

```
                ┌────────────────────────────────────────┐
                │          Piece file (piece.py)         │
                │      Score: voices, trajectories,      │
                │     couplings, bindings, events,       │
                │     rhetoric, gestures, seed, corpus   │
                └────────────────────┬───────────────────┘
                                     │
                                     ▼
   ┌───────────────────────────────────────────────────────────┐
   │                    Phonon Core (Python)                   │
   │                                                           │
   │  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐  │
   │  │  Score      │ │  Reference   │ │  Renderer          │  │
   │  │  Validator  │→│  Resolver    │→│  Scheduler         │  │
   │  │             │ │ (build DAG)  │ │ (control-rate loop)│  │
   │  └─────────────┘ └──────────────┘ └─────────┬──────────┘  │
   │                                             │             │
   │  ┌─────────────────────────────────────────────────────┐  │
   │  │              Process Primitive Layer                │  │
   │  │   Process · Threshold · SampleAndHold · Binding     │  │
   │  └─────────────────────┬───────────────────────────────┘  │
   │                        │                                  │
   │  ┌─────────────────────▼───────────────────────────────┐  │
   │  │               Pyo (audio backend)                   │  │
   │  │      PyoObject graph · Server · MIDI · OSC          │  │
   │  └─────────────────────────────────────────────────────┘  │
   └───────────────────────────────────────────────────────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
        ┌──────────────┐     ┌──────────────┐    ┌───────────────┐
        │  Audio file  │     │  .gestures   │    │  Realtime     │
        │   (FLAC)     │     │  (timeline)  │    │  audio output │
        └──────────────┘     └──────────────┘    └───────────────┘
```

The renderer runs a control-rate loop. At each tick, it evaluates trajectories at the current piece-time (with seed-deterministic noise sampled from a per-trajectory RNG), writes parameter values to bindings, tests threshold-crossing predicates and fires structural events, and reads gesture inputs (live mode) or applies recorded gesture values (replay mode) or default values (autopilot mode). Pyo's audio graph runs continuously underneath; audio-rate processes inside voices generate their own samples without the control loop's involvement.

---

## 5. Time model

### 5.1 The five Roads scales

Phonon adopts Curtis Roads' multiscale time model exactly as he describes it. Five scales are first-class in the framework's type system:

| Scale | Range | Examples in this framework |
|---|---|---|
| `Scale.SAMPLE` | < 100µs | Audio-rate signal samples; not directly addressed in piece files. |
| `Scale.MICRO` | 100µs – 100ms | Grain-level processes; fast envelopes; click-rate phenomena. |
| `Scale.MESO` | 100ms – 5s | Gestures; phrases; short rhythmic figures. |
| `Scale.MACRO` | 5s – several minutes | Sectional shapes; arcs of density and timbre. |
| `Scale.SUPRA` | Whole piece duration | The piece's overall trajectory; the form. |

A `Trajectory` declares the scale at which it operates. The scale annotation determines:

- **Time normalization.** `Scale.SUPRA` trajectories run from `t=0` (piece start) to `t=1` (piece end). `Scale.MACRO` trajectories normalize to a macro window (default: piece duration; configurable). `Scale.MESO` and below normalize to phrase windows or to attached voice/event lifetimes.
- **Modulation eligibility.** Lower-scale trajectories may be modulated by higher-scale trajectories; the reverse is forbidden. This captures Roads' asymmetric multiscale claim and prevents ill-posed feedback in trajectory composition.
- **Default variance.** The Score declares a `variance_defaults` mapping from scale to default jitter level; trajectories without an explicit `variance` inherit from their scale.

### 5.2 Piece time vs. wall time

Pieces operate in **piece time**, a normalized clock from 0 to `duration_seconds`. The renderer maps piece time to wall time during real-time rendering and to sample positions during offline rendering. Piece time is what trajectories see; wall time is what audio sees; the framework hides the conversion entirely from the composer.

### 5.3 Control rate

Trajectories and bindings run at the framework's **control rate**, which defaults to 200 Hz (5ms per tick). This is configurable on the Score (`control_hz=200`), but the default is appropriate for all anticipated work. Voice sources run at audio rate inside Pyo; the control loop only writes parameters, never samples.

---

## 6. The process primitive layer

The primitive layer is what every higher-level concept in the framework is built from. Composers rarely touch it directly; agents working under the framework rarely need to either, because the role-bearing facades (Voice, Trajectory, etc.) cover the typical surface. But the primitive layer is the framework's contract with Pyo and the foundation on which everything else is implemented.

### 6.1 Process

```python
class Process:
    """A continuous signal source or transformation.

    Wraps a PyoObject with framework metadata: rate, scale, and a
    seeded RNG (for stochastic processes). Has a single output signal
    addressable as `process.output`. Parameters are themselves
    Reference-able and modulatable.
    """
    rate: Rate           # Rate.AUDIO or Rate.CONTROL
    scale: Scale         # Scale.SAMPLE through Scale.SUPRA
    output: Signal       # The process's output value (sampleable)
    parameters: dict[str, Parameter]
    rng: Random          # Per-process seeded RNG, derived from Score seed
```

Concrete process subclasses:

**Generators (signal-producing):**

- `vdp(rate)` — van der Pol relaxation oscillator; produces pulse-like output suitable for clock-like roles.
- `lorenz(component, rho)` — Lorenz attractor; component is `"x"`, `"y"`, or `"z"`; produces continuous chaotic signal.
- `rossler(...)`, `chua(...)` — additional chaotic attractors.
- `pink_noise()`, `white_noise()`, `brown_noise()` — stochastic generators.
- `sine(freq)`, `saw(freq)`, `triangle(freq)` — periodic oscillators.
- `logistic_map(r)` — discrete chaotic generator at control rate.

**Transformations (signal-consuming):**

- `follower(source, attack, release)` — amplitude follower.
- `derivative(source)` — first derivative of a signal.
- `lowpass(source, cutoff)`, `highpass(source, cutoff)` — filters.
- `delay(source, time, feedback)` — fixed delay line.

**Sampler:**

- `Sample(corpus_key)` — references a sample by key in the Score's corpus block.

All process constructors return Process objects. They are pure data until the Score is rendered; the Pyo backing graph is built at render time.

### 6.2 Threshold

```python
class Threshold:
    """Converts a continuous signal into discrete trigger events.

    Fires a trigger when the source signal crosses `value` in the
    direction declared by `rising`. Hysteresis prevents jitter at the
    boundary; debounce prevents repeated fires within a window.
    """
    source: Reference | Process
    value: float
    rising: bool         # True = fires on upward crossings only
    hysteresis: float    # default: 0.01
    debounce_seconds: float  # default: 0.05
    trigger: Trigger     # The fired event stream
```

Thresholds are how rhythm, melody, and structural events arise from continuous flow. The framework uses Threshold internally for `Crossing` predicates on structural events, for voice entrance triggers, and for `Recurrence` return conditions.

### 6.3 SampleAndHold

```python
class SampleAndHold:
    """Latches a signal's value at trigger times into a held value.

    When `trigger` fires, samples `source` and holds the result on
    `output` until the next trigger.
    """
    source: Reference | Process
    trigger: Trigger
    output: Signal
```

SampleAndHold is how continuous signals become note-like material: drive a Threshold on a clock-like Process, attach SampleAndHold to a pitch-bearing Process, and the held output is a sequence of pitches.

### 6.4 Binding

```python
class Binding:
    """Connects a source signal to a target parameter, under a mode.

    On every control tick, computes the target's new value as
    `mode_apply(target.value, source.value)` and writes it.
    """
    source: Reference | Process | Signal
    target: Parameter
    mode: Mode           # Mode.ABSOLUTE, Mode.OFFSET, or Mode.MODULATE
    transform: Optional[Callable[[float], float]]  # rare; explicit escape hatch
```

Mode semantics:

- `Mode.ABSOLUTE` — target.value = source.value. The source replaces the target.
- `Mode.OFFSET` — target.value = base.value + source.value. The source is added to the target's underlying base value.
- `Mode.MODULATE` — target.value = base.value * source.value. The source multiplies the target.

The same `Mode` enum is used by `Binding` and `Gesture`. There is exactly one mode concept in the framework.

### 6.5 The Pyo mapping

Each primitive maps cleanly to Pyo:

- `Process.output` wraps a PyoObject. For audio-rate processes, the object is a `PyoObject` such as `Sine`, `Noise`, `SuperSaw`. For control-rate processes, it's typically a `Linseg`, `Randi`, or custom PyoObject subclass.
- `Threshold` uses `Compare` + `Trig` + (for hysteresis) a small `Sig` state machine. Debounce is enforced by the framework's scheduler, not Pyo, because debounce semantics need access to piece time.
- `SampleAndHold` uses `TrigVal`.
- `Binding` is implemented in the framework's control loop, not in Pyo; on each control tick the loop reads `source.value` and writes to `target.value` (which itself is a `Sig` or `SigTo` PyoObject under the hood for click-free parameter changes).

### 6.6 The control loop

A single Python control loop runs at `Score.control_hz` (default 200 Hz). On each tick:

1. Advance piece time.
2. Evaluate all trajectories at current piece time. Stochastic trajectories sample from their per-trajectory seeded RNG.
3. Resolve all `Reference` lookups against the current trajectory values.
4. Apply all bindings (write parameter values into Pyo `Sig` objects).
5. Test all Threshold-based crossing predicates (events, voice entrances, rhetoric returns); fire any whose conditions newly became true.
6. Read gesture inputs (live mode) or apply recorded values (replay mode); apply gesture-bound bindings.
7. Record gesture changes (live mode, change-point compression).

The loop is single-threaded, deterministic given seed and gesture timeline, and produces a complete dependency graph that the framework can serialize for `Score.describe()`.

---

## 7. Voices and role contracts

### 7.1 The Voice type

```python
class Voice:
    role: Role
    band: Band                    # frequency window of typical activity
    source: Process | Sample      # synthesis or sampled material
    entrance: Optional[Crossing]  # voice-local lifecycle: when this voice becomes present
    name: Optional[str]           # for Reference resolution; auto-generated if absent
    # role-specific parameters exposed via attribute access; see §7.3
```

A voice has a role (its place in the mix), a band (where in the spectrum it normally lives), and a source (where its signal comes from). Voice entrance is voice-local: a voice with `entrance=Crossing(...)` is `present=False` until the crossing fires, then becomes `present=True` and is mixed thereafter. Voices without an `entrance` field are present from `t=0`.

### 7.2 Roles

```python
class Role(Enum):
    ANCHOR_LOW    = "anchor_low"
    AIR_HIGH      = "air_high"
    PRIMARY_MID   = "primary_mid"
    SECONDARY_MID = "secondary_mid"
    CUSTOM        = "custom"     # escape hatch; forfeits role-specific parameters
```

The four canonical roles. `CUSTOM` is the escape hatch for pieces that need a voice outside the standard topology; CUSTOM voices expose only the universal parameters (§7.3).

### 7.3 The role contract

Every voice exposes a **universal parameter set**:

| Parameter | Type | Range | Semantics |
|---|---|---|---|
| `band` | Band | Hz × Hz | Frequency window; `band.center`, `band.width` are themselves modulatable. |
| `gain` | Parameter | 0.0 to 1.0 | Linear amplitude. |
| `position` | Parameter | -1.0 to 1.0 | Stereo position. |
| `intensity` | Parameter | 0.0 to 1.0 | Overall presence/loudness; multiplies gain in the mix. |

Each non-CUSTOM role extends the universal set with **role-specific parameters**:

**`ANCHOR_LOW`** (event-driven percussion):

| Parameter | Type | Range | Semantics |
|---|---|---|---|
| `event_rate` | Parameter | 0.5 to 8.0 Hz | Trigger rate; pulses per second. |
| `event_decay` | Parameter | 0.01 to 2.0 s | Per-pulse decay time. |
| `event_jitter` | Parameter | 0.0 to 1.0 | Timing variance; 0 is metric, 1 is fully randomized. |
| `tone` | Parameter | 0.0 to 1.0 | Body-vs-click balance; 0 is pure body, 1 is pure click. |

**`AIR_HIGH`** (continuous stochastic texture):

| Parameter | Type | Range | Semantics |
|---|---|---|---|
| `grain` | Parameter | 0.0 to 1.0 | Particle-size character; 0 is smooth, 1 is crackly. |
| `motion` | Parameter | 0.0 to 1.0 | Internal modulation depth. |

**`PRIMARY_MID` and `SECONDARY_MID`** (interactive mid voices, identical contracts):

| Parameter | Type | Range | Semantics |
|---|---|---|---|
| `event_rate` | Parameter | 0.0 to 16.0 Hz | Trigger rate when sampled-and-held. |
| `event_decay` | Parameter | 0.01 to 2.0 s | Per-event decay. |
| `pitch_center` | Parameter | 80 to 4000 Hz | Central pitch around which events cluster. |
| `pitch_spread` | Parameter | 0.0 to 1.0 | Spread of pitch around center; 0 is fixed, 1 is full octave. |

The role contract is the framework's contract with composers. Role parameters are stable across versions; new parameters may be added but existing ones may not be renamed or have their semantics changed without a major version bump.

### 7.4 Reference resolution from voices

A voice's parameters are addressable via attribute access for use in `Binding.target`:

```python
Binding(Reference("order"), anchor.event_rate, mode=Mode.MODULATE)
```

Voice parameter access returns a Parameter object whose `target` semantics are well-defined. Reading a Voice parameter from a Reference (e.g., `Reference("anchor.event_rate")`) is also supported and is the form an agent will typically generate.

---

## 8. Trajectories

### 8.1 The Trajectory type

```python
class Trajectory:
    name: str
    scale: Scale
    shape: Shape                       # the trajectory's deterministic shape
    variance: Optional[Variance]       # stochastic jitter; defaults to scale-level
    reshape_by: Optional[Reference]    # higher-scale trajectory that reshapes this one
    drift_toward: Optional[Reference]  # for stochastic shapes: bias mean toward referenced value
    output: Signal                     # the trajectory's current value
```

A trajectory is a control-rate signal living at a declared Roads scale. It produces a value at every control tick, computed as:

```
value(t) = shape.evaluate(normalized_t, reshape_params(t)) + variance.sample(t, rng) + drift_offset(t)
```

where `reshape_params(t)` is computed from `reshape_by`'s current value, `drift_offset(t)` is computed from `drift_toward`'s current value, and `variance.sample(t, rng)` draws jitter from the trajectory's seeded RNG.

### 8.2 Shapes

Shapes are declarative descriptions of deterministic curves:

- `linear(start, end)` — straight line from start to end across the trajectory's scale window.
- `sigmoid(start, end, midpoint=0.5, slope=1.0)` — S-curve.
- `exponential(start, end, base=2.71)` — exponential approach.
- `brown(rate, amplitude)` — brownian random walk; deterministic given seed and `rate` parameters but visually stochastic.
- `pink(rate, amplitude)` — 1/f noise walk.
- `arc(start, peak, end, peak_at=0.5)` — rises to peak, falls to end.
- `step(value)` — constant.
- `composite(segments)` — concatenation of shapes across the scale window.

Shapes are pure data; they expose `.evaluate(t_normalized, **reshape_params)` returning a float. Shape parameters are themselves Reference-able, which is how `reshape_by` is implemented: the source trajectory's value is passed in as `reshape_params` at every tick.

### 8.3 Variance

```python
class Variance:
    amount: float                      # 0.0 = deterministic, 1.0 = max jitter
    correlation: Optional[float]       # autocorrelation; default 0.5
    distribution: Distribution         # default GAUSSIAN
```

Variance is per-trajectory with **scale-level defaults flowing downward**. The Score declares `variance_defaults: dict[Scale, float]`; trajectories without an explicit `variance` field inherit the default for their scale.

Crucially, variance can itself be modulated. A binding that targets `Reference("trajectory_name").variance` allows a gesture or another trajectory to reshape the jitter level over time. This is how a piece can be tight in early sections and loose in late ones, or vice versa, and is one of the framework's most musically distinctive capabilities.

### 8.4 Trajectory composition

Trajectories at lower scales may be reshaped or biased by trajectories at higher scales. Two mechanisms:

- **`reshape_by=Reference(...)`** — the source trajectory's value is passed into the target trajectory's shape as `reshape_params`. The target's shape parameters (slope, midpoint, peak position, etc.) are themselves driven. This is the mechanism by which the *character* of macro change is itself transformed across the piece.

- **`drift_toward=Reference(...)`** — for stochastic shapes (brown, pink), the random walk's mean is biased toward the source trajectory's current value. This is how a stochastic process can be made to "agree with" the global trajectory while preserving its randomness.

Both mechanisms are forbidden in the upward direction: a `Scale.SUPRA` trajectory cannot be reshaped by a `Scale.MESO` trajectory. The Score validator rejects such configurations at Score construction time.

---

## 9. Couplings

### 9.1 The Coupling type

```python
class Coupling:
    a: Voice
    b: Voice
    strength: Reference | Trajectory | float
    kind: CouplingKind  # PHASE, AMPLITUDE, FREQUENCY, RESPONSE
    name: Optional[str]
```

A coupling declares a relationship between two voices. The strength is a signal (typically a trajectory reference, sometimes a constant) that ranges 0 to 1, where 0 is decoupled and 1 is fully coupled. Couplings always exist for the duration of the piece once declared; their existence is not changed by structural events. Only their strength and kind can change.

### 9.2 Coupling kinds

```python
class CouplingKind(Enum):
    PHASE     = "phase"      # voice b's event timing tracks voice a's
    AMPLITUDE = "amplitude"  # voice b's intensity tracks voice a's
    FREQUENCY = "frequency"  # voice b's pitch_center tracks voice a's
    RESPONSE  = "response"   # voice b is triggered by voice a's events
```

The kind determines the mechanism of coupling. A `PHASE` coupling at strength 1 phase-locks the two voices' clocks; at strength 0, they run independently. An `AMPLITUDE` coupling makes voice b's intensity track voice a's. A `FREQUENCY` coupling makes pitch follow pitch. A `RESPONSE` coupling fires voice b's events whenever voice a's events fire — call-and-response.

Kind is mutable via `RewireCoupling` events; strength is continuously modulated through its bound signal.

### 9.3 Coupling defaults by role

The framework provides default eligibility rules, used for validation warnings (not hard errors):

- `PRIMARY_MID` ↔ `SECONDARY_MID` are eligible for all coupling kinds.
- `AIR_HIGH` may couple weakly (`AMPLITUDE`) to `PRIMARY_MID` or `SECONDARY_MID`.
- `ANCHOR_LOW` typically remains uncoupled; couplings involving it produce a validation warning but are not errors.

These are conventions, not constraints. CUSTOM-role voices have no default eligibility rules.

---

## 10. Bindings and references

### 10.1 Reference

`Reference` is a first-class deferred reference to a named entity in the Score by string name. References resolve at Score construction time (validation) and again at render time (live evaluation).

```python
class Reference:
    name: str  # e.g., "order", "anchor.event_rate", "coupling_strength.variance"
```

References are used everywhere a piece needs to point at a named entity declared elsewhere. The framework requires references-by-name (rather than direct object references) because:

- It allows the Score to be built from declarative, independently-defined fragments.
- It produces a complete static dependency graph that the framework can analyze without execution.
- It makes `Score.describe()` nearly free to implement.
- It is the form an agent will reliably generate.

The verbosity cost is real but acceptable; future versions may introduce a metaclass-based shorthand if usage data justifies it.

### 10.2 Reference paths

Reference paths support attribute access for nested addressing:

- `Reference("order")` — references the trajectory named `"order"`.
- `Reference("order").variance` — references the variance object on that trajectory.
- `Reference("anchor.event_rate")` — references the `event_rate` parameter on the voice named `"anchor"`.
- `Reference("mid_pair.strength")` — references the strength field on the coupling named `"mid_pair"`.

The Reference resolver walks the Score at construction time and validates that every Reference path resolves to a real entity.

### 10.3 Binding

See §6.4. Bindings are the bridge from Reference-resolved source values to target Parameter writes, governed by Mode.

---

## 11. Rhetoric

The rhetorical primitives are the framework's machinery for long-form structural work. They are built on top of the primitive layer and the trajectory system. Five primitives ship in v1.

### 11.1 Persistence

```python
class Persistence:
    voice: Voice
```

Declares that a voice is exempt from structural events that would dissolve it. Persistence is the drone primitive: a process that runs across multiple structural events, accumulating drift while its surrounding context changes. Anchor voices are typically given Persistence.

### 11.2 Recurrence

```python
class Recurrence:
    capture: Voice                  # voice to capture
    window_seconds: tuple[float, float]  # (start, end) of capture window in piece time
    scale: Scale                    # capture at this scale's resolution
    return_at: Crossing             # condition under which the captured material returns
    distortion: Distortion          # how to transform on return
```

Recurrence is the central rhetorical move in long-form work: a meso shape introduced once, and returning later, distorted by the current state of the piece. The framework records the captured voice's parameter timeline (at the declared scale's resolution) during the capture window, and replays it at the return condition with the distortion applied.

### 11.3 Departure

```python
class Departure:
    capture: Voice
    window_seconds: tuple[float, float]
    scale: Scale
```

Declares a meso shape (gesture, motif, density profile) that is introduced once and forbidden from returning. The framework enforces the constraint: any Recurrence or recurring pattern that would replay the captured material is rejected at Score validation time. Departure produces a particular kind of memory in the listener — something heard, gone, not-quite-mourned.

### 11.4 Quotation

```python
class Quotation:
    source: Reference     # trajectory whose past values are quotable
    history_seconds: float  # how far back to keep
    target: Reference     # trajectory that may sample from history
    sample_at: Crossing   # when target samples from history
```

Quotation is the past-self-as-material primitive. The source trajectory keeps a delay-line of its past values; at the sample_at condition, the target trajectory samples a value from the source's history. The depth of the sample is configurable. Quotation lets a piece reach back into its own past as raw material.

### 11.5 Latency

```python
class Latency:
    event: Event
    delay_seconds: float
```

Wraps a structural event with a delay. The event's trigger condition is evaluated normally, but its action is deferred by `delay_seconds`. This is the closest the framework comes to designing for the spooky-action phenomenon — a structural event fires now, the listener hears its consequences later, and the link between cause and effect is decoupled by design.

### 11.6 Distortion

Distortions describe how Recurrence transforms captured material on return. The vocabulary is closed; lambdas are not accepted.

```python
class Distortion:
    density_scale: Optional[float | Reference]  # multiply event rate
    spectral_shift: Optional[float | Reference]  # multiply pitch center
    intensity_scale: Optional[float | Reference]  # multiply intensity
    time_stretch: Optional[float | Reference]    # multiply playback duration
    reverse: bool = False                         # play backward
```

Each distortion field is either a constant or a Reference. The framework applies them at return time, evaluating any References against the current trajectory state.

---

## 12. Structural events

### 12.1 The Event type

```python
class Event:
    when: Crossing  # condition that fires this event
    action: Action  # one of the six closed-set actions below
    name: Optional[str]
```

Events fire when their `when` Crossing predicate transitions from false to true. Each event has an action drawn from the closed set defined below.

### 12.2 The closed action set (v1)

Six actions ship in v1. The set is closed but extensible by design — see §12.3.

```python
class DissolveVoice:
    voice: Voice

class RewireCoupling:
    coupling: Coupling
    kind: CouplingKind

class BindToTrajectory:
    source: Reference     # trajectory or signal
    target: Reference     # parameter to bind
    mode: Mode

class UnbindFromTrajectory:
    binding: Binding | str  # binding object or its name

class SwapCorpus:
    voice: Voice
    new_source: Process | Sample

class ShiftBand:
    voice: Voice
    new_band: Band
    glide_seconds: float = 0.0  # 0 = instant, >0 = glide
```

These cover the full v1 surface for topology mutation. Voice introduction is voice-local (`entrance` field on Voice). Coupling introduction/dissolution is handled by modulating coupling strength to/from 0 — couplings always exist when declared.

### 12.3 The closed-as-protocol pattern

The closed action set is implemented as a Protocol, not a sealed type:

```python
class Action(Protocol):
    def apply(self, score: ScoreState, time: float, rng: Random) -> None: ...
```

The six v1 actions implement this Protocol. They use only the public Score-mutation API. User-defined actions implement the same Protocol and slot in identically. The migration from "closed" to "open" is a documentation change. Discipline: keep the Protocol minimal and stable from day one; ensure v1 actions only use the public API.

### 12.4 Probabilistic firing

Events fire **probabilistically with seeded determinism**, not at exact threshold crossings. A Crossing predicate defines a *region* in which the event becomes eligible to fire; the event's per-event RNG (derived from the Score seed and the event's name) chooses the exact moment. The eligibility region is the threshold crossing plus a configurable jitter window (default: ±5% of the relevant scale's typical duration).

This design choice — agreed in conversation — makes a piece a *space of performances* rather than a single recording. Re-rendering with a different seed produces a structurally similar but not identical performance.

---

## 13. Gestures

### 13.1 The Gesture type

```python
class Gesture:
    name: str
    range: tuple[float, float]
    default: float
    mapping: GestureMapping  # Midi.cc, Midi.note, Osc.address
    target: Reference        # what the gesture drives
    mode: Mode               # default Mode.OFFSET
```

A gesture is a named external input slot. Gestures appear in the piece file alongside trajectories and voices. They exist in the Score whether or not anything is plugged in.

### 13.2 Mapping types

```python
class Midi:
    @staticmethod
    def cc(number: int, channel: int = 1) -> GestureMapping: ...
    @staticmethod
    def note(number: int, channel: int = 1) -> GestureMapping: ...

class Osc:
    @staticmethod
    def address(path: str, port: int = 8000) -> GestureMapping: ...
```

Mappings are typed factory methods that produce GestureMapping objects. They validate at construction and provide IDE completion.

### 13.3 Continuous and discrete gestures

A gesture is **continuous** if its range is a continuous interval (default). Continuous gestures modulate trajectories or parameters via their bound mode.

A gesture is **discrete** if its `target` is an Action rather than a parameter. Discrete gestures fire structural events when their input crosses a threshold (e.g., MIDI note on, OSC bang). Discrete gestures use the same closed action set as scheduled events; this means the typed action vocabulary serves double duty as the agent's compositional vocabulary and the performer's instrument.

### 13.4 Default mode and behavior

The default `mode` for a gesture is `Mode.OFFSET`. In autopilot mode, gestures take their `default` value (not modulating internal evolution); in live mode, the connected controller drives them; in replay mode, a recorded gesture timeline drives them.

### 13.5 Variance modulation

Gestures may target a trajectory's `variance` directly:

```python
tighten = Gesture(
    name="tighten",
    range=(0.0, 1.0),
    default=0.0,
    mapping=Midi.cc(75, channel=1),
    target=Reference("coupling_strength").variance,
    mode=Mode.MODULATE,
)
```

This lets the performer reshape the variance profile in real time — a deeply Fell-shaped capability and one that distinguishes Phonon's gesture model from typical performance-control schemes.

### 13.6 Recording fidelity

Live-mode gesture recording uses **change-point compression**: a value is logged only when it moves more than the gesture's `epsilon` (default: 0.01 of the gesture's range) from its last logged value. This makes recording size scale with performance activity, not duration. A 25-minute piece with mostly-stable gestures produces a small `.gestures` file; an active performance produces a larger one.

The `.gestures` file format is line-delimited JSON, one entry per change point: `{"time": 12.345, "name": "warp", "value": 0.123}`.

---

## 14. Variance and determinism

### 14.1 Bit-exact reproducibility

Given the same `(source, seed, gesture_timeline)`, Phonon produces bit-identical audio. This is non-negotiable. It requires:

- All randomness routed through seeded RNGs derived from the Score seed.
- No use of unseeded `random` or `numpy.random` anywhere in the framework.
- No wall-clock dependencies in piece logic (only piece time).
- Pyo offline rendering at fixed sample rate (default 48000) with deterministic block size.
- Thread ordering in the control loop: single-threaded.

The framework's test suite includes bit-exact reproducibility tests: render the same piece twice, compare audio file hashes.

### 14.2 RNG hierarchy

The Score seed is the root of an RNG hierarchy:

```
Score.seed
├── trajectory[name].rng   = derive(seed, name)
├── voice[name].rng        = derive(seed, name)
├── event[name].rng        = derive(seed, name)
└── coupling[name].rng     = derive(seed, name)
```

Each entity gets its own RNG derived from the seed and the entity's name (via a stable hash). This means changing a single trajectory's name does not change the random behavior of unrelated trajectories. The naming is the entity's identity for randomness purposes.

### 14.3 Per-trajectory variance with scale defaults

As specified in §8.3: variance is per-trajectory; trajectories without explicit variance inherit from the Score's `variance_defaults` mapping by scale. Variance can itself be a target of bindings (it is a Parameter with a base value and modulation surface).

### 14.4 Variance profile in Score.describe()

`Score.describe()` includes a per-trajectory variance summary, so the listener of a released piece can see at a glance how much different seeds will move the territory. This is the listener-facing paratext that supports the seed-modification ritual.

---

## 15. The Score

### 15.1 The Score type

```python
class Score:
    title: str
    seed: int
    duration_seconds: float
    corpus: Optional[Corpus]
    voices: list[Voice]
    couplings: list[Coupling]
    trajectories: list[Trajectory]
    bindings: list[Binding]
    events: list[Event]
    gestures: list[Gesture]
    rhetoric: list[Persistence | Recurrence | Departure | Quotation | Latency]
    variance_defaults: dict[Scale, float]
    control_hz: int = 200
    sample_rate: int = 48000
```

The Score is the single value that contains a complete piece. Construction validates References, checks for cycles, verifies role-contract conformance, and registers names for resolution.

### 15.2 Score validation

At construction time, the Score validator checks:

- All Reference paths resolve to real entities.
- Trajectory composition respects the scale-asymmetry rule (lower-scale may be reshaped by higher-scale, never the reverse).
- Departure constraints are respected (no Recurrence captures within Departure windows).
- All Voice role-parameter bindings target parameters that exist on the role's contract.
- All gesture mappings are unique (no two gestures bound to the same MIDI CC on the same channel).
- All event names are unique.

Validation failures raise `ScoreValidationError` with a precise message and the offending entity's name.

### 15.3 Score.describe()

Returns a structured human- and agent-readable summary:

```python
{
    "title": "Threshold (study no. 1)",
    "duration": "7:00",
    "seed": 1729,
    "voices": [
        {"name": "anchor", "role": "ANCHOR_LOW", "band": [20, 120], "persistent": true, ...},
        ...
    ],
    "trajectories": [
        {"name": "order", "scale": "SUPRA", "variance": 0.04, "shape": "sigmoid(0.15→0.70 @ 0.55)"},
        ...
    ],
    "events": [...],
    "gestures": [...],
    "rhetoric": [...],
    "variance_profile": {"SUPRA": 0.04, "MACRO": 0.06, "MESO": 0.15, "MICRO": 0.20},
}
```

`describe()` does not execute the piece; it walks the static graph. This is what an agent uses to reason about a piece before editing it.

### 15.4 Corpus

```python
class Corpus:
    samples: dict[str, SamplePath]
    manifest_hash: str  # content hash for release-artifact verification

class SamplePath:
    path: str
    hash: str  # SHA-256 of file content
```

A Corpus declares the sonic raw material of a piece by content-hashed manifest. Samples are referenced from voice sources via `Sample("key")`. Corpora are optional; synthesis-only pieces have `corpus=None`.

For release artifacts, the Corpus's manifest is bundled with the piece source so listeners can verify they have the same material as the original render.

---

## 16. Render modes and performance artifacts

### 16.1 Three render modes

```python
class RenderMode(Enum):
    AUTOPILOT = "autopilot"  # gestures take defaults; system performs itself
    LIVE      = "live"       # connected controllers drive gestures; record to .gestures
    REPLAY    = "replay"     # recorded .gestures file drives gestures
```

Same source file, three operating modes, no special-cased branching. The composer's piece file works in all three.

### 16.2 Performance

A Performance is a specific render of a Score:

```python
class Performance:
    score: Score
    seed: int                  # may differ from score.seed
    gesture_timeline: Optional[Path]  # .gestures file or None
    audio_path: Path
    rendered_at: datetime
    framework_version: str
```

Each performance is a `(seed, gesture_timeline)` pair plus its rendered audio. The released piece has identity in the source; performances are instances.

### 16.3 Release artifact format

A released piece is a directory:

```
threshold-study-1/
├── piece.py
├── corpus/                      # optional
│   ├── manifest.json
│   └── samples/
│       └── *.flac
├── README.md                    # composer's notes; describe() output appended
├── version.txt                  # framework version pin
└── performances/
    ├── performance-001/
    │   ├── seed.txt
    │   ├── gestures.jsonl       # optional, if live pass
    │   └── audio.flac
    └── performance-002/
        └── ...
```

The listener's command to re-render is:

```
phonon render piece.py --seed 1729                     # autopilot, base seed
phonon render piece.py --seed 4242                     # different seed
phonon render piece.py --seed 1729 --gestures performances/performance-001/gestures.jsonl
phonon render piece.py --live                          # live performance
```

### 16.4 The CLI

The `phonon` CLI exposes:

- `phonon render <piece.py> [--seed N] [--gestures FILE | --live] [--out PATH]`
- `phonon describe <piece.py>` — prints `Score.describe()` output as YAML.
- `phonon validate <piece.py>` — runs Score validation; reports errors.
- `phonon package <piece.py> --performances N` — builds a release-artifact directory.
- `phonon midi-list` — lists available MIDI inputs (for live mode setup).
- `phonon osc-listen [--port 8000]` — runs an OSC listener for live mode.

---

## 17. Module layout

The framework's public Python module structure:

```
phonon/
├── __init__.py              # re-exports the public API surface (§18)
├── score.py                 # Score, validation, describe
├── voice.py                 # Voice, Role, Band, role-contract enforcement
├── trajectory.py            # Trajectory, Variance, scale logic
├── coupling.py              # Coupling, CouplingKind
├── binding.py               # Binding, Reference, Mode
├── rhetoric.py              # Persistence, Recurrence, Departure, Quotation, Latency, Distortion
├── event.py                 # Event, Action protocol, six closed-set actions
├── gesture.py               # Gesture, Midi, Osc, GestureMapping
├── shape.py                 # linear, sigmoid, brown, pink, arc, step, composite
├── process/                 # process primitive layer
│   ├── __init__.py
│   ├── base.py              # Process, Threshold, SampleAndHold
│   ├── generators.py        # vdp, lorenz, rossler, chua, pink_noise, ...
│   ├── transforms.py        # follower, derivative, lowpass, highpass, delay
│   └── sample.py            # Sample, Corpus
├── render/                  # rendering and runtime
│   ├── __init__.py
│   ├── scheduler.py         # the control loop
│   ├── pyo_backend.py       # PyoObject construction from Process
│   ├── midi_io.py           # MIDI input/output via Pyo
│   ├── osc_io.py            # OSC input via Pyo
│   └── recorder.py          # gesture recording with change-point compression
├── cli/
│   ├── __init__.py
│   └── main.py              # phonon CLI entry point
└── version.py
```

### 17.1 The five user-facing modules

The framework's public surface is presented to composers and the agent through five "facade" categories that map to the modular-synth ontology while remaining thin layers over the primitives:

1. **Clocks** — Processes whose output crosses Thresholds at metric frequencies. `vdp(rate)` is the canonical example. Surface in `phonon.process.generators`.
2. **Modulators** — Trajectories. The dominant non-audio signal source.
3. **Sequencers** — SampleAndHold + Threshold compositions; pre-built sequencer factories live in `phonon.process` (e.g., `euclidean(steps, fills)`, `markov(transitions)`).
4. **Instruments** — Voices. The carriers of sound.
5. **Effects** — Process transformations (filters, delays, followers); applied via voice source composition or as post-voice processors.

These are roles that primitives play, exposed via convenient names. They are not separate type hierarchies. The five-module label is for the agent's vocabulary and the docs; the type system is the smaller primitive set.

---

## 18. Public API surface

The public top-level imports from `phonon` are:

```python
from phonon import (
    # Score
    Score, RenderMode,

    # Voice
    Voice, Role, Band,

    # Trajectory
    Trajectory, Variance, Scale,

    # Coupling
    Coupling, CouplingKind,

    # Binding
    Binding, Mode, Reference,

    # Rhetoric
    Persistence, Recurrence, Departure, Quotation, Latency, Distortion,

    # Events
    Event, Crossing,
    DissolveVoice, RewireCoupling, BindToTrajectory,
    UnbindFromTrajectory, SwapCorpus, ShiftBand,

    # Gestures
    Gesture, Midi, Osc,

    # Corpus
    Corpus, Sample,

    # Process generators (flat)
    vdp, lorenz, rossler, chua,
    sine, saw, triangle,
    pink_noise, white_noise, brown_noise,
    logistic_map,

    # Process transformations (flat)
    follower, derivative, lowpass, highpass, delay,

    # Shapes (flat)
    linear, sigmoid, exponential, brown, pink, arc, step, composite,
)
```

Flat imports are preferred. The public API is approximately 50 names; this is large enough to require organization in docs but small enough to fit in an agent's context comfortably.

---

## 19. Implementation notes

### 19.1 Pyo specifics

- **Server lifecycle**: the framework owns the Pyo `Server` lifecycle. Composers never instantiate Server directly. The renderer constructs the Server with appropriate parameters (offline mode for `phonon render --out`, real-time mode for live performances), starts it, runs the control loop, and shuts it down cleanly.
- **PyoObject lifetime**: PyoObjects must be kept alive for the duration of the render. The framework holds references in the renderer's state; composers should not need to manage object lifetime.
- **Audio vs control rate**: trajectories, bindings, and the control loop run at framework control rate (200 Hz). Voice sources and audio-signal-processing chains run at Pyo audio rate. The split is enforced by type: `Process.rate` is `Rate.AUDIO` or `Rate.CONTROL`.
- **MIDI mapping**: Pyo's `Notein`, `Midictl`, and friends are wrapped by the framework's gesture I/O. Composers never see Pyo MIDI directly.
- **SigTo for click-free parameter changes**: parameter writes from the control loop go through `SigTo` PyoObjects with a small interpolation time (default 5ms) to prevent zipper noise. This time is configurable per-parameter for cases where instant changes are desired.

### 19.2 Determinism specifics

- Use `random.Random(seed)` instances exclusively, never the module-level random.
- Avoid `numpy` random unless wrapped with explicit seeding via `numpy.random.Generator`.
- Pyo's offline rendering must use the same sample rate, buffer size, and number of channels every render.
- The control loop must be single-threaded.
- File I/O for sample loading must occur before the control loop starts (no I/O during render).

### 19.3 Performance considerations

- 200 Hz control rate × 50 trajectories × 100 bindings ≈ 1M evaluations per second. Modern CPUs handle this trivially; Python's overhead is the dominant cost. No vectorization is needed at v1.
- Real-time live mode should target sub-10ms gesture-to-audio latency. The 5ms control tick + Pyo's buffer (typically 256 samples = 5.3ms at 48kHz) ≈ 10ms total. Acceptable for studio work; tight for stage.
- Offline rendering of a 7-minute piece should complete in under 1 minute on a modern machine. M-series Macs in particular run Pyo offline rendering significantly faster than realtime.

### 19.4 Testing strategy

- Unit tests for each primitive (Process, Threshold, SampleAndHold, Binding) with deterministic inputs.
- Integration tests for full Score validation (positive and negative cases).
- Bit-exact reproducibility tests: render → hash → render → hash → assert equal.
- Snapshot tests for `Score.describe()` output.
- A small library of "canonical pieces" (5–10 short scores) used both as documentation and as integration tests.
- Property-based tests for trajectory composition (using Hypothesis): a reshape_by relationship should never produce out-of-range values.

---

## 20. The Claude Code plugin

### 20.1 Plugin structure

The `phonon-claude` plugin (working name) wraps Claude Code with framework-specific knowledge. It ships:

- **A primary skill** (`phonon-composer`) that teaches the agent the framework's vocabulary, conventions, and composer's aesthetic preferences. Includes the role contract reference, the closed event set, the rhetorical primitives, and a library of technique vignettes mapped to API patterns.
- **A scholar mode** (`phonon-scholar`) for explicit lineage citation: the agent identifies which artist's technique a proposed move evokes ("this is a Fell-shaped density gradient"; "this is a Radigue-shaped persistence over slow harmonic drift"). The scholar mode is the primary identity; scribe and analyst are supporting modes.
- **A scribe mode** for rapid translation of intent to code without deep citation.
- **An analyst mode** that reads existing pieces and explains their structure (using `Score.describe()` plus framework knowledge).
- **A `/phonon:new` command** that scaffolds a new piece file from a brief description.
- **A `/phonon:render` command** that runs `phonon render` on the current piece and reports the audio output path.
- **A `/phonon:capture` command** that promotes the current ephemeral piece to a saved composition with a name.
- **Hooks** that validate piece files on save, reporting Score validation errors as actionable feedback.
- **Subagents** for specialized tasks: a `voice-designer` for sketching new voice configurations, a `trajectory-shaper` for proposing trajectory shapes given an intent, an `event-choreographer` for proposing structural event placement on the supra trajectory.

### 20.2 The composer's mental model document

Inside the plugin, a `composer-model.md` document captures the composer's mental model, aesthetic preferences, and stated influences. It is loaded into the agent's context for every session under the plugin. It includes:

- The aesthetic foundations from §2.
- The voice topology defaults from §2.2.
- The chaos–synchronicity framing from §2.3.
- A list of named lineages and what each is good at.
- A list of explicit refusals (the framework's non-goals; see §21).
- Examples of phrases that should map to which framework concepts.

### 20.3 Technique vignettes

The plugin ships a library of technique vignettes, each a short prose-plus-code passage demonstrating an API pattern in service of an aesthetic move. Examples:

- "Fell-shaped pattern density modulation": Trajectory at MESO scale with brown shape, drift_toward a SUPRA trajectory; bound to event_rate on a mid voice.
- "Ikeda-shaped grain-to-rhythm collapse": A continuous AIR_HIGH voice's grain parameter modulated by a Trajectory crossing a threshold around 0.5 — below threshold, perceived as texture; above, perceived as rhythm.
- "Radigue-shaped supra drone": A persistent ANCHOR_LOW voice with very low event_rate, intensity slowly rising via a SUPRA-scale trajectory over the full piece duration.
- "Autechre-shaped late-form recurrence": A meso-window Recurrence captured early, returning under a high-order condition with significant Distortion.

The vignettes are both documentation and few-shot examples for the agent.

---

## 21. Non-goals

These are the framework's explicit refusals. Each is a creative commitment.

1. **No song-form scaffolding.** No verse/chorus/bridge primitives. No section-marking abstractions beyond the supra trajectory and structural events.
2. **No diatonic/key-signature helpers.** Pitch is in Hz. Composers who want diatonic structure can compute it in Python; the framework will not help.
3. **No MIDI-file authoring.** The framework does not export MIDI files for use in DAWs. Audio is the output.
4. **No fixed-channel "tracks".** Voices are the unit. A voice has a role and a band; it does not have a track number.
5. **No event-list authoring.** Pieces are not lists of timed events. Events emerge from threshold crossings on trajectories.
6. **No psychoacoustic modeling.** No perceptual weighting, masking-aware density, or listener-targeting DSP.
7. **No automatic loudness normalization or mastering.** Composers handle final-stage processing externally.
8. **No undo/redo machinery.** The piece file is the history; git is the undo.
9. **No GUI.** The framework is a Python library plus CLI. The composer's editor is their text editor; the agent's interface is Claude Code. Future tooling may layer GUI affordances on top, but the core has none.
10. **No real-time JIT pattern editing.** Hot-reload of piece files is supported, but the framework does not provide a separate live-coding-style pattern manipulation surface. All edits go through the source file.

---

## 22. Phased implementation plan

The framework is built in five phases. Each phase produces a runnable, testable artifact.

### Phase 0 — Skeleton (1 week)

- Repository setup, packaging, CI.
- Module skeleton (empty modules, type stubs).
- Score validator (validation logic with no rendering).
- `Score.describe()` returning correct YAML for an empty score.
- Test infrastructure.

### Phase 1 — Process primitive layer (2–3 weeks)

- `Process`, `Threshold`, `SampleAndHold`, `Binding`, `Reference`, `Mode`.
- Pyo backend: PyoObject construction from Process; control loop skeleton.
- Determinism infrastructure: seeded RNG hierarchy.
- A handful of generators (vdp, lorenz, pink_noise, sine) and one transformation (lowpass).
- A handful of shapes (linear, sigmoid, brown).
- Manual test: a Python script that uses the primitive layer to produce 30 seconds of audio.

### Phase 2 — Voices, trajectories, couplings (2–3 weeks)

- `Voice` with role-contract enforcement for the four roles plus CUSTOM.
- `Trajectory` with `reshape_by` and `drift_toward`, scale-asymmetry validation.
- `Coupling` with the four kinds.
- `Binding` integration with the control loop.
- Variance with scale defaults.
- Render `threshold_study_1.py` (Appendix A) end-to-end in autopilot mode.
- Bit-exact reproducibility test passes.

### Phase 3 — Events, gestures, rhetoric (2–3 weeks)

- `Event` with the six v1 actions.
- Probabilistic firing with seeded jitter.
- `Gesture` with MIDI and OSC mappings.
- Three render modes: autopilot, live, replay.
- Change-point gesture recording.
- The five rhetorical primitives.
- Render `threshold_study_1.py` in all three modes.

### Phase 4 — CLI, packaging, plugin (2–3 weeks)

- `phonon` CLI with all subcommands.
- Release-artifact packaging.
- The Claude Code plugin: skill, scholar/scribe/analyst modes, slash commands, hooks, subagents.
- Composer-model document and technique vignettes library.
- Documentation site.

Total: 9–13 weeks for a fully working v1, single developer (with Claude Code as primary coder).

---

## 23. Open questions

These are decisions deferred to implementation or to a future revision.

### 23.1 Should `Reference("name")` have a shorthand?

The Reference verbosity is real but acceptable. Future revision may explore module-level capture (declare a trajectory at top-level and have its name auto-bind as a Reference) via metaclass or import-hook trickery. v1 ships with explicit `Reference("name")`.

### 23.2 Sample manipulation primitives

Phase 1's process primitive layer covers synthesis but treats `Sample` as a leaf. Pieces that want fine-grained sample manipulation (granular re-synthesis from a sample, time-stretch, pitch-shift) need additional primitives. v1 ships a basic `Sample` reference with simple playback; richer sample manipulation is v1.5 territory.

### 23.3 Multi-channel audio

v1 is stereo (2 channels). Multi-channel output (quad, 5.1, ambisonic) is feasible and cheap to add but not v1. Pieces declared with `Voice.position` continue to work; the channel mapping changes.

### 23.4 Distributed rendering

Long-form 25-minute pieces with many voices may exceed a single machine's offline render budget. Distributed rendering across multiple machines is feasible (the control loop is deterministic; segments can be rendered independently and concatenated) but not v1.

### 23.5 Live-coding-style hot-swap

The framework supports re-running a piece file from scratch but does not (in v1) support hot-swapping individual trajectories, voices, or events while a piece is rendering. This is a substantial implementation effort and is deferred. Current live workflow: edit, save, re-run.

### 23.6 What the long-form work demands beyond v1

The composer indicated long-form 20–30 minute work feels conceptually different from standard 6–10 minute work, and may become more frequent under this framework. v1's hierarchical trajectory composition and rhetorical primitives are designed to support long-form work, but the actual demands will only become clear after several long pieces are written. v2 likely revisits the rhetorical primitive set with whatever the long-form practice teaches.

### 23.7 Visual feedback during composition

A static or animated visualization of trajectories, threshold crossings, and event firings would significantly aid the composer's intuition for what a piece is doing. v1 ships text-only; a `phonon viz piece.py` command producing an HTML or SVG timeline view is a v1.5 candidate.

---

## 24. Appendix A — Complete first piece

The first piece written against this design — `threshold_study_1.py` — is included in full as both an exercise in the API and a test artifact for the implementation. It exercises every v1 primitive in roughly the simplest configuration that does so: four voices, one coupling, three trajectories at three scales, one structural event, two gestures (one offset-mode and one variance-modulating), one Persistence, one Recurrence. Synthesis-only (no corpus). Seven minutes, autopilot-ready.

```python
"""
threshold_study_1.py — first piece in the framework.

A seven-minute study in two mid-voices passing through coupling.
The piece moves along a single supra trajectory `order` from chaos
toward synchronicity. One structural event reshapes coupling kind as
it ascends; one captured motif returns near the end, distorted by
the local order value. Anchor (low) persists; secondary (mid) is
introduced by entrance; air (high) drifts on a brown random walk
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
    Event, RewireCoupling,
    Persistence, Recurrence, Distortion,
    RenderMode, vdp, pink_noise, lorenz, brown, linear, sigmoid,
)


SEED = 1729


# ── Voices ────────────────────────────────────────────────────────

anchor = Voice(
    name="anchor",
    role=Role.ANCHOR_LOW,
    band=Band(20, 120),
    source=vdp(rate=2.13),
)

air = Voice(
    name="air",
    role=Role.AIR_HIGH,
    band=Band(4000, 18000),
    source=pink_noise(),
)

primary = Voice(
    name="primary",
    role=Role.PRIMARY_MID,
    band=Band(200, 2000),
    source=lorenz(component="x", rho=28),
)

secondary = Voice(
    name="secondary",
    role=Role.SECONDARY_MID,
    band=Band(300, 3000),
    source=lorenz(component="y", rho=15.5),
    entrance=Crossing(Reference("order"), value=0.30, rising=True),
)


# ── Trajectories ──────────────────────────────────────────────────

order = Trajectory(
    name="order",
    scale=Scale.SUPRA,
    shape=sigmoid(start=0.15, end=0.70, midpoint=0.55),
    variance=Variance(0.04),
)

coupling_strength = Trajectory(
    name="coupling_strength",
    scale=Scale.MACRO,
    shape=linear(start=0.0, end=0.85),
    reshape_by=Reference("order"),
    variance=Variance(0.06),
)

air_intensity = Trajectory(
    name="air_intensity",
    scale=Scale.MESO,
    shape=brown(rate=0.05, amplitude=0.3),
    drift_toward=Reference("order"),
    variance=Variance(0.15),
)


# ── Couplings ─────────────────────────────────────────────────────

mid_pair = Coupling(
    name="mid_pair",
    a=primary,
    b=secondary,
    strength=Reference("coupling_strength"),
    kind=CouplingKind.PHASE,
)


# ── Bindings ──────────────────────────────────────────────────────

bindings = [
    Binding(Reference("order"), anchor.event_rate,  mode=Mode.MODULATE),
    Binding(Reference("order"), primary.event_rate, mode=Mode.MODULATE),
    Binding(Reference("air_intensity"), air.intensity, mode=Mode.ABSOLUTE),
]


# ── Rhetoric ──────────────────────────────────────────────────────

anchor_persistence = Persistence(voice=anchor)

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


# ── Structural events (closed, typed set) ─────────────────────────

events = [
    Event(
        name="rewire_to_amplitude",
        when=Crossing(Reference("order"), value=0.55, rising=True),
        action=RewireCoupling(mid_pair, kind=CouplingKind.AMPLITUDE),
    ),
]


# ── Gestures ──────────────────────────────────────────────────────

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
    duration_seconds=420,
    corpus=None,
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
```

---

## 25. Appendix B — Glossary

| Term | Definition |
|---|---|
| **Action** | The mutation performed when a structural event fires. Six v1 actions form a closed set implementing a public Protocol. |
| **Anchor** | The ANCHOR_LOW voice; the floor of a piece; usually given Persistence. |
| **Band** | A frequency window declared on a voice; both center and width are modulatable parameters. |
| **Binding** | A connection from a source signal to a target parameter, governed by Mode. |
| **Control rate** | The rate at which trajectories, bindings, and the scheduler loop execute (default 200 Hz). |
| **Corpus** | A content-hashed manifest of sample material used by a piece. |
| **Coupling** | A declared relationship between two voices, with a strength signal and a kind. |
| **Crossing** | A predicate that fires when a referenced signal crosses a value with declared direction. |
| **Distortion** | A closed vocabulary of transformations applied to recurrent material on return. |
| **Event** | A structural change to the score, triggered by a Crossing. |
| **Gesture** | A named external input slot (MIDI/OSC) bound to a parameter or action. |
| **Mode** | The relationship between a source value and a target value: ABSOLUTE, OFFSET, or MODULATE. |
| **Performance** | A specific render: `(score, seed, gesture_timeline)`. |
| **Phonon** | The framework. Also: the smallest unit of acoustic-mechanical vibration in a medium. |
| **Process** | A continuous signal source or transformation, wrapping a PyoObject. |
| **Reference** | A first-class deferred reference to a named entity by string name. |
| **Rhetoric** | The five long-form primitives: Persistence, Recurrence, Departure, Quotation, Latency. |
| **Role** | A voice's place in the mix: ANCHOR_LOW, AIR_HIGH, PRIMARY_MID, SECONDARY_MID, or CUSTOM. |
| **Scale** | A Roads time scale: SAMPLE, MICRO, MESO, MACRO, or SUPRA. |
| **Score** | The complete piece value: seed, voices, trajectories, couplings, bindings, events, gestures, rhetoric, variance defaults. |
| **Shape** | A declarative description of a deterministic curve (linear, sigmoid, brown, etc.). |
| **Threshold** | A device that converts a continuous signal into discrete trigger events at crossings. |
| **Trajectory** | A control-rate signal living at a declared scale, governing parameter evolution across that scale. |
| **Variance** | Per-trajectory stochastic jitter, with scale-level defaults flowing downward. |
| **Voice** | A named carrier of sound: role, band, source, role-specific parameter contract. |

---

*End of design specification.*
