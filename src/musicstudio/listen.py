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
import re
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
        sampled = audio.prerendered(piece, r.notes, to_sec, total, pans)
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


def _fixed(buf, lo: int, n: int):
    """Exactly ``n`` frames from ``lo``, padded with silence. The two renders
    being compared are different lengths (a sampler rings on, a model stops),
    and a mean over "whatever is left" is then a mean over different times:
    the same waveform, zero-padded, measured 3 dB apart that way."""
    seg = buf[lo:lo + n]
    if len(seg) < n:
        seg = np.concatenate([seg, np.zeros((n - len(seg),) + seg.shape[1:])])
    return seg


def _calibrate_font(names: list[str]) -> dict:
    """Trim and velocity curve for instruments sampled from their own bank.

    The same measurement as ``calibrate``, one instrument at a time through
    the path that will play it (``audio.sampled_stems``), against its model.
    """
    from .doc import Section, Voice
    from .ensemble import INSTRUMENTS
    from .theory import DYNAMICS
    soft, loud, mid = DYNAMICS["p"], DYNAMICS["f"], DYNAMICS["mf"]
    span = 20 * math.log10(loud / soft)
    trims: dict[str, float] = {}
    curve: dict[str, float] = {}
    for name in names:
        inst = INSTRUMENTS[name]
        levels = {}
        for engine in (None, "soundfont"):
            p = Piece("calibrate", "C major", tempo=60, style="freeform")
            p.sections.append(Section("A", 4))
            p.voices.append(Voice("v", name, "percussion" if inst.percussive else "melody",
                                  pan=0.0, engine=engine))
            for j, dyn in enumerate(("p", "f")):
                if inst.percussive:
                    p.add_op("v", "beat", id=f"c{dyn}", at=str(1 + 2 * j), bars=1,
                             dynamic=dyn, res="1/8",
                             lanes={"kick": "x...x...", "snare": "..x...x.",
                                    "hat": "xxxxxxxx"})
                else:
                    p.add_op("v", "phrase", id=f"c{dyn}", at=str(1 + 2 * j), unit="1/4",
                             steps="0 4 7 4", dynamic=dyn)
            to_sec = audio._tick_seconds(p)
            if engine is None:
                left, right = audio.synthesize(p, reverb=False, models=True)
            else:
                r = render(p)
                total = int((to_sec(p.total_ticks) + 2.0) * SR)
                got = audio.sampled_stems(p, r.notes, to_sec, total, bare=True)
                if "v" not in got:
                    break
                left, right = got["v"]
            buf = np.stack([np.asarray(left), np.asarray(right)], 1)
            heard = inst.percussive or inst.centre >= 48
            levels[engine] = [
                _loudness(_fixed(buf, int(to_sec(p.tick_of(1 + 2 * j)) * SR), 8 * SR),
                          heard) for j in (0, 1)]
        if len(levels) < 2 or min(levels[None] + levels["soundfont"]) <= 1e-12:
            continue
        m_soft, m_loud = (_db(x) for x in levels[None])
        s_soft, s_loud = (_db(x) for x in levels["soundfont"])
        s_slope, m_slope = (s_loud - s_soft) / span, (m_loud - m_soft) / span
        c = max(0.35, min(1.25, m_slope / s_slope)) if s_slope > 0.2 else 1.0
        curve[name] = round(c, 2)
        sent = 127 * (mid / 127) ** c
        s_mid = s_soft + s_slope * 20 * math.log10(sent / soft)
        m_mid = m_soft + m_slope * 20 * math.log10(mid / soft)
        trims[name] = round(max(-24.0, min(24.0, m_mid - s_mid)), 1)
    return {"trim": trims, "curve": curve, "offset": 0.0}


# --------------------------------------------------------------------------
# matching a sampler to the models
# --------------------------------------------------------------------------

#: The most a bank's instrument is ever turned up or down to match.
MAX_TRIM_DB = 10.0
CACHE_DIR = Path("~/.cache/musicstudio")


def calibrate(bank: str | Path, *, refresh: bool = False,
              font: str | None = None) -> dict[str, dict[str, float]]:
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

    ``font`` names a catalogued bank for particular instruments
    (``soundfonts.BANKS``): then only the instruments that live in it are
    measured, each against its own model, and nothing is centred -- such a
    bank is not a balanced set, it is a few sounds that each have to sit at
    the level the rest of the studio expects.
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
    if font is None:
        names = [n for n in synth.MODELS
                 if not INSTRUMENTS[n].percussive and INSTRUMENTS[n].font is None] + ["kit"]
    else:
        names = [n for n in synth.MODELS if INSTRUMENTS[n].font == font]
    # The cache is for this file, this level, and this list of instruments:
    # an instrument added later must be measured, not found missing.
    tag = hashlib.sha1(f"{bank.resolve()}|{stat.st_size}|{int(stat.st_mtime)}|"
                       f"{synth.LEVEL}|{font}|{','.join(names)}|v7".encode()).hexdigest()[:16]
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
    if font is not None:
        result = _calibrate_font(names)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(result))
        return result
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
                return _loudness(_fixed(buf, int(to_sec(p.tick_of(bar)) * SR), 8 * SR),
                                 weighted)

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
    #: Per voice, over the whole piece: what kind of sound it is and how it is
    #: played (``_character``). The things a score view cannot show and a
    #: listener says first: "the bass is all click", "the guitars are in the
    #: middle", "every note is the same note".
    character: dict[str, dict] = field(default_factory=dict)
    #: Silences inside the piece: ``(bar, beat, seconds, declared)``.
    gaps: list[tuple[int, float, float, bool]] = field(default_factory=list)


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
    return Heard(piece, through, bars, weak, measured,
                 _character(piece, r, parts), _gaps(piece, r, mix, to_sec))


