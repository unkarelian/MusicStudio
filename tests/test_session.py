"""Tests for the session layer: history, the cache, piece-level edits, the CLI,
and the audio render.

The history tests matter more than they look. Every mutation autosaves, which is
what makes the studio safe to use from a stream of tool calls -- and also what
would make a bad edit permanent if undo did not exist or the cache could drift
from the file.
"""

from __future__ import annotations

import json
import wave

import pytest

from musicstudio import Piece, Section, Studio, Voice, audio
from musicstudio.cli import main


def _studio(tmp_path) -> Studio:
    s = Studio(tmp_path)
    s.create("p", key="C major", sections=[("A", 4)])
    s.set_harmony("p", [["1", "I"], ["3", "V7"]])
    s.add_voice("p", "lead", "violin")
    return s


# --------------------------------------------------------------------------
# undo / redo
# --------------------------------------------------------------------------

def test_undo_takes_back_the_last_change_and_redo_reapplies_it(tmp_path):
    s = _studio(tmp_path)
    s.add_op("p", "lead", "phrase", id="line", steps="0 2 4 2", at="1")
    assert s.render("p").by_voice("lead")

    res = s.undo("p")
    assert res.ok and "restored" in res.message
    assert not s.render("p").by_voice("lead")
    with pytest.raises(KeyError):
        s.get("p").find_op("line")

    s.redo("p")
    assert len(s.render("p").by_voice("lead")) == 4


def test_a_new_change_after_undo_discards_the_redo_branch(tmp_path):
    s = _studio(tmp_path)
    s.add_op("p", "lead", "phrase", id="a", steps="0 2", at="1")
    s.undo("p")
    assert s.history("p")["redo"] == 1
    s.add_op("p", "lead", "phrase", id="b", steps="4 2", at="1")
    assert s.history("p")["redo"] == 0
    with pytest.raises(ValueError, match="nothing to redo"):
        s.redo("p")


def test_undo_reports_the_notes_it_changed(tmp_path):
    s = _studio(tmp_path)
    s.add_op("p", "lead", "phrase", id="line", steps="0 2 4", at="1")
    assert "3 notes removed" in s.undo("p").view


def test_a_deleted_piece_can_be_undeleted(tmp_path):
    s = _studio(tmp_path)
    s.delete("p")
    with pytest.raises(KeyError):
        s.get("p")
    s.undo("p")
    assert s.get("p").get_voice("lead").instrument == "violin"
    s.redo("p")
    assert not s.path_for("p").exists()


def test_history_depth_is_bounded(tmp_path, monkeypatch):
    import musicstudio.studio as studio_mod
    monkeypatch.setattr(studio_mod, "HISTORY_DEPTH", 5)
    s = _studio(tmp_path)
    for i in range(12):
        s.update_section("p", "A", dynamic=["p", "f"][i % 2])
    assert s.history("p")["undo"] == 5


# --------------------------------------------------------------------------
# the cache never outranks the file
# --------------------------------------------------------------------------

def test_a_failed_mutation_does_not_leave_a_half_applied_edit_behind(tmp_path):
    """update_section sets the field before validating it. Without eviction the
    bad value would sit in the cache and be saved by the next good call."""
    s = _studio(tmp_path)
    with pytest.raises(KeyError):
        s.update_section("p", "A", dynamic="loud")
    assert s.get("p").get_section("A").dynamic == "mf"
    s.add_voice("p", "low", "cello", role="bass")
    on_disk = json.loads(s.path_for("p").read_text())
    assert on_disk["sections"][0]["dynamic"] == "mf"


def test_an_edit_made_outside_the_session_is_not_overwritten(tmp_path):
    s = _studio(tmp_path)
    s.get("p")                                   # warm the cache
    other = Studio(tmp_path)
    other.add_voice("p", "low", "cello", role="bass")
    s.add_op("p", "lead", "phrase", id="line", steps="0 2", at="1")
    names = [v.name for v in Piece.load(s.path_for("p")).voices]
    assert names == ["lead", "low"]


