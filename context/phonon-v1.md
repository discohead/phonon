# Phonon

**A composition framework for continuous parametric processes, designed for human–agent collaboration.**

Version: v1.1 design specification (revised against vendored Pyo 1.0.6, 2026-04-28)
Author: Jared (composer) and Claude (collaborator)
Status: Design complete, implementation pending
License: MIT for Phonon's own source (`LICENSE`); LGPLv3+ retained on vendored Pyo at `pyo-src/`. Built artifacts that bundle Pyo binaries must honor LGPL's relink obligation (see `LICENSE` for details).

---

## Revision note

v1.0 was authored before reading Pyo's source. v1.1 is the same design audited section-by-section against `pyo-src/` (cloned from `belangeo/pyo` at tag 1.0.6, 2025-03-04) and corrected in three large ways:

1. **Pyo has no separate control rate.** Every `PyoObject` runs at audio rate; Phonon's "control rate" is a framework convention enforced by an external scheduler, not a Pyo capability. The architecture and primitive-layer sections are revised to reflect this.
2. **Pyo's stock random objects are not bit-exact reproducible.** They share a single process-global LCG that mutates per sample, with no per-object seed isolation. Phonon's bit-exact promise requires replacing every stochastic Pyo object with seeded surrogates (table-driven from a numpy seeded RNG). A new §14 elaborates the surrogate strategy and §17 adds the `phonon.dsp.randoms_seeded` module to the layout.
3. **Pyo's "manual" audio backend is the deterministic-rendering primitive.** `Server(audio="manual")` plus `Server.process()` lets the host pump audio block-by-block. This is the canonical offline-render and test-fixture mode and is now the rendering substrate Phonon's scheduler is built on. Real-time live mode uses `audio="portaudio"`/`"jack"`/`"coreaudio"` and gives up bit-exactness.