#: A run of one pitch at one loudness this long is reported: on a sampled
#: instrument it is one recording played that many times.
SAME_NOTE_RUN = 12
#: A hole in the middle of the music this long, this far under what is around it.
GAP_SECONDS, GAP_DB = 0.3, 40.0


def _character(piece: Piece, r: Render, parts) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for v in piece.voices:
        stem = parts.get(v.name)
        if stem is None or not len(stem):
            continue
        mid, side = stem.mean(axis=1), (stem[:, 0] - stem[:, 1]) * 0.5
        power = float(np.mean(mid ** 2))
        if power < 1e-12:
            continue
        # Whole half-second frames, the louder half of them: picking loud
        # *samples* out of a wave re-times it, and a 3.9 kHz sine then reads
        # as mostly above 4 kHz.
        sound = _stem_sound(mid)
        if not sound:
            continue
        notes = sorted((n for n in r.notes if n.voice == v.name and not n.ornament),
                       key=lambda n: n.start)
        run = best = 1
        where = notes[0].start if notes else 0
        at = where
        first_vel = notes[0].velocity if notes else 0
        for a, b in zip(notes, notes[1:]):
            # A rest longer than the note before it ends the run: the ear
            # resets, and so does a player's hand. Loudness is held against
            # the run's first note, or a slow crescendo would count as one.
            if a.pitch == b.pitch and abs(b.velocity - first_vel) <= 2 and \
                    not v.inst.percussive and b.start - a.end <= a.dur:
                run += 1
                if run > best:
                    best, where = run, at
            else:
                run, at, first_vel = 1, b.start, b.velocity
        vels = [n.velocity for n in notes]
        out[v.name] = {
            "centroid": sound["centroid"], "above4k": sound["above4k"],
            "below100": sound["below100"],
            "width": float(np.mean(side ** 2)) / (power + float(np.mean(side ** 2))),
            "vel_spread": float(np.std(vels)) if len(vels) > 1 else 0.0,
            "notes": len(notes), "run": best,
            "run_bar": piece.position_of(where)[0] if notes else 0,
            "sampled": v.engine == "soundfont"}
    return out


