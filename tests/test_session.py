"""Tests for the session layer: history, the cache, piece-level edits, the CLI,
and the audio render.

The history tests matter more than they look. Every mutation autosaves, which is
what makes the studio safe to use from a stream of tool calls -- and also what
would make a bad edit permanent if undo did not exist or the cache could drift
from the file.
"""

from __future__ import annotations

import json
import math
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

def test_undo_and_redo_never_reach_outside_the_project(tmp_path):
    """The piece name is checked before .history is touched: undo pops (and
    deletes) a snapshot, so checking the name afterwards is too late."""
    s = _studio(tmp_path / "project")
    elsewhere = tmp_path / "elsewhere"
    for name in ("../../elsewhere", str(elsewhere)):
        for verb, stack in ((s.undo, "undo"), (s.redo, "redo")):
            snapshot = elsewhere / stack / "000001.json"
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text("{}")
            with pytest.raises(ValueError, match="not a piece name"):
                verb(name)
            assert snapshot.exists(), f"{stack}({name!r}) deleted a file outside the project"
        with pytest.raises(ValueError, match="not a piece name"):
            s.history(name)


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


def test_an_edit_that_cannot_be_rendered_never_reaches_the_file(tmp_path):
    """The piece is rendered *before* it is saved. Saved first, an op that
    validates but will not render was on disk by the time the render raised,
    and evicting the cache only reloaded the broken piece."""
    s = _studio(tmp_path)
    before = s.path_for("p").read_text()
    voice = s.get("p").voices[0].name
    with pytest.raises(Exception):
        s.add_op("p", voice, "phrase", id="bad", steps="not-a-note", at="1")
    assert s.path_for("p").read_text() == before
    assert all(op.id != "bad" for _, op in s.get("p").all_ops())
    assert s.history("p") == s.history("p") and not list(s.pieces_dir.glob(".*part"))
    s.lint("p")                                   # and the piece still renders


def test_a_piece_name_is_a_file_name_and_nothing_more(tmp_path):
    s = _studio(tmp_path)
    for name in ("../escaped", "a/b", "..", "", "/abs"):
        with pytest.raises(ValueError, match="not a piece name"):
            s.path_for(name)
    with pytest.raises(ValueError, match="not a piece name"):
        s.create("../escaped")
    assert not (tmp_path / "escaped.ms.json").exists()


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
    fast_l, _ = audio.synthesize(p, reverb=False, models=False)
    monkeypatch.setattr(audio, "_np", None)
    slow_l, _ = audio.synthesize(p, reverb=False)
    slow = np.frombuffer(slow_l, dtype=np.float64)
    assert len(slow) == len(fast_l)
    # Not bit-identical: the fast path interpolates the table and adds vibrato.
    assert np.corrcoef(slow, fast_l)[0, 1] > 0.9


def _loudness(x, np, hop=2205):
    """RMS in 50 ms frames: where the notes are and how loud, timbre aside."""
    x = np.asarray(x, dtype=np.float64)
    frames = x[:len(x) // hop * hop].reshape(-1, hop)
    return np.sqrt((frames ** 2).mean(axis=1))


def test_instrument_models_change_the_sound_and_not_the_music():
    """A model may make a flute sound like a flute. It may not move a note,
    lengthen the piece, or re-seat a player -- that is the arrangement, and the
    arrangement is the same on every path."""
    np = pytest.importorskip("numpy")
    p = _tiny()
    plain_l, plain_r = audio.synthesize(p, reverb=False, models=False)
    model_l, model_r = audio.synthesize(p, reverb=False, models=True)
    assert len(model_l) == len(plain_l)
    assert np.abs(model_r).max() < np.abs(model_l).max() * 1e-6      # still hard left
    a, b = _loudness(plain_l, np), _loudness(model_l, np)
    assert np.corrcoef(a, b)[0, 1] > 0.8
    assert 0.5 < b.mean() / a.mean() < 2.0                            # not remixed
    assert np.corrcoef(plain_l, model_l)[0, 1] < 0.9                  # but not the same wave


def test_every_instrument_has_a_voice_and_a_stable_one():
    """Each model produces sound, never a NaN, and the same sound twice --
    in-process and across processes, since the seeds come from the note."""
    np = pytest.importorskip("numpy")
    import subprocess, sys
    from musicstudio import synth
    for name in synth.MODELS:
        ctx = synth.NoteCtx(name, "v", 60, 0.0, 0.5, 80, None, False, ("v", 0, 60))
        once = sum(sig for sig, _ in synth.render_note(ctx, 10 ** 7))
        again = sum(sig for sig, _ in synth.render_note(ctx, 10 ** 7))
        assert np.isfinite(once).all() and np.abs(once).max() > 0.01, name
        assert np.array_equal(once, again), name
    code = ("from musicstudio import synth; import zlib;"
            "c=synth.NoteCtx('violin','v',60,0.0,0.5,80,None,False,('v',0,60));"
            "print(zlib.crc32(sum(s for s,_ in synth.render_note(c,10**7)).tobytes()))")
    runs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={"PYTHONHASHSEED": seed, "PATH": ""}).stdout
            for seed in ("1", "2")}
    assert len(runs) == 1 and runs != {""}


def test_a_slurred_note_is_not_attacked_again():
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def onset(slur_from):
        ctx = synth.NoteCtx("violin", "v", 67, 0.0, 0.6, 80, slur_from, False, ("v", 0, 67))
        sig = synth.render_note(ctx, 10 ** 7)[0][0]
        spec = np.abs(np.fft.rfft(sig[:2048] * np.hanning(2048)))
        f = np.fft.rfftfreq(2048, 1 / synth.SR)
        return spec[f > 3000].sum() / spec.sum()

    # The bow-noise burst that starts a detached note is absent from a slur.
    assert onset(65) < onset(None)


def test_only_legato_notes_are_joined():
    pytest.importorskip("numpy")
    from musicstudio import synth
    from musicstudio.render import render
    for articulation, joined in (("legato", 3), ("staccato", 0), (None, 0)):
        p = _tiny()
        p.update_op("f", articulation=articulation)
        notes = render(p).notes
        links = synth.slur_links(notes, audio._tick_seconds(p))
        assert sum(1 for frm, _ in links.values() if frm is not None) == joined


def test_a_ritardando_lengthens_the_piece_and_both_exports_agree():
    p = _tiny()
    steady = audio._tick_seconds(p)(p.total_ticks)
    p.sections[0].tempo_end = 60
    slowed = audio._tick_seconds(p)(p.total_ticks)
    assert slowed > steady * 1.1
    marks = p.tempo_map()
    assert marks[0][1] == 120 and marks[-1][1] == 60
    assert [bpm for _, bpm in marks] == sorted((bpm for _, bpm in marks), reverse=True)
    from musicstudio.midi import to_bytes
    assert to_bytes(p).count(b"\xff\x51\x03") == len(marks)


def test_a_soundfont_render_needs_a_soundfont_and_says_so(tmp_path, monkeypatch):
    monkeypatch.delenv("MUSICSTUDIO_SOUNDFONT", raising=False)
    monkeypatch.setattr(audio, "SOUNDFONT_DIRS", (str(tmp_path / "none"),))
    with pytest.raises(FileNotFoundError, match="--soundfont"):
        audio.find_soundfont()
    with pytest.raises(FileNotFoundError):
        audio.find_soundfont(tmp_path / "missing.sf2")
    bank = tmp_path / "FluidR3_GM.sf2"
    bank.write_bytes(b"RIFF")
    monkeypatch.setattr(audio, "SOUNDFONT_DIRS", (str(tmp_path),))
    assert audio.find_soundfont() == bank
    assert audio.find_soundfont("auto") == bank


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


# --------------------------------------------------------------------------
# fetching a SoundFont
# --------------------------------------------------------------------------

def _fake_deb(tmp_path, bank_bytes: bytes):
    """A minimal Debian package: an ar archive holding a data.tar.xz."""
    import hashlib, io, tarfile
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:xz") as tar:
        for name, data in (("./usr/share/sounds/sf3/Bank.sf3", bank_bytes),
                           ("./usr/share/doc/bank/copyright", b"MIT, as described")):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    data = buf.getvalue()

    def member(name: bytes, body: bytes) -> bytes:
        head = name.ljust(16) + b"0".ljust(12) + b"0".ljust(6) + b"0".ljust(6) \
            + b"100644".ljust(8) + str(len(body)).encode().ljust(10) + b"`\n"
        return head + body + (b"\n" if len(body) & 1 else b"")

    deb = b"!<arch>\n" + member(b"debian-binary", b"2.0\n") + member(b"data.tar.xz", data)
    path = tmp_path / "bank.deb"
    path.write_bytes(deb)
    return path, hashlib.sha256(deb).hexdigest()


