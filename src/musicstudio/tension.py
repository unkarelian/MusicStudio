"""Where the piece pulls and where it lets go: a tension curve from the score.

``squint`` shows how much is happening. It cannot show whether what is
happening *leans* anywhere -- and a piece can be dense, loud and high for
sixteen bars while sitting on the tonic the whole time, going nowhere. This
module estimates the two things a listener tracks without being asked to:

**How far from home.** The key region against the piece's own key, the
function of the chord inside that region (tonic, a substitute for it,
subdominant, dominant, or something chromatic), and whether the chord itself
is unstable (a seventh, a diminished triad, an inversion).

**How surprising.** For the line carrying the tune, how unlikely each note was
given the one before it and the harmony under it; for the harmony, how unusual
each root motion is. Small steps onto chord tones are expected. A leap that
keeps going, a chromatic note, a chord arriving from an odd direction are not.

Both are *models*, and the view says so. The numbers come from fixed tables --
functional harmony, the Krumhansl-Kessler key profiles, the long-observed
preference for small intervals and for a leap to be followed by a step back --
not from any recording, and they describe common-practice tonal expectation,
which is the idiom the studio writes in. They are for seeing the shape of a
piece: where it climbs, whether its loudest moment was prepared, where it goes
level. They are not a verdict, and nothing here is a lint finding.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .doc import Piece
from .render import Note, Render, render
from .theory import Chord, Key

#: Krumhansl & Kessler (1982): how well each chromatic degree fits a key.
_MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
_MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)

#: Root motion in semitones upward -> how often tonal music does it. Down a
#: fifth is the engine of the style; a tritone or a held root is rare.
_ROOT_MOTION = {5: .30, 7: .15, 2: .12, 10: .08, 9: .08, 8: .07, 3: .05, 4: .05,
                1: .03, 11: .03, 6: .02, 0: .02}

ACCOMPANIMENT_ROLES = ("harmony", "pad", "bass", "percussion", "ornament")

#: A humanized note can land a few ticks before the barline it belongs to.
#: Positions are judged this far ahead, so an early downbeat is still a downbeat.
EARLY = 30


def _when(n: Note) -> int:
    return n.start + EARLY


# --------------------------------------------------------------------------
# who has the tune
# --------------------------------------------------------------------------

def followers(piece: Piece) -> dict[str, set[str]]:
    """``voice -> voices it doubles``, from the ``double`` ops."""
    out: dict[str, set[str]] = {}
    for v, op in piece.all_ops():
        if op.kind == "double" and op.enabled:
            out.setdefault(v.name, set()).add(op.params["source"])
    return out


def tune_at(piece: Piece, notes: list[Note], lo: int, hi: int,
            doubles: dict[str, set[str]] | None = None) -> tuple[str | None, set[str]]:
    """The voice carrying the tune between two ticks, and everyone doubling it.

    A voice counts if it is a melody or counter-melody part sounding for at
    least a quarter of the span on its own material. Among those the melody
    role wins, then a voice stating a motif, then the highest. Voices that are
    only doubling the winner here are returned with it: they are the tune too.
    """
    doubles = followers(piece) if doubles is None else doubles
    kinds = {op.id: op.kind for _, op in piece.all_ops()}
    sounding: dict[str, list[Note]] = {}
    for n in notes:
        if n.percussive or n.ornament or n.end <= lo or n.start >= hi:
            continue
        sounding.setdefault(n.voice, []).append(n)
    span = max(1, hi - lo)
    lead: list[tuple[tuple, str]] = []
    following: dict[str, set[str]] = {}
    for v in piece.voices:
        ns = sounding.get(v.name)
        if not ns or v.role in ACCOMPANIMENT_ROLES:
            continue
        time = sum(min(n.end, hi) - max(n.start, lo) for n in ns)
        if time * 4 < span:
            continue
        if all(kinds.get(n.op) == "double" for n in ns):
            following[v.name] = doubles.get(v.name, set())
            continue
        rank = (v.role == "melody", any(n.motif for n in ns),
                sum(n.pitch for n in ns) / len(ns))
        lead.append((rank, v.name))
    if not lead:
        return None, set()
    tune = max(lead)[1]
    return tune, {tune} | {name for name, src in following.items() if tune in src}


# --------------------------------------------------------------------------
# harmony
# --------------------------------------------------------------------------

def _signature(key: Key) -> int:
    """Position on the circle of fifths, with a minor key at its relative major."""
    tonic = (key.tonic + 3) % 12 if key.minorish else key.tonic
    return (tonic * 7) % 12


def region_distance(key: Key, home: Key) -> float:
    """How far a section's key is from the piece's: fifths between signatures,
    so the relative major is next door, plus a little for not being home at all."""
    d = abs(_signature(key) - _signature(home))
    d = min(d, 12 - d)
    return d + (0.5 if (key.tonic, key.minorish) != (home.tonic, home.minorish) else 0.0)


def chord_function(chord: Chord, key: Key) -> tuple[float, str]:
    """``(distance, label)`` of a chord inside its own key.

    0 tonic, 1 a tonic substitute, 2 subdominant, 3 dominant, 4 chromatic or a
    secondary dominant -- the order in which they ask to be resolved.
    """
    if "/" in chord.numeral:
        return 4.0, "secondary"
    steps = key.steps
    if chord.root_offset % 12 not in steps:
        return 4.0, "chromatic"
    degree = steps.index(chord.root_offset % 12)
    third = chord.intervals[1] if chord.size > 1 else 4
    if degree == 0:
        return 0.0, "tonic"
    if degree == 4:
        # A minor v has no leading tone and does not pull like a dominant.
        return (3.0, "dominant") if third == 4 else (2.0, "modal dominant")
    if degree == 6:
        return (2.5, "subtonic") if key.minorish and third == 4 else (3.0, "dominant")
    if degree in (3, 1):
        return 2.0, "subdominant"
    return 1.0, "tonic substitute"


def chord_instability(chord: Chord, key: Key) -> float:
    iv = chord.intervals
    extra = 0.0
    if chord.size >= 4:
        extra += 0.5
    fifth = iv[2] - iv[0] if chord.size > 2 else 7
    third = iv[1] - iv[0] if chord.size > 1 else 4
    if fifth != 7:
        extra += 1.0                      # diminished or augmented
    if third in (2, 5):
        extra += 0.5                      # suspended: the third is still owed
    if chord.inversion:
        extra += 0.5
    scale = {(key.tonic + s) % 12 for s in key.steps}
    extra += 0.5 * sum(1 for pc in chord.pitch_classes(key) if pc not in scale)
    return extra


# --------------------------------------------------------------------------
# melody
# --------------------------------------------------------------------------

def _interval_prob(interval: int, previous: int | None) -> float:
    """Chance of this melodic interval, given the one before it."""
    def weight(i: int) -> float:
        w = math.exp(-abs(i) / 3.0) * (0.6 if i == 0 else 1.0)
        if previous is not None and abs(previous) >= 5:
            back = (i > 0) != (previous > 0)
            if back and 1 <= abs(i) <= 2:
                w *= 2.0                  # a leap, then a step back: the norm
            elif not back and abs(i) >= 3:
                w *= 0.4                  # a leap, then another the same way
        return w
    total = sum(weight(i) for i in range(-12, 13))
    return weight(max(-12, min(12, interval))) / total


def _degree_prob(pitch: int, key: Key, chord: Chord | None) -> float:
    profile = _MINOR_PROFILE if key.minorish else _MAJOR_PROFILE
    tones = set(chord.pitch_classes(key)) if chord is not None else set()
    weights = [profile[(pc - key.tonic) % 12] * (1.6 if pc in tones else 1.0)
               for pc in range(12)]
    return weights[pitch % 12] / sum(weights)


# --------------------------------------------------------------------------
# the curve
# --------------------------------------------------------------------------

@dataclass
class BarTension:
    bar: int
    home: float = 0.0            # harmonic distance from the piece's tonic
    dissonance: float = 0.0      # share of sounding time off the chord, 0..1
    surprise: float = 0.0        # bits per event, melody and harmony together
    energy: float = 0.0          # dynamics and activity, 0..1
    height: float | None = None  # mean pitch of the tune
    tension: float = 0.0         # the combined estimate, 0..1
    chords: list[str] = field(default_factory=list)
    function: str = ""
    tune: str | None = None
    #: The single least expected thing in the bar, for the reading.
    moment: tuple[float, str] | None = None


def analyze(piece: Piece, rend: Render | None = None) -> list[BarTension]:
    r = rend if rend is not None else render(piece)
    home = piece.key
    doubles = followers(piece)
    out: list[BarTension] = []
    previous_root: int | None = None
    prev_tune: tuple[str, int, int | None] | None = None   # voice, pitch, interval
    bars = piece.total_bars
    for bar in range(1, bars + 1):
        lo = piece.tick_of(bar)
        hi = piece.tick_of(bar + 1) if bar < bars else piece.total_ticks
        sec = piece.section_of_tick(lo)
        key = piece.key_at(lo)
        b = BarTension(bar)
        beat = max(1, (hi - lo) // max(1, int(sec.meter.split("/")[0])))

        # -- harmony, sampled on every beat ---------------------------------
        dist, events = [], []
        label = ""
        for tick in range(lo, hi, beat):
            chord, _ = piece.chord_at(tick)
            if chord is None:
                continue
            f, name = chord_function(chord, key)
            dist.append(region_distance(key, home) + f + chord_instability(chord, key))
            label = label or name
            if not b.chords or b.chords[-1] != chord.numeral:
                b.chords.append(chord.numeral)
                root = (key.tonic + chord.root_offset) % 12
                if previous_root is not None and root != previous_root:
                    bits = -math.log2(_ROOT_MOTION.get((root - previous_root) % 12, .02))
                    events.append((bits, f"{chord.numeral} arrives"))
                previous_root = root
        b.home = sum(dist) / len(dist) if dist else 0.0
        b.function = label

        # -- surface dissonance ---------------------------------------------
        here = [n for n in r.notes if n.start < hi and n.end > lo and not n.percussive]
        total = off = 0.0
        for n in here:
            length = min(n.end, hi) - max(n.start, lo)
            chord, k = piece.chord_at(max(n.start, lo))
            if chord is None:
                continue
            total += length
            pc = n.pitch % 12
            if pc not in chord.pitch_classes(k):
                scale = {(k.tonic + s) % 12 for s in k.steps}
                off += length * (1.0 if pc in scale else 1.5)
        b.dissonance = min(1.0, off / total) if total else 0.0

        # -- the tune: height and expectation -------------------------------
        b.tune, _ = tune_at(piece, r.notes, lo, hi, doubles)
        line = sorted((n for n in r.notes if n.voice == b.tune and lo <= _when(n) < hi
                       and not n.ornament), key=lambda n: (n.start, -n.pitch))
        seen = set()
        line = [n for n in line if not (n.start in seen or seen.add(n.start))]
        if line:
            b.height = sum(n.pitch for n in line) / len(line)
        for n in line:
            chord, k = piece.chord_at(_when(n))
            fit = -math.log2(_degree_prob(n.pitch, k, chord))
            bits = fit
            what = "a note outside the chord" if (
                chord is not None and n.pitch % 12 not in chord.pitch_classes(k)) else "a note"
            if prev_tune is not None and prev_tune[0] == b.tune:
                step = n.pitch - prev_tune[1]
                bits += -math.log2(_interval_prob(step, prev_tune[2]))
                if abs(step) >= 7:
                    what = f"a leap of {abs(step)} semitones"
                prev_tune = (b.tune, n.pitch, step)
            else:
                bits += fit                         # an entry: no interval to judge
                prev_tune = (b.tune, n.pitch, None)
            _, beat_pos = piece.position_of(max(lo, (n.start + EARLY) // 60 * 60))
            events.append((bits / 2, f"{what} in {b.tune} at beat {float(beat_pos):g}"))
        if events:
            b.surprise = sum(e[0] for e in events) / len(events)
            b.moment = max(events)

        # -- energy -----------------------------------------------------------
        onsets = [n for n in r.notes if lo <= _when(n) < hi]
        loud = sum(n.velocity for n in onsets) / len(onsets) / 127 if onsets else 0.0
        busy = min(1.0, len(onsets) / (12.0 * max(1, (hi - lo) // 480)))
        b.energy = 0.6 * loud + 0.4 * busy if onsets else 0.0
        out.append(b)

    heights = [b.height for b in out if b.height is not None]
    lo_h, hi_h = (min(heights), max(heights)) if heights else (0, 1)
    for b in out:
        h = (b.height - lo_h) / (hi_h - lo_h) if b.height is not None and hi_h > lo_h else 0.3
        b.tension = (0.40 * min(1.0, b.home / 6.0) + 0.15 * b.dissonance
                     + 0.30 * b.energy + 0.15 * h)
    return out


def _ramp(values: list[float], top: float) -> str:
    ramp = " .:-=+*#%@"
    return "".join(ramp[max(0, min(len(ramp) - 1, int(v / top * (len(ramp) - 1) + 0.5)))]
                   if top > 0 else " " for v in values)


def _spans(bars: list[int]) -> str:
    """``[5, 6, 7, 12]`` -> ``'5-7, 12'``."""
    out, start, prev = [], None, None
    for b in sorted(bars):
        if start is None:
            start = prev = b
        elif b == prev + 1:
            prev = b
        else:
            out.append(f"{start}-{prev}" if prev > start else f"{start}")
            start = prev = b
    if start is not None:
        out.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ", ".join(out)


def reading(piece: Piece, curve: list[BarTension]) -> list[str]:
    """What the curve shows, in sentences. Descriptions, not verdicts."""
    if not curve:
        return []
    notes: list[str] = []
    peak = max(curve, key=lambda b: b.tension)
    loudest = max(curve, key=lambda b: b.energy)
    notes.append(f"tension peaks in bar {peak.bar} ({peak.function or 'no chord'}, "
                 f"{'/'.join(peak.chords) or '-'}); energy peaks in bar {loudest.bar}")

    # Was the loudest stretch prepared? Look at the bars leading into the
    # first bar of the section (or run) that holds the energy peak.
    first = loudest.bar
    while first > 1 and curve[first - 2].energy >= loudest.energy * 0.85:
        first -= 1
    before = curve[max(0, first - 5):first - 1]
    if len(before) >= 2:
        rise = before[-1].tension - before[0].tension
        dominant = before[-1].home >= 3.0
        if rise > 0.05 or dominant:
            how = ("on a dominant" if dominant else "with tension rising") + \
                  (" and tension rising" if dominant and rise > 0.05 else "")
            notes.append(f"the loud passage from bar {first} is prepared: the bar "
                         f"before it stands {how}")
        else:
            notes.append(f"the loud passage from bar {first} arrives without "
                         f"harmonic preparation: tension is level or falling in "
                         f"bars {before[0].bar}-{before[-1].bar}")

    arrivals = [b.bar for a, b in zip(curve, curve[1:]) if a.home - b.home >= 2.5]
    if arrivals:
        notes.append(f"releases (a dominant or distant chord falling home): "
                     f"bar {_spans(arrivals)}")

    # Level stretches: nothing changing in harmony-distance, energy or surprise.
    med = sorted(b.surprise for b in curve)[len(curve) // 2]
    run: list[int] = []
    level: list[list[int]] = []
    for b in curve:
        ref = curve[run[0] - 1] if run else b
        flat = (abs(b.tension - ref.tension) <= 0.05 and b.surprise <= med
                and b.home <= 2.0)
        if flat:
            run.append(b.bar)
        else:
            if len(run) >= 4:
                level.append(run)
            run = [b.bar] if (b.surprise <= med and b.home <= 2.0) else []
    if len(run) >= 4:
        level.append(run)
    for stretch in level:
        notes.append(f"bars {stretch[0]}-{stretch[-1]} sit level: close to home, "
                     f"little surprise, tension within 0.05 -- restful if meant, "
                     f"slack if not")

    top = sorted((b for b in curve if b.moment), key=lambda b: -b.moment[0])[:3]
    if top:
        notes.append("least expected moments: " + "; ".join(
            f"bar {b.bar} ({b.moment[1]}, {b.moment[0]:.1f} bits)" for b in top))

    last = curve[-1]
    mean = sum(b.tension for b in curve) / len(curve)
    if last.home <= 0.5 and last.tension < mean:
        notes.append(f"it ends at home and below its average tension "
                     f"({last.tension:.2f} against {mean:.2f}): closed")
    elif piece.loop:
        notes.append("it ends away from home, which is right for a loop")
    else:
        notes.append(f"it ends {'away from home' if last.home > 0.5 else 'at home'} "
                     f"with tension at {last.tension:.2f} against an average of "
                     f"{mean:.2f}: open rather than closed")
    return notes


def view(piece: Piece, rend: Render | None = None) -> str:
    """One column per bar: distance from home, dissonance, surprise, tension."""
    from .readback import _section_ruler
    curve = analyze(piece, rend)
    bars = len(curve)
    out = [f"{piece.name} -- tension, {bars} bars, one column per bar "
           f"(a model of tonal expectation, not a measurement)", ""]
    out.append(f"  {'home':<11}{_ramp([b.home for b in curve], 6.0)}"
               f"   distance from the tonic of {piece.key.name}")
    out.append(f"  {'dissonance':<11}{_ramp([b.dissonance for b in curve], 0.5)}"
               f"   sounding time off the chord")
    # Surprise is shown against the piece's own range: every bar of any tune
    # carries a few bits, and it is the bars that carry more that matter.
    known = [b.surprise for b in curve if b.surprise > 0]
    low, top = (min(known), max(known)) if known else (0.0, 1.0)
    out.append(f"  {'surprise':<11}"
               f"{_ramp([max(0.0, b.surprise - low) if b.surprise else 0.0 for b in curve], max(1e-9, top - low))}"
               f"   how unexpected the tune and chord changes are "
               f"({low:.1f}-{top:.1f} bits)")
    out.append(f"  {'energy':<11}{_ramp([b.energy for b in curve], 1.0)}"
               f"   dynamics and activity")
    out.append(f"  {'tension':<11}{_ramp([b.tension for b in curve], 0.8)}"
               f"   the four together")
    out.append(f"  {'':<11}{_section_ruler(piece, bars)}")
    out.append("")
    for line in reading(piece, curve):
        out.append(f"  - {line}")
    return "\n".join(out)


def to_json(piece: Piece, rend: Render | None = None) -> list[dict]:
    return [{"bar": b.bar, "home": round(b.home, 2), "dissonance": round(b.dissonance, 3),
             "surprise": round(b.surprise, 2), "energy": round(b.energy, 3),
             "tension": round(b.tension, 3), "chords": b.chords,
             "function": b.function, "tune": b.tune}
            for b in analyze(piece, rend)]
