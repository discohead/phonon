"""Pyo audit — pins the constructor signature of every class in design spec
Appendix C against vendored Pyo 1.0.6.

This test runs FIRST in CI (per FR-041) and short-circuits the rest of the
suite on failure. Its purpose is to catch upstream Pyo signature drift early
— before Phonon's process primitive layer is built on top of these classes.

Each entry below maps a Pyo class name to a tuple `(param_name, default)`
pairs in declaration order, excluding `self`. The sentinel `_REQUIRED` marks
parameters with no default. When Pyo's signature changes, edit the expected
table and the corresponding line in design spec Appendix C in the same PR.
"""

import inspect
import platform

import pytest

pyo = pytest.importorskip(  # noqa: PT017 — pyo is required for this test
    "pyo",
    reason="vendored pyo not built; run `pip install -e ./pyo-src/`",
)


_REQUIRED = inspect.Parameter.empty


# ---------------------------------------------------------------------------
# Expected signatures, pinned against vendored Pyo 1.0.6 at commit time of
# the Phase 0 spec (see design spec §1.0.6 vendoring note in CLAUDE.md).
# ---------------------------------------------------------------------------

EXPECTED_SIGNATURES: dict[str, list[tuple[str, object]]] = {
    "Server": [("sr", 44100), ("nchnls", 2), ("buffersize", 256), ("duplex", 1),
               ("audio", "portaudio"), ("jackname", "pyo"), ("ichnls", None),
               ("winhost", "directsound"), ("midi", "portmidi"), ("verbosity", 7)],
    # controls / utils
    "Sig":     [("value", _REQUIRED), ("mul", 1), ("add", 0)],
    "SigTo":   [("value", _REQUIRED), ("time", 0.025), ("init", 0.0), ("mul", 1), ("add", 0)],
    "Linseg":  [("list", _REQUIRED), ("loop", False), ("initToFirstVal", False), ("mul", 1), ("add", 0)],
    "Fader":   [("fadein", 0.01), ("fadeout", 0.1), ("dur", 0), ("mul", 1), ("add", 0)],
    "Adsr":    [("attack", 0.01), ("decay", 0.05), ("sustain", 0.707), ("release", 0.1),
                ("dur", 0), ("mul", 1), ("add", 0)],
    "Compare": [("input", _REQUIRED), ("comp", _REQUIRED), ("mode", "<"), ("mul", 1), ("add", 0)],
    "SampHold":[("input", _REQUIRED), ("controlsig", _REQUIRED), ("value", 0.0),
                ("mul", 1), ("add", 0)],
    "Snap":    [("input", _REQUIRED), ("choice", _REQUIRED), ("scale", 0), ("mul", 1), ("add", 0)],
    "Interp":  [("input", _REQUIRED), ("input2", _REQUIRED), ("interp", 0.5), ("mul", 1), ("add", 0)],
    # triggers
    "Trig":      [],
    "Metro":     [("time", 1), ("poly", 1)],
    "Beat":      [("time", 0.125), ("taps", 16), ("w1", 80), ("w2", 50), ("w3", 30),
                  ("poly", 1), ("onlyonce", False)],
    "Euclide":   [("time", 0.125), ("taps", 16), ("onsets", 10), ("poly", 1)],
    "Counter":   [("input", _REQUIRED), ("min", 0), ("max", 100), ("dir", 0), ("mul", 1), ("add", 0)],
    "Select":    [("input", _REQUIRED), ("value", 0), ("mul", 1), ("add", 0)],
    "TrigEnv":   [("input", _REQUIRED), ("table", _REQUIRED), ("dur", 1), ("interp", 2),
                  ("mul", 1), ("add", 0)],
    "TrigVal":   [("input", _REQUIRED), ("value", 0.0), ("init", 0.0), ("mul", 1), ("add", 0)],
    "TrigFunc":  [("input", _REQUIRED), ("function", _REQUIRED), ("arg", None)],
    "Thresh":    [("input", _REQUIRED), ("threshold", 0.0), ("dir", 0), ("mul", 1), ("add", 0)],
    "Change":    [("input", _REQUIRED), ("mul", 1), ("add", 0)],
    "TrigRand":  [("input", _REQUIRED), ("min", 0.0), ("max", 1.0), ("port", 0.0),
                  ("init", 0.0), ("mul", 1), ("add", 0)],
    "TrigChoice":[("input", _REQUIRED), ("choice", _REQUIRED), ("port", 0.0),
                  ("init", 0.0), ("mul", 1), ("add", 0)],
    "Cloud":     [("density", 10), ("poly", 1)],
    # generators
    "Sine":     [("freq", 1000), ("phase", 0), ("mul", 1), ("add", 0)],
    "Phasor":   [("freq", 100), ("phase", 0), ("mul", 1), ("add", 0)],
    "LFO":      [("freq", 100), ("sharp", 0.5), ("type", 0), ("mul", 1), ("add", 0)],
    "SuperSaw": [("freq", 100), ("detune", 0.5), ("bal", 0.7), ("mul", 1), ("add", 0)],
    "FM":       [("carrier", 100), ("ratio", 0.5), ("index", 5), ("mul", 1), ("add", 0)],
    "RCOsc":    [("freq", 100), ("sharp", 0.25), ("mul", 1), ("add", 0)],
    "SineLoop": [("freq", 1000), ("feedback", 0), ("mul", 1), ("add", 0)],
    "FastSine": [("freq", 1000), ("initphase", 0.0), ("quality", 1), ("mul", 1), ("add", 0)],
    "Blit":     [("freq", 100), ("harms", 40), ("mul", 1), ("add", 0)],
    "Lorenz":   [("pitch", 0.25), ("chaos", 0.5), ("stereo", False), ("mul", 1), ("add", 0)],
    "Rossler":  [("pitch", 0.25), ("chaos", 0.5), ("stereo", False), ("mul", 1), ("add", 0)],
    "ChenLee":  [("pitch", 0.25), ("chaos", 0.5), ("stereo", False), ("mul", 1), ("add", 0)],
    "Noise":      [("mul", 1), ("add", 0)],
    "PinkNoise":  [("mul", 1), ("add", 0)],
    "BrownNoise": [("mul", 1), ("add", 0)],
    "Input":      [("chnl", 0), ("mul", 1), ("add", 0)],
    # filters / analysis
    "Tone":     [("input", _REQUIRED), ("freq", 1000), ("mul", 1), ("add", 0)],
    "Atone":    [("input", _REQUIRED), ("freq", 1000), ("mul", 1), ("add", 0)],
    "ButLP":    [("input", _REQUIRED), ("freq", 1000), ("mul", 1), ("add", 0)],
    "ButHP":    [("input", _REQUIRED), ("freq", 1000), ("mul", 1), ("add", 0)],
    "ButBP":    [("input", _REQUIRED), ("freq", 1000), ("q", 1), ("mul", 1), ("add", 0)],
    "ButBR":    [("input", _REQUIRED), ("freq", 1000), ("q", 1), ("mul", 1), ("add", 0)],
    "MoogLP":   [("input", _REQUIRED), ("freq", 1000), ("res", 0), ("mul", 1), ("add", 0)],
    "SVF":      [("input", _REQUIRED), ("freq", 1000), ("q", 1), ("type", 0), ("mul", 1), ("add", 0)],
    "Reson":    [("input", _REQUIRED), ("freq", 1000), ("q", 1), ("mul", 1), ("add", 0)],
    "Biquad":   [("input", _REQUIRED), ("freq", 1000), ("q", 1), ("type", 0), ("mul", 1), ("add", 0)],
    "Hilbert":  [("input", _REQUIRED), ("mul", 1), ("add", 0)],
    "DCBlock":  [("input", _REQUIRED), ("mul", 1), ("add", 0)],
    "Port":     [("input", _REQUIRED), ("risetime", 0.05), ("falltime", 0.05),
                 ("init", 0), ("mul", 1), ("add", 0)],
    "Follower": [("input", _REQUIRED), ("freq", 20), ("mul", 1), ("add", 0)],
    "Follower2":[("input", _REQUIRED), ("risetime", 0.01), ("falltime", 0.1), ("mul", 1), ("add", 0)],
    "RMS":      [("input", _REQUIRED), ("function", None), ("mul", 1), ("add", 0)],
    "PeakAmp":  [("input", _REQUIRED), ("function", None), ("mul", 1), ("add", 0)],
    # effects
    "Delay":      [("input", _REQUIRED), ("delay", 0.25), ("feedback", 0), ("maxdelay", 1),
                   ("mul", 1), ("add", 0)],
    "SDelay":     [("input", _REQUIRED), ("delay", 0.25), ("maxdelay", 1), ("mul", 1), ("add", 0)],
    "SmoothDelay":[("input", _REQUIRED), ("delay", 0.25), ("feedback", 0),
                   ("crossfade", 0.05), ("maxdelay", 1), ("mul", 1), ("add", 0)],
    "Delay1":     [("input", _REQUIRED), ("mul", 1), ("add", 0)],
    "WGVerb":     [("input", _REQUIRED), ("feedback", 0.5), ("cutoff", 5000),
                   ("bal", 0.5), ("mul", 1), ("add", 0)],
    "Freeverb":   [("input", _REQUIRED), ("size", 0.5), ("damp", 0.5),
                   ("bal", 0.5), ("mul", 1), ("add", 0)],
    "STRev":      [("input", _REQUIRED), ("inpos", 0.5), ("revtime", 1), ("cutoff", 5000),
                   ("bal", 0.5), ("roomSize", 1), ("firstRefGain", -3), ("mul", 1), ("add", 0)],
    "Disto":      [("input", _REQUIRED), ("drive", 0.75), ("slope", 0.5), ("mul", 1), ("add", 0)],
    "FreqShift":  [("input", _REQUIRED), ("shift", 100), ("mul", 1), ("add", 0)],
    "Chorus":     [("input", _REQUIRED), ("depth", 1), ("feedback", 0.25),
                   ("bal", 0.5), ("mul", 1), ("add", 0)],
    # tables
    "DataTable":  [("size", _REQUIRED), ("chnls", 1), ("init", None)],
    "NewTable":   [("length", _REQUIRED), ("chnls", 1), ("init", None), ("feedback", 0.0)],
    "SndTable":   [("path", None), ("chnl", None), ("start", 0), ("stop", None), ("initchnls", 1)],
    "HannTable":  [("size", 8192)],
    "TableRead":  [("table", _REQUIRED), ("freq", 1), ("loop", 0), ("interp", 2),
                   ("mul", 1), ("add", 0)],
    "Looper":     [("table", _REQUIRED), ("pitch", 1), ("start", 0), ("dur", 1.0),
                   ("xfade", 20), ("mode", 1), ("xfadeshape", 0),
                   ("startfromloop", False), ("interp", 2), ("autosmooth", False),
                   ("mul", 1), ("add", 0)],
    "Granulator": [("table", _REQUIRED), ("env", _REQUIRED), ("pitch", 1), ("pos", 0),
                   ("dur", 0.1), ("grains", 8), ("basedur", 0.1), ("mul", 1), ("add", 0)],
    "Pointer2":   [("table", _REQUIRED), ("index", _REQUIRED), ("interp", 4),
                   ("autosmooth", True), ("mul", 1), ("add", 0)],
    "TableRec":   [("input", _REQUIRED), ("table", _REQUIRED), ("fadetime", 0)],
    # MIDI
    "Notein":     [("poly", 10), ("scale", 0), ("first", 0), ("last", 127),
                   ("channel", 0), ("mul", 1), ("add", 0)],
    "Midictl":    [("ctlnumber", _REQUIRED), ("minscale", 0), ("maxscale", 1),
                   ("init", 0), ("channel", 0), ("mul", 1), ("add", 0)],
    "Bendin":     [("brange", 2), ("scale", 0), ("channel", 0), ("mul", 1), ("add", 0)],
    "Touchin":    [("minscale", 0), ("maxscale", 1), ("init", 0), ("channel", 0),
                   ("mul", 1), ("add", 0)],
    "Programin":  [("channel", 0), ("mul", 1), ("add", 0)],
    "MidiAdsr":   [("input", _REQUIRED), ("attack", 0.01), ("decay", 0.05),
                   ("sustain", 0.7), ("release", 0.1), ("mul", 1), ("add", 0)],
    "RawMidi":    [("function", _REQUIRED)],
    "MidiListener":[("function", _REQUIRED), ("mididev", -1), ("reportdevice", False)],
    # OSC
    "OscReceive":     [("port", _REQUIRED), ("address", _REQUIRED), ("mul", 1), ("add", 0)],
    "OscDataReceive": [("port", _REQUIRED), ("address", _REQUIRED), ("function", _REQUIRED)],
    "OscListReceive": [("port", _REQUIRED), ("address", _REQUIRED), ("num", 8),
                       ("mul", 1), ("add", 0)],
    "OscSend":        [("input", _REQUIRED), ("port", _REQUIRED), ("address", _REQUIRED),
                       ("host", "127.0.0.1")],
    "OscDataSend":    [("types", _REQUIRED), ("port", _REQUIRED), ("address", _REQUIRED),
                       ("host", "127.0.0.1")],
    "OscListener":    [("function", _REQUIRED), ("port", 9000)],
    # expression
    "Expr": [("input", _REQUIRED), ("expr", ""), ("outs", 1), ("initout", 0.0),
             ("mul", 1), ("add", 0)],
}