def test_a_soundfont_is_installed_only_if_it_is_the_file_that_was_pinned(tmp_path, monkeypatch):
    from musicstudio import soundfonts
    sf = b"RIFF" + b"\x00" * 4 + b"sfbk" + b"samples"
    deb, digest = _fake_deb(tmp_path, sf)
    bank = soundfonts.Bank("test", "a test bank", deb.as_uri(), digest, 1, "Test_HQ.sf3",
                           member="usr/share/sounds/sf3/Bank.sf3",
                           license_member="usr/share/doc/bank/copyright")
    monkeypatch.setitem(soundfonts.BANKS, "test", bank)
    dest = tmp_path / "fonts"

    out = soundfonts.install("test", dest=dest, quiet=True)
    assert out == dest / "Test_HQ.sf3" and out.read_bytes() == sf
    assert (dest / "Test_HQ.LICENSE.txt").read_text() == "MIT, as described"
    assert soundfonts.installed(dest) == [out]
    # ...and the renderer finds it without being told where it is.
    monkeypatch.delenv("MUSICSTUDIO_SOUNDFONT", raising=False)
    monkeypatch.setattr(audio, "SOUNDFONT_DIRS", (str(dest),))
    assert audio.find_soundfont() == out

    # A download that is not the pinned file installs nothing at all.
    wrong = soundfonts.Bank("bad", "", deb.as_uri(), "0" * 64, 1, "Bad.sf3",
                            member="usr/share/sounds/sf3/Bank.sf3")
    monkeypatch.setitem(soundfonts.BANKS, "bad", wrong)
    with pytest.raises(ValueError, match="checksum mismatch"):
        soundfonts.install("bad", dest=dest, quiet=True)
    assert not (dest / "Bad.sf3").exists()
    assert [f.name for f in dest.iterdir() if f.name.startswith("Bad")] == []

    with pytest.raises(ValueError, match="sha256"):
        soundfonts.install(url="https://example.invalid/x.sf2", dest=dest)
    with pytest.raises(KeyError, match="unknown bank"):
        soundfonts.install("nope", dest=dest)


def test_the_hq_bank_is_preferred_over_the_others(tmp_path, monkeypatch):
    for name in ("FluidR3_GM.sf2", "MuseScore_General.sf3", "MuseScore_General_HQ.sf3"):
        (tmp_path / name).write_bytes(b"RIFF")
    monkeypatch.delenv("MUSICSTUDIO_SOUNDFONT", raising=False)
    monkeypatch.setattr(audio, "SOUNDFONT_DIRS", (str(tmp_path),))
    assert audio.find_soundfont().name == "MuseScore_General_HQ.sf3"


# --------------------------------------------------------------------------
# tension: where the piece leans
# --------------------------------------------------------------------------

from musicstudio import Key, render, tension  # noqa: E402
from musicstudio.doc import HarmonyEntry  # noqa: E402


def _cadence(chords, tune="0:1/1 | 1:1/1 | 0:1/1 | 0:1/1", dyn=("mf",) * 4) -> Piece:
    p = Piece("cad", "C major", tempo=90, style="chamber")
    for i, d in enumerate(dyn):
        p.sections.append(Section(f"s{i}", 1, dynamic=d))
    p.harmony = [HarmonyEntry(str(i + 1), c) for i, c in enumerate(chords)]
    p.voices += [Voice("vln", "violin", "melody", octave=5),
                 Voice("pad", "strings", "pad", octave=3)]
    p.add_op("vln", "phrase", id="t", steps=tune, at="1", octave=5)
    p.add_op("pad", "chords", id="c", at="1", bars=len(chords), voicing="pad")
    return p


def test_a_dominant_is_far_from_home_and_its_resolution_is_a_release():
    curve = tension.analyze(_cadence(["I", "IV", "V7", "I"]))
    home = [b.home for b in curve]
    assert home[0] == home[3] == 0.0 and home[1] < home[2]
    assert [b.function for b in curve] == ["tonic", "subdominant", "dominant", "tonic"]
    assert "bar 4" in " ".join(tension.reading(_cadence(["I", "IV", "V7", "I"]), curve))


def test_a_key_far_from_home_is_further_than_the_relative_major():
    home = Key.parse("e minor")
    assert tension.region_distance(home, home) == 0
    assert tension.region_distance(Key.parse("G major"), home) < \
        tension.region_distance(Key.parse("Bb major"), home)


def test_the_reading_says_whether_the_loud_passage_was_prepared():
    quiet_then_loud = ("p", "p", "p", "ff")
    prepared = _cadence(["I", "ii", "V7", "I"], dyn=quiet_then_loud)
    static = _cadence(["I", "I", "I", "I"], tune="0:1/1 | 0:1/1 | 0:1/1 | 0:1/1",
                      dyn=quiet_then_loud)
    said = " ".join(tension.reading(prepared, tension.analyze(prepared)))
    assert "is prepared" in said and "dominant" in said
    said = " ".join(tension.reading(static, tension.analyze(static)))
    assert "without harmonic preparation" in said


def test_a_chromatic_leap_is_more_surprising_than_a_step():
    step = tension.analyze(_cadence(["I"] * 4, tune="0:1/1 | 1:1/1 | 2:1/1 | 1:1/1"))
    leap = tension.analyze(_cadence(["I"] * 4, tune="0:1/1 | 1:1/1 | #8:1/1 | 1:1/1"))
    assert leap[2].surprise > step[2].surprise + 1.0
    assert "leap" in leap[2].moment[1]


def test_the_tune_is_the_melody_and_whoever_doubles_it():
    p = _cadence(["I", "IV", "V7", "I"])
    p.voices.append(Voice("fl", "flute", "counter"))
    p.add_op("fl", "double", id="d", source="vln", octaves=1)
    notes = render(p).notes
    assert tension.tune_at(p, notes, 0, 1920) == ("vln", {"vln", "fl"})
    p.get_voice("vln").muted = True
    assert tension.tune_at(p, render(p).notes, 0, 1920) == (None, set())


# --------------------------------------------------------------------------
# hear: measuring the render
# --------------------------------------------------------------------------

def _balance(tune_dyn: str, pad_dyn: str) -> Piece:
    p = _cadence(["I", "IV", "V7", "I"], tune="0 2 4 2 | 3 5 7 5 | 4 6 8 6 | 7:1/1")
    p.update_op("t", dynamic=tune_dyn, unit="1/4")
    p.update_op("c", dynamic=pad_dyn, tones=4)
    return p


def test_hear_reports_a_tune_under_its_accompaniment_and_not_a_clear_one():
    pytest.importorskip("numpy")
    from musicstudio import listen
    buried = listen.hear(_balance("pp", "ff"))
    clear = listen.hear(_balance("f", "pp"))
    assert all(b.tune == "vln" for b in buried.bars)
    assert max(b.margin for b in buried.bars) < 0 < min(b.margin for b in clear.bars)
    assert buried.bars[0].rival == "pad"
    assert "quieter than everything else" in " ".join(listen.reading(buried))
    assert "clears its accompaniment throughout" in " ".join(listen.reading(clear))
    text = listen.view(_balance("f", "pp"), heard=clear)
    assert "built-in instrument models" in text and "dBA by section" in text


def test_hear_finds_the_note_that_did_not_sound():
    np = pytest.importorskip("numpy")
    from musicstudio import listen
    p = Piece("w", "C major", tempo=120, style="chamber")
    p.sections.append(Section("A", 4))
    p.voices.append(Voice("pf", "piano", "melody", octave=4))
    p.add_op("pf", "phrase", id="f", at="1", unit="1/4",
             steps="0 2 4 5 | 7 5 4 2 | 0 2 4 5 | 7 5 4 2")
    r = render(p)
    to_sec = audio._tick_seconds(p)
    parts, _ = listen.stems(p, r)
    assert listen._weak_notes(p, r, parts, to_sec)[0] == []
    # Silence one note in the stem, as a stale note-off or a cancelled attack would.
    victim = sorted(r.notes, key=lambda n: n.start)[6]
    lo, hi = int(to_sec(victim.start) * listen.SR), int(to_sec(victim.end) * listen.SR)
    parts["pf"][lo:hi] *= 0.02
    weak, measured = listen._weak_notes(p, r, parts, to_sec)
    assert measured == 16 and [(w.bar, w.beat) for w in weak] == [(2, 3.0)]


def test_roughness_ranks_a_semitone_above_a_fifth_above_an_octave():
    np = pytest.importorskip("numpy")
    from musicstudio import listen
    t = np.arange(listen.SR) / listen.SR

    def pair(ratio):
        return listen.roughness(np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 440 * ratio * t))

    assert pair(2 ** (1 / 12)) > pair(1.5) * 3 and pair(1.5) >= pair(2.0)


def test_sampler_trims_and_curves_reach_the_midi_file():
    from musicstudio.midi import to_bytes, trim_to_volume
    assert trim_to_volume(-12) < trim_to_volume(0) < trim_to_volume(6) <= 127
    assert trim_to_volume(-12) == trim_to_volume(0) // 2            # 12 dB halves it
    p = _tiny()
    assert bytes([0xB0, 7]) not in to_bytes(p)                      # untouched by default
    data = to_bytes(p, trims={"v": -6.0})
    assert bytes([0xB0, 7, trim_to_volume(-6.0)]) in data
    plain, lifted = to_bytes(p), to_bytes(p, velocity_curve={"v": 0.5})
    at = plain.index(bytes([0x90])) + 2
    assert lifted[at] > plain[at]
    assert to_bytes(p, velocity_curve={"someone_else": 0.5}) == plain


# --------------------------------------------------------------------------
# kits, chopping, basses, processing
# --------------------------------------------------------------------------

from musicstudio import lint as run_lint  # noqa: E402
from musicstudio.ensemble import KIT_DRUMS  # noqa: E402

AMEN = {"kick": "x.x.......xx....", "snare": "....x..o.o..x..o", "hat": "x.x.x.x.x.x.x.x."}


def _groove(**beat) -> Piece:
    p = Piece("brk", "A minor", tempo=160, style="electronic")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("drums", "kit", "percussion"))
    p.add_op("drums", "beat", id="b", at="1", bars=2, **{"lanes": AMEN, **beat})
    return p


