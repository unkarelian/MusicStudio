"""Rendering to audio, so a person can actually hear the thing.

Wavetable and additive oscillators summed into a stereo buffer and written as a
16-bit WAV. It is not a sample library and is not trying to be -- it is the
equivalent of rendering a sprite to a PNG at 8x. The point is that somebody can
open the file and find out whether the music works, which is not a question the
ASCII views can answer.

Three things matter more than the oscillators do, because they are what let an
ear separate the parts -- and separating the parts is the whole reason to listen:

**Voices are seated in a stereo field.** Each voice gets a pan position, either
its own ``pan`` or a seat taken from where the instrument sits in an orchestra.
Two lines in the same register are much easier to tell apart when they come
from different places.

**Tables are band-limited per note.** A sawtooth with 23 partials is fine at C3
and folds back into inharmonic noise at C7; the oscillator only includes the
partials that fit under Nyquist for the pitch it is playing.

**There is a room.** A style-appropriate reverb (long for ambient, short for
chamber, nearly dry for chiptune) when numpy is installed. Dry synthesized notes
sound shorter and more disconnected than the writing is, which misleads the ear
about the phrasing.

The core path is pure standard library. With the ``analysis`` extra installed,
numpy is used for speed, the reverb, and the instrument models in ``synth.py``
-- moving spectra, formants, onset noise, slurs, inharmonic bars and real drum
strokes in place of one fixed oscillator per voice. Without numpy the render is
dry and plainly synthetic, but it is the same piece: the models change how a
note sounds, never which notes there are, when they start, or where they sit.

For sampled instruments, :func:`save_wav_soundfont` hands the MIDI export to
FluidSynth with a SoundFont. That is the most realistic render available and
the only one that needs anything outside Python.
"""

from __future__ import annotations

import math
import os
import random
import shutil
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path

from .doc import Piece, Voice
from .render import Render, render
from .theory import TPQ

SR = 44100
TABLE = 2048
NYQUIST = SR / 2