# Server methods that Phonon uses (FR-033). They must be present and callable.
EXPECTED_SERVER_METHODS = (
    "boot", "start", "stop", "shutdown", "process",
    "recordOptions", "setGlobalSeed", "setCallback",
    "addMidiEvent", "getCurrentTime",
)

# Audio backend modes Phonon constructs Servers with (FR-034). Cross-platform
# subset: "manual" everywhere; "portaudio" everywhere; "jack" on Linux/macOS;
# "coreaudio" on macOS. We check that the kwarg is *accepted* (Server constructs
# without raising), then immediately shut down — no audio I/O is started.
EXPECTED_AUDIO_MODES = ("manual", "portaudio")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("class_name,expected", sorted(EXPECTED_SIGNATURES.items()))
def test_pyo_class_signature_matches_appendix_c(class_name, expected):
    cls = getattr(pyo, class_name, None)
    assert cls is not None, f"pyo.{class_name} is missing"

    sig = inspect.signature(cls.__init__)
    actual = []
    for pname, p in sig.parameters.items():
        if pname == "self":
            continue
        actual.append((pname, p.default))

    assert actual == expected, (
        f"pyo.{class_name} signature drift:\n"
        f"  expected: {expected}\n"
        f"  actual:   {actual}\n"
        f"Update tests/test_pyo_audit.py and design spec Appendix C in the same PR."
    )


