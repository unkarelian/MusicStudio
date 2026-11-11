"""Evaluating the op-log into notes.

This is where degree space becomes pitch, and it is the file most easily got
subtly wrong, so a few decisions are worth stating plainly.

**Pitch is resolved at each note's own onset.** A motif is sampled against
whatever key and chord are in force at the moment each of its notes sounds, not
at the moment the phrase started. That is why one ``anchor='chord'`` figure can
run across a whole progression and fit every chord, and why moving a phrase two
bars later automatically reharmonizes it.

**Register is chosen, not assumed.** If an op does not name an octave, the
motif is placed in the octave that centres it in the instrument's comfortable
range. Agents pick octaves badly and the resulting music is unplayably high or
inaudibly low far more often than it is wrong in any other way.

**Ties join, they do not overlap.** A tied step absorbs the next step's
duration and sounds one note, which is what the notation means.

**Ornaments are degrees too.** A trill, a mordent or a grace note is written as
a mark on a step and realized here, each of its notes resolved against the key
at its own onset like any other. The written note keeps its onset and its end;
graces and runs take their time from the note *before*, as a player does. So
decorating a theme cannot move it, and cannot take it out of key.

**Chords can be led.** ``chords`` with ``lead=True`` picks, for every change of
harmony, the inversion nearest to where the hands already are. Stacking every
chord in root position makes all the voices jump in parallel at every change,
which is the surest way to make an accompaniment sound programmed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .doc import Op, Piece, Voice
from .ensemble import suggest_register
from .motif import Motif, Step, apply_transform, parse_ornament, parse_steps
from .theory import Chord, Key, beat_ticks, dynamic_velocity, ticks

#: ``(length ratio, velocity delta)``. The default leaves a sliver of silence so
#: that repeated notes retrigger instead of reading as one held note.
ARTICULATIONS: dict[str, tuple[float, int]] = {
    "legato": (1.0, -2),
    "normal": (0.92, 0),
    "tenuto": (0.98, 3),
    "staccato": (0.5, 2),
    "marcato": (0.65, 12),
    "portato": (0.75, 0),
}


#: Ops that shape the sound and leave the notes alone. ``audio.voice_fx`` reads
#: them; here they are deliberately nothing.
AUDIO_ONLY = ("filter", "drive", "compress", "crush", "gain", "eq", "duck", "cut", "tone")


@dataclass
class Note:
    """One sounding note, with the provenance that made it.

    ``motif`` and ``form`` are what let the analysis views answer "where does the
    hero theme come back, and in what shape" without guessing.
    """

    voice: str
    pitch: int
    start: int
    dur: int
    velocity: int
    op: str = ""
    #: The root theme, for grouping -- a derived motif reports its ancestor, so
    #: the motif map can say "hero, inverted" rather than listing two themes.
    motif: str | None = None
    #: The motif actually named by the op, which may be a derived one.
    played: str | None = None
    form: str = ""
    degree: int | None = None
    percussive: bool = False
    #: Joined to the note that follows, under one bow or one breath. The audio
    #: render glides into the next note instead of attacking it again.
    slur: bool = False
    #: Part of an ornament rather than the written line, so the critique pass
    #: can judge the line itself and not the decoration on it.
    ornament: bool = False
    #: Semitones a drum stroke is pitched away from itself: a break played
    #: faster comes out higher. Only the audio render can honour it.
    tune: float = 0.0
    #: The syllable sung on this note, as written, and as phonemes
    #: (``lyrics.Syllable.to_json``; ``-`` holds the previous vowel).
    lyric: str = ""
    sung: str = ""
    #: ``word#index/count`` -- which syllable of which word, for a voice bank.
    word: str = ""

    @property
    def end(self) -> int:
        return self.start + self.dur

    def to_json(self) -> dict:
        d = {"voice": self.voice, "pitch": self.pitch, "start": self.start,
             "dur": self.dur, "velocity": self.velocity, "op": self.op}
        if self.motif:
            d["motif"] = self.motif
            d["played"] = self.played
            if self.form:
                d["form"] = self.form
        return d


@dataclass
class Render:
    piece: Piece
    notes: list[Note] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def by_voice(self, name: str) -> list[Note]:
        return [n for n in self.notes if n.voice == name]

    @property
    def duration(self) -> int:
        return max((n.end for n in self.notes), default=self.piece.total_ticks)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def render(piece: Piece, *, upto: str | None = None) -> Render:
    """Evaluate every voice. ``upto`` stops after that op id, to see the build-up."""
    out = Render(piece)
    cache: dict[str, list[Note]] = {}
    for voice in piece.voices:
        _render_voice(piece, voice, cache, out, upto)
    out.notes = [n for v in piece.voices if not v.muted for n in cache.get(v.name, [])]
    out.notes.sort(key=lambda n: (n.start, n.pitch))
    return out


def _render_voice(piece: Piece, voice: Voice, cache: dict[str, list[Note]],
                  out: Render, upto: str | None, _stack: tuple[str, ...] = ()) -> list[Note]:
    if voice.name in cache:
        return cache[voice.name]
    if voice.name in _stack:
        raise ValueError(f"voices double each other in a cycle: {' -> '.join(_stack + (voice.name,))}")
    notes: list[Note] = []
    for op in voice.ops:
        if op.enabled:
            try:
                notes = _apply(piece, voice, op, notes, cache, out, _stack)
            except (KeyError, ValueError) as exc:
                raise type(exc)(f"op {op.id!r} ({op.kind}) on voice {voice.name!r}: {exc}") from None
        if upto is not None and op.id == upto:
            break
    notes.sort(key=lambda n: (n.start, n.pitch))
    cache[voice.name] = notes
    return notes


def _apply(piece, voice, op, notes, cache, out, stack) -> list[Note]:
    k = op.kind
    if k == "play":
        return notes + _op_play(piece, voice, op)
    if k == "phrase":
        return notes + _op_phrase(piece, voice, op)
    if k == "chords":
        return notes + _op_chords(piece, voice, op)
    if k == "bass":
        return notes + _op_bass(piece, voice, op)
    if k == "drone":
        return notes + _op_drone(piece, voice, op)
    if k == "groove":
        return notes + _op_groove(piece, voice, op)
    if k == "beat":
        return notes + _op_beat(piece, voice, op)
    if k == "lyrics":
        return _op_lyrics(piece, voice, op, notes, out)
    if k == "chop":
        return _op_chop(piece, voice, op, notes)
    if k in AUDIO_ONLY:
        return notes
    if k == "events":
        return notes + _op_events(piece, voice, op)
    if k == "double":
        return notes + _op_double(piece, voice, op, cache, out, stack)
    if k == "dynamics":
        return _op_dynamics(piece, voice, op, notes)
    if k == "articulate":
        return _op_articulate(piece, voice, op, notes)
    if k == "humanize":
        return _op_humanize(piece, voice, op, notes)
    if k == "shape":
        return _op_shape(piece, voice, op, notes)
    if k == "swing":
        return _op_swing(piece, voice, op, notes)
    if k == "rest":
        lo, hi = _span(piece, op, "from", "until")
        return [n for n in notes if not (lo <= n.start < hi)]
    raise ValueError(f"unhandled op kind {k!r}")  # pragma: no cover


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _span(piece: Piece, op: Op, a: str = "at", b: str = "until") -> tuple[int, int]:
    start = piece.tick_of(op.params[a]) if op.params.get(a) is not None else 0
    if op.params.get(b) is not None:
        end = piece.tick_of(op.params[b])
    elif op.params.get("bars") is not None:
        sec = piece.section_of_tick(start)
        end = start + int(op.params["bars"]) * sec.bar_ticks
    else:
        end = piece.total_ticks
    return start, max(end, start)


def _velocity(piece: Piece, voice: Voice, op: Op, tick: int, accent: int = 0) -> int:
    """Op dynamic beats voice dynamic beats the section's own level."""
    name = op.params.get("dynamic") or voice.dynamic
    if not name:
        sec = piece.section_of_tick(tick)
        name = sec.dynamic if sec else "mf"
    return max(1, min(127, dynamic_velocity(name) + accent * 11))