def test_a_beat_is_one_voice_playing_a_whole_kit():
    notes = render(_groove()).notes
    by_drum = {name: [n for n in notes if n.pitch == key] for name, key in KIT_DRUMS.items()}
    assert len(by_drum["kick"]) == 8 and len(by_drum["hat"]) == 16
    assert [n.start for n in by_drum["kick"]][:4] == [0, 240, 1200, 1320]
    snare = sorted(by_drum["snare"], key=lambda n: n.start)
    assert snare[1].velocity < snare[0].velocity * 0.6           # 'o' is a ghost
    assert all(n.percussive for n in notes)
    # Kick and hat together is one drummer, not a polyphony error.
    assert "polyphony_exceeded" not in {f.code for f in run_lint(_groove())}
    from musicstudio.midi import to_bytes
    kit808 = _groove()
    kit808.get_voice("drums").instrument = "kit_808"
    assert bytes([0xC9, 25]) in to_bytes(kit808)                  # the kit, on the drum channel


def test_beat_and_groove_say_which_of_them_a_voice_wants():
    p = _groove()
    with pytest.raises(ValueError, match="beat"):
        p.add_op("drums", "groove", id="g", at="1", bars=1, pattern="x...")
        render(p)
    p.remove_op("g")
    p.voices.append(Voice("sn", "snare", "percussion"))
    with pytest.raises(ValueError, match="kit"):
        p.add_op("sn", "beat", id="b2", at="1", bars=1, lanes=AMEN)
        render(p)
    p.remove_op("b2")
    with pytest.raises(ValueError, match="unknown drum"):
        p.update_op("b", lanes={"gong": "x..."})
        render(p)


def _hits(p: Piece) -> list[tuple[int, int]]:
    return sorted((n.start, n.pitch) for n in render(p).notes)


def test_chop_reorders_slices_and_the_plain_order_changes_nothing():
    plain = _hits(_groove())
    p = _groove()
    p.add_op("drums", "chop", id="c", **{"from": "1", "until": "3"},
             slices=8, order="0 1 2 3 4 5 6 7")
    assert _hits(p) == plain
    # Slot 4 takes slice 2: the snare's backbeat lands where slice 4 was.
    p.update_op("c", order="0 1 2 3 2 5 6 7")
    moved = _hits(p)
    assert (960, KIT_DRUMS["snare"]) in moved and moved != plain
    # Silence, and leaving a slot as written.
    p.update_op("c", order=". _ _ _ _ _ _ _")
    assert [h for h in _hits(p) if h[0] < 240] == [] \
        and [h for h in _hits(p) if 240 <= h[0] < 1920] == [h for h in plain if 240 <= h[0] < 1920]
    # Only the span is touched.
    p.update_op("c", order=".", **{"until": "2"})
    assert [h for h in _hits(p) if h[0] >= 1920] == [h for h in plain if h[0] >= 1920]
    assert [h for h in _hits(p) if h[0] < 1920] == []


def test_chop_retriggers_pitches_and_reverses():
    p = _groove()
    p.add_op("drums", "chop", id="c", **{"from": "1", "until": "2"}, slices=8,
             order="0*2 . . . . . . .")
    first = [n for n in render(p).notes if n.start < 240]
    # Slice 0 holds a kick and a hat on its first sixteenth; its first half, twice.
    assert sorted(n.start for n in first) == [0, 0, 120, 120]
    p.update_op("c", order="0^7 . . . . . . .")
    assert {n.tune for n in render(p).notes if n.start < 240} == {7.0}
    p.update_op("c", order="1r . . . . . . .")
    # Slice 1 has its kick and hat on its first sixteenth; backwards, on its last.
    assert {n.start for n in render(p).notes if n.start < 240} == {120}
    with pytest.raises(ValueError, match="chop token"):
        p.update_op("c", order="9")
        render(p)


def test_processing_ops_shape_the_sound_and_leave_the_notes_alone():
    np = pytest.importorskip("numpy")
    p = Piece("fx", "A minor", tempo=120, style="electronic")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("pad", "synth_lead", "melody", pan=0.0))
    p.add_op("pad", "phrase", id="f", steps="0:1/1 | 0:1/1", at="1", octave=3)
    before = render(p).notes
    dry, _ = audio.synthesize(p, reverb=False)

    def high_share(x, a, b):
        seg = x[int(a * audio.SR):int(b * audio.SR)]
        spec = np.abs(np.fft.rfft(seg)) ** 2
        f = np.fft.rfftfreq(len(seg), 1 / audio.SR)
        return spec[f > 1500].sum() / spec.sum()

    p.add_op("pad", "filter", id="lp", start=250, end=250, **{"from": "1", "until": "2"})
    assert render(p).notes == before
    wet, _ = audio.synthesize(p, reverb=False)
    assert len(wet) == len(dry)
    assert high_share(wet, 0.3, 1.7) < high_share(dry, 0.3, 1.7) * 0.05      # bar 1: closed
    assert high_share(wet, 2.3, 3.7) == pytest.approx(high_share(dry, 2.3, 3.7), rel=0.05)

    p.remove_op("lp")
    p.voices[0].instrument = "sub_bass"
    clean, _ = audio.synthesize(p, reverb=False)
    p.add_op("pad", "drive", id="d", amount=1.0)
    driven, _ = audio.synthesize(p, reverb=False)
    assert high_share(driven, 0.3, 1.7) > high_share(clean, 0.3, 1.7) * 20   # harmonics appear
    assert np.abs(driven).max() == pytest.approx(np.abs(clean).max(), rel=0.02)
    p.update_op("d", amount=0.0)
    p.add_op("pad", "crush", id="c", rate=4000, bits=6)
    crushed, _ = audio.synthesize(p, reverb=False)
    assert high_share(crushed, 0.3, 1.7) > high_share(clean, 0.3, 1.7) * 5
    with pytest.raises(ValueError, match="filter mode"):
        p.add_op("pad", "filter", id="bad", start=200, mode="bandpass")
        audio.synthesize(p, reverb=False)


def test_an_acid_note_opens_with_velocity_and_a_slide_does_not_reopen_it():
    """The acid machine's velocity is its cutoff knob: a loud note is brighter,
    not just louder. A note slid into keeps what is left of the last envelope
    instead of firing a new one, and the filter -- which does not follow the
    keyboard -- is never shut on the note itself, so a high note still sounds."""
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def note(pitch, vel, slur_from=None, name="acid_bass"):
        ctx = synth.NoteCtx(name, "v", pitch, 0.0, 0.1, vel, slur_from, False,
                            ("v", 0, pitch))
        return synth.render_note(ctx, 10 ** 7)[0][0]

    def centroid(sig):
        spec = np.abs(np.fft.rfft(sig[:2048] * np.hanning(2048)))
        return float((spec * np.fft.rfftfreq(2048, 1 / synth.SR)).sum() / spec.sum())

    def rms(sig):
        return float(np.sqrt(np.mean(sig ** 2)))

    for name in ("acid_bass", "acid_square"):
        assert centroid(note(43, 120, name=name)) > 2 * centroid(note(43, 40, name=name))
    assert centroid(note(43, 120, slur_from=50)) < centroid(note(43, 120))
    assert rms(note(88, 100)) > 0.25 * rms(note(43, 100))
    # It may not lengthen a note by more than its few milliseconds of release.
    assert len(note(43, 100)) <= int(0.13 * synth.SR)


def test_a_sub_bass_is_nearly_all_fundamental_and_a_reese_is_not():
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def low_share(name):
        ctx = synth.NoteCtx(name, "b", 33, 0.0, 1.0, 90, None, False, ("b", 0, 33))
        x = sum(sig for sig, _ in synth.render_note(ctx, 10 ** 7))
        spec = np.abs(np.fft.rfft(x)) ** 2
        f = np.fft.rfftfreq(len(x), 1 / synth.SR)
        return spec[f < 100].sum() / spec.sum()

    assert low_share("sub_bass") > 0.95 > low_share("reese_bass")
    assert low_share("electric_bass") < low_share("sub_bass")


def test_a_tuned_drum_is_shorter_and_every_kit_drum_sounds():
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def stroke(inst, key, tune=0.0):
        ctx = synth.NoteCtx(inst, "d", key, 0.0, 0.1, 100, None, False, ("d", 0, key), tune)
        return synth.render_note(ctx, 10 ** 7)[0][0]

    assert len(stroke("kit", 38, 7.0)) < len(stroke("kit", 38)) * 0.7
    for inst in ("kit", "kit_808"):
        for key in set(KIT_DRUMS.values()):
            x = stroke(inst, key)
            assert np.isfinite(x).all() and np.abs(x).max() > 0.01, (inst, key)
    assert not np.array_equal(stroke("kit", 36), stroke("kit_808", 36))


def test_a_roll_can_climb_and_a_chopped_line_stays_one_note_at_a_time():
    p = _groove()
    p.add_op("drums", "chop", id="c", **{"from": "1", "until": "2"}, slices=4,
             order="1*4^0>12 . . .")
    roll = sorted((n for n in render(p).notes if n.start < 480 and n.pitch == 38),
                  key=lambda n: n.start)
    assert [n.tune for n in roll] == [0.0, 4.0, 8.0, 12.0]
    assert [n.start for n in roll] == [0, 120, 240, 360]
    # A monophonic line that is stuttered must not overlap itself.
    q = _line("0:1/2 2:1/2 | 4:1/1")
    q.add_op("v", "chop", id="c", **{"from": "1", "until": "2"}, slices=4,
             order="0*2 0*4 2 _")
    line = sorted(render(q).notes, key=lambda n: n.start)
    assert all(a.end <= b.start for a, b in zip(line, line[1:]))
    assert "polyphony_exceeded" not in {f.code for f in run_lint(q)}


def _line(steps: str) -> Piece:
    p = Piece("mono", "C major", tempo=100, style="electronic")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "synth_lead", "melody", octave=4))
    p.add_op("v", "phrase", id="f", steps=steps, at="1", octave=4)
    return p


