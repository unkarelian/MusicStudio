"""Faults found by a review of the whole codebase, each held by a test here.

Every one of them was an input the studio accepted and then did the wrong
thing with, quietly or with an error that did not say where.
"""
from __future__ import annotations

import pytest

from musicstudio import Piece, Section, Studio, Voice, render
from musicstudio.cli import main
from musicstudio.midi import save_midi
from musicstudio.readback import score
from musicstudio.score import ScoreError, compile_score

SCORE = """
piece {name} key="A minor" tempo=120 style=electronic
section A bars=4
section B bars=4
harmony
  @A: i VI i VI
  @B: {chords}
voice lead saw_lead role=melody octave=5
  play motif=cell at=@A times=2
motif cell = 0 2 4:1/4 2
stop from=@B.4:3 until=@B.end keep=[{keep}]
"""


def _text(name="small", chords="iv V7 i i", keep="lead") -> str:
    return SCORE.format(name=name, chords=chords, keep=keep)


def _scale_piece() -> Piece:
    p = Piece("s", "C major", style="freeform")
    p.sections.append(Section("A", 4))
    p.voices.append(Voice("v", "piano", "melody"))
    p.add_motif("run", "0 1 2 3 4 5 6 7")
    p.add_op("v", "play", id="tune", motif="run", at="1", times=4)
    return p


# -- render -----------------------------------------------------------------

@pytest.mark.parametrize("kind, params", [
    ("humanize", {"timing": 30}),
    ("swing", {"amount": 0.66}),
])
def test_until_alone_ends_a_modifier_where_it_says(kind, params):
    """``until`` without ``from`` was ignored by lyrics, double, humanize,
    shape and swing: the op ran to the end of the piece."""
    plain = _scale_piece()
    before = {(n.start, n.pitch) for n in render(plain).notes}
    p = _scale_piece()
    p.add_op("v", kind, id="m", until="3", **params)
    after = {(n.start, n.pitch) for n in render(p).notes}
    edge = p.tick_of("3")
    assert {x for x in before if x[0] >= edge} == {x for x in after if x[0] >= edge}
    assert {x for x in before if x[0] < edge} != {x for x in after if x[0] < edge}


def test_a_bar_number_below_one_is_refused_as_a_number_too():
    p = _scale_piece()
    for bad in (0, -1, "0"):
        with pytest.raises(ValueError, match="bar numbers start at 1"):
            p.tick_of(bad)


# -- the score language --------------------------------------------------------

def test_a_stop_that_keeps_a_voice_that_is_not_there_names_its_line():
    with pytest.raises(ScoreError, match="no voice 'nobody'") as err:
        compile_score(_text(keep="nobody"))
    assert err.value.line and "keep=[nobody]" in str(err.value)


def test_a_bad_chord_in_the_harmony_names_its_line():
    with pytest.raises(ScoreError) as err:
        compile_score(_text(chords="iv Q i i"))
    assert err.value.line and "@B: iv Q i i" in str(err.value)


# -- views ---------------------------------------------------------------------

def test_one_bar_asked_for_past_the_end_is_the_last_bar():
    p = _scale_piece()
    assert score(p, bars=500, legend=False) == score(p, bars=4, legend=False)
    assert score(p, bars=0, legend=False) == score(p, bars=1, legend=False)


# -- the session ---------------------------------------------------------------

def test_a_build_knows_its_piece_whatever_it_is_called(tmp_path, capsys):
    """The CLI and the MCP server took the name out of the message by its
    quotes, which a name with a quote in it moves."""
    s = Studio(tmp_path)
    s.create("it's", sections=[("A", 2)])
    s.source("it's", write=True)
    assert s.build("it's").piece == "it's"
    pytest.importorskip("numpy")  # --hear measures the render
    assert main(["-p", str(tmp_path), "build", "it's", "--hear"]) == 0
    assert "error" not in capsys.readouterr().err


def test_a_section_takes_its_fields_and_nothing_else(tmp_path):
    s = Studio(tmp_path)
    s.build(text=_text())
    for bad in ("to_json", "length", "bar_ticks"):
        with pytest.raises(ValueError, match="section has no field"):
            s.update_section("small", "A", **{bad: 5})
    assert s.update_section("small", "A", dynamic="f").ok
    assert s.get("small").get_section("A").dynamic == "f"


def test_an_import_that_fails_leaves_the_piece_that_was_there(tmp_path):
    s = Studio(tmp_path)
    s.build(text=_text())
    before = s.path_for("small").read_text()
    undo = s.history("small")
    save_midi(_scale_piece(), tmp_path / "in.mid")
    with pytest.raises(KeyError):
        s.import_music("small", str(tmp_path / "in.mid"), instrument="no_such_thing",
                       overwrite=True)
    assert s.path_for("small").read_text() == before
    assert s.history("small") == undo
    got = s.import_music("small", str(tmp_path / "in.mid"), overwrite=True)
    assert got["events"] == 32 and len(render(s.get("small")).notes) == 32
    # One import is one checkpoint: undo is the piece as it was, not an empty one.
    assert s.undo("small").ok and s.path_for("small").read_text() == before


def test_a_changed_preutterance_is_not_answered_from_the_entry_as_it_was(tmp_path):
    """The unit cache was keyed by file, offset and cutoff only, so an oto.ini
    edited while the server ran kept its old landmarks."""
    import dataclasses
    import wave

    np = pytest.importorskip("numpy")
    from musicstudio import utau
    from musicstudio.vocal import SR
    t = np.arange(SR) / SR
    with wave.open(str(tmp_path / "a.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.sin(2 * np.pi * 220 * t) * 12000).astype("<i2").tobytes())
    e = utau.Entry("a", tmp_path / "a.wav", 0.1, 0.15, -600.0, 0.1, 0.04)
    _, start, pre, fixed, _, _ = utau._unit(e)
    later = utau._unit(dataclasses.replace(e, pre=0.2, consonant=0.3))
    assert later[2] - start == int(0.2 * SR) and later[3] - start == int(0.3 * SR)
    assert (pre, fixed) != (later[2], later[3])