def _articulation(op: Op, default: str = "normal") -> tuple[float, int]:
    return ARTICULATIONS.get(op.params.get("articulation") or default,
                             ARTICULATIONS[default])


def _auto_octave(piece: Piece, voice: Voice, motif_or_degrees, transpose: int,
                 anchor: str) -> int:
    """Pick the octave that centres this material in the instrument's tessitura.

    Tried in preference order rather than computed in closed form because the
    mapping from degree to pitch depends on the key and the anchor, and a loop
    over eight octaves is both exact and obviously correct.
    """
    if voice.octave is not None:
        return voice.octave
    degs = [d for d in motif_or_degrees if d is not None]
    if not degs:
        return 4
    mean = sum(degs) / len(degs) + transpose
    key = piece.key
    target = voice.inst.centre
    best, best_err = 4, 10 ** 9
    for octv in range(0, 9):
        pitch = (key.pitch(int(round(mean)), 0, octv) if anchor == "scale"
                 else 12 * (octv + 1) + key.tonic + int(round(mean)) * 2)
        err = abs(pitch - target)
        if err < best_err:
            best, best_err = octv, err
    return best


def _pitch_of(piece: Piece, step: Step, tick: int, octave: int, transpose: int,
              anchor: str, scale: str | None) -> int | None:
    """Degree -> pitch, sampled against the harmony in force at ``tick``."""
    chord, key = piece.chord_at(tick)
    if scale:
        key = Key(key.tonic, scale)
    deg = step.deg + transpose
    if anchor == "chord":
        if chord is None:
            return key.pitch(deg, step.alt, octave)
        return chord.tone(key, deg, octave) + step.alt
    return key.pitch(deg, step.alt, octave)


def _emit_steps(piece: Piece, voice: Voice, op: Op, steps, start: int, octave: int,
                transpose: int, anchor: str, scale: str | None,
                motif: str | None = None, form: str = "", played: str | None = None,
                default_art: str = "normal") -> list[Note]:
    """Walk a run of steps onto the timeline. Ties absorb the following step."""
    op_art = op.params.get("articulation") or default_art
    notes: list[Note] = []
    tick = start
    i = 0
    while i < len(steps):
        s = steps[i]
        dur = s.dur
        # A tie means one note, not two -- swallow the next step's time.
        while s.tie and i + 1 < len(steps):
            i += 1
            dur += steps[i].dur
            s = replace(s, tie=steps[i].tie)
        if not s.is_rest:
            art = s.art or op_art
            ratio, vel_delta = ARTICULATIONS.get(art, ARTICULATIONS[default_art])
            vel = _velocity(piece, voice, op, tick, s.accent) + vel_delta
            sounding = max(1, int(dur * ratio))

            def emit(deg_off: int, at: int, length: int, v: int, *, orn: bool,
                     slur: bool, _s=s) -> None:
                step = _s if not deg_off else replace(_s, deg=_s.deg + deg_off, alt=0)
                pitch = _pitch_of(piece, step, max(0, at), octave, transpose, anchor, scale)
                if pitch is not None:
                    notes.append(Note(
                        voice.name, pitch, max(0, at), max(1, length),
                        max(1, min(127, v)), op.id, motif, played, form, step.deg,
                        slur=slur, ornament=orn))

            figure = _ornament(s.orn, tick, sounding) if s.orn else None
            if not figure:
                emit(0, tick, sounding, vel, orn=False, slur=art == "legato")
            else:
                lead_in = min((at for _, at, _, _ in figure), default=tick)
                if lead_in < tick:
                    # Graces borrow from the note before, as a player's do.
                    for k, prev in enumerate(notes):
                        if prev.start < lead_in < prev.end:
                            notes[k] = replace(prev, dur=lead_in - prev.start, slur=True)
                for off, at, length, main in figure:
                    emit(off, at, length, vel if main else vel - 7, orn=not main,
                         slur=(not main) or art == "legato")
        tick += dur
        i += 1
    return notes


