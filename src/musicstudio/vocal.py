"""A singing voice, synthesized from nothing: no recordings, no samples.

It works the way a throat does, as far as that can be written down. A **source**
buzzes at the pitch of the note -- a pulse train with the spectrum of vocal
folds, brighter when sung louder -- and a **tract** shapes it: a handful of
resonances (formants) whose positions *are* the vowel. "Ah" is a first formant
near 850 Hz and a second near 1250; move them to 310 and 2750 and the same buzz
says "ee". Consonants are the moments the tract closes or hisses: silence and a
burst for ``t``, noise in a high band for ``s``, a hum through the nose for
``m``.

What makes it *sing* rather than speak on a pitch:

* **The vowel lands on the beat.** Consonants that open a syllable are sung
  ahead of the note, on time borrowed from the note before, exactly as a singer
  places them. Consonants that close it take the end of its own note.
* **Formants glide.** The tract moves from one shape to the next over a few
  hundredths of a second; those transitions carry as much of the consonant as
  the consonant does, and without them every syllable sounds pasted on.
* **Pitch is a line.** It slides into each new note, scoops slightly into the
  first one of a phrase, and vibrato arrives late on notes long enough to want
  it.
* **High notes retune the mouth.** When the pitch climbs past the first
  formant, sopranos open the vowel so the formant follows the pitch; otherwise
  the note loses its body. So does this.

The filter is applied in the frequency domain, frame by frame (5.8 ms), because
a filter whose resonances move cannot be a single convolution. Numpy only; one
phrase at a time. Everything random is seeded from the voice and the phrase.

This is a formant synthesizer, and sounds like one: clear vowels, intelligible
if you know the words, unmistakably synthetic. It is an instrument with a
character, not an imitation of a particular person.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass

import numpy as np

from .lyrics import DIPHTHONGS, VOWELS, Syllable

#: Output scale, set so a mezzo-forte "ah" is as loud as a mezzo-forte violin.
LEVEL = 1.0
SR = 44100
SIZE = 1024
HOP = 256
FPS = SR / HOP
CEILING = 14000.0


@dataclass(frozen=True)
class Singer:
    """A voice: the size of its tract and how it uses it."""

    #: Formant scale. Above 1 is a shorter tract: younger, brighter, smaller.
    tract: float = 1.0
    breath: float = 0.035           # aspiration noise under every vowel
    tilt: float = 1.0               # spectral slope of the source; lower is brighter
    vibrato: float = 32.0           # cents
    vibrato_rate: float = 5.7
    glide: float = 0.07             # seconds to slide between notes
    level: float = 1.0


SINGERS: dict[str, Singer] = {
    # Bright and light: a short tract, little breath, and the pitch of a
    # synthesized singer -- it steps to each note quickly and barely wavers.
    "singer": Singer(tract=1.14, breath=0.03, tilt=0.62, vibrato=11.0, glide=0.04),
    # The same voice sung the way a person would: slower slides, real vibrato.
    "singer_warm": Singer(tract=1.1, breath=0.045, tilt=0.8, vibrato=30.0, glide=0.075),
    # The same throat an octave of size bigger.
    "singer_low": Singer(tract=0.9, breath=0.04, tilt=0.8, vibrato=24.0,
                         vibrato_rate=5.3, glide=0.07, level=1.1),
    # More air than tone.
    "singer_breathy": Singer(tract=1.1, breath=0.14, tilt=1.05, vibrato=16.0,
                             level=1.1),
}


def is_singer(instrument: str) -> bool:
    return instrument in SINGERS


#: Formant targets ``(F1, F2, F3)`` in Hz for an adult woman's voice (the
#: English ones after Peterson & Barney, 1952). A singer's ``tract`` scales them.
FORMANTS: dict[str, tuple[float, float, float]] = {
    "a": (850, 1250, 2800), "i": (310, 2750, 3300), "u": (370, 1450, 2650),
    "e": (540, 2200, 2900), "o": (500, 900, 2750),
    "aa": (850, 1220, 2810), "ae": (860, 2050, 2850), "ah": (760, 1400, 2780),
    "ao": (590, 920, 2710), "eh": (610, 2330, 2990), "er": (500, 1640, 1960),
    "ih": (430, 2480, 3070), "iy": (310, 2790, 3310), "uh": (470, 1160, 2680),
    "uw": (370, 950, 2670),
    # voiced consonants are tract shapes too
    "m": (250, 1100, 2200), "n": (250, 1600, 2600), "ng": (250, 2100, 2800),
    "N": (250, 1500, 2600), "l": (360, 1150, 2750), "r": (420, 1150, 1550),
    "rr": (380, 1500, 2600), "w": (340, 800, 2400), "y": (290, 2600, 3200),
}
#: How open the mouth is: an "ah" is simply louder than an "oo".
OPENNESS = {"a": 1.0, "aa": 1.0, "ae": 1.0, "ah": 0.9, "eh": 0.9, "e": 0.9, "ao": 0.85,
            "o": 0.85, "er": 0.75, "ih": 0.75, "uh": 0.72, "iy": 0.66, "i": 0.66,
            "uw": 0.62, "u": 0.64}
BANDWIDTHS = (80.0, 100.0, 140.0, 220.0, 300.0)

#: Consonants: ``kind, seconds, voiced level, noise (centre Hz, width in
#: octaves, level)``. A stop's time is its closure; the burst follows.
CONSONANTS: dict[str, tuple] = {
    "p": ("stop", 0.055, 0.0, (900, 2.2, 0.45)),
    "t": ("stop", 0.050, 0.0, (4800, 1.3, 0.75)),
    "k": ("stop", 0.055, 0.0, (2300, 1.0, 0.70)),
    "b": ("stop", 0.045, 0.22, (700, 2.2, 0.25)),
    "d": ("stop", 0.040, 0.22, (4000, 1.4, 0.40)),
    "g": ("stop", 0.045, 0.22, (2200, 1.0, 0.38)),
    "q": ("stop", 0.060, 0.0, (2000, 2.0, 0.0)),
    "ch": ("affricate", 0.095, 0.0, (3400, 1.0, 0.70)),
    "jh": ("affricate", 0.080, 0.25, (3200, 1.0, 0.45)),
    "ts": ("affricate", 0.090, 0.0, (6500, 0.9, 0.65)),
    "s": ("fricative", 0.105, 0.0, (6800, 0.9, 0.62)),
    "z": ("fricative", 0.080, 0.45, (6500, 0.9, 0.36)),
    "sh": ("fricative", 0.105, 0.0, (3300, 1.0, 0.66)),
    "zh": ("fricative", 0.080, 0.45, (3200, 1.0, 0.38)),
    "f": ("fricative", 0.090, 0.0, (5200, 2.6, 0.22)),
    "v": ("fricative", 0.065, 0.50, (5000, 2.6, 0.12)),
    "th": ("fricative", 0.085, 0.0, (6500, 2.6, 0.17)),
    "dh": ("fricative", 0.050, 0.55, (6000, 2.6, 0.08)),
    "hh": ("aspirate", 0.070, 0.0, (0, 0, 0.40)),
    "m": ("nasal", 0.070, 0.42, None), "n": ("nasal", 0.065, 0.42, None),
    "ng": ("nasal", 0.070, 0.40, None), "N": ("nasal", 0.080, 0.45, None),
    "l": ("liquid", 0.060, 0.62, None), "r": ("liquid", 0.070, 0.62, None),
    "rr": ("liquid", 0.032, 0.34, None),
    "w": ("glide", 0.060, 0.62, None), "y": ("glide", 0.055, 0.62, None),
}
_SUSTAIN = {"nasal": 0.45, "liquid": 0.62}


def _seconds(ph: str) -> float:
    return CONSONANTS[ph][1] + (0.018 if CONSONANTS[ph][0] in ("stop", "affricate") else 0.0)


# --------------------------------------------------------------------------
# from notes to a timeline of sounds
# --------------------------------------------------------------------------

@dataclass
class Sung:
    """One note as the voice will sing it, in seconds."""

    start: float
    end: float
    pitch: float
    velocity: int
    onset: tuple[str, ...]
    nucleus: str
    coda: tuple[str, ...]
    #: Carries on from the note before with no new syllable.
    hold: bool = False
    #: ``word#index/count``: which syllable of which word, for a voice bank.
    word: str = ""


def plan(notes, to_sec) -> list[Sung]:
    """Attach syllables to notes and move codas to where they are sung.

    A melisma (``-``) keeps the previous vowel, and the consonants that end its
    syllable wait until the last note of it: "wa-ter - -" closes the "r" at
    the very end, not after the first note.
    """
    out: list[Sung] = []
    for n in sorted(notes, key=lambda n: (n.start, n.pitch)):
        syl = Syllable.from_json(n.sung) if n.sung else Syllable((), "aa", (), "")
        s = Sung(to_sec(n.start), to_sec(n.end), n.pitch + n.tune, n.velocity,
                 syl.onset, syl.nucleus, syl.coda, syl.hold, n.word)
        if s.hold and out:
            prev = out[-1]
            s.onset, s.nucleus, s.coda = (), _held(prev.nucleus), prev.coda
            prev.coda = ()
        elif s.hold:
            s.hold = False
        out.append(s)
    return out


def _held(nucleus: str) -> str:
    """What a diphthong sounds like once it has arrived: its second vowel."""
    return nucleus


def phrases(sung: list[Sung], gap: float = 0.3) -> list[list[Sung]]:
    out: list[list[Sung]] = []
    for s in sung:
        if not out or s.start - out[-1][-1].end > gap:
            out.append([])
        out[-1].append(s)
    return out


# --------------------------------------------------------------------------
# one phrase
# --------------------------------------------------------------------------

def _formants(ph: str, tract: float) -> tuple[float, ...]:
    f1, f2, f3 = FORMANTS[ph]
    return (f1 * tract, f2 * tract, f3 * tract, 3900.0 * tract, 4900.0 * tract)


def _smooth(x: np.ndarray, frames: int) -> np.ndarray:
    if frames <= 1 or len(x) < 3:
        return x
    k = np.hanning(frames + 2)[1:-1]
    k /= k.sum()
    pad = frames // 2
    return np.convolve(np.pad(x, (pad, pad), mode="edge"), k, mode="same")[pad:pad + len(x)]


def render_phrase(sung: list[Sung], singer: Singer, seed: int) -> tuple[np.ndarray, float]:
    """Synthesize one phrase. Returns ``(samples, start time in seconds)``.

    The phrase begins before its first note if that note opens on consonants.
    """
    rng = np.random.default_rng(seed)
    lead = sum(_seconds(p) for p in sung[0].onset) + 0.03
    t0 = max(0.0, sung[0].start - lead)
    total = sung[-1].end - t0 + 0.25
    count = int(total * FPS) + 8
    n = count * HOP + SIZE

    F = np.full((count, 5), np.nan)          # formant targets; NaN = whatever is nearby
    voiced = np.zeros(count)
    breath = np.zeros(count)
    fric = np.zeros(count)
    fric_c = np.full(count, 4000.0)
    fric_w = np.full(count, 1.0)
    lowpass = np.full(count, 20000.0)
    loud = np.zeros(count)

    def frames(a: float, b: float) -> slice:
        return slice(max(0, int((a - t0) * FPS)), max(0, min(count, int((b - t0) * FPS) + 1)))

    def consonant(ph: str, a: float, b: float, level: float) -> None:
        kind, _, voice, noise = CONSONANTS[ph]
        sl = frames(a, b)
        if sl.stop <= sl.start:
            return
        loud[sl] = np.maximum(loud[sl], level)
        if ph in FORMANTS:
            F[sl] = _formants(ph, singer.tract)
        if kind in ("nasal", "liquid", "glide"):
            voiced[sl] = voice
            if kind == "nasal":
                lowpass[sl] = 1100.0          # the mouth is shut; the nose is a lowpass
            return
        if kind == "aspirate":
            breath[sl] = noise[2]
            return
        if kind == "fricative":
            voiced[sl] = voice
            fric[sl] = noise[2]
            fric_c[sl], fric_w[sl] = noise[0], noise[1]
            if voice:
                lowpass[sl] = 2500.0
            return
        # Stops and affricates: silence (or a murmur), then the release.
        release = 0.018 if kind == "stop" else b - a - 0.035
        hold = frames(a, b - release)
        voiced[hold] = voice
        lowpass[hold] = 450.0
        burst = frames(b - release, b)
        fric[burst] = noise[2]
        fric_c[burst], fric_w[burst] = noise[0], noise[1]
        if not voice and noise[2]:
            breath[burst] = 0.2               # a puff of air on the release

    for i, s in enumerate(sung):
        level = (max(1, min(127, s.velocity)) / 127.0) ** 1.3
        nxt = sung[i + 1] if i + 1 < len(sung) else None
        joined = nxt is not None and nxt.start - s.end < 0.03
        on_next = sum(_seconds(p) for p in nxt.onset) if joined else 0.0
        coda = sum(_seconds(p) for p in s.coda)
        # The vowel keeps at least 45% of its note; consonants share the rest.
        room = (s.end - s.start) * 0.55
        squeeze = min(1.0, room / (on_next + coda)) if on_next + coda > 0 else 1.0
        v_end = s.end - (on_next + coda) * squeeze

        # Onset consonants, ending exactly on the note.
        on = sum(_seconds(p) for p in s.onset)
        prev = sung[i - 1] if i else None
        space = (s.start - t0) if prev is None else max(
            0.0, s.start - (prev.start + (prev.end - prev.start) * 0.45))
        k = min(1.0, space / on) if on > 0 else 1.0
        at = s.start - on * k
        for ph in s.onset:
            d = _seconds(ph) * k
            consonant(ph, at, at + d, level)
            at += d

        # The vowel (or the hum of a syllabic consonant).
        sl = frames(s.start, v_end)
        nucleus = s.nucleus
        if nucleus in DIPHTHONGS:
            first, second = DIPHTHONGS[nucleus]
            F[sl] = _formants(first, singer.tract)
            turn = max(s.start + (v_end - s.start) * 0.55, v_end - 0.14)
            F[frames(turn, v_end)] = _formants(second, singer.tract)
            openness = OPENNESS[first]
        elif nucleus in VOWELS:
            F[sl] = _formants(nucleus, singer.tract)
            openness = OPENNESS.get(nucleus, 0.8)
        else:
            F[sl] = _formants(nucleus, singer.tract)
            openness = _SUSTAIN.get(CONSONANTS[nucleus][0], 0.5)
            if CONSONANTS[nucleus][0] == "nasal":
                lowpass[sl] = 1100.0
        voiced[sl] = openness
        breath[sl] = np.maximum(breath[sl], singer.breath)
        loud[sl] = level

        # Coda consonants, inside the end of the note.
        at = v_end
        for ph in s.coda:
            d = _seconds(ph) * squeeze
            consonant(ph, at, at + d, level)
            at += d

    # Unspecified frames take the shape of their neighbours: a "t" has no
    # formants of its own, it is the gap between two that do.
    known = ~np.isnan(F[:, 0])
    if not known.any():
        return np.zeros(0), t0
    idx = np.arange(count)
    for j in range(5):
        F[:, j] = np.interp(idx, idx[known], F[known, j])
        F[:, j] = _smooth(F[:, j], 9)          # ~50 ms: the tract takes time to move
    voiced_s = _smooth(voiced, 4)
    breath_s = _smooth(breath, 4)
    fric_s = _smooth(fric, 2)
    loud_s = _smooth(loud, 5)
    lowpass_s = np.exp(_smooth(np.log(lowpass), 4))

    # -- pitch ----------------------------------------------------------------
    t = np.arange(n) / SR + t0
    cents = np.zeros(n)
    midi = np.full(n, sung[0].pitch, dtype=np.float64)
    for i, s in enumerate(sung):
        if i == 0:
            continue
        # A slide into each note, centred just ahead of it.
        x = np.clip((t - (s.start - 0.012)) / (singer.glide / 4.0), -40.0, 40.0)
        midi += (s.pitch - sung[i - 1].pitch) / (1.0 + np.exp(-x))
    cents -= 55.0 * np.exp(-np.maximum(t - sung[0].start, 0.0) / 0.05) * (t >= sung[0].start - 0.05)
    for s in sung:
        if s.end - s.start < 0.36 or s.nucleus not in VOWELS:
            continue
        rate = singer.vibrato_rate * rng.uniform(0.95, 1.05)
        rise = np.clip((t - s.start - 0.2) / 0.3, 0.0, 1.0) * (t < s.end)
        cents += singer.vibrato * rise * np.sin(2 * np.pi * rate * (t - s.start)
                                                + rng.uniform(0, 2 * np.pi))
    drift = np.interp(t, np.linspace(t[0], t[-1], max(4, int(total * 3))),
                      rng.normal(0.0, 5.0, max(4, int(total * 3))))
    f0 = 440.0 * 2.0 ** ((midi - 69.0) / 12.0 + (cents + drift) / 1200.0)

    # -- source ---------------------------------------------------------------
    from .synth import _osc, _table
    top = max(1, int(CEILING / float(f0.max())))
    harm = np.arange(1, top + 1, dtype=np.float64)
    dark = _table(harm ** -(singer.tilt + 0.9))
    bright = _table(harm ** -singer.tilt)
    cycles = np.cumsum(f0) / SR
    level_t = np.interp(np.arange(n), np.arange(count) * HOP + SIZE / 2, loud_s)
    source = _osc(dark, cycles)
    source += (_osc(bright, cycles) - source) * np.clip(level_t * 1.25, 0.0, 1.0)
    # Flutter and shimmer: no two cycles of a real voice are the same size.
    source *= 1.0 + 0.03 * np.interp(np.arange(n), np.arange(0, n, 64),
                                     rng.standard_normal(len(range(0, n, 64))))
    noise = rng.standard_normal(n)

    # -- tract, frame by frame ----------------------------------------------------
    f = np.fft.rfftfreq(SIZE, 1.0 / SR)
    f0_frame = f0[np.minimum(n - 1, np.arange(count) * HOP + SIZE // 2)]
    # Formant tuning: keep the first formant at or above the pitch.
    F[:, 0] = np.maximum(F[:, 0], f0_frame * 1.03)
    env = np.ones((count, len(f)))
    for j, bw in enumerate(BANDWIDTHS):
        fj = F[:, j][:, None]
        env *= fj ** 2 / np.sqrt((fj ** 2 - f[None, :] ** 2) ** 2 + (bw * (1 + j * 0.2) * f[None, :]) ** 2)
    env /= env.max(axis=1, keepdims=True)
    # A chain of ideal resonators has deeper valleys and a steeper top than a
    # real mouth, whose walls are soft and whose lips radiate the highs. Taking
    # a root of the response fills the valleys, and the tilt above 1.5 kHz is
    # the radiation. Without both the upper formants are present but too quiet
    # to tell "ee" from "oo", and there is no air above 4 kHz at all.
    env = env ** 0.72 * (1.0 + (f[None, :] / 1500.0) ** 2) ** 0.3
    env /= env.max(axis=1, keepdims=True)
    env /= 1.0 + (f[None, :] / lowpass_s[:, None]) ** 4
    window = np.sqrt(np.hanning(SIZE + 1)[:SIZE])

    def shape(signal: np.ndarray, gains: np.ndarray) -> np.ndarray:
        fr = np.lib.stride_tricks.sliding_window_view(signal, SIZE)[::HOP][:count] * window
        out_frames = np.fft.irfft(np.fft.rfft(fr, axis=1) * gains, SIZE, axis=1) * window
        out = np.zeros(n)
        for k in range(SIZE // HOP):               # overlap-add, four frames deep
            part = out_frames[k::SIZE // HOP]
            flat = part.reshape(-1)
            a = k * HOP
            out[a:a + len(flat)] += flat[:n - a]
        return out / 2.0                           # sqrt-hann at 75% overlap sums to 2

    air = f[None, :] / (f[None, :] + 1200.0)       # breath has no low end
    band = np.exp(-0.5 * (np.log2(np.maximum(f[None, :], 30.0) / fric_c[:, None])
                          / (fric_w[:, None] / 2.0)) ** 2)
    out = shape(source, env * (voiced_s * loud_s)[:, None])
    out += shape(noise, env * air * (breath_s * loud_s)[:, None] * 0.5)
    out += shape(rng.standard_normal(n), band * (fric_s * np.maximum(loud_s, 0.25))[:, None] * 0.35)
    return out * (LEVEL * singer.level), t0


# --------------------------------------------------------------------------
# a whole voice
# --------------------------------------------------------------------------

def voice_stems(piece, notes, to_sec, total: int, pans: dict[str, float]) -> dict[str, tuple]:
    """``{voice: (left, right)}`` for every singer in the piece."""
    out: dict[str, tuple] = {}
    for v in piece.voices:
        if v.muted or not is_singer(v.instrument) or v.engine == "soundfont":
            continue
        mine = [n for n in notes if n.voice == v.name and not n.percussive]
        if not mine:
            continue
        singer = SINGERS[v.instrument]
        mono = np.zeros(total)
        for group in phrases(plan(mine, to_sec)):
            seed = zlib.crc32(f"{v.name}|{group[0].start:.4f}|{group[0].pitch}".encode())
            sig, t0 = render_phrase(group, singer, seed)
            a = int(t0 * SR)
            k = min(len(sig), total - a)
            if k > 0:
                mono[a:a + k] += sig[:k]
        theta = (max(-1.0, min(1.0, pans.get(v.name, 0.0))) + 1.0) * math.pi / 4
        out[v.name] = (mono * math.cos(theta) * math.sqrt(2),
                       mono * math.sin(theta) * math.sqrt(2))
    return out
