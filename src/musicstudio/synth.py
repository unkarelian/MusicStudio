"""Instrument models: what makes a rendered note sound played rather than generated.

``audio.py`` on its own gives every note one fixed waveform under one ADSR
curve. That is a faithful description of a 1980s sound chip and of nothing
else, and it is why a correct orchestral score rendered that way still sounds
like a game cartridge. A real instrument differs from a static oscillator in a
handful of specific, nameable ways, and this module is those ways:

**The spectrum moves.** A trumpet's upper partials arrive after the note starts
and leave before it ends; a piano's die away many times faster than its
fundamental; everything is brighter when it is played louder. So a note here is
several band-limited tables crossfading over its lifetime, never one.

**The body does not transpose.** A violin's wood and a singer's mouth resonate
at fixed frequencies whatever note is played, so harmonics are shaped by
*formants* at absolute pitch. This, more than any waveform, is what lets an ear
say "oboe" -- and its absence is what makes a synthesized scale sound like one
sample being pitch-shifted.

**Onsets are noise.** Bow hair catching, breath before the tone speaks, a
hammer hitting a string: the first few milliseconds of most instruments are
not pitched at all, and they carry most of the identity.

**Nothing is exactly steady.** Vibrato starts late and wavers; pitch drifts by a
few cents; a section is many players who do not quite agree. And two slurred
notes are one gesture: the second glides out of the first instead of attacking.

**Struck and plucked things are inharmonic and decay.** Bells, bars and drums
are sums of partials at non-integer ratios, each with its own decay; stiff
piano strings stretch their overtones sharp.

All of it is numpy, and all of it is *timbre*. Which notes sound, when, how
long, how loud and where they sit is decided before this module is called and
is identical on the plain path -- an instrument model may not rearrange music.

Everything random is seeded from the note itself (voice, onset, pitch) through
``zlib.crc32``, so a render is the same bytes on every run and every machine.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field

import numpy as np

SR = 44100
TABLE = 4096
#: Partials above this are left out: nothing an orchestra plays has useful
#: energy there, and stopping short of Nyquist is what keeps vibrato from
#: sweeping a top partial through it.
CEILING = 15000.0

_tables: dict[tuple, np.ndarray] = {}
_noises: dict[tuple, np.ndarray] = {}
_hits: dict[tuple, np.ndarray] = {}
#: One fixed phase per harmonic number, shared by every table, so two tables of
#: the same note can be crossfaded without their partials cancelling.
_PHASES = np.random.default_rng(20240229).uniform(0.0, 2 * np.pi, TABLE // 2)


def _rng(*key) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32("|".join(map(str, key)).encode("utf-8")))


# --------------------------------------------------------------------------
# building blocks
# --------------------------------------------------------------------------

def _table(amps: np.ndarray, normalize: bool = True) -> np.ndarray:
    """One cycle holding the given harmonic amplitudes, with a guard sample."""
    spec = np.zeros(TABLE // 2 + 1, dtype=np.complex128)
    k = min(len(amps), TABLE // 2 - 1)
    spec[1:k + 1] = amps[:k] * np.exp(1j * _PHASES[:k]) * (TABLE / 2)
    tab = np.fft.irfft(spec, TABLE)
    if normalize:
        rms = float(np.sqrt(np.mean(tab ** 2))) or 1.0
        tab = tab / rms
    return np.append(tab, tab[0])


def _osc(tab: np.ndarray, cycles: np.ndarray) -> np.ndarray:
    pos = (cycles - np.floor(cycles)) * TABLE
    i = pos.astype(np.int64)
    frac = pos - i
    return tab[i] + (tab[i + 1] - tab[i]) * frac


def _harmonics(f0: float) -> np.ndarray:
    return np.arange(1, max(1, int(min(TABLE // 2 - 2, CEILING / f0))) + 1, dtype=np.float64)


def _body(f: np.ndarray, formants, lowpass: float, order: float = 4.0) -> np.ndarray:
    """A fixed spectral envelope: resonant bumps over a rolloff, in absolute Hz."""
    env = 1.0 / (1.0 + (f / lowpass) ** order)
    if formants:
        bump = np.zeros_like(f)
        for fc, width, gain in formants:
            bump += gain * np.exp(-0.5 * (np.log2(f / fc) / width) ** 2)
        env = env * (1.0 + bump)
    return env


def _noise(name: str, lo: float, hi: float, seconds: float = 2.0) -> np.ndarray:
    """Band-limited noise with soft edges, unit RMS, cached."""
    key = (name, lo, hi, seconds)
    if key not in _noises:
        n = int(seconds * SR)
        raw = _rng("noise", name).standard_normal(n)
        spec = np.fft.rfft(raw)
        f = np.fft.rfftfreq(n, 1 / SR)
        shape = 1.0 / (1.0 + (lo / np.maximum(f, 1.0)) ** 4) / (1.0 + (f / hi) ** 4)
        out = np.fft.irfft(spec * shape, n)
        _noises[key] = out / (float(np.sqrt(np.mean(out ** 2))) or 1.0)
    return _noises[key]


def _noise_slice(buf: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    if n >= len(buf):
        return np.resize(buf, n)
    at = int(rng.integers(0, len(buf) - n))
    return buf[at:at + n]


def _wander(t: np.ndarray, rng: np.random.Generator, rates=(0.6, 1.7, 3.1)) -> np.ndarray:
    """Slow, smooth, roughly unit-range wandering: a hand that is not a machine."""
    out = np.zeros_like(t)
    for r in rates:
        out += np.sin(2 * np.pi * r * rng.uniform(0.8, 1.25) * t + rng.uniform(0, 2 * np.pi))
    return out / len(rates)


# --------------------------------------------------------------------------
# model descriptions
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Sustained:
    """Anything a player holds: bowed strings, winds, brass, voices."""

    #: Spectral rolloff exponents (amplitude ~ 1/n^slope) at soft and loud.
    dark: float = 1.6
    bright: float = 1.0
    formants: tuple = ()
    lowpass: float = 5000.0
    lowpass_bright: float | None = None
    #: Level of even harmonics; a clarinet's cylindrical bore suppresses them.
    even: float = 1.0
    attack: float = 0.06
    release: float = 0.12
    #: Seconds for the upper partials to arrive after the note speaks.
    bloom: float = 0.03
    #: Level the tone settles to on a long note.
    settle: float = 0.9
    vib_rate: float = 5.5
    vib_depth: float = 0.0          # cents
    vib_delay: float = 0.18
    vib_am: float = 0.0
    scoop: float = 0.0              # cents below pitch at the onset
    drift: float = 2.0              # cents of slow wander
    glide: float = 0.03             # seconds to slide into a slurred note
    noise: float = 0.0              # steady breath / bow hiss, relative to tone
    chiff: float = 0.0              # extra noise at the onset
    noise_band: tuple[float, float] = (2000.0, 7000.0)
    unison: int = 1
    detune: float = 0.0             # cents, section spread
    spread: float = 0.0             # stereo width of the section
    tremolo: float = 0.0            # bowed tremolo depth
    level: float = 1.0
    send: float = 1.0


@dataclass(frozen=True)
class Plucked:
    """A string set going and left alone: harp, guitar, pizzicato, piano."""

    slope: float = 1.0
    #: Where along the string it is excited; sets which harmonics are missing.
    position: float = 0.2
    lowpass: float = 6000.0
    formants: tuple = ()
    #: Decay of the fundamental at middle C, and how it shortens with pitch.
    decay: float = 2.0
    decay_track: float = 0.5
    #: How much faster each higher band dies.
    damping: float = 0.5
    #: How much darker a soft note is.
    vel_tilt: float = 0.8
    release: float = 0.15
    click: float = 0.15
    click_band: tuple[float, float] = (900.0, 5000.0)
    stretch: float = 0.0            # piano-string inharmonicity
    strings: int = 1                # unison strings per note
    two_stage: float = 0.0          # weight of the fast initial decay
    thump: float = 0.0              # hammer / finger noise, low
    level: float = 1.0
    send: float = 1.0


@dataclass(frozen=True)
class Bell:
    """Bars, tines and membranes: a few inharmonic partials, each decaying."""

    #: ``(frequency ratio, amplitude, decay relative to the fundamental's)``.
    partials: tuple = ((1.0, 1.0, 1.0),)
    decay: float = 1.5
    ref: int = 72
    decay_track: float = 0.5
    ring: bool = True
    release: float = 0.2
    click: float = 0.1
    click_band: tuple[float, float] = (1500.0, 8000.0)
    tremolo: float = 0.0
    settle: float = 0.0             # cents sharp at the strike (timpani)
    thump: float = 0.0
    level: float = 1.0
    send: float = 1.0


@dataclass(frozen=True)
class Drum:
    kind: str = "snare"
    level: float = 1.0
    send: float = 0.6


def _strings(**kw) -> Sustained:
    base = dict(dark=1.55, bright=0.95, attack=0.075, release=0.13, bloom=0.04,
                settle=0.94, vib_depth=15.0, vib_am=0.05, drift=3.0, glide=0.035,
                noise=0.035, chiff=0.10, noise_band=(2500.0, 8000.0))
    base.update(kw)
    return Sustained(**base)


def _brass(**kw) -> Sustained:
    base = dict(dark=2.0, bright=0.75, attack=0.045, release=0.11, bloom=0.07,
                settle=0.86, vib_depth=4.0, vib_delay=0.35, vib_rate=5.0, scoop=14.0,
                drift=2.0, glide=0.02, noise=0.012, chiff=0.05,
                noise_band=(1500.0, 6000.0))
    base.update(kw)
    return Sustained(**base)


def _reed(**kw) -> Sustained:
    base = dict(dark=1.25, bright=0.7, attack=0.035, release=0.09, bloom=0.03,
                settle=0.92, vib_depth=6.0, vib_delay=0.25, vib_am=0.04, drift=2.0,
                glide=0.015, noise=0.02, chiff=0.08, noise_band=(2000.0, 7000.0))
    base.update(kw)
    return Sustained(**base)


#: Formants are ``(centre Hz, width in octaves, gain)``. The numbers are the
#: commonly measured resonance regions for each instrument, not tuned to taste:
#: the violin's air and wood modes and its bridge hill, the oboe's two nasal
#: peaks, the horn's low single one.
MODELS: dict[str, Sustained | Plucked | Bell | Drum] = {
    # -- bowed strings -----------------------------------------------------
    "violin": _strings(formants=((290, 0.22, 1.6), (520, 0.2, 1.3), (2700, 0.45, 2.4)),
                       lowpass=6000, vib_rate=5.9),
    "viola": _strings(formants=((230, 0.25, 1.6), (400, 0.2, 1.2), (1700, 0.5, 1.8)),
                      lowpass=4800, vib_rate=5.6, vib_depth=14.0, attack=0.08),
    "cello": _strings(formants=((180, 0.3, 1.6), (300, 0.22, 1.3), (620, 0.3, 1.0),
                                (1500, 0.5, 1.4)),
                      lowpass=3800, vib_rate=5.3, vib_depth=14.0, attack=0.085,
                      release=0.16),
    "contrabass": _strings(formants=((100, 0.35, 1.5), (210, 0.3, 1.2), (480, 0.35, 0.9)),
                           lowpass=2200, vib_rate=4.9, vib_depth=7.0, attack=0.1,
                           release=0.2, send=0.6, level=0.95),
    "strings": _strings(formants=((280, 0.3, 1.2), (480, 0.3, 1.0), (2400, 0.6, 1.5)),
                        lowpass=4600, dark=1.7, bright=1.1, attack=0.2, release=0.32,
                        vib_depth=10.0, unison=5, detune=9.0, spread=0.3, glide=0.0,
                        noise=0.02, chiff=0.03, level=0.72),
    "tremolo_strings": _strings(formants=((280, 0.3, 1.2), (480, 0.3, 1.0), (2400, 0.6, 1.5)),
                                lowpass=5200, attack=0.12, release=0.25, vib_depth=5.0,
                                unison=5, detune=9.0, spread=0.3, glide=0.0, tremolo=0.7,
                                noise=0.03, level=0.8),
    # -- woodwinds ---------------------------------------------------------
    "flute": Sustained(dark=2.9, bright=1.9, lowpass=6500, attack=0.055, release=0.1,
                       bloom=0.03, settle=0.93, vib_rate=5.2, vib_depth=9.0,
                       vib_delay=0.2, vib_am=0.12, drift=2.5, glide=0.015, noise=0.07,
                       chiff=0.3, noise_band=(1800.0, 9000.0), level=1.3),
    "piccolo": Sustained(dark=3.2, bright=2.2, lowpass=9000, attack=0.04, release=0.08,
                         vib_rate=5.5, vib_depth=7.0, vib_am=0.1, noise=0.06, chiff=0.3,
                         noise_band=(3000.0, 11000.0), glide=0.012, level=0.8),
    "oboe": _reed(formants=((1120, 0.22, 3.2), (2900, 0.28, 1.6)), lowpass=6500,
                  dark=1.0, bright=0.55, level=0.9),
    "english_horn": _reed(formants=((930, 0.25, 3.0), (2300, 0.3, 1.2)), lowpass=5000,
                          dark=1.15, bright=0.7, attack=0.045),
    "clarinet": _reed(formants=((1500, 0.6, 0.7),), lowpass=5200, even=0.12, dark=1.5,
                      bright=0.95, vib_depth=2.0, vib_am=0.0, attack=0.045, noise=0.015,
                      level=1.15),
    "bassoon": _reed(formants=((480, 0.3, 3.0), (1150, 0.3, 1.1)), lowpass=3400,
                     dark=1.3, bright=0.8, attack=0.05, release=0.11, vib_depth=5.0),
    # -- brass -------------------------------------------------------------
    "horn": _brass(formants=((340, 0.4, 2.0), (800, 0.4, 0.7)), lowpass=2000,
                   lowpass_bright=4200, dark=2.2, bright=1.05, attack=0.065, bloom=0.1,
                   scoop=10.0, vib_depth=2.5, release=0.14),
    "trumpet": _brass(formants=((1250, 0.4, 2.4), (2500, 0.4, 1.2)), lowpass=3600,
                      lowpass_bright=9000, dark=1.7, bright=0.6, attack=0.035,
                      bloom=0.05, vib_depth=7.0, level=0.9),
    "trombone": _brass(formants=((520, 0.35, 2.2), (1500, 0.4, 1.0)), lowpass=2600,
                       lowpass_bright=6500, dark=1.9, bright=0.7, attack=0.05),
    "tuba": _brass(formants=((230, 0.4, 2.0), (450, 0.4, 1.0)), lowpass=1300,
                   lowpass_bright=3000, dark=2.3, bright=1.15, attack=0.075, bloom=0.12,
                   scoop=8.0, vib_depth=0.0, release=0.16, send=0.6, level=1.15),
    # -- voices and sustained keyboards -----------------------------------
    "choir": Sustained(formants=((700, 0.2, 4.0), (1150, 0.18, 3.0), (2750, 0.2, 1.6)),
                       lowpass=5000, dark=1.9, bright=1.3, attack=0.22, release=0.35,
                       bloom=0.1, settle=0.95, vib_rate=5.3, vib_depth=16.0,
                       vib_delay=0.25, vib_am=0.05, drift=5.0, glide=0.0, noise=0.03,
                       chiff=0.02, noise_band=(1500.0, 6000.0), unison=6, detune=13.0,
                       spread=0.35, level=0.8),
    "organ": Sustained(dark=1.9, bright=1.5, lowpass=6000, attack=0.03, release=0.09,
                       bloom=0.01, settle=1.0, drift=0.5, glide=0.0, noise=0.012,
                       chiff=0.12, noise_band=(800.0, 5000.0), unison=2, detune=2.5,
                       spread=0.15, level=0.8),
    "synth_pad": Sustained(dark=1.6, bright=1.1, lowpass=3200, attack=0.4, release=0.6,
                           bloom=0.3, settle=1.0, vib_depth=4.0, drift=4.0, glide=0.0,
                           unison=4, detune=11.0, spread=0.4, level=0.8),
    # -- plucked and hammered strings -------------------------------------
    "harp": Plucked(slope=1.25, position=0.38, lowpass=5200, decay=2.4, decay_track=0.55,
                    damping=0.55, vel_tilt=0.7, release=0.45, click=0.10,
                    click_band=(600.0, 3500.0), thump=0.05, level=0.85),
    "guitar": Plucked(slope=1.05, position=0.16, lowpass=5500,
                      formants=((110, 0.35, 1.2), (210, 0.3, 1.0)), decay=1.9,
                      decay_track=0.5, damping=0.6, release=0.2, click=0.16),
    "pizz_strings": Plucked(slope=1.3, position=0.22, lowpass=3800,
                            formants=((280, 0.3, 1.4), (480, 0.25, 1.0)), decay=0.42,
                            decay_track=0.35, damping=1.2, release=0.12, click=0.2,
                            click_band=(500.0, 3000.0), thump=0.12),
    "harpsichord": Plucked(slope=0.75, position=0.09, lowpass=8000, decay=1.5,
                           decay_track=0.4, damping=0.22, vel_tilt=0.15, release=0.07,
                           click=0.35, click_band=(2000.0, 9000.0)),
    "piano": Plucked(slope=1.0, position=0.121, lowpass=6500,
                     formants=((220, 0.6, 0.5), (1900, 0.8, 0.4)), decay=3.4,
                     decay_track=0.55, damping=0.3, vel_tilt=1.5, release=0.14,
                     click=0.0, stretch=1.0, strings=2, two_stage=0.55, thump=0.22,
                     level=0.95),
    # -- bars, tines and skins --------------------------------------------
    "celesta": Bell(partials=((1, 1, 1), (2.0, 0.28, 0.55), (3.0, 0.1, 0.35),
                              (4.2, 0.05, 0.2)),
                    decay=1.3, ref=84, ring=False, release=0.3, click=0.06),
    "glockenspiel": Bell(partials=((1, 1, 1), (2.76, 0.42, 0.5), (5.4, 0.22, 0.3),
                                   (8.93, 0.1, 0.18)),
                         decay=1.9, ref=91, click=0.12, level=0.8),
    "music_box": Bell(partials=((1, 1, 1), (2.0, 0.2, 0.5), (3.01, 0.12, 0.4),
                                (6.27, 0.18, 0.14)),
                      decay=1.2, ref=84, click=0.2, click_band=(3000.0, 10000.0),
                      level=0.85),
    "vibraphone": Bell(partials=((1, 1, 1), (4.0, 0.3, 0.25), (10.0, 0.07, 0.08)),
                       decay=3.2, ref=65, decay_track=0.4, tremolo=0.22, click=0.06,
                       click_band=(800.0, 4000.0)),
    "marimba": Bell(partials=((1, 1, 1), (4.0, 0.28, 0.14), (9.2, 0.07, 0.05)),
                    decay=0.55, ref=60, decay_track=0.45, click=0.14,
                    click_band=(400.0, 2500.0), thump=0.1),
    "rhodes": Bell(partials=((1, 1, 1), (2.0, 0.26, 0.7), (3.0, 0.08, 0.5),
                             (14.2, 0.1, 0.05)),
                   decay=2.4, ref=60, decay_track=0.45, ring=False, release=0.18,
                   click=0.03, tremolo=0.06),
    "timpani": Bell(partials=((1, 1, 1), (1.5, 0.6, 0.8), (1.99, 0.36, 0.6),
                              (2.44, 0.2, 0.42), (2.89, 0.12, 0.3)),
                    decay=1.5, ref=45, decay_track=0.3, settle=22.0, thump=0.6,
                    click=0.0, level=1.5, send=0.9),
    # -- untuned percussion ------------------------------------------------
    "kick": Drum("kick", level=1.5, send=0.25),
    "snare": Drum("snare", level=1.0),
    "hat": Drum("hat", level=0.55, send=0.4),
    "ride": Drum("ride", level=0.6),
    "crash": Drum("crash", level=1.3, send=0.8),
    "taiko": Drum("taiko", level=1.7, send=0.8),
    "tambourine": Drum("tambourine", level=0.6),
}

#: Base amplitude for a unit-RMS table, set so a mezzo-forte note sits where the
#: plain oscillator path puts it -- switching models on must not remix a piece.
LEVEL = 0.36


def has_model(instrument: str) -> bool:
    return instrument in MODELS


def send_of(instrument: str) -> float:
    """How much of this instrument goes to the room. Low end is kept drier."""
    m = MODELS.get(instrument)
    return m.send if m is not None else 1.0


# --------------------------------------------------------------------------
# per-note context
# --------------------------------------------------------------------------

@dataclass
class NoteCtx:
    """Everything a model needs to play one note, already in seconds."""

    instrument: str
    voice: str
    pitch: int
    start: float
    dur: float
    velocity: int
    #: Pitch of the note this one is slurred from, if any.
    slur_from: int | None = None
    #: Whether the next note takes over without a gap.
    slur_out: bool = False
    key: tuple = field(default_factory=tuple)

    @property
    def vel(self) -> float:
        return max(1, min(127, self.velocity)) / 127.0

    @property
    def freq(self) -> float:
        return 440.0 * 2 ** ((self.pitch - 69) / 12.0)


def slur_links(notes, to_sec) -> dict[int, tuple[int | None, bool]]:
    """Which notes are joined: ``id(note) -> (pitch slurred from, slurs onward)``.

    Two notes are one gesture when the first is marked ``slur`` and the second
    begins where it ends, give or take the slack a humanized performance has.
    In a chordal voice each note is joined to the nearest pitch that is ending,
    so a held chord changing under one bow does not re-attack either.
    """
    out: dict[int, tuple[int | None, bool]] = {}
    by_voice: dict[str, list] = {}
    for n in notes:
        if not n.percussive:
            by_voice.setdefault(n.voice, []).append(n)
    for group in by_voice.values():
        group.sort(key=lambda n: (n.start, n.pitch))
        ending = [n for n in group if n.slur]
        j0 = 0
        for n in group:
            t0 = to_sec(n.start)
            best = None
            while j0 < len(ending) and to_sec(ending[j0].end) < t0 - 0.5:
                j0 += 1
            for p in ending[j0:]:
                if p.start >= n.start:
                    break
                gap = t0 - to_sec(p.end)
                if -0.12 <= gap <= 0.035 and p is not n:
                    if best is None or abs(p.pitch - n.pitch) < abs(best.pitch - n.pitch):
                        best = p
            if best is not None:
                frm, onward = out.get(id(n), (None, False))
                out[id(n)] = (best.pitch, onward)
                frm, _ = out.get(id(best), (None, False))
                out[id(best)] = (frm, True)
    return out


# --------------------------------------------------------------------------
# the models
# --------------------------------------------------------------------------

def render_note(ctx: NoteCtx, limit: int) -> list[tuple[np.ndarray, float]]:
    """Play one note: a list of ``(samples, pan offset)`` layers.

    ``limit`` is how many samples remain in the output buffer. Layers are
    returned separately so a section's players can be spread across the stage.
    """
    model = MODELS[ctx.instrument]
    if isinstance(model, Sustained):
        return _sustained(ctx, model, limit)
    if isinstance(model, Plucked):
        return [(_plucked(ctx, model, limit), 0.0)]
    if isinstance(model, Bell):
        return [(_bell(ctx, model, limit), 0.0)]
    return [(_drum(ctx, model, limit), 0.0)]


def _amp(ctx: NoteCtx, level: float) -> float:
    return LEVEL * level * ctx.vel ** 1.3


def _sustained_tables(name: str, m: Sustained, pitch: int, f0: float):
    key = ("sus", name, pitch)
    if key not in _tables:
        n = _harmonics(f0)
        f = n * f0
        even = np.ones_like(n)
        if m.even != 1.0:
            # The clarinet's missing even harmonics come back as it goes up.
            lift = min(1.0, m.even + max(0.0, (pitch - 62) / 30.0))
            even[1::2] = lift
        dark = n ** -m.dark * even * _body(f, m.formants, m.lowpass)
        bright = n ** -m.bright * even * _body(f, m.formants, m.lowpass_bright or m.lowpass)
        _tables[key] = (_table(dark), _table(bright))
    return _tables[key]


def _sustained(ctx: NoteCtx, m: Sustained, limit: int) -> list[tuple[np.ndarray, float]]:
    legato_in = ctx.slur_from is not None
    release = 0.07 if ctx.slur_out else m.release
    n = min(int((ctx.dur + release) * SR), limit)
    if n <= 8:
        return []
    t = np.arange(n) / SR
    v = ctx.vel
    f0 = ctx.freq
    dark, bright = _sustained_tables(ctx.instrument, m, ctx.pitch, f0)

    # Amplitude: a rounded attack (faster when louder), a settle, a release.
    att = 0.045 if legato_in else m.attack * (1.3 - 0.6 * v)
    att = max(0.004, min(att, ctx.dur * 0.6))
    env = np.ones(n)
    k = min(n, int(att * SR))
    if k > 1:
        env[:k] = 0.5 - 0.5 * np.cos(np.pi * np.arange(k) / k)
    env *= m.settle + (1.0 - m.settle) * np.exp(-t / 0.4)
    r0 = min(n, int(ctx.dur * SR))
    if n > r0:
        rel = 1.0 - np.arange(n - r0) / max(1, n - r0)
        env[r0:] *= rel * rel
    # Upper partials arrive late and leave early.
    bloom = (1.0 - np.exp(-t / max(0.005, m.bloom))) * env
    mix = np.clip(v ** 1.4 * 1.15 * bloom, 0.0, 1.0)

    layers: list[tuple[np.ndarray, float]] = []
    count = max(1, m.unison)
    for u in range(count):
        rng = _rng(*ctx.key, u)
        cents = m.drift * _wander(t, rng)
        if count > 1:
            cents += m.detune * (2 * u / (count - 1) - 1) * rng.uniform(0.7, 1.0)
        vib = None
        if m.vib_depth and ctx.dur > 0.3:
            rate = m.vib_rate * rng.uniform(0.93, 1.07)
            depth = m.vib_depth * (0.55 + 0.6 * v) * rng.uniform(0.8, 1.15)
            fade = np.clip((t - m.vib_delay * rng.uniform(0.8, 1.3)) / 0.45, 0.0, 1.0)
            vib = fade * np.sin(2 * np.pi * rate * t + rng.uniform(0, 2 * np.pi)
                                + 0.6 * _wander(t, rng, (0.4, 0.9)))
            cents = cents + depth * vib
        if legato_in and m.glide:
            cents = cents + (ctx.slur_from - ctx.pitch) * 100.0 * np.exp(-t / (m.glide / 2.5))
        elif m.scoop:
            cents = cents - m.scoop * (0.5 + v) * np.exp(-t / 0.035)
        cycles = np.cumsum(f0 * 2.0 ** (cents / 1200.0)) / SR + rng.uniform(0, 1)
        sig = _osc(dark, cycles)
        sig += (_osc(bright, cycles) - sig) * mix
        amp = env.copy()
        if vib is not None and m.vib_am:
            amp *= 1.0 + m.vib_am * vib
        if m.tremolo:
            trem = np.sin(2 * np.pi * rng.uniform(10.5, 13.0) * t + rng.uniform(0, 2 * np.pi))
            amp *= 1.0 - m.tremolo * (0.5 + 0.5 * trem)
        amp *= 1.0 + 0.04 * _wander(t, rng, (2.3, 5.1, 7.7))
        sig *= amp
        if m.noise or m.chiff:
            hiss = _noise_slice(_noise(ctx.instrument, *m.noise_band), n, rng)
            onset = 0.0 if legato_in else m.chiff
            sig += hiss * env * (m.noise + onset * np.exp(-t / 0.045)) * (0.6 + 0.6 * v)
        pan = m.spread * (2 * u / (count - 1) - 1) if count > 1 else 0.0
        layers.append((sig * (_amp(ctx, m.level) / math.sqrt(count)), pan))
    return layers


_BANDS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 40, 100000)


def _plucked_tables(name: str, m: Plucked, pitch: int, f0: float, bucket: int):
    """Band tables for a decaying string: ``[(table, mean harmonic, weight)]``."""
    key = ("plk", name, pitch, bucket)
    if key not in _tables:
        n = _harmonics(f0)
        f = n * f0
        v = (bucket + 0.5) / 4.0
        comb = 0.25 + 0.75 * np.abs(np.sin(np.pi * n * m.position))
        amps = n ** -(m.slope + m.vel_tilt * (1.0 - v)) * comb * _body(f, m.formants, m.lowpass)
        # A soundboard cannot radiate a fundamental far below its own size.
        amps *= f / (f + 55.0)
        total = float(np.sqrt(np.sum(amps ** 2) / 2)) or 1.0
        bands = []
        for lo, hi in zip(_BANDS, _BANDS[1:]):
            sel = (n >= lo) & (n < hi)
            if not sel.any():
                break
            part = np.where(sel, amps, 0.0) / total
            mean = float(np.sum(n[sel] * part[sel] ** 2) / max(1e-12, np.sum(part[sel] ** 2)))
            bands.append((_table(part, normalize=False), mean))
        _tables[key] = bands
    return _tables[key]


def _plucked(ctx: NoteCtx, m: Plucked, limit: int) -> np.ndarray:
    v = ctx.vel
    f0 = ctx.freq
    release = m.release * (1.6 if ctx.pitch < 48 else 1.0)
    n = min(int((ctx.dur + release) * SR), limit)
    if n <= 8:
        return np.zeros(0)
    rng = _rng(*ctx.key)
    t = np.arange(n) / SR
    base = m.decay * 2.0 ** (-(ctx.pitch - 60) / 12.0 * m.decay_track)
    # Piano strings are stiff, so their overtones run sharp: f_n = n f0 sqrt(1 + B n^2).
    stiff = m.stretch * 1.2e-4 * 2.0 ** (max(0, ctx.pitch - 40) / 12.0 * 0.95)
    out = np.zeros(n)
    bands = _plucked_tables(ctx.instrument, m, ctx.pitch, f0, min(3, int(v * 4)))
    for b, (tab, mean) in enumerate(bands):
        rate = (1.0 + m.damping * (mean - 1.0)) / base
        # No point computing a band after it has fallen 70 dB.
        k = min(n, int(8.0 / rate * SR) + 1)
        tb = t[:k]
        env = np.exp(-rate * tb)
        if m.two_stage:
            env = m.two_stage * np.exp(-3.5 * rate * tb) + (1 - m.two_stage) * env
        ratio = math.sqrt(1.0 + stiff * mean * mean)
        strings = m.strings if (m.strings > 1 and b < 4) else 1
        part = np.zeros(k)
        for s in range(strings):
            cents = 0.0 if strings == 1 else (s - (strings - 1) / 2) * rng.uniform(1.2, 2.4)
            part += _osc(tab, f0 * ratio * 2 ** (cents / 1200.0) * tb + rng.uniform(0, 1))
        out[:k] += part * env / strings
    # The attack is a couple of milliseconds, not zero: an instant onset clicks.
    k = min(n, int(0.0018 * SR))
    out[:k] *= np.arange(k) / k
    if m.click:
        c = min(n, int(0.03 * SR))
        out[:c] += (_noise_slice(_noise(ctx.instrument + ".click", *m.click_band), c, rng)
                    * np.exp(-t[:c] / 0.004) * m.click * (0.3 + v))
    if m.thump:
        c = min(n, int(0.12 * SR))
        out[:c] += (_noise_slice(_noise(ctx.instrument + ".thump", 60.0, 900.0), c, rng)
                    * np.exp(-t[:c] / 0.018) * m.thump * v * v * 2.0)
    r0 = min(n, int(ctx.dur * SR))
    if n > r0:
        out[r0:] *= np.exp(-np.arange(n - r0) / SR / (release / 4.5))
    return out * _amp(ctx, m.level) * 1.05


def _bell(ctx: NoteCtx, m: Bell, limit: int) -> np.ndarray:
    v = ctx.vel
    f0 = ctx.freq
    base = m.decay * 2.0 ** (-(ctx.pitch - m.ref) / 12.0 * m.decay_track)
    ring = base * 5.0 if m.ring else ctx.dur + m.release
    n = min(int(max(ctx.dur + 0.05, ring) * SR), limit)
    if n <= 8:
        return np.zeros(0)
    rng = _rng(*ctx.key)
    t = np.arange(n) / SR
    out = np.zeros(n)
    norm = math.sqrt(sum(a * a for _, a, _ in m.partials) / 2) or 1.0
    bend = 2.0 ** (m.settle * np.exp(-t / 0.05) / 1200.0) if m.settle else None
    for i, (ratio, amp, life) in enumerate(m.partials):
        f = f0 * ratio
        if f > CEILING:
            continue
        k = min(n, int(8.0 * base * life * SR) + 1)
        phase = (np.cumsum(f * bend[:k]) / SR if bend is not None else f * t[:k])
        # A soft stroke excites the fundamental and little else.
        out[:k] += (amp * v ** (0.45 * i) / norm * np.exp(-t[:k] / (base * life))
                    * np.sin(2 * np.pi * (phase + rng.uniform(0, 1))))
    k = min(n, int(0.0012 * SR))
    out[:k] *= np.arange(k) / k
    if m.tremolo:
        out *= 1.0 - m.tremolo * (0.5 + 0.5 * np.sin(2 * np.pi * 4.6 * t))
    if m.click:
        c = min(n, int(0.025 * SR))
        out[:c] += (_noise_slice(_noise(ctx.instrument + ".click", *m.click_band), c, rng)
                    * np.exp(-t[:c] / 0.003) * m.click * (0.3 + v))
    if m.thump:
        c = min(n, int(0.2 * SR))
        out[:c] += (_noise_slice(_noise(ctx.instrument + ".thump", 50.0, 500.0), c, rng)
                    * np.exp(-t[:c] / 0.03) * m.thump * v)
    if not m.ring:
        r0 = min(n, int(ctx.dur * SR))
        if n > r0:
            out[r0:] *= np.exp(-np.arange(n - r0) / SR / (m.release / 4.5))
    return out * _amp(ctx, m.level) * 1.0


def _hit(kind: str, variant: int) -> np.ndarray:
    """One drum stroke at unit level, cached. Two variants, so repeated hits
    are not the same sample twice -- the 'machine gun' that gives loops away."""
    key = (kind, variant)
    if key in _hits:
        return _hits[key]
    rng = _rng("drum", kind, variant)

    def noise(seconds, lo, hi):
        n = int(seconds * SR)
        spec = np.fft.rfft(rng.standard_normal(n))
        f = np.fft.rfftfreq(n, 1 / SR)
        shape = 1.0 / (1.0 + (lo / np.maximum(f, 1.0)) ** 4) / (1.0 + (f / hi) ** 4)
        out = np.fft.irfft(spec * shape, n)
        return out / (float(np.sqrt(np.mean(out ** 2))) or 1.0)

    def sweep(seconds, f_start, f_end, tau):
        tt = np.arange(int(seconds * SR)) / SR
        f = f_end + (f_start - f_end) * np.exp(-tt / tau)
        return np.sin(2 * np.pi * np.cumsum(f) / SR), tt

    if kind == "kick":
        body, tt = sweep(0.5, 150.0, 48.0, 0.035)
        out = body * np.exp(-tt / 0.16)
        c = int(0.02 * SR)
        out[:c] += noise(0.02, 800.0, 5000.0) * np.exp(-tt[:c] / 0.003) * 0.35
    elif kind == "taiko":
        body, tt = sweep(1.4, 120.0, 62.0, 0.06)
        second, _ = sweep(1.4, 190.0, 99.0, 0.06)
        out = body * np.exp(-tt / 0.42) + 0.35 * second * np.exp(-tt / 0.2)
        c = int(0.15 * SR)
        out[:c] += noise(0.15, 150.0, 1800.0) * np.exp(-tt[:c] / 0.022) * 0.7
    elif kind == "snare":
        tt = np.arange(int(0.4 * SR)) / SR
        det = rng.uniform(0.98, 1.02)
        out = (np.sin(2 * np.pi * 186.0 * det * tt) + 0.6 * np.sin(2 * np.pi * 332.0 * det * tt)) \
            * np.exp(-tt / 0.055) * 0.7
        out += noise(0.4, 1200.0, 9500.0) * np.exp(-tt / 0.095) * 0.75
    elif kind in ("hat", "tambourine"):
        seconds = 0.14 if kind == "hat" else 0.35
        tt = np.arange(int(seconds * SR)) / SR
        out = noise(seconds, 6500.0, 14000.0) * np.exp(-tt / (0.028 if kind == "hat" else 0.07))
        if kind == "tambourine":
            # Jingles settle after the hand does: a few late, smaller rattles.
            for delay in (0.022, 0.05, 0.085):
                d = int(delay * rng.uniform(0.85, 1.15) * SR)
                out[d:] += 0.45 * noise(seconds, 7000.0, 13000.0)[:len(out) - d] \
                    * np.exp(-tt[:len(out) - d] / 0.045)
    else:                                           # ride, crash
        seconds = 1.6 if kind == "ride" else 2.4
        tt = np.arange(int(seconds * SR)) / SR
        # Cymbals are dozens of inharmonic modes; a cluster of detuned partials
        # under shaped noise is the cheapest thing that does not sound like hiss.
        out = np.zeros(len(tt))
        modes = rng.uniform(2800.0, 9500.0, 14) if kind == "ride" else rng.uniform(1800.0, 11000.0, 22)
        for fm in modes:
            out += np.sin(2 * np.pi * fm * tt + rng.uniform(0, 6.28)) \
                * np.exp(-tt / rng.uniform(0.25, 0.9 if kind == "ride" else 1.3))
        out /= math.sqrt(len(modes))
        if kind == "ride":
            out += 1.2 * noise(seconds, 5000.0, 12000.0) * np.exp(-tt / 0.3)
            out[:int(0.03 * SR)] *= 1.8
        else:
            out = 0.6 * out + 1.6 * noise(seconds, 2500.0, 12000.0) * np.exp(-tt / 0.55)
    k = min(len(out), 32)
    out[:k] *= np.arange(k) / k
    peak = float(np.abs(out).max()) or 1.0
    _hits[key] = out / peak
    return _hits[key]


def _drum(ctx: NoteCtx, m: Drum, limit: int) -> np.ndarray:
    rng = _rng(*ctx.key)
    hit = _hit(m.kind, int(rng.integers(0, 2)))
    n = min(len(hit), limit)
    if n <= 8:
        return np.zeros(0)
    v = ctx.vel
    out = hit[:n].copy()
    # A soft stroke is duller as well as quieter: fade the first millisecond in
    # harder, which takes the edge off without a filter.
    if v < 0.6:
        k = min(n, int((0.6 - v) * 0.006 * SR) + 1)
        out[:k] *= np.linspace(0.0, 1.0, k) ** 2
    return out * (LEVEL * m.level * 1.6 * v ** 1.5 * rng.uniform(0.93, 1.05))
