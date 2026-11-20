"""The render's own table of the form must agree with the piece it was built from.

``render._Timeline`` answers "which section, key, chord and bar is this tick
in" for every note of a render, by bisection instead of by walking the section
list. It is only allowed to be faster: wherever it and ``Piece`` could
disagree -- a change of meter, a change of key, harmony that overlaps or stops
short, a tick before the start or past the end -- they are asked the same
question here.
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

from musicstudio import Piece, Section
from musicstudio.doc import HarmonyEntry

# ``musicstudio.render`` the attribute is the function; this is the module.
rmod = importlib.import_module("musicstudio.render")


def _piece() -> Piece:
    piece = Piece("form", "D minor", tempo=100)
    piece.sections = [
        Section("a", 2, "4/4"),
        Section("b", 3, "6/8", key="F major", dynamic="p"),
        Section("c", 1, "5/4"),
        Section("d", 2, "3/4", key="A minor", dynamic="ff"),
    ]
    piece.harmony = [
        HarmonyEntry("1", "i"),
        HarmonyEntry("2:3", "V7", "1/4"),      # ends early: a gap with no chord
        HarmonyEntry("3", "I", "1/1"),         # runs on under the next entry
        HarmonyEntry("3:4", "IV"),
        HarmonyEntry("6", "bVI"),
        HarmonyEntry("7:2", "i"),
    ]
    return piece


def test_the_timeline_answers_as_the_piece_does_at_every_tick():
    piece = _piece()
    tl = rmod._Timeline(piece)
    assert tl.total == piece.total_ticks
    assert tl.spans == piece.harmony_spans()
    for tick in range(-600, piece.total_ticks + 2000, 20):
        assert tl.section_of(tick) is piece.section_of_tick(tick), tick
        assert tl.key_at(tick) == piece.key_at(tick), tick
        assert tl.chord_at(tick) == piece.chord_at(tick), tick
        assert tl.chord_at(tick) == piece.chord_at(tick), tick   # and when remembered
        assert tl.position_of(tick) == piece.position_of(tick), tick
        assert tl.bar_start(tick) == piece.tick_of(piece.position_of(tick)[0]), tick


def test_the_timeline_places_a_position_as_the_piece_does():
    piece = _piece()
    tl = rmod._Timeline(piece)
    for bar in range(1, piece.total_bars + 4):   # to the end and past it
        assert tl.tick_of(bar) == piece.tick_of(bar), bar
    for bar in (0, -1):                          # there is no bar before the first
        with pytest.raises(ValueError, match="bar numbers start at 1"):
            tl.tick_of(bar)
    for bar in range(1, piece.total_bars + 4):
        for beat in ("1", "2", "2.5", "3.75", "7/3", "9"):
            pos = f"{bar}:{beat}"
            assert tl.tick_of(pos) == piece.tick_of(pos), pos
    with pytest.raises(ValueError, match="bad position"):
        tl.tick_of("two")


def test_a_piece_with_no_form_is_still_the_pieces_to_answer_for():
    piece = Piece("empty", "C major")
    tl = rmod._Timeline(piece)
    assert tl.total == 0
    assert tl.position_of(0) == piece.position_of(0)
    assert tl.key_at(0) == piece.key_at(0)
    assert tl.chord_at(0) == piece.chord_at(0)
    with pytest.raises(ValueError, match="no sections yet"):
        tl.tick_of("1")


def test_copying_a_note_with_changes_is_dataclasses_replace():
    """``_with`` skips ``Note.__init__``; this fails the day that stops being
    the same thing (a ``__post_init__``, a slot, a field that is not stored)."""
    note = rmod.Note("flute", 62, 480, 240, 80, "play_1", "hero", "hero_inv", "invert", 3,
                     slur=True, tune=0.5, lyric="la", sung="l a", word="la#0/1")
    changed = {"voice": "oboe", "pitch": 65, "start": 0, "dur": 1, "velocity": 1,
               "op": "x", "motif": None, "played": None, "form": "chopped",
               "degree": None, "percussive": True, "slur": False, "ornament": True,
               "tune": -0.25, "lyric": "", "sung": "", "word": ""}
    assert set(changed) == {f.name for f in dataclasses.fields(rmod.Note)}
    for name, value in changed.items():
        made = rmod._with(note, **{name: value})
        assert made == dataclasses.replace(note, **{name: value})
        assert made is not note and vars(made).keys() == vars(note).keys()
    assert rmod._with(note, **changed) == dataclasses.replace(note, **changed)
    assert note.voice == "flute" and note.pitch == 62      # the original is untouched