@pytest.mark.parametrize("method_name", EXPECTED_SERVER_METHODS)
def test_pyo_server_has_method(method_name):
    method = getattr(pyo.Server, method_name, None)
    assert callable(method), (
        f"pyo.Server.{method_name} is missing or not callable"
    )


@pytest.mark.parametrize("audio_mode", EXPECTED_AUDIO_MODES)
def test_pyo_server_accepts_audio_mode(audio_mode):
    """Constructing a Server with each accepted audio kwarg must not raise."""
    server = pyo.Server(audio=audio_mode)
    try:
        # No boot() — we only verify construction; some backends would probe
        # devices on boot which is undesirable in CI.
        assert server is not None
    finally:
        server.shutdown()


@pytest.mark.skipif(
    platform.system() not in ("Darwin", "Linux"),
    reason="JACK backend is Linux/macOS only",
)
def test_pyo_server_accepts_jack_audio_mode():
    """JACK backend accepts construction; we don't assert it boots."""
    server = pyo.Server(audio="jack")
    try:
        assert server is not None
    finally:
        server.shutdown()


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="CoreAudio backend is macOS only",
)
def test_pyo_server_accepts_coreaudio_mode():
    server = pyo.Server(audio="coreaudio")
    try:
        assert server is not None
    finally:
        server.shutdown()