def test_compression_makes_a_voice_denser_and_not_louder_and_gain_is_a_fader():
    np = pytest.importorskip("numpy")
    plain, _ = audio.synthesize(_groove(), reverb=False)
    p = _groove()
    p.add_op("drums", "compress", id="k", ratio=8, threshold=-24)
    squashed, _ = audio.synthesize(p, reverb=False)

    def power(x):
        return float(np.mean(np.asarray(x) ** 2))

    def crest(x):
        return float(np.abs(x).max() / np.sqrt(power(x)))

    assert power(squashed) == pytest.approx(power(plain), rel=0.02)
    assert crest(squashed) < crest(plain) * 0.75
    p.add_op("drums", "gain", id="g", db=-6)
    quieter, _ = audio.synthesize(p, reverb=False)
    assert power(quieter) == pytest.approx(power(squashed) / 10 ** 0.6, rel=0.02)
    assert render(p).notes == render(_groove()).notes        # sound, not notes


def test_a_voice_marked_for_the_soundfont_falls_back_when_there_is_none(monkeypatch):
    pytest.importorskip("numpy")
    p = _groove()
    modelled, _ = audio.synthesize(p, reverb=False)
    p.get_voice("drums").engine = "soundfont"
    assert Piece.from_json(p.to_json()).get_voice("drums").engine == "soundfont"
    monkeypatch.setattr(audio, "soundfont_available", lambda: False)
    with pytest.warns(UserWarning, match="instrument models"):
        fallback, _ = audio.synthesize(p, reverb=False)
    assert (fallback == modelled).all()
    with pytest.raises(ValueError, match="engine"):
        Voice("x", "kit", "percussion", engine="tape")


def test_time_scale_stretches_the_midi_file_without_touching_a_note():
    from musicstudio.midi import to_bytes
    p = _tiny()
    plain, slow = to_bytes(p), to_bytes(p, time_scale=1.5)
    assert struct_division(plain) == 480 and struct_division(slow) == 320
    assert plain[14:] == slow[14:]                          # every event identical


def struct_division(data: bytes) -> int:
    import struct
    return struct.unpack(">H", data[12:14])[0]


def test_a_chopped_pitch_moves_a_pitched_voice_too():
    np = pytest.importorskip("numpy")
    from musicstudio import synth
    base = synth.NoteCtx("supersaw", "v", 57, 0.0, 0.3, 90, None, False, ("v", 0, 57))
    up = synth.NoteCtx("supersaw", "v", 57, 0.0, 0.3, 90, None, False, ("v", 0, 57), 12.0)
    assert up.freq == pytest.approx(base.freq * 2)
    q = _line("0:1/1 | 0:1/1")
    q.add_op("v", "chop", id="c", **{"from": "1", "until": "2"}, slices=4, order="0*4^0>12 . . .")
    # On a pitched voice a whole-semitone shift is a different note, so it is
    # the *pitch* that moves: lint, the tension view and MIDI see what sounds.
    roll = sorted((n for n in render(q).notes if n.start < 480), key=lambda n: n.start)
    assert [n.pitch - roll[0].pitch for n in roll] == [0, 4, 8, 12]
    assert all(n.tune == 0.0 for n in roll)
    # Only the fraction of a shift is tuning.
    h = _line("0:1/1 | 0:1/1")
    h.add_op("v", "chop", id="c", **{"from": "1", "until": "2"}, slices=4, order="0^2.5 . . .")
    first = min(render(h).notes, key=lambda n: n.start)
    assert (first.pitch - roll[0].pitch, first.tune) in ((2, 0.5), (3, -0.5))


def test_a_chopped_theme_is_not_reported_as_written_and_chop_refuses_dust():
    p = Piece("c", "C major", tempo=100, style="electronic")
    p.sections.append(Section("A", 2))
    p.add_motif("hero", "0 2 4 2", unit="1/4")
    p.voices.append(Voice("v", "synth_lead", "melody", octave=4))
    p.add_op("v", "play", id="s", motif="hero", at="1")
    assert {n.form for n in render(p).notes} == {""}
    p.add_op("v", "chop", id="c", **{"from": "1", "until": "2"}, slices=4, order="3 2 1 0")
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert {n.form for n in notes} == {"chopped"} and {n.motif for n in notes} == {"hero"}
    from musicstudio.readback import motif_map
    assert "chopped" in motif_map(p, render(p))
    # A slot left where it was ('_') is still the theme as written.
    p.update_op("c", order="_ _ 3 2")
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert [n.form for n in notes[:2]] == ["", ""]
    p.update_op("c", slices=100000)
    with pytest.raises(ValueError, match="finer than"):
        render(p)


def test_a_retuned_note_sounds_the_same_whatever_was_rendered_before_it():
    """The table cache is keyed by the frequency a table is built from. Keyed
    by written pitch alone, a tuned note inherited the untuned note's table --
    or left its own behind -- and a render depended on its history."""
    np = pytest.importorskip("numpy")
    from musicstudio import synth
    for inst in ("clarinet", "piano"):
        plain = synth.NoteCtx(inst, "v", 60, 0.0, 0.4, 90, None, False, ("v", 0, 60))
        tuned = synth.NoteCtx(inst, "v", 60, 0.0, 0.4, 90, None, False, ("v", 0, 60), 7.0)
        synth._tables.clear()
        alone = [layer for layer, _ in synth.render_note(tuned, 44100)]
        synth._tables.clear()
        synth.render_note(plain, 44100)
        after = [layer for layer, _ in synth.render_note(tuned, 44100)]
        assert len(alone) == len(after) and all(
            np.array_equal(a, b) for a, b in zip(alone, after)), inst


def test_a_rhythm_pattern_says_the_shape_of_a_bar():
    from fractions import Fraction as F
    from musicstudio import pattern
    def at(text, cycle=0):
        return [(e.start, e.symbol) for e in pattern.events(pattern.parse(text), cycle)]
    assert at("x . x .") == [(F(0), "x"), (F(1, 2), "x")]
    assert at("x [o o] . X") == [(F(0), "x"), (F(1, 4), "o"), (F(3, 8), "o"), (F(3, 4), "X")]
    assert [s for s, _ in at("x*4 .")] == [F(0), F(1, 8), F(1, 4), F(3, 8)]
    assert [s for s, _ in at("x!3 o")] == [F(0), F(1, 4), F(1, 2), F(3, 4)]
    assert at("x@3 o") == [(F(0), "x"), (F(3, 4), "o")]
    # Three over eight is the tresillo; rotated, it starts somewhere else.
    assert pattern.describe("x(3,8)", steps=8) == "x..x..x."
    assert pattern.describe("x(3,8,2)", steps=8) == "x.x..x.."
    assert pattern.describe("x(5,8)", steps=8) == "x.xx.xx."
    # Alternation is by cycle, at any depth, and '|' is whole bars in turn.
    assert [at("<x o> .", c)[0][1] for c in range(4)] == ["x", "o", "x", "o"]
    assert pattern.describe("x . . . | . . x .", 3, 4) == "x...\n..x.\nx..."
    assert pattern.describe("x <o [o o]>", 2, 4) == "x.o.\nx.oo"
    assert pattern.describe("x o?", 1, 2) == "x?"
    for bad, why in (("x [o", "never closed"), ("x(9,8)", "do not fit"), ("", "empty"),
                     ("x*0", "at least 1"), ("x(3 8)", "hits,steps"), ("<>", "choose from")):
        with pytest.raises(pattern.PatternError, match=why):
            pattern.parse(bad)


def test_beat_takes_patterns_and_chance_is_the_same_every_render():
    def kit(lanes, bars=4, **kw):
        p = Piece("k", "C major", tempo=120, style="electronic")
        p.sections.append(Section("A", bars))
        p.voices.append(Voice("d", "kit", "percussion"))
        p.add_op("d", "beat", id="b", at="1", bars=bars, lanes=lanes, **kw)
        return p
    # The same bar written both ways is the same notes.
    grid = render(kit({"kick": "x.....x...x.....", "snare": "....x.......x...",
                       "hat": "x.x.x.x.x.x.x.x."})).notes
    said = render(kit({"kick": "x . . x . x . .", "snare": ". x . x", "hat": "x*8"},
                      cycle=1)).notes
    key = lambda n: (n.start, n.pitch, n.velocity, n.dur)
    assert sorted(map(key, grid)) == sorted(map(key, said))
    # Accents and ghosts mean what they mean on the grid.
    vel = {n.start: n.velocity for n in render(kit({"snare": "x X o ."}, 1, cycle=1)).notes}
    assert vel[480] > vel[0] > vel[960]
    # A two-bar cycle, and a fill that only happens every fourth bar.
    two = render(kit({"kick": "x . . . . . . x"}, cycle=2)).notes
    assert sorted(n.start for n in two) == [0, 3360, 3840, 7200]
    fill = render(kit({"tom_hi": "<. . . [. . . x*4]>"}, cycle=1)).notes
    assert len(fill) == 4 and min(n.start for n in fill) == 3 * 1920 + 1440
    # "Sometimes" is seeded: some but not all, and identical on a second render.
    p = kit({"hat": "o?*16"}, 8, cycle=1)
    first, again = render(p).notes, render(p).notes
    assert 30 < len(first) < 100 and [key(n) for n in first] == [key(n) for n in again]
    bad = kit({"kick": "x q"}, cycle=1)
    with pytest.raises(ValueError, match="made of 'x' hit"):
        render(bad)
    with pytest.raises(ValueError, match="lane 'kick'.*never closed"):
        render(kit({"kick": "x [x"}, cycle=1))


