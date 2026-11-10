"""Hearing the render: measurements of the audio the studio actually produced.

Every other view reads the score. This one reads the *sound*: each voice is
rendered on its own, exactly as it will be in the mix, and the results are
measured. It exists because the agent writing the music cannot listen to it,
and the things a person notices in the first ten seconds -- the accompaniment
is as loud as the tune, that note never spoke, the middle section is harsh --
are all in the audio and none of them are in the note list.

What is measured, per bar:

**Loudness**, A-weighted, of the mix and of every voice. A-weighting is the
rough shape of the ear's sensitivity, so a contrabass with a great deal of
energy and little loudness is not reported as dominating.

**Who has the tune, and by how much.** The voice carrying the tune (and
anything doubling it) against everything else sounding. A tune that is not
clearly above its accompaniment is the single commonest fault of a mix.

**Brightness**, the spectral centroid, and **roughness**, Sethares' model of
sensory dissonance applied to the strongest partials actually present. A
written fifth is smooth and can still come out rough if the two instruments'
overtones collide; only the audio knows.

And per note: **whether it sounded.** The energy at each note's own pitch,
during its own time, is compared with what that voice's other notes of the
same strength produce. A note far below that did not speak -- it was cut off,
buried under its own attack, or too short for the instrument.

These are measurements, and they are labelled as such: a reading says what is
there, not whether it is good. A buried tune can be a choice. Works on either
render -- the built-in models, or a SoundFont through FluidSynth.
"""

from __future__ import annotations

import math
import tempfile
import wave
from dataclasses import dataclass, field
from pathlib import Path

from . import audio
from .doc import Piece
from .render import Note, Render, render
from .tension import EARLY, _spans, followers, tune_at

try:                                   # pragma: no cover - depends on the extras
    import numpy as np
except ImportError:                    # pragma: no cover
    np = None

SR = audio.SR
#: How far below its expected level a note must be before it "did not sound".
WEAK_DB = 10.0
#: The tune should clear everything else combined by about this much.
CLEAR_DB = 3.0


def _need_numpy() -> None:
    if np is None:
        raise RuntimeError("hearing the render needs numpy; `uv sync --extra analysis`")


# --------------------------------------------------------------------------
# stems
# --------------------------------------------------------------------------

def stems(piece: Piece, rend: Render | None = None, *, source: str = "models",
          soundfont: str | None = None) -> tuple[dict[str, "np.ndarray"], str]:
    """Every sounding voice rendered alone and dry: ``{voice: samples[n, 2]}``.

    Dry, because a room smears onsets and adds level that belongs to no note.
    Returns the stems and a label naming what they were heard through.
    """
    _need_numpy()
    r = rend if rend is not None else render(piece)
    by_voice: dict[str, list[Note]] = {}
    for n in r.notes:
        by_voice.setdefault(n.voice, []).append(n)
    to_sec = audio._tick_seconds(piece)
    end = max((n.end for n in r.notes), default=piece.total_ticks)
    total = int((to_sec(end) + 1.5) * SR) + 1
    out: dict[str, np.ndarray] = {}
    if source == "models":
        voices = {v.name: v for v in piece.voices}
        pans = audio.pan_positions(piece)
        fx = audio.voice_fx(piece, to_sec)
        sampled = audio.sampled_stems(piece, r.notes, to_sec, total)
        for name, notes in by_voice.items():
            left, right, _ = audio._synth_numpy(
                notes, voices, pans, to_sec, total, 0.72, True, 1.0,
                {k: v for k, v in fx.items() if k == name},
                {k: v for k, v in sampled.items() if k == name})
            out[name] = np.stack([left, right], 1)
        return out, "the built-in instrument models"
    if source != "soundfont":
        raise ValueError(f"source must be 'models' or 'soundfont', got {source!r}")
    bank = audio.find_soundfont(soundfont)
    with tempfile.TemporaryDirectory() as tmp:
        for name, notes in by_voice.items():
            path = audio.save_wav_soundfont(
                piece, Path(tmp) / "stem.wav", bank, Render(piece, list(notes)),
                room=False, normalize=False)
            with wave.open(str(path), "rb") as w:
                raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
                data = raw.reshape(-1, w.getnchannels()).astype(np.float64) / 32768.0
            if data.shape[1] == 1:
                data = np.repeat(data, 2, axis=1)
            fixed = np.zeros((total, 2))
            fixed[:min(total, len(data))] = data[:total]
            out[name] = fixed
    return out, f"the SoundFont {bank.name}"