Smaller corrections are inline. A new Appendix C is the verified Pyo class reference. Appendix D is the source-vendoring policy.

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
26. [Appendix C — Verified Pyo class reference](#26-appendix-c--verified-pyo-class-reference)
27. [Appendix D — Source vendoring policy](#27-appendix-d--source-vendoring-policy)

---

## 1. Spirit and vision

Phonon is a Python framework for composing experimental electronic music as **continuous parametric processes whose discrete consequences emerge from threshold conditions in the medium**. The framework's name is taken from physics: a phonon is the smallest unit of acoustic-mechanical vibration in a medium, and its wave–particle duality — continuous wave behavior, discrete events arising from threshold conditions — is the framework's metaphysics in miniature.

A piece in Phonon is not a pattern, a sequence, a loop, or a note list. A piece is a single Python file containing a `Score`: a seed, a corpus, a small set of voices, the couplings between them, the trajectories that govern parameter evolution across nested time scales, the bindings from trajectories to parameters, the closed set of typed structural events that reshape topology at threshold crossings, the gestures that allow live physical input, and a small rhetorical vocabulary for long-form work.

The framework is opinionated. It refuses song-form scaffolding, diatonic helpers, MIDI-file authoring, fixed-channel tracks, and event-list authoring APIs. It treats the listener as agnostic — it does not perform psychoacoustic shaping, perceptual weighting, or quality-of-life DSP that would tame the conditions under which the composer's intended phenomena arise. It is built from the ground up to be authored by a human composer in dialogue with a coding agent, primarily Claude Code; the API is designed for agent-readiness first and human-readability second, on the working hypothesis that what is good for an agent is also good for a human reading code months later.

Audio is rendered through Pyo. Pyo's source is **vendored into the repository at `pyo-src/`** (see Appendix D); Phonon may patch, extend, or replace specific Pyo components as the design warrants, and any such modifications live as commits on the vendored copy rather than monkey-patches at runtime. Phonon is a thin, opinionated abstraction over Pyo's signal graph that adds scale-aware time, role-bearing voices, hierarchical trajectory composition, deterministic stochastic processes, and the rhetorical machinery long-form work needs.

### 1.1 Why this framework now

The composer comes to this framework after extended hardware-mediated work (Elektron Octatrack, Digitakt II, Analog Four MK2) and previous abstraction efforts (a Digitakt II agentic composition framework; a CLI DAW built on continuous dynamical systems; live coding studies in Sonic Pi against Curtis Roads' microsound theory and Mark Fell's pattern synthesis). Phonon synthesizes those threads into a system unburdened by hardware constraints, where the composer's opinions and aesthetic commitments provide the creative discipline that hardware previously imposed.

The hypothesis that motivates the work: pure software, when given sharp opinions and tight refusals, can produce music more fluidly and with less effort than hardware allows, and the agentic interface (Claude Code as primary author, the composer as listener-and-director) can produce volumes and depths of work that hands-on programming cannot match.

### 1.2 What success looks like

- A composer writes pieces in dialogue with Claude Code, in 80–150 lines per piece.
- A piece file is the composition. Diffs of the file are diffs of the composition.
- Rendering the same file with the same seed produces bit-identical audio (offline mode).
- Rendering with a different seed produces a recognizable variant of the same piece.
- A listener can re-render any released piece on their own machine in a single command.
- Live performance and offline rendering use the same piece file, with no special-cased branching at the composer's level (the renderer selects the right Pyo backend).
- The framework is small enough that a composer can read its source in a weekend and a senior engineer can audit it in a day. The vendored Pyo is out of scope for that audit — Phonon is the framework, Pyo is the substrate.

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
| **Process** | A continuous signal source or transformation; a Phonon facade over a `PyoObject`. |
| **Threshold** | A device that converts a continuous signal into discrete trigger events at crossings. Implemented over Pyo's `Thresh`. |
| **SampleAndHold** | Latches a signal's value at trigger times into a held value. Implemented over Pyo's `SampHold`. |
| **Voice** | A named carrier of sound with a role, a band, and a source process; bears a role-specific parameter contract. |
| **Coupling** | A declared relationship between two voices, with a kind (phase, amplitude, etc.) and a strength signal. |
| **Trajectory** | A logical control-rate signal living at a declared Roads scale. Sampled at the framework's tick from a Python evaluator and pushed into Pyo `Sig`/`SigTo` slots. |
| **Binding** | A connection from a source signal to a target parameter, under a mode (absolute, offset, modulate). |
| **Reference** | A first-class deferred reference to a named entity (typically a trajectory) by string name. |
| **Crossing** | A predicate that fires when a referenced signal crosses a value with declared direction. |
| **Event** | A structural change to the score, fired when its trigger condition becomes true. |
| **Rhetoric** | A small vocabulary of long-form structural primitives: Persistence, Recurrence, Departure, Quotation, Latency. |
| **Gesture** | A named external input slot (MIDI/OSC) bound to a parameter or trigger, with a default value. |
| **Score** | The whole piece: seed, corpus, voices, couplings, trajectories, bindings, events, rhetoric, gestures, variance defaults. |
| **Performance** | A specific render: `(score, seed, gesture_timeline | autopilot)` producing audio. |
| **Tick** | One iteration of Phonon's scheduler at `control_hz`. Computes trajectory values, applies bindings, tests crossings, optionally pumps the Pyo server (offline only). |

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
   ┌─────────────────────────────────────────────────────────────┐
   │                    Phonon Core (Python)                     │
   │                                                             │
   │  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
   │  │  Score      │ │  Reference   │ │  Renderer           │   │
   │  │  Validator  │→│  Resolver    │→│  Scheduler          │   │
   │  │             │ │ (build DAG)  │ │ (tick loop, manual  │   │
   │  └─────────────┘ └──────────────┘ │  or live driven)    │   │
   │                                   └────────┬────────────┘   │
   │                                            │                │
   │  ┌─────────────────────────────────────────────────────┐    │
   │  │              Process Primitive Layer                │    │
   │  │   Process · Threshold · SampleAndHold · Binding     │    │
   │  │   Seeded random surrogates · Custom DSP (vdp, …)    │    │
   │  └─────────────────────┬───────────────────────────────┘    │
   │                        │                                    │
   │  ┌─────────────────────▼───────────────────────────────┐    │
   │  │              Pyo (vendored at pyo-src/)             │    │
   │  │  Server · PyoObject graph · MIDI · OSC · Tables     │    │
   │  │  Offline: audio="manual" + Server.process()         │    │
   │  │  Live:    audio="portaudio" / "jack" / "coreaudio"  │    │
   │  └─────────────────────────────────────────────────────┘    │
   └─────────────────────────────────────────────────────────────┘
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
        ┌──────────────┐     ┌──────────────┐    ┌───────────────┐
        │  Audio file  │     │  .gestures   │    │  Realtime     │
        │  (FLAC/WAV)  │     │  (timeline)  │    │  audio output │
        └──────────────┘     └──────────────┘    └───────────────┘
```

There are two distinct rendering substrates, selected by render mode:

- **Offline (autopilot, replay):** `Server(audio="manual")`. The Phonon scheduler is the sole driver: each tick advances piece time, evaluates trajectories, applies bindings, tests crossings, and then calls `Server.process()` once per audio block boundary. No audio thread runs. The render is single-threaded, deterministic, and bit-exact reproducible given seed and gesture timeline. Output is via `Server.recordOptions(...)` in a streaming WAV/FLAC writer fed by the manually-pumped server. *(Implementation note: pyo's stock `audio="offline"` is also block-driven internally and blocking, but `"manual"` cedes the loop to Phonon entirely, which is what we want for synchronizing the framework's tick boundaries with audio block boundaries.)*

- **Live (live, replay-with-live-overlay):** `Server(audio="portaudio")` (or `"jack"`/`"coreaudio"` per platform). Pyo runs an audio callback thread internally; Phonon's scheduler runs at `control_hz` on the main thread and writes parameters via the Server's pre-block callback (`Server.setCallback`) to keep timing aligned to block boundaries. Bit-exactness is given up; latency is the floor.

The renderer's tick loop is the same in both modes; the only difference is whether the loop calls `Server.process()` itself (offline) or schedules its updates inside Pyo's pre-block callback (live).

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

In offline mode, piece time is derived directly from the sample counter (`samples_rendered / sample_rate`), guaranteeing no drift. In live mode, piece time is derived from Pyo's `Server.getCurrentTime()` (which itself ticks from sample counts inside Pyo's audio callback), interpolated linearly between block boundaries.

### 5.3 Control rate

Trajectories and bindings run at the framework's **control rate**, which defaults to 200 Hz (5ms per tick). This is configurable on the Score (`control_hz=200`).

Critically: **Pyo has no separate control rate.** All Pyo objects, including envelope-shaped objects like `Sig`, `SigTo`, and `Linseg`, run at audio rate inside Pyo's per-block computation. Phonon's "control rate" is a scheduler-imposed cadence at which the framework writes new parameter values into Pyo's `Sig`/`SigTo` slots, which Pyo then interpolates at audio rate inside its block. The granularity of parameter updates from Phonon's perspective is therefore `max(control_hz_period, audio_block_duration)`.

At default settings (200 Hz control = 5ms tick, 256-sample buffer at 48kHz = 5.3ms block), the two are within rounding distance of each other. Raising `control_hz` above the block rate provides no benefit; lowering it is fine for slow pieces and saves Python overhead.

The control loop is single-threaded and deterministic given `(seed, gesture_timeline, control_hz, sample_rate, buffer_size)`. Changing `control_hz`, `sample_rate`, or `buffer_size` between renders may change audio output bit-for-bit even with the same seed, because Phonon's per-tick decisions land at slightly different sample positions. The reproducibility contract therefore pins all four.

---

## 6. The process primitive layer

The primitive layer is what every higher-level concept in the framework is built from. Composers rarely touch it directly; agents working under the framework rarely need to either, because the role-bearing facades (Voice, Trajectory, etc.) cover the typical surface. But the primitive layer is the framework's contract with Pyo and the foundation on which everything else is implemented.

### 6.1 Process

```python
class Process:
    """A continuous signal source or transformation.

    Wraps a PyoObject (or composes several) with framework metadata: rate,
    scale, and a seeded RNG (for stochastic processes). Has a single output
    signal addressable as `process.output`. Parameters are themselves
    Reference-able and modulatable.
    """
    rate: Rate                       # Rate.AUDIO or Rate.CONTROL
    scale: Scale                     # Scale.SAMPLE through Scale.SUPRA
    output: Signal                   # Reference to underlying PyoObject
    parameters: dict[str, Parameter]
    rng: Random                      # Per-process seeded numpy RNG, derived from Score seed
    pyo_objects: list[PyoObject]     # Held to prevent GC (Pyo lifetime foot-gun)
```

Concrete process subclasses:

**Generators (signal-producing) — Pyo-backed where the parameterization aligns:**

| Phonon factory | Pyo backing | Notes |
|---|---|---|
| `sine(freq, phase=0)` | `Sine(freq, phase)` | Direct. |
| `phasor(freq)` | `Phasor(freq)` | Direct. |
| `saw(freq)` | `LFO(freq, type=0)` | Saw-up; band-limited. |
| `triangle(freq)` | `LFO(freq, type=3)` | Band-limited. |
| `square(freq, sharp=0.5)` | `LFO(freq, sharp, type=2)` | Band-limited. |
| `superSaw(freq, detune=0.5, bal=0.7)` | `SuperSaw(freq, detune, bal)` | Direct. |
| `fm(carrier, ratio, index)` | `FM(carrier, ratio, index)` | Direct. |
| `rcOsc(freq, sharp=0.25)` | `RCOsc(freq, sharp)` | Direct. |
| `lfo(freq, sharp, type)` | `LFO(...)` | Pass-through to Pyo's 8-shape LFO. |

**Generators — chaotic / dynamical, Phonon-implemented (Pyo's variants are kept available but not the default):**

The composer's spec calls for parameterizable Lorenz, Rossler, and van der Pol with their classical coefficients (ρ, σ, β; a, b, c; µ). Pyo's `Lorenz`, `Rossler`, and `ChenLee` expose only normalized `pitch` (speed 0–1) and `chaos` (0–1) controls — they're flavored chaotic-attractor LFOs, not faithful ODE integrators, and they do not expose the parameters Phonon's aesthetic vocabulary needs. Phonon therefore ships its own:

| Phonon factory | Implementation strategy | Notes |
|---|---|---|
| `vdp(rate, mu=2.0)` | Pyo `Expr` with one-sample-delay state | Van der Pol relaxation oscillator; `rate` is fundamental frequency, `mu` is nonlinearity. |
| `lorenz(component, sigma=10, rho=28, beta=8/3, dt=0.001)` | Pyo `Expr` with 3-state Euler integrator | `component` ∈ `{"x","y","z"}`; output is normalized to `[-1, 1]` per axis. |
| `rossler(component, a=0.2, b=0.2, c=5.7, dt=0.005)` | Pyo `Expr` | Same shape as lorenz. |
| `chua(component, alpha=15.6, beta=28, m0=-1.143, m1=-0.714, dt=0.001)` | Pyo `Expr` | Chua's circuit — true Chua, not pyo's `ChenLee`. |
| `logistic_map(r, dt=control_period)` | Python at control rate, written into a `Sig` | Discrete iteration; control-rate only. |
| `pyo_lorenz_lfo(pitch, chaos)` | direct `Lorenz` | Escape hatch when the pyo flavor is what's wanted. |
| `pyo_rossler_lfo(pitch, chaos)` | direct `Rossler` | Same. |
| `pyo_chen_lee_lfo(pitch, chaos)` | direct `ChenLee` | Same. |

Pyo's `Expr` (defined in `pyo.lib.expression`) is a prefix-syntax DSL with one-sample delay (`(delay x)`), conditionals, periodic ramps (`(~ freq phase)`), trigonometric functions, and seeded randoms (`(randf x y)`, `(randi x y)`). It is the right substrate for ODE integration: each integrator step is a self-recurrent expression that computes `state += dt * f(state, params)` per audio sample. `Expr`'s randoms are *not* deterministic across runs (they share Pyo's global LCG), so Phonon's `Expr` programs avoid `randf`/`randi` and route any required randomness through table lookups.

**Generators — stochastic, Phonon-seeded surrogates:**

Pyo's `Noise`, `PinkNoise`, `BrownNoise` are not bit-exact reproducible (see §14.1). Phonon ships seeded surrogates as the default:

| Phonon factory | Implementation | Notes |
|---|---|---|
| `white_noise()` | `numpy.random.Generator.standard_normal` → `DataTable` (large, e.g. 60s of samples) → `TableRead(loop=True)` | Bit-exact given seed; loop-detectable but acceptable for noise. Table size configurable. |
| `pink_noise()` | Same approach with Voss-McCartney filtering applied during table generation | |
| `brown_noise()` | Same with cumulative-sum filtering | |
| `pyo_white_noise()` | direct `Noise` | Escape hatch for live-mode use where seed determinism is irrelevant. |

Tables are generated lazily at Score construction time using each Process's per-process RNG (derived from Score seed; see §14.2). The same Score + same seed produces the same tables, hence the same audio.

**Transformations (signal-consuming) — Pyo-backed:**

| Phonon factory | Pyo backing |
|---|---|
| `follower(source, freq=20)` | `Follower(source, freq)` (analysis module). |
| `derivative(source)` | `Compare(source - delay(source, dt=1/sr), 0)` via `Sig` arithmetic, or `Expr`. Pyo has no direct derivative object. |
| `lowpass(source, cutoff)` | `Tone(source, cutoff)` (1-pole) or `ButLP(source, cutoff)` (Butterworth) or `MoogLP(source, cutoff, res)` for resonance. |
| `highpass(source, cutoff)` | `Atone(source, cutoff)` or `ButHP(source, cutoff)`. |
| `bandpass(source, freq, q)` | `Reson(source, freq, q)` or `ButBP(source, freq, q)`. |
| `delay(source, time, feedback=0)` | `Delay(source, time, feedback)`. |
| `smoothdelay(source, time, feedback=0)` | `SmoothDelay(source, time, feedback)`. |

**Sampler:**

- `Sample(corpus_key)` — references a sample by key in the Score's corpus block. Backed at render time by `SfPlayer` (file-based, streaming) or `SndTable` + `TableRead`/`Looper` (memory-loaded, position-controllable, the typical choice).

All process constructors return Process objects. They are pure data until the Score is rendered; the Pyo backing graph is built at render time inside the renderer's setup phase, after `Server.boot()` and before the first tick.

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
    rising: bool             # True = fires on upward crossings only
    hysteresis: float        # default: 0.01 (in source units)
    debounce_seconds: float  # default: 0.05
    trigger: Trigger         # The fired event stream
```

Implementation: Pyo's `Thresh(input, threshold, dir)` is a complete edge-triggered comparator with `dir=0` (rising), `dir=1` (falling), `dir=2` (both). Phonon's `Threshold` wraps `Thresh` and adds:

- **Hysteresis** by maintaining two `Thresh` objects with offsets `±hysteresis/2` and a small `Sig`-state machine that arms one and disarms the other after each fire.
- **Debounce** in the Phonon scheduler (not in Pyo): when a Threshold fires, it is silenced for `debounce_seconds` of piece time before re-arming. Debounce semantics need access to piece time, which lives in the framework, not in Pyo's `Thresh`.

Thresholds are how rhythm, melody, and structural events arise from continuous flow. The framework uses Threshold internally for `Crossing` predicates on structural events, for voice entrance triggers, and for `Recurrence` return conditions.

### 6.3 SampleAndHold

```python
class SampleAndHold:
    """Latches a signal's value at trigger times into a held value.

    When `trigger` fires, samples `source` and holds the result on
    `output` until the next trigger.
    """
    source: Reference | Process
    trigger: Trigger             # framework Trigger (a Pyo trigger stream under the hood)
    output: Signal
```

Implementation: Pyo's `SampHold(input, controlsig, value=1.0)` samples `input` whenever `controlsig` equals `value`. Phonon's `SampleAndHold` constructs `SampHold(input=source, controlsig=trigger, value=1.0)`, which fits Pyo's trigger convention (a trigger stream is "1.0 surrounded by 0.0").

(Note: Pyo also has `TrigVal(input, value, init)` which latches a *parameter* value rather than a signal. That is the wrong primitive for sample-and-hold; `SampHold` is the right one.)

SampleAndHold is how continuous signals become note-like material: drive a Threshold on a clock-like Process, attach SampleAndHold to a pitch-bearing Process, and the held output is a sequence of pitches.

### 6.4 Binding

```python
class Binding:
    """Connects a source signal to a target parameter, under a mode.

    On every control tick, computes the target's new value as
    `mode_apply(target.base, source.value)` and writes it to the underlying
    Sig/SigTo PyoObject.
    """
    source: Reference | Process | Signal
    target: Parameter
    mode: Mode                                       # Mode.ABSOLUTE, Mode.OFFSET, Mode.MODULATE
    glide_seconds: float = 0.005                     # SigTo interpolation time; 0 for instant
    transform: Optional[Callable[[float], float]]    # rare; explicit escape hatch
    name: Optional[str]                              # for explicit removal via UnbindFromTrajectory
```

Mode semantics:

- `Mode.ABSOLUTE` — `target.value = source.value`. The source replaces the target.
- `Mode.OFFSET` — `target.value = base + source.value`. The source is added to the target's underlying base value.
- `Mode.MODULATE` — `target.value = base * source.value`. The source multiplies the target.

Each Parameter is backed by a `Sig` (instant) or `SigTo` (linear-ramp interpolated) PyoObject. `SigTo` provides linear-ramp click-free updates over `glide_seconds`; for non-linear glides, use `Port` (lowpass-smoothed) or `VarPort` (one-shot ramp with callback) — exposed via `glide_curve=Curve.LINEAR | Curve.PORT | Curve.VARPORT`.

The same `Mode` enum is used by `Binding` and `Gesture`. There is exactly one mode concept in the framework.

### 6.5 The Pyo mapping (verified)

Every primitive in the framework maps to specific verified Pyo classes. The full reference is in Appendix C. Key facts that guide the implementation:

- **`Sig(value, mul, add)`** — wraps a Python number as an audio stream. The framework's Parameter abstraction is built on this. Updates via `sig.value = x` are visible at the next audio block boundary (≤ buffer_size samples of latency).
- **`SigTo(value, time, init, mul, add)`** — linear ramp from current to new value over `time` seconds whenever the value is set. The framework's default click-free parameter writes use this with `time=0.005`.
- **`Linseg(list, loop, initToFirstVal, mul, add)`** — multi-segment linear envelope. Used inside trajectory shape evaluators for the deterministic shape contribution.
- **`Thresh(input, threshold, dir)`** — edge-triggered threshold. `dir`: 0=rising, 1=falling, 2=both.
- **`Compare(input, comp, mode)`** — continuous comparator producing a 0/1 gate signal (not a trigger). Used internally by trajectory range checks.
- **`Change(input)`** — fires a trigger whenever the input value differs from its previous sample. Useful for stepped signals like `Counter` outputs.
- **`SampHold(input, controlsig, value)`** — true sample-and-hold; samples `input` when `controlsig == value`.
- **`TrigVal(input, value, init)`** — *not* sample-and-hold; latches a Python-mutated `value` parameter on each trigger. Phonon does not use this.
- **`Trig()`** — trigger source; emits a single trigger on `play()`. Triggers in Pyo are sparse-impulse audio streams (1 surrounded by 0s), not a separate stream type.
- **`Metro(time, poly)`** — isochronous trigger generator. Time is in seconds.
- **`Beat(time, taps, w1, w2, w3, poly)`** — algorithmic pattern generator with probability weights and 32-slot preset memory. Auxiliary streams: `obj['tap']`, `obj['amp']`, `obj['dur']`, `obj['end']`.
- **`Euclide(time, taps, onsets, poly)`** — Euclidean rhythm generator; same auxiliary streams as Beat.
- **`Counter(input, min, max, dir)`** — counts triggers; output is a stepped integer signal.
- **`Select(input, value)`** — fires a trigger whenever `input == value`; useful with `Counter` for selecting steps.
- **`Adsr(attack, decay, sustain, release, dur, mul, add)`** — standard ADSR envelope.

### 6.6 The control loop

The Phonon scheduler runs at `Score.control_hz` (default 200 Hz). It is the single source of truth for piece time and all framework-level state.

**Offline mode (`audio="manual"`)**:

```
boot Server with sr, buffersize, audio="manual"
build Pyo graph from Score, holding all PyoObjects in scheduler state
Server.recordOptions(dur=duration, filename=output, fileformat=5)  # FLAC
Server.start()  # arms recording but does not run audio
total_samples = duration * sr
samples_done = 0
tick_period_samples = sr // control_hz
loop:
    advance_phonon_state(piece_time = samples_done / sr)
    blocks_to_render = min(remaining_blocks, tick_period_samples // buffersize)
    for _ in range(blocks_to_render):
        Server.process()             # one audio block
    samples_done += blocks_to_render * buffersize
    if samples_done >= total_samples: break
Server.stop(); Server.shutdown()
```

`advance_phonon_state(t)` performs:

1. Evaluate all trajectories at `t`. Stochastic trajectories sample from their per-trajectory seeded RNG.
2. Resolve all `Reference` lookups against the current trajectory values (via a pre-computed resolution table built at validation time).
3. Apply all bindings: write parameter values into their backing `Sig`/`SigTo` objects.
4. Test all Threshold-based crossing predicates (events, voice entrances, rhetoric returns); fire any whose conditions newly became true.
5. Apply gesture values (replay mode: from recorded timeline; autopilot: defaults).

**Live mode (`audio="portaudio"` or platform-equivalent)**:

```
boot Server with sr, buffersize, audio="portaudio"
build Pyo graph from Score
register Server.setCallback(advance_phonon_state)  # called once per audio block
Server.start()  # spawns audio thread and runs until stop
on each block (in audio callback):
    advance_phonon_state(Server.getCurrentTime())
    [Pyo computes the audio block]
on each Phonon tick (in main thread, between blocks):
    read MIDI/OSC inputs, update gesture latches (lock-free single-writer)
    record gesture changes (change-point compression)
on stop: Server.stop(); Server.shutdown()
```

In live mode, MIDI input is read via Pyo's `Notein`, `Midictl`, `Bendin`, `Touchin`, `Programin` objects (all of which run inside the Pyo graph as PyoObjects). OSC input is read via `OscReceive` / `OscDataReceive`. Phonon's gesture-latch updates from these are applied at the next `advance_phonon_state` callback, so the callback sees a consistent snapshot each block.

Both modes use the same `advance_phonon_state` function. The dependency graph and execution order are identical; only the loop driver changes.

### 6.7 Determinism strategy

Bit-exact reproducibility (offline mode) requires:

- **Pinned render parameters.** `(sample_rate, buffer_size, control_hz)` are part of the reproducibility contract along with seed and gesture timeline.
- **No wall-clock dependence in piece logic.** Only piece time (sample-counter-derived in offline mode).
- **Single-threaded scheduler.** No `audio="offline_nb"`, no asyncio in the render path.
- **No use of Pyo's stock random objects.** All stochastic processes use Phonon's seeded-table surrogates (§6.1, §14.1). Pyo's `Server.setGlobalSeed(seed)` is also called on boot for any stray uses inside Pyo's internals (granulators, denormal injection, etc.), but the framework's own randomness flows through numpy seeded RNGs, not Pyo's LCG.
- **Pinned environment.** `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, and `PYO_SERVER_WINHOST` env vars are explicitly cleared at Server construction (Pyo silently falls back to env vars if set; the framework does not allow this).
- **Pinned Pyo precision.** Phonon defaults to single-precision (`pyo._pyo`). Double precision (`pyo._pyo64` via `import pyo64 as pyo`) is supported as an alternative but the choice is part of the reproducibility contract — single and double will produce different audio.

### 6.8 PyoObject lifetime

Pyo's PyoObjects must be kept alive for the duration of the render; if all Python references go out of scope, the underlying `Stream` is garbage-collected and audio stops mid-render. This is a documented Pyo foot-gun.

Phonon's renderer holds all created PyoObjects in `RendererState.pyo_objects: list[PyoObject]` for the duration of the render. Composers never need to think about this; the role-bearing facades and the scheduler's setup phase handle it. Process objects also hold their own `pyo_objects` list as a defense-in-depth.

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

Internally, voice presence is implemented by an `Adsr`-shaped gain envelope on a `Sig` between the voice's source chain and the master mix. When a voice becomes present, the envelope opens over a short attack (default 50ms, configurable per voice). When dissolved by a `DissolveVoice` event, the envelope closes over a release time.

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

| Parameter | Type | Range | Pyo backing | Semantics |
|---|---|---|---|---|
| `band` | Band | Hz × Hz | `ButBP` filter or per-role-specific shaping | Frequency window; `band.center`, `band.width` are themselves modulatable. |
| `gain` | Parameter | 0.0 to 1.0 | `Sig` mul factor | Linear amplitude. |
| `position` | Parameter | -1.0 to 1.0 | `SPan` (constant-power) | Stereo position. |
| `intensity` | Parameter | 0.0 to 1.0 | `SigTo`, multiplies `gain` in mix | Overall presence/loudness. |

Each non-CUSTOM role extends the universal set with **role-specific parameters**:

**`ANCHOR_LOW`** (event-driven percussion):

| Parameter | Type | Range | Realization | Semantics |
|---|---|---|---|---|
| `event_rate` | Parameter | 0.5 to 8.0 Hz | `Metro(time=1/event_rate)` | Trigger rate; pulses per second. |
| `event_decay` | Parameter | 0.01 to 2.0 s | `TrigEnv` decay segment | Per-pulse decay time. |
| `event_jitter` | Parameter | 0.0 to 1.0 | jitter applied to Metro time via `Sig` | Timing variance; 0 is metric, 1 is fully randomized. |
| `tone` | Parameter | 0.0 to 1.0 | crossfade between filtered body Sig and click Sig | Body-vs-click balance; 0 is pure body, 1 is pure click. |

**`AIR_HIGH`** (continuous stochastic texture):

| Parameter | Type | Range | Realization | Semantics |
|---|---|---|---|---|
| `grain` | Parameter | 0.0 to 1.0 | granulation density (Granulator-driven) or filter Q | Particle-size character; 0 is smooth, 1 is crackly. |
| `motion` | Parameter | 0.0 to 1.0 | LFO depth on filter cutoff | Internal modulation depth. |

**`PRIMARY_MID` and `SECONDARY_MID`** (interactive mid voices, identical contracts):

| Parameter | Type | Range | Realization | Semantics |
|---|---|---|---|---|
| `event_rate` | Parameter | 0.0 to 16.0 Hz | `Metro` with jittered period | Trigger rate when sampled-and-held. |
| `event_decay` | Parameter | 0.01 to 2.0 s | `TrigEnv` | Per-event decay. |
| `pitch_center` | Parameter | 80 to 4000 Hz | `Sig` driving the source's freq input | Central pitch around which events cluster. |
| `pitch_spread` | Parameter | 0.0 to 1.0 | random offset around `pitch_center`, drawn at each Metro tick from a seeded surrogate | Spread of pitch around center; 0 is fixed, 1 is full octave. |

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
    output: Signal                     # the trajectory's current value (a Sig under the hood)
```

A trajectory is a logical control-rate signal living at a declared Roads scale. It produces a value at every Phonon control tick, computed as:

```
value(t) = shape.evaluate(normalized_t, reshape_params(t)) + variance.sample(t, rng) + drift_offset(t)
```

where `reshape_params(t)` is computed from `reshape_by`'s current value, `drift_offset(t)` is computed from `drift_toward`'s current value, and `variance.sample(t, rng)` draws jitter from the trajectory's seeded RNG.

The computed value is written to a backing `Sig` (or `SigTo` if smoothing is requested) once per tick, making the trajectory's signal available to downstream Pyo objects at audio rate via Pyo's normal modulation paths.

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

`brown` and `pink` shapes consume from the trajectory's per-trajectory seeded RNG (numpy-derived from Score seed), guaranteeing reproducibility.

### 8.3 Variance

```python
class Variance:
    amount: float                      # 0.0 = deterministic, 1.0 = max jitter
    correlation: Optional[float]       # autocorrelation; default 0.5
    distribution: Distribution         # default GAUSSIAN
```

Variance is per-trajectory with **scale-level defaults flowing downward**. The Score declares `variance_defaults: dict[Scale, float]`; trajectories without an explicit `variance` field inherit the default for their scale.

Variance samples are drawn from the trajectory's per-trajectory RNG using `numpy.random.Generator` methods (`standard_normal`, `uniform`, etc.), with autocorrelation enforced by an AR(1) filter on the sample stream. Distribution choice is via `Distribution` enum (`GAUSSIAN`, `UNIFORM`, `BIMODAL`, `EXPONENTIAL`).

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
    kind: CouplingKind           # PHASE, AMPLITUDE, FREQUENCY, RESPONSE
    name: Optional[str]
```

A coupling declares a relationship between two voices. The strength is a signal (typically a trajectory reference, sometimes a constant) that ranges 0 to 1, where 0 is decoupled and 1 is fully coupled. Couplings always exist for the duration of the piece once declared; their existence is not changed by structural events. Only their strength and kind can change.

### 9.2 Coupling kinds and Pyo realization

```python
class CouplingKind(Enum):
    PHASE     = "phase"      # voice b's event timing tracks voice a's
    AMPLITUDE = "amplitude"  # voice b's intensity tracks voice a's
    FREQUENCY = "frequency"  # voice b's pitch_center tracks voice a's
    RESPONSE  = "response"   # voice b is triggered by voice a's events
```

The kind determines the mechanism of coupling and its Pyo realization:

- **`PHASE`** — voice b's `Metro` time is interpolated, by `strength`, between its own value and voice a's `Metro` time. At strength 1 the two metros share a phase-locked period; at strength 0 they run independently. Implemented by writing the interpolated time into both `Metro` objects each tick.
- **`AMPLITUDE`** — voice b's `intensity` parameter is interpolated, by `strength`, between its own base value and the *amplitude follower* of voice a (a `Follower(voice_a.output, freq=20)` running inside the Pyo graph).
- **`FREQUENCY`** — voice b's `pitch_center` is interpolated by `strength` toward voice a's `pitch_center`.
- **`RESPONSE`** — voice b's event trigger is OR-mixed (via `Mix`) with voice a's event trigger, scaled by `strength` (a 1.0 strength merges all of a's triggers into b; 0.0 leaves b independent).

Kind is mutable via `RewireCoupling` events; strength is continuously modulated through its bound signal. Rewiring a coupling rebuilds the relevant connection in the Pyo graph at the framework's next tick (atomically, with a 5ms `SigTo` ramp on amplitudes/frequencies to avoid clicks).

### 9.3 Coupling defaults by role

The framework provides default eligibility rules, used for validation warnings (not hard errors):

- `PRIMARY_MID` ↔ `SECONDARY_MID` are eligible for all coupling kinds.
- `AIR_HIGH` may couple weakly (`AMPLITUDE`) to `PRIMARY_MID` or `SECONDARY_MID`.
- `ANCHOR_LOW` typically remains uncoupled; couplings involving it produce a validation warning but are not errors.

These are conventions, not constraints. CUSTOM-role voices have no default eligibility rules.

---

## 10. Bindings and references

### 10.1 Reference

`Reference` is a first-class deferred reference to a named entity in the Score by string name. References resolve at Score construction time (validation) and again at render time (live evaluation, against the trajectory value table maintained by the scheduler).

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

The Reference resolver walks the Score at construction time and validates that every Reference path resolves to a real entity. It produces a `ResolvedRef` table indexed by Reference object identity, mapping each to a `(getter, setter)` pair on the actual runtime entity. The runtime path is therefore O(1) per Reference per tick.

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

The validator rejects any `DissolveVoice` event whose target voice carries Persistence.

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

Implementation: at scheduler tick boundaries during the capture window, the values of the voice's role-contract parameters are appended to a per-Recurrence ring buffer keyed by piece time. On the return crossing, the buffer is replayed by writing each frame's values back into the voice's parameters, with `Distortion` applied frame-by-frame.

### 11.3 Departure

```python
class Departure:
    capture: Voice
    window_seconds: tuple[float, float]
    scale: Scale
```

Declares a meso shape (gesture, motif, density profile) that is introduced once and forbidden from returning. The framework enforces the constraint: any Recurrence whose capture window overlaps a Departure window targeting the same voice is rejected at Score validation time. Departure produces a particular kind of memory in the listener — something heard, gone, not-quite-mourned.

### 11.4 Quotation

```python
class Quotation:
    source: Reference     # trajectory whose past values are quotable
    history_seconds: float  # how far back to keep
    target: Reference     # trajectory that may sample from history
    sample_at: Crossing   # when target samples from history
    depth_seconds: float | Reference  # how far back to reach (constant or modulatable)
```

Quotation is the past-self-as-material primitive. The source trajectory keeps a delay-line of its past values (a `numpy.ndarray` ring buffer of length `history_seconds * control_hz`); at the sample_at condition, the target trajectory samples a value from the source's history at offset `depth_seconds`. Quotation lets a piece reach back into its own past as raw material.

### 11.5 Latency

```python
class Latency:
    event: Event
    delay_seconds: float
```

Wraps a structural event with a delay. The event's trigger condition is evaluated normally, but its action is deferred by `delay_seconds`. This is the closest the framework comes to designing for the spooky-action phenomenon — a structural event fires now, the listener hears its consequences later, and the link between cause and effect is decoupled by design.

Implementation: when the inner event's Crossing fires, the action is enqueued in the scheduler's deferred-action queue with execution time `current_piece_time + delay_seconds`. The queue is drained at each tick.

### 11.6 Distortion

Distortions describe how Recurrence transforms captured material on return. The vocabulary is closed; lambdas are not accepted.

```python
class Distortion:
    density_scale: Optional[float | Reference]   # multiply event rate
    spectral_shift: Optional[float | Reference]  # multiply pitch center
    intensity_scale: Optional[float | Reference] # multiply intensity
    time_stretch: Optional[float | Reference]    # multiply playback duration
    reverse: bool = False                        # play backward
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
    release_seconds: float = 0.5  # envelope close time

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
    crossfade_seconds: float = 0.1

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

Events fire **probabilistically with seeded determinism**, not at exact threshold crossings. A Crossing predicate defines a *region* in which the event becomes eligible to fire; the event's per-event RNG (derived from the Score seed and the event's name; see §14.2) chooses the exact moment within the region. The eligibility region is the threshold crossing plus a configurable jitter window (default: ±5% of the relevant scale's typical duration).

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
    epsilon: float = 0.01    # change-point recording threshold; in fraction of range
```

A gesture is a named external input slot. Gestures appear in the piece file alongside trajectories and voices. They exist in the Score whether or not anything is plugged in.

### 13.2 Mapping types

```python
class Midi:
    @staticmethod
    def cc(number: int, channel: int = 1) -> GestureMapping: ...
    @staticmethod
    def note(number: int, channel: int = 1) -> GestureMapping: ...
    @staticmethod
    def bend(channel: int = 1) -> GestureMapping: ...
    @staticmethod
    def aftertouch(channel: int = 1) -> GestureMapping: ...

class Osc:
    @staticmethod
    def address(path: str, port: int = 8000) -> GestureMapping: ...
```

Mappings are typed factory methods that produce GestureMapping objects. They validate at construction and provide IDE completion.

### 13.3 Continuous and discrete gestures

A gesture is **continuous** if its range is a continuous interval (default). Continuous gestures modulate trajectories or parameters via their bound mode. Realized via `Midictl(ctlnumber, channel)`, `Bendin(channel)`, etc.

A gesture is **discrete** if its `target` is an Action rather than a parameter. Discrete gestures fire structural events when their input crosses a threshold (e.g., MIDI note on, OSC bang). Realized via `Notein(...)` for MIDI notes and `OscReceive(...)` with a `Thresh` for OSC. Discrete gestures use the same closed action set as scheduled events; this means the typed action vocabulary serves double duty as the agent's compositional vocabulary and the performer's instrument.

### 13.4 Default mode and behavior

The default `mode` for a gesture is `Mode.OFFSET`. In autopilot mode, gestures take their `default` value (not modulating internal evolution); in live mode, the connected controller drives them; in replay mode, a recorded gesture timeline drives them.

In offline mode (autopilot or replay), Pyo's MIDI/OSC modules are not booted — the `Server` runs with `audio="manual"` and gesture values are written directly into their backing `Sig` objects from the scheduler. In live mode, `audio="portaudio"` (or `"jack"` on Linux, `"coreaudio"` on macOS) and `Notein`/`Midictl`/`OscReceive` are real PyoObjects in the graph, with their values mirrored into the scheduler's gesture-latch table once per block via the `Server.setCallback` hook.

For deterministic test rendering of MIDI input, Phonon also exposes `Server.addMidiEvent(status, data1, data2)` via a `Performance.inject_midi(time, status, data1, data2)` API — the equivalent of replay mode for MIDI events scheduled at specific piece times.

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

The `.gestures` file format is line-delimited JSON, one entry per change point: `{"time": 12.345, "name": "warp", "value": 0.123}`. Times are in piece-time seconds, monotonically increasing.

---

## 14. Variance and determinism

### 14.1 Bit-exact reproducibility

Given the same `(source, seed, gesture_timeline, sample_rate, buffer_size, control_hz, pyo_precision)`, Phonon produces bit-identical audio in offline mode. This is non-negotiable. The reproducibility contract pins the four render parameters in addition to the seed and gesture timeline because Phonon's per-tick decisions land at slightly different sample positions when these parameters change.

Achieving this required several discoveries from the Pyo audit:

**Pyo's stock random objects are not bit-exact.** Pyo uses a single process-global linear-congruential generator (`PYO_RAND_SEED` in `src/engine/servermodule.c`) that is mutated per sample by every random object in the graph. `Server.setGlobalSeed(seed)` only sets the global at object construction time; runtime draws all share the same global cursor, with order dependent on construction sequence and per-block scheduling. Two stochastic objects' outputs are entangled through this shared cursor in a way that makes per-object reproducibility impossible without source modifications to Pyo.

**Phonon's response is to sidestep Pyo's RNG.** All stochastic processes use seeded surrogates that draw from `numpy.random.Generator` instances seeded from the Score seed. Specifically:

- **`white_noise()`, `pink_noise()`, `brown_noise()`** generate a long lookup table at Score-render setup time using a numpy seeded RNG, load it into a Pyo `DataTable`, and play it through `TableRead(loop=True)`. Default table length is 60 seconds of samples; the loop is undetectable for noise. For deterministic short-form work, a piece can request `length_seconds=duration` to make the table cover the full piece without looping.
- **Trajectory `brown` and `pink` shapes** sample their walk values directly in Python at control rate, written into a backing `Sig`. No Pyo random involvement.
- **Variance jitter** is sampled from the trajectory's per-trajectory numpy RNG, also at control rate.
- **Probabilistic event firing** uses the event's per-event numpy RNG.

Pyo's `Noise`/`PinkNoise`/`BrownNoise`/`Randi`/`Randh`/`Choice`/`Xnoise`/`LogiMap` etc. are accessible through `pyo_compat.*` factories for live-mode work where reproducibility is irrelevant, and for cases where the composer accepts non-determinism as a design choice. Using them in a piece that is intended to be reproducible produces a Score validation warning.

**Pyo's Server.setGlobalSeed is also called.** Some Pyo internals (denormal injection, `Granulator` density, `PadSynthTable`) call into the global LCG even in code paths Phonon does not directly touch. The renderer calls `Server.setGlobalSeed(seed_lower_32_bits)` at boot to make those paths at least construction-deterministic, even though they do not contribute to bit-exactness across all paths.

**Other determinism requirements:**

- Pyo offline mode: `Server(audio="manual")` driven by the framework's tick loop calling `Server.process()` per block, with `recordOptions(...)` configured before `start()`.
- Pinned environment: `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, and `PYO_SERVER_WINHOST` env vars cleared at Server construction.
- Fixed sample rate (default 48000), buffer size (default 256), nchnls (2), and pyo precision (single).
- No `numpy.random` use without explicit `numpy.random.Generator` instance.
- No wall-clock time access in piece logic (only piece time).
- Single-threaded scheduler.
- File I/O for sample loading completed before `Server.start()`.

The framework's test suite includes bit-exact reproducibility tests: render the same piece twice, compare audio file SHA-256 hashes; render with different control_hz at otherwise identical settings, assert outputs differ (negative test for the contract).

### 14.2 RNG hierarchy

The Score seed is the root of an RNG hierarchy:

```
Score.seed
├── trajectory[name].rng   = numpy.random.default_rng(derive(seed, "trajectory", name))
├── voice[name].rng        = numpy.random.default_rng(derive(seed, "voice", name))
├── event[name].rng        = numpy.random.default_rng(derive(seed, "event", name))
├── coupling[name].rng     = numpy.random.default_rng(derive(seed, "coupling", name))
├── process[id].rng        = numpy.random.default_rng(derive(seed, "process", auto_id))
└── tables[name].rng       = numpy.random.default_rng(derive(seed, "table", name))  # noise tables
```

Each entity gets its own `numpy.random.Generator` derived from the seed and a stable identity string (entity kind + name). The `derive(seed, kind, name)` function uses `numpy.random.SeedSequence` with `entropy=seed` and `spawn_key=hash(kind, name)` to produce independent, statistically uncorrelated streams.

This means changing a single trajectory's name does not change the random behavior of unrelated trajectories. The naming is the entity's identity for randomness purposes. Renaming a trajectory will, however, change *its own* random behavior — that is, a renamed trajectory is, for randomness purposes, a new trajectory.

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
    buffer_size: int = 256
    nchnls: int = 2
    pyo_precision: PyoPrecision = PyoPrecision.SINGLE
```

The Score is the single value that contains a complete piece. Construction validates References, checks for cycles, verifies role-contract conformance, and registers names for resolution.

### 15.2 Score validation

At construction time, the Score validator checks:

- All Reference paths resolve to real entities.
- Trajectory composition respects the scale-asymmetry rule (lower-scale may be reshaped by higher-scale, never the reverse).
- Departure constraints are respected (no Recurrence captures within Departure windows on the same voice).
- All Voice role-parameter bindings target parameters that exist on the role's contract.
- All gesture mappings are unique (no two gestures bound to the same MIDI CC on the same channel; no two OSC gestures on the same address+port).
- All event names are unique.
- No event names a target voice for `DissolveVoice` that carries `Persistence`.
- All sample references have valid corpus entries.
- `control_hz`, `sample_rate`, `buffer_size`, `nchnls` are positive; `sample_rate` is a Pyo-supported value; `buffer_size` is a power of two.

Validation failures raise `ScoreValidationError` with a precise message and the offending entity's name. Validation is non-fatal warnings (e.g., uncommon coupling-by-role combinations, use of `pyo_compat.*` non-deterministic sources) attach to a `Score.warnings` field and surface in `describe()` and the CLI.

### 15.3 Score.describe()

Returns a structured human- and agent-readable summary:

```python
{
    "title": "Threshold (study no. 1)",
    "duration": "7:00",
    "seed": 1729,
    "render_contract": {
        "sample_rate": 48000, "buffer_size": 256, "control_hz": 200,
        "pyo_precision": "single", "framework_version": "0.1.0",
    },
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
    "warnings": [...],
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
    sample_rate: int  # native rate; resampled to score sr at load time if different
```

A Corpus declares the sonic raw material of a piece by content-hashed manifest. Samples are referenced from voice sources via `Sample("key")`. Corpora are optional; synthesis-only pieces have `corpus=None`.

Sample loading uses `SndTable(path)` (file → memory `PyoTableObject`). At Score construction time, the validator opens each sample file and verifies its SHA-256 against the corpus manifest, failing fast if the content has drifted from what the score was authored against.

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

Same source file, three operating modes, no special-cased branching in the piece file. The renderer selects the appropriate Pyo audio backend per mode:

| Mode | Pyo audio backend | Determinism | Use case |
|---|---|---|---|
| AUTOPILOT | `"manual"` | bit-exact | offline render, releases, regression tests |
| LIVE | `"portaudio"` / `"jack"` / `"coreaudio"` | not guaranteed | live performance, controller experimentation |
| REPLAY | `"manual"` | bit-exact | re-render of a live performance offline |
| LIVE-OVERLAY | `"portaudio"` / `"jack"` / `"coreaudio"` | not guaranteed | replay a `.gestures` while still accepting live input on undriven gestures |

The composer's piece file works in all four modes without modification. The choice is made at the CLI layer.

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
    pyo_version: str
    render_contract: dict       # sample_rate, buffer_size, control_hz, pyo_precision
```

Each performance is a `(seed, gesture_timeline, render_contract)` triple plus its rendered audio. The released piece has identity in the source; performances are instances.

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
├── pyo-version.txt              # pyo version pin (from pyproject.toml of vendored copy)
└── performances/
    ├── performance-001/
    │   ├── seed.txt
    │   ├── render-contract.json # sr, buffer, control_hz, pyo_precision
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
phonon render piece.py --live --gestures performances/performance-001/gestures.jsonl  # live overlay
```

### 16.4 The CLI

The `phonon` CLI exposes:

- `phonon render <piece.py> [--seed N] [--gestures FILE | --live] [--out PATH] [--sr 48000] [--buffer 256] [--control-hz 200]`
- `phonon describe <piece.py>` — prints `Score.describe()` output as YAML.
- `phonon validate <piece.py>` — runs Score validation; reports errors and warnings.
- `phonon package <piece.py> --performances N [--seed-strategy random|sequential|fixed:1729,4242,…]` — builds a release-artifact directory.
- `phonon midi-list` — lists available MIDI inputs (for live mode setup).
- `phonon osc-listen [--port 8000]` — runs an OSC listener for live mode debugging.
- `phonon hash <audio.flac>` — convenience SHA-256 of a render output.
- `phonon repro <piece.py> --seed N --runs 2` — renders twice, compares hashes, exits 0 on match.

---

## 17. Module layout

The framework's public Python module structure:

```
phonon/
├── __init__.py              # re-exports the public API surface (§18)
├── score.py                 # Score, validation, describe, render contract
├── voice.py                 # Voice, Role, Band, role-contract enforcement
├── trajectory.py            # Trajectory, Variance, scale logic, RNG hierarchy
├── coupling.py              # Coupling, CouplingKind, Pyo realization helpers
├── binding.py               # Binding, Reference, ResolvedRef, Mode
├── rhetoric.py              # Persistence, Recurrence, Departure, Quotation, Latency, Distortion
├── event.py                 # Event, Action protocol, six closed-set actions
├── gesture.py               # Gesture, Midi, Osc, GestureMapping
├── shape.py                 # linear, sigmoid, exponential, brown, pink, arc, step, composite
├── seedseq.py               # derive() function; SeedSequence-based RNG hierarchy
├── process/                 # process primitive layer
│   ├── __init__.py
│   ├── base.py              # Process, Threshold, SampleAndHold (over Pyo Thresh, SampHold)
│   ├── generators_pyo.py    # sine, phasor, saw, triangle, square, superSaw, fm, lfo (direct Pyo wrappers)
│   ├── generators_chaos.py  # vdp, lorenz, rossler, chua, logistic_map (custom, Expr-based)
│   ├── randoms_seeded.py    # white_noise, pink_noise, brown_noise (table-based, deterministic)
│   ├── pyo_compat.py        # pyo_white_noise, pyo_lorenz_lfo, etc. — direct Pyo aliases for live-mode use
│   ├── transforms.py        # follower, derivative, lowpass, highpass, bandpass, delay, smoothdelay
│   └── sample.py            # Sample, Corpus, manifest verification
├── render/                  # rendering and runtime
│   ├── __init__.py
│   ├── scheduler.py         # the tick loop (offline + live drivers)
│   ├── pyo_backend.py       # PyoObject construction from Process; lifetime management
│   ├── server.py            # Server boot/teardown, env pinning, manual-mode pumping
│   ├── midi_io.py           # MIDI input via Pyo Notein/Midictl/...; output via Server.noteout
│   ├── osc_io.py            # OSC input via OscReceive/OscDataReceive; output via OscSend
│   ├── recorder.py          # gesture recording with change-point compression
│   └── reproducibility.py   # render-contract pinning, hash assertions
├── cli/
│   ├── __init__.py
│   └── main.py              # phonon CLI entry point
└── version.py
```

Vendored Pyo source remains in `pyo-src/` (a sibling directory to `phonon/`, not a subpackage). The `pyo` Python module is installed from the vendored source via `pip install -e ./pyo-src/`. See Appendix D for the vendoring policy.

### 17.1 The five user-facing modules

The framework's public surface is presented to composers and the agent through five "facade" categories that map to the modular-synth ontology while remaining thin layers over the primitives:

1. **Clocks** — Processes whose output crosses Thresholds at metric frequencies. `vdp(rate)` is the canonical example. Surface in `phonon.process.generators_chaos` (vdp) and `phonon.process.generators_pyo` (Metro-based factories).
2. **Modulators** — Trajectories. The dominant non-audio signal source.
3. **Sequencers** — SampleAndHold + Threshold compositions; pre-built sequencer factories live in `phonon.process` (e.g., `euclidean(steps, fills)` over `Euclide`, `markov(transitions)` custom).
4. **Instruments** — Voices. The carriers of sound.
5. **Effects** — Process transformations (filters, delays, followers); applied via voice source composition or as post-voice processors.

These are roles that primitives play, exposed via convenient names. They are not separate type hierarchies. The five-module label is for the agent's vocabulary and the docs; the type system is the smaller primitive set.

### 17.2 Naming collision with Pyo

Pyo exports a class named `Score` (in `pyo.lib.pattern`) — a per-event-list scheduler unrelated to Phonon's piece-level Score. **Phonon never does `from pyo import *`** in framework code or example pieces; all Pyo references are qualified (`from pyo import Sine, SigTo, Server`) or namespaced (`import pyo as _pyo`). Composers writing piece files use `from phonon import *`; if they need Pyo objects directly (escape hatches), they import them by name from `pyo`. The Phonon plugin's skill content includes this convention as a default lint check.

---

## 18. Public API surface

The public top-level imports from `phonon` are:

```python
from phonon import (
    # Score
    Score, RenderMode, PyoPrecision,

    # Voice
    Voice, Role, Band,

    # Trajectory
    Trajectory, Variance, Scale, Distribution,

    # Coupling
    Coupling, CouplingKind,

    # Binding
    Binding, Mode, Reference, Curve,

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

    # Process generators (Pyo-direct, deterministic-friendly)
    sine, phasor, saw, triangle, square, superSaw, fm, rcOsc, lfo,

    # Process generators (chaos / custom; deterministic)
    vdp, lorenz, rossler, chua, logistic_map,

    # Process generators (stochastic; seeded surrogates, deterministic)
    white_noise, pink_noise, brown_noise,

    # Process transformations
    follower, derivative, lowpass, highpass, bandpass, delay, smoothdelay,

    # Shapes
    linear, sigmoid, exponential, brown, pink, arc, step, composite,

    # Sequencer factories
    metro, beat, euclidean, counter,
)
```

Flat imports are preferred. The public API is approximately 60 names — large enough to require organization in docs but small enough to fit in an agent's context comfortably.

Non-deterministic Pyo-direct factories are exposed under `phonon.pyo_compat`:

```python
from phonon.pyo_compat import (
    pyo_white_noise, pyo_pink_noise, pyo_brown_noise,
    pyo_lorenz_lfo, pyo_rossler_lfo, pyo_chen_lee_lfo,
    pyo_randi, pyo_randh, pyo_choice, pyo_xnoise,
)
```

Use of these in a Score generates a validation warning ("non-deterministic source: white_noise will not be bit-exact"). Live-mode pieces that don't care about reproducibility use these freely; archival pieces don't.

---

## 19. Implementation notes

### 19.1 Pyo specifics

- **Server lifecycle**: the framework owns the Pyo `Server` lifecycle. Composers never instantiate Server directly. The renderer constructs the Server with appropriate parameters, boots it, builds the graph, runs the scheduler, and shuts down cleanly.
  - **Offline boot**: `Server(sr=score.sample_rate, nchnls=score.nchnls, buffersize=score.buffer_size, audio="manual", duplex=0).boot()`. Recording configured via `Server.recordOptions(dur, filename, fileformat=5, sampletype=1, quality=0.4)` for FLAC/24-bit. Pumped via per-block `Server.process()` calls inside the scheduler tick loop. Teardown: `Server.stop(); Server.shutdown()`. Do not rely on `Server.__del__`, which has wall-clock `time.sleep(0.25)` guards for live mode.
  - **Live boot**: `Server(sr=..., nchnls=..., buffersize=..., audio=<platform>, duplex=1, midi="portmidi").boot()`. Server runs internally; scheduler attaches to its `setCallback(...)` hook to align phonon ticks to block boundaries.
  - **Env pinning**: Phonon clears `PYO_SERVER_AUDIO`, `PYO_SERVER_MIDI`, `PYO_SERVER_WINHOST` at Server construction so user-shell defaults can never silently change the backend.
  - **Server.setGlobalSeed(seed)** is called immediately after boot to seed Pyo's internal LCG for paths Phonon doesn't directly stochasticize.
- **PyoObject lifetime**: PyoObjects must be kept alive for the duration of the render. The renderer holds references in `RendererState.pyo_objects`; Process objects also hold their own. Composers should not need to manage object lifetime.
- **Audio vs control rate**: Pyo has no separate control rate. All Pyo objects are audio-rate. Phonon's "control rate" is a scheduler cadence at which the framework writes new values into Pyo `Sig`/`SigTo` slots. The split is enforced at the framework boundary, not in Pyo.
- **MIDI mapping**: Pyo's `Notein`, `Midictl`, `Bendin`, `Touchin`, `Programin` are wrapped by the framework's gesture I/O. Composers never see Pyo MIDI directly. For deterministic test-injected MIDI, the framework uses `Server.addMidiEvent(status, data1, data2)` driven from the gesture timeline.
- **OSC mapping**: `OscReceive`, `OscDataReceive`, `OscListReceive` for input; `OscSend`, `OscDataSend` for output. Wrapped by `phonon.render.osc_io`.
- **SigTo for click-free parameter changes**: parameter writes from the control loop go through `SigTo` PyoObjects with a small linear interpolation time (default 5ms) to prevent zipper noise. This time is configurable per-parameter (`Binding.glide_seconds`) for cases where instant changes (`glide_seconds=0`, backed by `Sig`) or non-linear glides (`Curve.PORT` → `Port`) are desired.
- **Pyo precision**: defaults to single-precision (`pyo._pyo`). Double precision is opt-in via `Score(pyo_precision=PyoPrecision.DOUBLE)`, which causes the renderer to import `pyo64` instead. Single and double produce different bit-exact outputs; the choice is part of the reproducibility contract.

### 19.2 Determinism specifics

- Use `numpy.random.Generator` instances exclusively from `numpy.random.default_rng(SeedSequence(...))`. Never use the module-level `numpy.random` or Python's `random` module directly in piece logic.
- Avoid Pyo's stochastic objects in deterministic paths; use Phonon's seeded surrogates (§14.1).
- Pyo's offline rendering must use the same sample rate, buffer size, and number of channels every render. The render contract enforces this.
- The control loop must be single-threaded.
- File I/O for sample loading must occur before `Server.start()` (no I/O during render).
- `Server.setGlobalSeed(seed_low_32)` is called at boot; this does not bit-exact-determinize Pyo internals but does bound their initial state.
- `audio="offline_nb"` is forbidden in offline render paths (it spawns a worker thread).

### 19.3 Performance considerations

- 200 Hz control rate × 50 trajectories × 100 bindings ≈ 1M evaluations per second from Python. Modern CPUs handle this trivially; Python's overhead is the dominant cost. No vectorization is needed at v1.
- Real-time live mode should target sub-10ms gesture-to-audio latency. Pyo's audio block at 48kHz/256 = 5.3ms; Phonon's tick at 200 Hz = 5ms; total ≈ 10ms. Acceptable for studio work; tight for stage. Stage-quality reduction: lower `buffer_size` to 128 (2.7ms block) at the cost of CPU headroom.
- Offline rendering of a 7-minute piece should complete in well under 1 minute on a modern machine. M-series Macs run Pyo offline rendering significantly faster than realtime. Phonon's manual-mode pumping adds Python loop overhead but the dominant cost remains Pyo's audio computation.
- Noise-table generation at Score setup adds O(seconds_of_table × sr) numpy operations and 4 × seconds_of_table × sr bytes of memory per noise voice (single-precision float). Default 60-second tables × 4 voices × 48kHz × 4 bytes ≈ 46 MB. Acceptable.

### 19.4 Testing strategy

- Unit tests for each primitive (Process, Threshold, SampleAndHold, Binding) with deterministic inputs.
- Integration tests for full Score validation (positive and negative cases).
- Bit-exact reproducibility tests: render → hash → render → hash → assert equal. Run on `Server(audio="manual")` for full determinism.
- Differential reproducibility tests: same Score, varying `(sr, buffer_size, control_hz)`, assert outputs differ — proves the reproducibility contract is well-defined.
- Snapshot tests for `Score.describe()` output.
- A small library of "canonical pieces" (5–10 short scores) used both as documentation and as integration tests. The first canonical piece is `threshold_study_1.py` (Appendix A).
- Property-based tests for trajectory composition (using Hypothesis): a `reshape_by` relationship should never produce out-of-range values.
- A "Pyo audit" test that asserts every Pyo class Phonon depends on still has the expected constructor signature; this guards against future Pyo upstream changes if/when the vendored copy is updated.

### 19.5 Working with the vendored Pyo

The vendored Pyo copy at `pyo-src/` is treated as a maintained subproject:

- Build: `pip install -e ./pyo-src/` or `cd pyo-src && python -m build`. Native deps (portaudio, portmidi, libsndfile 1.0.30+, liblo 0.32+) per Pyo's README; macOS via Homebrew, Linux via apt/yum, Windows via vcpkg+MSYS2.
- Modifications: any patch lives as a commit on the main repo affecting `pyo-src/`. No runtime monkey-patching of Pyo. If a patch lands, document the rationale in the commit and add a note to Appendix D.
- Upstream tracking: the vendored copy is from upstream tag 1.0.6 (committed 2025-03-04). When Phonon updates the vendored copy, the bump is a single commit; the Phonon test suite (especially the Pyo audit test, §19.4) catches breaking changes.
- Single-precision is the default; double-precision (`pyo._pyo64`) requires `--use-double` build flag and is opt-in per Score.

---

## 20. The Claude Code plugin

### 20.1 Plugin structure

The `phonon-claude` plugin (working name) wraps Claude Code with framework-specific knowledge. It ships:

- **A primary skill** (`phonon-composer`) that teaches the agent the framework's vocabulary, conventions, and composer's aesthetic preferences. Includes the role contract reference, the closed event set, the rhetorical primitives, the Pyo class reference (Appendix C), and a library of technique vignettes mapped to API patterns.
- **A scholar mode** (`phonon-scholar`) for explicit lineage citation: the agent identifies which artist's technique a proposed move evokes ("this is a Fell-shaped density gradient"; "this is a Radigue-shaped persistence over slow harmonic drift"). The scholar mode is the primary identity; scribe and analyst are supporting modes.
- **A scribe mode** for rapid translation of intent to code without deep citation.
- **An analyst mode** that reads existing pieces and explains their structure (using `Score.describe()` plus framework knowledge).
- **A `/phonon:new` command** that scaffolds a new piece file from a brief description.
- **A `/phonon:render` command** that runs `phonon render` on the current piece and reports the audio output path.
- **A `/phonon:repro` command** that runs `phonon repro` to verify reproducibility.
- **A `/phonon:capture` command** that promotes the current ephemeral piece to a saved composition with a name.
- **Hooks** that validate piece files on save, reporting Score validation errors as actionable feedback.
- **Subagents** for specialized tasks: a `voice-designer` for sketching new voice configurations, a `trajectory-shaper` for proposing trajectory shapes given an intent, an `event-choreographer` for proposing structural event placement on the supra trajectory, a `dsp-extender` for proposing new chaotic generators or surrogates when the existing set is insufficient.

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
11. **No silent shimming of Pyo's non-determinism.** Phonon does not pretend Pyo's stock random objects are reproducible; it provides seeded surrogates and warns when non-deterministic sources are used.

---

## 22. Phased implementation plan

The framework is built in five phases. Each phase produces a runnable, testable artifact.

### Phase 0 — Skeleton (1 week)

- Repository setup, packaging, CI.
- Module skeleton (empty modules, type stubs).
- Score validator (validation logic with no rendering).
- `Score.describe()` returning correct YAML for an empty score.
- Test infrastructure including a `Server(audio="manual")` fixture identical in spirit to Pyo's `tests/pytests/conftest.py`.
- Vendored Pyo build verification on CI; `pip install -e ./pyo-src/` producing a working module.
- Project constitution (`.specify/memory/constitution.md`) authored from §1, §2, §14.1, §21.

### Phase 1 — Process primitive layer + determinism (3 weeks)

- `Process`, `Threshold` (over `Thresh`), `SampleAndHold` (over `SampHold`), `Binding`, `Reference`, `Mode`.
- Pyo backend module: PyoObject construction, lifetime tracking.
- Server lifecycle: boot/teardown, env pinning, manual-mode pumping, recordOptions wiring.
- RNG hierarchy: `derive()` based on `numpy.random.SeedSequence`.
- Seeded surrogate generators: `white_noise`, `pink_noise`, `brown_noise` (table-based).
- A handful of Pyo-direct generators: `sine`, `saw`, `triangle`.
- One transformation: `lowpass`.
- A handful of shapes: `linear`, `sigmoid`, `brown`.
- Bit-exact reproducibility test: a 5-second white-noise + sine piece renders to bit-identical FLAC twice.
- Differential test: changing `control_hz` produces different audio.
- Manual integration test: a Python script that uses the primitive layer to produce 30 seconds of audio.

### Phase 2 — Voices, trajectories, couplings (3 weeks)

- `Voice` with role-contract enforcement for the four roles plus CUSTOM.
- `Trajectory` with `reshape_by` and `drift_toward`, scale-asymmetry validation.
- `Coupling` with the four kinds.
- `Binding` integration with the control loop.
- Variance with scale defaults.
- Custom chaotic generators: `vdp`, `lorenz`, `rossler`, `chua` via Pyo `Expr`.
- Render `threshold_study_1.py` (Appendix A) end-to-end in autopilot mode.
- Bit-exact reproducibility test passes for the canonical piece.

### Phase 3 — Events, gestures, rhetoric (3 weeks)

- `Event` with the six v1 actions.
- Probabilistic firing with seeded jitter.
- `Gesture` with MIDI and OSC mappings; live-mode reading via Pyo `Notein`/`Midictl`/`OscReceive`.
- Three render modes: autopilot, live, replay.
- Change-point gesture recording.
- The five rhetorical primitives (Persistence, Recurrence, Departure, Quotation, Latency).
- Render `threshold_study_1.py` in all three modes.
- Render artifact `phonon repro` confirms hash equality across two autopilot runs.

### Phase 4 — CLI, packaging, plugin (3 weeks)

- `phonon` CLI with all subcommands (render, describe, validate, package, midi-list, osc-listen, hash, repro).
- Release-artifact packaging with manifest and per-performance subdirectories.
- The Claude Code plugin: skill, scholar/scribe/analyst modes, slash commands, hooks, subagents.
- Composer-model document and technique vignettes library.
- Documentation site; a `phonon viz piece.py` HTML/SVG timeline view (was v1.5 in v1.0; promoted to Phase 4 because the trajectory-shape and event-placement views are core to the agent's compositional reasoning).

Total: 13 weeks for a fully working v1, single developer (with Claude Code as primary coder).

---

## 23. Open questions

These are decisions deferred to implementation or to a future revision.

### 23.1 Should `Reference("name")` have a shorthand?

The Reference verbosity is real but acceptable. Future revision may explore module-level capture (declare a trajectory at top-level and have its name auto-bind as a Reference) via metaclass or import-hook trickery. v1 ships with explicit `Reference("name")`.

### 23.2 Sample manipulation primitives

Phase 1's process primitive layer covers synthesis but treats `Sample` as a leaf. Pieces that want fine-grained sample manipulation (granular re-synthesis from a sample, time-stretch, pitch-shift) need additional primitives. Pyo provides `Granulator`, `Granule`, `Particle`, `Particle2`, `Pulsar`, `Looper`, `Pointer2` — a richer sample primitive set in v1.5 will wrap these as Phonon-native granular processes.

### 23.3 Multi-channel audio

v1 is stereo (2 channels). Multi-channel output (quad, 5.1, ambisonic) is feasible and cheap to add but not v1. Pyo natively supports multi-channel via `Server(nchnls=N)`. Pieces declared with `Voice.position` continue to work; the channel mapping changes.

### 23.4 Distributed rendering

Long-form 25-minute pieces with many voices may exceed a single machine's offline render budget. Distributed rendering across multiple machines is feasible (the control loop is deterministic; segments can be rendered independently and concatenated with overlap-and-fade) but not v1.

### 23.5 Live-coding-style hot-swap

The framework supports re-running a piece file from scratch but does not (in v1) support hot-swapping individual trajectories, voices, or events while a piece is rendering. This is a substantial implementation effort and is deferred. Current live workflow: edit, save, re-run.

### 23.6 What the long-form work demands beyond v1

The composer indicated long-form 20–30 minute work feels conceptually different from standard 6–10 minute work, and may become more frequent under this framework. v1's hierarchical trajectory composition and rhetorical primitives are designed to support long-form work, but the actual demands will only become clear after several long pieces are written. v2 likely revisits the rhetorical primitive set with whatever the long-form practice teaches.

### 23.7 Visual feedback during composition

Promoted from v1.5 to Phase 4 because the trajectory and event timelines are central to the agent's reasoning. A static or animated visualization (HTML/SVG) of trajectories, threshold crossings, and event firings will significantly aid both the composer's intuition and the agent's ability to explain a piece.

### 23.8 Should Phonon patch Pyo for true per-object random seeding?

Pyo's single global LCG is the root cause of stochastic non-determinism. A Phonon patch could add a per-object `Stream` field and route `RANDOM_UNIFORM` through it. This would make `Noise`, `PinkNoise`, `Randi`, etc. directly usable in deterministic paths. It is a tractable change to `pyo-src/` (~50 lines of C plus a Python-side seed parameter on each random class) but introduces a maintenance burden when bumping the vendored Pyo. v1 chooses the surrogate-table strategy as lower-risk and faster to ship; v1.5 may revisit if the table-loop limitation becomes audible in practice.

### 23.9 Custom C extensions for chaotic generators

`vdp`, `lorenz` (with rho/sigma/beta), `rossler` (with a/b/c), and `chua` are implemented over Pyo's `Expr` in v1. This is correct and works, but the per-sample interpreter overhead of `Expr` may be prohibitive for the longest-form work. v1.5 may promote one or more of these to a custom Pyo C external in `pyo-src/externals/` (Pyo's stable extension mechanism), giving native-speed integration. The Phonon API surface stays identical; only the backend changes.

### 23.10 OSC MIDI bridge for phones / tablets

Live-mode MIDI works through any USB/Bluetooth controller via Pyo's `portmidi` backend. OSC works through any OSC-capable surface (TouchOSC, Open Stage Control, etc.). Whether to ship a Phonon-default OSC layout (a "default phonon control surface" template for TouchOSC/OSC) is open.

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
    source=vdp(rate=2.13, mu=2.0),  # van der Pol relaxation oscillator, classical mu
)

air = Voice(
    name="air",
    role=Role.AIR_HIGH,
    band=Band(4000, 18000),
    source=pink_noise(),  # seeded surrogate; deterministic
)

primary = Voice(
    name="primary",
    role=Role.PRIMARY_MID,
    band=Band(200, 2000),
    source=lorenz(component="x", sigma=10, rho=28, beta=8/3),  # classical Lorenz
)

secondary = Voice(
    name="secondary",
    role=Role.SECONDARY_MID,
    band=Band(300, 3000),
    source=lorenz(component="y", sigma=10, rho=15.5, beta=8/3),
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
    sample_rate=48000,
    buffer_size=256,
    control_hz=200,
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
| **Block** | One Pyo audio buffer's worth of samples (default 256 at 48kHz = 5.3ms). The atom of audio computation. |
| **Control rate** | The Phonon scheduler cadence at which trajectories, bindings, and crossings are evaluated (default 200 Hz). Not a Pyo concept. |
| **Corpus** | A content-hashed manifest of sample material used by a piece. |
| **Coupling** | A declared relationship between two voices, with a strength signal and a kind. |
| **Crossing** | A predicate that fires when a referenced signal crosses a value with declared direction. |
| **Distortion** | A closed vocabulary of transformations applied to recurrent material on return. |
| **Event** | A structural change to the score, triggered by a Crossing. |
| **Gesture** | A named external input slot (MIDI/OSC) bound to a parameter or action. |
| **Mode** | The relationship between a source value and a target value: ABSOLUTE, OFFSET, or MODULATE. |
| **Performance** | A specific render: `(score, seed, gesture_timeline, render_contract)`. |
| **Phonon** | The framework. Also: the smallest unit of acoustic-mechanical vibration in a medium. |
| **Process** | A continuous signal source or transformation, wrapping one or more PyoObjects. |
| **Reference** | A first-class deferred reference to a named entity by string name. |
| **Render contract** | The pinned tuple `(sample_rate, buffer_size, control_hz, pyo_precision)` that, with seed and gesture timeline, determines bit-exact output. |
| **Rhetoric** | The five long-form primitives: Persistence, Recurrence, Departure, Quotation, Latency. |
| **Role** | A voice's place in the mix: ANCHOR_LOW, AIR_HIGH, PRIMARY_MID, SECONDARY_MID, or CUSTOM. |
| **Scale** | A Roads time scale: SAMPLE, MICRO, MESO, MACRO, or SUPRA. |
| **Score** | The complete piece value: seed, voices, trajectories, couplings, bindings, events, gestures, rhetoric, variance defaults. (Distinct from Pyo's `pattern.Score` class, which Phonon does not import.) |
| **Shape** | A declarative description of a deterministic curve (linear, sigmoid, brown, etc.). |
| **Surrogate** | A seeded deterministic substitute for a non-deterministic Pyo random object (e.g., table-based `white_noise`). |
| **Threshold** | A device that converts a continuous signal into discrete trigger events at crossings; built over Pyo's `Thresh`. |
| **Tick** | One iteration of the Phonon scheduler at `control_hz`. |
| **Trajectory** | A logical control-rate signal living at a declared scale, governing parameter evolution across that scale. |
| **Variance** | Per-trajectory stochastic jitter, with scale-level defaults flowing downward. |
| **Voice** | A named carrier of sound: role, band, source, role-specific parameter contract. |

---

## 26. Appendix C — Verified Pyo class reference

This appendix lists every Pyo class Phonon directly depends on, with verified constructor signatures and behavior, against vendored Pyo 1.0.6. Phonon's process primitive layer is built on these. When the vendored Pyo is updated, this appendix is the reconciliation point.

### Server

```python
Server(sr=44100, nchnls=2, buffersize=256, duplex=1,
       audio="portaudio", jackname="pyo", ichnls=None,
       winhost="directsound", midi="portmidi", verbosity=7)

# Phonon defaults override sr to 48000.
# Backend modes Phonon uses:
#   "manual"     — no audio thread; user calls Server.process() per block. Offline.
#   "portaudio"  — default real-time backend; thread-based. Live.
#   "jack"       — Linux/macOS JACK backend. Live.
#   "coreaudio"  — macOS native. Live.
# Backend modes Phonon avoids:
#   "offline"    — single-threaded but fully internal loop; loses external pumping control.
#   "offline_nb" — non-blocking offline; spawns thread, breaks determinism.
#   "embedded"   — host-driven; for embedded use cases.

Server.boot()                                  # initialize backend
Server.start()                                  # arm/start (offline: blocking; manual: no-op)
Server.stop()                                   # stop audio
Server.shutdown()                               # release backend; required before reconfig
Server.process()                                # manual mode: compute one block
Server.recordOptions(dur=-1, filename=None,
                     fileformat=0, sampletype=0, quality=0.4)
                                                # fileformat: 0=WAV, 1=AIFF, 5=FLAC, 7=OGG
                                                # sampletype: 0=int16, 1=int24, 3=float32, 4=float64
Server.setGlobalSeed(seed)                      # Pyo's per-construction RNG seed (NOT bit-exact)
Server.setCallback(fn)                          # called once per block before DSP; live mode
Server.addMidiEvent(status, data1, data2)       # programmatic MIDI injection; deterministic test path
Server.setMidiInputDevice(idx)
Server.deactivateMidi()                         # before boot, to skip MIDI subsystem
Server.getCurrentTime()                         # samples elapsed, for piece-time derivation
```

### Core building blocks (controls.py, utils.py, _core.py)

```python
Sig(value, mul=1, add=0)                        # constant-as-stream; .value setter
SigTo(value, time=0.025, init=0.0, mul=1, add=0) # linear-ramp click-free; .value setter
Linseg(list, loop=False, initToFirstVal=False, mul=1, add=0)
                                                # list = [(time_s, value), ...]
Fader(fadein=0.01, fadeout=0.1, dur=0, mul=1, add=0)
Adsr(attack=0.01, decay=0.05, sustain=0.707, release=0.1,
     dur=0, mul=1, add=0)
Compare(input, comp, mode="<", mul=1, add=0)    # 0/1 gate; mode in <,<=,>,>=,==,!=
SampHold(input, controlsig, value=0.0, mul=1, add=0)
                                                # samples input when controlsig == value
Snap(input, choice, scale=0, mul=1, add=0)      # snap to scale
Interp(input1, input2, interp=0.5, mul=1, add=0)
```

### Triggers (triggers.py)

```python
Trig()                                           # one-shot trigger; play() emits it
Metro(time=1, poly=1)                            # isochronous trigger generator
Beat(time=0.125, taps=16, w1=80, w2=50, w3=30, poly=1, onlyonce=False)
                                                # algorithmic; aux streams ['tap'], ['amp'], ['dur'], ['end']
Euclide(time=0.125, taps=16, onsets=10, poly=1)  # Euclidean rhythm; same aux streams as Beat
Counter(input, min=0, max=100, dir=0, mul=1, add=0)
                                                # counts triggers; dir 0=up, 1=down, 2=ud
Select(input, value=0, mul=1, add=0)             # trigger when input == value (use with Counter)
TrigEnv(input, table, dur=1, interp=2, mul=1, add=0)
                                                # play envelope on each trigger
TrigVal(input, value=0.0, init=0.0, mul=1, add=0) # latch parameter on trigger (NOT signal-level S&H)
TrigFunc(input, function, arg=None)              # call Python on trigger (live-mode tracker)
Thresh(input, threshold=0.0, dir=0, mul=1, add=0)
                                                # edge trigger; dir 0=rising, 1=falling, 2=both
Change(input, mul=1, add=0)                      # trigger on every value change
TrigRand(input, min=0, max=1, port=0, init=0, mul=1, add=0)
                                                # NON-DETERMINISTIC; not used in deterministic paths
TrigChoice(input, choice, port=0, init=0, mul=1, add=0)
                                                # NON-DETERMINISTIC
Cloud(density=10, poly=1)                        # NON-DETERMINISTIC trigger cloud
```

### Generators (generators.py)

```python
Sine(freq=1000, phase=0, mul=1, add=0)
Phasor(freq=100, phase=0, mul=1, add=0)
LFO(freq=100, sharp=0.5, type=0, mul=1, add=0)
                                                # type: 0=saw up, 1=saw down, 2=square,
                                                #       3=triangle, 4=pulse, 5=bipolar pulse,
                                                #       6=sample-and-hold, 7=modulated sine
SuperSaw(freq=100, detune=0.5, bal=0.7, mul=1, add=0)
FM(carrier=100, ratio=0.5, index=5, mul=1, add=0)
RCOsc(freq=100, sharp=0.25, mul=1, add=0)
SineLoop(freq=1000, feedback=0, mul=1, add=0)
FastSine(freq=1000, initphase=0, quality=1, mul=1, add=0)
Blit(freq=100, harms=40, mul=1, add=0)
Lorenz(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)
                                                # NOTE: NOT a classical Lorenz integrator;
                                                #       pitch/chaos are normalized 0-1 controls.
                                                #       Phonon uses Expr-based custom Lorenz instead.
Rossler(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)  # same caveat
ChenLee(pitch=0.25, chaos=0.5, stereo=False, mul=1, add=0)  # not Chua; different system
Noise(type=0, mul=1, add=0)                      # NON-DETERMINISTIC; replaced by Phonon surrogate
PinkNoise(mul=1, add=0)                          # NON-DETERMINISTIC; replaced
BrownNoise(mul=1, add=0)                         # NON-DETERMINISTIC; replaced
Input(chnl=0, mul=1, add=0)                      # live audio input
```

### Filters and analysis (filters.py, analysis.py)

```python
Tone(input, freq=1000, mul=1, add=0)             # 1-pole LP
Atone(input, freq=1000, mul=1, add=0)            # 1-pole HP
ButLP(input, freq=1000, mul=1, add=0)            # Butterworth LP
ButHP(input, freq=1000, mul=1, add=0)
ButBP(input, freq=1000, q=1, mul=1, add=0)
ButBR(input, freq=1000, q=1, mul=1, add=0)
MoogLP(input, freq=1000, res=0, mul=1, add=0)    # resonant; classical
SVF(input, freq=1000, q=1, type=0, mul=1, add=0) # state-variable
Reson(input, freq=1000, q=1, mul=1, add=0)       # resonant bandpass
Biquad(input, freq=1000, q=1, type=0, mul=1, add=0)
Hilbert(input, mul=1, add=0)
DCBlock(input, mul=1, add=0)
Port(input, risetime=0.05, falltime=0.05, init=0, mul=1, add=0)
                                                # asymmetric lowpass smoother; non-linear glide
Follower(input, freq=20, mul=1, add=0)           # amplitude follower
Follower2(input, risetime=0.01, falltime=0.1, mul=1, add=0)
RMS(input, freq=20, mul=1, add=0)
PeakAmp(input)                                   # for monitoring; not in graph chain
```

### Effects (effects.py)

```python
Delay(input, delay=0.25, feedback=0, maxdelay=1, mul=1, add=0)
SDelay(input, delay=0.25, maxdelay=1, mul=1, add=0)  # static delay (no feedback)
SmoothDelay(input, delay=0.25, feedback=0, crossfade=0.05, maxdelay=1, mul=1, add=0)
Delay1(input, mul=1, add=0)                      # one-sample delay; useful for ODE integrators
WGVerb(input, feedback=0.5, cutoff=5000, bal=0.5, mul=1, add=0)
Freeverb(input, size=0.5, damp=0.5, bal=0.5, mul=1, add=0)
STRev(input, inpos=0.5, revtime=1, cutoff=5000, bal=0.5, roomSize=1, firstRefGain=-3, mul=1, add=0)
Disto(input, drive=0.75, slope=0.5, mul=1, add=0)
FreqShift(input, shift=100, mul=1, add=0)
Chorus(input, depth=1, feedback=0.25, bal=0.5, mul=1, add=0)
```

### Tables (tables.py, tableprocess.py)

```python
DataTable(size, init=None, chnls=1)              # raw float buffer; for surrogate noise tables
NewTable(length, chnls=1, init=None, feedback=0.0)
SndTable(path, chnl=None, start=0, stop=-1, initchnls=1)
HannTable(size=8192)
TableRead(table, freq=1, loop=0, interp=2, mul=1, add=0)
                                                # the surrogate-noise playback path
Looper(table, pitch=1, start=0, dur=1, xfade=20, mode=1, xfadeshape=0,
       startfromloop=False, interp=2, autosmooth=False, mul=1, add=0)
Granulator(table, env, pitch=1, pos=0, dur=0.1, grains=8, basedur=0.1, mul=1, add=0)
                                                # NOTE: density uses Pyo's global LCG; non-deterministic
Pointer2(table, index, interp=4, autosmooth=True, mul=1, add=0)
TableRec(input, table, fadetime=0)               # record a stream into a table
```

### MIDI and OSC (midi.py, opensndctrl.py, listener.py)

```python
Notein(poly=10, scale=0, first=0, last=127, channel=0, mul=1, add=0)
                                                # returns aux streams ['pitch'], ['velocity']
Midictl(ctlnumber, minscale=0, maxscale=1, init=0, channel=0, mul=1, add=0)
Bendin(brange=2, scale=0, channel=0, mul=1, add=0)
Touchin(channel=0, minscale=0, maxscale=1, init=0, mul=1, add=0)
Programin(channel=0, mul=1, add=0)
MidiAdsr(input, attack=0.01, decay=0.05, sustain=0.707, release=0.1, mul=1, add=0)
RawMidi(function)                                # raw MIDI byte callback
MidiListener(function, mididev=None)             # listener thread for raw MIDI

OscReceive(port, address, mul=1, add=0)
OscDataReceive(port, address, function)
OscListReceive(port, address, num=8, mul=1, add=0)
OscSend(input, port, address, host="127.0.0.1")
OscDataSend(types, port, address, host="127.0.0.1")
OscListener(function, port=9001)
```

### Expression (expression.py)

```python
Expr(input, expr="", outs=1, initout=0.0, mul=1, add=0)
# Prefix-syntax DSL with one-sample delay (delay x), conditionals (if x y z),
# trig/log/exp, periodic ramps (~ freq phase), filters (rpole, rzero, cpole, czero),
# multi-output (out chnl signal), variable bindings (let var init body),
# and randoms (randf, randi — NON-DETERMINISTIC; avoid for bit-exact paths).
# Used by Phonon for vdp, lorenz, rossler, chua, custom integrators.
```

### Pattern, Score (pattern.py) — **NOT USED BY PHONON**

Pyo's `Pattern`, `Score`, `CallAfter` schedule Python callbacks on a Metro. Phonon does not import them and never does `from pyo import *` in framework code or example pieces; the name `Score` collides with Phonon's central type.

---

## 27. Appendix D — Source vendoring policy

### Status

Pyo's source is vendored in `pyo-src/` at the root of the Phonon repository, copied wholesale (excluding `.git`, build artifacts, and pyo's `.github/`) from upstream `belangeo/pyo` at tag `1.0.6` (commit dated 2025-03-04). Upstream development appears effectively frozen (no 1.0.7 release as of 2026-04-28); vendoring is therefore a maintenance choice rather than a tracking choice.

### Why vendored, not pinned to a release

- Pyo's wheels on PyPI are 1.0.6, but the framework needs source-level access to (a) plumb a per-object random seed through the C engine if §23.8 is acted on, (b) add custom externals for chaotic integrators (§23.9), and (c) audit the C-side determinism guarantees Phonon depends on.
- Vendoring also pins the framework's dependency exactly: the same Phonon repo at the same commit always builds against the same Pyo source.
- LGPLv3+ compatibility: shipping Pyo's source alongside Phonon's source is well within Pyo's license. Phonon's eventual license must be LGPLv3-compatible if it links Pyo; statically linking imposes additional obligations (must allow recipients to relink against modified Pyo).

### Modification policy

- **Patches land as commits on the main Phonon repo**, modifying files inside `pyo-src/`. They are not stored separately as `.patch` files and not applied at runtime. The git history of the Phonon repo *is* the patch series.
- **Each modifying commit** must include in its message: (a) what changed, (b) why Phonon needs it, (c) whether it could plausibly upstream, and (d) what test verifies the change.
- **No runtime monkey-patching** of Pyo from inside Phonon. If a behavior needs changing, modify the source.
- **Upstream tracking** is opportunistic. If upstream resumes development, pulling new commits is a manual rebase: bump the `pyo-src/` files to the new upstream snapshot, replay any local modifying commits, and run the Pyo audit test.

### What the audit test guards

`tests/test_pyo_audit.py` (Phase 0 deliverable) asserts:

- Every Pyo class Phonon depends on (Appendix C) is importable.
- Constructor signatures match expectations (introspected via `inspect.signature`).
- `Server` has the methods Phonon's renderer calls: `boot`, `start`, `stop`, `shutdown`, `process`, `recordOptions`, `setGlobalSeed`, `setCallback`, `addMidiEvent`, `getCurrentTime`.
- The audio-mode constants Phonon uses (`"manual"`, `"portaudio"`, `"jack"`, `"coreaudio"`) are still recognized.
- The fileformat constants used (`5` for FLAC) still map as expected.

A bumped `pyo-src/` that breaks any of these fails CI loudly. Phonon then either (a) updates its mapping table to track upstream changes or (b) reverts the bump.

### Build

`pip install -e ./pyo-src/` from the Phonon repo root installs the editable Pyo. Native dependencies are inherited from Pyo's `setup.py`:

- macOS: `brew install portaudio portmidi libsndfile liblo libogg libvorbis flac opus mpg123 lame`.
- Linux: `apt install portaudio19-dev libportmidi-dev libsndfile1-dev liblo-dev` (or yum equivalents).
- Windows: vcpkg + MSYS2 mingw64 per Pyo's `scripts/win/`.

Phonon's CI matrix builds Pyo from `pyo-src/` on macOS-arm64, macOS-x86_64, ubuntu-latest, and windows-latest, then runs Phonon's test suite against the built extension. The Pyo audit test runs first; if it fails, the rest of the suite is skipped.

### Documentation

The Pyo upstream Sphinx docs (rendered HTML at `pyo-src/docs/` and source at `pyo-src/documentation/`) are kept available locally for reference but are not built or hosted by Phonon. Phonon's documentation site references Pyo class names and links externally to https://belangeo.github.io/pyo/ where helpful.

---

*End of design specification, v1.1.*