# --------------------------------------------------------------------------
# piece-level edits
# --------------------------------------------------------------------------

def test_an_added_section_follows_the_piece_tempo(tmp_path):
    """A section that copies the tempo it was created at is left behind when the
    piece is retimed -- the bug the Section docstring warns about."""
    s = _studio(tmp_path)
    s.add_section("p", "B", bars=4)
    assert s.get("p").get_section("B").tempo is None
    s.update_piece("p", tempo=120)
    p = s.get("p")
    assert p.tempo_of(p.get_section("B")) == 120


def test_changing_the_key_transposes_everything_written_in_degrees(tmp_path):
    s = _studio(tmp_path)
    s.add_op("p", "lead", "phrase", id="line", steps="0 2 4", at="1", octave=4)
    before = [n.pitch for n in s.render("p").notes]
    s.update_piece("p", key="D major")
    after = [n.pitch for n in s.render("p").notes]
    assert [b - a for a, b in zip(before, after)] == [2, 2, 2]


def test_a_key_change_that_breaks_the_harmony_is_refused_and_leaves_the_piece(tmp_path):
    s = _studio(tmp_path)
    with pytest.raises(ValueError, match="7-note scale"):
        s.update_piece("p", key="C pentatonic_major")
    assert s.get("p").key.name == "C major"


def test_a_loop_is_not_asked_to_end_on_the_tonic(tmp_path):
    s = _studio(tmp_path)
    s.add_op("p", "lead", "phrase", id="line", steps="0 2 4 2 1 3 4 1", at="1",
             unit="1/2")
    assert "cadence_missing" in {f.code for f in s.lint("p")}
    s.update_piece("p", loop=True)
    assert "cadence_missing" not in {f.code for f in s.lint("p")}
    assert Piece.load(s.path_for("p")).loop is True


def test_bad_dynamics_and_pans_fail_where_they_are_written():
    with pytest.raises(KeyError):
        Section("A", 4, dynamic="loud")
    with pytest.raises(KeyError):
        Voice("v", "violin", dynamic="medium")
    with pytest.raises(ValueError):
        Voice("v", "violin", pan=3)


def test_a_voice_another_voice_doubles_cannot_be_removed(tmp_path):
    s = _studio(tmp_path)
    s.add_voice("p", "shadow", "viola", role="counter")
    s.add_op("p", "shadow", "double", id="d", source="lead", octaves=-1)
    with pytest.raises(ValueError, match="doubled by"):
        s.remove_voice("p", "lead")


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def test_the_cli_drives_a_whole_edit_undo_cycle(tmp_path, capsys):
    pj = str(tmp_path)
    assert main(["-p", pj, "new", "c", "--key", "d minor", "--form", "miniature"]) == 0
    assert main(["-p", pj, "harmony", "c", "1=i", "5=iv", "9=V7", "12=i"]) == 0
    assert main(["-p", pj, "voice", "c", "lead", "flute", "--pan", "-0.3"]) == 0
    assert main(["-p", pj, "op", "c", "lead", "phrase", "--id", "l",
                 "steps=0 2 4 2", "at=1"]) == 0
    assert main(["-p", pj, "toggle", "c", "l", "off"]) == 0
    assert main(["-p", pj, "undo", "c"]) == 0
    assert main(["-p", pj, "setsection", "c", "A", "dynamic=p", "tempo=70"]) == 0
    assert main(["-p", pj, "piece", "c", "--loop"]) == 0
    capsys.readouterr()
    assert main(["-p", pj, "history", "c"]) == 0
    # harmony, voice, op, toggle, (undo pops one), setsection, piece
    assert json.loads(capsys.readouterr().out) == {"undo": 5, "redo": 0}
    p = Studio(tmp_path).get("c")
    assert p.loop and p.get_voice("lead").pan == -0.3
    assert p.get_voice("lead").find("l").enabled          # the toggle was undone
    assert p.get_section("A").dynamic == "p"