# --------------------------------------------------------------------------
# matching a sampler to the models
# --------------------------------------------------------------------------

#: The most a bank's instrument is ever turned up or down to match.
MAX_TRIM_DB = 10.0
CACHE_DIR = Path("~/.cache/musicstudio")


def calibrate(bank: str | Path, *, refresh: bool = False) -> dict[str, dict[str, float]]:
    """How to make a SoundFont balance the way the built-in models do.

    Returns ``{"trim": {instrument: dB}, "curve": {instrument: exponent},
    "offset": dB}``.
    Every instrument plays the same phrase soft and then loud, through the bank
    and through the models, and the loudnesses are compared:

    * **curve** -- how much louder each gets from ``p`` to ``f``. Samplers are
      steeper than the models, and not equally: the exponent is what velocity
      must be raised to so this instrument's dynamics span what the model's do.
    * **trim** -- with that curve applied, how far its ``mf`` sits from the
      model's. The median over all instruments is removed, so trims re-balance
      the bank without changing its overall level.

    What matters is the difference *between* instruments: a bank whose horn is
    6 dB hotter than its violin will bury a tune that ``hear`` reported as
    clear. Measured once per bank and kept in ``~/.cache``.
    """
    import hashlib
    import json
    from . import synth
    from .doc import Section, Voice
    from .ensemble import INSTRUMENTS
    from .theory import DYNAMICS
    _need_numpy()
    bank = Path(bank)
    stat = bank.stat()
    tag = hashlib.sha1(f"{bank.resolve()}|{stat.st_size}|{int(stat.st_mtime)}|"
                       f"{synth.LEVEL}|v5".encode()).hexdigest()[:16]
    cache = CACHE_DIR.expanduser() / f"balance-{tag}.json"
    if cache.is_file() and not refresh:
        try:
            got = json.loads(cache.read_text())
            return {"trim": dict(got["trim"]), "curve": dict(got["curve"]),
                    "offset": float(got["offset"])}
        except (ValueError, OSError, KeyError):
            pass
    # Pitched instruments one by one; and the drum channel once, as a kit
    # playing a beat, since a bank's kit is as arbitrary in level as its horn.
    names = [n for n in synth.MODELS if not INSTRUMENTS[n].percussive] + ["kit"]
    soft, loud, mid = DYNAMICS["p"], DYNAMICS["f"], DYNAMICS["mf"]
    span = 20 * math.log10(loud / soft)
    diff: dict[str, float] = {}
    curve: dict[str, float] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(0, len(names), 12):           # one MIDI channel each
            batch = names[i:i + 12]
            p = Piece("calibrate", "C major", tempo=60, style="freeform")
            p.sections.append(Section("A", 4 * len(batch)))
            for k, name in enumerate(batch):
                drums = INSTRUMENTS[name].percussive
                p.voices.append(Voice(name, name, "percussion" if drums else "melody",
                                      pan=0.0))
                for j, dyn in enumerate(("p", "f")):
                    if drums:
                        p.add_op(name, "beat", id=f"c{k}{dyn}", at=str(1 + 4 * k + 2 * j),
                                 bars=1, dynamic=dyn, res="1/8",
                                 lanes={"kick": "x...x...", "snare": "..x...x.",
                                        "hat": "xxxxxxxx"})
                    else:
                        p.add_op(name, "phrase", id=f"c{k}{dyn}",
                                 at=str(1 + 4 * k + 2 * j), unit="1/4",
                                 steps="0 4 7 4", dynamic=dyn)
            to_sec = audio._tick_seconds(p)
            left, right = audio.synthesize(p, reverb=False, models=True)
            path = audio.save_wav_soundfont(p, Path(tmp) / "c.wav", bank, room=False,
                                            normalize=False, balance=False,
                                            velocity_curve=1.0)
            with wave.open(str(path), "rb") as w:
                raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
                sampled = raw.reshape(-1, w.getnchannels()).astype(np.float64) / 32768.0
            modelled = np.stack([left, right], 1)

            def level(buf, bar, weighted):
                lo = int(to_sec(p.tick_of(bar)) * SR)
                hi = int(to_sec(p.tick_of(bar + 2)) * SR) if bar + 2 <= p.total_bars \
                    else lo + 8 * SR
                return _loudness(buf[lo:hi], weighted)

            for k, name in enumerate(batch):
                # A bass is matched on its energy, not its A-weighted loudness:
                # the ear's curve all but ignores 50 Hz, so a modelled sub that
                # is nearly a pure sine would "match" a sampled one only by
                # turning the sample down until the low end was gone.
                inst = INSTRUMENTS[name]
                heard = inst.percussive or inst.centre >= 48
                m = [level(modelled, 1 + 4 * k + 2 * j, heard) for j in (0, 1)]
                s = [level(sampled, 1 + 4 * k + 2 * j, heard) for j in (0, 1)]
                if min(m + s) <= 1e-12:
                    continue
                m_soft, m_loud, s_soft, s_loud = (_db(x) for x in m + s)
                s_slope = (s_loud - s_soft) / span          # dB per dB of velocity
                m_slope = (m_loud - m_soft) / span
                c = max(0.35, min(1.25, m_slope / s_slope)) if s_slope > 0.2 else 1.0
                curve[name] = round(c, 2)
                # Where this instrument's mf lands in each, once the curve has
                # reshaped the velocity the sampler is sent.
                sent = 127 * (mid / 127) ** c
                s_mid = s_soft + s_slope * 20 * math.log10(sent / soft)
                m_mid = m_soft + m_slope * 20 * math.log10(mid / soft)
                diff[name] = m_mid - s_mid
    if not diff:
        return {"trim": {}, "curve": {}, "offset": 0.0}
    centre = float(np.median(list(diff.values())))
    trims = {name: round(max(-MAX_TRIM_DB, min(MAX_TRIM_DB, d - centre)), 1)
             for name, d in diff.items()}
    # `offset` is the bank's level as a whole against the models' (at the
    # sampler gain the calibration ran at), for mixing a sampled voice into the
    # built-in render; `trim` is each instrument's distance from that.
    result = {"trim": trims, "curve": curve, "offset": round(centre, 2)}
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(result, indent=1))
    except OSError:
        pass
    return result