def test_eq_cuts_its_band_and_leaves_the_rest_alone():
    np = pytest.importorskip("numpy")
    def bands(piece):
        x, _ = audio.synthesize(piece, reverb=False)
        spec = np.abs(np.fft.rfft(x)) ** 2
        f = np.fft.rfftfreq(len(x), 1 / audio.SR)
        return [float(spec[(f >= a) & (f < b)].sum()) for a, b in ((100, 600), (2400, 4200))]
    plain = _line("0:1/1 | 0:1/1")
    cut = _line("0:1/1 | 0:1/1")
    cut.add_op("v", "eq", id="e", freq=3200, gain=-12, width=1.0)
    low0, mid0 = bands(plain)
    low1, mid1 = bands(cut)
    assert 10 * math.log10(mid1 / mid0) < -6           # the band is down
    assert abs(10 * math.log10(low1 / low0)) < 0.2     # two octaves away, untouched
    # It is audio only: the notes and the MIDI file are the same.
    from musicstudio.midi import to_bytes
    assert to_bytes(plain) == to_bytes(cut)
    cut.update_op("e", freq=5)
    with pytest.raises(ValueError, match="eq freq"):
        audio.synthesize(cut, reverb=False)


def test_a_duck_pumps_against_its_source_and_a_stop_silences_band_and_room(tmp_path):
    np = pytest.importorskip("numpy")
    p = Piece("d", "C major", tempo=120, style="electronic")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("pad", "synth_pad", "pad", octave=4))
    p.voices.append(Voice("drums", "kit", "percussion"))
    p.voices.append(Voice("solo", "synth_lead", "melody", octave=5))
    p.add_op("pad", "phrase", id="hold", steps="0:1/1 | 0:1/1", at="1")
    p.add_op("solo", "phrase", id="tune", steps="4:1/1 | 4:1/1", at="1")
    p.add_op("drums", "beat", id="b", at="1", bars=2, lanes={"kick": "x...x...x...x...",
                                                            "hat": "..x...x...x...x."})
    only = lambda q, name: [setattr(v, "muted", v.name != name) for v in q.voices]

    import copy
    flat = copy.deepcopy(p); only(flat, "pad")
    plain, _ = audio.synthesize(flat, reverb=False)
    p.add_op("pad", "duck", id="pump", source="drums", drum="kick", depth=12, release=0.1)
    ducked = copy.deepcopy(p); only(ducked, "pad")
    pumped, _ = audio.synthesize(ducked, reverb=False)
    beat = int(0.5 * audio.SR)
    def level(x, at, span=0.02):
        a = int(at * audio.SR)
        return float(np.sqrt(np.mean(x[a:a + int(span * audio.SR)] ** 2)))
    # Down by about the depth just after a kick, back up before the next one,
    # and the hats (not the drum asked for) do not move it.
    assert level(pumped, 0.505) < 0.4 * level(plain, 0.505)
    assert level(pumped, 0.45) > 0.9 * level(plain, 0.45)
    assert level(pumped, 0.25 + 0.2) > 0.9 * level(plain, 0.25 + 0.2)
    with pytest.raises(ValueError, match="not a drum"):
        p.update_op("pump", drum="cowbell-ish"); audio.synthesize(p, reverb=False)
    p.update_op("pump", drum="kick")

    # A stop: band and room go dead, the kept voice carries on.
    s = Studio(tmp_path)
    p.name = "d"; s.save(p)
    wet_before, _ = audio.synthesize(s.get("d"), reverb=True)
    s.set_master("d", stops=[{"from": "2", "until": "2:3", "keep": ["solo"]}])
    alone = copy.deepcopy(s.get("d")); only(alone, "solo")
    alone.meta = {}
    dry_solo, _ = audio.synthesize(alone, reverb=False)
    stopped, _ = audio.synthesize(s.get("d"), reverb=True)
    a, b = int(2.02 * audio.SR), int(2.9 * audio.SR)
    assert np.allclose(stopped[a:b], dry_solo[a:b], atol=1e-9)      # only the solo, dry
    assert not np.allclose(wet_before[a:b], dry_solo[a:b], atol=1e-3)
    assert float(np.abs(stopped[int(3.2 * audio.SR):int(3.4 * audio.SR)]).max()) > 0.01
    with pytest.raises(ValueError, match="end after"):
        s.set_master("d", stops=[{"from": "2", "until": "2"}])
    assert s.set_master("d", stops=[])["master"].get("stops") is None


def test_drive_modes_get_harsher_and_a_noise_wall_is_noise():
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def flatness(x):
        spec = np.abs(np.fft.rfft(np.asarray(x) * np.hanning(len(x)))) ** 2
        f = np.fft.rfftfreq(len(x), 1 / audio.SR)
        band = spec[(f > 200) & (f < 8000)] + 1e-18
        return float(np.exp(np.log(band).mean()) / band.mean())

    def driven(mode, amount):
        p = _line("0:1/1 | 0:1/1")
        p.voices[0].instrument = "sub_bass"
        p.update_op("f", octave=2)
        if mode:
            p.add_op("v", "drive", id="d", amount=amount, mode=mode)
        return audio.synthesize(p, reverb=False)[0]

    def highs(x):
        spec = np.abs(np.fft.rfft(x)) ** 2
        f = np.fft.rfftfreq(len(x), 1 / audio.SR)
        return spec[f > 1000].sum() / spec.sum()

    clean, soft, clip, fold = (driven(None, 0), driven("soft", 1.0), driven("clip", 2.0),
                               driven("fold", 2.0))
    assert highs(clean) < highs(soft) < highs(clip) < highs(fold)
    with pytest.raises(ValueError, match="drive mode"):
        driven("fuzz", 1.0)
    wall = synth.NoteCtx("noise_wall", "v", 60, 0.0, 1.0, 90, None, False, ("v", 0, 60))
    tone = synth.NoteCtx("supersaw", "v", 60, 0.0, 1.0, 90, None, False, ("v", 0, 60))
    render1 = lambda c: sum(sig for sig, _ in synth.render_note(c, 10 ** 7))
    assert flatness(render1(wall)) > 10 * flatness(render1(tone))


def test_the_master_can_be_told_to_clip(tmp_path):
    np = pytest.importorskip("numpy")
    s = Studio(tmp_path)
    s.create("m", key="A minor", tempo=160, style="electronic", form="binary")
    s.add_voice("m", "drums", "kit", role="percussion")
    s.add_op("m", "drums", "beat", id="b", at="1", bars=4, lanes=AMEN, dynamic="ff")

    def crest(path):
        with wave.open(str(path)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768.0
        return float(np.abs(x).max() / np.sqrt((x ** 2).mean()))

    polite = crest(s.export_wav("m", str(tmp_path / "a.wav")))
    assert s.set_master("m", clip=12)["master"] == {"clip": 12.0}
    assert s.get("m").meta["master"] == {"clip": 12.0}           # saved with the piece
    assert crest(s.export_wav("m", str(tmp_path / "b.wav"))) < polite * 0.6
    assert s.set_master("m", clip=0)["master"] == {}


# --------------------------------------------------------------------------
# lyrics and the singing voice
# --------------------------------------------------------------------------

from musicstudio import lyrics as lyr  # noqa: E402


def test_romaji_is_read_syllable_by_syllable():
    syl, warn = lyr.parse("ka ze ga fu i te ru")
    assert [s.to_json() for s in syl] == ["k a", "z e", "g a", "f u", "i", "t e", "rr u"]
    assert warn == []
    assert [s.to_json() for s in lyr.parse("kyo u wa ki tte n shi")[0]] == \
        ["k y o", "u", "w a", "k i", "q t e", "N", "sh i"]
    assert lyr.romaji("the") is None and lyr.romaji("la") is None
    with pytest.raises(ValueError, match="romaji"):
        lyr.parse("ka the", lang="ja")


def test_brackets_holds_and_plain_ah():
    syl, _ = lyr.parse("[s t r ey n jh] - _ la", lang="en")
    assert syl[0].onset == ("s", "t", "r") and syl[0].nucleus == "ey" and syl[0].coda == ("n", "jh")
    assert syl[1].hold and syl[2].nucleus == "aa" and not syl[2].onset
    assert lyr.Syllable.from_json(syl[0].to_json()) == lyr.Syllable(
        ("s", "t", "r"), "ey", ("n", "jh"), syl[0].to_json())
    with pytest.raises(ValueError, match="unknown phoneme"):
        lyr.parse("[x y z]")
    with pytest.raises(ValueError, match="nothing to hold"):
        lyr.parse("[s t]")


def test_english_without_a_dictionary_guesses_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)
    syl, warn = lyr.parse("fire and stone")
    assert [s.to_json() for s in syl] == ["f ay r", "ae n d", "s t ow n"]
    assert len(warn) == 1 and "ms lyrics install" in warn[0]


def test_english_with_a_dictionary_splits_words_at_syllables(tmp_path, monkeypatch):
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)
    (tmp_path / lyr.DICT_NAME).write_text(
        "lanterns L AE1 N T ER0 N Z\nstrange S T R EY1 N JH\nwater W AO1 T ER0\n"
        "water(2) W AA1 T ER0\nthe DH AH0\n")
    syl, warn = lyr.parse("lan-terns strange wa-ter the")
    assert [s.to_json() for s in syl] == ["l ae n", "t er n z", "s t r ey n jh",
                                          "w ao", "t er", "dh ah"]
    assert warn == []
    # nt cannot start a syllable, so it is split; str can, so it is not.
    assert lyr.split_syllables("ih n s t r ah k t".split()) == [["ih", "n"], ["s", "t", "r", "ah", "k", "t"]]
    with pytest.raises(ValueError, match="hyphenate"):
        lyr.parse("lanterns")
    with pytest.raises(ValueError, match="pronounced as 2"):
        lyr.parse("lan-ter-ns")
    assert "guessed" in lyr.parse("zzyzx")[1][0]


