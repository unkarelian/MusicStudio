"""MCP server: the studio as a tool surface for agents.

Tool design follows one rule -- every mutating tool hands back the new score
view and the critique in the same response. An agent should not have to *decide*
to listen to what it just wrote; the loop closes whether or not it thinks to
close it.

Run with ``ms-mcp`` or ``python -m musicstudio.mcp_server [project_dir]``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from . import __version__
from .lint import report
from .studio import Studio

INSTRUCTIONS = """\
MusicStudio is a studio for instrumental score writing -- OST rather than songs.
A piece is not a list of notes here. It is a form, a harmonic scaffold, and
voices made of named, re-editable operations.

Why that matters for you:
  * You never name a MIDI note. Melodies are scale degrees ("0 2 4:1/4 3 2:1/2"),
    chords are roman numerals ("i", "V7", "bVI"). Wrong-key notes are
    unrepresentable rather than discouraged, and modulating is a one-line change.
  * Motifs are objects, so a leitmotif survives. `ms_derive_motif("fate_far",
    "fate", ["invert","augment:2"])` is provably still `fate`, and
    `ms_motif_map` will tell you where every theme appears and in what shape.
    Re-typing notes you half-remember is how agents lose their own themes.
  * Time is bars and beats ("5:2.5") and note values ("1/8.", "1/4t"). The
    studio does the arithmetic, so rhythm cannot drift out from under the bar.
  * Every op has an id, so revision is surgical: `ms_update_op("theme_2",
    transpose=2)` moves one statement of a theme and leaves the score alone.
  * The studio knows what instruments can do. It picks a register that fits the
    player, and refuses to let a horn play a note it does not have.
  * A melody can be as elaborate as you can hear. Notes take ornaments and
    articulations ("4:1/4@tr", "2@gr+1", "0@st"), cells join into long themes
    (`then`), and a theme is decorated by derivation (`embellish`, `ornament`,
    `dot`, `expand`) -- so the ornate repeat is still provably the theme.
  * It is played, not sequenced. `chords` with lead=True voice-leads, ring=True
    pedals, figure= writes your own accompaniment pattern; the `shape` op
    phrases a line and legato notes are slurred. A section's tempo_end is a
    ritardando. The WAV render plays each voice through an instrument model.

Suggested loop:
  1. ms_describe_styles / ms_describe_ops / ms_describe_transforms -- the vocabulary
  2. ms_new with a `form` preset -- give the cue a shape before it has notes
  3. ms_set_harmony -- the scaffold everything else is written against
  4. ms_add_motif -- state your themes as objects, before placing them
  5. ms_add_voice, then ms_add_op to place motifs, chords, bass and groove
     -- then `shape` on each melodic voice and `humanize` last
  6. read the view every mutation returns; ms_squint to check the piece has an arc
  7. ms_motif_map -- is the theme actually developing, or just repeating?
     ms_tension -- does it lean anywhere, and was the climax prepared?
  8. ms_lint -- fix errors, judge warnings, ignore info you meant
  9. ms_hear -- measure the render: is the tune clear, did every note sound?
 10. ms_export_wav -- render it and have the human actually listen

Every change is a checkpoint. If an idea does not work, ms_undo takes it back
(and ms_redo re-applies it), so try the bold version first.