def _gaps(piece: Piece, r: Render, mix, to_sec) -> list[tuple[int, float, float, bool]]:
    """Stretches where the mix falls silent between two stretches of music."""
    if not r.notes or not len(mix):
        return []
    hop = 441                                           # 10 ms
    mono = mix.mean(axis=1)
    n = len(mono) // hop
    level = np.sqrt(np.mean(mono[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-20)
    first = int(to_sec(min(x.start for x in r.notes)) * SR / hop)
    last = min(n, int(to_sec(max(x.end for x in r.notes)) * SR / hop))
    if last - first < 200:
        return []
    # Each frame against the loudest of the second before it: a decay is not a
    # gap, a hole in the middle of a groove is.
    stops = [(piece.tick_of(s["from"]), piece.tick_of(s["until"]))
             for s in (piece.meta.get("master") or {}).get("stops") or []]
    floor = 10 ** (-GAP_DB / 20)
    out = []
    i = first + 100
    while i < last:
        around = float(level[max(first, i - 100):i].max())
        if level[i] < around * floor:
            j = i
            while j < last and level[j] < around * floor:
                j += 1
            seconds = (j - i) * hop / SR
            if j < last and seconds >= GAP_SECONDS:
                tick = _tick_at(piece, to_sec, i * hop / SR)
                bar, beat = piece.position_of(tick)
                declared = any(lo - 120 <= tick < hi for lo, hi in stops)
                out.append((bar, float(beat), seconds, declared))
            i = j + 1
        else:
            i += 1
    return out


def _tick_at(piece: Piece, to_sec, seconds: float) -> int:
    lo, hi = 0, piece.total_ticks
    while lo < hi:
        mid = (lo + hi) // 2
        if to_sec(mid) < seconds:
            lo = mid + 1
        else:
            hi = mid
    return lo


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
    # A note written under a stop or a `cut` is silent on purpose: it is
    # neither a fault to report nor a fair sample of how loud the voice plays.
    silenced: dict[str, list[tuple[int, int]]] = {}
    for st in (piece.meta.get("master") or {}).get("stops") or []:
        for v in piece.voices:
            if v.name not in (st.get("keep") or ()):
                silenced.setdefault(v.name, []).append(
                    (piece.tick_of(st["from"]), piece.tick_of(st["until"])))
    for v in piece.voices:
        for op in v.ops:
            if op.kind == "cut" and op.enabled:
                silenced.setdefault(v.name, []).append(
                    (piece.tick_of(op.params["from"]), piece.tick_of(op.params["until"])))
    for name, stem in parts.items():
        mono = stem.mean(axis=1)
        rows = []
        for n in r.notes:
            if n.voice != name or n.percussive:
                continue
            if any(min(n.end, hi) - max(n.start, lo) >= 0.5 * (n.end - n.start)
                   for lo, hi in silenced.get(name, ())):
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
    out += _reading_character(h)
    return out


def _runs(bars: list[int]) -> str:
    """``[3, 4, 5, 9]`` -> ``'3-5, 9'``."""
    out, start, prev = [], None, None
    for b in bars + [None]:
        if start is None:
            start = prev = b
        elif b is not None and b == prev + 1:
            prev = b
        else:
            out.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = b
    return ", ".join(out)


def _reading_character(h: Heard) -> list[str]:
    """What a listener would say first and no score view can: one thing far
    too loud, a note repeated like a machine, a hole, a voice that is all top
    or sits in the middle of the stage. Each is a measurement with its number;
    whether it is wanted is the writer's call."""
    out: list[str] = []
    piece = h.piece
    role = {v.name: v.role for v in piece.voices}
    # One voice over everything else put together, when it is not the tune.
    over: dict[str, list[tuple[int, float]]] = {}
    for b in h.bars:
        if len(b.voices) < 2:
            continue
        top = max(b.voices, key=b.voices.get)
        rest = _db(sum(10 ** (v / 10) for k, v in b.voices.items() if k != top))
        # A pad alone in an introduction, or a bass under a thin texture, is
        # the texture. An ornament, a counter-line or percussion over the
        # whole band is the thing a listener calls "way too loud".
        # ... and over a band that is there: twenty dB clear of everything
        # is a solo, which is a decision, not a balance.
        if top != b.tune and top not in b.group and 6.0 <= b.voices[top] - rest < 20.0 \
                and role.get(top) in ("ornament", "counter", "percussion", "harmony"):
            over.setdefault(top, []).append((b.bar, b.voices[top] - rest))
    for voice, hits in over.items():
        worst = max(d for _, d in hits)
        out.append(f"{voice} ({role.get(voice)}) alone is up to {worst:.0f} dB louder "
                   f"than everything else together in bar {_runs([b for b, _ in hits])}")
    for voice, c in h.character.items():
        if c["run"] >= SAME_NOTE_RUN:
            kind = ("a sampled instrument, so one recording that many times"
                    if c["sampled"] else "the model gives each its own onset noise")
            out.append(f"{voice} plays one pitch at one loudness {c['run']} times in a "
                       f"row from bar {c['run_bar']} ({kind}); accents ('!') or "
                       f"`humanize` vary it")
    for bar, beat, seconds, declared in h.gaps:
        out.append(f"{seconds:.2f} s of silence at {bar}:{beat:g}"
                   + (" (a declared stop)" if declared else
                      " in the dry stems -- nothing is written there (the room's tail "
                      "may cover some of it in the render)"))
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
    if h.character:
        out += ["", f"  {'what each voice is':<16}{'centre Hz':>10}{'>4 kHz':>8}{'<100 Hz':>9}"
                    f"{'width':>7}{'notes':>7}{'vel +/-':>9}{'same x':>8}"]
        for name in names:
            c = h.character.get(name)
            if c:
                out.append(f"  {name:<16}{c['centroid']:10.0f}{c['above4k']:7.0f}%"
                           f"{c['below100']:8.0f}%{c['width']:7.2f}{c['notes']:7d}"
                           f"{c['vel_spread']:9.1f}{c['run']:8d}")
        out.append("  (width 0 is the middle of the stage, 0.5 as wide as it goes; "
                   "'same x' is the longest run of one pitch at one loudness)")
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
            "voices": {k: {a: (round(b, 2) if isinstance(b, float) else b)
                           for a, b in c.items()} for k, c in h.character.items()},
            "gaps": [{"bar": b, "beat": bt, "seconds": round(s, 2), "declared": d}
                     for b, bt, s, d in h.gaps],
            "reading": reading(h)}


# --------------------------------------------------------------------------
# against a reference recording
# --------------------------------------------------------------------------

#: Band edges in Hz, and what each is called in the report.
MATCH_BANDS = ((20, 60, "sub"), (60, 120, "bass"), (120, 250, "low"), (250, 500, "lo-mid"),
               (500, 1000, "mid"), (1000, 2000, "hi-mid"), (2000, 4000, "presence"),
               (4000, 8000, "top"), (8000, 16000, "air"))


def _profile(x, lo: int, hi: int) -> dict:
    """What one stretch of mono audio is like: level, spectrum, how busy."""
    seg = x[lo:hi]
    if len(seg) < 4096:
        return {}
    n, hop = 4096, 1024
    frames = np.lib.stride_tricks.sliding_window_view(seg, n)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(n), axis=1)) ** 2
    f = np.fft.rfftfreq(n, 1.0 / SR)
    mean = spec.mean(0)
    total = float(mean[(f >= 20) & (f < 16000)].sum()) or 1e-20
    bands = [_db(float(mean[(f >= a) & (f < b)].sum()) / total) for a, b, _ in MATCH_BANDS]
    flux = np.maximum(0.0, np.diff(np.log1p(100.0 * np.sqrt(spec)), axis=0)).sum(1)
    hits = 0.0
    if len(flux) > 8:
        floor = float(np.median(flux)) + 1.5 * float(flux.std())
        peak = (flux[1:-1] > flux[:-2]) & (flux[1:-1] >= flux[2:]) & (flux[1:-1] > floor)
        hits = float(peak.sum()) / (len(seg) / SR)
    power = float(np.mean(seg ** 2))
    return {"level": _db(power), "bands": bands, "hits": hits,
            "centroid": float((mean * f).sum() / (mean.sum() or 1e-20)),
            "under80": 100.0 * float(mean[(f >= 20) & (f < 80)].sum()) / total,
            "crest": _db(float(np.max(np.abs(seg)) ** 2) / (power or 1e-20))}


def _pulse(x) -> float | None:
    """The strongest repeating period of the onsets, as beats a minute in
    60-240 (so a double or half reading is possible; both are printed)."""
    n, hop = 2048, 512
    if len(x) < SR * 8:
        return None
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(n), axis=1))
    flux = np.maximum(0.0, np.diff(np.log1p(100.0 * spec), axis=0)).sum(1)
    flux = flux - flux.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(flux, 2 * len(flux))) ** 2)[:len(flux)]
    best, at = -1.0, None
    for bpm in np.arange(60.0, 240.0, 0.25):
        lag = 60.0 / bpm * SR / hop
        score = sum(float(np.interp(lag * k, np.arange(len(ac)), ac)) for k in (1, 2, 4))
        if score > best:
            best, at = score, float(bpm)
    return at