def _sung(text: str, steps: str = "0 2 4 2", inst: str = "singer", **op) -> Piece:
    p = Piece("vox", "C major", tempo=96, style="chamber")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("vox", inst, "melody", octave=4, pan=0.0))
    p.add_op("vox", "phrase", id="m", steps=steps, at="1", unit="1/4", octave=4)
    p.add_op("vox", "lyrics", id="l", text=text, **op)
    return p


def test_lyrics_ride_on_the_notes_and_reach_the_midi_file():
    p = _sung("sa ku ra -")
    r = render(p)
    assert [(n.lyric, n.sung) for n in sorted(r.notes, key=lambda n: n.start)] == \
        [("sa", "s a"), ("ku", "k u"), ("ra", "rr a"), ("-", "-")]
    assert r.warnings == []
    from musicstudio.midi import to_bytes
    data = to_bytes(p)
    assert b"\xff\x05\x02sa" in data and b"\xff\x05\x02ku" in data
    assert b"\xff\x05\x01-" not in data                    # a hold is not a word
    # Too many or too few syllables is said, not hidden.
    assert "not sung" in render(_sung("a i u e o ka")).warnings[0]
    assert "'ah'" in render(_sung("a i")).warnings[0]
    with pytest.raises(ValueError, match="romaji"):
        _sung("ka the", lang="ja")


def _spectrum(x, np, lo, hi, a, b):
    seg = np.asarray(x)[int(a * audio.SR):int(b * audio.SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / audio.SR)
    return float(spec[(f >= lo) & (f < hi)].sum())


def test_the_voice_makes_different_vowels_and_they_are_the_right_ones():
    np = pytest.importorskip("numpy")
    beat = 60 / 96
    x, _ = audio.synthesize(_sung("a i u -", "0:1/2 0:1/2 | 0:1/2 0:1/2"), reverb=False)

    def share(a, lo, hi):
        t0 = a * 2 * beat + 0.25
        return _spectrum(x, np, lo, hi, t0, t0 + 0.6) / _spectrum(x, np, 150, 8000, t0, t0 + 0.6)

    # "ah": energy around 800-1500 Hz. "ee": a high second formant near 3 kHz
    # and nothing in between. "oo": neither.
    assert share(0, 700, 1700) > 3 * share(1, 700, 1700)
    assert share(1, 2500, 4200) > 5 * share(0, 2500, 4200)
    assert share(1, 2500, 4200) > 5 * share(2, 2500, 4200)
    assert np.abs(x).max() > 0.05


def test_consonants_come_before_the_beat_and_the_vowel_lands_on_it():
    np = pytest.importorskip("numpy")
    beat = 60 / 96
    plain, _ = audio.synthesize(_sung("a a a a"), reverb=False)
    hissed, _ = audio.synthesize(_sung("a sa a a"), reverb=False)
    # The "s" is noise above 5 kHz in the 100 ms *before* the second note...
    before = (beat - 0.11, beat - 0.005)
    assert _spectrum(hissed, np, 5000, 12000, *before) > 50 * _spectrum(plain, np, 5000, 12000, *before)
    # ...and by the time the note is under way it is a vowel again.
    during = (beat + 0.15, beat + 0.45)
    assert _spectrum(hissed, np, 5000, 12000, *during) < \
        0.05 * _spectrum(hissed, np, 5000, 12000, *before)
    assert _spectrum(hissed, np, 200, 3000, *during) == pytest.approx(
        _spectrum(plain, np, 200, 3000, *during), rel=0.3)


def test_the_voice_is_the_same_every_time_and_other_instruments_still_sing_ah(
        tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)        # spelling rules, on any machine
    p = _sung("[l ae n] [t er n z] on stone - -", "0 2 4 5 | 4 2", lang="en")
    once, _ = audio.synthesize(p, reverb=False)
    again, _ = audio.synthesize(p, reverb=False)
    assert np.array_equal(once, again) and np.isfinite(once).all()
    for inst in ("singer_warm", "singer_low", "singer_breathy"):
        q = _sung("a i u e", inst=inst, steps="0 2 4 2")
        if inst == "singer_low":
            q.voices[0].octave = 3
            q.update_op("m", octave=3)
        x, _ = audio.synthesize(q, reverb=False)
        assert np.abs(x).max() > 0.03, inst
    # A violin given lyrics carries them (for MIDI) and is still a violin.
    v = _sung("a i u e", inst="violin")
    assert render(v).notes[0].lyric == "a"
    assert np.abs(audio.synthesize(v, reverb=False)[0]).max() > 0.03


# --------------------------------------------------------------------------
# voice banks: a recorded voice that sings any lyric
# --------------------------------------------------------------------------

FAKE_CORPUS = """# a tiny recording list for tests
ra r aa -
mi m iy -
so s ow -
sun s ah n
moon m uw n
"""


def _fake_bank(tmp_path, monkeypatch, whole=()):
    """A 'recorded' voice made with the synthesized one, so no network and no
    paid service is involved: each word is spoken on a flat pitch and saved
    where a real recording would be."""
    np = pytest.importorskip("numpy")
    from musicstudio import vocal, voicebank as vb
    corpus = tmp_path / "corpus.txt"
    corpus.write_text(FAKE_CORPUS)
    monkeypatch.setattr(vb, "CORPUS", corpus)
    monkeypatch.setattr(vb, "CACHE_DIR", tmp_path / "bank")
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path / "nodict")
    vb._banks.clear()
    vb._words.clear()

    def record(word, syllables):
        at, sung = 0.2, []
        for onset, nucleus, coda in syllables:
            sung.append(vocal.Sung(at, at + 0.26, 55.0, 90, onset, nucleus, coda))
            at += 0.28
        sig, _ = vocal.render_phrase(sung, vocal.SINGERS["singer_warm"], 7)
        path = vb.sample_path(word, "test")
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(vb.SR)
            w.writeframes((np.clip(sig * 3, -1, 1) * 32000).astype("<i2").tobytes())

    for word, (onset, vowel, coda) in vb.corpus().items():
        record(word, [((onset,) if onset else (), vowel, (coda,) if coda else ())])
    for word, syllables in whole:
        record(word, syllables)
    return vb


def test_lyrics_tag_each_note_with_its_word_and_syllable(tmp_path, monkeypatch):
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)
    (tmp_path / lyr.DICT_NAME).write_text("lanterns L AE1 N T ER0 N Z\nshine SH AY1 N\n")
    p = _sung("lan-terns shine -", lang="en")
    assert [n.word for n in sorted(render(p).notes, key=lambda n: n.start)] == \
        ["lanterns#0/2", "lanterns#1/2", "shine#0/1", ""]


def test_the_recording_list_covers_what_it_says_and_a_bank_reports_itself(tmp_path, monkeypatch):
    pytest.importorskip("numpy")
    from musicstudio import voicebank as vb
    real = vb.corpus()
    assert len(real) > 250
    assert all(v in lyr.VOWELS and len(v) == 2 for _, v, _ in real.values())
    onsets = {o for o, _, _ in real.values()}
    assert {"", "b", "ch", "dh", "hh", "jh", "sh", "th", "y", "z"} <= onsets
    vb = _fake_bank(tmp_path, monkeypatch)
    st = vb.status("test")
    assert st["complete"] and st["recorded"] == st["words"] == 5 and st["vocabulary"] == 5
    assert vb.status("nobody")["recorded"] == 0 and vb.load("nobody") is None
    bank = vb.load("test")
    assert ("r", "aa") in bank.cv and ("ah", "n") in bank.vc
    # A join that was never recorded falls back to the nearest vowel.
    unit, exact = bank.opening("r", "ah")
    assert unit is not None and not exact
    assert bank.opening("s", "ah")[1] and bank.closing("uw", "n")[1]


def test_a_word_is_cut_into_its_syllables_inside_the_part_that_sounds():
    np = pytest.importorskip("numpy")
    from musicstudio import voicebank as vb
    hill, silence = np.hanning(30), np.zeros(40)

    def word(rms):
        rms = rms + 0.001
        return {"rms": rms, "energy": np.where(rms > 0.05, rms, 0.0)}

    # Two clear hills, then a long breath: the cut goes between the hills.
    d = word(np.concatenate([np.zeros(5), hill, hill * 0.6, silence]))
    (a0, a1), (b0, b1) = vb.split_word(d, 2)
    assert a0 == 0 and b1 == len(d["rms"]) and 30 <= a1 == b0 <= 40
    # One hill for two syllables (speech ran them together): split the hill,
    # not the silence after it.
    d = word(np.concatenate([np.zeros(5), np.hanning(60), silence]))
    assert 25 <= vb.split_word(d, 2)[0][1] <= 45
    assert vb.split_word(d, 1) == [(0, len(d["rms"]))]


