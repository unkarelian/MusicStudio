"""Turning a render back into something an agent can read.

Agents lose music the way they lose pixel art: they emit a stream they never
inspect, and nothing tells them the counter-melody is sitting on top of the tune
or that bar 30 is identical to bar 6. Every view here is *addressed* -- columns
carry bar numbers, rows carry note names -- so a position never has to be
counted out, and the thing an agent needs to notice is visible rather than
inferable.

Four views, each answering a different question:

  ``score``      what is actually sounding, and against what harmony
  ``chart``      what the form is, at a glance
  ``motif_map``  where each theme appears and in what shape
  ``squint``     does the piece have an arc, or is it flat for four minutes
"""

from __future__ import annotations

from .doc import Piece
from .render import Note, Render, render
from .theory import chord_symbol, parse_chord, spell_pitch, velocity_dynamic

GUTTER = 7
MAX_ROWS = 46


def voice_glyphs(piece: Piece) -> dict[str, str]:
    """A stable letter per voice, taken from its name where possible."""
    used: dict[str, str] = {}
    taken: set[str] = set()
    for v in piece.voices:
        for cand in list(v.name.upper()) + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            if cand.isalpha() and cand not in taken:
                used[v.name] = cand
                taken.add(cand)
                break
        else:  # pragma: no cover - 26 voices is already unreasonable
            used[v.name] = "?"
    return used


def _bar_range(piece: Piece, bars) -> tuple[int, int]:
    if bars is None:
        return 1, max(1, piece.total_bars)
    if isinstance(bars, int):
        return bars, bars
    lo, hi = bars
    return max(1, int(lo)), min(max(1, piece.total_bars), int(hi))


