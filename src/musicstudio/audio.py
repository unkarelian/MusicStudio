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
numpy is used for speed, vibrato and the reverb; without it the render is dry
but otherwise the same piece.
"""

from __future__ import annotations

import math
import random
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
    """Ticks -> seconds through the tempo map, as a lookup over section bounds."""
    marks = []
    elapsed = 0.0
    for sec, _, tick in piece.section_bounds():
        spb = 60.0 / max(1, piece.tempo_of(sec)) / TPQ
        marks.append((tick, elapsed, spb))
        elapsed += sec.length * spb

    def convert(t: int) -> float:
        best = marks[0] if marks else (0, 0.0, 60.0 / max(1, piece.tempo) / TPQ)
        for m in marks:
            if t >= m[0]:
                best = m
        return best[1] + (t - best[0]) * best[2]

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
               reverb: bool | None = None):
    """Render to sample buffers: ``(left, right)``, or ``(mono, mono)``.

    ``reverb=None`` means "if numpy is available". Returns numpy arrays on the
    fast path and ``array('d')`` buffers otherwise; :func:`save_wav` takes either.
    """
    r = rend if rend is not None else render(piece)
    to_sec = _tick_seconds(piece)
    room = ROOMS.get(piece.style, ROOMS["freeform"])
    use_reverb = (has_fast_path() if reverb is None else reverb) and room[1] > 0
    if use_reverb and not has_fast_path():
        raise RuntimeError("reverb needs numpy; `uv sync --extra analysis`, or "
                           "pass reverb=False")
    tail = max(tail, room[0] * 0.8 if use_reverb else 0.0)
    end = max((n.end for n in r.notes), default=piece.total_ticks)
    total = int((to_sec(end) + tail) * SR) + 1
    pans = pan_positions(piece) if stereo else {v.name: 0.0 for v in piece.voices}
    voices = {v.name: v for v in piece.voices}
    synth = _synth_numpy if has_fast_path() else _synth_python
    left, right = synth(r.notes, voices, pans, to_sec, total, gain)
    if use_reverb:
        left, right = _reverb(left, right, *room)
    return left, right


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
    freq = 440.0 * 2 ** ((n.pitch - 69) / 12.0)
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


def _synth_numpy(notes, voices, pans, to_sec, total, gain):
    np = _np
    left = np.zeros(total)
    right = np.zeros(total)
    rng = np.random.default_rng(1729)
    for n in notes:
        plan = _note_plan(n, voices[n.voice], to_sec, total, gain)
        if plan is None:
            continue
        start, length, amp, freq, spec, timbre = plan
        gl, gr = _gains(pans.get(n.voice, 0.0))
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
        sig = sig * env * amp
        left[start:start + length] += sig * gl
        right[start:start + length] += sig * gr
    return left, right


def _reverb(left, right, decay: float, wet: float):
    """Convolution with a synthetic room: decaying noise that darkens as it dies.

    A real hall loses its highs faster than its lows, which is most of what
    makes a reverb tail sound like a room rather than like hiss. Separate noise
    for each ear decorrelates the channels and gives the tail width.
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
        return out / (np.sqrt((out ** 2).sum()) or 1.0)

    size = 1 << int(math.ceil(math.log2(len(left) + n)))
    outs = []
    for dry, h in ((left, ir()), (right, ir())):
        wet_sig = np.fft.irfft(np.fft.rfft(dry, size) * np.fft.rfft(h, size), size)
        outs.append(dry * (1 - wet) + wet_sig[:len(dry)] * wet * 1.3)
    return outs[0], outs[1]


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def save_wav(piece: Piece, path: str | Path, rend: Render | None = None, *,
             stereo: bool = True, reverb: bool | None = None) -> Path:
    """Normalize and write 16-bit PCM. Normalization is peak-based, not RMS, so
    a quiet cue stays quiet relative to its own loud moments."""
    left, right = synthesize(piece, rend, stereo=stereo, reverb=reverb)
    channels = 2 if stereo else 1
    if _np is not None:
        l_arr, r_arr = _np.asarray(left), _np.asarray(right)
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