#: ``(harmonic, amplitude)`` pairs plus an ADSR envelope in seconds, per timbre.
#: Odd harmonics read as hollow and reedy, a full series as bright and brassy;
#: the attack time does more for the character than the spectrum does.
#: ``vibrato`` is depth as a fraction of the frequency, for sustained timbres.
VOICES: dict[str, dict] = {
    "bow":     {"partials": [(n, 1 / n ** 1.4) for n in range(1, 12)],
                "adsr": (0.09, 0.10, 0.75, 0.22), "vibrato": 0.0035},
    "pad":     {"partials": [(n, 1 / n ** 1.7) for n in range(1, 9)],
                "adsr": (0.45, 0.30, 0.85, 0.70), "vibrato": 0.0018},
    "reed":    {"partials": [(n, 1 / n ** 1.2) for n in range(1, 14, 2)],
                "adsr": (0.05, 0.08, 0.80, 0.14), "vibrato": 0.0025},
    "flute":   {"partials": [(1, 1.0), (2, 0.22), (3, 0.07), (4, 0.03)],
                "adsr": (0.07, 0.06, 0.86, 0.16), "vibrato": 0.003},
    "brass":   {"partials": [(n, 1 / n ** 1.15) for n in range(1, 16)],
                "adsr": (0.045, 0.14, 0.72, 0.18), "vibrato": 0.0015},
    "pluck":   {"partials": [(n, 1 / n ** 1.3) for n in range(1, 13)],
                "adsr": (0.004, 0.55, 0.02, 0.20)},
    "struck":  {"partials": [(1, 1.0), (2, 0.42), (3, 0.20), (4, 0.13), (5, 0.07),
                             (6, 0.04), (8, 0.02)],
                "adsr": (0.005, 0.85, 0.06, 0.35)},
    "bell":    {"partials": [(1, 1.0), (2.76, 0.52), (5.4, 0.28), (8.9, 0.16)],
                "adsr": (0.003, 1.5, 0.02, 0.8)},
    "saw":     {"partials": [(n, 1 / n) for n in range(1, 24)],
                "adsr": (0.01, 0.12, 0.80, 0.10)},
    "pulse50": {"partials": [(n, 1 / n) for n in range(1, 24, 2)],
                "adsr": (0.005, 0.05, 0.90, 0.04)},
    "pulse25": {"partials": [(n, abs(math.sin(math.pi * n * 0.25)) / n)
                             for n in range(1, 24)],
                "adsr": (0.005, 0.05, 0.90, 0.04)},
    "pulse12": {"partials": [(n, abs(math.sin(math.pi * n * 0.125)) / n)
                             for n in range(1, 24)],
                "adsr": (0.005, 0.05, 0.90, 0.04)},
    "tri":     {"partials": [(n, (1 / n ** 2) * (1 if (n // 2) % 2 == 0 else -1))
                             for n in range(1, 16, 2)],
                "adsr": (0.005, 0.05, 0.92, 0.04)},
    "noise":   {"partials": None, "adsr": (0.001, 0.09, 0.0, 0.05)},
}

#: Where an instrument sits, -1 (hard left) .. 1 (hard right), after a standard
#: orchestral seating: violins left, low strings right, winds centre, brass
#: right-of-centre, harp and keyboards left. Anything not listed is seated by
#: :func:`pan_positions` so that unlisted voices still spread out.
SEATS: dict[str, float] = {
    "violin": -0.5, "viola": 0.15, "cello": 0.4, "contrabass": 0.5,
    "strings": -0.2, "pizz_strings": -0.3, "tremolo_strings": -0.25,
    "flute": -0.15, "piccolo": -0.2, "oboe": 0.1, "english_horn": 0.15,
    "clarinet": -0.1, "bassoon": 0.2,
    "horn": -0.3, "trumpet": 0.3, "trombone": 0.45, "tuba": 0.5,
    "harp": -0.6, "piano": -0.1, "celesta": -0.55, "music_box": -0.4,
    "glockenspiel": 0.55, "vibraphone": 0.45, "marimba": 0.4, "timpani": 0.25,
    "choir": 0.0, "kick": 0.0, "snare": 0.05, "hat": 0.3, "ride": -0.3,
    "crash": -0.4,
}

#: Reverb per style: ``(decay seconds to -60 dB, wet mix)``. Chiptune is nearly
#: dry because the idiom is; ambient is long because space is its material.
ROOMS: dict[str, tuple[float, float]] = {
    "orchestral": (2.0, 0.24), "chamber": (1.3, 0.18), "piano": (1.5, 0.16),
    "ambient": (3.6, 0.36), "chiptune": (0.35, 0.05), "freeform": (1.6, 0.18),
    "electronic": (1.1, 0.12),
}

_tables: dict[tuple[str, int], array] = {}

try:                                   # pragma: no cover - depends on the extras
    import numpy as _np
except ImportError:                    # pragma: no cover
    _np = None


def has_fast_path() -> bool:
    """Whether numpy is available, which buys speed, vibrato and the reverb."""
    return _np is not None


# --------------------------------------------------------------------------
# oscillators
# --------------------------------------------------------------------------

def _harmonic(spec: dict) -> bool:
    """A wavetable holds one cycle, so it can only hold whole-number partials."""
    return spec["partials"] is not None and all(
        float(p).is_integer() for p, _ in spec["partials"])


def _partials_under(spec: dict, freq: float) -> list[tuple[float, float]]:
    """The partials that fit below Nyquist at this pitch (always the fundamental)."""
    keep = [(p, a) for p, a in spec["partials"] if p * freq < NYQUIST * 0.95]
    return keep or spec["partials"][:1]


def _wavetable(timbre: str, freq: float) -> array:
    """One band-limited cycle of the timbre at this pitch, normalized and cached.

    Cached by how many partials survive, not by pitch, so a whole piece needs a
    handful of tables per timbre rather than one per note.
    """
    spec = VOICES.get(timbre, VOICES["bow"])
    parts = _partials_under(spec, freq)
    key = (timbre, len(parts))
    if key in _tables:
        return _tables[key]
    tab = array("d", [0.0]) * TABLE
    for partial, amp in parts:
        w = 2 * math.pi * int(partial) / TABLE
        for i in range(TABLE):
            tab[i] += amp * math.sin(w * i)
    peak = max(abs(v) for v in tab) or 1.0
    for i in range(TABLE):
        tab[i] /= peak
    _tables[key] = tab
    return tab


def _envelope(n: int, adsr: tuple[float, float, float, float]) -> array:
    """A per-sample ADSR curve of exactly ``n`` samples."""
    a, d, s, r = adsr
    env = array("d", [0.0]) * n
    ai = min(n, int(a * SR)) or 1
    di = min(max(0, n - ai), int(d * SR))
    ri = min(max(0, n - ai - di), int(r * SR))
    si = max(0, n - ai - di - ri)
    i = 0
    for k in range(min(ai, n)):
        env[i] = k / ai
        i += 1
    for k in range(di):
        env[i] = 1.0 + (s - 1.0) * (k / max(1, di))
        i += 1
    for _ in range(si):
        env[i] = s
        i += 1
    start = env[i - 1] if i else s
    for k in range(ri):
        env[i] = start * (1.0 - k / max(1, ri))
        i += 1
    return env


def _envelope_np(n: int, adsr: tuple[float, float, float, float]):
    """:func:`_envelope`, vectorized; the two must agree sample for sample."""
    np = _np
    a, d, s, r = adsr
    ai = min(n, int(a * SR)) or 1
    di = min(max(0, n - ai), int(d * SR))
    ri = min(max(0, n - ai - di), int(r * SR))
    si = max(0, n - ai - di - ri)
    att = np.arange(min(ai, n)) / ai
    dec = 1.0 + (s - 1.0) * (np.arange(di) / max(1, di))
    sus = np.full(si, s)
    head = np.concatenate([att, dec, sus])
    start = head[-1] if len(head) else s
    rel = start * (1.0 - np.arange(ri) / max(1, ri))
    out = np.concatenate([head, rel])
    return np.pad(out, (0, n - len(out))) if len(out) < n else out[:n]


# --------------------------------------------------------------------------
# time and space
# --------------------------------------------------------------------------

def _tick_seconds(piece: Piece):
    """Ticks -> seconds through the tempo map, as a lookup over its marks."""
    import bisect
    marks = []
    elapsed = 0.0
    tempo_map = piece.tempo_map()
    for i, (tick, bpm) in enumerate(tempo_map):
        spb = 60.0 / max(1.0, bpm) / TPQ
        marks.append((tick, elapsed, spb))
        if i + 1 < len(tempo_map):
            elapsed += (tempo_map[i + 1][0] - tick) * spb
    starts = [m[0] for m in marks]

    def convert(t: int) -> float:
        m = marks[max(0, bisect.bisect_right(starts, t) - 1)]
        return m[1] + (t - m[0]) * m[2]

    return convert


def pan_positions(piece: Piece) -> dict[str, float]:
    """Each voice's stereo seat.

    An explicit ``Voice.pan`` wins. Otherwise the instrument's orchestral seat;
    otherwise voices fan out alternately left and right. Bass and percussion
    roles are pulled toward the centre either way -- low end that comes from one
    side sounds like a fault in the speakers, not like a seating plan.
    """
    out: dict[str, float] = {}
    fan = [-0.35, 0.35, -0.6, 0.6, -0.15, 0.15, -0.75, 0.75]
    used: dict[float, int] = {}
    spare = 0
    for v in piece.voices:
        if v.pan is not None:
            out[v.name] = float(v.pan)
            continue
        seat = SEATS.get(v.instrument)
        if seat is None:
            seat = fan[spare % len(fan)]
            spare += 1
        # Two violins on the same seat would sum to one louder violin; nudge
        # repeats apart so a doubled instrument is still two players.
        k = used.get(seat, 0)
        used[seat] = k + 1
        seat = seat + (0.12 * ((k + 1) // 2) * (1 if k % 2 else -1))
        if v.role in ("bass", "percussion") or v.inst.percussive:
            seat *= 0.4
        out[v.name] = max(-1.0, min(1.0, seat))
    return out


def _gains(pan: float) -> tuple[float, float]:
    """Equal-power panning: the voice is as loud in the middle as at the side."""
    theta = (pan + 1.0) * math.pi / 4
    return math.cos(theta), math.sin(theta)


# --------------------------------------------------------------------------
# synthesis
# --------------------------------------------------------------------------

def synthesize(piece: Piece, rend: Render | None = None, *, tail: float = 1.5,
               gain: float = 0.72, stereo: bool = True,
               reverb: bool | None = None, models: bool | None = None,
               strict: bool = False, engines: dict | None = None):
    """Render to sample buffers: ``(left, right)``, or ``(mono, mono)``.

    A voice that asks for an engine this machine cannot run (a voicebank that
    is not installed, a SoundFont voice without FluidSynth) is played by the
    next engine down, with a warning. ``strict=True`` raises instead, which is
    what a test of an engine wants; ``engines``, if given, is filled with
    ``{voice: engine}`` for every voice rendered whole, so a caller can see who
    actually sang.

    ``reverb=None`` and ``models=None`` both mean "if numpy is available".
    ``models`` plays each voice through its instrument model (``synth.py``)
    instead of a fixed oscillator; it changes how the notes sound and nothing
    about which notes there are. Returns numpy arrays on the fast path and
    ``array('d')`` buffers otherwise; :func:`save_wav` takes either.
    """
    r = rend if rend is not None else render(piece)
    to_sec = _tick_seconds(piece)
    room = ROOMS.get(piece.style, ROOMS["freeform"])
    how = (piece.meta.get("master") or {}).get("room")
    if how:
        # The piece's own room: (seconds of tail, how much of it), in place of
        # the style's. A pop vocal wants far less of it than a string section.
        room = (float(how.get("decay", room[0])), float(how.get("wet", room[1])))
    use_reverb = (has_fast_path() if reverb is None else reverb) and room[1] > 0
    if use_reverb and not has_fast_path():
        raise RuntimeError("reverb needs numpy; `uv sync --extra analysis`, or "
                           "pass reverb=False")
    tail = max(tail, room[0] * 0.8 if use_reverb else 0.0)
    end = max((n.end for n in r.notes), default=piece.total_ticks)
    total = int((to_sec(end) + tail) * SR) + 1
    pans = pan_positions(piece) if stereo else {v.name: 0.0 for v in piece.voices}
    voices = {v.name: v for v in piece.voices}
    use_models = has_fast_path() if models is None else models
    if use_models and not has_fast_path():
        raise RuntimeError("instrument models need numpy; `uv sync --extra "
                           "analysis`, or pass models=False")
    send = None
    if has_fast_path():
        left, right, send = _synth_numpy(
            r.notes, voices, pans, to_sec, total, gain, use_models,
            1.0 if stereo else 0.0, voice_fx(piece, to_sec, r.notes),
            prerendered(piece, r.notes, to_sec, total, pans, strict=strict,
                        engines=engines) if use_models else None)
    else:
        lost = _lost_without_numpy(piece)
        if lost and strict:
            raise RuntimeError(f"this render needs numpy (`uv sync --extra "
                               f"analysis`): {lost}")
        if lost:
            import warnings
            warnings.warn(f"rendering without numpy, so this is not the piece as "
                          f"written: {lost}. `uv sync --extra analysis` renders "
                          f"all of it.", stacklevel=2)
        left, right = _synth_python(r.notes, voices, pans, to_sec, total, gain)
    if use_reverb:
        wet_l, wet_r = _reverb(left, right, *room, send=send)
        dead = stops(piece, to_sec)
        if dead:
            # The room stops with the band: the tail of what came before a
            # stop is taken out, so what is kept through it is heard dry.
            live = _np.ones(len(left))
            for lo, hi, _ in dead:
                _fade_out(live, lo, hi)
            wet_l = left + (wet_l - left) * live
            wet_r = right + (wet_r - right) * live
        left, right = wet_l, wet_r
    return left, right


def _fade_out(gain, lo: int, hi: int, ms: float = 4.0) -> None:
    """Take ``gain`` to zero across ``lo..hi`` in place, with a few
    milliseconds of ramp at each end so the cut is silent, not a click."""
    np = _np
    lo, hi = max(0, lo), min(len(gain), hi)
    if hi <= lo:
        return
    k = max(1, min(int(ms * SR / 1000), (hi - lo) // 2))
    shape = np.zeros(hi - lo)
    shape[:k] = np.linspace(1.0, 0.0, k)
    shape[-k:] = np.linspace(0.0, 1.0, k)
    gain[lo:hi] = np.minimum(gain[lo:hi], shape)


def _lost_without_numpy(piece: Piece) -> str:
    """What the pure-stdlib render leaves out of this piece, in words. It
    plays the same notes; it has no per-voice processing and no singers, and a
    fader that is silently ignored is a different mix, so it must say so."""
    from .render import AUDIO_ONLY

    def is_singer(instrument: str) -> bool:     # vocal.py itself needs numpy
        return instrument.startswith("singer")
    fx = sorted({op.kind for v in piece.voices if not v.muted
                 for op in v.ops if op.enabled and op.kind in AUDIO_ONLY})
    sung = [v.name for v in piece.voices if not v.muted and is_singer(v.instrument)]
    sampled = [v.name for v in piece.voices if not v.muted and v.engine == "soundfont"]
    parts = []
    if fx:
        parts.append(f"the {', '.join(fx)} ops are ignored")
    if sung:
        parts.append(f"{', '.join(sung)} will not sing (a plain tone instead)")
    if sampled:
        parts.append(f"{', '.join(sampled)} will not be sampled")
    return "; ".join(parts)


def _note_plan(n, voice: Voice, to_sec, total: int, gain: float):
    """Where a note lands in the buffer and how loud, or None if it does not."""
    start = int(to_sec(n.start) * SR)
    dur = max(0.03, to_sec(n.end) - to_sec(n.start))
    inst = voice.inst
    spec = VOICES.get(inst.timbre, VOICES["bow"])
    length = min(int((dur + spec["adsr"][3]) * SR), total - start)
    if length <= 0 or start < 0:
        return None
    amp = gain * (n.velocity / 127.0) ** 1.4 * (0.5 if inst.percussive else 1.0)
    freq = 440.0 * 2 ** ((n.pitch - 69 + (0.0 if inst.percussive else n.tune)) / 12.0)
    return start, length, amp, freq, spec, inst.timbre


def _synth_python(notes, voices, pans, to_sec, total, gain):
    left = array("d", [0.0]) * total
    right = array("d", [0.0]) * total
    rng = random.Random(1729)
    for n in notes:
        plan = _note_plan(n, voices[n.voice], to_sec, total, gain)
        if plan is None:
            continue
        start, length, amp, freq, spec, timbre = plan
        gl, gr = _gains(pans.get(n.voice, 0.0))
        env = _envelope(length, spec["adsr"])
        if spec["partials"] is None:
            for i in range(length):
                v = rng.uniform(-1.0, 1.0) * env[i] * amp
                left[start + i] += v * gl
                right[start + i] += v * gr
            continue
        if _harmonic(spec):
            table = _wavetable(timbre, freq)
            inc = freq * TABLE / SR
            phase = 0.0
            for i in range(length):
                v = table[int(phase) & (TABLE - 1)] * env[i] * amp
                left[start + i] += v * gl
                right[start + i] += v * gr
                phase += inc
            continue
        parts = _partials_under(spec, freq)
        norm = sum(a for _, a in parts) or 1.0
        ws = [(2 * math.pi * freq * p / SR, a / norm) for p, a in parts]
        for i in range(length):
            v = sum(a * math.sin(w * i) for w, a in ws) * env[i] * amp
            left[start + i] += v * gl
            right[start + i] += v * gr
    return left, right


def stops(piece: Piece, to_sec) -> list[tuple[int, int, tuple]]:
    """The piece's hard stops as ``(first sample, last sample, voices kept)``.

    A stop is the whole band cut to nothing -- ringing notes, releases and the
    room's tail -- while the voices in ``keep`` carry on, dry. It lives in
    ``meta['master']['stops']`` because it belongs to no one voice."""
    out = []
    for st in (piece.meta.get("master") or {}).get("stops") or []:
        lo, hi = piece.tick_of(st["from"]), piece.tick_of(st["until"])
        if hi > lo:
            out.append((int(to_sec(lo) * SR), int(to_sec(hi) * SR), tuple(st.get("keep") or ())))
    return out


def voice_fx(piece: Piece, to_sec, notes=()) -> dict[str, list[tuple]]:
    """``{voice: [(kind, params, first sample, last sample)]}`` for the ops that
    shape a voice's sound rather than its notes, in the order they were added.
    ``notes`` are the rendered notes, which a `duck` needs to know when its
    source plays; the piece's stops are added to every voice they silence."""
    from .render import AUDIO_ONLY
    out: dict[str, list[tuple]] = {}
    for v in piece.voices:
        for op in v.ops:
            if op.kind not in AUDIO_ONLY or not op.enabled:
                continue
            lo = piece.tick_of(op.params["from"]) if op.params.get("from") else 0
            hi = (piece.tick_of(op.params["until"]) if op.params.get("until")
                  else piece.total_ticks)
            params = op.params
            if op.kind == "duck":
                from .ensemble import KIT_DRUMS
                piece.get_voice(params["source"])            # a typo fails here
                drum = params.get("drum")
                if drum is not None and drum not in KIT_DRUMS:
                    raise ValueError(f"duck drum {drum!r} is not a drum; a kit has "
                                     f"{sorted(KIT_DRUMS)}")
                source = piece.get_voice(params["source"])
                played = notes
                if source.muted:
                    # A muted key still keys: a pad soloed (as `ms hear` does)
                    # must pump the way it does in the mix.
                    import copy
                    alone = copy.deepcopy(piece)
                    for other in alone.voices:
                        other.muted = other.name != source.name
                    played = render(alone).notes
                hits = sorted({int(to_sec(n.start) * SR) for n in played
                               if n.voice == params["source"] and lo <= n.start < hi
                               and (drum is None or n.pitch == KIT_DRUMS[drum])})
                params = {**params, "_hits": hits}
            if op.kind == "echo":
                # A note value, so the repeats sit on the grid; measured at
                # the tempo where the echo starts.
                from .theory import ticks
                span = ticks(str(params.get("time") or "1/8."))
                params = {**params, "_delay": to_sec(lo + span) - to_sec(lo)}
            out.setdefault(v.name, []).append(
                (op.kind, params, int(to_sec(lo) * SR), int(to_sec(max(hi, lo)) * SR)))
    for lo, hi, keep in stops(piece, to_sec):
        for v in piece.voices:
            if v.name not in keep:
                out.setdefault(v.name, []).append(("cut", {}, lo, hi))
    return out


def _sweep_filter(x, lo: int, hi: int, start: float, end: float, mode: str,
                  resonance: float):
    """A filter whose cutoff moves from ``start`` to ``end`` Hz across a span.

    Done frame by frame in the frequency domain (overlap-add), because a
    cutoff that moves cannot be one convolution. The slope is about 24 dB per
    octave; resonance adds a peak at the cutoff, which is what makes a sweep
    audible as a sweep rather than as the sound getting duller.
    """
    np = _np
    hi = min(hi, len(x))
    if hi - lo < 2048:
        return x
    size, hop = 2048, 512
    seg = x[lo:hi]
    count = 1 + (len(seg) - size) // hop
    window = np.sqrt(np.hanning(size + 1)[:size])
    f = np.fft.rfftfreq(size, 1.0 / SR)
    out = np.zeros(len(seg))
    norm = np.zeros(len(seg))
    start, end = max(20.0, float(start)), max(20.0, float(end))
    for k in range(count):
        t = k / max(1, count - 1)
        cut = start * (end / start) ** t                 # exponential: even in pitch
        ratio = (f / cut) if mode == "lowpass" else (cut / np.maximum(f, 1.0))
        gain = 1.0 / np.sqrt(1.0 + ratio ** 8)
        if resonance:
            gain = gain * (1.0 + 3.0 * resonance
                           * np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / cut) / 0.12) ** 2))
        a = k * hop
        frame = np.fft.irfft(np.fft.rfft(seg[a:a + size] * window) * gain, size)
        out[a:a + size] += frame * window
        norm[a:a + size] += window ** 2
    covered = norm > 1e-3
    seg = np.where(covered, out / np.maximum(norm, 1e-3), seg)
    y = x.copy()
    y[lo:hi] = seg
    return y


def _bell(x, lo: int, hi: int, freq: float, db: float, width: float):
    """A bell-shaped boost or cut, ``width`` octaves across at half its depth,
    over samples ``lo..hi``. Done on the spectrum, so it has no phase of its
    own and a cut at 3 kHz leaves 300 Hz exactly as it was; the span is faded
    in and out over 20 ms so it does not click."""
    np = _np
    lo, hi = max(0, lo), min(len(x), hi)
    if hi - lo < 16:
        return x
    seg = x[lo:hi]
    spec = np.fft.rfft(seg)
    f = np.fft.rfftfreq(len(seg), 1.0 / SR)
    octaves = np.log2(np.maximum(f, 1e-6) / freq)
    curve = 10 ** (db / 20.0 * np.exp(-0.5 * (octaves / (width / 2.355)) ** 2))
    wet = np.fft.irfft(spec * curve, len(seg))
    k = min(int(0.02 * SR), (hi - lo) // 2)
    mix = np.ones(len(seg))
    if lo > 0:
        mix[:k] = np.linspace(0.0, 1.0, k)
    if hi < len(x):
        mix[-k:] = np.linspace(1.0, 0.0, k)
    out = x.copy()
    out[lo:hi] = seg + (wet - seg) * mix
    return out


def _echo(left, right, lo: int, hi: int, delay: float, feedback: float, mix: float,
          tone: float, spread: float):
    """A feedback delay over samples ``lo..hi`` of a bus.

    Each repeat is the one before it, quieter and duller, the way a tape or a
    bucket-brigade echo loses its top on every pass; with ``spread`` the
    repeats take alternate sides. Only sound that starts inside the span is
    repeated, and the repeats ring on past its end. It is laid down repeat by
    repeat instead of run as a recursive filter, so the same input always gives
    the same output whatever came before the span.
    """
    np = _np
    n = len(left)
    lo, hi = max(0, lo), min(n, hi)
    step = int(round(delay * SR))
    if hi - lo < 16 or step < 1 or mix <= 0:
        return left, right
    feedback = max(0.0, min(0.92, feedback))
    k = min(int(0.005 * SR), (hi - lo) // 2)
    gate = np.ones(hi - lo)
    gate[:k] = np.linspace(0.0, 1.0, k)
    gate[-k:] = np.linspace(1.0, 0.0, k)
    tap = (0.5 * (left[lo:hi] + right[lo:hi]) * gate if spread
           else None)
    taps = [tap] if spread else [left[lo:hi] * gate, right[lo:hi] * gate]
    # One-pole lowpass as a short kernel: applied once per repeat, so the
    # fifth echo has been through it five times.
    a = math.exp(-2.0 * math.pi * max(200.0, min(tone, SR / 2.2)) / SR)
    kernel = (1.0 - a) * a ** np.arange(64)
    kernel /= kernel.sum()
    out_l, out_r = left.copy(), right.copy()
    level, at, count = mix, lo + step, 0
    while level > 1e-3 and at < n and count < 48:
        taps = [np.convolve(t, kernel)[:len(t)] for t in taps]
        end = min(n, at + (hi - lo))
        if spread:
            side = 1.0 if count % 2 == 0 else -1.0     # first repeat to the left
            gl = math.sqrt(0.5 * (1.0 + side * spread))
            gr = math.sqrt(0.5 * (1.0 - side * spread))
            out_l[at:end] += taps[0][:end - at] * level * gl * math.sqrt(2.0)
            out_r[at:end] += taps[0][:end - at] * level * gr * math.sqrt(2.0)
        else:
            out_l[at:end] += taps[0][:end - at] * level
            out_r[at:end] += taps[1][:end - at] * level
        level *= feedback
        at += step
        count += 1
    return out_l, out_r


def _apply_fx(left, right, chain):
    """Run a voice's processing chain over its own bus."""
    np = _np
    for kind, params, lo, hi in chain:
        if kind == "filter":
            start = float(params["start"])
            end = float(params["end"]) if params.get("end") is not None else start
            mode = params.get("mode") or "lowpass"
            if mode not in ("lowpass", "highpass"):
                raise ValueError(f"filter mode must be lowpass or highpass, got {mode!r}")
            res = max(0.0, min(1.0, float(params.get("resonance") or 0.0)))
            left = _sweep_filter(left, lo, hi, start, end, mode, res)
            right = _sweep_filter(right, lo, hi, start, end, mode, res)
        elif kind == "cut":
            keep = np.ones(len(left))
            _fade_out(keep, lo, hi)
            left, right = left * keep, right * keep
        elif kind == "duck":
            depth = max(0.0, min(40.0, float(params.get("depth") or 8.0)))
            release = max(0.01, float(params.get("release") or 0.18))
            floor = 10 ** (-depth / 20.0)
            # Down in 5 ms at each hit, back up along an exponential: the
            # shape a compressor keyed from the kick draws.
            n = int(release * 5 * SR)
            swell = 1.0 - (1.0 - floor) * np.exp(-np.arange(n) / (release * SR))
            attack = int(0.005 * SR)
            curve = np.ones(len(left))
            for hit in params.get("_hits") or ():
                a = max(0, hit - attack)
                if a >= len(curve):
                    continue
                curve[a:hit] = np.minimum(curve[a:hit],
                                          np.linspace(curve[a], floor, hit - a))
                b = min(len(curve), hit + n)
                curve[hit:b] = np.minimum(curve[hit:b], swell[:b - hit])
            left, right = left * curve, right * curve
        elif kind == "eq":
            freq = float(params["freq"])
            db = max(-24.0, min(24.0, float(params["gain"])))
            width = max(0.1, float(params.get("width") or 1.0))
            if not 20.0 <= freq <= SR / 2:
                raise ValueError(f"eq freq must be between 20 Hz and {SR // 2}, got {freq}")
            if db:
                left = _bell(left, lo, hi, freq, db, width)
                right = _bell(right, lo, hi, freq, db, width)
        elif kind == "drive":
            amount = max(0.0, min(4.0, float(params.get("amount") or 0.0)))
            mode = params.get("mode") or "soft"
            if mode not in ("soft", "clip", "fold"):
                raise ValueError(f"drive mode must be soft, clip or fold, got {mode!r}")
            peak = float(max(np.abs(left).max(initial=0.0), np.abs(right).max(initial=0.0)))
            if amount and peak > 0:
                g = 1.0 + amount * 9.0

                def shape(x):
                    # Level-matched at the peak, so drive adds harmonics and
                    # density rather than simply turning the voice up.
                    if mode == "soft":
                        return peak * np.tanh(g * x / peak) / math.tanh(g)
                    if mode == "clip":                 # flat tops: square and brutal
                        return peak * np.clip(g * x / peak, -1.0, 1.0)
                    # fold: what goes over the top comes back down, again and
                    # again -- the harshest of the three, and nearly noise.
                    y = g * x / peak
                    return peak * (np.abs((y - 1.0) % 4.0 - 2.0) - 1.0)

                left, right = shape(left), shape(right)
        elif kind == "compress":
            ratio = max(1.0, float(params.get("ratio") or 4.0))
            thr_db = float(params.get("threshold") if params.get("threshold") is not None
                           else -18.0)
            peak = float(max(np.abs(left).max(initial=0.0), np.abs(right).max(initial=0.0)))
            if ratio > 1.0 and peak > 0:
                # Level follower: a fast attack and a slower release, done on
                # short blocks so it costs nothing, then interpolated.
                block = 64
                n = len(left)
                mag = np.maximum(np.abs(left), np.abs(right))
                env = np.pad(mag, (0, (-n) % block)).reshape(-1, block).max(axis=1)
                rel = math.exp(-block / (0.08 * SR))
                for i in range(1, len(env)):
                    env[i] = max(env[i], env[i - 1] * rel)
                thr = peak * 10 ** (thr_db / 20.0)
                over = np.maximum(env / thr, 1.0)
                gain = over ** (1.0 / ratio - 1.0)
                gain = np.interp(np.arange(n), np.arange(len(env)) * block + block / 2, gain)
                # Make-up to the same power as before: compression is then a
                # change of density and not of level, so it can be added to a
                # voice without remixing the piece. `makeup` dB goes on top.
                before = float(np.mean(left ** 2 + right ** 2))
                left, right = left * gain, right * gain
                after = float(np.mean(left ** 2 + right ** 2)) or 1.0
                level = math.sqrt(before / after) * 10 ** (
                    float(params.get("makeup") or 0.0) / 20.0)
                left, right = left * level, right * level
        elif kind == "gain":
            level = 10 ** (float(params["db"]) / 20.0)
            left, right = left * level, right * level
        elif kind == "echo":
            left, right = _echo(left, right, lo, hi, float(params.get("_delay") or 0.0),
                                float(params.get("feedback") if params.get("feedback")
                                      is not None else 0.4),
                                float(params.get("mix") if params.get("mix") is not None
                                      else 0.35),
                                float(params.get("tone") or 3000.0),
                                max(0.0, min(1.0, float(
                                    params.get("spread") if params.get("spread")
                                    is not None else 0.6))))
        elif kind == "crush":
            step = max(1, int(round(SR / max(500.0, float(params.get("rate") or SR)))))
            levels = 2.0 ** (max(2, int(params.get("bits") or 16)) - 1)
            peak = float(max(np.abs(left).max(initial=0.0), np.abs(right).max(initial=0.0))) or 1.0
            for buf in (left, right):
                held = np.repeat(buf[::step], step)[:len(buf)]
                buf[:len(held)] = np.round(held / peak * levels) / levels * peak
    return left, right


def _synth_numpy(notes, voices, pans, to_sec, total, gain, models=False, width=1.0,
                 fx=None, sampled=None):
    """The fast path. Returns ``(left, right, (send_left, send_right))``; the
    sends are what goes to the room, which is less than everything for the
    instruments whose low end would turn a reverb tail to mud."""
    np = _np
    left = np.zeros(total)
    right = np.zeros(total)
    send_l = np.zeros(total)
    send_r = np.zeros(total)
    rng = np.random.default_rng(1729)
    links = {}
    if models:
        from . import synth
        links = synth.slur_links(notes, to_sec)

    # A voice with processing on it is rendered to its own bus first, so the
    # filter hears that voice alone; everyone else goes straight to the mix.
    fx = fx or {}
    sampled = sampled or {}
    buses = {name: [np.zeros(total), np.zeros(total), 1.0] for name in fx}
    # A voice played from the SoundFont arrives already rendered; it takes its
    # place on a bus like any other and goes through the same processing.
    for name, (s_left, s_right) in sampled.items():
        send = 1.0
        if models:
            send = synth.send_of(voices[name].instrument)
        buses[name] = [s_left * (gain / 0.72), s_right * (gain / 0.72), send]
        fx.setdefault(name, [])

    def place(sig, start, pan, send, voice=None):
        length = min(len(sig), total - start)
        if length <= 0:
            return
        gl, gr = _gains(max(-1.0, min(1.0, pan)))
        if voice in buses:
            bus = buses[voice]
            bus[0][start:start + length] += sig[:length] * gl
            bus[1][start:start + length] += sig[:length] * gr
            bus[2] = send
            return
        left[start:start + length] += sig[:length] * gl
        right[start:start + length] += sig[:length] * gr
        send_l[start:start + length] += sig[:length] * (gl * send)
        send_r[start:start + length] += sig[:length] * (gr * send)

    for n in notes:
        if n.voice in sampled:
            continue
        voice = voices[n.voice]
        if models and synth.has_model(voice.instrument):
            start = int(to_sec(n.start) * SR)
            if start < 0 or start >= total:
                continue
            frm, onward = links.get(id(n), (None, False))
            ctx = synth.NoteCtx(
                voice.instrument, n.voice, n.pitch, to_sec(n.start),
                max(0.03, to_sec(n.end) - to_sec(n.start)), n.velocity, frm, onward,
                (n.voice, n.start, n.pitch), n.tune)
            seat = pans.get(n.voice, 0.0)
            # ``width`` is 0 for a mono render: a section is spread around its
            # seat only when there is a stage to spread it on.
            for sig, offset in synth.render_note(ctx, total - start):
                place(sig * (gain / 0.72), start, seat + offset * width,
                      synth.send_of(voice.instrument), n.voice)
            continue
        plan = _note_plan(n, voice, to_sec, total, gain)
        if plan is None:
            continue
        start, length, amp, freq, spec, timbre = plan
        env = _envelope_np(length, spec["adsr"])
        if spec["partials"] is None:
            sig = rng.uniform(-1.0, 1.0, length)
        else:
            t = np.arange(length) / SR
            depth = spec.get("vibrato", 0.0)
            if depth and length > SR * 0.3:
                # Vibrato fades in, as a player's does: a note that wobbles from
                # its first instant sounds like a tape fault, not expression.
                fade = np.clip((t - 0.18) / 0.35, 0.0, 1.0)
                inst_freq = freq * (1.0 + depth * fade * np.sin(2 * np.pi * 5.3 * t))
                cycles = np.cumsum(inst_freq) / SR
            else:
                cycles = freq * t
            if _harmonic(spec):
                table = np.frombuffer(_wavetable(timbre, freq), dtype=np.float64)
                pos = (cycles * TABLE) % TABLE
                i0 = pos.astype(np.int64)
                frac = pos - i0
                sig = table[i0] * (1 - frac) + table[(i0 + 1) % TABLE] * frac
            else:
                parts = _partials_under(spec, freq)
                norm = sum(a for _, a in parts) or 1.0
                sig = sum((a / norm) * np.sin(2 * np.pi * p * cycles) for p, a in parts)
        place(sig * env * amp, start, pans.get(n.voice, 0.0), 1.0, n.voice)
    for name, (bus_l, bus_r, send) in buses.items():
        bus_l, bus_r = _apply_fx(bus_l, bus_r, fx[name])
        left += bus_l
        right += bus_r
        send_l += bus_l * send
        send_r += bus_r * send
    return left, right, (send_l, send_r)


def _reverb(left, right, decay: float, wet: float, send=None):
    """Convolution with a synthetic room: a few early reflections, then
    decaying noise that darkens as it dies.

    A real hall loses its highs faster than its lows, which is most of what
    makes a reverb tail sound like a room rather than like hiss. Separate noise
    for each ear decorrelates the channels and gives the tail width. The early
    reflections are what place the players at a distance; a tail on its own
    sounds like a dry instrument with a wash behind it. ``send`` is what is fed
    to the room when that is not simply the dry signal.
    """
    np = _np
    n = int(decay * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(4242)
    env = np.exp(-6.91 * t / decay)            # -60 dB at `decay`
    bright = np.clip(1.0 - t / (decay * 0.5), 0.0, 1.0)
    pre = int(0.012 * SR)                       # early-reflection gap

    def ir():
        raw = rng.standard_normal(n)
        k = 24
        dark = np.convolve(raw, np.ones(k) / k, mode="same") * math.sqrt(k)
        out = (bright * raw + (1 - bright) * dark) * env
        out[:pre] = 0.0
        # The diffuse tail builds up rather than starting at full strength.
        build = int(0.06 * SR)
        out[pre:build] *= np.linspace(0.25, 1.0, build - pre)
        out = out / (np.sqrt((out ** 2).sum()) or 1.0)
        for ms in (13, 19, 27, 34, 43, 58, 71):
            at = int(ms * rng.uniform(0.9, 1.1) * SR / 1000)
            if at < n:
                out[at] += rng.choice((-1.0, 1.0)) * 0.34 * math.exp(-ms / 45.0)
        return out

    size = 1 << int(math.ceil(math.log2(len(left) + n)))
    feeds = send if send is not None else (left, right)
    outs = []
    for dry, feed, h in ((left, feeds[0], ir()), (right, feeds[1], ir())):
        wet_sig = np.fft.irfft(np.fft.rfft(feed, size) * np.fft.rfft(h, size), size)
        outs.append(dry * (1 - wet) + wet_sig[:len(dry)] * wet * 1.3)
    return outs[0], outs[1]


#: How many dB over the ceiling a mix may be pushed into the limiter, by style.
#: Orchestral music keeps its peaks; a breakbeat track is meant to be a slab.
MASTER_PUSH = {"electronic": 9.0}


def _master(left, right, ceiling: float = 0.95, push: float = 3.5, clip: float = 0.0):
    """Hold the loudest moments under the ceiling without turning the rest down.

    Scaling a whole piece by its single highest peak lets one drum stroke make
    four minutes of music quiet. So a mix that overshoots is first brought to
    within a few dB of the ceiling, and a limiter with a few milliseconds of
    lookahead takes the remainder off just the peaks. A mix that never reaches
    the ceiling is returned untouched: a quiet cue stays quiet.
    """
    np = _np
    peak = float(max(np.abs(left).max(initial=0.0), np.abs(right).max(initial=0.0)))
    if clip > 0 and peak > 0:
        # Deliberate destruction: the mix is driven `clip` dB past full scale
        # and the tops are cut off flat. No limiter is involved, on purpose.
        scale = ceiling / peak * 10 ** (clip / 20.0)
        return (np.clip(left * scale, -ceiling, ceiling),
                np.clip(right * scale, -ceiling, ceiling))
    if peak <= ceiling:
        return left, right
    scale = min(1.0, ceiling / peak * 10 ** (push / 20.0))   # the rest is the limiter's
    left, right = left * scale, right * scale
    block = 128
    n = len(left)
    pad = (-n) % block
    mag = np.maximum(np.abs(left), np.abs(right))
    blocks = np.pad(mag, (0, pad)).reshape(-1, block).max(axis=1)
    # Lookahead and hold: each block also answers for its neighbours' peaks.
    wide = blocks.copy()
    for shift in range(1, 5):
        wide[:-shift] = np.maximum(wide[:-shift], blocks[shift:])
        wide[shift:] = np.maximum(wide[shift:], blocks[:-shift])
    g = np.minimum(1.0, ceiling / np.maximum(wide, 1e-9))
    # Release slowly so the gain does not pump with every note.
    rel = 0.9
    for i in range(1, len(g)):
        g[i] = min(g[i], g[i - 1] + (1.0 - g[i - 1]) * (1 - rel))
    gain = np.interp(np.arange(n), np.arange(len(g)) * block + block / 2, g)
    return left * gain, right * gain


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def save_wav(piece: Piece, path: str | Path, rend: Render | None = None, *,
             stereo: bool = True, reverb: bool | None = None,
             models: bool | None = None, strict: bool = False,
             engines: dict | None = None) -> Path:
    """Normalize and write 16-bit PCM. Normalization is peak-based, not RMS, so
    a quiet cue stays quiet relative to its own loud moments."""
    left, right = synthesize(piece, rend, stereo=stereo, reverb=reverb, models=models,
                             strict=strict, engines=engines)
    channels = 2 if stereo else 1
    if _np is not None:
        how = piece.meta.get("master") or {}
        l_arr, r_arr = _master(_np.asarray(left), _np.asarray(right),
                               push=float(how.get("push", MASTER_PUSH.get(piece.style, 3.5))),
                               clip=float(how.get("clip", 0.0)))
        if how.get("level"):
            # The output fader, after everything: a mix can be crushed for its
            # sound and still be handed over at a civil volume.
            trim = 10 ** (min(0.0, float(how["level"])) / 20.0)
            l_arr, r_arr = l_arr * trim, r_arr * trim
        peak = float(max(_np.abs(l_arr).max(initial=0.0), _np.abs(r_arr).max(initial=0.0)))
        scale = 32767.0 * (0.95 / peak if peak > 0.95 else 1.0)
        frames = (_np.stack([l_arr, r_arr], 1) if stereo else l_arr[:, None])
        pcm = _np.clip(frames * scale, -32768, 32767).astype("<i2").tobytes()
    else:
        peak = max(max((abs(v) for v in left), default=0.0),
                   max((abs(v) for v in right), default=0.0)) or 1.0
        scale = 32767.0 * (0.95 / peak if peak > 0.95 else 1.0)
        out = array("h", [0]) * (len(left) * channels)
        for i in range(len(left)):
            if stereo:
                out[2 * i] = max(-32768, min(32767, int(left[i] * scale)))
                out[2 * i + 1] = max(-32768, min(32767, int(right[i] * scale)))
            else:
                out[i] = max(-32768, min(32767, int(left[i] * scale)))
        pcm = out.tobytes()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    return p


# --------------------------------------------------------------------------
# sampled render
# --------------------------------------------------------------------------

#: Where a General MIDI SoundFont usually lives, in the order tried.
SOUNDFONT_DIRS = ("~/.local/share/soundfonts", "~/.local/share/sounds/sf2",
                  "/usr/share/soundfonts", "/usr/share/sounds/sf2",
                  "/usr/share/sounds/sf3", "/usr/local/share/soundfonts",
                  "/Library/Audio/Sounds/Banks")
#: Samplers get louder with velocity faster than the built-in render does.
#: Raising velocities to this power before they reach the sampler narrows the
#: gap. It is the fallback: with numpy, ``listen.calibrate`` measures the right
#: exponent for each instrument of the bank in use (0.75-1.0 for the two banks
#: it has been run on), and that is used instead.
SAMPLER_VELOCITY_CURVE = 0.8
_SOUNDFONT_PREFERENCE = ("musescore_general_hq", "musescore_general_full",
                         "musescore", "fluidr3_gm", "fluid", "generaluser", "timgm",
                         "default", "freepats")


def find_soundfont(path: str | os.PathLike | None = None) -> Path:
    """Resolve a SoundFont: an explicit path, ``$MUSICSTUDIO_SOUNDFONT``, or the
    best General MIDI bank found in the usual system directories."""
    chosen = path if path and str(path) != "auto" else os.environ.get("MUSICSTUDIO_SOUNDFONT")
    if chosen:
        p = Path(chosen).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"no SoundFont at {p}")
        return p
    found: list[Path] = []
    for d in SOUNDFONT_DIRS:
        base = Path(d).expanduser()
        if base.is_dir():
            found += [f for f in sorted(base.iterdir())
                      if f.suffix.lower() in (".sf2", ".sf3")]
    if not found:
        raise FileNotFoundError(
            "no SoundFont found. `ms soundfont install` downloads one (MuseScore "
            "General HQ, MIT, 73 MB) to ~/.local/share/soundfonts. Or give your "
            "own with --soundfont PATH or MUSICSTUDIO_SOUNDFONT; any General MIDI "
            ".sf2/.sf3 works")

    def rank(f: Path) -> int:
        name = f.name.lower()
        return next((i for i, k in enumerate(_SOUNDFONT_PREFERENCE) if k in name),
                    len(_SOUNDFONT_PREFERENCE))

    return min(found, key=rank)


def soundfont_available() -> bool:
    """Whether a sampled render is possible here: FluidSynth and a bank."""
    if shutil.which("fluidsynth") is None:
        return False
    try:
        find_soundfont()
    except FileNotFoundError:
        return False
    return True


def prerendered(piece: Piece, notes, to_sec, total: int, pans, *,
                strict: bool = False, engines: dict | None = None) -> dict[str, tuple]:
    """Voices that are rendered whole rather than note by note: sampled ones
    from the SoundFont, and singers, whose syllables run into each other.

    Each voice is rendered once, by the first engine that can: its bank if it
    names one, the formant singer otherwise *or if the bank could not be run*
    (which warns, or raises under ``strict``). ``engines`` records which.
    """
    from .vocal import voice_stems
    out: dict[str, tuple] = {}
    used: dict[str, str] = {}
    if any(v.bank for v in piece.voices):
        # A bank is either a neural singer (a trained voicebank) or a recorded
        # voice; a name the neural engine knows is never tried as the other.
        from .neural import voice_stems as neural
        from .voicebank import voice_stems as banked
        bank_of = {v.name: v.bank for v in piece.voices}
        for label, stems in (("voicebank", banked), ("neural", neural)):
            got = stems(piece, notes, to_sec, total, pans, strict=strict)
            out.update(got)
            used.update({name: f"{label}:{bank_of[name]}" for name in got})
    plain = voice_stems(piece, notes, to_sec, total, pans, skip=set(out))
    out.update(plain)
    used.update({name: "formant" for name in plain})
    sampled = sampled_stems(piece, notes, to_sec, total, strict=strict)
    out.update(sampled)
    used.update({name: "soundfont" for name in sampled})
    if engines is not None:
        engines.update(used)
    return out


def sampled_stems(piece: Piece, notes, to_sec, total: int, *,
                  strict: bool = False, bare: bool = False) -> dict[str, tuple]:
    """Render the voices marked ``engine='soundfont'`` from the SoundFont.

    Returns ``{voice: (left, right)}`` at the built-in render's level, ready for
    that voice's bus. Notes are grouped by their ``tune``: each group is
    rendered *slowed down* by its pitch ratio and then played back faster, so a
    kit tuned up five semitones is shorter and higher exactly as a sped-up
    break is, and a roll that climbs is a set of such renders.

    Which SoundFont: the voice's ``bank`` if it names one in
    ``soundfonts.BANKS``, else the instrument's own ``font``, else the General
    MIDI bank -- so one piece can draw on several. ``bare`` leaves out the
    level matching (it is what the level matching itself measures with).

    Without FluidSynth or a bank this returns nothing and the voices fall back
    to their instrument models, so a piece still renders everywhere.
    """
    np = _np
    wanted = [v for v in piece.voices if v.engine == "soundfont" and not v.muted]
    if not wanted or np is None:
        return {}
    import warnings
    if shutil.which("fluidsynth") is None:
        if strict:
            raise RuntimeError("voices with engine='soundfont' cannot be sampled: "
                               "FluidSynth is missing")
        warnings.warn("voices with engine='soundfont' are being played by the "
                      "instrument models: FluidSynth is missing", stacklevel=2)
        return {}
    from . import soundfonts
    from .listen import calibrate
    from .midi import _chunk, _track
    import struct
    general = find_soundfont() if soundfont_available() else None
    # Which file each voice is played from, and which preset in it. A voice's
    # own `bank` names a catalogued SoundFont and wins; otherwise the
    # instrument's `font`; otherwise the General MIDI bank. A bank that is not
    # installed falls back one step, and says so.
    plan: dict[str, tuple[Path, str | None, int, int]] = {}
    keymaps: dict[str, dict[int, int]] = {}
    for v in wanted:
        asked = None if v.inst.family == "voice" else v.bank   # a singer's is a voice
        font = asked or v.inst.font
        path = soundfonts.path_of(font) if font else None
        if font and path is None:
            what = (f"voice {v.name!r} ({v.instrument}) asks for the SoundFont "
                    f"{font!r}, which is not installed (`ms soundfont install {font}`)")
            if strict:
                raise RuntimeError(what)
            warnings.warn(what + "; " + ("the General MIDI bank plays it instead"
                                         if general else "its model plays it instead"),
                          stacklevel=2)
        if path is not None:
            own = font == v.inst.font and v.inst.preset is not None
            bank_no, program = v.inst.preset if own else (
                128 if v.inst.percussive else 0, v.inst.program)
            plan[v.name] = (path, font, bank_no, program)
            if own and v.inst.keymap:
                keymaps[v.name] = dict(v.inst.keymap)
        elif general is not None:
            plan[v.name] = (general, None, 128 if v.inst.percussive else 0,
                            v.inst.program)
    if not plan:
        if strict:
            raise RuntimeError("voices with engine='soundfont' cannot be sampled: "
                               "no SoundFont is installed")
        warnings.warn("voices with engine='soundfont' are being played by the "
                      "instrument models: no SoundFont is installed "
                      "(`ms soundfont install`)", stacklevel=2)
        return {}
    wanted = [v for v in wanted if v.name in plan]
    pans = pan_positions(piece)
    out: dict[str, tuple] = {}
    rate = 960                      # ticks per second: 480 per quarter at 120 bpm
    with tempfile.TemporaryDirectory() as tmp:
        for v in wanted:
            mine = [n for n in notes if n.voice == v.name]
            if not mine:
                continue
            bank, font, bank_no, program = plan[v.name]
            keymap = keymaps.get(v.name, {})
            if bare:
                level, curve = 1.0, 1.0
            else:
                # An instrument in its own bank is measured against its own
                # model; anything else played from a bank (the General MIDI
                # one, or another whole set a voice asked for) uses that
                # bank's balance as a set.
                own = font is not None and v.inst.font == font
                cal = calibrate(bank, font=font if own else None)
                key = v.instrument if own or not v.inst.percussive else "kit"
                level = 10 ** ((cal.get("offset", 0.0) + cal["trim"].get(key, 0.0)) / 20.0)
                curve = cal["curve"].get(key, SAMPLER_VELOCITY_CURVE)
            groups: dict[float, list] = {}
            for n in mine:
                groups.setdefault(round(n.tune * 2) / 2, []).append(n)
            # One FluidSynth run for the whole voice: every pitch group is laid
            # end to end in a single file, each slowed by its own ratio, and
            # cut apart again afterwards. Loading the bank is the slow part.
            # Bank 128 is the drum channel's. A kit that a bank keeps as an
            # ordinary preset (bank 0) is played on an ordinary channel.
            ch = 9 if bank_no == 128 else 0
            events: list[tuple[int, bytes]] = []
            if ch != 9:
                events.append((0, bytes([0xB0 | ch, 0, bank_no & 0x7F])))
            events.append((0, bytes([0xC0 | ch, program & 0x7F])))
            layout = []
            cursor = 0.0
            for tune, group in sorted(groups.items()):
                ratio = 2.0 ** (tune / 12.0)
                first = min(to_sec(n.start) for n in group)
                last = max(to_sec(n.end) for n in group)
                length = (last - first + 2.5) * ratio
                # One note-off per pitch: a note struck again while it still
                # rings ends where the next one starts, or its own later
                # note-off would land inside the new note and silence it
                # (the rule `midi._sounding_ends` applies to the MIDI export).
                spans: list[list[int]] = []
                ringing: dict[int, list[int]] = {}
                for n in sorted(group, key=lambda n: n.start):
                    on = int((cursor + (to_sec(n.start) - first) * ratio) * rate)
                    off = max(on + 1, int((cursor + (to_sec(n.end) - first) * ratio) * rate))
                    pitch = max(0, min(127, keymap.get(n.pitch, n.pitch)))
                    before = ringing.get(pitch)
                    if before is not None and before[1] > on:
                        before[1] = max(before[0] + 1, on)
                    vel = max(1, min(127, round(127 * (max(1, n.velocity) / 127) ** curve)))
                    span = [on, off, pitch, vel]
                    spans.append(span)
                    ringing[pitch] = span
                # Offs first, so an off and an on at one tick end the old note
                # rather than the new one.
                events += [(off, bytes([0x80 | ch, pitch, 0])) for _, off, pitch, _ in spans]
                events += [(on, bytes([0x90 | ch, pitch, vel])) for on, _, pitch, vel in spans]
                layout.append((ratio, first, cursor, length))
                cursor += length
            meta = _track([(0, b"\xff\x51\x03" + struct.pack(">I", 500000)[1:])])
            mid = Path(tmp) / "stem.mid"
            mid.write_bytes(_chunk(b"MThd", struct.pack(">HHH", 1, 2, 480))
                            + meta + _track(events))
            wav = Path(tmp) / "stem.wav"
            _fluidsynth(mid, wav, bank, gain=0.4, room=None)
            with wave.open(str(wav), "rb") as w:
                raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
                data = raw.reshape(-1, w.getnchannels()).astype(np.float64) / 32768.0
            if data.shape[1] == 1:
                data = np.repeat(data, 2, axis=1)
            left, right = np.zeros(total), np.zeros(total)
            gl, gr = (1.0, 1.0) if v.inst.percussive else \
                tuple(g * math.sqrt(2) for g in _gains(pans.get(v.name, 0.0)))
            for ratio, first, at, length in layout:
                seg = data[int(at * SR):int((at + length) * SR)]
                start = int(first * SR)
                for x, buf, g in ((seg[:, 0], left, gl), (seg[:, 1], right, gr)):
                    if ratio != 1.0 and len(x) > 1:
                        x = np.interp(np.arange(0.0, len(x) - 1, ratio), np.arange(len(x)), x)
                    k = min(total - start, len(x))
                    if k > 0:
                        buf[start:start + k] += x[:k] * (level * g)
            out[v.name] = (left, right)
    return out


def _fluidsynth(mid: Path, out: Path, bank: Path, *, gain: float,
                room: tuple[float, float] | None) -> None:
    """One FluidSynth run: a MIDI file in, a WAV out. ``room`` is ``(size,
    wet)`` or ``None`` for the sampler's bare output."""
    exe = shutil.which("fluidsynth")
    if exe is None:
        raise RuntimeError("a SoundFont render needs FluidSynth on PATH "
                           "(https://www.fluidsynth.org); the built-in render "
                           "needs nothing -- leave --soundfont off to use it")
    size, wet = room if room is not None else (1.0, 0.0)
    cmd = [exe, "-ni", "-q", "-g", f"{gain:g}", "-r", str(SR), "-O", "s16",
           "-T", "wav", "-F", str(out),
           "-o", f"synth.reverb.active={1 if room is not None else 0}",
           "-o", f"synth.reverb.room-size={min(1.0, 0.3 + size / 8):.2f}",
           "-o", f"synth.reverb.level={min(1.0, wet * 1.4):.2f}",
           "-o", "synth.reverb.damp=0.35", "-o", "synth.reverb.width=0.9",
           "-o", "synth.chorus.active=0", "-o", "synth.polyphony=512",
           str(bank), str(mid)]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0 or not out.is_file():
        raise RuntimeError(f"fluidsynth failed ({done.returncode}): "
                           f"{(done.stderr or done.stdout).strip()[:400]}")


def save_wav_soundfont(piece: Piece, path: str | Path, soundfont: str | Path | None = None,
                       rend: Render | None = None, *, gain: float = 0.4,
                       room: bool = True, normalize: bool = True,
                       balance: bool = True,
                       velocity_curve: float | None = None) -> Path:
    """Render through FluidSynth with sampled instruments.

    The MIDI export is the single source of truth here -- the same notes, the
    same tempo map and the same seating the synthesized render uses -- so the
    two renders are one performance heard through two sets of instruments.
    ``room=False`` and ``normalize=False`` give the sampler's bare output, which
    is what a measurement wants and a listener does not.

    ``balance`` matches the bank to the built-in models, instrument by
    instrument: how loud each one is, and how much louder it gets when played
    harder (see ``listen.calibrate``). Every bank records its violin, horn and
    strings at its own levels, and a piece balanced against one set comes out
    with the tune buried in another. Needs numpy; without it a single fixed
    velocity curve is used for everything.
    """
    from .midi import save_midi
    sf = find_soundfont(soundfont)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    trims = None
    curve: float | dict = (SAMPLER_VELOCITY_CURVE if velocity_curve is None
                           else velocity_curve)
    if balance and has_fast_path():
        from .listen import calibrate
        cal = calibrate(sf)
        # Every drum shares the one drum channel, so they share the kit's figures.
        key = {v.name: "kit" if v.inst.percussive else v.instrument for v in piece.voices}
        trims = {name: cal["trim"].get(k, 0.0) for name, k in key.items()}
        curve = {name: cal["curve"].get(k, SAMPLER_VELOCITY_CURVE)
                 for name, k in key.items()}
    with tempfile.TemporaryDirectory() as tmp:
        mid = save_midi(piece, Path(tmp) / "piece.mid", rend,
                        velocity_curve=curve, trims=trims)
        _fluidsynth(mid, out, sf, gain=gain,
                    room=ROOMS.get(piece.style, ROOMS["freeform"]) if room else None)
    if normalize:
        _normalize_wav(out)
    return out


def _normalize_wav(path: Path, ceiling: float = 0.95) -> None:
    """Bring a rendered file's peak up to the ceiling.

    A sampler's output level depends on the bank, and a quiet piece through a
    quiet bank comes out 20 dB down. Only ever turns a file up: one that
    already reaches the ceiling was mixed that way on purpose.
    """
    with wave.open(str(path), "rb") as w:
        params = w.getparams()
        raw = w.readframes(w.getnframes())
    if params.sampwidth != 2 or not raw:
        return
    samples = array("h")
    samples.frombytes(raw)
    peak = max(max(samples), -min(samples)) / 32768.0
    if peak <= 0 or peak >= ceiling * 0.98:
        return
    scale = ceiling / peak
    if _np is not None:
        pcm = _np.clip(_np.frombuffer(raw, dtype="<i2") * scale, -32768, 32767) \
            .astype("<i2").tobytes()
    else:
        pcm = array("h", (max(-32768, min(32767, int(v * scale))) for v in samples)).tobytes()
    with wave.open(str(path), "wb") as w:
        w.setparams(params)
        w.writeframes(pcm)
