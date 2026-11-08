"""Motifs and the transformations that develop them.

A motif is the unit of musical thought, so it is the unit the studio addresses.
It is stored in *degree space* -- a run of scale steps and durations, with no
key, no register and no instrument attached -- which is what makes the classical
development operations exact rather than approximate:

    transpose   deg + n              inversion   2*axis - deg
    retrograde  reverse the steps    augment     durations * factor

Because these are integer operations on a named object, a leitmotif that comes
back inverted and augmented in the last act is *provably the same motif*, and
the studio can say so. An agent re-emitting notes it thinks it remembers cannot
make that claim, which is precisely why agent-written scores have themes that
quietly stop being themes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from fractions import Fraction

from .theory import TPQ, ticks, ticks_to_dur

DEFAULT_UNIT = "1/8"


@dataclass(frozen=True, slots=True)
class Step:
    """One event: a scale degree with a duration, or a rest.

    ``deg`` is an offset in scale steps from the motif's anchor, so 0 is the
    anchor itself and 7 is the octave above it in a seven-note scale. ``alt``
    is a chromatic inflection in semitones, carried through every transform so
    a raised leading tone stays raised.
    """

    deg: int | None = None
    alt: int = 0
    dur: int = TPQ // 2
    accent: int = 0
    tie: bool = False

    @property
    def is_rest(self) -> bool:
        return self.deg is None

    def to_json(self) -> dict:
        d: dict = {"dur": ticks_to_dur(self.dur)}
        if self.is_rest:
            d["rest"] = True
        else:
            d["deg"] = self.deg
            if self.alt:
                d["alt"] = self.alt
        if self.accent:
            d["accent"] = self.accent
        if self.tie:
            d["tie"] = True
        return d

    @classmethod
    def from_json(cls, d: dict) -> Step:
        return cls(None if d.get("rest") else d.get("deg", 0), d.get("alt", 0),
                   ticks(d.get("dur", DEFAULT_UNIT)), d.get("accent", 0), d.get("tie", False))

    def source(self, unit: int) -> str:
        head = "r" if self.is_rest else f"{'#' * self.alt if self.alt > 0 else 'b' * -self.alt}{self.deg}"
        tail = "" if self.dur == unit else f":{ticks_to_dur(self.dur)}"
        return head + tail + ("~" if self.tie else "") + "!" * self.accent


_TOKEN_RE = re.compile(r"^(r|[b#]*-?\d+)(?::([^~!]+))?(~?)(!*)$")


def parse_steps(source: str | list, unit: str = DEFAULT_UNIT) -> tuple[Step, ...]:
    """Parse the compact motif notation.

    ``"0 2 4:1/4 r:1/8 b6 7~ 7"`` reads as: three steps of the default unit
    rising through the scale, a quarter note, an eighth rest, a flattened sixth,
    and a tied pair. ``|`` is allowed anywhere as a barline for the reader and
    is ignored. Degrees are scale steps, so ``7`` is the octave and ``-1`` is
    the step below the anchor.
    """
    if isinstance(source, (list, tuple)):
        return tuple(s if isinstance(s, Step) else Step.from_json(s) for s in source)
    unit_ticks = ticks(unit)
    steps: list[Step] = []
    for tok in str(source).replace("|", " ").split():
        m = _TOKEN_RE.match(tok)
        if not m:
            raise ValueError(
                f"bad motif token {tok!r} in {source!r}. A token is a scale degree with "
                f"optional accidental, duration, tie and accent: '0', 'b3', '4:1/4', "
                f"'5~', '0!!'. A rest is 'r' or 'r:1/2'.")
        head, dur, tie, bangs = m.groups()
        d = ticks(dur) if dur else unit_ticks
        if head == "r":
            steps.append(Step(None, 0, d))
        else:
            alt = head.count("#") - head.count("b")
            steps.append(Step(int(head.lstrip("#b")), alt, d, min(len(bangs), 2), bool(tie)))
    if not steps:
        raise ValueError(f"motif source {source!r} has no steps")
    return tuple(steps)


@dataclass(frozen=True)
class Motif:
    """A named shape in degree space, plus the record of how it was derived."""

    name: str
    steps: tuple[Step, ...]
    #: ``scale`` counts steps of the key's scale; ``chord`` counts chord tones,
    #: so 0/1/2 are root/third/fifth and the figure re-fits every chord it meets.
    anchor: str = "scale"
    #: Optional scale override, e.g. a pentatonic tune over diatonic harmony.
    scale: str | None = None
    unit: str = DEFAULT_UNIT
    note: str = ""
    derived_from: str | None = None
    #: The transformations applied to get here, in order.
    lineage: tuple[str, ...] = ()

    # -- measurements ------------------------------------------------------

    @property
    def duration(self) -> int:
        return sum(s.dur for s in self.steps)

    @property
    def pitched(self) -> list[Step]:
        return [s for s in self.steps if not s.is_rest]

    @property
    def span(self) -> int:
        """Range in scale steps between the lowest and highest degree."""
        d = [s.deg for s in self.pitched]
        return (max(d) - min(d)) if d else 0

    @property
    def intervals(self) -> tuple[int, ...]:
        """Successive degree differences -- the motif's identity under transposition."""
        d = [s.deg for s in self.pitched]
        return tuple(b - a for a, b in zip(d, d[1:]))

    @property
    def rhythm(self) -> tuple[int, ...]:
        return tuple(s.dur for s in self.steps)

    @property
    def root(self) -> str:
        """The name of the motif this one ultimately came from."""
        return self.derived_from or self.name

    def contour(self) -> str:
        """Up/down/repeat as a string -- what a listener actually remembers."""
        return "".join("+" if i > 0 else "-" if i < 0 else "=" for i in self.intervals)

    def source(self) -> str:
        u = ticks(self.unit)
        return " ".join(s.source(u) for s in self.steps)

    # -- transformations ---------------------------------------------------

    def _derive(self, steps, op: str, name: str | None = None) -> Motif:
        return replace(
            self,
            name=name or f"{self.name}.{op.split(':')[0]}",
            steps=tuple(steps),
            derived_from=self.derived_from or self.name,
            lineage=self.lineage + (op,),
        )

    def transpose(self, n: int, *, name: str | None = None) -> Motif:
        """Move by ``n`` scale steps. Diatonic, so it stays in key by construction."""
        return self._derive([s if s.is_rest else replace(s, deg=s.deg + n)
                             for s in self.steps], f"transpose:{n}", name)

    def invert(self, axis: int | None = None, *, name: str | None = None) -> Motif:
        """Flip the contour about ``axis`` (default: the motif's first note)."""
        if axis is None:
            axis = next((s.deg for s in self.steps if not s.is_rest), 0)
        return self._derive([s if s.is_rest else replace(s, deg=2 * axis - s.deg, alt=-s.alt)
                             for s in self.steps], f"invert:{axis}", name)

    def retrograde(self, *, name: str | None = None) -> Motif:
        """Reverse the order. Ties belong to the note they precede, so they shift."""
        rev = list(reversed(self.steps))
        ties = [False] + [s.tie for s in rev[:-1]]
        return self._derive([replace(s, tie=t) for s, t in zip(rev, ties)],
                            "retrograde", name)

    def augment(self, factor: str | int | Fraction = 2, *, name: str | None = None) -> Motif:
        """Stretch durations. ``factor`` may be a fraction like ``'3/2'``."""
        f = Fraction(str(factor))
        if f <= 0:
            raise ValueError(f"augment factor must be positive, got {factor}")
        out = []
        for s in self.steps:
            t = Fraction(s.dur) * f
            if t.denominator != 1:
                raise ValueError(
                    f"augmenting {self.name!r} by {factor} gives a duration of {t} ticks; "
                    f"pick a factor that divides evenly (2, 1/2, 3/2, 2/3)")
            out.append(replace(s, dur=int(t)))
        return self._derive(out, f"augment:{f}", name)

    def diminish(self, factor: str | int | Fraction = 2, *, name: str | None = None) -> Motif:
        return self.augment(Fraction(1, 1) / Fraction(str(factor)), name=name)._retag(
            f"diminish:{factor}")

    def _retag(self, op: str) -> Motif:
        return replace(self, lineage=self.lineage[:-1] + (op,),
                       name=self.name.rsplit(".", 1)[0] + "." + op.split(":")[0])

    def fragment(self, start: int = 0, count: int | None = None, *,
                 name: str | None = None) -> Motif:
        """Take a slice. Development is mostly this plus a sequence."""
        end = len(self.steps) if count is None else start + count
        chunk = self.steps[start:end]
        if not chunk:
            raise ValueError(
                f"fragment of {self.name!r} from {start} count {count} is empty; "
                f"the motif has {len(self.steps)} steps")
        return self._derive(chunk, f"fragment:{start},{len(chunk)}", name)

    def rotate(self, n: int = 1, *, name: str | None = None) -> Motif:
        n %= len(self.steps)
        return self._derive(self.steps[n:] + self.steps[:n], f"rotate:{n}", name)

    def sequence(self, times: int = 2, step: int = 1, *, name: str | None = None) -> Motif:
        """Restate the motif ``times`` times, each ``step`` scale steps higher.

        The rising sequence is the single most common development device there
        is, and doing it by hand is where transposition errors accumulate.
        """
        if times < 1:
            raise ValueError("sequence needs times >= 1")
        out: list[Step] = []
        for i in range(times):
            out += [s if s.is_rest else replace(s, deg=s.deg + step * i) for s in self.steps]
        return self._derive(out, f"sequence:{times},{step}", name)

    def rhythmize(self, pattern: str, *, name: str | None = None) -> Motif:
        """Keep the pitches, take the rhythm from elsewhere. Pitches cycle to fit."""
        durs = [ticks(d) for d in str(pattern).replace("|", " ").split()]
        if not durs:
            raise ValueError("rhythmize needs a pattern like '1/8 1/8 1/4'")
        pitched = self.pitched or list(self.steps)
        return self._derive([replace(pitched[i % len(pitched)], dur=d)
                             for i, d in enumerate(durs)], f"rhythmize:{len(durs)}", name)

    def fill(self, *, name: str | None = None) -> Motif:
        """Fill leaps with stepwise passing tones, keeping the total duration.

        The inserted notes come out of the leaping note's own value, so the
        motif still lands exactly where it did before -- the point is to smooth
        a line without moving anything after it.
        """
        out: list[Step] = []
        for i, s in enumerate(self.steps):
            nxt = next((t for t in self.steps[i + 1:] if not t.is_rest), None)
            gap = 0 if (s.is_rest or nxt is None) else nxt.deg - s.deg
            if abs(gap) < 2:
                out.append(s)
                continue
            direction = 1 if gap > 0 else -1
            passing = list(range(s.deg + direction, nxt.deg, direction))
            share, extra = divmod(s.dur, len(passing) + 1)
            if share == 0:                      # too short to subdivide; leave it
                out.append(s)
                continue
            out.append(replace(s, dur=share + extra, tie=False))
            out += [Step(d, 0, share, 0, False) for d in passing]
        return self._derive(out, "fill", name)

    def accentuate(self, positions: tuple[int, ...] = (0,), amount: int = 1, *,
                   name: str | None = None) -> Motif:
        idx = set(positions)
        return self._derive([replace(s, accent=max(-2, min(2, s.accent + amount)))
                             if i in idx else s for i, s in enumerate(self.steps)],
                            f"accentuate:{sorted(idx)}", name)

    # -- persistence -------------------------------------------------------

    def to_json(self) -> dict:
        d = {"name": self.name, "anchor": self.anchor, "unit": self.unit,
             "source": self.source(), "steps": [s.to_json() for s in self.steps]}
        if self.scale:
            d["scale"] = self.scale
        if self.note:
            d["note"] = self.note
        if self.derived_from:
            d["derived_from"] = self.derived_from
            d["lineage"] = list(self.lineage)
        return d

    @classmethod
    def from_json(cls, d: dict) -> Motif:
        return cls(d["name"], tuple(Step.from_json(s) for s in d["steps"]),
                   d.get("anchor", "scale"), d.get("scale"), d.get("unit", DEFAULT_UNIT),
                   d.get("note", ""), d.get("derived_from"), tuple(d.get("lineage", ())))


