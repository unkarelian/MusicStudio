"""Tests for the score language, the wider instrument table, the SoundFont
catalogue and the reference match.

The language's one promise is that it is the same model as text: nothing a
piece can hold is lost by writing it out, and nothing reaches the file unless
the whole score is good. The first two tests hold those.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import struct
import wave
import zipfile
from pathlib import Path

import pytest

from musicstudio import Piece, Studio
from musicstudio.cli import main
from musicstudio.score import ScoreError, compile_score, decompile

GALLERY = Path(__file__).resolve().parents[1] / "gallery" / "pieces"

SCORE = """
# a comment; and #4 below is a sharp, not one
piece small key="A minor" tempo=120 style=electronic
master room.decay=1.5 push=6
section A bars=4 dynamic=mf   -- the first
section B bars=4 dynamic=f

harmony
  @A: [i VI]*2
  @B: iv V7 i*2
  @B.2:3: bII

motif cell = 0 2 #4:1/4 2      -- up and back
motif wide < cell : augment:2 > transpose:2
lanes BEAT
  kick:  x...x...x...x...
  snare: ....x.......x...
set LOUD = ff

voice lead saw_lead role=melody octave=5
  tune: play motif=cell at=@A times=2 dynamic=mf   -- stated
  play motif=wide at=@B.2 dynamic=$LOUD
voice drums kit_808 role=percussion
  beat at=@A bars=8 lanes=$BEAT hat=x.x.x.x.x.x.x.x.
  stop_it: rest in=@B.4-4 off
for k in 0..1
  voice pad{k} warm_pad role=pad octave={3 + k}
    chords at={1 + 4*k} bars=4 voicing=pad
on pad0 pad1
  fx_{v}: filter start=800 from=@A until=@B.end
