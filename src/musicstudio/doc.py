"""The piece document: a form, a harmonic scaffold, and voices of named ops.

A piece is not a list of notes here. It is:

  * a **form** -- named sections with their own meter, tempo, key and dynamic,
  * a **harmonic scaffold** -- roman numerals on a timeline, and
  * **voices**, each an ordered log of named operations that place motifs
    against that scaffold.

Everything is addressable and everything re-renders. ``update_op('theme_a2',
transpose=2)`` moves one statement of a theme up a third and leaves the rest of
the score alone; nothing has to be re-emitted, and nothing downstream drifts.

The op vocabulary splits in two. *Generators* (``play``, ``chords``, ``bass``,
``groove``...) put notes on the timeline. *Modifiers* (``double``, ``dynamics``,
``articulate``, ``rest``) read what earlier ops produced and reshape it -- the
same layering that lets an outline op trace whatever ended up underneath it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from .ensemble import ROLES, get_instrument
from .motif import Motif, make_motif
from .theory import (
    Chord, Key, bar_ticks, beat_ticks, dynamic_velocity, parse_chord, parse_meter,
    parse_position, ticks,
)

SCHEMA_VERSION = 1


# --------------------------------------------------------------------------
# op schema
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class OpSpec:
    kind: str
    doc: str
    required: tuple[str, ...] = ()
    optional: dict[str, Any] = field(default_factory=dict)
    #: Generators add notes; modifiers reshape what earlier ops already added.
    modifier: bool = False


def _spec(kind, doc, required=(), *, modifier=False, **optional) -> OpSpec:
    return OpSpec(kind, doc, tuple(required), optional, modifier)


OP_SPECS: dict[str, OpSpec] = {
    s.kind: s for s in [
        _spec("play",
              "State a motif at a position. `transform` applies development ops on "
              "the way in (e.g. ['invert','augment:2']) while keeping the motif's "
              "identity, so the motif map still knows it is the same theme.",
              ["motif", "at"], transpose=0, octave=None, transform=None, times=1,
              every=None, dynamic=None, articulation=None, anchor=None),
        _spec("phrase",
              "Write degrees inline without naming a motif. The escape hatch for "
              "connective tissue -- if you find yourself reusing one, name it as a "
              "motif instead so it can be developed and tracked.",
              ["steps", "at"], unit="1/8", octave=None, transpose=0, dynamic=None,
              articulation=None, anchor="scale"),
        _spec("chords",
              "Realize the harmonic scaffold as a voicing. Voicings: block, pad, "
              "arpeggio_up, arpeggio_down, arpeggio_updown, broken, alberti. "
              "lead=True moves each chord to the nearest inversion of the next "
              "instead of jumping in root position -- use it for anything meant to "
              "sound played. spread opens the voicing; roll='1/32' strums it low to "
              "high; ring=True lets each note sound until the chord changes (harp, "
              "guitar, a pedalled piano); figure='0 2 1 2' or '0 1+2 1+2' writes "
              "your own pattern in chord-tone indices.",
              ["at", "bars"], voicing="block", rhythm=None, octave=None, tones=3,
              dynamic=None, spread=False, lead=False, ring=False, roll=None,
              figure=None, articulation=None),
        _spec("bass",
              "Realize the scaffold's bass line. Patterns: root, root_fifth, "
              "octaves, walking, pedal, ostinato.",
              ["at", "bars"], pattern="root", rhythm=None, octave=None,
              dynamic=None, degree=0, articulation=None),
        _spec("drone",
              "Hold one degree underneath everything. Ambient's load-bearing wall.",
              ["at", "bars"], degree=0, octave=None, dynamic=None, retrigger=None),
        _spec("groove",
              "An unpitched pattern on a grid. 'x' hits, 'X' accents, '.' rests, "
              "'|' is a barline for the reader. res sets the grid step.",
              ["at", "bars", "pattern"], res="1/16", dynamic=None),
        _spec("beat",
              "A whole drum pattern on a kit voice: one lane per drum, all on one "
              "grid. lanes is {'kick': 'x...x...', 'snare': '....x...', 'hat': "
              "'x.x.x.x.'} -- 'x' hit, 'X' accent, 'o' ghost note, '.' rest, '|' a "
              "barline for the reader. Lanes cycle independently, so a two-bar kick "
              "under a one-beat hat is two short strings. Drums: kick snare rim clap "
              "hat pedal open tom_lo tom_mid tom_hi ride bell crash splash tamb cow "
              "shaker. tune shifts the whole kit in semitones (a sped-up break is "
              "tune=3 to 7).",
              ["at", "bars", "lanes"], res="1/16", dynamic=None, tune=0),
        _spec("chop",
              "Cut what this voice plays into slices and re-order them -- how a "
              "break is chopped. slices is how many per bar; order names a source "
              "slice for each output slot and cycles: '0 1 2 3 2 2 6 7'. A slot may "
              "be '.' (silence), '_' (leave as written), '3*2' (the first half of "
              "slice 3, twice: a retrigger), '3*4' (a roll), '3r' (backwards), "
              "'3^5' (five semitones up), '3*8^0>12' (a roll that climbs an octave "
              "as it goes). Works on any voice, bass included.",
              ["from", "until", "order"], slices=8, modifier=True),
        _spec("filter",
              "Sweep a filter over this voice's sound: mode lowpass or highpass, "
              "from `start` Hz to `end` Hz across the span, resonance 0-1. The "
              "build-up and the drop. Audio only -- it shapes the built-in render "
              "and is not written to MIDI.",
              ["start"], end=None, mode="lowpass", resonance=0.0, modifier=True,
              **{"from": None, "until": None}),
        _spec("drive",
              "Saturate this voice: amount 0-1, from warmth to distortion. Audio "
              "only.", [], amount=0.4, modifier=True),
        _spec("compress",
              "Squash this voice's dynamics: everything above `threshold` (dB below "
              "its own peak) is reduced by `ratio`, and the result is brought back "
              "to the power it had -- denser, not louder. `makeup` adds dB on top. "
              "What makes a drum break sound like one slab instead of separate "
              "hits. Audio only.",
              [], ratio=4.0, threshold=-18.0, makeup=0.0, modifier=True),
        _spec("gain",
              "Turn this voice up or down by `db` after its other processing: the "
              "fader. Drive and compression change how loud a voice is as well as "
              "how it sounds, and this puts it back where the mix wants it. Audio "
              "only -- in a score, use dynamics.",
              ["db"], modifier=True),
        _spec("crush",
              "Reduce this voice's sample rate (rate, Hz) and bit depth (bits): the "
              "grit of an old sampler. Audio only.",
              [], rate=11025, bits=10, modifier=True),
        _spec("double",
              "Double another voice at an interval, reading whatever that voice "
              "ended up playing. `source` is the voice to follow; interval counts "
              "scale steps (2 = a third above); octaves shift by whole octaves.",
              ["source"], interval=0, octaves=0, dynamic=None, delay=None,
              **{"from": None, "until": None}),
        _spec("dynamics",
              "Shape what this voice already plays across a span: a crescendo, a "
              "diminuendo, or a flat level.",
              ["from", "until"], start=None, end=None, modifier=True),
        _spec("articulate",
              "Reshape note lengths and attacks over a span. Styles: legato, "
              "tenuto, staccato, marcato.",
              ["from", "until"], style="legato", modifier=True),
        _spec("humanize",
              "Deterministic micro-variation in timing and velocity. Seeded, so the "
              "render stays reproducible.",
              [], amount=0.4, timing=12, seed=0, modifier=True,
              **{"from": None, "until": None}),
        _spec("shape",
              "Phrase a line as a player would: swell toward each phrase's peak and "
              "taper its ending, lean on high notes and downbeats. amount scales it "
              "(0.5 is natural, 1.0 romantic); peak is where in the phrase it "
              "crests; breath is the rest that separates two phrases.",
              [], amount=0.5, peak=0.62, breath="1/4", modifier=True,
              **{"from": None, "until": None}),
        _spec("swing",
              "Delay the off-beat subdivisions so pairs play long-short. amount is "
              "the long note's share: 0.5 straight, 0.67 triplet swing.",
              [], amount=0.62, res="1/8", modifier=True,
              **{"from": None, "until": None}),
        _spec("events",
              "Raw note events as [pitch, start_tick, dur_tick, velocity]. The "
              "escape hatch for imported music: a recording cannot be expressed in "
              "degree space, so it arrives as absolute pitches. Everything else -- "
              "views, critique, export -- works on it unchanged.",
              ["events"], at=None, transpose=0),
        _spec("rest",
              "Silence this voice across a span, removing what earlier ops put "
              "there. Space is a compositional decision, so it gets to be an op.",
              ["from", "until"], modifier=True),
    ]
}


@dataclass
class Op:
    id: str
    kind: str
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        spec = OP_SPECS.get(self.kind)
        if spec is None:
            raise ValueError(f"unknown op kind {self.kind!r}; known: {sorted(OP_SPECS)}")
        missing = [r for r in spec.required if self.params.get(r) is None]
        if missing:
            raise ValueError(f"op {self.id!r} ({self.kind}) missing required: {missing}")
        unknown = set(self.params) - set(spec.required) - set(spec.optional)
        if unknown:
            raise ValueError(
                f"op {self.id!r} ({self.kind}) got unknown params {sorted(unknown)}; "
                f"accepted: {sorted(set(spec.required) | set(spec.optional))}")
        self.params = {**spec.optional, **self.params}

    @property
    def is_modifier(self) -> bool:
        return OP_SPECS[self.kind].modifier

    def to_json(self) -> dict:
        return {"id": self.id, "kind": self.kind, "enabled": self.enabled,
                "note": self.note, "params": self.params}

    @classmethod
    def from_json(cls, d: dict) -> Op:
        return cls(d["id"], d["kind"], dict(d.get("params", {})),
                   d.get("enabled", True), d.get("note", ""))


# --------------------------------------------------------------------------
# form
# --------------------------------------------------------------------------

@dataclass
class Section:
    """A span of bars with its own tempo, meter, key and dynamic level.

    Form is explicit because form is the thing OST writing lives or dies on, and
    because a section is the unit the critique pass reasons about: whether it
    states any known material, whether it contrasts with its neighbours, whether
    it ever gets quieter than the one before.
    """

    name: str
    bars: int = 8
    meter: str = "4/4"
    #: ``None`` means "whatever the piece is at". Only a section that actually
    #: changes tempo should state one -- otherwise retiming the piece would leave
    #: every section behind at its own stale marking.
    tempo: int | None = None
    key: str | None = None
    dynamic: str = "mf"
    note: str = ""
    #: Where the tempo has got to by the section's last bar: lower than ``tempo``
    #: is a ritardando, higher an accelerando. ``None`` holds the tempo steady.
    tempo_end: int | None = None

    def __post_init__(self) -> None:
        parse_meter(self.meter)
        if self.bars < 1:
            raise ValueError(f"section {self.name!r} needs at least one bar")
        if self.key:
            Key.parse(self.key)
        # Fail at the section, not three tool calls later inside a render.
        dynamic_velocity(self.dynamic)
        if self.tempo is not None and not 1 <= int(self.tempo) <= 400:
            raise ValueError(f"section {self.name!r}: tempo {self.tempo} is not a "
                             f"plausible marking")
        if self.tempo_end is not None and not 1 <= int(self.tempo_end) <= 400:
            raise ValueError(f"section {self.name!r}: tempo_end {self.tempo_end} is "
                             f"not a plausible marking")

    @property
    def bar_ticks(self) -> int:
        return bar_ticks(self.meter)

    @property
    def length(self) -> int:
        return self.bars * self.bar_ticks

    def to_json(self) -> dict:
        d = {"name": self.name, "bars": self.bars, "meter": self.meter,
             "tempo": self.tempo, "key": self.key, "dynamic": self.dynamic,
             "note": self.note}
        if self.tempo_end is not None:
            d["tempo_end"] = self.tempo_end
        return d

    @classmethod
    def from_json(cls, d: dict) -> Section:
        return cls(d["name"], d.get("bars", 8), d.get("meter", "4/4"),
                   d.get("tempo"), d.get("key"), d.get("dynamic", "mf"),
                   d.get("note", ""), d.get("tempo_end"))


@dataclass
class HarmonyEntry:
    """One chord on the scaffold, as a roman numeral in the key in force."""

    at: str
    chord: str
    dur: str | None = None
    note: str = ""

    def to_json(self) -> dict:
        return {"at": self.at, "chord": self.chord, "dur": self.dur, "note": self.note}

    @classmethod
    def from_json(cls, d: dict) -> HarmonyEntry:
        return cls(d["at"], d["chord"], d.get("dur"), d.get("note", ""))


@dataclass
class Voice:
    name: str
    instrument: str
    role: str = "melody"
    octave: int | None = None
    dynamic: str | None = None
    muted: bool = False
    ops: list[Op] = field(default_factory=list)
    #: Stereo position for the WAV render, -1 (left) .. 1 (right). ``None`` lets
    #: the renderer seat the voice by role, the way an orchestra is laid out.
    pan: float | None = None
    #: ``"soundfont"`` plays this voice from the installed SoundFont *inside*
    #: the built-in render, so it still gets drum tuning, filters, drive and
    #: the rest. ``None`` uses the instrument model. A sampled kit under the
    #: studio's own processing is how a break is made to sound like a break.
    engine: str | None = None

    def __post_init__(self) -> None:
        get_instrument(self.instrument)
        if self.engine not in (None, "soundfont"):
            raise ValueError(f"engine must be 'soundfont' or left unset, got "
                             f"{self.engine!r}")
        if self.role not in ROLES:
            raise ValueError(f"unknown role {self.role!r}; have {list(ROLES)}")
        if self.dynamic is not None:
            dynamic_velocity(self.dynamic)
        if self.pan is not None and not -1.0 <= float(self.pan) <= 1.0:
            raise ValueError(f"pan must be between -1 (left) and 1 (right), got {self.pan}")

    @property
    def inst(self):
        return get_instrument(self.instrument)

    def find(self, op_id: str) -> Op | None:
        return next((o for o in self.ops if o.id == op_id), None)

    def to_json(self) -> dict:
        d = {"name": self.name, "instrument": self.instrument, "role": self.role,
             "octave": self.octave, "dynamic": self.dynamic, "muted": self.muted,
             "ops": [o.to_json() for o in self.ops]}
        if self.pan is not None:
            d["pan"] = self.pan
        if self.engine:
            d["engine"] = self.engine
        return d

    @classmethod
    def from_json(cls, d: dict) -> Voice:
        return cls(d["name"], d["instrument"], d.get("role", "melody"), d.get("octave"),
                   d.get("dynamic"), d.get("muted", False),
                   [Op.from_json(o) for o in d.get("ops", [])], d.get("pan"),
                   d.get("engine"))


# --------------------------------------------------------------------------
# the piece
# --------------------------------------------------------------------------

class Piece:
    def __init__(self, name: str, key: str = "C major", *, tempo: int = 90,
                 meter: str = "4/4", style: str = "freeform", meta: dict | None = None,
                 loop: bool = False):
        self.name = name
        self.key = Key.parse(key)
        self.tempo = tempo
        self.meter = meter
        self.style = style
        self.meta = meta or {}
        #: A loop ends by leading back to its own start (game BGM, menu music),
        #: so it is not expected to close on the tonic.
        self.loop = loop
        self.sections: list[Section] = []
        self.harmony: list[HarmonyEntry] = []
        self.voices: list[Voice] = []
        self.motifs: dict[str, Motif] = {}

    # -- timeline ----------------------------------------------------------
    #
    # Bar numbers are global and 1-indexed: bar 1 is the first bar of the first
    # section, and they keep counting across section boundaries. Everything an
    # agent writes is in bars and beats; ticks exist only below this line.

    @property
    def total_bars(self) -> int:
        return sum(s.bars for s in self.sections)

    @property
    def total_ticks(self) -> int:
        return sum(s.length for s in self.sections)

    def section_bounds(self) -> list[tuple[Section, int, int]]:
        """``(section, first_bar, first_tick)`` for each section, in order."""
        out, bar, tick = [], 1, 0
        for s in self.sections:
            out.append((s, bar, tick))
            bar += s.bars
            tick += s.length
        return out

    def section_at_bar(self, bar: int) -> tuple[Section, int, int]:
        bounds = self.section_bounds()
        if not bounds:
            raise ValueError(
                f"{self.name!r} has no sections yet; add one before writing music "
                f"(a piece needs a form before it can have notes in it)")
        for sec, first, tick in bounds:
            if first <= bar < first + sec.bars:
                return sec, first, tick
        sec, first, tick = bounds[-1]
        return sec, first, tick

    def section_of_tick(self, tick: int) -> Section:
        for sec, _, start in self.section_bounds():
            if start <= tick < start + sec.length:
                return sec
        return self.sections[-1] if self.sections else Section("", 1, self.meter, self.tempo)

    def tick_of(self, pos: str | int) -> int:
        """Resolve ``'5:2.5'`` to absolute ticks through the meter map."""
        bar, beat = parse_position(pos)
        sec, first_bar, sec_tick = self.section_at_bar(bar)
        return (sec_tick + (bar - first_bar) * sec.bar_ticks
                + int((beat - 1) * beat_ticks(sec.meter)))

    def position_of(self, tick: int) -> tuple[int, Fraction]:
        """Ticks back to ``(bar, beat)``, for readbacks and findings."""
        for sec, first_bar, start in self.section_bounds():
            if start <= tick < start + sec.length:
                off = tick - start
                bar, within = divmod(off, sec.bar_ticks)
                return first_bar + bar, Fraction(within, beat_ticks(sec.meter)) + 1
        return self.total_bars, Fraction(1)

    def key_at(self, tick: int) -> Key:
        sec = self.section_of_tick(tick)
        return Key.parse(sec.key) if sec and sec.key else self.key

    def tempo_of(self, section: Section | None) -> int:
        """A section's tempo, falling back to the piece's own."""
        return (section.tempo if section is not None and section.tempo else self.tempo)

    def tempo_at(self, tick: int) -> int:
        return self.tempo_of(self.section_of_tick(tick))

    def tempo_map(self) -> list[tuple[int, float]]:
        """``(tick, bpm)`` marks covering the piece, in order.

        A steady section contributes one mark. A section with ``tempo_end``
        changes beat by beat, easing in -- most of a ritardando happens in its
        last bar, which is what makes it sound like arriving rather than like a
        tape slowing down. The WAV render and the MIDI export both read this,
        so they cannot disagree about how long the piece is.
        """
        marks: list[tuple[int, float]] = []
        for sec, _, start in self.section_bounds():
            bpm = float(self.tempo_of(sec))
            if sec.tempo_end is None or sec.tempo_end == bpm:
                marks.append((start, bpm))
                continue
            beat = beat_ticks(sec.meter)
            steps = max(1, sec.length // beat)
            for k in range(steps):
                t = k / max(1, steps - 1)
                marks.append((start + k * beat, bpm + (sec.tempo_end - bpm) * t ** 1.6))
        return marks or [(0, float(self.tempo))]

    # -- harmony -----------------------------------------------------------

    def harmony_spans(self) -> list[tuple[int, int, str]]:
        """``(start, end, numeral)`` spans covering the timeline, in order.

        An entry without an explicit duration runs until the next one, which is
        how a chord chart is actually written -- nobody annotates the length of
        every chord when the next one says where it ends.
        """
        if not self.harmony:
            return []
        # Asked for at every note of every render; the answer only changes when
        # the scaffold or the form does, so it is kept against exactly those.
        sig = (tuple((h.at, h.chord, h.dur) for h in self.harmony),
               tuple((s.bars, s.meter) for s in self.sections))
        cached = getattr(self, "_spans", None)
        if cached is not None and cached[0] == sig:
            return cached[1]
        out = self._harmony_spans()
        self._spans = (sig, out)
        return out

    def _harmony_spans(self) -> list[tuple[int, int, str]]:
        marks = sorted(((self.tick_of(h.at), h) for h in self.harmony), key=lambda t: t[0])
        end_of_piece = self.total_ticks
        out = []
        for i, (start, h) in enumerate(marks):
            if h.dur:
                end = start + ticks(h.dur)
            elif i + 1 < len(marks):
                end = marks[i + 1][0]
            else:
                end = end_of_piece
            out.append((start, max(end, start + 1), h.chord))
        return out

    def chord_at(self, tick: int) -> tuple[Chord, Key] | tuple[None, Key]:
        key = self.key_at(tick)
        for start, end, numeral in self.harmony_spans():
            if start <= tick < end:
                return parse_chord(numeral, key), key
        return None, key

    # -- structure ---------------------------------------------------------

    def get_section(self, name: str) -> Section:
        sec = next((s for s in self.sections if s.name == name), None)
        if sec is None:
            raise KeyError(f"no section {name!r}; have {[s.name for s in self.sections]}")
        return sec

    def section_bars(self, name: str) -> tuple[int, int]:
        """``(first_bar, last_bar)`` of a named section, both inclusive."""
        for sec, first, _ in self.section_bounds():
            if sec.name == name:
                return first, first + sec.bars - 1
        raise KeyError(f"no section {name!r}; have {[s.name for s in self.sections]}")

    def get_voice(self, name: str) -> Voice:
        v = next((v for v in self.voices if v.name == name), None)
        if v is None:
            raise KeyError(f"no voice {name!r}; have {[v.name for v in self.voices]}")
        return v

    def all_ops(self) -> list[tuple[Voice, Op]]:
        return [(v, op) for v in self.voices for op in v.ops]

    def find_op(self, op_id: str) -> tuple[Voice, Op]:
        for v in self.voices:
            op = v.find(op_id)
            if op is not None:
                return v, op
        raise KeyError(f"no op {op_id!r}; have {[o.id for _, o in self.all_ops()]}")

    def _unique_id(self, kind: str) -> str:
        used = {o.id for _, o in self.all_ops()}
        i = 1
        while f"{kind}_{i}" in used:
            i += 1
        return f"{kind}_{i}"

    def add_op(self, voice: str, kind: str, *, id: str | None = None,
               index: int | None = None, note: str = "", **params) -> Op:
        v = self.get_voice(voice)
        op_id = id or self._unique_id(kind)
        if any(o.id == op_id for _, o in self.all_ops()):
            raise ValueError(f"op id {op_id!r} already exists")
        params = {k: val for k, val in params.items()
                  if val is not None or k in OP_SPECS[kind].required}
        op = Op(op_id, kind, params, note=note)
        self._validate_op(op)
        v.ops.insert(len(v.ops) if index is None else index, op)
        return op

    def update_op(self, op_id: str, **params) -> Op:
        v, op = self.find_op(op_id)
        new = Op(op.id, op.kind, {**op.params, **params}, op.enabled, op.note)
        self._validate_op(new)
        v.ops[v.ops.index(op)] = new
        return new

    def move_op(self, op_id: str, bars: int = 0, beats: float = 0) -> Op:
        """Shift an op's position. The analogue of nudging a shape by a pixel."""
        v, op = self.find_op(op_id)
        key = "at" if "at" in op.params else "from"
        if op.params.get(key) is None:
            raise ValueError(f"op {op_id!r} ({op.kind}) has no position to move")
        params = {key: self._shifted(op.params[key], bars, beats)}
        if op.kind in ("dynamics", "articulate", "rest", "shape", "swing", "chop",
                       "filter") or "until" in op.params:
            if op.params.get("until") is not None:
                params["until"] = self._shifted(op.params["until"], bars, beats)
        return self.update_op(op_id, **params)

    def _shifted(self, pos: str | int, bars: int, beats: float) -> str:
        from .theory import format_position
        bar, beat = parse_position(pos)
        sec, _, _ = self.section_at_bar(bar)
        num, _ = parse_meter(sec.meter)
        total = Fraction(beat) + Fraction(str(beats))
        while total > num:
            total -= num
            bars += 1
        while total < 1:
            total += num
            bars -= 1
        return format_position(max(1, bar + bars), total)

    def remove_op(self, op_id: str) -> Op:
        v, op = self.find_op(op_id)
        v.ops.remove(op)
        return op

    def reorder_op(self, op_id: str, index: int, voice: str | None = None) -> Op:
        v, op = self.find_op(op_id)
        v.ops.remove(op)
        dest = self.get_voice(voice) if voice else v
        dest.ops.insert(max(0, min(index, len(dest.ops))), op)
        return op

    def _validate_op(self, op: Op) -> None:
        """Catch what would otherwise fail obscurely deep inside the render."""
        p = op.params
        if op.kind == "play" and p["motif"] not in self.motifs:
            raise KeyError(
                f"op {op.id!r} plays motif {p['motif']!r}, which does not exist; "
                f"have {sorted(self.motifs)}. Define it with add_motif first.")
        if op.kind == "double":
            self.get_voice(p["source"])
        for key in ("at", "from", "until"):
            if p.get(key) is not None:
                parse_position(p[key])
        if p.get("rhythm"):
            for d in str(p["rhythm"]).replace("|", " ").split():
                ticks(d)

    # -- motifs ------------------------------------------------------------

    def add_motif(self, name: str, source: str | list, **kw) -> Motif:
        if name in self.motifs:
            raise ValueError(f"motif {name!r} already exists; pick another name "
                             f"or derive from it instead")
        m = make_motif(name, source, **kw)
        self.motifs[name] = m
        return m

    def get_motif(self, name: str) -> Motif:
        try:
            return self.motifs[name]
        except KeyError:
            raise KeyError(f"no motif {name!r}; have {sorted(self.motifs)}") from None

    def heard_within(self, names) -> set[str]:
        """Motifs that sound as *part of* the given ones, through ``then``.

        A period built as ``call then rise then close`` plays all three, though
        only the period is ever named by an op. Follows joins through derived
        motifs too, so the cell a decorated variant came from counts as heard.
        ``names`` may be motif names or the ``+``-joined lineage a note carries.
        """
        out: set[str] = set()
        todo = [t for n in names for t in str(n).split("+")]
        todo += [t for n in names if n in self.motifs for t in self.motifs[n].lineage]
        while todo:
            tok = todo.pop()
            if not tok.startswith("then:"):
                continue
            name = tok[5:]
            m = self.motifs.get(name)
            if m is None or name in out:
                continue
            out.add(name)
            if m.derived_from:
                out.add(m.derived_from)
            todo += list(m.lineage)
        return out

    # -- persistence -------------------------------------------------------

    def to_json(self) -> dict:
        return {"schema": SCHEMA_VERSION, "name": self.name, "key": self.key.name,
                "tempo": self.tempo, "meter": self.meter, "style": self.style,
                "loop": self.loop, "meta": self.meta,
                "sections": [s.to_json() for s in self.sections],
                "harmony": [h.to_json() for h in self.harmony],
                "motifs": [m.to_json() for m in self.motifs.values()],
                "voices": [v.to_json() for v in self.voices]}

    @classmethod
    def from_json(cls, d: dict) -> Piece:
        if d.get("schema", 1) > SCHEMA_VERSION:
            raise ValueError(f"piece uses schema {d['schema']}, this build reads "
                             f"{SCHEMA_VERSION}")
        p = cls(d["name"], d.get("key", "C major"), tempo=d.get("tempo", 90),
                meter=d.get("meter", "4/4"), style=d.get("style", "freeform"),
                meta=d.get("meta", {}), loop=bool(d.get("loop", False)))
        p.sections = [Section.from_json(s) for s in d.get("sections", [])]
        p.harmony = [HarmonyEntry.from_json(h) for h in d.get("harmony", [])]
        p.motifs = {m["name"]: Motif.from_json(m) for m in d.get("motifs", [])}
        p.voices = [Voice.from_json(v) for v in d.get("voices", [])]
        return p

    def dumps(self) -> str:
        return json.dumps(self.to_json(), indent=2)

    def save(self, path: str | Path) -> Path:
        pth = Path(path)
        pth.parent.mkdir(parents=True, exist_ok=True)
        pth.write_text(self.dumps())
        return pth

    @classmethod
    def load(cls, path: str | Path) -> Piece:
        return cls.from_json(json.loads(Path(path).read_text()))
