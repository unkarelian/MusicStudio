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
    #: An ornament realized at render time, in degree space: ``tr``, ``mord``,
    #: ``lmord``, ``turn``, ``gr`` (grace) or ``run``, optionally with a signed
    #: step count (``gr+1`` is a grace from the step above, ``run-3`` a run up
    #: from a fourth below). The written note keeps its onset and its length, so
    #: decorating a theme never moves it.
    orn: str = ""
    #: A per-note articulation that overrides the op's: one of ``ARTICULATIONS``.
    art: str = ""

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
        if self.orn:
            d["orn"] = self.orn
        if self.art:
            d["art"] = self.art
        return d

    @classmethod
    def from_json(cls, d: dict) -> Step:
        return cls(None if d.get("rest") else d.get("deg", 0), d.get("alt", 0),
                   ticks(d.get("dur", DEFAULT_UNIT)), d.get("accent", 0), d.get("tie", False),
                   d.get("orn", ""), d.get("art", ""))

    def source(self, unit: int) -> str:
        head = "r" if self.is_rest else f"{'#' * self.alt if self.alt > 0 else 'b' * -self.alt}{self.deg}"
        tail = "" if self.dur == unit else f":{ticks_to_dur(self.dur)}"
        marks = "".join(f"@{m}" for m in (self.orn, _ART_SHORT.get(self.art, self.art)) if m)
        return head + tail + ("~" if self.tie else "") + "!" * self.accent + marks


#: Ornaments a step may carry, and what each one does. Realized in
#: ``render._ornament``; listed here because the notation is defined here.
ORNAMENTS: dict[str, str] = {
    "tr": "Trill with the scale step above, settling on the written note.",
    "mord": "Upper mordent: note, step above, note -- a quick bite on the beat.",
    "lmord": "Lower mordent: note, step below, note.",
    "turn": "Turn: step above, note, step below, note.",
    "gr": "Grace note just before the beat. 'gr' comes from the step below, "
          "'gr+1' from above, 'gr-2' from a third below.",
    "run": "A fast scalar run into the note, before the beat. 'run-3' climbs "
           "from a fourth below, 'run+4' falls from a fifth above.",
}

#: ``@st`` and friends: short spellings of the articulations in ``render``.
ARTICULATION_MARKS = {"st": "staccato", "stac": "staccato", "ten": "tenuto",
                      "leg": "legato", "marc": "marcato", "port": "portato",
                      "staccato": "staccato", "tenuto": "tenuto", "legato": "legato",
                      "marcato": "marcato", "portato": "portato", "normal": "normal"}
_ART_SHORT = {"staccato": "st", "tenuto": "ten", "legato": "leg", "marcato": "marc",
              "portato": "port"}

_TOKEN_RE = re.compile(r"^(r|[b#]*-?\d+)(?::([^~!@]+))?(~?)(!*)((?:@[a-z]+[+-]?\d*)*)$")
_ORN_RE = re.compile(r"^(tr|mord|lmord|turn|gr|run)([+-]\d+)?$")


def parse_ornament(mark: str) -> tuple[str, int]:
    """``'gr+1'`` -> ``('gr', 1)``. The count is scale steps; 0 means the default."""
    m = _ORN_RE.match(mark)
    if not m:
        raise ValueError(f"unknown ornament {mark!r}; have {sorted(ORNAMENTS)}, "
                         f"with an optional signed step count as in 'gr+1' or 'run-3'")
    kind, n = m.group(1), int(m.group(2) or 0)
    if n and kind not in ("gr", "run"):
        raise ValueError(f"ornament {kind!r} takes no step count (got {mark!r})")
    return kind, n


def _flip_ornament(mark: str) -> str:
    """An ornament under inversion: what came from below now comes from above."""
    if not mark:
        return mark
    kind, n = parse_ornament(mark)
    if kind in ("mord", "lmord"):
        return "lmord" if kind == "mord" else "mord"
    if kind in ("gr", "run"):
        n = -(n or (-1 if kind == "gr" else -3))
        return f"{kind}{n:+d}"
    return mark