def score(piece: Piece, rend: Render | None = None, *, bars=None, res: str = "1/8",
          glyphs: str = "voice", legend: bool = True, voices: list[str] | None = None) -> str:
    """A pitch-by-time grid, one glyph per voice.

    This is the view that makes counterpoint visible. Two voices crossing, an
    inner part doubling the melody by accident, a bass line that never moves --
    all of it is a shape here, and none of it is a shape in a list of notes.

    Onsets are uppercase and sustains lowercase, so rhythm reads off the grid
    without counting durations. With ``glyphs='degree'`` each note prints its
    scale degree instead, which is the view to use when checking whether a line
    is actually outlining the harmony.
    """
    r = rend if rend is not None else render(piece)
    lo_bar, hi_bar = _bar_range(piece, bars)
    start = piece.tick_of(lo_bar)
    end = (piece.tick_of(hi_bar + 1) if hi_bar < piece.total_bars else piece.total_ticks)
    step = _res_ticks(res)
    cols = max(1, (end - start + step - 1) // step)
    glyph = voice_glyphs(piece)
    wanted = set(voices) if voices else None

    notes = [n for n in r.notes if n.end > start and n.start < end
             and (wanted is None or n.voice in wanted)]
    if not notes:
        return (f"{piece.name}  {piece.key.name}  bars {lo_bar}-{hi_bar}\n"
                f"(nothing sounds in these bars)")

    pitches = sorted({n.pitch for n in notes}, reverse=True)
    truncated = 0
    if len(pitches) > MAX_ROWS:
        truncated = len(pitches) - MAX_ROWS
        pitches = pitches[:MAX_ROWS]
    row_of = {p: i for i, p in enumerate(pitches)}
    grid = [[" "] * cols for _ in pitches]

    for n in notes:
        if n.pitch not in row_of:
            continue
        c0 = max(0, (n.start - start) // step)
        c1 = min(cols - 1, (max(n.end - 1, n.start) - start) // step)
        mark = glyph[n.voice] if glyphs == "voice" else _degree_glyph(piece, n)
        for c in range(c0, c1 + 1):
            if c >= cols:
                break
            cur = grid[row_of[n.pitch]][c]
            ch = mark if c == c0 else mark.lower()
            # An onset always wins over a neighbour's sustain; two onsets on the
            # same pitch and column mean a genuine collision, shown as '*'.
            if cur == " " or (c == c0 and cur.islower()):
                grid[row_of[n.pitch]][c] = ch
            elif cur != ch:
                grid[row_of[n.pitch]][c] = "*"

    out = [f"{piece.name}  {piece.key.name}  q={piece.tempo}  bars {lo_bar}-{hi_bar}  "
           f"res={res}"]
    out += _rulers(piece, lo_bar, hi_bar, start, step, cols)
    key0 = piece.key_at(start)
    for i, p in enumerate(pitches):
        out.append(f"{spell_pitch(p, key0):>{GUTTER}}|" + "".join(grid[i]))
    if truncated:
        out.append(f"{'...':>{GUTTER}}|({truncated} more pitch rows hidden; "
                   f"crop with bars= or voices=)")
    out.append(_chord_row(piece, start, step, cols))
    if legend:
        out.append("")
        out.append("voices:")
        for v in piece.voices:
            if wanted and v.name not in wanted:
                continue
            n = sum(1 for x in r.notes if x.voice == v.name)
            mute = "  (muted)" if v.muted else ""
            out.append(f"  {glyph[v.name]} = {v.name:<14} {v.instrument:<16} "
                       f"{v.role:<10} {n:>5} notes{mute}")
    return "\n".join(out)


def _res_ticks(res: str) -> int:
    from .theory import ticks
    t = ticks(res)
    if t < 1:
        raise ValueError(f"resolution {res!r} is too fine")
    return t


def _degree_glyph(piece: Piece, n: Note) -> str:
    key = piece.key_at(n.start)
    deg, alt, _ = key.degree_of(n.pitch)
    return "#" if alt > 0 else "b" if alt < 0 else str((deg % key.size) + 1)


def _rulers(piece: Piece, lo_bar: int, hi_bar: int, start: int, step: int,
            cols: int) -> list[str]:
    """Bar numbers and barlines above the grid, so no column is ever counted."""
    bar_line = [" "] * cols
    num_line = [" "] * cols
    for bar in range(lo_bar, hi_bar + 1):
        c = (piece.tick_of(bar) - start) // step
        if not 0 <= c < cols:
            continue
        bar_line[c] = "|"
        for j, ch in enumerate(str(bar)):
            if c + j < cols:
                num_line[c + j] = ch
    return [f"{'bar':>{GUTTER}} " + "".join(num_line),
            f"{'':>{GUTTER}} " + "".join(bar_line)]


def _chord_row(piece: Piece, start: int, step: int, cols: int) -> str:
    row = [" "] * cols
    for s, e, numeral in piece.harmony_spans():
        c = (s - start) // step
        if not 0 <= c < cols:
            continue
        for j, ch in enumerate(numeral):
            if c + j < cols:
                row[c + j] = ch
    return f"{'chord':>{GUTTER}}|" + "".join(row)


def chart(piece: Piece, rend: Render | None = None) -> str:
    """The form at a glance: sections, harmony, and who is playing.

    The question this answers is "what shape is this piece", which is the
    question an agent writing a four-minute cue most needs to keep asking and
    is least able to answer from a note list.
    """
    r = rend if rend is not None else render(piece)
    out = [f"{piece.name}  {piece.key.name}  q={piece.tempo}  {piece.meter}  "
           f"style={piece.style}",
           f"{piece.total_bars} bars, {_mmss(piece, r)}, {len(r.notes)} notes, "
           f"{len(piece.voices)} voices, {len(piece.motifs)} motifs", ""]
    glyph = voice_glyphs(piece)
    head = f"  {'section':<10} {'bars':<9} {'meter':<6} {'q':<5} {'key':<12} {'dyn':<4} voices"
    out.append(head)
    out.append("  " + "-" * (len(head) - 2))
    for sec, first, tick in piece.section_bounds():
        last = first + sec.bars - 1
        active = "".join(glyph[v.name] for v in piece.voices
                         if any(n.voice == v.name and tick <= n.start < tick + sec.length
                                for n in r.notes))
        key = sec.key or ""
        out.append(f"  {sec.name:<10} {f'{first}-{last}':<9} {sec.meter:<6} "
                   f"{piece.tempo_of(sec):<5} {key:<12} {sec.dynamic:<4} {active or '-'}"
                   + (f"   {sec.note}" if sec.note else ""))
    out.append("")
    out.append("  harmony")
    for s, e, numeral in piece.harmony_spans():
        bar, beat = piece.position_of(s)
        key = piece.key_at(s)
        try:
            sym = chord_symbol(parse_chord(numeral, key), key)
        except (ValueError, KeyError):
            sym = "?"
        bars = (e - s) / max(1, piece.section_of_tick(s).bar_ticks)
        out.append(f"    {f'{bar}:{float(beat):g}':<8} {numeral:<10} {sym:<10} {bars:g} bars")
    return "\n".join(out)


def _mmss(piece: Piece, r: Render) -> str:
    seconds = 0.0
    for sec, _, _ in piece.section_bounds():
        seconds += sec.length / 480 * 60 / max(1, piece.tempo_of(sec))
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def motif_map(piece: Piece, rend: Render | None = None) -> str:
    """Where every theme appears, and in what shape.

    This is the view the whole design exists to make possible. Because a motif
    is a named object and its transformations are recorded, the studio can state
    -- not guess -- that the theme returns at bar 33 inverted and augmented. An
    agent that re-emits remembered notes has no way to be asked this question,
    which is exactly why its leitmotifs quietly stop being leitmotifs.
    """
    r = rend if rend is not None else render(piece)
    if not piece.motifs:
        return "no motifs defined -- material written with `phrase` is not tracked"
    out = [f"{piece.name}: {len(piece.motifs)} motifs"]
    for name, m in piece.motifs.items():
        head = f"  {name:<16} {m.source():<40}"
        info = (f"<- {m.derived_from} via {' + '.join(m.lineage)}" if m.derived_from
                else f"{m.anchor:<6} span {m.span} steps  contour {m.contour() or '-'}")
        out.append(head + info + (f"   -- {m.note}" if m.note else ""))
    out.append("")
    out.append(f"  {'motif':<16} {'form':<22} appearances (bar: voice)")
    out.append("  " + "-" * 74)

    seen: dict[tuple[str, str], list[tuple[int, str]]] = {}
    played: set[str] = set()
    for n in r.notes:
        if not n.motif:
            continue
        if n.played:
            played.add(n.played)
        key = (n.motif, n.form or "as written")
        bar, _ = piece.position_of(n.start)
        entries = seen.setdefault(key, [])
        if not entries or entries[-1] != (bar, n.voice):
            entries.append((bar, n.voice))
    if not seen:
        out.append("  (no motif is ever played -- every note came from phrase/chords/bass)")
    for (name, form), spots in sorted(seen.items()):
        firsts: list[str] = []
        last = None
        for bar, voice in spots:
            if last != (bar, voice):
                firsts.append(f"{bar}:{voice}")
                last = (bar, voice)
        shown = " ".join(dict.fromkeys(firsts))
        out.append(f"  {name:<16} {form:<22} {shown}")

    # A derived motif reports its *root* on every note, so membership has to be
    # checked against the name the op actually named as well.
    inside = piece.heard_within(played | {form for _, form in seen})
    unheard = [n for n in piece.motifs
               if n not in played and n not in inside and not any(k[0] == n for k in seen)]
    joined = sorted(n for n in inside if n not in played and not any(k[0] == n for k in seen))
    if joined:
        out.append("")
        out.append(f"  heard as part of a longer theme: {', '.join(joined)}")
    if unheard:
        out.append("")
        out.append(f"  never played: {', '.join(unheard)}")
    return "\n".join(out)


def squint(piece: Piece, rend: Render | None = None) -> str:
    """The squint test: one column per bar, three lines, the whole arc.

    If the density, register and dynamic lines are flat, the piece is flat --
    and no amount of good voice leading inside the bars will fix that. This is
    the view to look at before adding another counter-melody.
    """
    r = rend if rend is not None else render(piece)
    bars = max(1, piece.total_bars)
    ramp = " .:-=+*#%@"
    density, register, dynamic, voices = [], [], [], []
    for bar in range(1, bars + 1):
        lo = piece.tick_of(bar)
        hi = piece.tick_of(bar + 1) if bar < bars else piece.total_ticks
        here = [n for n in r.notes if lo <= n.start < hi]
        density.append(len(here))
        register.append(sum(n.pitch for n in here) / len(here) if here else None)
        dynamic.append(sum(n.velocity for n in here) / len(here) if here else 0)
        voices.append(len({n.voice for n in here}))

    peak = max(density) or 1
    dens_line = "".join(ramp[min(len(ramp) - 1, int(d / peak * (len(ramp) - 1)))]
                        for d in density)
    known = [p for p in register if p is not None]
    if known:
        lo_p, hi_p = min(known), max(known)
        rng = max(1, hi_p - lo_p)
        reg_line = "".join(" " if p is None else
                           "_.-~^"[min(4, int((p - lo_p) / rng * 4.999))] for p in register)
    else:
        reg_line = " " * bars
    dyn_line = "".join(ramp[min(len(ramp) - 1, int(d / 127 * (len(ramp) - 1)))]
                       for d in dynamic)
    voice_line = "".join(str(min(9, v)) if v else "." for v in voices)

    out = [f"{piece.name} -- {bars} bars, one column per bar", ""]
    out.append(f"  {'density':<9}{dens_line}")
    out.append(f"  {'register':<9}{reg_line}")
    out.append(f"  {'dynamic':<9}{dyn_line}")
    out.append(f"  {'voices':<9}{voice_line}")
    out.append(f"  {'':<9}{_section_ruler(piece, bars)}")
    if known:
        out.append("")
        out.append(f"  register spans {spell_pitch(int(min(known)), piece.key)}"
                   f"-{spell_pitch(int(max(known)), piece.key)} (mean per bar); "
                   f"density peaks at {peak} notes/bar")
    return "\n".join(out)


def _section_ruler(piece: Piece, bars: int) -> str:
    row = [" "] * bars
    for sec, first, _ in piece.section_bounds():
        for j, ch in enumerate(sec.name):
            if first - 1 + j < bars:
                row[first - 1 + j] = ch
    return "".join(row)


def voice_view(piece: Piece, name: str, rend: Render | None = None, *, bars=None) -> str:
    """One voice as a list of events -- for when the grid is too coarse to check."""
    r = rend if rend is not None else render(piece)
    v = piece.get_voice(name)
    lo_bar, hi_bar = _bar_range(piece, bars)
    lo, hi = piece.tick_of(lo_bar), (piece.tick_of(hi_bar + 1)
                                    if hi_bar < piece.total_bars else piece.total_ticks)
    out = [f"{name}  {v.instrument}  role={v.role}  "
           f"range {v.inst.low}-{v.inst.high} (comfort {v.inst.comfort_low}-"
           f"{v.inst.comfort_high})",
           f"  {'pos':<9} {'pitch':<6} {'deg':<5} {'dur':<8} {'dyn':<5} {'motif':<18} op"]
    from .theory import ticks_to_dur
    for n in sorted(r.by_voice(name), key=lambda n: n.start):
        if not (lo <= n.start < hi):
            continue
        bar, beat = piece.position_of(n.start)
        key = piece.key_at(n.start)
        deg, alt, _ = key.degree_of(n.pitch)
        mark = ("#" if alt > 0 else "b" if alt < 0 else "") + str(deg + 1)
        label = n.motif + (f"[{n.form}]" if n.form else "") if n.motif else ""
        if n.lyric:
            label = f"{n.lyric!r} {label}".strip()
        out.append(f"  {f'{bar}:{float(beat):g}':<9} "
                   f"{spell_pitch(n.pitch, key):<6} {mark:<5} "
                   f"{ticks_to_dur(n.dur):<8} {velocity_dynamic(n.velocity):<5} "
                   f"{label:<18} {n.op}")
    if len(out) == 2:
        out.append("  (silent in these bars)")
    return "\n".join(out)


def stats(piece: Piece, rend: Render | None = None) -> dict:
    r = rend if rend is not None else render(piece)
    notes = r.notes
    per_voice = {}
    for v in piece.voices:
        vn = [n for n in notes if n.voice == v.name]
        per_voice[v.name] = {
            "instrument": v.instrument, "role": v.role, "notes": len(vn),
            "range": [spell_pitch(min(n.pitch for n in vn), piece.key),
                      spell_pitch(max(n.pitch for n in vn), piece.key)] if vn else None,
            "ops": len(v.ops),
        }
    motif_notes = sum(1 for n in notes if n.motif)
    return {
        "bars": piece.total_bars,
        "duration": _mmss(piece, r),
        "notes": len(notes),
        "voices": per_voice,
        "sections": [s.name for s in piece.sections],
        "motifs": {m: sum(1 for n in notes if n.motif == m) for m in piece.motifs},
        "motif_coverage": round(motif_notes / len(notes), 3) if notes else 0.0,
        "pitch_range": ([spell_pitch(min(n.pitch for n in notes), piece.key),
                         spell_pitch(max(n.pitch for n in notes), piece.key)]
                        if notes else None),
    }


def diff(before: Render, after: Render, piece: Piece) -> str:
    """What changed between two renders, as events rather than a wall of grid."""
    def key(n: Note):
        return (n.voice, n.start, n.pitch, n.dur, n.velocity)

    a, b = {key(n) for n in before.notes}, {key(n) for n in after.notes}
    added, removed = sorted(b - a), sorted(a - b)
    out = []
    for tag, rows in (("-", removed), ("+", added)):
        for voice, start, pitch, dur, vel in rows[:24]:
            bar, beat = piece.position_of(start)
            out.append(f"  {tag} {voice:<12} {f'{bar}:{float(beat):g}':<9} "
                       f"{spell_pitch(pitch, piece.key)}")
    extra = max(0, len(added) + len(removed) - 48)
    out.append(f"\n{len(removed)} notes removed, {len(added)} added"
               + (f" ({extra} not listed)" if extra else ""))
    return "\n".join(out) if out else "no change"