def match(piece: Piece, reference: str | Path, *, slices: int = 10,
          stems_dir: str | Path | None = None) -> str:
    """A piece's render beside a reference recording, measured the same way.

    This is a *measurement*, and of two things only a recording can show: what
    the spectrum is and where the energy is over time. It cannot say whether
    the writing is like the reference's. Levels are each track's own -- every
    figure is relative to that track's total or to its loudest stretch -- so a
    reference mastered louder does not read as a difference.

    When the two are within 5% of the same length the piece's own sections are
    laid over the reference (it was written to that form); otherwise both are
    cut into ``slices`` equal parts.

    ``stems_dir`` is a folder holding the reference separated into stems by
    any source-separation tool: files named ``drums``, ``bass`` and anything
    else (``other``, ``guitar``, ``vocals`` ...). With it the report compares
    the *balance* -- drums against bass against the rest, section by section
    -- and the drum pattern, which a mix cannot give: two mixes can have the
    same spectrum with the kit 11 dB apart. The studio never separates
    anything itself; that is someone's model, run on purpose.

    What the figures are not. A band is given as a *share* of its track's
    energy, so one band turned up lowers every other band's share: read the
    row as a shape, and fix the largest difference first. And none of it is a
    target: "45% of the energy under 80 Hz" describes one master on one
    system. A stem's power is its hits, their length, how many there are and
    what the separator leaked into it, all at once -- which is why the drums
    also get their hit level and how much of the time they fill.

    Not here, because it was tried and failed its test: reading the harmony's
    rate of change, or the bass's note, bar by bar out of a recording. Against
    a transcription of a real track it told a chord change from a held chord
    62% of the time, stems or no stems. A row of confident marks that is
    wrong one bar in three is worse than no row.
    """
    _need_numpy()
    from .ingest import decode_audio
    ref = np.asarray(decode_audio(reference, SR), dtype=np.float64)
    # The mastered mix, as `save_wav` writes it: the limiter and any clipping
    # are part of what is heard, and of the crest and the top of the spectrum.
    left, right = audio.synthesize(piece)
    how = piece.meta.get("master") or {}
    left, right = audio._master(
        np.asarray(left), np.asarray(right),
        push=float(how.get("push", audio.MASTER_PUSH.get(piece.style, 3.5))),
        clip=float(how.get("clip", 0.0)))
    mine = (np.asarray(left) + np.asarray(right)) * 0.5
    to_sec = audio._tick_seconds(piece)
    len_m, len_r = len(mine) / SR, len(ref) / SR
    # The render carries a tail of reverb; the music ends where the form does.
    end_m = to_sec(piece.total_ticks)
    quiet = np.where(np.abs(ref) > 10 ** (-50 / 20) * (np.abs(ref).max() or 1.0))[0]
    end_r = (quiet[-1] / SR) if len(quiet) else len_r
    same_form = abs(end_m - end_r) <= 0.05 * max(end_m, end_r)
    spans: list[tuple[str, float, float, float, float]] = []
    if same_form:
        for sec, first, start in piece.section_bounds():
            a, b = to_sec(start), to_sec(start + sec.length)
            spans.append((sec.name, a, b, a, b))
    else:
        for i in range(slices):
            spans.append((f"{i + 1}/{slices}", end_m * i / slices, end_m * (i + 1) / slices,
                          end_r * i / slices, end_r * (i + 1) / slices))
    rows = []
    for name, a, b, ra, rb in spans:
        pm = _profile(mine, int(a * SR), int(b * SR))
        pr = _profile(ref, int(ra * SR), int(rb * SR))
        if pm and pr:
            rows.append((name, a, pm, pr))
    # Which voice holds each band in each stretch, from the dry stems: a
    # difference is only useful with the name of the line that makes it.
    parts, _ = stems(piece)
    span_of = {name: (int(a * SR), int(b * SR)) for name, a, b, _, _ in spans}
    shaping = ("gain", "eq", "filter", "dynamics", "drive", "compress", "crush")
    tick_of = {name: (_tick_at(piece, to_sec, a), _tick_at(piece, to_sec, b))
               for name, a, b, _, _ in spans}

    def holder(span: str, band: int) -> str:
        lo, hi = span_of[span]
        a, b, _ = MATCH_BANDS[band]
        share: dict[str, float] = {}
        for voice, stem in parts.items():
            seg = stem[lo:hi].mean(axis=1)
            if len(seg) < 4096:
                continue
            size = 1 << int(math.ceil(math.log2(len(seg))))
            spec = np.abs(np.fft.rfft(seg, size)) ** 2
            f = np.fft.rfftfreq(size, 1.0 / SR)
            share[voice] = float(spec[(f >= a) & (f < b)].sum())
        total = sum(share.values())
        if total <= 0:
            return ""
        top = sorted(share, key=share.get, reverse=True)[:2]
        who = ", ".join(f"{v} {100 * share[v] / total:.0f}%" for v in top
                        if share[v] / total >= 0.15)
        tick_lo, tick_hi = tick_of[span]
        mine = [o for o in piece.get_voice(top[0]).ops if o.kind in shaping and o.enabled
                and (o.params.get("from") is None
                     or piece.tick_of(o.params["from"]) < tick_hi)
                and (o.params.get("until") is None
                     or piece.tick_of(o.params["until"]) > tick_lo)]
        mine.sort(key=lambda o: shaping.index(o.kind))
        ops = [o.id for o in mine][:4]
        return (f" -- there that band is {who}"
                + (f"; level and tone of {top[0]}: {', '.join(ops)}" if ops else
                   f"; {top[0]} has no level or tone op yet"))
    whole_m = _profile(mine, 0, int(end_m * SR))
    whole_r = _profile(ref, 0, int(end_r * SR))
    out = [f"{piece.name} against {Path(reference).name} -- measured from the two "
           f"recordings, each relative to its own level",
           f"  length    {end_m:6.1f} s  vs  {end_r:6.1f} s"
           + ("   (same form: the piece's sections are laid over the reference)"
              if same_form else f"   (different lengths: compared in {slices} equal parts)")]
    bm, br = _pulse(mine), _pulse(ref)
    if bm and br:
        out.append(f"  pulse     {bm:6.1f}     vs  {br:6.1f} bpm   (or half, or double)")
    if whole_m and whole_r:
        out.append(f"  under 80 Hz {whole_m['under80']:4.0f}%  vs  {whole_r['under80']:4.0f}% "
                   f"of the energy")
        out.append(f"  centroid  {whole_m['centroid']:6.0f}     vs  {whole_r['centroid']:6.0f} Hz")
        out.append(f"  crest     {whole_m['crest']:6.1f}     vs  {whole_r['crest']:6.1f} dB   "
                   f"(peak over average: lower is denser, more compressed)")
    if not rows:
        return "\n".join(out + ["  (too short to compare)"])
    top_m = max(r[2]["level"] for r in rows)
    top_r = max(r[3]["level"] for r in rows)
    names = [n for _, _, n in MATCH_BANDS]
    out += ["", "  spectrum, piece minus reference, dB (each band as a share of its own "
                "track's energy there; + is more of it than the reference has)",
            "  " + " " * 18 + "".join(f"{n:>9}" for n in names)]
    notes: list[tuple[float, str, tuple | None]] = []
    out_of: dict[tuple[int, bool], list[tuple[str, float]]] = {}
    for name, a, pm, pr in rows:
        diffs = [m - r for m, r in zip(pm["bands"], pr["bands"])]
        cells = "".join(f"{d:+9.0f}" if max(m, r) > -45 else f"{'.':>9}"
                        for d, m, r in zip(diffs, pm["bands"], pr["bands"]))
        out.append(f"  {name:<10}{int(a) // 60}:{int(a) % 60:02d}   {cells}")
        for k, (d, m, r) in enumerate(zip(diffs, pm["bands"], pr["bands"])):
            if abs(d) >= 6 and max(m, r) > -30:
                out_of.setdefault((k, d > 0), []).append((name, abs(d)))
    out += ["", "  over time (level is below each track's own loudest part)",
            f"  {'':<16}{'level dB':>16}{'hits/s':>14}{'under 80 Hz':>16}{'centroid Hz':>18}"]
    for name, a, pm, pr in rows:
        lm, lr = pm["level"] - top_m, pr["level"] - top_r
        out.append(f"  {name:<10}{int(a) // 60}:{int(a) % 60:02d}  "
                   f"{lm:7.1f} /{lr:6.1f}  {pm['hits']:5.1f} /{pr['hits']:5.1f}  "
                   f"{pm['under80']:6.0f}% /{pr['under80']:4.0f}%  "
                   f"{pm['centroid']:8.0f} /{pr['centroid']:6.0f}")
        if same_form and abs(lm - lr) >= 4:
            notes.append((abs(lm - lr) + 2, f"{name}: sits {abs(lm - lr):.0f} dB "
                          f"{'higher' if lm > lr else 'lower'} against its own loudest "
                          f"part than the reference does", None))
        if same_form and pr["hits"] > 0.5 and (pm["hits"] > 1.6 * pr["hits"]
                                               or pm["hits"] < 0.6 * pr["hits"]):
            notes.append((3.0, f"{name}: {pm['hits']:.1f} hits a second where the "
                               f"reference has {pr['hits']:.1f}", None))
    if stems_dir is not None:
        out += _match_stems(piece, parts, Path(stems_dir), spans, to_sec, same_form, notes)
    out += ["", "  furthest from the reference (piece / reference in the table above):"]
    # One line a band, not one a section: "the top is 8 dB over from the build
    # to the end" is one thing to fix, in one place.
    if not same_form:
        # Two different songs cut into tenths: part 3 of one is a verse and of
        # the other a chorus, so a difference in one part says nothing. What
        # holds in most parts, in the same direction, is the mix.
        held = {}
        for (k, over), where in out_of.items():
            if len(where) >= 0.6 * len(rows):
                mids = sorted(d for _, d in where)
                held[(k, over)] = (mids[len(mids) // 2], len(where),
                                   max(where, key=lambda w: w[1])[0])
        for (k, over), (mid, count, worst) in held.items():
            notes.append((mid + count, f"{names[k]} is about {mid:.0f} dB "
                          f"{'over' if over else 'under'} the reference in {count} of "
                          f"{len(rows)} parts of the song", (worst, k)))
        out_of = {}
    for (k, over), where in out_of.items():
        worst = max(where, key=lambda w: w[1])
        lo, hi = min(d for _, d in where), worst[1]
        size = f"{hi:.0f}" if hi - lo < 1 else f"{lo:.0f}-{hi:.0f}"
        notes.append((hi + len(where), f"{names[k]} is {size} dB "
                      f"{'over' if over else 'under'} the reference in "
                      f"{', '.join(n for n, _ in where)}", (worst[0], k)))
    notes.sort(key=lambda n: -n[0])
    out += [f"  - {text}{holder(*key) if key else ''}" for _, text, key in notes[:12]] or \
           ["  - nothing is 6 dB out in any band, or 4 dB out in level"]
    return "\n".join(out)


def _grid_raw(x, piece: Piece, to_sec, first: int, last: int, lo: float, hi: float):
    """Onset strength in one band on a sixteenth grid, averaged over every two
    bars of a span: 32 numbers, not yet scaled."""
    n, hop = 1024, 256
    a0 = max(0, int(to_sec(piece.tick_of(first)) * SR) - SR)
    z0 = min(len(x), int(to_sec(piece.tick_of(last)) * SR) + SR) if last <= piece.total_bars \
        else len(x)
    seg = x[a0:z0]
    acc = np.zeros(32)
    if len(seg) < 4 * n:
        return acc
    frames = np.lib.stride_tricks.sliding_window_view(seg, n)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(n), axis=1))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    env = np.maximum(0.0, np.diff(np.log1p(50.0 * spec[:, (f >= lo) & (f < hi)]),
                                  axis=0)).sum(1)
    rate = SR / hop
    count = 0
    for bar in range(first, last - 1, 2):
        t0 = to_sec(piece.tick_of(bar)) - a0 / SR
        step = (to_sec(piece.tick_of(bar + 2)) - a0 / SR - t0) / 32
        for i in range(32):
            a, z = int((t0 + i * step - 0.02) * rate), int((t0 + i * step + 0.05) * rate)
            if 0 <= a < z <= len(env):
                acc[i] += float(env[a:z].max())
        count += 1
    return acc / max(1, count)