def _marks(raw: str, tok: str) -> tuple[str, str]:
    """Split ``'@tr@st'`` into an ornament and an articulation."""
    orn = art = ""
    for mark in filter(None, raw.split("@")):
        if mark in ARTICULATION_MARKS:
            art = ARTICULATION_MARKS[mark]
        else:
            try:
                parse_ornament(mark)
            except ValueError:
                raise ValueError(
                    f"bad mark '@{mark}' in {tok!r}: an ornament is one of "
                    f"{sorted(ORNAMENTS)} (e.g. '4:1/4@tr', '2@gr+1', '0@run-3') and an "
                    f"articulation one of {sorted(set(_ART_SHORT.values()))}") from None
            orn = mark
    return orn, art


def parse_steps(source: str | list, unit: str = DEFAULT_UNIT) -> tuple[Step, ...]:
    """Parse the compact motif notation.

    ``"0 2 4:1/4 r:1/8 b6 7~ 7"`` reads as: three steps of the default unit
    rising through the scale, a quarter note, an eighth rest, a flattened sixth,
    and a tied pair. ``|`` is allowed anywhere as a barline for the reader and
    is ignored. Degrees are scale steps, so ``7`` is the octave and ``-1`` is
    the step below the anchor.

    A note may end in ``@`` marks: an ornament (``4:1/4@tr``, ``2@mord``,
    ``0@gr``, ``7@run-3``) and/or an articulation (``2@st``, ``4:1/2@leg``).
    Ornaments are scale steps too, so a trill is always the trill the key gives.
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
                f"'5~', '0!!', '4:1/4@tr', '2@st'. A rest is 'r' or 'r:1/2'.")
        head, dur, tie, bangs, raw_marks = m.groups()
        d = ticks(dur) if dur else unit_ticks
        if head == "r":
            steps.append(Step(None, 0, d))
        else:
            alt = head.count("#") - head.count("b")
            orn, art = _marks(raw_marks, tok)
            steps.append(Step(int(head.lstrip("#b")), alt, d, min(len(bangs), 2),
                              bool(tie), orn, art))
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
        return self._derive([s if s.is_rest else
                             replace(s, deg=2 * axis - s.deg, alt=-s.alt,
                                     orn=_flip_ornament(s.orn))
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

    # -- elaboration -------------------------------------------------------
    #
    # Everything below makes a line *more* than it was -- longer, busier, more
    # decorated -- and every one of them goes through ``_derive``, so a theme
    # that has been embellished, dotted and extended is still, provably, that
    # theme. That is the difference between developing a tune and replacing it.

    def ornament(self, kind: str = "tr", positions: tuple[int, ...] | None = None, *,
                 name: str | None = None) -> Motif:
        """Mark notes with an ornament. ``positions`` index the *pitched* notes
        (default: the longest one), so rests never shift the count."""
        parse_ornament(kind)
        pitched = [i for i, s in enumerate(self.steps) if not s.is_rest]
        if not pitched:
            raise ValueError(f"motif {self.name!r} has no notes to ornament")
        if positions is None:
            want = {max(pitched, key=lambda i: (self.steps[i].dur, -i))}
        else:
            bad = [p for p in positions if not -len(pitched) <= p < len(pitched)]
            if bad:
                raise ValueError(f"ornament positions {bad} are out of range; "
                                 f"{self.name!r} has {len(pitched)} notes")
            want = {pitched[p] for p in positions}
        return self._derive([replace(s, orn=kind) if i in want else s
                             for i, s in enumerate(self.steps)],
                            f"ornament:{kind}", name)

    def embellish(self, kind: str = "neighbor", positions: tuple[int, ...] | None = None,
                  *, name: str | None = None) -> Motif:
        """Written-out diminution: break notes into smaller ones around themselves.

        ``neighbor`` and ``lower`` leave the note, touch the step beside it and
        come back; ``turn`` circles it; ``passing`` walks to the next note through
        the steps between; ``escape`` steps away and then leaps on. Each figure is
        carved out of the note's own value, so the bar it sits in stays the same
        length -- the same promise ``fill`` makes.
        """
        figures = {"neighbor": (0, 1, 0), "lower": (0, -1, 0), "turn": (0, 1, 0, -1, 0),
                   "escape": (0, 1), "passing": None}
        if kind not in figures:
            raise ValueError(f"unknown embellishment {kind!r}; have {sorted(figures)}")
        pitched = [i for i, s in enumerate(self.steps) if not s.is_rest]
        want = (set(pitched) if positions is None else
                {pitched[p] for p in positions if -len(pitched) <= p < len(pitched)})
        out: list[Step] = []
        for i, s in enumerate(self.steps):
            if i not in want or s.tie:
                out.append(s)
                continue
            if kind == "passing":
                nxt = next((t for t in self.steps[i + 1:] if not t.is_rest), None)
                gap = 0 if nxt is None else nxt.deg - s.deg
                if abs(gap) < 2:
                    out.append(s)
                    continue
                d = 1 if gap > 0 else -1
                offs = [0] + [k * d for k in range(1, abs(gap))]
            else:
                offs = list(figures[kind])
            # The written note keeps at least half its value, and the figure is
            # cut in plain note values -- the largest that fit -- so a dotted
            # quarter becomes a quarter and an eighth, not two dotted eighths.
            tail = len(offs) - 1
            room = (s.dur // 2) // tail if tail else 0
            share = TPQ * 4
            while share > room:
                share //= 2
            if share < TPQ // 8:                 # finer than a 32nd: leave it alone
                out.append(s)
                continue
            out.append(replace(s, dur=s.dur - share * tail))
            out += [Step(s.deg + o, 0, share, 0, False) for o in offs[1:]]
        return self._derive(out, f"embellish:{kind}", name)

    def expand(self, factor: int = 2, *, name: str | None = None) -> Motif:
        """Multiply every interval from the first note: steps become thirds.

        The contour and the rhythm are untouched, which is why an expanded theme
        is still heard as itself -- only more urgent, or more heroic.
        """
        factor = int(factor)
        if factor < 1:
            raise ValueError("expand needs a whole factor >= 1")
        first = next((s.deg for s in self.steps if not s.is_rest), 0)
        return self._derive([s if s.is_rest else
                             replace(s, deg=first + (s.deg - first) * factor)
                             for s in self.steps], f"expand:{factor}", name)

    def dot(self, ratio: str = "3/1", *, name: str | None = None) -> Motif:
        """Turn pairs of equal notes long-short. ``'3/1'`` is a dotted rhythm,
        ``'2/1'`` a swung or siciliano lilt, ``'1/3'`` a Scotch snap. Each pair
        keeps its combined length."""
        a, _, b = str(ratio).partition("/")
        num, den = int(a), int(b or 1)
        if num < 1 or den < 1:
            raise ValueError(f"dot ratio must be like '3/1', got {ratio!r}")
        out: list[Step] = []
        i = 0
        steps = self.steps
        while i < len(steps):
            s = steps[i]
            t = steps[i + 1] if i + 1 < len(steps) else None
            pair = (t is not None and not s.is_rest and not t.is_rest
                    and s.dur == t.dur and not s.tie and not t.tie
                    and (2 * s.dur) % (num + den) == 0)
            if not pair:
                out.append(s)
                i += 1
                continue
            unit = 2 * s.dur // (num + den)
            out += [replace(s, dur=unit * num), replace(t, dur=unit * den)]
            i += 2
        return self._derive(out, f"dot:{num}/{den}", name)

    def displace(self, by: str = "1/8", *, name: str | None = None) -> Motif:
        """Start late by ``by`` and take the time back off the last note, so the
        same shape arrives syncopated without growing longer."""
        d = ticks(by)
        last = self.steps[-1]
        if last.dur <= d:
            raise ValueError(
                f"cannot displace {self.name!r} by {by}: its last step is only "
                f"{ticks_to_dur(last.dur)} long and the time has to come from there")
        return self._derive((Step(None, 0, d),) + self.steps[:-1]
                            + (replace(last, dur=last.dur - d),), f"displace:{by}", name)

    def thin(self, grid: str = "1/4", *, name: str | None = None) -> Motif:
        """Reduce to the notes that fall on ``grid``; each absorbs what followed it.

        The inverse of embellishing: the skeleton of a busy line, for the bass to
        shadow or the brass to state broadly while the strings keep the detail.
        """
        g = ticks(grid)
        out: list[Step] = []
        tick = 0
        for s in self.steps:
            if tick % g == 0 or not out:
                out.append(replace(s, tie=False, orn="" if s.is_rest else s.orn))
            else:
                out[-1] = replace(out[-1], dur=out[-1].dur + s.dur)
            tick += s.dur
        return self._derive(out, f"thin:{grid}", name)

    def mirror(self, *, name: str | None = None) -> Motif:
        """The motif, then itself backwards -- an arch, twice as long."""
        back = self.retrograde().steps
        return self._derive(self.steps + back, "mirror", name)

    def append(self, steps: str, *, name: str | None = None) -> Motif:
        """Add a tail in the same notation: a cadence, a pickup, a held note."""
        return self._derive(self.steps + parse_steps(steps, self.unit), "append", name)

    def then(self, other: Motif, *, name: str | None = None) -> Motif:
        """Join another motif on the end, to build a long theme out of cells.

        The result still descends from *this* motif -- a period is its opening
        idea plus whatever answers it -- and the lineage names what was joined.
        """
        return self._derive(self.steps + other.steps, f"then:{other.name}", name)

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
    "ornament": "Mark notes with an ornament -- tr, mord, lmord, turn, gr, run-3. "
                "args: kind, positions (default: the longest note). 'ornament:tr,0 3'",
    "embellish": "Written-out diminution inside each note's own value: neighbor, "
                 "lower, turn, passing, escape. args: kind, positions",
    "expand": "Multiply every interval from the first note (steps become thirds). "
              "args: factor",
    "dot": "Make pairs of equal notes long-short, keeping each pair's length: "
           "'3/1' dotted, '2/1' lilting, '1/3' snapped. args: ratio",
    "displace": "Enter late and take the time off the last note -- syncopation "
                "without growing longer. args: by ('1/8')",
    "thin": "Reduce to the notes on a grid; the skeleton of a busy line. args: grid",
    "mirror": "The motif followed by its own retrograde. args: none",
    "append": "Add a tail in motif notation. args: steps ('4 2 0:1/2')",
    "then": "Join another named motif on the end -- how a long theme is built "
            "from cells while staying traceable. args: motif name",
}


def apply_transform(m: Motif, op: str, resolve=None, **kwargs) -> Motif:
    """Apply one named transform. ``op`` may carry args as ``'transpose:2'``.

    ``resolve`` looks a motif up by name, for ``then``; a piece passes its own
    ``get_motif``.
    """
    if ":" in op and not kwargs:
        op, _, raw = op.partition(":")
        # Motif notation has colons and no commas, so only the first colon splits.
        args = [raw] if op == "append" else [a for a in raw.split(",") if a != ""]
        kwargs = _positional(op, args)
    if op not in TRANSFORMS:
        raise ValueError(f"unknown transform {op!r}; have {sorted(TRANSFORMS)}")
    if op == "then":
        other = kwargs.pop("motif", None) or kwargs.pop("other", None)
        if isinstance(other, str):
            if resolve is None:
                raise ValueError("'then' joins a named motif, which needs a piece to "
                                 "look it up in")
            other = resolve(other)
        if other is None:
            raise ValueError("'then' needs a motif name, e.g. 'then:answer'")
        return m.then(other, **kwargs)
    return getattr(m, op)(**kwargs)


def _positional(op: str, args: list[str]) -> dict:
    names = {"transpose": ["n"], "invert": ["axis"], "retrograde": [],
             "augment": ["factor"], "diminish": ["factor"],
             "fragment": ["start", "count"], "rotate": ["n"],
             "sequence": ["times", "step"], "rhythmize": ["pattern"], "fill": [],
             "accentuate": ["positions", "amount"],
             "ornament": ["kind", "positions"], "embellish": ["kind", "positions"],
             "expand": ["factor"], "dot": ["ratio"], "displace": ["by"],
             "thin": ["grid"], "mirror": [], "append": ["steps"],
             "then": ["motif"]}.get(op, [])
    out = {}
    for key, val in zip(names, args):
        if key in ("pattern", "kind", "ratio", "by", "grid", "steps", "motif"):
            out[key] = val
        elif key == "positions":
            out[key] = tuple(int(v) for v in val.split())
        elif key == "factor":
            out[key] = int(val) if op == "expand" else val
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
