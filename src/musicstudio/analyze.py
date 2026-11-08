"""Finding themes in music the studio did not write.

The hard part of motif discovery is not finding repeated patterns. It is
refusing to report the ones that mean nothing. Any long melody contains
thousands of repeated interval sequences by pure chance, and a scale passage
will hand you ``[2,2,2,2]`` in every piece ever written -- so a discovery tool
that ranks by frequency will confidently announce that two unrelated works
share a theme.

Every pattern here is therefore tested against a null model: the same interval
sequence, shuffled, many times over. If the pattern shows up about as often in
the shuffles as in the music, it is a property of the interval vocabulary rather
than a theme, and it is dropped. Degenerate shapes -- all repeated notes, pure
alternation, pure scale runs -- are dropped outright, because those are also the
exact artifacts a pitch tracker produces when it fails.

This is the same principle as the critique pass: a false positive costs more
trust than a missed finding costs insight. A tool that tells you two pieces
share a leitmotif when they do not is worse than one that says it cannot tell.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .ingest import Event
from .motif import Motif, Step
from .theory import TPQ, interval_name

MIN_LEN, MAX_LEN = 4, 10


@dataclass
class Occurrence:
    source: str
    index: int
    tick: int
    pitch: int


@dataclass
class Pattern:
    """A candidate theme: an interval sequence plus where it was found."""

    intervals: tuple[int, ...]
    occurrences: list[Occurrence] = field(default_factory=list)
    #: Fraction of shuffled controls containing this pattern. Low means real.
    p_value: float = 1.0
    sources: tuple[str, ...] = ()

    @property
    def length(self) -> int:
        return len(self.intervals) + 1        # intervals -> notes

    @property
    def span(self) -> int:
        run, lo, hi = 0, 0, 0
        for i in self.intervals:
            run += i
            lo, hi = min(lo, run), max(hi, run)
        return hi - lo

    def contour(self) -> str:
        return "".join("+" if i > 0 else "-" if i < 0 else "=" for i in self.intervals)

    def as_motif(self, name: str, unit: str = "1/8") -> Motif:
        """Turn a discovered pattern into a real motif you can play and develop."""
        from .theory import ticks
        degs, run = [0], 0
        for i in self.intervals:
            run += i
            degs.append(run)
        # Chromatic intervals become semitone offsets from the first note, carried
        # as alterations so the shape survives exactly rather than being rounded
        # into whatever the key happens to allow.
        steps = tuple(Step(round(d / 2), d - 2 * round(d / 2), ticks(unit)) for d in degs)
        return Motif(name, steps, "scale", "chromatic", unit,
                     f"discovered pattern, p={self.p_value:.3f}")

    def to_json(self) -> dict:
        return {"intervals": list(self.intervals), "notes": self.length,
                "contour": self.contour(), "span_semitones": self.span,
                "p_value": round(self.p_value, 4),
                "sources": list(self.sources),
                "occurrences": [{"source": o.source, "tick": o.tick,
                                 "beat": round(o.tick / TPQ, 2)} for o in self.occurrences[:12]],
                "shape": " ".join(interval_name(i) + ("↑" if i > 0 else "↓" if i < 0 else "")
                                  for i in self.intervals)}


# --------------------------------------------------------------------------
# reducing polyphony to a line
# --------------------------------------------------------------------------

def melody_line(events: list[Event], *, mode: str = "top") -> list[Event]:
    """Reduce a polyphonic part to one line before looking for melodic patterns.

    ``top`` keeps the highest note sounding at each onset, which is where a
    melody almost always is. Without this step, chords turn into arpeggios and
    every interval measurement is meaningless.
    """
    if not events:
        return []
    order = sorted(events, key=lambda e: (e.start, -e.pitch))
    out: list[Event] = []
    for ev in order:
        if out and ev.start - out[-1].start < TPQ // 16:
            if mode == "top" and ev.pitch > out[-1].pitch:
                out[-1] = ev
            elif mode == "bottom" and ev.pitch < out[-1].pitch:
                out[-1] = ev
            continue
        out.append(ev)
    return out


def intervals_of(line: list[Event]) -> list[int]:
    return [b.pitch - a.pitch for a, b in zip(line, line[1:])]


# --------------------------------------------------------------------------
# degeneracy filters
# --------------------------------------------------------------------------

def is_degenerate(pat: tuple[int, ...]) -> str | None:
    """Shapes that carry no thematic information, and why they are dropped.

    Each of these is also a known pitch-tracker artifact, which is not a
    coincidence: a failing tracker produces exactly the patterns that a melody
    would never make distinctive use of.
    """
    if all(i == 0 for i in pat):
        return "all repeated notes"
    if all(pat[i] == -pat[i + 1] for i in range(len(pat) - 1)) and pat[0] != 0:
        return "pure alternation between two pitches"
    if len({abs(i) for i in pat} - {0}) <= 1 and all(i >= 0 for i in pat):
        return "an unbroken run in one direction"
    if len({abs(i) for i in pat} - {0}) <= 1 and all(i <= 0 for i in pat):
        return "an unbroken run in one direction"
    if sum(1 for i in pat if i == 0) > len(pat) * 0.6:
        return "mostly repeated notes"
    if max(abs(i) for i in pat) > 24:
        return "a leap larger than two octaves, almost certainly a tracking error"
    return None


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------

def _ngram_index(ivs: list[int], lo: int, hi: int) -> dict[tuple[int, ...], list[int]]:
    out: dict[tuple[int, ...], list[int]] = {}
    for L in range(lo, hi + 1):
        for i in range(len(ivs) - L + 1):
            out.setdefault(tuple(ivs[i:i + L]), []).append(i)
    return out


def _null_rate(pat: tuple[int, ...], ivs: list[int], trials: int, rng: random.Random) -> float:
    """How often this pattern appears in shuffles of the same interval vocabulary."""
    needle = "," + ",".join(map(str, pat)) + ","
    shuffled = list(ivs)
    hits = 0
    for _ in range(trials):
        rng.shuffle(shuffled)
        if needle in "," + ",".join(map(str, shuffled)) + ",":
            hits += 1
    return hits / trials


def find_motifs(events: list[Event], *, source: str = "piece", min_notes: int = 4,
                max_notes: int = 10, min_occurrences: int = 2, p_max: float = 0.05,
                trials: int = 120, seed: int = 17, limit: int = 12) -> list[Pattern]:
    """Repeated melodic shapes within one piece, filtered for significance."""
    line = melody_line(events)
    ivs = intervals_of(line)
    if len(ivs) < min_notes:
        return []
    rng = random.Random(seed)
    index = _ngram_index(ivs, min_notes - 1, max_notes - 1)
    out: list[Pattern] = []
    for pat, spots in index.items():
        if len(spots) < min_occurrences or is_degenerate(pat):
            continue
        p = _null_rate(pat, ivs, trials, rng)
        if p > p_max:
            continue
        out.append(Pattern(pat, [Occurrence(source, i, line[i].start, line[i].pitch)
                                 for i in spots], p, (source,)))
    # Prefer long, frequent, unlikely patterns; drop any that is a sub-pattern of
    # a longer accepted one, since reporting both says the same thing twice.
    out.sort(key=lambda x: (-x.length, -len(x.occurrences), x.p_value))
    kept: list[Pattern] = []
    for cand in out:
        needle = "," + ",".join(map(str, cand.intervals)) + ","
        if any(needle in "," + ",".join(map(str, k.intervals)) + "," for k in kept):
            continue
        kept.append(cand)
        if len(kept) >= limit:
            break
    return kept


def shared_motifs(sources: dict[str, list[Event]], *, min_notes: int = 4,
                  max_notes: int = 10, require: int | None = None,
                  p_max: float = 0.02, trials: int = 200, seed: int = 17,
                  limit: int = 12) -> list[Pattern]:
    """Melodic shapes common to several pieces -- the leitmotif question.

    Intervals are used rather than pitches, so a theme still matches when it
    returns in another key. A pattern must clear the null model *in every piece
    it is claimed to appear in*: sharing a shape that both pieces would produce
    by chance is not evidence of a shared theme.
    """
    need = require if require is not None else len(sources)
    rng = random.Random(seed)
    lines = {k: melody_line(v) for k, v in sources.items()}
    ivs = {k: intervals_of(v) for k, v in lines.items()}
    index = {k: _ngram_index(v, min_notes - 1, max_notes - 1) for k, v in ivs.items()}

    tally: dict[tuple[int, ...], list[str]] = {}
    for name, idx in index.items():
        for pat in idx:
            tally.setdefault(pat, []).append(name)

    out: list[Pattern] = []
    for pat, names in tally.items():
        if len(names) < need or is_degenerate(pat):
            continue
        ps = {n: _null_rate(pat, ivs[n], trials, rng) for n in names}
        if max(ps.values()) > p_max:
            continue
        occ = [Occurrence(n, i, lines[n][i].start, lines[n][i].pitch)
               for n in names for i in index[n][pat]]
        out.append(Pattern(pat, occ, max(ps.values()), tuple(sorted(names))))

    out.sort(key=lambda x: (-len(x.sources), -x.length, x.p_value))
    kept: list[Pattern] = []
    for cand in out:
        needle = "," + ",".join(map(str, cand.intervals)) + ","
        if any(needle in "," + ",".join(map(str, k.intervals)) + ","
               and set(cand.sources) <= set(k.sources) for k in kept):
            continue
        kept.append(cand)
        if len(kept) >= limit:
            break
    return kept


def report_patterns(patterns: list[Pattern], *, header: str = "") -> str:
    if not patterns:
        return ((header + "\n" if header else "")
                + "no pattern survived the significance test -- nothing here is "
                  "repeated more than the interval vocabulary alone would predict")
    lines = [header] if header else []
    lines.append(f"{'shape (contour)':<20} {'notes':>5} {'span':>5} {'p':>7}  where")
    lines.append("-" * 78)
    for p in patterns:
        where = ", ".join(f"{s}×{sum(1 for o in p.occurrences if o.source == s)}"
                          for s in p.sources)
        lines.append(f"{p.contour():<20} {p.length:>5} {p.span:>4}st {p.p_value:>7.3f}  {where}")
        lines.append(f"  intervals {list(p.intervals)}")
    return "\n".join(lines)