#: A 32nd note: the speed of a trill and of a grace note.
_ORN_UNIT = 60


def _ornament(mark: str, tick: int, sounding: int) -> list[tuple[int, int, int, bool]] | None:
    """Realize an ornament as ``(degree offset, onset, length, is_main)`` notes.

    Returns ``None`` when the note is too short to decorate, which leaves it
    plain rather than squeezing a figure into a value that cannot hold one.
    The written note always starts on its own beat and ends where it would
    have ended, so nothing after it moves.
    """
    kind, n = parse_ornament(mark)
    u = _ORN_UNIT
    if kind == "gr":
        return [(n or -1, tick - u, u, False), (0, tick, sounding, True)]
    if kind == "run":
        n = n or -3
        step = 1 if n < 0 else -1
        offs = list(range(n, 0, step))
        return ([(o, tick - (len(offs) - k) * u, u, False) for k, o in enumerate(offs)]
                + [(0, tick, sounding, True)])
    if kind in ("mord", "lmord"):
        if sounding < 4 * u:
            u = sounding // 4
        if u < 20:
            return None
        nb = 1 if kind == "mord" else -1
        return [(0, tick, u, False), (nb, tick + u, u, False),
                (0, tick + 2 * u, sounding - 2 * u, True)]
    if kind == "turn":
        if sounding < 6 * u:
            return None
        return [(1, tick, u, False), (0, tick + u, u, False), (-1, tick + 2 * u, u, False),
                (0, tick + 3 * u, sounding - 3 * u, True)]
    if kind == "tr":
        if sounding < 6 * u:
            return _ornament("mord", tick, sounding)
        # Trill for most of the note, then settle on it: a trill that runs to
        # the very end has no arrival, and the arrival is what a trill is for.
        pairs = max(2, min((sounding * 2 // 3) // (2 * u), 12))
        out = []
        for k in range(pairs):
            out.append((0, tick + 2 * k * u, u, False))
            out.append((1, tick + (2 * k + 1) * u, u, False))
        out.append((0, tick + 2 * pairs * u, sounding - 2 * pairs * u, True))
        return out
    return None


def _resolved_motif(piece: Piece, op: Op) -> tuple[Motif, str]:
    """The motif an op plays, after any inline development, plus a form label."""
    m = piece.get_motif(op.params["motif"])
    for t in op.params.get("transform") or []:
        m = (apply_transform(m, t, resolve=piece.get_motif) if isinstance(t, str)
             else apply_transform(m, resolve=piece.get_motif, **t))
    return m, "+".join(m.lineage)


# --------------------------------------------------------------------------
# generators
# --------------------------------------------------------------------------

def _op_play(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    m, form = _resolved_motif(piece, op)
    start = piece.tick_of(op.params["at"])
    transpose = int(op.params.get("transpose") or 0)
    anchor = op.params.get("anchor") or m.anchor
    octave = (op.params.get("octave")
              if op.params.get("octave") is not None
              else _auto_octave(piece, voice, [s.deg for s in m.steps], transpose, anchor))
    every = ticks(op.params["every"]) if op.params.get("every") else m.duration
    notes: list[Note] = []
    for rep in range(max(1, int(op.params.get("times") or 1))):
        notes += _emit_steps(piece, voice, op, m.steps, start + rep * every, octave,
                             transpose, anchor, m.scale, m.root, form,
                             op.params["motif"])
    return notes


def _op_phrase(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    steps = parse_steps(op.params["steps"], op.params.get("unit") or "1/8")
    start = piece.tick_of(op.params["at"])
    transpose = int(op.params.get("transpose") or 0)
    anchor = op.params.get("anchor") or "scale"
    octave = (op.params.get("octave") if op.params.get("octave") is not None
              else _auto_octave(piece, voice, [s.deg for s in steps], transpose, anchor))
    return _emit_steps(piece, voice, op, steps, start, octave, transpose, anchor, None)


def _register(piece: Piece, voice: Voice, op: Op, default_shift: int = 0) -> int:
    """The octave a chordal/bass op starts from, honouring what the voice is for.

    A cello marked ``role='bass'`` should not be handed the same register as a
    cello marked ``role='melody'``; taking the middle of the instrument for both
    is how accompaniments end up sitting on top of the tune.
    """
    if op.params.get("octave") is not None:
        return int(op.params["octave"])
    if voice.octave is not None:
        return voice.octave
    lo, hi = suggest_register(voice.inst, voice.role)
    anchor = lo if voice.role in ("bass", "percussion") else (lo + hi) // 2
    return anchor // 12 - 1 + default_shift


def _rhythm_ticks(op: Op, fallback: int) -> list[int]:
    r = op.params.get("rhythm")
    if not r:
        return [fallback]
    return [ticks(d) for d in str(r).replace("|", " ").split()]


def _op_chords(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    start, end = _span(piece, op)
    octave = _register(piece, voice, op)
    tones = max(2, int(op.params.get("tones") or 3))
    voicing = op.params.get("voicing") or "block"
    ratio, vel_delta = _articulation(op, "legato" if voicing == "pad" else "normal")
    lead = bool(op.params.get("lead"))
    ring = bool(op.params.get("ring"))
    roll = ticks(op.params["roll"]) if op.params.get("roll") else 0
    figure = _parse_figure(op.params.get("figure"))
    notes: list[Note] = []
    prev: list[int] | None = None
    for s_start, s_end, numeral in piece.harmony_spans():
        lo, hi = max(s_start, start), min(s_end, end)
        if lo >= hi:
            continue
        chord, key = piece.chord_at(lo)
        if chord is None:
            continue
        pitches = [chord.tone(key, i + chord.inversion, octave) for i in range(tones)]
        if lead and prev is not None:
            pitches = _nearest_voicing(pitches, prev)
        prev = list(pitches)
        if op.params.get("spread") and len(pitches) >= 3:
            # Open position: the third goes up an octave, so the chord breathes
            # instead of sitting in one fist.
            pitches = sorted([pitches[0]] + pitches[2:] + [pitches[1] + 12])
        if voicing == "pad" and figure is None:
            for k, p in enumerate(pitches):
                at = min(lo + k * roll, hi - 1)
                notes.append(Note(voice.name, p, at, max(1, int((hi - at) * ratio)),
                                  _velocity(piece, voice, op, lo) + vel_delta, op.id,
                                  slur=True))
            continue
        pattern = _rhythm_ticks(op, beat_ticks(piece.section_of_tick(lo).meter))
        seq = figure if figure is not None else _voicing_sequence(voicing, pitches)
        tick, i = lo, 0
        while tick < hi:
            dur = pattern[i % len(pattern)]
            group = seq[i % len(seq)]
            if figure is not None:
                group = [_figure_pitch(pitches, k) for k in group]
            for k, p in enumerate(group):
                at = min(tick + k * roll, hi - 1)
                length = (hi - at) if ring else min(dur, hi - tick) - (at - tick)
                notes.append(Note(voice.name, p, at, max(1, int(length * ratio)),
                                  _velocity(piece, voice, op, tick) + vel_delta, op.id))
            tick += dur
            i += 1
    if ring:
        notes = _stop_restruck(notes)
    return notes


def _nearest_voicing(pitches: list[int], prev: list[int]) -> list[int]:
    """The same chord tones, turned to whichever inversion is closest to the
    last chord played.

    Candidates are the rotations of the voicing across three octaves; the cost
    is how far the hands move, plus a pull back toward the register the op
    asked for so that a long progression cannot drift up or down the keyboard
    one step at a time. Only the arrangement changes -- the tones sounded are
    exactly the ones the unled voicing would sound.
    """
    home = sum(pitches) / len(pitches)
    best, best_cost = pitches, None
    for shift in (-12, 0, 12):
        for turn in range(len(pitches)):
            cand = sorted([p + shift for p in pitches[turn:]]
                          + [p + shift + 12 for p in pitches[:turn]])
            move = (sum(abs(a - b) for a, b in zip(cand, prev)) if len(cand) == len(prev)
                    else abs(sum(cand) / len(cand) - sum(prev) / len(prev)) * len(cand))
            cost = move + 0.6 * abs(sum(cand) / len(cand) - home)
            if best_cost is None or cost < best_cost:
                best, best_cost = cand, cost
    return best


def _parse_figure(source) -> list[list[int | None]] | None:
    """``'0 2 1 2'`` or ``'0 1+2 1+2'``: chord-tone indices, low to high.

    ``+`` strikes tones together and ``.`` is a rest, so an oom-pah-pah is
    ``'0 1+2 1+2'`` and an Alberti bass is ``'0 2 1 2'``. Indices past the top of
    the voicing carry on up the chord into the next octave.
    """
    if not source:
        return None
    out: list[list[int]] = []
    for tok in str(source).replace("|", " ").split():
        if tok in (".", "r"):
            out.append([])
            continue
        try:
            out.append([int(t) for t in tok.split("+")])
        except ValueError:
            raise ValueError(
                f"bad figure token {tok!r}; a figure is chord-tone indices like "
                f"'0 2 1 2', with '+' for tones struck together ('0 1+2 1+2') and "
                f"'.' for a rest") from None
    if not any(out):
        raise ValueError("figure has no notes in it")
    return out


def _figure_pitch(pitches: list[int], index: int) -> int:
    octv, i = divmod(index, len(pitches))
    return pitches[i] + 12 * octv


def _stop_restruck(notes: list[Note]) -> list[Note]:
    """A ringing string struck again starts over; it does not sound twice."""
    last: dict[int, int] = {}
    out = sorted(notes, key=lambda n: n.start)
    for i, n in enumerate(out):
        j = last.get(n.pitch)
        if j is not None and out[j].end > n.start:
            out[j] = replace(out[j], dur=max(1, n.start - out[j].start))
        last[n.pitch] = i
    return out


def _voicing_sequence(voicing: str, pitches: list[int]) -> list[list[int]]:
    """A voicing is a cycle of note-groups; the rhythm decides how fast it turns."""
    if voicing in ("block", "pad"):
        return [pitches]
    if voicing == "arpeggio_up":
        return [[p] for p in pitches]
    if voicing == "arpeggio_down":
        return [[p] for p in reversed(pitches)]
    if voicing == "arpeggio_updown":
        return [[p] for p in pitches + pitches[-2:0:-1]]
    if voicing == "broken":
        return [[pitches[0]], pitches[1:]] if len(pitches) > 1 else [pitches]
    if voicing == "alberti":
        # low - high - middle - high, the classical accompaniment figure.
        if len(pitches) < 3:
            return [[p] for p in pitches]
        lo, mid, hi = pitches[0], pitches[1], pitches[2]
        return [[lo], [hi], [mid], [hi]]
    raise ValueError(f"unknown voicing {voicing!r}; have block, pad, arpeggio_up, "
                     f"arpeggio_down, arpeggio_updown, broken, alberti")


def _op_bass(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    start, end = _span(piece, op)
    octave = _register(piece, voice, op, default_shift=0)
    pattern = op.params.get("pattern") or "root"
    ratio, vel_delta = _articulation(op, "normal")
    spans = [(a, b, c) for a, b, c in piece.harmony_spans() if b > start and a < end]
    notes: list[Note] = []
    for idx, (s_start, s_end, numeral) in enumerate(spans):
        lo, hi = max(s_start, start), min(s_end, end)
        chord, key = piece.chord_at(lo)
        if chord is None:
            continue
        root = chord.bass_pitch(key, octave)
        beat = beat_ticks(piece.section_of_tick(lo).meter)
        if pattern == "pedal":
            notes.append(Note(voice.name, root, lo, hi - lo,
                              _velocity(piece, voice, op, lo), op.id))
            continue
        if pattern == "walking":
            nxt = spans[idx + 1] if idx + 1 < len(spans) else None
            target = (piece.chord_at(nxt[0])[0].bass_pitch(key, octave)
                      if nxt and piece.chord_at(nxt[0])[0] else root)
            seq = _walk(chord, key, octave, root, target, max(1, (hi - lo) // beat))
        elif pattern == "root_fifth":
            seq = [root, chord.tone(key, 2, octave)]
        elif pattern == "octaves":
            seq = [root, root + 12]
        elif pattern == "ostinato":
            seq = [root, chord.tone(key, 2, octave), root + 12, chord.tone(key, 2, octave)]
        else:
            seq = [root]
        durs = _rhythm_ticks(op, beat)
        tick, i = lo, 0
        while tick < hi:
            dur = durs[i % len(durs)]
            notes.append(Note(voice.name, seq[i % len(seq)], tick,
                              max(1, int(min(dur, hi - tick) * ratio)),
                              _velocity(piece, voice, op, tick) + vel_delta, op.id))
            tick += dur
            i += 1
    return notes


def _walk(chord: Chord, key: Key, octave: int, root: int, target: int, count: int) -> list[int]:
    """A walking bass: chord tones, then approach the next root by step."""
    if count <= 1:
        return [root]
    tones = [chord.tone(key, i, octave) for i in range(chord.size)]
    line = [root] + [t for t in tones[1:] if t != root]
    while len(line) < count:
        line.append(tones[len(line) % len(tones)] + 12 * (len(line) // max(1, len(tones))))
    line = line[:count]
    if count >= 2 and target != root:
        line[-1] = target - 1 if target > line[-2] else target + 1
    return line


def _op_drone(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    start, end = _span(piece, op)
    octave = _register(piece, voice, op)
    key = piece.key
    pitch = key.pitch(int(op.params.get("degree") or 0), 0, octave)
    if not op.params.get("retrigger"):
        return [Note(voice.name, pitch, start, end - start,
                     _velocity(piece, voice, op, start), op.id)]
    step = ticks(op.params["retrigger"])
    return [Note(voice.name, pitch, t, min(step, end - t),
                 _velocity(piece, voice, op, t), op.id)
            for t in range(start, end, step)]


def _op_groove(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    start, end = _span(piece, op)
    grid = ticks(op.params.get("res") or "1/16")
    pattern = str(op.params["pattern"]).replace("|", "").replace(" ", "")
    if not pattern:
        raise ValueError("groove pattern is empty; use 'x' for a hit, '.' for a rest")
    bad = set(pattern) - set("xX.-oO")
    if bad:
        raise ValueError(f"groove pattern has unknown characters {sorted(bad)}; "
                         f"use 'x' hit, 'X' accent, 'o' ghost, '.' rest")
    inst = voice.inst
    pitch = inst.drum_key if inst.drum_key is not None else inst.centre
    from .ensemble import is_kit
    if is_kit(voice.instrument):
        raise ValueError(f"{voice.name!r} is a kit: write it with `beat`, which "
                         f"takes one lane per drum, rather than `groove`")
    notes: list[Note] = []
    tick, i = start, 0
    while tick < end:
        ch = pattern[i % len(pattern)]
        if ch in "xXoO":
            accent = 1 if ch == "X" else -1 if ch in "oO" else 0
            notes.append(Note(voice.name, pitch, tick, grid,
                              _velocity(piece, voice, op, tick, accent), op.id,
                              percussive=True))
        tick += grid
        i += 1
    return notes


def _op_lyrics(piece: Piece, voice: Voice, op: Op, notes: list[Note], out) -> list[Note]:
    """Give the notes in a span one syllable each, in order.

    The words are a property of the notes, not a separate track: move a note
    and its syllable moves with it, and a note added in the middle of the line
    pushes the later syllables along, which is what a singer would do.
    """
    from .lyrics import parse
    lo, hi = _span(piece, op, "from", "until")
    if op.params.get("from") is None:
        lo, hi = 0, piece.total_ticks
    syllables, warnings = parse(str(op.params["text"]), op.params.get("lang") or "auto",
                                op.params.get("said"))
    for w in warnings:
        out.warnings.append(f"{voice.name}/{op.id}: {w}")
    inside = sorted((n for n in notes if lo <= n.start < hi and not n.ornament
                     and not n.percussive), key=lambda n: (n.start, n.pitch))
    # One syllable per onset: a chord sings one word.
    onsets = sorted({n.start for n in inside})
    if len(syllables) > len(onsets):
        out.warnings.append(
            f"{voice.name}/{op.id}: {len(syllables)} syllables for {len(onsets)} "
            f"notes; the last {len(syllables) - len(onsets)} are not sung "
            f"(from {syllables[len(onsets)].text!r})")
    elif len(syllables) < len(onsets):
        out.warnings.append(
            f"{voice.name}/{op.id}: {len(onsets)} notes for {len(syllables)} "
            f"syllables; the last {len(onsets) - len(syllables)} notes are sung "
            f"on 'ah'. Use '-' to hold a syllable over more notes.")
    words = {t: s for t, s in zip(onsets, syllables)}
    def tag(s) -> str:
        return f"{s.word}#{s.index}/{s.count}" if s.word else ""

    return [replace(n, lyric=words[n.start].text, sung=words[n.start].to_json(),
                    word=tag(words[n.start]))
            if n.start in words and lo <= n.start < hi and not n.ornament else n
            for n in notes]


def _op_beat(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    """A kit pattern: every lane is one drum on the same grid."""
    from .ensemble import KIT_DRUMS, is_kit
    if not is_kit(voice.instrument):
        raise ValueError(
            f"beat writes a whole kit, and {voice.name!r} is a {voice.instrument}; "
            f"give the voice a kit instrument (kit, kit_808, kit_jazz ...), or use "
            f"`groove` for a single drum")
    lanes = op.params["lanes"]
    if isinstance(lanes, str):
        # 'kick: x...x... / snare: ....x...' for the command line.
        lanes = {k.strip(): v.strip() for k, _, v in
                 (part.partition(":") for part in lanes.replace("\n", "/").split("/"))
                 if k.strip()}
    if not isinstance(lanes, dict) or not lanes:
        raise ValueError("beat needs lanes, e.g. {'kick': 'x...x...', 'snare': '....x...'}")
    start, end = _span(piece, op)
    grid = ticks(op.params.get("res") or "1/16")
    tune = float(op.params.get("tune") or 0)
    notes: list[Note] = []
    cycle = op.params.get("cycle")
    for drum, source in lanes.items():
        if drum not in KIT_DRUMS:
            raise ValueError(f"unknown drum {drum!r}; a kit has {sorted(KIT_DRUMS)}")
        if cycle:
            notes += _pattern_lane(piece, voice, op, drum, str(source), float(cycle),
                                   start, end, tune)
            continue
        pattern = str(source).replace("|", "").replace(" ", "")
        bad = set(pattern) - set("xXoO.-")
        if not pattern or bad:
            raise ValueError(f"lane {drum!r} must be made of 'x' hit, 'X' accent, "
                             f"'o' ghost and '.' rest; got {source!r}")
        tick, i = start, 0
        while tick < end:
            ch = pattern[i % len(pattern)]
            if ch in "xXoO":
                # A ghost note is far quieter than "one dynamic down": it is felt.
                accent = 1 if ch == "X" else 0
                vel = _velocity(piece, voice, op, tick, accent)
                if ch in "oO":
                    vel = max(1, int(vel * 0.45))
                notes.append(Note(voice.name, KIT_DRUMS[drum], tick, grid, vel, op.id,
                                  percussive=True, tune=tune))
            tick += grid
            i += 1
    return notes


def _pattern_lane(piece: Piece, voice: Voice, op: Op, drum: str, source: str,
                  bars: float, start: int, end: int, tune: float) -> list[Note]:
    """One drum written as a pattern (``pattern.py``) that fills ``bars`` bars
    each time round. ``x`` is a stroke, ``X`` an accent, ``o`` a ghost note."""
    import zlib
    from . import pattern
    from .ensemble import KIT_DRUMS
    if bars <= 0:
        raise ValueError("beat cycle must be a number of bars above zero")
    try:
        tree = pattern.parse(source)
    except pattern.PatternError as exc:
        raise ValueError(f"lane {drum!r}: {exc}") from None

    def lucky(ev, odds: float) -> bool:
        # Seeded from stable data, like everything random in a render: the
        # same piece plays the same "sometimes" every time.
        seed = zlib.crc32(f"{voice.name}|{op.id}|{drum}|{turn}|{ev.path}".encode())
        return seed / 2 ** 32 < odds

    out: list[Note] = []
    short = ticks("1/16")
    tick, turn = start, 0
    while tick < end:
        length = max(1, int(round(piece.section_of_tick(tick).bar_ticks * bars)))
        for ev in pattern.play(tree, turn, lucky):
            if ev.symbol not in ("x", "X", "o", "O"):
                raise ValueError(f"lane {drum!r}: a drum pattern is made of 'x' hit, "
                                 f"'X' accent, 'o' ghost and '.' rest; got {ev.symbol!r}")
            at = tick + int(round(ev.start * length))
            if at >= end:
                continue
            vel = _velocity(piece, voice, op, at, 1 if ev.symbol == "X" else 0)
            if ev.symbol in "oO":
                vel = max(1, int(vel * 0.45))
            # A stroke is a stroke however long its step is: no longer than
            # the grid's sixteenth, or a crash written as one step of a bar
            # would count as a bar of sound.
            out.append(Note(voice.name, KIT_DRUMS[drum], at,
                            max(1, min(short, int(round(ev.length * length)))), vel, op.id,
                            percussive=True, tune=tune))
        tick += length
        turn += 1
    return out


def _op_chop(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    """Cut the bar into slices and play them in another order.

    This is break-chopping done on the notes rather than on a recording, so it
    stays an edit: change the order and the same break is cut differently. The
    slices are equal divisions of the bar; a token names which source slice
    lands in each output slot.
    """
    lo, hi = _span(piece, op, "from", "until")
    per_bar = int(op.params.get("slices") or 8)
    if per_bar < 1:
        raise ValueError("chop needs at least one slice per bar")
    order = _parse_order(op.params["order"], per_bar)
    keep = [n for n in notes if not (lo <= n.start < hi)]
    inside = [n for n in notes if lo <= n.start < hi]
    out: list[Note] = []
    slot = 0
    tick = lo
    while tick < hi:
        bar, _ = piece.position_of(tick)
        bar_lo = piece.tick_of(bar)
        size = piece.section_of_tick(tick).bar_ticks // per_bar
        if size < 1:
            raise ValueError(f"chop cannot cut a bar into {per_bar} slices: that is "
                             f"finer than the studio's time grid")
        src, repeat, tune, backwards, tune_to = order[slot % len(order)]
        slot += 1
        here = tick
        tick += size
        if src is None:
            continue
        if src == "_":
            out += [n for n in inside if here <= n.start < here + size]
            continue
        src_lo = bar_lo + src * size
        piece_len = size // repeat
        source = [n for n in inside if src_lo <= n.start < src_lo + piece_len]
        for k in range(repeat):
            for n in source:
                offset = n.start - src_lo
                if backwards:
                    offset = max(0, piece_len - offset - min(n.dur, piece_len))
                at = here + k * piece_len + offset
                # A roll may climb (or fall) as it goes: the pitch runs from
                # `tune` on the first repeat to `tune_to` on the last.
                shift = tune if tune_to is None or repeat < 2 else \
                    tune + (tune_to - tune) * k / (repeat - 1)
                room = here + (k + 1) * piece_len - at if repeat > 1 else here + size - at
                # A chop is a sampler's edit: the slice keeps the sound it had
                # where it was cut from, and is not re-harmonized where it
                # lands. So a moved note is no longer the theme "as written",
                # and says so, or the motif map would claim a statement that
                # nobody hears. On a pitched voice a whole-semitone shift is a
                # different *note*, and goes into the pitch, where lint, the
                # tension view and MIDI can see it; only the fraction is tuning.
                pitch, bend = n.pitch, n.tune + shift
                if not n.percussive:
                    whole = round(bend)
                    pitch, bend = n.pitch + whole, bend - whole
                moved = at != n.start or pitch != n.pitch
                form = n.form
                if moved and n.motif and "chopped" not in form:
                    form = f"{form}, chopped" if form else "chopped"
                out.append(replace(n, pitch=pitch, start=at,
                                   dur=max(1, min(n.dur, room)), tune=bend,
                                   form=form,
                                   degree=n.degree if pitch == n.pitch else None,
                                   op=n.op))
    if voice.inst.polyphony == 1 and not voice.inst.percussive:
        # One note at a time: a slice moved in front of a held note cuts it off,
        # as it would on the instrument.
        out.sort(key=lambda n: n.start)
        out = [replace(a, dur=max(1, min(a.dur, b.start - a.start)))
               for a, b in zip(out, out[1:])] + out[-1:]
    return keep + out


def _parse_order(source, per_bar: int) -> list[tuple]:
    """``'0 1 2*2 . 3r 6^5 _'`` -> ``(slice, repeats, semitones, backwards,
    semitones at the end of a roll)``."""
    import re
    out = []
    for tok in str(source).replace("|", " ").split():
        if tok == ".":
            out.append((None, 1, 0.0, False, None))
            continue
        if tok == "_":
            out.append(("_", 1, 0.0, False, None))
            continue
        m = re.match(r"^(\d+)(r?)(?:\*(\d+))?(?:\^(-?\d+(?:\.\d+)?)"
                     r"(?:>(-?\d+(?:\.\d+)?))?)?(r?)$", tok)
        if not m or int(m.group(1)) >= per_bar or (m.group(3) and int(m.group(3)) < 1):
            raise ValueError(
                f"bad chop token {tok!r}: a slice number below {per_bar}, optionally "
                f"'*2' to retrigger, '^5' to pitch, '^0>12' to climb across a roll, "
                f"'r' to reverse -- or '.' for silence and '_' to leave the slot "
                f"as written")
        out.append((int(m.group(1)), int(m.group(3) or 1), float(m.group(4) or 0),
                    bool(m.group(2) or m.group(6)),
                    float(m.group(5)) if m.group(5) is not None else None))
    if not out:
        raise ValueError("chop order is empty")
    return out


def _op_events(piece: Piece, voice: Voice, op: Op) -> list[Note]:
    """Imported notes, placed verbatim. No degree resolution: these are already
    pitches, and re-deriving them through a key would only lose information."""
    offset = piece.tick_of(op.params["at"]) if op.params.get("at") is not None else 0
    shift = int(op.params.get("transpose") or 0)
    out: list[Note] = []
    for ev in op.params["events"]:
        pitch, start, dur = int(ev[0]), int(ev[1]), int(ev[2])
        vel = int(ev[3]) if len(ev) > 3 else 80
        out.append(Note(voice.name, pitch + shift, start + offset, max(1, dur),
                        max(1, min(127, vel)), op.id))
    return out


def _op_double(piece: Piece, voice: Voice, op: Op, cache, out, stack) -> list[Note]:
    from .render import _render_voice  # self-reference kept explicit for the cycle guard
    target = piece.get_voice(op.params["source"])
    src = _render_voice(piece, target, cache, out, None, stack + (voice.name,))
    lo, hi = _span(piece, op, "from", "until")
    if op.params.get("from") is None:
        lo, hi = 0, piece.total_ticks
    interval = int(op.params.get("interval") or 0)
    octaves = int(op.params.get("octaves") or 0)
    delay = ticks(op.params["delay"]) if op.params.get("delay") else 0
    notes: list[Note] = []
    for n in src:
        if not (lo <= n.start < hi):
            continue
        key = piece.key_at(n.start)
        if interval:
            # Doubling is diatonic: a "third above" is a third in the key, which
            # is what makes parallel thirds sound like harmony instead of a chorus.
            deg, alt, octv = key.degree_of(n.pitch)
            pitch = key.pitch(deg + interval, alt, octv) + 12 * octaves
        else:
            pitch = n.pitch + 12 * octaves
        notes.append(replace(n, voice=voice.name, pitch=pitch, start=n.start + delay,
                             op=op.id,
                             velocity=_velocity(piece, voice, op, n.start)
                             if op.params.get("dynamic") else n.velocity))
    return notes


# --------------------------------------------------------------------------
# modifiers
# --------------------------------------------------------------------------

def _op_dynamics(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    lo, hi = _span(piece, op, "from", "until")
    start_v = dynamic_velocity(op.params["start"]) if op.params.get("start") else None
    end_v = dynamic_velocity(op.params["end"]) if op.params.get("end") else None
    if start_v is None and end_v is None:
        raise ValueError("dynamics needs at least one of start= or end= "
                         "(e.g. start='pp', end='ff' for a crescendo)")
    if start_v is None:
        start_v = end_v
    if end_v is None:
        end_v = start_v
    out = []
    for n in notes:
        if lo <= n.start < hi and hi > lo:
            t = (n.start - lo) / (hi - lo)
            out.append(replace(n, velocity=max(1, min(127, int(start_v + (end_v - start_v) * t)))))
        else:
            out.append(n)
    return out


def _op_articulate(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    lo, hi = _span(piece, op, "from", "until")
    style = op.params.get("style") or "legato"
    if style not in ARTICULATIONS:
        raise ValueError(f"unknown articulation {style!r}; have {sorted(ARTICULATIONS)}")
    ratio, delta = ARTICULATIONS[style]
    out = []
    for n in notes:
        if lo <= n.start < hi:
            # Re-derive from the written value rather than compounding ratios, so
            # articulating twice is idempotent instead of shrinking every note.
            base = n.dur / ARTICULATIONS["normal"][0]
            out.append(replace(n, dur=max(1, int(base * ratio)),
                               velocity=max(1, min(127, n.velocity + delta)),
                               slur=style == "legato"))
        else:
            out.append(n)
    return out


def _op_humanize(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    """Seeded, so a humanized render is still byte-identical run to run."""
    import random
    import zlib
    lo, hi = _span(piece, op, "from", "until")
    if op.params.get("from") is None:
        lo, hi = 0, piece.total_ticks
    amount = float(op.params.get("amount") or 0.4)
    timing = int(op.params.get("timing") or 12)
    # crc32, not hash(): Python salts str hashes per process, so hash(op.id)
    # gave every run a different "seeded" performance.
    seed = int(op.params.get("seed") or 0) or zlib.crc32(op.id.encode("utf-8"))
    rng = random.Random(seed)
    out = []
    for n in sorted(notes, key=lambda n: (n.start, n.pitch)):
        if lo <= n.start < hi:
            jitter = rng.randint(-timing, timing)
            vel = n.velocity + int(rng.uniform(-9, 9) * amount)
            out.append(replace(n, start=max(0, n.start + jitter),
                               velocity=max(1, min(127, vel))))
        else:
            out.append(n)
    return out


def _phrases(notes: list[Note], gap: int) -> list[list[Note]]:
    """Split a line where it breathes: wherever the silence is at least ``gap``."""
    out: list[list[Note]] = []
    end = None
    for n in sorted(notes, key=lambda n: (n.start, n.pitch)):
        if end is None or n.start - end >= gap:
            out.append([])
        out[-1].append(n)
        end = n.end if end is None else max(end, n.end)
    return out


def _op_shape(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    """Phrase the line the way a player would without being told to.

    Three things, all small and all deterministic: each phrase swells toward a
    point past its middle and tapers off its last notes; higher notes are a
    little stronger than lower ones; and the note on a downbeat carries slightly
    more than the ones between. A line at one flat velocity is the single
    clearest sign that nobody is playing it.
    """
    import math
    lo, hi = _span(piece, op, "from", "until")
    if op.params.get("from") is None:
        lo, hi = 0, piece.total_ticks
    amount = float(op.params.get("amount") if op.params.get("amount") is not None else 0.5)
    peak = float(op.params.get("peak") if op.params.get("peak") is not None else 0.62)
    peak = max(0.05, min(0.95, peak))
    inside = [n for n in notes if lo <= n.start < hi and not n.percussive]
    delta: dict[int, float] = {}
    for phrase in _phrases(inside, ticks(op.params.get("breath") or "1/4")):
        t0, t1 = phrase[0].start, max(n.start for n in phrase)
        p_lo = min(n.pitch for n in phrase)
        p_hi = max(n.pitch for n in phrase)
        for n in phrase:
            t = (n.start - t0) / (t1 - t0) if t1 > t0 else peak
            # Rise to the peak, fall away after it; the fall is steeper because
            # a phrase ending is a release, not a mirror of its beginning.
            arc = (0.35 + 0.65 * math.sin(0.5 * math.pi * t / peak) if t <= peak
                   else math.cos(0.5 * math.pi * (t - peak) / (1 - peak)) ** 1.3)
            height = (n.pitch - p_lo) / (p_hi - p_lo) if p_hi > p_lo else 0.5
            _, beat = piece.position_of(n.start)
            metric = 1.0 if beat == 1 else 0.35 if float(beat).is_integer() else 0.0
            delta[id(n)] = amount * (22 * (arc - 0.6) + 9 * (height - 0.5) + 5 * metric)
    return [replace(n, velocity=max(1, min(127, int(round(n.velocity + delta[id(n)])))))
            if id(n) in delta else n for n in notes]


def _op_swing(piece: Piece, voice: Voice, op: Op, notes: list[Note]) -> list[Note]:
    """Delay every off-beat subdivision, so pairs play long-short.

    ``amount`` is the share of the pair the first note takes: 0.5 is straight,
    0.67 is triplet swing. Notes are moved, never re-ordered, and a note that is
    pushed late gives the time up from its own length.
    """
    lo, hi = _span(piece, op, "from", "until")
    if op.params.get("from") is None:
        lo, hi = 0, piece.total_ticks
    res = ticks(op.params.get("res") or "1/8")
    amount = float(op.params.get("amount") if op.params.get("amount") is not None else 0.62)
    if not 0.5 <= amount <= 0.8:
        raise ValueError(f"swing amount is the long note's share of the pair, "
                         f"0.5 (straight) to 0.8; got {amount}")
    shift = int(round((amount - 0.5) * 2 * res))
    out = []
    for n in notes:
        if not (lo <= n.start < hi):
            out.append(n)
            continue
        bar, _ = piece.position_of(n.start)
        within = n.start - piece.tick_of(bar)
        if within % res == 0 and (within // res) % 2 == 1:
            out.append(replace(n, start=n.start + shift, dur=max(1, n.dur - shift)))
        else:
            out.append(n)
    return out