def _peak_multiple(x, np, t0, t1, hz):
    seg = np.asarray(x)[int(t0 * audio.SR):int(t1 * audio.SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    f = np.fft.rfftfreq(len(seg), 1 / audio.SR)
    peak = f[np.argmax(spec)]
    return abs(peak / hz - round(peak / hz))


def test_a_voice_bank_sings_the_written_pitch_from_the_recording(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    vb = _fake_bank(tmp_path, monkeypatch)
    p = _sung("ra mi so ra", "0:1/2 4:1/2 | 7:1/2 4:1/2")
    plain, _ = audio.synthesize(p, reverb=False)
    p.get_voice("vox").bank = "test"
    assert Piece.from_json(p.to_json()).get_voice("vox").bank == "test"
    banked, _ = audio.synthesize(p, reverb=False)
    again, _ = audio.synthesize(p, reverb=False)
    assert np.array_equal(banked, again) and np.isfinite(banked).all()
    assert len(banked) == len(plain) and not np.allclose(banked, plain)
    assert np.abs(banked).max() > 0.03
    # The pitch is the score's, not the recording's (which was spoken at G3):
    # the third note is C5, and its strongest partial is a multiple of 523 Hz.
    beat = 60 / 96
    assert _peak_multiple(banked, np, 4 * beat + 0.3, 4 * beat + 1.0, 523.25) < 0.04

    # No bank recorded: the voice falls back to the synthesized one, and says so.
    p.get_voice("vox").bank = "nobody"
    with pytest.warns(UserWarning, match="ms voicebank build nobody"):
        fallback, _ = audio.synthesize(p, reverb=False)
    assert np.array_equal(fallback, plain)


def test_a_word_recorded_whole_is_sung_from_its_own_recording(tmp_path, monkeypatch):
    """`sunmoon` is in the bank as one two-syllable recording. Sung with that
    word tag, it comes from that recording; the same sounds given in brackets
    (no word) are assembled from the unit corpus instead."""
    np = pytest.importorskip("numpy")
    vb = _fake_bank(tmp_path, monkeypatch,
                    whole=[("sunmoon", [(("s",), "ah", ("n",)), (("m",), "uw", ("n",))])])
    (tmp_path / "nodict").mkdir()
    (tmp_path / "nodict" / lyr.DICT_NAME).write_text("sunmoon S AH1 N M UW1 N\n")
    lyr._dictionary = None
    units = vb.word_units("sunmoon", [("s", "n"), ("m", "n")], "test")
    assert units is not None and len(units) == 2
    first, second = units
    assert first.start < first.vowel < first.v_end <= first.end <= second.start + 2048
    assert second.vowel < second.v_end <= second.end
    assert vb.word_units("nothere", [("s", "n")], "test") is None

    whole = _sung("sun-moon", "0:1/2 4:1/2", lang="en")
    whole.get_voice("vox").bank = "test"
    parts = _sung("[s ah n] [m uw n]", "0:1/2 4:1/2", lang="en")
    parts.get_voice("vox").bank = "test"
    a, _ = audio.synthesize(whole, reverb=False)
    b, _ = audio.synthesize(parts, reverb=False)
    assert np.abs(a).max() > 0.03 and np.abs(b).max() > 0.03 and not np.allclose(a, b)
    beat = 60 / 96
    for x in (a, b):                         # either way, the second note is G4
        assert _peak_multiple(x, np, 2 * beat + 0.3, 2 * beat + 0.9, 392.0) < 0.05
    lyr._dictionary = None


def test_a_consonant_played_faster_keeps_its_tone():
    """Unvoiced sound is laid down in fixed grains, never resampled: an "s"
    sped up three times lasts a third as long and hisses at the same pitch."""
    np = pytest.importorskip("numpy")
    from musicstudio import voicebank as vb
    rng = np.random.default_rng(3)
    n = vb.SR
    t = np.arange(n) / vb.SR
    hiss = rng.standard_normal(n)
    spec = np.fft.rfft(hiss)
    f = np.fft.rfftfreq(n, 1 / vb.SR)
    hiss = np.fft.irfft(spec * np.exp(-0.5 * ((f - 6000) / 600) ** 2), n)
    u = vb.Unit(x=hiss / np.abs(hiss).max(), marks=np.zeros(0, dtype=np.int64),
                voiced=np.zeros(n), period=np.full(n, 200.0), start=0, end=n)
    def centroid(x):
        s_ = np.abs(np.fft.rfft(x)) ** 2
        return float((s_ * np.fft.rfftfreq(len(x), 1 / vb.SR)).sum() / s_.sum())
    slow = vb.psola(u, np.linspace(2000, n - 2000, n - 4000), np.full(n, 220.0))
    fast = vb.psola(u, np.linspace(2000, n - 2000, (n - 4000) // 3), np.full(n, 220.0))
    assert len(fast) * 3 == pytest.approx(len(slow), rel=0.01)
    assert centroid(fast) == pytest.approx(centroid(slow), rel=0.05)
    assert centroid(fast) == pytest.approx(6000, rel=0.1)
    del t


def test_how_much_of_a_lyric_was_understood():
    pytest.importorskip("numpy")
    from musicstudio import voicebank as vb
    # Recall alone is satisfied by every word sung among a lot of noise.
    assert vb.words_heard(["hold", "on"], "nonsense hold nonsense on nonsense")[0] == 1.0
    assert vb.words_added(["hold", "on"], "nonsense hold nonsense on nonsense") == \
        ["nonsense"] * 3
    assert vb.words_added(["hold", "on"], "Hold on.") == []
    for name in ("../../up", "/abs/olute", ".."):
        with pytest.raises(ValueError) if name == ".." else _no_raise():
            inside = vb.bank_dir(name).resolve()
            assert vb.CACHE_DIR.expanduser().resolve() in inside.parents
    share, missed = vb.words_heard(["neon", "in", "the", "puddles", "last", "train's"],
                                   "Neon in the hurdles... last rain's.")
    assert share == pytest.approx(4 / 6) and missed == ["puddles", "train's"]
    assert vb.words_heard(["hold", "on"], "") == (0.0, ["hold", "on"])
    # Recording and transcribing need a key and are never attempted without one.
    import os
    if not os.environ.get(vb.KEY_ENV):
        with pytest.raises(RuntimeError, match=vb.KEY_ENV):
            vb.fetch("hello", "nobody")


# --------------------------------------------------------------------------
# neural singers: a trained voicebank, never part of the studio
# --------------------------------------------------------------------------

def test_every_listed_voicebank_is_pinned_and_says_what_its_terms_ask():
    from musicstudio import neural
    assert "qixuan" in neural.CATALOGUE
    for name, e in neural.CATALOGUE.items():
        assert e.name == name and e.terms.startswith("https://") and e.homepage
        assert e.asks and all(len(a) > 20 for a in e.asks)
        if e.url:                                    # a download is pinned or absent
            assert e.url.startswith("https://") and len(e.sha256) == 64
            int(e.sha256, 16)
        assert not e.vocoder or e.vocoder in neural.VOCODERS
    for v in neural.VOCODERS.values():
        assert len(v.sha256) == 64 and v.licence and v.url.startswith("https://")


import contextlib  # noqa: E402


@contextlib.contextmanager
def _no_raise():
    yield


def test_a_lyric_carries_its_pronunciation_and_is_sung_the_same_without_a_dictionary(
        tmp_path, monkeypatch):
    """How a word is said is decided when the line is written and stored in
    the op. Looked up again at every render, the same saved piece failed on a
    machine with no dictionary ('sat-el-lites' guessed as four syllables)."""
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)
    (tmp_path / lyr.DICT_NAME).write_text(
        "satellites S AE1 T AH0 L AY2 T S\nshine SH AY1 N\n")
    p = _sung("sat-el-lites shine", lang="en")
    op = p.find_op("l")[1]
    assert op.params["said"] == {"satellites": "s ae t ah l ay t s", "shine": "sh ay n"}
    here = [(n.sung, n.word) for n in sorted(render(p).notes, key=lambda n: n.start)]
    saved = p.dumps()

    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path / "nowhere")
    with pytest.raises(ValueError, match="pronounced as 4"):     # what a bare lyric does
        lyr.parse("sat-el-lites shine", "en")
    (tmp_path / "saved.ms.json").write_text(saved)
    q = Piece.load(tmp_path / "saved.ms.json")
    r = render(q)
    assert [(n.sung, n.word) for n in sorted(r.notes, key=lambda n: n.start)] == here
    assert r.warnings == []
    # Moving the line does not re-pronounce it; changing the words does, and
    # keeps what it was told about a word this machine cannot look up.
    q.update_op("l", **{"from": "1"})
    assert q.find_op("l")[1].params["said"] == op.params["said"]
    q.update_op("l", text="shine shine sat-el-lites -")
    assert q.find_op("l")[1].params["said"] == op.params["said"]
    # A word with two pronunciations is flagged when the line is checked, the
    # choice is one entry of `said`, and it survives a change of the words.
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path)
    (tmp_path / lyr.DICT_NAME).write_text(
        "lives L IH1 V Z\nlives(2) L AY1 V Z\nnine N AY1 N\nthe DH AH0\nthe(2) DH IY0\n")
    _, notes = lyr.parse("nine lives the", "en")
    assert len(notes) == 1 and "'lives' can be said 2 ways" in notes[0] and "l ay v z" in notes[0]
    cat = _sung("nine lives", "0 2", lang="en", said={"lives": "l ay v z"})
    assert cat.find_op("l")[1].params["said"] == {"nine": "n ay n", "lives": "l ay v z"}
    assert render(cat).warnings == []
    cat.update_op("l", text="lives nine")
    assert cat.find_op("l")[1].params["said"]["lives"] == "l ay v z"
    cat.update_op("l", said=None)
    assert cat.find_op("l")[1].params["said"]["lives"] == "l ih v z"
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path / "nowhere")
    # One word said differently is an edit of the op, like any other.
    q.update_op("l", said={"shine": "sh iy n", "satellites": "s ae t ah l ay t s"})
    assert render(q).notes and "sh iy n" in {n.sung for n in render(q).notes}


def test_what_the_render_could_not_sing_comes_back_with_the_edit(tmp_path):
    s = _studio(tmp_path)
    s.add_voice("p", "vox", "singer")
    s.add_op("p", "vox", "phrase", id="m", steps="0 2", at="1", unit="1/4")
    res = s.add_op("p", "vox", "lyrics", id="l", text="sa ku ra")
    assert len(res.warnings) == 1 and "not sung" in res.warnings[0]
    assert "not sung" in str(res) and res.to_json()["warnings"] == res.warnings
    assert s.update_op("p", "l", text="sa ku").warnings == []


def test_rendering_without_numpy_says_what_it_left_out(monkeypatch):
    p = _line("0:1/1 | 0:1/1")
    monkeypatch.setattr(audio, "_np", None)
    import warnings as w
    with w.catch_warnings():
        w.simplefilter("error")
        audio.synthesize(p, reverb=False, models=False)      # nothing lost: silent
    p.add_op("v", "gain", id="g", db=-40)
    with pytest.warns(UserWarning, match="gain ops are ignored"):
        audio.synthesize(p, reverb=False, models=False)
    with pytest.raises(RuntimeError, match="needs numpy"):
        audio.synthesize(p, reverb=False, models=False, strict=True)


def test_a_custom_soundfont_must_be_a_soundfont(tmp_path, monkeypatch):
    from musicstudio import soundfonts
    monkeypatch.setattr(soundfonts, "_fetch", lambda url, sha, progress=None: b"<html>no</html>")
    with pytest.raises(ValueError, match="not a SoundFont"):
        soundfonts.install(url="https://example.invalid/a.sf2", sha256="0" * 64,
                           dest=tmp_path, quiet=True)
    assert not list(tmp_path.iterdir())


def _bank_zip(members: dict[str, bytes]) -> bytes:
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_a_voicebank_is_only_fetched_once_its_terms_are_accepted(tmp_path, monkeypatch):
    from musicstudio import neural, soundfonts
    monkeypatch.setattr(neural, "SINGER_DIR", tmp_path)
    fetched = []

    def fake(url, sha256, folder, progress=None):
        fetched.append(url)
        if "vocoders" in url:
            data = _bank_zip({"vocoder.yaml": b"model: v.onnx\n", "v.onnx": b"x"})
        else:
            data = _bank_zip(
                {"Qixuan_v2.7.0_DiffSinger_OpenUtau/dsconfig.yaml": b"acoustic: a.onnx\n",
                 "Qixuan_v2.7.0_DiffSinger_OpenUtau/a.onnx": b"x"})
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"dl{len(fetched)}.part"
        path.write_bytes(data)
        return path

    def never(*a, **k):                                 # a test must not download
        raise AssertionError("tried to fetch into memory")
    monkeypatch.setattr(soundfonts, "_fetch_file", fake)
    monkeypatch.setattr(soundfonts, "_fetch", never)

    with pytest.raises(PermissionError, match="terms of use") as refusal:
        neural.install("qixuan")
    # The vocoder arrives with the bank under its own licence; say so up front.
    assert "vocoder" in str(refusal.value) and "CC BY-NC-SA" in str(refusal.value)
    assert fetched == [] and not neural.is_installed("qixuan") and neural.installed() == []
    with pytest.raises(ValueError, match="ms singer add"):
        neural.install("somebody-else", accept=True)

    where = neural.install("qixuan", accept=True)
    assert len(fetched) == 2 and neural.is_installed("qixuan")
    assert neural.installed() == ["qixuan"]            # the vocoder folder is not a singer
    note = (where / "SOURCE.txt").read_text()
    assert "terms of use: https://" in note and "DiffSinger" in note
    assert (tmp_path / "vocoders" / neural.CATALOGUE["qixuan"].vocoder / "vocoder.yaml").is_file()
    neural.install("qixuan", accept=True)              # already there: nothing more fetched
    assert len(fetched) == 2
    assert not list(tmp_path.rglob("*.part"))          # the archives are not kept


def test_adding_your_own_voicebank_and_refusing_a_hostile_archive(tmp_path, monkeypatch):
    from musicstudio import neural
    monkeypatch.setattr(neural, "SINGER_DIR", tmp_path / "singers")
    good = tmp_path / "mine.zip"
    good.write_bytes(_bank_zip({"Mine v1/dsconfig.yaml": b"acoustic: a.onnx\n"}))
    assert neural.add("Mine", good) == tmp_path / "singers" / "mine"
    assert neural.is_installed("mine") and neural.knows("mine:soft") and not neural.knows("sarah")
    with pytest.raises(FileExistsError):
        neural.add("mine", good)
    bad = tmp_path / "bad.zip"
    bad.write_bytes(_bank_zip({"../../escaped.txt": b"x", "dsconfig.yaml": b""}))
    with pytest.raises(ValueError, match="escapes"):
        neural.add("bad", bad)
    assert not (tmp_path / "escaped.txt").exists() and not neural.is_installed("bad")
    notabank = tmp_path / "n.zip"
    notabank.write_bytes(_bank_zip({"readme.txt": b"x"}))
    with pytest.raises(ValueError, match="not a DiffSinger voicebank"):
        neural.add("n", notabank)
    # Replacing an install with something that is not a voicebank leaves the
    # install alone: the new folder is checked before the old one is removed.
    with pytest.raises(ValueError, match="not a DiffSinger voicebank"):
        neural.add("mine", notabank, force=True)
    assert neural.is_installed("mine")
    monkeypatch.setattr(neural, "UNPACK_LIMIT", 4)
    with pytest.raises(ValueError, match="unpacks to more than"):
        neural.add("big", good)
    with pytest.raises(ValueError):
        neural.singer_dir("../up")


def test_a_singer_without_its_voicebank_falls_back_and_says_so(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    from musicstudio import neural
    monkeypatch.setattr(neural, "SINGER_DIR", tmp_path)
    p = _sung("ra mi so ra")
    plain, _ = audio.synthesize(p, reverb=False)
    p.get_voice("vox").bank = "qixuan"
    used = {}
    with pytest.warns(UserWarning, match="neural singer 'qixuan' is not installed"):
        sung, _ = audio.synthesize(p, reverb=False, engines=used)
    assert np.array_equal(sung, plain)
    # The fallback is visible to a caller, and a caller can refuse it.
    assert used == {"vox": "formant"}
    with pytest.raises(RuntimeError, match="cannot be run here"):
        audio.synthesize(p, reverb=False, strict=True)


def test_a_syllable_s_consonants_come_before_its_note_and_its_vowel_on_it():
    """What the models are told: a group runs from one vowel to the next, so
    the consonants that open a syllable close the group before it."""
    pytest.importorskip("numpy")
    from types import SimpleNamespace
    from musicstudio import neural
    from musicstudio.vocal import Sung
    stub = SimpleNamespace(name="stub", dur=None,
                           symbols=lambda p, lang="en": [] if p == "q" else [f"en/{p}"])
    sung = [Sung(1.0, 1.5, 60, 100, ("s", "t"), "aa", ("r",)),
            Sung(1.5, 2.0, 62, 100, (), "aa", (), hold=True),       # a melisma
            Sung(2.0, 2.5, 64, 100, ("l",), "ay", ("t",)),
            Sung(2.7, 3.2, 65, 100, ("q",), "ow", ())]              # after a short rest
    sung[0].coda, sung[1].coda = (), ("r",)                         # as `vocal.plan` leaves them
    groups, end = neural.group_phrase(sung, stub)
    assert end == 3.2
    assert [[p.symbol.split("/")[-1] for p in g.phones] for g in groups] == \
        [["SP", "s", "t"], ["aa", "r", "l"], ["ay", "t"], ["SP"], ["ow"]]
    assert [g.start for g in groups] == [0.5, 1.0, 2.0, 2.5, 2.7]
    phones = neural.time_phones(groups, end, stub, 1)
    assert [p.symbol.split("/")[-1] for p in phones] == \
        ["s", "t", "aa", "r", "l", "ay", "t", "SP", "ow"]
    s_, t_, aa, r_, l_, ay, t2, rest, ow = phones
    assert aa.start == pytest.approx(1.0) and ay.start == pytest.approx(2.0)
    assert ow.start == pytest.approx(2.7) and ow.end == pytest.approx(3.2)
    assert s_.start < t_.start < t_.end == pytest.approx(1.0)
    assert l_.end == pytest.approx(2.0) and r_.end == pytest.approx(l_.start)
    assert t2.end == pytest.approx(2.5) == pytest.approx(rest.start)
    assert all(b.start == pytest.approx(a.end) for a, b in zip(phones, phones[1:]))
    # Frame counts follow the clock: rounding one boundary never moves the next.
    frames = neural._frames([10.0] * 100, 11.61)
    assert sum(frames) == round(1000 / 11.61 + 0.5) and set(frames) <= {0, 1}


def test_an_installed_neural_singer_sings_the_score_the_same_way_twice(tmp_path, monkeypatch):
    """Runs only where a voicebank is installed (never in CI): the pitch is the
    score's, and a fresh render -- no cache -- is sample-identical to the last."""
    np = pytest.importorskip("numpy")
    from musicstudio import neural
    if not (neural.available() and neural.is_installed("qixuan")):
        pytest.skip("no neural singer installed here")
    monkeypatch.setattr(lyr, "DICT_DIR", tmp_path / "nodict")
    p = _sung("[l aa] [l aa] [l aa] [l aa]", "0:1/2 4:1/2 | 7:1/2 4:1/2", lang="en")
    p.get_voice("vox").bank = "qixuan"
    takes = []
    for k in range(2):
        monkeypatch.setattr(neural, "CACHE_DIR", tmp_path / f"cache{k}")
        neural._trims.clear()
        used = {}
        # strict: a neural engine that fails must fail this test, not hand the
        # line to the formant singer, whose audio passes every check below.
        takes.append(audio.synthesize(p, reverb=False, strict=True, engines=used)[0])
        assert used == {"vox": "neural:qixuan"}
    assert np.array_equal(takes[0], takes[1]) and np.abs(takes[0]).max() > 0.03
    beat = 60 / 96
    assert _peak_multiple(takes[0], np, 4 * beat + 0.4, 4 * beat + 1.0, 523.25) < 0.04