Work form first, then harmony, then themes, then texture. Do not write bar 1
before you know what bar 40 is doing. The critique pass will tell you when the
bass has turned to mud or the piece has been at one dynamic for four minutes --
trust it over your own reading of the note list.
"""

_studio = Studio(os.environ.get("MUSICSTUDIO_PROJECT", "."))
mcp = MCPServer(
    name="musicstudio",
    title="MusicStudio",
    version=__version__,
    instructions=INSTRUCTIONS,
)


def _j(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def _guard(fn, *args, **kwargs) -> str:
    """Return errors as readable text; a traceback teaches an agent nothing."""
    try:
        return fn(*args, **kwargs)
    except (KeyError, ValueError, TypeError, IndexError, RuntimeError, ImportError,
            OSError) as exc:
        msg = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        return f"error: {msg}"


# -- discovery -------------------------------------------------------------

@mcp.tool(description="List style profiles: their rules, form presets and house notes.")
def ms_describe_styles() -> str:
    return _j(_studio.describe_styles())


@mcp.tool(description=(
    "List the op vocabulary with required and optional params. Generators put "
    "notes on the timeline; modifiers reshape what earlier ops produced."))
def ms_describe_ops() -> str:
    return _j(_studio.describe_ops())


@mcp.tool(description=(
    "List the motif development vocabulary -- transpose, invert, retrograde, "
    "augment, fragment, sequence, and the elaborations: embellish, ornament, "
    "expand, dot, displace, thin, mirror, append, then -- plus the ornament and "
    "articulation marks a note can carry. This is how a theme becomes a "
    "leitmotif rather than a loop, and how a plain tune becomes an ornate one "
    "without ceasing to be itself."))
def ms_describe_transforms() -> str:
    return _j({"transforms": _studio.describe_transforms(),
               **_studio.describe_notation()})


@mcp.tool(description=(
    "List instruments with their ranges, comfortable registers, polyphony and "
    "idiomatic notes. Consult before scoring: the range is a hard constraint and "
    "the comfortable register is where the instrument actually sounds like itself."))
def ms_describe_instruments(family: str | None = None) -> str:
    return _j(_studio.describe_instruments(family))


@mcp.tool(description="List pieces in the project.")
def ms_list() -> str:
    return _j(_studio.list_pieces())


# -- lifecycle -------------------------------------------------------------

@mcp.tool(description=(
    "Create a piece. Give a `form` preset (cue, ternary, arch, loop, binary, "
    "miniature) so the piece has a shape before it has notes -- writing bar 1 "
    "with no idea what bar 40 does is the single commonest way a cue meanders."))
def ms_new(name: str, key: str = "C major", tempo: int = 90, meter: str = "4/4",
           style: str = "orchestral", form: str | None = None,
           sections: list | None = None, overwrite: bool = False,
           loop: bool = False) -> str:
    def go():
        p = _studio.create(name, key=key, tempo=tempo, meter=meter, style=style,
                           form=form, sections=sections, overwrite=overwrite, loop=loop)
        return (f"created {p.name}: {p.key.name}, q={p.tempo}, {p.meter}, "
                f"style={p.style}{', loop' if p.loop else ''}\n"
                f"sections: {[(s.name, s.bars) for s in p.sections] or 'none yet'}\n"
                f"file: {_studio.path_for(p.name)}")
    return _guard(go)


@mcp.tool(description="Delete a piece from the project. Undoable with ms_undo.")
def ms_delete(name: str) -> str:
    return _guard(lambda: (_studio.delete(name), f"deleted {name} (ms_undo restores it)")[1])


@mcp.tool(description=(
    "Change the piece-level key, tempo, style or loop flag. A new key re-renders "
    "every degree in it -- transposing a whole cue is one call -- and each chord is "
    "re-checked first. loop=true marks game music that repeats, so the critique "
    "stops asking it to end on the tonic."))
def ms_update_piece(name: str, key: str | None = None, tempo: int | None = None,
                    style: str | None = None, loop: bool | None = None) -> str:
    return _guard(lambda: str(_studio.update_piece(name, key=key, tempo=tempo,
                                                   style=style, loop=loop)))


@mcp.tool(description=(
    "Take back the last change to a piece. Every mutation is a checkpoint, so an "
    "experiment that did not work costs one call. Returns a diff of what changed "
    "back, plus the critique."))
def ms_undo(name: str) -> str:
    return _guard(lambda: str(_studio.undo(name)))


@mcp.tool(description="Re-apply a change that ms_undo took back.")
def ms_redo(name: str) -> str:
    return _guard(lambda: str(_studio.redo(name)))


# -- form and scaffold -----------------------------------------------------

@mcp.tool(description=(
    "Add a section. Sections carry their own meter, tempo, key and dynamic, and "
    "they are what the critique pass reasons about when it asks whether the piece "
    "has an arc. tempo_end lower than the tempo is a ritardando across the section."))
def ms_add_section(name: str, section: str, bars: int = 8, meter: str | None = None,
                   tempo: int | None = None, key: str | None = None,
                   dynamic: str = "mf", note: str = "", index: int | None = None,
                   tempo_end: int | None = None) -> str:
    return _guard(lambda: str(_studio.add_section(name, section, bars=bars, meter=meter,
                                                  tempo=tempo, key=key, dynamic=dynamic,
                                                  note=note, index=index,
                                                  tempo_end=tempo_end)))


@mcp.tool(description=(
    "Change a section's bars, meter, tempo, key or dynamic level. tempo_end makes "
    "the tempo move across the section: lower than tempo is a ritardando."))
def ms_update_section(name: str, section: str, fields: dict) -> str:
    return _guard(lambda: str(_studio.update_section(name, section, **fields)))


@mcp.tool(description="Remove a section. Bars after it move earlier.")
def ms_remove_section(name: str, section: str) -> str:
    return _guard(lambda: str(_studio.remove_section(name, section)))


@mcp.tool(description=(
    "Set the harmonic scaffold as roman numerals on the timeline: "
    "[['1','i'],['3','VI'],['5','iv'],['7','V7']]. Chords stack thirds in the "
    "scale, so 'ii' is minor in a major key without being told. Understood: "
    "I ii V7 vii%7 viio7 bVI IVmaj7 Vsus4, secondaries as 'V/V', inversions as "
    "'V_1'. In a minor key the 3rd/6th/7th are already lowered -- write 'VII', "
    "not 'bVII'."))
def ms_set_harmony(name: str, entries: list, replace: bool = True) -> str:
    return _guard(lambda: str(_studio.set_harmony(name, entries, replace=replace)))


@mcp.tool(description=(
    "Add a voice: a named part with an instrument and a role (melody, counter, "
    "harmony, bass, pad, ornament, percussion). The role decides the default "
    "register and what the critique pass expects of it."))
def ms_add_voice(name: str, voice: str, instrument: str, role: str = "melody",
                 octave: int | None = None, dynamic: str | None = None,
                 pan: float | None = None) -> str:
    return _guard(lambda: str(_studio.add_voice(name, voice, instrument, role=role,
                                                octave=octave, dynamic=dynamic, pan=pan)))


@mcp.tool(description=(
    "Change a voice's instrument, role, octave, dynamic, muted state or pan "
    "(-1 left .. 1 right; by default voices are seated like an orchestra)."))
def ms_set_voice(name: str, voice: str, fields: dict) -> str:
    return _guard(lambda: str(_studio.set_voice(name, voice, **fields)))


@mcp.tool(description="Remove a voice and all its ops. Refused if another voice doubles it.")
def ms_remove_voice(name: str, voice: str) -> str:
    return _guard(lambda: str(_studio.remove_voice(name, voice)))


# -- motifs ----------------------------------------------------------------

@mcp.tool(description=(
    "Define a motif in degree notation: '0 2 4:1/4 r:1/8 b6 7~ 7'. Degrees are "
    "scale steps from the anchor (0 is the anchor, 7 is the octave, -1 is the "
    "step below), ':' gives a duration, 'r' is a rest, '~' ties, '!' accents. "
    "A note may end in @marks: an ornament (@tr trill, @mord / @lmord mordents, "
    "@turn, @gr grace from below, @gr+1 from above, @run-3 a run up from a fourth "
    "below) and/or an articulation (@st, @ten, @leg, @marc, @port). Ornaments are "
    "scale steps and never move the note they decorate. "
    "anchor='chord' counts chord tones instead, so the figure re-fits every chord "
    "it passes over."))
def ms_add_motif(name: str, motif: str, source: str, anchor: str = "scale",
                 scale: str | None = None, unit: str = "1/8", note: str = "") -> str:
    return _guard(lambda: _j(_studio.add_motif(name, motif, source, anchor=anchor,
                                               scale=scale, unit=unit, note=note)))


@mcp.tool(description=(
    "Derive a named variation, keeping the lineage: derive_motif('fate_far', "
    "'fate', ['invert','augment:2']). This is what makes a leitmotif a leitmotif "
    "-- the studio can state that the transformed theme IS the theme, and "
    "ms_motif_map will show it."))
def ms_derive_motif(name: str, motif: str, source_motif: str, transforms: list,
                    note: str = "") -> str:
    return _guard(lambda: _j(_studio.derive_motif(name, motif, source_motif,
                                                  transforms, note=note)))


@mcp.tool(description="Remove a motif. Refused while any op still plays it.")
def ms_remove_motif(name: str, motif: str) -> str:
    return _guard(lambda: _j(_studio.remove_motif(name, motif)))


@mcp.tool(description="List the piece's motifs with their sources and lineages.")
def ms_list_motifs(name: str) -> str:
    return _guard(lambda: _j(_studio.list_motifs(name)))


# -- ops -------------------------------------------------------------------

@mcp.tool(description=(
    "Add an op to a voice. `params` takes the op's own arguments -- see "
    "ms_describe_ops. Give a stable, meaningful id ('theme_entry', 'climax_brass') "
    "so you can revise it later. Returns the new score view plus the critique."))
def ms_add_op(name: str, voice: str, kind: str, params: dict, id: str | None = None,
              index: int | None = None, note: str = "",
              view_bars: list | None = None) -> str:
    return _guard(lambda: str(_studio.add_op(name, voice, kind, id=id, index=index,
                                             note=note, view_bars=view_bars, **params)))


@mcp.tool(description="Change an op's params, keeping its id and position in the log.")
def ms_update_op(name: str, op_id: str, params: dict) -> str:
    return _guard(lambda: str(_studio.update_op(name, op_id, **params)))


@mcp.tool(description=(
    "Shift an op in time by whole bars and/or beats. Returns a diff of exactly "
    "which notes moved."))
def ms_move_op(name: str, op_id: str, bars: int = 0, beats: float = 0) -> str:
    return _guard(lambda: str(_studio.move_op(name, op_id, bars, beats)))


@mcp.tool(description="Remove an op.")
def ms_remove_op(name: str, op_id: str) -> str:
    return _guard(lambda: str(_studio.remove_op(name, op_id)))


@mcp.tool(description="Move an op to a new position in the log, optionally onto another voice.")
def ms_reorder_op(name: str, op_id: str, index: int, voice: str | None = None) -> str:
    return _guard(lambda: str(_studio.reorder_op(name, op_id, index, voice)))


@mcp.tool(description="Enable or disable an op without deleting it -- for A/B checks.")
def ms_toggle_op(name: str, op_id: str, enabled: bool) -> str:
    return _guard(lambda: str(_studio.set_op_enabled(name, op_id, enabled)))


@mcp.tool(description="List a piece's ops in order with their params.")
def ms_list_ops(name: str, voice: str | None = None) -> str:
    return _guard(lambda: _j(_studio.list_ops(name, voice)))


# -- views -----------------------------------------------------------------

@mcp.tool(description=(
    "The score: a pitch-by-time grid, one glyph per voice, every column labelled "
    "by bar. Onsets are uppercase and sustains lowercase. This is the view that "
    "makes counterpoint visible -- crossing voices, accidental doublings and a "
    "bass that never moves are all shapes here. glyphs='degree' prints scale "
    "degrees instead, for checking a line against the harmony."))
def ms_score(name: str, bars: list | None = None, res: str = "1/8",
             glyphs: str = "voice", voices: list | None = None,
             upto: str | None = None) -> str:
    return _guard(_studio.score, name, bars=tuple(bars) if bars else None, res=res,
                  glyphs=glyphs, voices=voices, upto=upto)


@mcp.tool(description="The form and harmony at a glance: sections, keys, tempos, chords.")
def ms_chart(name: str) -> str:
    return _guard(_studio.chart, name)


@mcp.tool(description=(
    "Where every theme appears and in what shape. Ask this before adding more "
    "material: a cue whose theme is stated four times unchanged has no "
    "development, and a cue whose sections share no material has no unity."))
def ms_motif_map(name: str) -> str:
    return _guard(_studio.motifs, name)


@mcp.tool(description=(
    "The squint test: one column per bar showing density, register, dynamics and "
    "voice count. If these lines are flat the piece is flat, and no amount of "
    "good writing inside the bars will fix it."))
def ms_squint(name: str) -> str:
    return _guard(_studio.squint, name)


@mcp.tool(description="One voice as an event list: position, pitch, degree, duration, dynamic.")
def ms_part(name: str, voice: str, bars: list | None = None) -> str:
    return _guard(_studio.voice, name, voice, bars=tuple(bars) if bars else None)


@mcp.tool(description="Counts, ranges, per-voice note totals and motif coverage.")
def ms_stats(name: str) -> str:
    return _guard(lambda: _j(_studio.stats(name)))


@mcp.tool(description=(
    "Run the critique pass: range and polyphony violations, parallel fifths, "
    "voice crossing, muddy low intervals, unresolved clashes, harmonic stasis, "
    "flat dynamics, verbatim repeats and themes that never develop. Reports "
    "bar positions."))
def ms_lint(name: str) -> str:
    return _guard(lambda: report(_studio.lint(name)))


# -- import and analysis ---------------------------------------------------

@mcp.tool(description=(
    "Import an existing piece so the studio can analyze it. MIDI is EXACT -- every "
    "pitch and onset comes from the file. Audio is an ESTIMATE produced by melody "
    "tracking, and comes back with a confidence figure and the reasons behind it; "
    "on dense multi-layered mixes it will merge voices and chase accompaniment. "
    "Prefer MIDI whenever it exists. The result is an ordinary piece: every view, "
    "the critique pass and every export work on it unchanged."))
def ms_import(name: str, path: str, kind: str = "auto", instrument: str = "piano",
              tempo: int | None = None, overwrite: bool = False) -> str:
    return _guard(lambda: _j(_studio.import_music(name, path, kind=kind,
                                                  instrument=instrument, tempo=tempo,
                                                  overwrite=overwrite)))


@mcp.tool(description=(
    "Find repeated melodic shapes in a piece. Every candidate is tested against a "
    "null model -- the same intervals, shuffled -- and dropped if it appears about "
    "as often by chance. Degenerate shapes (repeated notes, pure alternation, plain "
    "scale runs) are refused outright, because any long melody contains thousands "
    "of them and they are also exactly what a failing pitch tracker produces."))
def ms_find_motifs(name: str, min_notes: int = 4, max_notes: int = 10,
                   p_max: float = 0.05) -> str:
    return _guard(lambda: _studio.find_motifs(name, min_notes=min_notes,
                                              max_notes=max_notes, p_max=p_max)["report"])


@mcp.tool(description=(
    "Find melodic shapes shared across several pieces -- the leitmotif question. "
    "Matching is on intervals, so a theme still matches transposed into another "
    "key. A pattern must clear the significance test in EVERY piece it is claimed "
    "to appear in. If the sources are estimated transcriptions the report says so: "
    "a shared-theme claim is only as good as the weakest transcription under it."))
def ms_compare(names: list, require: int | None = None, p_max: float = 0.02) -> str:
    return _guard(lambda: _studio.compare(names, require=require, p_max=p_max)["report"])


@mcp.tool(description=(
    "Turn a discovered pattern into a named motif on the piece, so you can play it, "
    "develop it and hear it. This is how you check a find: state it plainly and "
    "listen to whether it is the theme you thought you heard."))
def ms_adopt_pattern(name: str, motif: str, index: int = 0, unit: str = "1/8") -> str:
    return _guard(lambda: _j(_studio.adopt_pattern(name, motif, index, unit)))


# -- export ----------------------------------------------------------------

@mcp.tool(description="Write a standard MIDI file and return its path.")
def ms_export_midi(name: str, path: str | None = None) -> str:
    return _guard(lambda: str(_studio.export_midi(name, path)))


@mcp.tool(description=(
    "The tension curve: one column per bar for how far the harmony is from home, "
    "how much is sounding off the chord, how surprising the tune and the chord "
    "changes are, and the three combined -- then a reading: where tension peaks, "
    "whether the loud passage was prepared, where the piece releases, where it "
    "sits level, and the least expected moments. squint shows how much is "
    "happening; this shows whether it is going anywhere. A model of tonal "
    "expectation, not a measurement."))
def ms_tension(name: str) -> str:
    return _guard(lambda: _studio.tension(name))


@mcp.tool(description=(
    "Listen, as far as an agent can: render every voice alone and measure the "
    "audio. Per bar: loudness, brightness, roughness, who carries the tune, who "
    "is actually loudest, and how far the tune clears everything else; a level "
    "table by voice and section; and every note that did not really sound. Use "
    "it before handing a render to a person -- an accompaniment as loud as the "
    "tune, or a note that was cut off, is in these numbers and in no score view. "
    "soundfont='auto' measures the sampled render, which can differ from the "
    "built-in one. Takes as long as a render."))
def ms_hear(name: str, soundfont: str | None = None) -> str:
    return _guard(lambda: _studio.hear(
        name, source="soundfont" if soundfont else "models", soundfont=soundfont))


@mcp.tool(description=(
    "Render to a WAV and return its path, so a person can actually listen. The "
    "ASCII views tell you whether the writing is correct; only this tells you "
    "whether the music works. Voices are played through instrument models by "
    "default. soundfont='auto' (or a path to an .sf2/.sf3) renders sampled "
    "instruments through FluidSynth instead, when both are installed."))
def ms_export_wav(name: str, path: str | None = None, stereo: bool = True,
                  reverb: bool | None = None, soundfont: str | None = None) -> str:
    return _guard(lambda: str(_studio.export_wav(name, path, stereo=stereo,
                                                 reverb=reverb, soundfont=soundfont)))


def main() -> None:
    global _studio
    if len(sys.argv) > 1:
        _studio = Studio(Path(sys.argv[1]))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