def make_motif(name: str, source: str | list, *, anchor: str = "scale",
               scale: str | None = None, unit: str = DEFAULT_UNIT,
               note: str = "") -> Motif:
    if anchor not in ("scale", "chord"):
        raise ValueError(f"anchor must be 'scale' or 'chord', got {anchor!r}")
    return Motif(name, parse_steps(source, unit), anchor, scale, unit, note)


#: The development vocabulary, for discovery. Each maps to a ``Motif`` method.
TRANSFORMS: dict[str, str] = {
    "transpose": "Move by n scale steps (diatonic, so it stays in key). args: n",
    "invert": "Flip the contour about an axis degree (default: the first note). args: axis",
    "retrograde": "Play it backwards. args: none",
    "augment": "Stretch durations by a factor, e.g. 2 or '3/2'. args: factor",
    "diminish": "Compress durations by a factor. args: factor",
    "fragment": "Take a slice -- the raw material of development. args: start, count",
    "rotate": "Start from a different step, wrapping around. args: n",
    "sequence": "Restate n times, each `step` degrees higher. args: times, step",
    "rhythmize": "Keep the pitches, take a new rhythm. args: pattern ('1/8 1/8 1/4')",
    "fill": "Fill leaps with passing tones without changing the total duration. args: none",
    "accentuate": "Add accents at step positions. args: positions, amount",
}