def _grid(x, piece: Piece, to_sec, first: int, last: int, lo: float, hi: float,
          top: float | None = None) -> str:
    """The grid as marks. ``top`` is the strength that counts as loudest --
    the track's own strongest section -- so a section where the hats have
    all but gone shows as dots, not as a pattern scaled back up to full."""
    acc = _grid_raw(x, piece, to_sec, first, last, lo, hi)
    top = top or float(acc.max())
    if top <= 0 or float(acc.max()) <= 0:
        return ""
    row = "".join("X" if v > 0.75 * top else "x" if v > 0.45 * top else
                  "o" if v > 0.25 * top else "." for v in acc)
    return row[:16] + "|" + row[16:]


def _stem_hits(drums, bass) -> dict:
    """How hard a kit is hit and how much of the time it is sounding: the
    level its loudest tenth of a second-hundredths reach (against the same for
    the bass), the share of the time it is within 20 dB of that, and how many
    onsets a second."""
    hop = SR // 100
    n = min(len(drums), len(bass)) // hop
    if n < 200:
        return {}
    d = np.sqrt(np.mean(drums[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-20)
    b = np.sqrt(np.mean(bass[:n * hop].reshape(n, hop) ** 2, axis=1) + 1e-20)
    peak, bass_peak = float(np.percentile(d, 95)), float(np.percentile(b, 95))
    if peak <= 1e-6 or bass_peak <= 1e-6:
        return {}
    active = d > peak * 10 ** (-40 / 20)
    if active.sum() < 100:
        return {}
    rise = (d[1:-1] > d[:-2]) & (d[1:-1] >= d[2:]) & (d[1:-1] > peak * 10 ** (-12 / 20)) \
        & (d[1:-1] > 1.5 * np.minimum(d[:-2], np.roll(d, 3)[1:-1]))
    seconds = float(active.sum()) / 100.0
    return {"over_bass": 20 * math.log10(peak / bass_peak),
            "occupancy": 100.0 * float((d[active] > peak * 10 ** (-20 / 20)).mean()),
            "rate": float(rise.sum()) / max(1.0, seconds)}


def _stem_sound(x) -> dict:
    """Spectrum shares of one stem over the half of it that is loudest."""
    hop = SR // 2
    n = len(x) // hop
    if n < 4:
        return {}
    level = np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)
    keep = np.argsort(level)[n // 2:]
    if level[keep].max() <= 0:
        return {}
    acc = None
    for k in keep[:240]:
        spec = np.abs(np.fft.rfft(x[k * hop:(k + 1) * hop] * np.hanning(hop))) ** 2
        acc = spec if acc is None else acc + spec
    f = np.fft.rfftfreq(hop, 1.0 / SR)
    total = float(acc.sum()) or 1e-20
    return {"centroid": float((acc * f).sum() / total),
            "above4k": 100.0 * float(acc[f >= 4000].sum()) / total,
            "presence": 100.0 * float(acc[(f >= 2000) & (f < 4000)].sum()) / total,
            "below100": 100.0 * float(acc[f < 100].sum()) / total}


def _match_stems(piece: Piece, parts, folder: Path, spans, to_sec, same_form: bool,
                 notes: list) -> list[str]:
    """Drums, bass and everything else: the piece's own stems, grouped by what
    each voice is, beside a separated reference."""
    from .ingest import decode_audio
    files = {f.stem.lower(): f for f in sorted(folder.iterdir())
             if f.suffix.lower() in (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus")}
    if "drums" not in files or "bass" not in files:
        raise FileNotFoundError(f"{folder} needs at least drums.* and bass.* "
                                f"(found {sorted(files) or 'no audio'})")
    def load(path) -> "np.ndarray":
        # A separator's empty stem is often a constant offset, not silence;
        # as power that is a loud instrument that is not there. Nothing
        # under 20 Hz is music.
        x = np.asarray(decode_audio(path, SR), dtype=np.float64)
        spec = np.fft.rfft(x)
        spec[:max(1, int(20.0 * len(x) / SR))] = 0
        return np.fft.irfft(spec, len(x))

    ref = {"drums": load(files["drums"]), "bass": load(files["bass"])}
    if "vocals" in files:
        ref["vocals"] = load(files["vocals"])
    others = [load(f) for name, f in files.items()
              if name not in ("drums", "bass", "vocals")]
    if others:
        size = min(len(o) for o in others)
        ref["rest"] = sum(o[:size] for o in others)
    groups: dict[str, list[str]] = {g: [] for g in ("drums", "bass", "vocals", "rest")}
    for v in piece.voices:
        if v.name in parts:
            groups["drums" if v.inst.percussive else "bass" if v.role == "bass"
                   else "vocals" if v.inst.family == "voice" and "vocals" in ref
                   else "rest"].append(v.name)
    if "vocals" not in ref:
        groups.pop("vocals")
    size = len(next(iter(parts.values())))
    mine = {g: (sum(parts[n].mean(axis=1) for n in names) if names else np.zeros(size))
            for g, names in groups.items()}

    out = ["", "  balance by stem: each against the rest of its own band in that "
               "section, dB (piece / reference). The piece's are its dry stems, the "
               "reference's the separated ones"]
    table = {}
    for label, track, cols in (("m", mine, [(n, a, b) for n, a, b, _, _ in spans]),
                               ("r", ref, [(n, ra, rb) for n, _, _, ra, rb in spans])):
        power = {g: [float(np.mean(x[int(a * SR):int(b * SR)] ** 2))
                     if len(x[int(a * SR):int(b * SR)]) > 64 else 0.0 for _, a, b in cols]
                 for g, x in track.items()}
        whole = max(max(v) for v in power.values()) or 1e-20
        # A stem 40 dB under the track's loudest is not playing there: its
        # "balance" would be a ratio of two silences.
        table[label] = {
            g: [(_db(v[k]) - _db(sum(power[o][k] for o in power if o != g) or 1e-20))
                if v[k] > whole * 1e-4 else None for k in range(len(cols))]
            for g, v in power.items()}
    out.append("  " + " " * 8 + "".join(f"{n[:9]:>13}" for n, *_ in spans))
    for g in ("drums", "bass", "vocals", "rest"):
        if g not in table["r"] or g not in table["m"]:
            continue
        show = lambda v: "  -" if v is None else f"{v:+3.0f}"       # noqa: E731
        cells = "".join(f"{show(m):>7} /{show(r):>4} " if (m, r) != (None, None)
                        else f"{'.':>13}" for m, r in zip(table["m"][g], table["r"][g]))
        out.append(f"  {g:<8}{cells}")
        off: list[tuple[str, float]] = []
        missing: dict[bool, list[str]] = {}
        for (name, *_), m, r in zip(spans, table["m"][g], table["r"][g]):
            if m is not None and r is not None and abs(m - r) >= 5:
                off.append((name, m - r))
            elif (m is None) != (r is None):
                missing.setdefault(m is None, []).append(name)
        if not same_form:
            # As with the spectrum: only what holds across the song.
            pairs = [m - r for m, r in zip(table["m"][g], table["r"][g])
                     if m is not None and r is not None]
            off, missing = [], {}
            if len(pairs) >= 4:
                pairs.sort()
                mid = pairs[len(pairs) // 2]
                agree = sum(1 for d in pairs if d * mid > 0 and abs(d) >= 3)
                if abs(mid) >= 4 and agree >= 0.6 * len(pairs):
                    off = [(f"{agree} of {len(pairs)} parts of the song", mid)]
        for sign, word in ((1, "louder"), (-1, "quieter")):
            where = [(n, d) for n, d in off if d * sign > 0]
            if where:
                lo, hi = min(abs(d) for _, d in where), max(abs(d) for _, d in where)
                amount = f"{hi:.0f}" if hi - lo < 1 else f"{lo:.0f}-{hi:.0f}"
                gains = [o.id for n in groups[g] for o in piece.get_voice(n).ops
                         if o.kind == "gain" and o.enabled]
                notes.append((hi + 2 * len(where) + 4,
                              f"the {g} {'is' if g in ('bass', 'rest') else 'are'} "
                              f"{amount} dB "
                              f"{word} against the rest of the "
                              f"band than the reference's in {', '.join(n for n, _ in where)}"
                              f" -- {g} here is {', '.join(groups[g]) or 'no voice'}"
                              + (f"; faders: {', '.join(gains[:6])}" if gains else ""), None))
        for absent, where in missing.items():
            notes.append((5.0 + len(where), (f"the reference has {g} in {', '.join(where)} "
                                             f"and the piece has none" if absent else
                                             f"the piece has {g} in {', '.join(where)} and "
                                             f"the reference has none"), None))
    # What each stem sounds like, over the stretches where it is playing: a
    # dull mix is a dull something, and this says which.
    out += ["", f"  each stem's own sound (piece / reference)"
                f"{'centre Hz':>22}{'above 4 kHz':>20}{'2-4 kHz':>18}{'under 100 Hz':>20}"]
    for g in ("drums", "bass", "vocals", "rest"):
        if g not in ref or g not in mine or not groups.get(g):
            continue
        cm, cr = _stem_sound(mine[g]), _stem_sound(ref[g])
        if not cm or not cr:
            continue
        out.append(f"  {g:<28}{cm['centroid']:13.0f} /{cr['centroid']:6.0f}"
                   f"{cm['above4k']:11.0f}% /{cr['above4k']:3.0f}%"
                   f"{cm['presence']:10.0f}% /{cr['presence']:3.0f}%"
                   f"{cm['below100']:11.0f}% /{cr['below100']:3.0f}%")
        for key, label in (("above4k", "above 4 kHz"), ("presence", "at 2-4 kHz")):
            a, b = max(cm[key], 0.05), max(cr[key], 0.05)
            ratio = 10 * math.log10(a / b)
            if abs(ratio) >= 5 and max(a, b) >= 1.0:
                tone = [o.id for n in groups[g] for o in piece.get_voice(n).ops
                        if o.kind in ("filter", "eq", "crush") and o.enabled]
                notes.append((abs(ratio) + 5,
                              f"the {g} carry {abs(ratio):.0f} dB "
                              f"{'more' if ratio > 0 else 'less'} of their own energy "
                              f"{label} than the reference's {g} ({a:.1f}% / {b:.1f}%) -- "
                              f"{', '.join(groups[g][:6])}"
                              + (f"; tone ops: {', '.join(tone[:6])}" if tone else
                                 "; no filter or eq on them"), None))
    # Louder drums, or longer, or more of them? Power cannot say. The level of
    # the hits themselves (against the bass's) and the share of the time the
    # kit is sounding can.
    if groups["drums"]:
        hm, hr = _stem_hits(mine["drums"], mine["bass"]), _stem_hits(ref["drums"], ref["bass"])
        if hm and hr:
            out += ["", f"  the drums' hits (piece / reference): level over the bass "
                        f"{hm['over_bass']:+.0f} / {hr['over_bass']:+.0f} dB, sounding "
                        f"{hm['occupancy']:.0f}% / {hr['occupancy']:.0f}% of the time, "
                        f"{hm['rate']:.1f} / {hr['rate']:.1f} hits a second"]
            d = hm["over_bass"] - hr["over_bass"]
            if abs(d) >= 4:
                gains = [o.id for n in groups["drums"] for o in piece.get_voice(n).ops
                         if o.kind == "gain" and o.enabled]
                notes.append((abs(d) + 6, f"each drum hit is {abs(d):.0f} dB "
                              f"{'louder' if d > 0 else 'quieter'} against the bass than the "
                              f"reference's ({hm['over_bass']:+.0f} / {hr['over_bass']:+.0f} "
                              f"dB)" + (f"; faders: {', '.join(gains[:4])}" if gains else ""),
                              None))
            if hr["occupancy"] > 0 and not 0.6 <= hm["occupancy"] / hr["occupancy"] <= 1.6:
                notes.append((5.0, f"the kit is sounding {hm['occupancy']:.0f}% of the time "
                                   f"where the reference's is {hr['occupancy']:.0f}%: that "
                                   f"is the writing or the decay, not a fader", None))
    if same_form and groups["drums"]:
        out += ["", "  drums on a sixteenth grid, two bars, each track against its own "
                    "loudest section (X loudest; the low band for the kick, the top band "
                    "for hats and cymbals)"]
        scale = {(who, lo): max((_grid_raw(x, piece, to_sec, first, first + sec.bars, lo, hi)
                                 .max() for sec, first, _ in piece.section_bounds()
                                 if sec.bars >= 4), default=0.0)
                 for who, x in (("m", mine["drums"]), ("r", ref["drums"]))
                 for lo, hi in ((30.0, 110.0), (6000.0, 14000.0))}
        for k, (sec, first, _) in enumerate(piece.section_bounds()):
            if sec.bars < 4:
                continue
            # A pattern read out of a stem that is all but silent there is the
            # separator's leakage, not a drummer.
            there_m = table["m"]["drums"][k] is not None
            there_r = table["r"]["drums"][k] is not None
            for band, lo, hi in (("kick", 30.0, 110.0), ("top", 6000.0, 14000.0)):
                m = _grid(mine["drums"], piece, to_sec, first, first + sec.bars, lo, hi,
                          scale[("m", lo)]) if there_m else ""
                r = _grid(ref["drums"], piece, to_sec, first, first + sec.bars, lo, hi,
                          scale[("r", lo)]) if there_r else ""
                if m or r:
                    out.append(f"  {sec.name[:9]:<10}{band:<5} piece {m or '(none)':<34} "
                               f"reference {r or '(none)'}")
    return out


# --------------------------------------------------------------------------
# one moment
# --------------------------------------------------------------------------

def at(piece: Piece, *, time: str | float | None = None, bar: str | int | None = None,
       score: str | None = None) -> str:
    """Everything about one moment: where it is in the form, the chord, and
    for each voice the notes sounding and the op that wrote them.

    A listener, a reference and a waveform all speak in minutes and seconds;
    the piece is written in bars and ops. This is the conversion, in both
    directions, down to the line to edit: ``time="1:28"`` or ``bar="41:3"``.
    ``score`` is the text of the piece's score file, if it has one: each op is
    then given with its line number there.
    """
    from .theory import pitch_name
    to_sec = audio._tick_seconds(piece)
    if (time is None) == (bar is None):
        raise ValueError("give one of time= ('1:28' or seconds) or bar= ('41' or '41:3')")
    if time is not None:
        if isinstance(time, str) and ":" in time:
            m, _, s = time.partition(":")
            seconds = int(m) * 60 + float(s)
        else:
            seconds = float(time)
        tick = min(_tick_at(piece, to_sec, seconds), max(0, piece.total_ticks - 1))
    else:
        tick = piece.tick_of(str(bar))
    seconds = to_sec(tick)
    b, beat = piece.position_of(tick)
    sec, first, _ = piece.section_at_bar(b)
    chord, key = piece.chord_at(tick)
    lines = {}
    if score:
        for no, text in enumerate(score.splitlines(), 1):
            m = re.match(r"\s+([\w.\-{}]+):\s", text)
            if m:
                lines[m.group(1)] = no
    r = render(piece)
    out = [f"{piece.name} at {int(seconds) // 60}:{seconds % 60:04.1f} = bar {b} beat "
           f"{float(beat):g}: section {sec.name!r} (its bar {b - first + 1} of {sec.bars}), "
           f"{chord.numeral if chord else 'no chord'} in {key.name}, "
           f"q={piece.tempo_of(sec)}, {sec.dynamic}"]
    quiet = True
    for v in piece.voices:
        mine = [n for n in r.notes if n.voice == v.name and n.start <= tick < n.end]
        soon = [n for n in r.notes if n.voice == v.name and tick < n.start <= tick + 480]
        if not mine and not soon:
            continue
        quiet = False
        what = " ".join(sorted({pitch_name(n.pitch) for n in mine})) if mine else \
            "(rests; enters within a beat)"
        if v.inst.percussive and mine:
            what = f"{len(mine)} drum stroke(s)"
        ops = []
        for op_id in dict.fromkeys(n.op for n in (mine or soon) if n.op):
            ops.append(f"{op_id} (line {lines[op_id]})" if op_id in lines else op_id)
        shaped = [o.id for o in v.ops if o.enabled and o.kind in
                  ("gain", "filter", "eq", "drive", "crush", "compress", "dynamics",
                   "duck", "cut") and _covers(piece, o, tick)]
        out.append(f"  {v.name:<10}{v.instrument:<18}{what:<24} from {', '.join(ops) or '?'}"
                   + (f"   shaped by {', '.join(shaped)}" if shaped else ""))
    if quiet:
        out.append("  nothing is sounding")
    return "\n".join(out)


def _covers(piece: Piece, op, tick: int) -> bool:
    lo = op.params.get("from")
    hi = op.params.get("until")
    return ((lo is None or piece.tick_of(lo) <= tick)
            and (hi is None or tick < piece.tick_of(hi)))