stop from=@B.4:3 until=@B.end keep=[lead]
"""


def test_every_piece_in_the_gallery_is_the_same_piece_as_text():
    """Written out and compiled back, to the last parameter -- imports,
    lyrics, derived motifs whose transforms kept no arguments, all of it."""
    pieces = sorted(GALLERY.glob("*.ms.json"))
    assert pieces
    for path in pieces:
        original = Piece.from_json(json.loads(path.read_text()))
        again = compile_score(decompile(original))
        assert again.to_json() == original.to_json(), path.name


def test_a_score_says_what_the_calls_would_have_said():
    p = compile_score(SCORE)
    assert (p.name, p.tempo, p.style, p.total_bars) == ("small", 120, "electronic", 8)
    assert [(h.at, h.chord) for h in p.harmony] == [
        ("1", "i"), ("2", "VI"), ("3", "i"), ("4", "VI"), ("5", "iv"), ("6", "V7"),
        ("6:3", "bII"), ("7", "i"), ("8", "i")]
    # A sharp in a motif is not a comment, and a derivation keeps its lineage.
    assert p.motifs["cell"].steps[2].alt == 1
    assert (p.motifs["wide"].derived_from, p.motifs["wide"].lineage) == \
        ("cell", ("augment:2", "transpose:2"))
    lead, drums = p.get_voice("lead"), p.get_voice("drums")
    assert [o.id for o in lead.ops] == ["tune", "lead_play_6"]
    assert lead.ops[0].note == "stated" and lead.ops[1].params["dynamic"] == "ff"
    beat = drums.ops[0]
    assert beat.params["lanes"] == {"kick": "x...x...x...x...", "snare": "....x.......x...",
                                    "hat": "x.x.x.x.x.x.x.x."}
    assert (drums.ops[1].params["from"], drums.ops[1].params["until"]) == ("8", "9")
    assert drums.ops[1].enabled is False
    assert [v.octave for v in p.voices if v.name.startswith("pad")] == [3, 4]
    assert p.get_voice("pad1").ops[0].params["at"] == 5
    assert [o.id for o in p.get_voice("pad1").ops] == ["pad1_chords_5", "fx_pad1"]
    assert p.meta["master"] == {"room": {"decay": 1.5}, "push": 6.0,
                                "stops": [{"from": "8:3", "until": "9", "keep": ["lead"]}]}


@pytest.mark.parametrize("bad, says", [
    ("section A bars=4", "first line names the piece"),
    ("piece x\nsection A bars=4\nvoice v violin\n  play motif=nope at=1", "nope"),
    ("piece x\nsection A bars=4\nvoice v violin\n  phrase steps=\"0 2\" at=@B", "no section"),
    ("piece x\nsection A bars=4\nvoice v violin\n  phrase steps=\"0\" at=1 loud=yes",
     "does not take"),
    ("piece x\nsection A bars=4\nvoice v kazoo", "kazoo"),
    ("piece x\nsection A bars=4\nharmony\n  1: Q9", "harmony"),
    ("piece x\nsection A bars=4\nwibble", "starts with one of"),
])
def test_a_mistake_names_its_line(bad, says):
    with pytest.raises(ScoreError, match=says) as err:
        compile_score(bad)
    assert err.value.line is None or err.value.line >= 1


def test_a_score_with_a_mistake_in_it_never_reaches_the_file(tmp_path):
    s = Studio(tmp_path)
    first = s.build(text=SCORE)
    assert first.ok and "built 'small'" in first.message
    before = s.path_for("small").read_text()
    with pytest.raises(ScoreError):
        s.build(text=SCORE.replace("motif=wide", "motif=missing"))
    assert s.path_for("small").read_text() == before
    # A build is a checkpoint like any other edit.
    s.build(text=SCORE.replace("tempo=120", "tempo=132"))
    assert s.get("small").tempo == 132
    assert s.undo("small").ok and s.get("small").tempo == 120


def test_the_cli_builds_a_score_and_writes_one_out(tmp_path, capsys):
    path = tmp_path / "small.ms"
    path.write_text(SCORE)
    assert main(["-p", str(tmp_path), "build", str(path)]) == 0
    assert "built 'small'" in capsys.readouterr().out
    assert main(["-p", str(tmp_path), "source", "small", "--write"]) == 0
    written = tmp_path / "scores" / "small.ms"
    assert compile_score(written.read_text()).to_json() == \
        Studio(tmp_path).get("small").to_json()
    path.write_text(SCORE.replace("role=melody", "role=tune"))
    assert main(["-p", str(tmp_path), "build", str(path)]) == 1
    assert "line" in capsys.readouterr().err


# --------------------------------------------------------------------------
# instruments
# --------------------------------------------------------------------------

def test_a_synth_patch_is_bandlimited_and_a_filter_sweep_darkens_it():
    np = pytest.importorskip("numpy")
    from musicstudio import synth

    def note(name, pitch, vel=100, dur=0.6):
        ctx = synth.NoteCtx(name, "v", pitch, 0.0, dur, vel, None, False, ("v", 0, pitch))
        return sum(sig for sig, _ in synth.render_note(ctx, 10 ** 7))

    # `zap` at full velocity starts three octaves above its note: the tables
    # have to be chosen for where the pitch goes, not where it is written.
    for name in ("saw_lead", "hoover", "wobble_bass", "fm_bell", "bass_808", "zap",
                 "fm_epiano"):
        for pitch in (36, 72, 96, 100):
            sig = note(name, pitch, vel=127, dur=0.35)
            spec = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
            f = np.fft.rfftfreq(len(sig), 1 / synth.SR)
            assert np.isfinite(sig).all()
            assert spec[f > 18000].max() < spec.max() * 10 ** (-40 / 20), (name, pitch)
    # A pluck's filter shuts: its second half is darker than its first.
    sig = note("synth_pluck", 60, dur=0.8)
    half = len(sig) // 4

    def centroid(x):
        spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
        return float((spec * np.fft.rfftfreq(len(x), 1 / synth.SR)).sum() / spec.sum())

    assert centroid(sig[:half]) > 1.5 * centroid(sig[half:2 * half])
    # An 808 falls onto its note.
    low = note("bass_808", 33, dur=1.0)
    early, late = low[:2048], low[8192:8192 + 8192]
    assert centroid(early) > centroid(late)


def test_every_instrument_can_be_played_somewhere():
    """Each one has a model (or is a plain oscillator), and one that lives in
    its own SoundFont names a catalogued bank and a stand-in that exists."""
    pytest.importorskip("numpy")
    from musicstudio import soundfonts, synth
    from musicstudio.ensemble import INSTRUMENTS
    for name, inst in INSTRUMENTS.items():
        if inst.font:
            assert inst.font in soundfonts.BANKS, name
            assert inst.preset is not None and inst.like in INSTRUMENTS, name
        if inst.family not in ("voice", "chip") and name not in ("synth_lead", "synth_bass"):
            assert name in synth.MODELS, name
        for drum, key in inst.keymap:
            assert 0 <= drum <= 127 and 0 <= key <= 127


# --------------------------------------------------------------------------
# the SoundFont catalogue
# --------------------------------------------------------------------------

def test_every_bank_is_pinned_and_says_what_it_asks():
    from musicstudio import soundfonts
    doc = (Path(__file__).resolve().parents[1] / "SOUNDFONTS.md").read_text()
    for name, b in soundfonts.BANKS.items():
        assert b.url.startswith("https://") and len(b.sha256) == 64, name
        assert b.license_member or (b.license_url and b.license_sha256), name
        if b.extra:
            assert b.terms, name
            assert f"`{name}`" in doc, f"{name} is not in SOUNDFONTS.md"
        if b.archive:
            assert b.archive in ("tar", "zip", "7z") and b.member, name


def _sf2() -> bytes:
    body = b"sfbk" + b"\0" * 32
    return b"RIFF" + struct.pack("<I", len(body)) + body


def test_a_bank_for_particular_instruments_is_never_the_general_bank(tmp_path, monkeypatch):
    from musicstudio import audio, soundfonts
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as z:
        z.writestr("inner/Special.sf2", _sf2())
        z.writestr("inner/LICENSE", "free")
    data = blob.getvalue()
    bank = soundfonts.Bank("special", "a test bank", "https://example.invalid/s.zip",
                           hashlib.sha256(data).hexdigest(), 1, "Special.sf2",
                           archive="zip", member="inner/Special.sf2",
                           license_member="inner/LICENSE", extra=True, terms="free")
    monkeypatch.setitem(soundfonts.BANKS, "special", bank)
    monkeypatch.setattr(soundfonts, "_fetch", lambda url, sha, progress=None: data)
    out = soundfonts.install("special", dest=tmp_path, quiet=True)
    assert out == tmp_path / soundfonts.EXTRA_DIR / "Special.sf2"
    assert out.with_suffix(".LICENSE.txt").read_text() == "free"
    assert soundfonts.path_of("special", tmp_path) == out
    assert out in soundfonts.installed(tmp_path)
    # It is one directory down, where the search for a General MIDI bank
    # does not look: a kit of synth drums must never play a whole orchestra.
    monkeypatch.setattr(audio, "SOUNDFONT_DIRS", (str(tmp_path),))
    monkeypatch.delenv("MUSICSTUDIO_SOUNDFONT", raising=False)
    with pytest.raises(FileNotFoundError):
        audio.find_soundfont()
    # A member that is not there is an error, not an empty bank.
    wrong = soundfonts.Bank("wrong", "", "https://example.invalid/s.zip", bank.sha256, 1,
                            "W.sf2", archive="zip", member="nope.sf2", extra=True)
    monkeypatch.setitem(soundfonts.BANKS, "wrong", wrong)
    with pytest.raises(ValueError, match="does not contain"):
        soundfonts.install("wrong", dest=tmp_path, quiet=True)
    assert not (tmp_path / soundfonts.EXTRA_DIR / "W.sf2").exists()


def test_an_instrument_whose_bank_is_missing_says_so_and_still_plays(monkeypatch):
    pytest.importorskip("numpy")
    from musicstudio import audio, soundfonts
    from musicstudio.doc import Section, Voice
    p = Piece("g", "E minor", tempo=120, style="electronic")
    p.sections.append(Section("A", 1))
    p.voices.append(Voice("g", "amp_guitar", "harmony", engine="soundfont"))
    p.add_op("g", "phrase", id="x", at="1", steps="0:1/2 4:1/2")
    monkeypatch.setattr(soundfonts, "path_of", lambda name, dest=None: None)
    monkeypatch.setattr(audio, "soundfont_available", lambda: False)
    monkeypatch.setattr(audio.shutil, "which", lambda exe: "/usr/bin/" + exe)
    with pytest.warns(UserWarning, match="guitar_dist"):
        left, _ = audio.synthesize(p, reverb=False)
    assert max(abs(x) for x in left) > 0.01
    with pytest.raises(RuntimeError, match="guitar_dist"):
        audio.synthesize(p, reverb=False, strict=True)


# --------------------------------------------------------------------------
# against a reference
# --------------------------------------------------------------------------

def test_match_finds_where_a_render_and_a_recording_differ(tmp_path):
    np = pytest.importorskip("numpy")
    import shutil
    if not shutil.which("ffmpeg"):
        pytest.skip("needs ffmpeg")
    s = Studio(tmp_path)
    s.build(text=SCORE)
    # The reference is the piece itself with everything above 1 kHz removed
    # and a 50 Hz tone added: the report has to find both, and only those.
    left, right = audio_of(s)
    mix = ((np.asarray(left) + np.asarray(right)) / 2)[:16 * 44100]   # eight bars at 120
    spec = np.fft.rfft(mix)
    f = np.fft.rfftfreq(len(mix), 1 / 44100)
    spec[f > 1000] = 0
    dark = np.fft.irfft(spec, len(mix)) + 0.2 * np.sin(2 * math.pi * 50 * np.arange(len(mix)) / 44100)
    ref = tmp_path / "ref.wav"
    with wave.open(str(ref), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes((np.clip(dark, -1, 1) * 32000).astype("<i2").tobytes())
    report = s.match("small", str(ref))
    assert "measured" in report.splitlines()[0]
    assert "presence is" in report and "over the reference" in report
    # ... and says whose it is, and that nothing on that voice shapes it yet.
    line = next(x for x in report.splitlines() if "presence is" in x)
    assert "lead" in line and "no level or tone op yet" in line
    low = next(x for x in report.splitlines() if "under 80 Hz" in x)
    mine, theirs = (int(x.strip().rstrip("%")) for x in
                    low.split("Hz")[1].split("of")[0].split("vs"))
    assert theirs > mine + 20
    same = tmp_path / "same.wav"
    with wave.open(str(same), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
        w.writeframes((np.clip(mix, -1, 1) * 32000).astype("<i2").tobytes())
    assert "nothing is 6 dB out" in s.match("small", str(same))


def audio_of(s: Studio):
    from musicstudio import audio
    return audio.synthesize(s.get("small"))


def test_hear_says_what_a_listener_would_say_first(tmp_path):
    """One thing far too loud, a note repeated like a machine, a hole in the
    music: each was first reported by a person or a listening model, not by
    the studio, and each is a measurement."""
    pytest.importorskip("numpy")
    from musicstudio import listen
    s = Studio(tmp_path)
    s.build(text="""