def apply_transform(m: Motif, op: str, **kwargs) -> Motif:
    """Apply one named transform. ``op`` may carry args as ``'transpose:2'``."""
    if ":" in op and not kwargs:
        op, _, raw = op.partition(":")
        args = [a for a in raw.split(",") if a != ""]
        kwargs = _positional(op, args)
    if op not in TRANSFORMS:
        raise ValueError(f"unknown transform {op!r}; have {sorted(TRANSFORMS)}")
    return getattr(m, op)(**kwargs)


def _positional(op: str, args: list[str]) -> dict:
    names = {"transpose": ["n"], "invert": ["axis"], "retrograde": [],
             "augment": ["factor"], "diminish": ["factor"],
             "fragment": ["start", "count"], "rotate": ["n"],
             "sequence": ["times", "step"], "rhythmize": ["pattern"], "fill": [],
             "accentuate": ["positions", "amount"]}[op]
    out = {}
    for key, val in zip(names, args):
        if key in ("pattern",):
            out[key] = val
        elif key == "positions":
            out[key] = tuple(int(v) for v in val.split())
        elif key == "factor":
            out[key] = val
        else:
            out[key] = int(val)
    return out


def similarity(a: Motif, b: Motif) -> float:
    """How much two motifs share, 0..1, ignoring transposition.

    Intervals carry identity far more than absolute degrees do, and rhythm
    carries it more than either -- a theme survives being transposed, and it
    survives being reharmonized, but it stops being itself when the rhythm goes.
    Used to notice that a passage is quoting a theme without being told.
    """
    ai, bi = a.intervals, b.intervals
    ar, br = _normalized_rhythm(a), _normalized_rhythm(b)
    return 0.55 * _seq_ratio(ai, bi) + 0.45 * _seq_ratio(ar, br)


def _normalized_rhythm(m: Motif) -> tuple[Fraction, ...]:
    """Durations as ratios to the first, so augmentation still matches."""
    r = m.rhythm
    return tuple(Fraction(d, r[0]) for d in r) if r else ()


def _seq_ratio(a, b) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    # Longest common subsequence, length-normalized.
    la, lb = len(a), len(b)
    prev = [0] * (lb + 1)
    for i in range(la):
        cur = [0] * (lb + 1)
        for j in range(lb):
            cur[j + 1] = prev[j] + 1 if a[i] == b[j] else max(prev[j + 1], cur[j])
        prev = cur
    return prev[lb] / max(la, lb)