# --------------------------------------------------------------------------
# measures
# --------------------------------------------------------------------------

def _a_weight(f):
    """The A-weighting curve as a power gain (IEC 61672), 1.0 at 1 kHz."""
    f2 = np.maximum(f, 1e-6) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2)
                                                                 * (f2 + 737.9 ** 2))
                                     * (f2 + 12194.0 ** 2))
    return (ra * 1.2589) ** 2


def _db(power: float) -> float:
    return 10.0 * math.log10(power) if power > 1e-14 else -140.0


def _loudness(seg, weighted: bool = True) -> float:
    """Mean power of a stereo segment, A-weighted unless told otherwise."""
    if len(seg) < 64:
        return 0.0
    # Zero-padded to a power of two: a bar is an arbitrary number of samples,
    # and an FFT of an awkward length is many times slower for the same answer.
    size = 1 << int(math.ceil(math.log2(len(seg))))
    w = _a_weight(np.fft.rfftfreq(size, 1.0 / SR)) if weighted else 1.0
    power = 0.0
    for ch in range(seg.shape[1]):
        spec = np.abs(np.fft.rfft(seg[:, ch], size)) ** 2
        power += float((spec * w).sum()) * 2.0 / (size * len(seg))
    return power / seg.shape[1]


def _centroid(mono) -> float:
    size = 1 << int(math.ceil(math.log2(len(mono))))
    spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono)), size)) ** 2
    total = float(spec.sum())
    if total <= 0:
        return 0.0
    return float((spec * np.fft.rfftfreq(size, 1.0 / SR)).sum() / total)