def test_cli_errors_are_one_line_and_exit_2(tmp_path, capsys):
    assert main(["-p", str(tmp_path), "lint", "nope"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: no piece 'nope'") and "Traceback" not in err


def test_the_mcp_guard_turns_every_expected_failure_into_text():
    pytest.importorskip("mcp")
    from musicstudio.mcp_server import _guard

    def boom(exc):
        raise exc

    for exc in (IndexError("pattern 3 out of range"), RuntimeError("needs ffmpeg"),
                KeyError("no piece 'x'")):
        out = _guard(boom, exc)
        assert out.startswith("error: ") and "Traceback" not in out


# --------------------------------------------------------------------------
# audio
# --------------------------------------------------------------------------

def _tiny() -> Piece:
    p = Piece("tiny", "C major", tempo=120, style="chamber")
    p.sections.append(Section("A", 1))
    p.voices.append(Voice("v", "flute", "melody", pan=-1.0))
    p.add_op("v", "phrase", id="f", steps="0 2 4 7", at="1", unit="1/4")
    return p


def test_the_wav_is_stereo_and_long_enough_to_hold_the_piece(tmp_path):
    path = audio.save_wav(_tiny(), tmp_path / "t.wav")
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 2 and w.getsampwidth() == 2
        assert w.getnframes() / w.getframerate() >= 2.0    # one 4/4 bar at q=120


def test_a_hard_left_voice_is_silent_on_the_right():
    left, right = audio.synthesize(_tiny(), reverb=False)
    peak_l = max(abs(x) for x in left)
    peak_r = max(abs(x) for x in right)
    assert peak_l > 0.05 and peak_r < peak_l * 1e-6


def test_voices_are_seated_and_low_end_stays_central():
    p = Piece("seat", "C major")
    p.voices += [Voice("vln", "violin"), Voice("vc", "cello"),
                 Voice("bass", "contrabass", role="bass"), Voice("vln2", "violin")]
    pans = audio.pan_positions(p)
    assert pans["vln"] < 0 < pans["vc"]
    assert abs(pans["bass"]) < abs(audio.SEATS["contrabass"])
    assert pans["vln"] != pans["vln2"]          # two violins are two players


def test_oscillators_drop_partials_above_nyquist():
    spec = audio.VOICES["saw"]
    high = audio._partials_under(spec, 4186.0)       # C8
    assert all(p * 4186.0 < audio.NYQUIST for p, _ in high)
    assert len(audio._partials_under(spec, 65.4)) == len(spec["partials"])


def test_the_pure_python_and_numpy_paths_render_the_same_piece(monkeypatch):
    np = pytest.importorskip("numpy")
    p = _tiny()
    p.get_voice("v").pan = 0.0
    fast_l, _ = audio.synthesize(p, reverb=False)
    monkeypatch.setattr(audio, "_np", None)
    slow_l, _ = audio.synthesize(p, reverb=False)
    slow = np.frombuffer(slow_l, dtype=np.float64)
    assert len(slow) == len(fast_l)
    # Not bit-identical: the fast path interpolates the table and adds vibrato.
    assert np.corrcoef(slow, fast_l)[0, 1] > 0.9


def test_the_vectorized_envelope_matches_the_reference():
    np = pytest.importorskip("numpy")
    for n in (1, 7, 2000, 90000):
        for spec in audio.VOICES.values():
            ref = np.frombuffer(audio._envelope(n, spec["adsr"]), dtype=np.float64)
            assert np.allclose(ref, audio._envelope_np(n, spec["adsr"]))


def test_reverb_lengthens_the_tail_without_moving_the_music():
    np = pytest.importorskip("numpy")
    p = _tiny()
    dry, _ = audio.synthesize(p, reverb=False)
    wet, _ = audio.synthesize(p, reverb=True)
    assert len(wet) >= len(dry)
    onset = int(np.argmax(np.abs(dry) > 1e-3))
    assert abs(int(np.argmax(np.abs(wet) > 1e-3)) - onset) < 50
