"""The critique pass.

These are the defects that make agent-written music read as agent-written. Not
wrong notes -- degree space already made those hard -- but the structural
failures a note-by-note writer cannot see: a counter-melody sitting on top of
the tune, thirds in the bass turning to mud, four minutes at exactly one dynamic,
a theme stated once and never developed, a B section that is bar-for-bar the A
section again.

Every finding carries positions, because "the voice leading is bad somewhere" is
not actionable and "parallel fifths at 12:3 between horn and cello" is.

**Precision over recall.** A false positive on correct writing costs more trust
than a missed finding costs quality, so every check here is deliberately
conservative: parallels are only reported between two genuinely independent
monophonic lines, a clash must be long *and* dissonant *and* unresolved, and a
leap has to exceed an octave before anyone is told about it. Textbook-correct
four-part writing must come back clean, and there is a test that says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from .doc import Piece
from .render import Note, Render, render
from .style import StyleProfile, get_style
from .theory import parse_chord, spell_pitch

MAX_SPOTS = 10

#: Slices shorter than a 32nd note are not "moments". Humanized timing and
#: legato overlaps produce sonorities a few ticks long where one note's release
#: meets the next one's attack; counting those as chords is how a correct line
#: gets reported as a monophonic instrument playing two notes.
MIN_MOMENT = 60
#: How far ahead of a chord change a note may land and still count as on it.
EARLY = 30


@dataclass
class Finding:
    code: str
    severity: str  # error | warn | info
    message: str
    spots: list[str] = field(default_factory=list)
    hint: str = ""

    def to_json(self) -> dict:
        d = {"code": self.code, "severity": self.severity, "message": self.message,
             "spots": self.spots[:MAX_SPOTS]}
        if len(self.spots) > MAX_SPOTS:
            d["spots_truncated"] = len(self.spots) - MAX_SPOTS
        if self.hint:
            d["hint"] = self.hint
        return d

    def __str__(self) -> str:
        shown = " ".join(self.spots[:6])
        more = f" +{len(self.spots) - 6} more" if len(self.spots) > 6 else ""
        tail = f"\n          at {shown}{more}" if self.spots else ""
        head = f"[{self.severity:<5}] {self.code}: {self.message}"
        return head + tail + (f"\n          hint: {self.hint}" if self.hint else "")


def report(findings: list[Finding]) -> str:
    if not findings:
        return "clean - no findings"
    n = {s: sum(1 for f in findings if f.severity == s) for s in ("error", "warn", "info")}
    return (f"{n['error']} error, {n['warn']} warn, {n['info']} info\n"
            + "\n".join(str(f) for f in findings))


def summary(findings: list[Finding]) -> str:
    if not findings:
        return "clean"
    n = {s: sum(1 for f in findings if f.severity == s) for s in ("error", "warn", "info")}
    return f"{n['error']} error, {n['warn']} warn, {n['info']} info"


# --------------------------------------------------------------------------
# shared analysis
# --------------------------------------------------------------------------

def _spot(piece: Piece, tick: int, *extra: str) -> str:
    bar, beat = piece.position_of(tick)
    return f"{bar}:{float(beat):g}" + ("(" + ",".join(extra) + ")" if extra else "")


@dataclass
class Slice:
    """A stretch of time over which the set of sounding notes does not change."""
    start: int
    end: int
    notes: list[Note]

    def voice(self, name: str) -> list[Note]:
        return [n for n in self.notes if n.voice == name]


def sonorities(notes: list[Note]) -> list[Slice]:
    """Cut the timeline wherever anything starts or stops."""
    if not notes:
        return []
    bounds = sorted({n.start for n in notes} | {n.end for n in notes})
    active: list[Note] = []
    out: list[Slice] = []
    order = sorted(notes, key=lambda n: n.start)
    i = 0
    for a, b in zip(bounds, bounds[1:]):
        while i < len(order) and order[i].start <= a:
            active.append(order[i])
            i += 1
        active = [n for n in active if n.end > a]
        if active:
            out.append(Slice(a, b, list(active)))
    return out


def _monophonic_voices(piece: Piece, r: Render) -> set[str]:
    """Voices that only ever sound one note at a time.

    Voice-leading rules are about independent lines. Running them over a piano
    part playing block chords produces a torrent of technically-true findings
    that nobody wants, so those voices are simply excluded.
    """
    out = set()
    for v in piece.voices:
        notes = r.by_voice(v.name)
        if not notes:
            continue
        overlaps = sum(1 for a, b in zip(sorted(notes, key=lambda n: n.start),
                                         sorted(notes, key=lambda n: n.start)[1:])
                       if b.start < a.end - 1)
        if overlaps <= len(notes) * 0.05:
            out.add(v.name)
    return out


def _doubling_pairs(piece: Piece) -> set[frozenset[str]]:
    """Voice pairs where one is explicitly doubling the other.

    A ``double`` op is a deliberate request for parallel motion, so reporting
    the parallel octaves it produces would be reporting the feature as a bug.
    """
    pairs = set()
    for v in piece.voices:
        for op in v.ops:
            if op.kind == "double" and op.enabled:
                pairs.add(frozenset({v.name, op.params["source"]}))
    return pairs


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_structure(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    out: list[Finding] = []
    if not piece.sections:
        out.append(Finding("no_form", "error", "the piece has no sections",
                           hint="add_section('A', bars=8) -- a cue needs a shape "
                                "before it needs notes"))
    if not piece.harmony:
        out.append(Finding("no_harmony", "warn",
                           "no harmonic scaffold, so every degree resolves against the "
                           "key alone and chord-anchored motifs have nothing to fit",
                           hint="set_harmony([('1','i'), ('3','iv'), ('5','V7')])"))
    if not r.notes:
        out.append(Finding("silent", "error", "nothing sounds anywhere in the piece"))
        return out
    over = [n for n in r.notes if n.start >= piece.total_ticks]
    if over:
        out.append(Finding("overruns_form", "error",
                           f"{len(over)} note(s) start after the last bar of the form",
                           [_spot(piece, n.start, n.voice) for n in over[:MAX_SPOTS]],
                           hint="lengthen the final section, or move the op earlier"))
    for v in piece.voices:
        if not v.ops:
            out.append(Finding("orphan_voice", "info",
                               f"voice {v.name!r} ({v.instrument}) has no ops",
                               hint="give it something to play, or remove it"))
        elif not r.by_voice(v.name) and not v.muted:
            out.append(Finding("orphan_voice", "warn",
                               f"voice {v.name!r} has {len(v.ops)} op(s) but produces "
                               f"no notes",
                               hint="check the op positions land inside the form"))
    if st.max_voices and len(piece.voices) > st.max_voices:
        out.append(Finding("voice_budget", "warn",
                           f"{len(piece.voices)} voices, style {st.name!r} allows "
                           f"{st.max_voices}",
                           hint="merge two inner parts, or cut the one that only doubles"))
    if st.families:
        bad = [v.name for v in piece.voices if v.inst.family not in st.families]
        if bad:
            out.append(Finding("family_budget", "warn",
                               f"voices outside style {st.name!r}: {', '.join(bad)}",
                               hint=f"this style covers {list(st.families)}"))
    return out


def check_ranges(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    out: list[Finding] = []
    for v in piece.voices:
        notes = [n for n in r.by_voice(v.name) if not n.percussive]
        if not notes:
            continue
        inst = v.inst
        bad = [n for n in notes if not (inst.lo <= n.pitch <= inst.hi)]
        if bad:
            worst = min(bad, key=lambda n: min(abs(n.pitch - inst.lo), abs(n.pitch - inst.hi)))
            out.append(Finding(
                "range_violation", "error",
                f"{v.name} ({v.instrument}) has {len(bad)} note(s) outside its range "
                f"{inst.low}-{inst.high}; worst is "
                f"{spell_pitch(worst.pitch, piece.key)}",
                [_spot(piece, n.start, spell_pitch(n.pitch, piece.key)) for n in bad[:MAX_SPOTS]],
                hint="set octave= on the op, or move the line to an instrument that "
                     "reaches it"))
        if not st.check_tessitura:
            continue
        # A single note outside the sweet spot is expressive; a sustained run of
        # them is a line written in the wrong register, so only runs are reported.
        outside = [n for n in notes if not (inst.clo <= n.pitch <= inst.chi)]
        if len(outside) >= max(6, len(notes) * 0.4):
            where = "below" if mean(n.pitch for n in outside) < inst.clo else "above"
            out.append(Finding(
                "out_of_tessitura", "warn",
                f"{len(outside)} of {v.name}'s {len(notes)} notes sit {where} its "
                f"characteristic range ({inst.comfort_low}-{inst.comfort_high})",
                [_spot(piece, n.start, spell_pitch(n.pitch, piece.key)) for n in outside[:6]],
                hint=(inst.notes[0] if inst.notes else
                      "shift the part an octave, or give it to another instrument")))
    return out


def check_polyphony(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    out: list[Finding] = []
    slices = [s for s in sonorities(r.notes) if s.end - s.start >= MIN_MOMENT]
    for v in piece.voices:
        cap = v.inst.polyphony
        bad = [s for s in slices if len(s.voice(v.name)) > cap]
        if bad:
            worst = max(len(s.voice(v.name)) for s in bad)
            out.append(Finding(
                "polyphony_exceeded", "error",
                f"{v.name} ({v.instrument}) is asked for up to {worst} simultaneous "
                f"notes but can play {cap}",
                [_spot(piece, s.start) for s in bad[:MAX_SPOTS]],
                hint=("this instrument is monophonic -- split the chord across voices, "
                      "or arpeggiate it" if cap == 1 else
                      "thin the voicing, or move a tone to another voice")))
        if st.max_hand_span and cap > 2:
            wide = [s for s in bad or slices
                    if (ns := s.voice(v.name)) and len(ns) > 1
                    and max(n.pitch for n in ns) - min(n.pitch for n in ns) > st.max_hand_span]
            if wide:
                out.append(Finding(
                    "hand_span", "warn",
                    f"{v.name} spans more than {st.max_hand_span} semitones in one "
                    f"sonority at {len(wide)} place(s)",
                    [_spot(piece, s.start) for s in wide[:MAX_SPOTS]],
                    hint="one hand reaches a tenth; roll the chord or drop a tone"))
    thick = [s for s in slices if len(s.notes) > st.max_sonority]
    if thick:
        out.append(Finding(
            "density_overload", "warn",
            f"{len(thick)} moment(s) with more than {st.max_sonority} notes sounding "
            f"at once (peak {max(len(s.notes) for s in thick)})",
            [_spot(piece, s.start) for s in thick[:MAX_SPOTS]],
            hint="doubling at the octave reads as weight; doubling at the unison "
                 "just uses up players"))
    return out


def check_voice_leading(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """Parallel perfect intervals and sustained voice crossing.

    Only between two independent monophonic lines that are not explicitly
    doubling each other -- everywhere else the rule does not apply and firing it
    would be noise.
    """
    if not st.voice_leading:
        return []
    mono = _monophonic_voices(piece, r)
    skip = _doubling_pairs(piece)
    names = [v.name for v in piece.voices
             if v.name in mono and not v.inst.percussive and r.by_voice(v.name)]
    out: list[Finding] = []
    # Judge the written lines, not the decoration on them: a trill against a
    # held fifth is not a run of parallel fifths, and reporting it as one would
    # punish exactly the writing an ornament is for.
    slices = sonorities([n for n in r.notes if not n.ornament])
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if frozenset({a, b}) in skip:
                continue
            out += _parallels(piece, slices, a, b)
            out += _crossing(piece, slices, a, b, piece.get_voice(a), piece.get_voice(b))
    return out


def _line(slices: list[Slice], name: str) -> list[tuple[int, int | None]]:
    return [(s.start, ns[0].pitch if (ns := s.voice(name)) else None) for s in slices]


def _parallels(piece: Piece, slices, a: str, b: str) -> list[Finding]:
    la, lb = _line(slices, a), _line(slices, b)
    fifths, octaves = [], []
    prev = None
    for (t, pa), (_, pb) in zip(la, lb):
        if pa is None or pb is None:
            prev = None
            continue
        iv = abs(pa - pb) % 12
        if prev is not None:
            (ppa, ppb, piv) = prev
            moved = pa != ppa and pb != ppb
            similar = (pa - ppa) * (pb - ppb) > 0
            if moved and similar and iv == piv and iv in (0, 7):
                (octaves if iv == 0 else fifths).append(_spot(piece, t, a, b))
        prev = (pa, pb, iv)
    out = []
    if fifths:
        out.append(Finding(
            "parallel_fifths", "warn",
            f"{a} and {b} move in parallel fifths at {len(fifths)} place(s)",
            fifths, hint="contrary motion in one of the two, or reharmonize the second "
                         "chord so the fifth is not doubled"))
    if octaves:
        out.append(Finding(
            "parallel_octaves", "warn",
            f"{a} and {b} move in parallel octaves/unisons at {len(octaves)} place(s), "
            f"so they stop being two parts",
            octaves, hint="if the doubling is deliberate, say so with a `double` op and "
                          "this check will stand down"))
    return out


def _crossing(piece: Piece, slices, a: str, b: str, va, vb) -> list[Finding]:
    """Sustained crossing only. A single crossed note is a normal thing to write."""
    order = {"melody": 3, "counter": 2, "ornament": 3, "harmony": 1, "pad": 1,
             "bass": 0, "percussion": 0}
    if order.get(va.role, 1) == order.get(vb.role, 1):
        return []
    upper, lower = (a, b) if order.get(va.role, 1) > order.get(vb.role, 1) else (b, a)
    la, lb = dict(_line(slices, upper)), dict(_line(slices, lower))
    bad, total = [], 0
    for t, pu in la.items():
        pl = lb.get(t)
        if pu is None or pl is None:
            continue
        total += 1
        if pl > pu:
            bad.append(_spot(piece, t, upper, lower))
    if total and len(bad) > max(3, total * 0.15):
        return [Finding(
            "voice_crossing", "warn",
            f"{lower} sits above {upper} for {len(bad)} of {total} shared moments, "
            f"even though {upper} is the {piece.get_voice(upper).role} voice",
            bad[:MAX_SPOTS],
            hint="drop the lower part an octave, or swap what the two are doing")]
    return []


#: The lowest pitch at which each interval still reads as two notes rather than
#: a smear, following the standard orchestration tables. Keyed by interval, not
#: by register: a major second is fine at Eb3 and mud a fifth lower, while a
#: perfect fifth is fine almost to the bottom of the piano.
LOW_INTERVAL_LIMITS = {
    1: 52,   # m2 above E3
    2: 51,   # M2 above Eb3
    3: 48,   # m3 above C3
    4: 46,   # M3 above Bb2
    5: 41,   # P4 above F2
    7: 34,   # P5 above Bb1
    12: 28,  # octave above E1
}


def check_low_interval_limit(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    if not st.low_interval_limit:
        return []
    bad: list[str] = []
    worst = ""
    for s in sonorities(r.notes):
        if s.end - s.start < 120:      # shorter than a 16th: a passing collision
            continue
        pitches = sorted({n.pitch for n in s.notes if not n.percussive})
        for lo, hi in zip(pitches, pitches[1:]):
            gap = hi - lo
            if gap == 0 or gap > 12:
                continue          # unisons double, and nothing wider than an octave muds
            # The threshold for the widest tabulated interval this one covers, so a
            # tritone is judged by the fourth's limit rather than the fifth's.
            floor = LOW_INTERVAL_LIMITS[max(k for k in LOW_INTERVAL_LIMITS if k <= gap)]
            if lo < floor:
                bad.append(_spot(piece, s.start,
                                 f"{spell_pitch(lo, piece.key)}+{spell_pitch(hi, piece.key)}"))
                worst = worst or f"{spell_pitch(lo, piece.key)}/{spell_pitch(hi, piece.key)}"
                break
    if not bad:
        return []
    return [Finding(
        "low_interval_limit", "warn",
        f"{len(bad)} sonority/sonorities put a narrow interval too low to stay clear "
        f"(e.g. {worst})",
        bad[:MAX_SPOTS],
        hint="a third needs to be above C3 and a second above Eb3; lower than that, "
             "open the voicing upward rather than dropping the top note")]


def check_harmony(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    out: list[Finding] = []
    spans = piece.harmony_spans()
    if not spans:
        return out

    # Redundant flats: in a minor key the third, sixth and seventh are already
    # lowered, so 'bVII' asks for a doubly-flattened degree. Agents write this
    # constantly, meaning the subtonic, and get a chord a semitone below it.
    for h in piece.harmony:
        key = piece.key_at(piece.tick_of(h.at))
        num = h.chord.lstrip()
        if key.minorish and num.startswith("b"):
            body = num.lstrip("b#").rstrip("0123456789osu+%maj")
            if body.lower() in ("iii", "vi", "vii"):
                out.append(Finding(
                    "redundant_accidental", "warn",
                    f"{h.chord!r} at {h.at} in a minor key: the third, sixth and "
                    f"seventh are already lowered, so this asks for a further flat",
                    [f"{h.at}({h.chord})"],
                    hint=f"you almost certainly mean {num.lstrip('b')!r}"))

    if st.max_static_bars:
        for start, end, numeral in spans:
            # Measured in the bars of the section the chord starts in, so a 6/8
            # section is not judged in 4/4 bars borrowed from the opening.
            bars = (end - start) / piece.section_of_tick(start).bar_ticks
            if bars > st.max_static_bars:
                out.append(Finding(
                    "harmonic_stasis", "warn",
                    f"{numeral} lasts {bars:g} bars (style {st.name!r} expects a change "
                    f"within {st.max_static_bars})",
                    [_spot(piece, start, numeral)],
                    hint="an inversion or a passing chord keeps a long pedal moving "
                         "without changing the harmony"))

    if st.require_cadence and len(spans) >= 2 and not piece.loop:
        last = spans[-1][2]
        key = piece.key_at(spans[-1][0])
        try:
            resolves = parse_chord(last, key).root_offset == 0
        except (ValueError, KeyError):
            resolves = True
        if not resolves:
            out.append(Finding(
                "cadence_missing", "warn",
                f"the piece ends on {last}, not on the tonic",
                [_spot(piece, spans[-1][0], last)],
                hint="end V -> i; or, if this is game music that repeats, mark it "
                     "as a loop (update_piece loop=true) and this check stands down"))

    out += _clashes(piece, r)
    return out


def _clashes(piece: Piece, r: Render) -> list[Finding]:
    """Long, dissonant, unresolved non-chord tones.

    All three conditions matter. Passing tones are short, colour tones are
    consonant against what is actually sounding, and suspensions resolve by
    step -- so requiring all three is what keeps this check from firing on
    every expressive note ever written.
    """
    by_voice: dict[str, list[Note]] = {}
    for n in sorted(r.notes, key=lambda n: n.start):
        by_voice.setdefault(n.voice, []).append(n)
    slices = sonorities(r.notes)
    bad: list[str] = []
    for notes in by_voice.values():
        for i, n in enumerate(notes):
            if n.percussive or n.dur < 360:
                continue
            # A note that arrives a hair before the barline belongs to the chord
            # it is arriving on: a humanized downbeat is not an anticipation.
            chord, key = piece.chord_at(n.start + EARLY)
            if chord is None or n.pitch % 12 in chord.pitch_classes(key):
                continue
            nxt = notes[i + 1] if i + 1 < len(notes) else None
            if nxt is not None and abs(nxt.pitch - n.pitch) <= 2:
                continue          # resolves by step: a suspension or appoggiatura
            here = next((s for s in slices if s.start <= n.start < s.end), None)
            if here is None:
                continue
            others = {o.pitch for o in here.notes if o is not n and not o.percussive}
            harsh = any(abs(n.pitch - p) % 12 in (1, 11, 6) for p in others)
            if harsh:
                bad.append(_spot(piece, n.start,
                                 f"{n.voice}:{spell_pitch(n.pitch, key)}/{chord.numeral}"))
    if not bad:
        return []
    return [Finding(
        "chord_clash", "warn",
        f"{len(bad)} long note(s) sit outside the chord, grind against something "
        f"sounding, and never resolve",
        bad[:MAX_SPOTS],
        hint="resolve it down by step, shorten it to a passing tone, or change the "
             "chord underneath to admit it")]


def check_melody(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    out: list[Finding] = []
    for v in piece.voices:
        if v.role not in ("melody", "counter") or v.inst.percussive:
            continue
        notes = sorted(r.by_voice(v.name), key=lambda n: n.start)
        if len(notes) < 4:
            continue
        # Only leaps beyond an octave. A sixth or a seventh left hanging is
        # ordinary melodic writing and reporting it would be pedantry.
        leaps = []
        for a, b, c in zip(notes, notes[1:], notes[2:]):
            jump = b.pitch - a.pitch
            if abs(jump) <= 12:
                continue
            # Across a rest it is a new entry, not a leap: nobody hears the
            # interval between the end of one phrase and the start of the next.
            if b.start - a.end >= 480:
                continue
            recovers = (c.pitch - b.pitch) * jump < 0 and abs(c.pitch - b.pitch) <= 2
            if not recovers:
                leaps.append(_spot(piece, b.start,
                                   f"{v.name}:{abs(jump)}st"))
        if leaps:
            out.append(Finding(
                "unresolved_leap", "warn",
                f"{v.name} leaps more than an octave without stepping back at "
                f"{len(leaps)} place(s)",
                leaps[:MAX_SPOTS],
                hint="follow a big leap with a step in the opposite direction, or "
                     "fill it in -- motif.fill() does exactly that"))
        span = max(n.pitch for n in notes) - min(n.pitch for n in notes)
        if span <= 4 and len(notes) >= 16:
            out.append(Finding(
                "static_register", "warn",
                f"{v.name} covers only {span} semitones across {len(notes)} notes",
                [_spot(piece, notes[0].start, v.name)],
                hint="a melody needs somewhere to go; give the phrase a high point"))
    return out


def check_dynamics(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    if not st.min_dynamic_range or len(piece.sections) < 2 or not r.notes:
        return []
    levels = []
    for sec, _, tick in piece.section_bounds():
        here = [n.velocity for n in r.notes if tick <= n.start < tick + sec.length]
        if here:
            levels.append((sec.name, mean(here)))
    if len(levels) < 2:
        return []
    spread = max(v for _, v in levels) - min(v for _, v in levels)
    if spread >= st.min_dynamic_range:
        return []
    return [Finding(
        "flat_dynamics", "warn",
        f"every section averages within {spread:.0f} velocity of every other "
        f"({', '.join(f'{n} {v:.0f}' for n, v in levels)}) -- the piece has no arc",
        hint="give sections different dynamic= levels, or add a dynamics op with "
             "start= and end= to shape a crescendo into the climax")]


def check_material(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """Whether the piece is actually made of themes, and whether they develop."""
    out: list[Finding] = []
    if not piece.motifs:
        if r.notes:
            out.append(Finding(
                "no_motifs", "warn",
                "no motifs are defined, so nothing in the piece is thematic material "
                "the listener can be expected to recognize or you can develop",
                hint="add_motif('main', '0 2 4:1/4 3 2:1/2'), then play it -- a cue "
                     "without a theme is texture"))
        return out

    melodic = [n for n in r.notes
               if piece.get_voice(n.voice).role in ("melody", "counter")]
    if melodic and st.min_motif_coverage:
        share = sum(1 for n in melodic if n.motif) / len(melodic)
        if share < st.min_motif_coverage:
            out.append(Finding(
                "motif_starvation", "warn",
                f"only {share:.0%} of melodic notes come from a named motif "
                f"(style {st.name!r} expects {st.min_motif_coverage:.0%})",
                hint="material written with `phrase` is untracked connective tissue; "
                     "name the good bits as motifs so they can come back"))

    forms: dict[str, set[str]] = {}
    played: set[str] = set()
    for n in r.notes:
        if n.motif:
            forms.setdefault(n.motif, set()).add(n.form or "")
            if n.played:
                played.add(n.played)
    # A cell joined into a longer theme has been played, and has been developed:
    # building a period out of it is the development.
    for name in piece.heard_within(played | {f for fs in forms.values() for f in fs}):
        forms.setdefault(name, set()).add("joined")
    for name, seen in forms.items():
        if len(seen) == 1 and "" in seen and len(piece.sections) >= 3:
            out.append(Finding(
                "motif_never_developed", "info",
                f"motif {name!r} is only ever played exactly as written",
                hint="transform=['invert'] or ['augment:2'] on a later statement is "
                     "what turns a tune into a leitmotif"))
    for name in piece.motifs:
        if name not in forms and name not in played:
            out.append(Finding(
                "motif_unused", "info", f"motif {name!r} is defined but never played",
                hint="play it or remove it"))

    return out


def check_repetition(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """Sections that are literally the same music, bar for bar.

    Deliberately independent of the motif checks: a piece with no motifs at all
    is the one most likely to be built by pasting a section twice.
    """
    sigs: dict[tuple, list[str]] = {}
    for sec, _, tick in piece.section_bounds():
        sig = tuple(sorted((n.start - tick, n.pitch, n.dur, n.voice) for n in r.notes
                           if tick <= n.start < tick + sec.length))
        if sig:
            sigs.setdefault(sig, []).append(sec.name)
    return [Finding(
        "verbatim_repeat", "warn",
        f"sections {', '.join(names)} are note-for-note identical",
        hint="vary the return: reorchestrate it, change one voice, or state the theme "
             "inverted. An exact repeat is a copy, not a recapitulation")
        for names in sigs.values() if len(names) > 1]


def check_breathing(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """Whether anything ever stops. Players breathe, and textures need holes."""
    out: list[Finding] = []
    bar = piece.sections[0].bar_ticks if piece.sections else 1920
    for v in piece.voices:
        # A pad or a drone is *supposed* to be continuous, and a drummer does not
        # breathe. The finding only means something for a line meant to be heard
        # as a line, played by someone with lungs.
        if v.role in ("pad", "harmony", "percussion") or v.inst.percussive:
            continue
        if v.role not in ("melody", "counter") and v.inst.family not in (
                "winds", "brass", "voice"):
            continue
        notes = sorted(r.by_voice(v.name), key=lambda n: n.start)
        if len(notes) < 8:
            continue
        gaps = [b.start - a.end for a, b in zip(notes, notes[1:])]
        longest = max(gaps, default=0)
        covered = (notes[-1].end - notes[0].start)
        if longest < bar // 2 and covered > bar * 8:
            out.append(Finding(
                "never_rests", "info",
                f"{v.name} plays for {covered / bar:.0f} bars with no gap as long as "
                f"half a bar",
                hint="wind and brass players need to breathe, and a line that never "
                     "stops stops being heard. A `rest` op is a compositional choice"))
    return out


ACCOMPANIMENT_ROLES = ("harmony", "pad", "bass")


def check_masking(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """An accompaniment sitting just above the tune, so the tune is buried.

    The orchestral house note calls this the commonest scoring error, and it is
    one ``voice_crossing`` cannot see: that check only compares single lines,
    while the usual culprit is a pad or a block-chord part whose top note lands
    a third above the melody. Deliberately narrow -- the accompaniment must be
    above the melody *and within an octave of it* for most of the time they
    share, over at least two bars. A halo two octaves up does not mask, and a
    single crossed chord is ordinary writing.
    """
    mono = _monophonic_voices(piece, r)
    skip = _doubling_pairs(piece)
    melodies = [v for v in piece.voices
                if v.role == "melody" and not v.inst.percussive and r.by_voice(v.name)]
    if not melodies:
        return []
    slices = [s for s in sonorities(r.notes) if s.end - s.start >= MIN_MOMENT]
    # While a melody instrument is doubling someone else it is reinforcing
    # their line, usually an octave below it; the tune is the line on top, and
    # that voice is checked in its own right.
    doubling = {op.id for _, op in piece.all_ops() if op.kind == "double"}
    out: list[Finding] = []
    for m in melodies:
        for a in piece.voices:
            if (a.role not in ACCOMPANIMENT_ROLES or a.inst.percussive
                    or frozenset({m.name, a.name}) in skip
                    or (m.name in mono and a.name in mono)):   # voice_crossing's job
                continue
            shared = above = 0
            first = None
            for s in slices:
                mn, an = s.voice(m.name), s.voice(a.name)
                if not mn or not an or all(n.op in doubling for n in mn):
                    continue
                tune = max(n.pitch for n in mn)
                top = max(n.pitch for n in an)
                length = s.end - s.start
                shared += length
                if 0 < top - tune <= 12:
                    above += length
                    first = first if first is not None else s.start
            bar = piece.section_of_tick(first or 0).bar_ticks
            if shared >= 2 * bar and above > shared * 0.5:
                out.append(Finding(
                    "melody_buried", "warn",
                    f"{a.name} ({a.role}) sits just above the {m.name} melody for "
                    f"{above / shared:.0%} of the time they sound together, so the "
                    f"tune is covered by its own accompaniment",
                    [_spot(piece, first, a.name, m.name)],
                    hint=f"give {a.name} octave= one lower, or raise {m.name}; the "
                         f"melody wants an octave of clear space above the harmony"))
    return out


def check_untracked_quotes(piece: Piece, r: Render, st: StyleProfile) -> list[Finding]:
    """A ``phrase`` that restates a motif by hand, so the studio cannot see it.

    Retyping a theme is the exact failure the motif system exists to prevent:
    the notes sound right, but the motif map no longer knows the theme came
    back, and a later edit to the motif will silently skip this statement. Only
    near-exact restatements are reported (similarity >= 0.9 to the motif, its
    inversion or its retrograde, ignoring transposition and augmentation), so a
    phrase that merely shares a contour is left alone.
    """
    from .motif import parse_steps, similarity, Motif
    roots = [m for m in piece.motifs.values() if len(m.pitched) >= 4]
    if not roots:
        return []
    out: list[Finding] = []
    for v, op in piece.all_ops():
        if op.kind != "phrase" or not op.enabled:
            continue
        try:
            steps = parse_steps(op.params["steps"], op.params.get("unit") or "1/8")
        except (ValueError, KeyError):
            continue
        quote = Motif(op.id, steps)
        if len(quote.pitched) < 4:
            continue
        best = None
        for m in roots:
            for shape, label in ((m, []), (m.invert(), ["invert"]),
                                 (m.retrograde(), ["retrograde"])):
                if abs(len(shape.pitched) - len(quote.pitched)) > 1:
                    continue
                score = similarity(quote, shape)
                if score >= 0.9 and (best is None or score > best[0]):
                    best = (score, m.name, label)
        if best is None:
            continue
        score, name, label = best
        how = f", transform={label}" if label else ""
        out.append(Finding(
            "untracked_quote", "info",
            f"phrase {op.id!r} on {v.name} restates motif {name!r} by hand "
            f"(similarity {score:.2f}), so the motif map cannot see this statement",
            [f"{op.params.get('at')}({op.id})"],
            hint=f"replace it with a play op: motif={name!r}{how} -- add transpose= "
                 f"or a rhythmize transform if the shape was shifted"))
    return out


# --------------------------------------------------------------------------

CHECKS = (check_structure, check_ranges, check_polyphony, check_voice_leading,
          check_low_interval_limit, check_harmony, check_melody, check_dynamics,
          check_material, check_repetition, check_breathing, check_masking,
          check_untracked_quotes)


def lint(piece: Piece, rend: Render | None = None,
         style: StyleProfile | None = None) -> list[Finding]:
    """Run every check. Findings come back ordered error -> warn -> info."""
    r = rend if rend is not None else render(piece)
    st = style or get_style(piece.style)
    findings: list[Finding] = []
    for check in CHECKS:
        findings += check(piece, r, st)
    rank = {"error": 0, "warn": 1, "info": 2}
    return sorted(findings, key=lambda f: (rank[f.severity], f.code))