def roughness(mono, frame: int = 8192, peaks: int = 32) -> float:
    """Sensory dissonance of what is sounding (Sethares 1993, after Plomp and
    Levelt): every pair of strong partials contributes most when they are about
    a quarter of a critical band apart, and nothing when they coincide or are
    far apart. Amplitudes are normalized, so this is roughness and not volume.
    """
    if len(mono) < frame:
        return 0.0
    window = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1.0 / SR)
    values = []
    for start in range(0, len(mono) - frame + 1, frame // 2):
        mag = np.abs(np.fft.rfft(mono[start:start + frame] * window))
        mag[freqs < 40.0] = 0.0
        if mag.max() <= 1e-9:
            continue
        local = np.flatnonzero((mag[1:-1] > mag[:-2]) & (mag[1:-1] >= mag[2:])
                               & (mag[1:-1] > mag.max() * 0.01)) + 1
        if len(local) < 2:
            values.append(0.0)
            continue
        local = local[np.argsort(mag[local])[-peaks:]]
        f, a = freqs[local], mag[local] / mag[local].sum()
        lo = np.minimum.outer(f, f)
        gap = np.abs(np.subtract.outer(f, f))
        s = 0.24 / (0.0207 * lo + 18.96)
        curve = np.exp(-3.5 * s * gap) - np.exp(-5.75 * s * gap)
        values.append(float((np.minimum.outer(a, a) * curve).sum() / 2.0))
    return float(np.mean(values)) if values else 0.0


def _note_level(stem_mono, freq: float, start: int, length: int) -> float | None:
    """Power at a note's own harmonics during its own time, in dB."""
    seg = stem_mono[start:start + length]
    if len(seg) < 256:
        return None
    window = np.hanning(len(seg))
    size = max(4096, 1 << int(math.ceil(math.log2(len(seg)))))
    spec = np.abs(np.fft.rfft(seg * window, size)) ** 2
    res = SR / size
    # The window's own main lobe sets how wide a "partial" is in bins.
    half = max(2, int(math.ceil(2.0 * SR / len(seg) / res)))
    power = 0.0
    for h in (1, 2, 3, 4):
        centre = int(round(freq * h / res))
        if centre + half >= len(spec):
            break
        power += float(spec[max(1, centre - half):centre + half + 1].sum())
    return _db(power / float((window ** 2).sum()) / size + 1e-16)


# --------------------------------------------------------------------------
# the result
# --------------------------------------------------------------------------

@dataclass
class BarHeard:
    bar: int
    loudness: float                      # dBA of the mix
    brightness: float                    # Hz
    roughness: float
    voices: dict[str, float] = field(default_factory=dict)   # dBA per voice
    tune: str | None = None
    group: tuple[str, ...] = ()
    #: Tune (with its doublings) minus everything else combined, in dB.
    margin: float | None = None
    rival: str | None = None
    rival_margin: float | None = None


@dataclass
class WeakNote:
    voice: str
    bar: int
    beat: float
    pitch: int
    deficit: float
    ornament: bool
    dur: float


@dataclass
class Heard:
    piece: Piece
    through: str
    bars: list[BarHeard]
    weak: list[WeakNote]
    notes_measured: int


def hear(piece: Piece, rend: Render | None = None, *, source: str = "models",
         soundfont: str | None = None) -> Heard:
    _need_numpy()
    r = rend if rend is not None else render(piece)
    parts, through = stems(piece, r, source=source, soundfont=soundfont)
    to_sec = audio._tick_seconds(piece)
    doubles = followers(piece)
    mix = sum(parts.values()) if parts else np.zeros((1, 2))
    # Roughness is judged on the pitched voices: a cymbal is all roughness by
    # this measure, and that says nothing about the harmony.
    unpitched = {v.name for v in piece.voices if v.inst.percussive}
    tuned = sum((s for name, s in parts.items() if name not in unpitched),
                np.zeros_like(mix))
    bars: list[BarHeard] = []
    count = piece.total_bars
    for bar in range(1, count + 1):
        lo_t = piece.tick_of(bar)
        hi_t = piece.tick_of(bar + 1) if bar < count else piece.total_ticks
        lo, hi = int(to_sec(lo_t) * SR), int(to_sec(hi_t) * SR)
        seg = mix[lo:hi]
        mono = seg.mean(axis=1) if len(seg) else np.zeros(1)
        whole = _loudness(seg)
        b = BarHeard(bar, _db(whole), _centroid(mono) if len(mono) > 64 else 0.0,
                     roughness(tuned[lo:hi].mean(axis=1)) if hi > lo else 0.0)
        power = {name: _loudness(stem[lo:hi]) for name, stem in parts.items()}
        # A voice 60 dB under the mix is the tail of a note from the bar before.
        power = {name: p for name, p in power.items() if p > whole * 1e-6}
        b.voices = {name: _db(p) for name, p in power.items()}
        b.tune, group = tune_at(piece, r.notes, lo_t - EARLY, hi_t - EARLY, doubles)
        b.group = tuple(sorted(group))
        if b.tune and b.tune in b.voices:
            mine = sum(power.get(v, 0.0) for v in group)
            others = {v: p for v, p in power.items() if v not in group and p > 1e-12}
            if others:
                b.margin = _db(mine) - _db(sum(others.values()))
                b.rival = max(others, key=others.get)
                b.rival_margin = _db(mine) - _db(others[b.rival])
        bars.append(b)

    weak, measured = _weak_notes(piece, r, parts, to_sec)
    return Heard(piece, through, bars, weak, measured)


def _weak_notes(piece: Piece, r: Render, parts, to_sec) -> tuple[list[WeakNote], int]:
    """Notes whose own pitch is far quieter than that voice's other notes of
    the same strength and length -- the ones that did not really sound.

    The expectation is fitted per voice (level against velocity and against how
    long the note is measured for), so an instrument that is simply quiet, or
    whose short notes are naturally weaker, sets its own standard. Only a note
    that falls well outside its own voice's spread is reported.
    """
    weak: list[WeakNote] = []
    measured = 0
    for name, stem in parts.items():
        mono = stem.mean(axis=1)
        rows = []
        for n in r.notes:
            if n.voice != name or n.percussive:
                continue
            start = int(to_sec(n.start) * SR)
            seconds = to_sec(n.end) - to_sec(n.start)
            length = int(min(seconds, 0.5) * SR)
            level = _note_level(mono, 440.0 * 2 ** ((n.pitch - 69) / 12.0), start, length)
            if level is None:
                continue
            rows.append((n, level, 20 * math.log10(max(1, n.velocity) / 127.0),
                         math.log2(max(length, 1) / SR), seconds))
        if len(rows) < 8:
            continue
        measured += len(rows)
        y = np.array([row[1] for row in rows])
        x = np.array([[1.0, row[2], row[3]] for row in rows])
        coef, *_ = np.linalg.lstsq(x, y, rcond=None)
        resid = y - x @ coef
        spread = float(np.median(np.abs(resid - np.median(resid)))) * 1.4826
        limit = max(WEAK_DB, 3.5 * spread)
        for (n, _, _, _, seconds), d in zip(rows, resid):
            if d < -limit:
                bar, beat = piece.position_of((n.start + EARLY) // 60 * 60)
                weak.append(WeakNote(name, bar, float(beat), n.pitch, float(-d),
                                     n.ornament, seconds))
    weak.sort(key=lambda w: (w.bar, w.beat, w.voice))
    return weak, measured


# --------------------------------------------------------------------------
# the view
# --------------------------------------------------------------------------

def _scale(values: list[float], lo: float, hi: float) -> str:
    ramp = " .:-=+*#%@"
    span = max(1e-9, hi - lo)
    return "".join(ramp[max(0, min(len(ramp) - 1,
                                   int((v - lo) / span * (len(ramp) - 1) + 0.5)))]
                   for v in values)


def _margin_glyph(m: float | None) -> str:
    if m is None:
        return " "
    return "!" if m < 0 else "-" if m < CLEAR_DB else "=" if m < 6 else "+" if m < 10 else "#"


def reading(h: Heard) -> list[str]:
    """What the measurements show, in sentences. Descriptions, not verdicts."""
    out: list[str] = []
    bars = [b for b in h.bars if b.loudness > -120]
    if not bars:
        return ["nothing sounds"]
    loud = max(bars, key=lambda b: b.loudness)
    quiet = min(bars, key=lambda b: b.loudness)
    out.append(f"loudest bar {loud.bar} ({loud.loudness:.0f} dBA), quietest bar "
               f"{quiet.bar} ({quiet.loudness:.0f} dBA): a range of "
               f"{loud.loudness - quiet.loudness:.0f} dB")

    under = [b for b in h.bars if b.margin is not None and b.margin < 0]
    close = [b for b in h.bars if b.margin is not None and 0 <= b.margin < CLEAR_DB]
    for label, group in (("is quieter than everything else combined", under),
                         (f"clears the rest by under {CLEAR_DB:g} dB", close)):
        by_tune: dict[str, list[BarHeard]] = {}
        for b in group:
            by_tune.setdefault(b.tune, []).append(b)
        for tune, bs in by_tune.items():
            rivals: dict[str, int] = {}
            for b in bs:
                rivals[b.rival] = rivals.get(b.rival, 0) + 1
            rival = max(rivals, key=rivals.get)
            worst = min(bs, key=lambda b: b.margin)
            out.append(f"the tune ({tune}) {label} in bar {_spans([b.bar for b in bs])}; "
                       f"its loudest rival there is {rival} (worst: bar {worst.bar}, "
                       f"{worst.margin:+.1f} dB)")
    single = [b for b in h.bars if b.rival_margin is not None and b.rival_margin < 0]
    if single:
        pairs: dict[tuple[str, str], list[int]] = {}
        for b in single:
            pairs.setdefault((b.rival, b.tune), []).append(b.bar)
        for (rival, tune), where in pairs.items():
            out.append(f"{rival} alone is louder than the tune ({tune}) in bar "
                       f"{_spans(where)}")
    if not under and not close and any(b.margin is not None for b in h.bars):
        lowest = min((b for b in h.bars if b.margin is not None), key=lambda b: b.margin)
        out.append(f"the tune clears its accompaniment throughout; the narrowest "
                   f"margin is {lowest.margin:+.1f} dB in bar {lowest.bar} "
                   f"(against {lowest.rival})")

    rough = max(bars, key=lambda b: b.roughness)
    typical = sorted(b.roughness for b in bars)[len(bars) // 2]
    if typical > 0 and rough.roughness > 1.6 * typical:
        out.append(f"roughest bar {rough.bar}: {rough.roughness / typical:.1f}x the "
                   f"piece's median roughness")
    bright = max(bars, key=lambda b: b.brightness)
    dark = min(bars, key=lambda b: b.brightness)
    out.append(f"brightest bar {bright.bar} (centroid {bright.brightness:.0f} Hz), "
               f"darkest bar {dark.bar} ({dark.brightness:.0f} Hz)")

    written = [w for w in h.weak if not w.ornament]
    orn = [w for w in h.weak if w.ornament]
    for label, group in (("written note(s)", written), ("ornament note(s)", orn)):
        by_voice: dict[str, list[WeakNote]] = {}
        for w in group:
            by_voice.setdefault(w.voice, []).append(w)
        for voice, ws in by_voice.items():
            spots = ", ".join(f"{w.bar}:{w.beat:g}" for w in ws[:6])
            more = f" +{len(ws) - 6} more" if len(ws) > 6 else ""
            worst = max(ws, key=lambda w: w.deficit)
            out.append(f"{len(ws)} {label} in {voice} barely sound (up to "
                       f"{worst.deficit:.0f} dB under what that voice's other notes "
                       f"give): {spots}{more}")
    if not h.weak and h.notes_measured:
        out.append(f"all {h.notes_measured} pitched notes measured sound at the "
                   f"level their voice gives them")
    return out


def view(piece: Piece, rend: Render | None = None, *, source: str = "models",
         soundfont: str | None = None, heard: Heard | None = None) -> str:
    """One column per bar: loudness, brightness, roughness, who has the tune,
    who is loudest, and how far the tune clears the rest."""
    from .readback import _section_ruler, voice_glyphs
    h = heard if heard is not None else hear(piece, rend, source=source, soundfont=soundfont)
    glyph = voice_glyphs(piece)
    bars = h.bars
    sounding = [b for b in bars if b.loudness > -120]
    out = [f"{piece.name} -- as heard through {h.through}, {len(bars)} bars, one "
           f"column per bar (dry stems, measured)", ""]
    if not sounding:
        return "\n".join(out + ["  (nothing sounds)"])
    top = max(b.loudness for b in sounding)
    out.append(f"  {'loudness':<11}{_scale([b.loudness for b in bars], top - 30, top)}"
               f"   mix, A-weighted; full scale of the ramp is 30 dB")
    cents = [math.log2(max(b.brightness, 50.0)) for b in bars]
    out.append(f"  {'brightness':<11}"
               f"{_scale(cents, min(cents[i] for i, b in enumerate(bars) if b.loudness > -120), max(cents))}"
               f"   spectral centroid, "
               f"{min(b.brightness for b in sounding):.0f}-{max(b.brightness for b in sounding):.0f} Hz")
    out.append(f"  {'roughness':<11}"
               f"{_scale([b.roughness for b in bars], 0.0, max(b.roughness for b in bars) or 1.0)}"
               f"   sensory dissonance of what is sounding")
    out.append(f"  {'tune':<11}"
               + "".join(glyph.get(b.tune, "?") if b.tune else "." for b in bars)
               + "   who carries it")
    out.append(f"  {'loudest':<11}"
               + "".join((glyph.get(max(b.voices, key=b.voices.get), "?")
                          if b.voices else ".") for b in bars)
               + "   the loudest single voice")
    out.append(f"  {'clear':<11}" + "".join(_margin_glyph(b.margin) for b in bars)
               + f"   tune over everything else: ! under, - <{CLEAR_DB:g} dB, = <6, + <10, # more")
    out.append(f"  {'':<11}{_section_ruler(piece, len(bars))}")
    out.append("")
    out.append("  " + "  ".join(f"{g}={name}" for name, g in glyph.items()
                                if any(name in b.voices for b in bars)))
    out.append("")

    # Per-section levels: the table that shows a balance at a glance.
    names = [v.name for v in piece.voices if any(v.name in b.voices for b in bars)]
    secs = [(sec.name, first, first + sec.bars - 1) for sec, first, _ in piece.section_bounds()]
    out.append(f"  {'dBA by section':<16}" + "".join(f"{n[:8]:>9}" for n, _, _ in secs))
    for name in names:
        cells = []
        for _, a, z in secs:
            vals = [10 ** (b.voices[name] / 10) for b in bars[a - 1:z] if name in b.voices]
            n = z - a + 1
            cells.append(f"{_db(sum(vals) / n):9.1f}" if vals else f"{'-':>9}")
        out.append(f"  {name:<16}" + "".join(cells))
    out.append("")
    for line in reading(h):
        out.append(f"  - {line}")
    return "\n".join(out)


def to_json(h: Heard) -> dict:
    return {"through": h.through,
            "bars": [{"bar": b.bar, "loudness": round(b.loudness, 1),
                      "brightness": round(b.brightness), "roughness": round(b.roughness, 4),
                      "tune": b.tune, "doubled_by": [v for v in b.group if v != b.tune],
                      "margin": None if b.margin is None else round(b.margin, 1),
                      "rival": b.rival,
                      "voices": {k: round(v, 1) for k, v in b.voices.items()}}
                     for b in h.bars],
            "weak_notes": [{"voice": w.voice, "bar": w.bar, "beat": w.beat,
                            "deficit_db": round(w.deficit, 1), "ornament": w.ornament}
                           for w in h.weak],
            "reading": reading(h)}