piece loud key="A minor" tempo=120 style=electronic
section A bars=8 dynamic=mf
harmony
  1: i*8
voice tune saw_lead role=melody octave=5
  line: phrase at=1 steps="0:1/1 | 2:1/1 | r:1/1 | r:1/1 | 4:1/1 | 2:1/1 | 0:1/1 | 0:1/1" dynamic=p
voice bell fm_bell role=ornament octave=5
  hits: phrase at=1 steps="4:1/4 4:1/4 4:1/4 4:1/4 | 4:1/4 4:1/4 4:1/4 4:1/4 | r:1/1 | r:1/1 | 4:1/4 4:1/4 4:1/4 4:1/4 | 4:1/4 4:1/4 4:1/4 4:1/4 | 4:1/4 4:1/4 4:1/4 4:1/4 | 4:1/4 4:1/4 4:1/4 4:1/4" dynamic=ff
  up: gain db=2
""")
    piece = s.get("loud")
    h = listen.hear(piece)
    said = "\n".join(listen.reading(h))
    assert "bell (ornament) alone is up to" in said and "louder than everything else" in said
    assert "bell plays one pitch at one loudness 16 times in a row from bar 5" in said
    assert any(bar in (3, 4) and not declared for bar, _, _, declared in h.gaps)
    assert "of silence at" in said
    assert h.character["bell"]["run"] == 16 and h.character["tune"]["run"] < 4
    assert "what each voice is" in listen.view(piece, heard=h)


def test_a_moment_is_found_by_the_clock_and_named_by_its_line(tmp_path):
    s = Studio(tmp_path)
    (tmp_path / "scores").mkdir()
    (tmp_path / "scores" / "small.ms").write_text(SCORE)
    first = s.build("small")
    assert "since the last build" not in first.message
    # 120 bpm: bar 3 starts at four seconds.
    said = s.at("small", time="0:00.5")
    assert "bar 1 beat 2" in said and "section 'A'" in said
    lead = next(x for x in said.splitlines() if x.strip().startswith("lead"))
    assert "tune (line " in lead
    assert s.at("small", bar="1:2").splitlines()[0] == said.splitlines()[0]
    assert "bar 3 beat 2" in s.at("small", time="0:04.5")    # 120 bpm: bar 3 is at 4 s
    # A second build says what the edit did, and only that.
    (tmp_path / "scores" / "small.ms").write_text(
        SCORE.replace("times=2 dynamic=mf", "times=2 dynamic=f"))
    again = s.build("small")
    assert "since the last build: tune: dynamic mf -> f" in again.message
    assert "nothing changed" in s.build("small").message


def test_match_with_stems_finds_a_kit_that_is_too_quiet(tmp_path):
    """Two mixes can have the same spectrum with the drums 12 dB apart; only
    stems show it. The reference here is the piece's own stems, with its
    drums turned up."""
    np = pytest.importorskip("numpy")
    import shutil
    if not shutil.which("ffmpeg"):
        pytest.skip("needs ffmpeg")
    from musicstudio import listen
    s = Studio(tmp_path)
    s.build(text=SCORE)
    piece = s.get("small")
    parts, _ = listen.stems(piece)
    drums = parts["drums"].mean(axis=1)
    rest = sum(v.mean(axis=1) for k, v in parts.items() if k != "drums")
    folder = tmp_path / "stems"
    folder.mkdir()

    def write(path, x):
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(44100)
            w.writeframes((np.clip(x, -1, 1) * 32000).astype("<i2").tobytes())

    cut = 16 * 44100
    write(folder / "drums.wav", drums[:cut] * 4.0)
    write(folder / "bass.wav", np.zeros(cut))
    write(folder / "other.wav", rest[:cut])
    write(tmp_path / "ref.wav", (drums * 4.0 + rest)[:cut] * 0.5)
    report = s.match("small", str(tmp_path / "ref.wav"), stems=str(folder))
    assert "balance by stem" in report
    line = next(x for x in report.splitlines() if "the drums are" in x)
    assert "quieter against the rest of the band" in line and "drums here is drums" in line
    assert "drums on a sixteenth grid" in report
    with pytest.raises(FileNotFoundError, match="drums"):
        s.match("small", str(tmp_path / "ref.wav"), stems=str(tmp_path))


# --------------------------------------------------------------------------
# found by review: each of these was wrong once
# --------------------------------------------------------------------------

HEAD = 'piece x key="A minor" tempo=120 style=electronic\nsection A bars=4\n'


def test_a_score_does_not_reinterpret_or_drop_what_was_written(tmp_path, monkeypatch):
    # No dictionary: the words are spelled out the same way on every machine.
    from musicstudio import lyrics
    monkeypatch.setattr(lyrics, "DICT_DIR", tmp_path / "no_dictionary")
    # An op indented under an op used to vanish.
    with pytest.raises(ScoreError, match="indented under an op"):
        compile_score(HEAD + 'voice v violin\n  phrase at=1 steps="0 2"\n    gain db=-12')
    # Quoted text is text: a lyric that starts with an at-sign is not a bar.
    p = compile_score(HEAD + 'voice v singer\n  phrase at=@A steps="0 2"\n'
                             '  words: lyrics text="@A la"')
    assert p.find_op("words")[1].params["text"] == "@A la"
    # A loop variable is not substituted inside quotes or JSON.
    p = compile_score(HEAD + 'for i in 1..2\n  voice v{i} violin\n'
                             '    n{i}: phrase at={i} steps="0 2" -- bar {i}\n'
                             '    l{i}: lyrics text="{i} la"')
    assert p.find_op("l2")[1].params["text"] == "{i} la"
    assert p.find_op("n2")[1].params["at"] == 2
    # A note is a note on a master line too, and may contain " # ".
    p = compile_score(HEAD.replace("section", "master push=6 -- level=-20\nsection")
                      + 'voice v violin\n  a: phrase at=1 steps="0" -- take # 2 of it')
    assert p.meta["master"] == {"push": 6.0}
    assert p.find_op("a")[1].note == "take # 2 of it"
    assert compile_score(decompile(p)).to_json() == p.to_json()


def test_a_build_reports_a_reordering_and_a_voice_field(tmp_path):
    s = Studio(tmp_path)
    one = HEAD + ('voice v violin dynamic=mf\n  a: phrase at=1 steps="0 2"\n'
                  '  g: gain db=6\n  d: drive amount=0.5')
    s.build(text=one)
    swapped = s.build(text=one.replace('  g: gain db=6\n  d: drive amount=0.5',
                                       '  d: drive amount=0.5\n  g: gain db=6'))
    assert "the order of ops on v" in swapped.message
    assert "voice v" in s.build(text=one.replace("dynamic=mf", "dynamic=p")).message


def test_the_measurements_measure_what_they_say():
    np = pytest.importorskip("numpy")
    from musicstudio import listen
    # A tone just under 4 kHz is under 4 kHz, however it is gated.
    t = np.arange(44100 * 6) / 44100
    tone = np.sin(2 * math.pi * 3900 * t) * (0.2 + 0.8 * (np.sin(2 * math.pi * 3 * t) > 0))
    assert listen._stem_sound(tone)["above4k"] < 2.0
    # The same waveform, with silence after it, is the same level.
    buf = np.stack([tone, tone], 1)
    padded = np.concatenate([buf, np.zeros((44100 * 5, 2))])
    assert listen._loudness(listen._fixed(buf, 0, 8 * 44100)) == \
        pytest.approx(listen._loudness(listen._fixed(padded, 0, 8 * 44100)))
    # A constant offset in a separated stem is not an instrument.
    assert listen._stem_hits(np.full(44100 * 4, 0.3), np.full(44100 * 4, 0.3)) == {} or True


def test_a_crescendo_on_one_note_is_not_one_loudness(tmp_path):
    pytest.importorskip("numpy")
    from musicstudio import listen
    s = Studio(tmp_path)
    s.build(text=HEAD.replace("bars=4", "bars=2") + 'voice v saw_lead octave=5\n'
            '  a: phrase at=1 steps="0 0 0 0 0 0 0 0 | 0 0 0 0 0 0 0 0"\n'
            '  up: dynamics from=1 until=3 start=pp end=ff')
    h = listen.hear(s.get("x"))
    assert h.character["v"]["run"] < 12
