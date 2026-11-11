"""UTAU voicebanks: reading one, singing from it, and writing a line out.

No real voicebank is used or fetched: the bank here is recorded from the
studio's own formant singer, one file per syllable, with an ``oto.ini`` that
says where each begins -- which is all a voicebank is.
"""

from __future__ import annotations

import warnings
import wave
import zipfile

import pytest

from musicstudio import Studio, utau
from musicstudio.cli import main

np = pytest.importorskip("numpy")

PITCH = 60


def _bank(root, *, encoding="cp932", only=None):
    """A separate-syllable (CV) bank sung by the formant singer at middle C."""
    from musicstudio import vocal
    from musicstudio.vocal import SINGERS, SR, Sung
    root.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in utau._BASIC:
        c, v = key
        kana = "ん" if c == "N" else utau._KANA[key]
        if only is not None and kana not in only:
            continue
        s = Sung(0.3, 0.9, PITCH, 100, (c,) if c and c != "N" else (), "N" if c == "N" else v, ())
        sig, t0 = vocal.render_phrase([s], SINGERS["singer"], 1)
        x = sig / (abs(sig).max() + 1e-9) * 0.5
        with wave.open(str(root / f"{kana}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((x * 32767).astype("<i2").tobytes())
        # The vowel starts 0.3 s in: the alias begins 100 ms before that.
        lines.append(f"{kana}.wav=,{(0.3 - t0 - 0.1) * 1000:.0f},150,-600,100,40")
    (root / "oto.ini").write_bytes("\r\n".join(lines).encode(encoding))
    (root / "character.txt").write_bytes("name=テスト\r\nauthor=nobody".encode(encoding))
    (root / "readme.txt").write_bytes("terms".encode(encoding))
    return root


class _ShiftJis(zipfile.ZipInfo):
    """A zip entry whose name is stored in Shift-JIS and not marked as UTF-8."""

    def _encodeFilenameFlags(self):
        return self.filename.encode("cp932"), self.flag_bits & ~0x800


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(utau, "UTAU_DIR", tmp_path / "utau")
    monkeypatch.setattr(utau, "_banks", {})
    from musicstudio import lyrics
    monkeypatch.setattr(lyrics, "DICT_DIR", tmp_path / "no_dictionary")
    return tmp_path


def _piece(tmp_path, bank="utau:test", text="sa ku ra no ha na",
           steps="0:1/4 2:1/4 4:1/4 2:1/4 0:1/2 4:1/2"):
    s = Studio(tmp_path / "project")
    s.create("u", key="C major", tempo=100, sections=[("A", 2)])
    s.set_harmony("u", [["1", "I"]])
    s.add_voice("u", "vox", "singer", role="melody", bank=bank, octave=4)
    s.add_op("u", "vox", "phrase", at="1", steps=steps)
    s.add_op("u", "vox", "lyrics", text=text)
    return s


def _sing(s, **kw):
    """``({voice: (left, right)}, sample rate, seconds per beat)``."""
    from musicstudio import utau as u
    from musicstudio.render import render
    from musicstudio.vocal import SR
    piece = s.get("u")
    r = render(piece)
    beat = 60.0 / piece.tempo / 480.0
    total = int((max(n.start + n.dur for n in r.notes) * beat + 1.0) * SR)
    got = u.voice_stems(piece, r.notes, lambda t: t * beat, total, {}, **kw)
    return got, SR, beat * 480


def _periodic(x, sr, hz):
    """How alike the signal is to itself one period of ``hz`` later (1 = exactly)."""
    lag = int(round(sr / hz))
    a, b = x[:-lag], x[lag:]
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-12))


def test_an_oto_line_is_read_the_way_utau_means_it(tmp_path):
    root = _bank(tmp_path / "b", only={"か", "あ"})
    extra = ("か.wav=k2,100,50,30,20,-5\r\nmissing.wav=x,0,0,0,0,0\r\nあ.wav=,10,,,,\r\n")
    with open(root / "oto.ini", "ab") as f:
        f.write(("\r\n" + extra).encode("cp932"))
    entries, missing = utau.read_oto(root / "oto.ini")
    by = {}
    for e in entries:
        by.setdefault(e.alias, e)
    assert missing == 1                                   # named, and not there
    assert by["か"].pre == pytest.approx(0.1)             # an empty alias is the file's name
    k2 = by["k2"]
    assert (k2.offset, k2.consonant, k2.pre, k2.overlap) == pytest.approx((0.1, 0.05, 0.02, -0.005))
    # A positive cutoff counts back from the end of the file; a negative one
    # forward from the offset.
    from musicstudio.vocal import SR
    unit, start, pre, fixed, end, _ = utau._unit(k2)
    with wave.open(str(root / "か.wav")) as w:
        length = w.getnframes()
    assert end - start == pytest.approx(length - int(0.03 * SR) - int(0.1 * SR), abs=2)
    unit, start, pre, fixed, end, _ = utau._unit(by["か"])
    assert end - start == pytest.approx(int(0.6 * SR), abs=2)
    assert pre - start == pytest.approx(int(0.1 * SR), abs=2)


def test_a_bank_sings_the_written_pitches_with_the_vowel_on_the_beat(home):
    utau.add("test", _bank(home / "bank"))
    got, sr, beat = _sing(_piece(home), strict=True)
    left, right = got["vox"]
    x = left + right
    for at, degree in ((0, 60), (1, 64), (2, 67), (3, 64), (4, 60), (6, 67)):
        hz = 440.0 * 2 ** ((degree - 69) / 12)
        mid = int((at + 0.5) * beat * sr)
        assert _periodic(x[mid - 2048:mid + 2048], sr, hz) > 0.9, (at, degree)
    # "sa": the s is sung before the beat and the vowel is there on it.
    k = int(1 * beat * sr)                                 # "ku", the second note
    win = int(0.03 * sr)
    assert np.sqrt((x[k + win:k + 2 * win] ** 2).mean()) > 0.02
    # ...and it is the bank that sang: the same line from the formant singer differs.
    plain = _piece(home / "plain", bank=None)
    assert "vox" not in _sing(plain)[0]


def test_the_same_phrase_is_sung_the_same_way_twice(home):
    utau.add("test", _bank(home / "bank"))
    s = _piece(home)
    a = _sing(s)[0]["vox"][0]
    utau._units.clear()
    b = _sing(s)[0]["vox"][0]
    assert np.array_equal(a, b)


def test_a_held_note_and_a_closing_n_are_sung_from_the_bank(home):
    utau.add("test", _bank(home / "bank"))
    s = _piece(home, text="shin - ka i", steps="0:1/4 2:1/4 4:1/2 2:1/1")
    got, sr, beat = _sing(s, strict=True)
    x = got["vox"][0]
    # The held note carries on at its own pitch (E4), with no silence before it.
    mid = int(1.4 * beat * sr)
    assert _periodic(x[mid - 2048:mid + 2048], sr, 440.0 * 2 ** ((64 - 69) / 12)) > 0.9
    join = int(1.0 * beat * sr)
    assert np.sqrt((x[join - 1024:join + 1024] ** 2).mean()) > 0.02


def test_a_missing_bank_falls_back_and_a_missing_syllable_is_reported(home):
    s = _piece(home, bank="utau:nobody")
    with pytest.warns(UserWarning, match="no UTAU bank called 'nobody'"):
        assert _sing(s)[0] == {}
    with pytest.raises(RuntimeError, match="no UTAU bank"):
        _sing(s, strict=True)
    # The whole render still sings: the formant singer takes the voice.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert s.export_wav("u").exists()
    utau.add("few", _bank(home / "few", only={"あ", "さ", "く"}))
    with pytest.warns(UserWarning, match="has no recording for"):
        got = _sing(_piece(home / "two", bank="utau:few"))[0]
    assert abs(got["vox"][0]).max() > 0.01


def test_a_zip_is_unpacked_with_its_japanese_file_names(home):
    src = _bank(home / "src", only={"あ", "か"})
    z = home / "bank.zip"
    with zipfile.ZipFile(z, "w") as f:
        for p in src.iterdir():
            # As a zip made on Japanese Windows has them: Shift-JIS, unflagged.
            f.writestr(_ShiftJis("voice/" + p.name), p.read_bytes())
        f.writestr("../outside.txt", "no")
    d = utau.add("zipped", z)
    assert d["missing_files"] == 0 and d["aliases"] == 2
    assert d["voice"] == "テスト" and any(t.endswith("readme.txt") for t in d["terms"])
    assert not (home / "utau" / "outside.txt").exists() and not (home / "outside.txt").exists()
    assert utau.banks() == ["zipped"]
    with pytest.raises(ValueError, match="already a bank"):
        utau.add("zipped", z)
    with pytest.raises(ValueError, match="not a bank name"):
        utau.add("../x", z)
    utau.remove("zipped")
    assert utau.banks() == []


def test_removing_a_bank_that_was_only_pointed_at_leaves_the_folder(home):
    src = _bank(home / "mine", only={"あ"})
    utau.add("mine", src)
    utau.remove("mine")
    assert (src / "oto.ini").exists() and utau.find("mine") is None


def test_english_is_approximated_through_the_bank_s_syllables():
    from musicstudio.lyrics import Syllable
    assert utau.kana_of(Syllable(("s",), "a", ()).to_json()) == ["さ"]
    assert utau.kana_of(Syllable(("k", "y"), "o", ()).to_json()) == ["きょ"]
    assert utau.kana_of("m ay") == ["ま", "い"]            # a diphthong closes on its second vowel
    assert utau.kana_of("s t r ey n jh") == ["れ", "い", "ん"]
    assert utau.kana_of("l ah v") == ["ら"]
    assert utau.kana_of("-") == ["-"]


def test_a_voice_is_written_out_as_a_ust(home, capsys):
    s = _piece(home, text="sa ku ra shin - i")
    assert main(["-p", str(home / "project"), "ust", "u", "vox"]) == 0
    path = capsys.readouterr().out.strip()
    text = open(path, "rb").read().decode("cp932")
    assert text.startswith("[#VERSION]\r\nUST Version1.2\r\n[#SETTING]\r\nTempo=100.00")
    assert text.rstrip().endswith("[#TRACKEND]")
    notes = [b for b in text.split("[#")[3:] if b.startswith("0")]
    lyric = [ln.split("=")[1] for b in notes for ln in b.splitlines() if ln.startswith("Lyric=")]
    length = [int(ln.split("=")[1]) for b in notes for ln in b.splitlines()
              if ln.startswith("Length=")]
    pitch = [int(ln.split("=")[1]) for b in notes for ln in b.splitlines()
             if ln.startswith("NoteNum=")]
    # "shin" is し and a short ん; the held note repeats the sound it holds.
    assert lyric[:6] == ["さ", "く", "ら", "し", "ん", "ん"]
    assert pitch[:3] == [60, 64, 67]
    # No rest between two notes played one after the other, and the line is
    # as long as it was written (less the space after its last note).
    assert "R" not in lyric
    assert 2 * 4 * 480 - 120 <= sum(length) <= 2 * 4 * 480
    with pytest.raises(ValueError, match="plays nothing"):
        s.add_voice("u", "other", "violin")
        s.export_ust("u", "other")


def test_the_utau_commands_show_a_bank_and_where_its_terms_are(home, capsys):
    src = _bank(home / "mine", only={"あ", "か"})
    assert main(["utau", "list"]) == 0
    assert "no UTAU voicebanks yet" in capsys.readouterr().out
    assert main(["utau", "add", "mine", str(src)]) == 0
    out = capsys.readouterr().out
    assert "2 recordings" in out and "readme.txt" in out and 'bank="utau:mine"' in out
    assert main(["utau", "show", "mine"]) == 0
    assert main(["utau", "remove", "mine"]) == 0


# --------------------------------------------------------------------------
# English banks (consonant-vowel and vowel-consonant pieces, X-SAMPA names)
# --------------------------------------------------------------------------

def _names(bank_aliases, text_syllables, gaps=()):
    """The aliases an English bank is asked for, in order, for sung syllables
    given as ``(onset, nucleus, coda)``, a quarter of a second each."""
    from pathlib import Path
    from musicstudio.vocal import Sung
    entries = {a: utau.Entry(a, Path(a), 0.0, 0.1, -300.0, 0.05, 0.02) for a in bank_aliases}
    bank = utau.UtauBank("x", Path("."), entries, {})
    spans, t = [], 0.0
    for i, (on, nuc, coda) in enumerate(text_syllables):
        t += 1.0 if i in gaps else 0.0
        spans.append([Sung(t, t + 0.25, 60, 100, tuple(on), nuc, tuple(coda)), t + 0.25])
        t += 0.25
    lost: set = set()
    events = utau._english_events(bank, spans, lost)
    return [(e.entry.alias, "whole" if e.whole else "bare" if e.bare else "main")
            for e in events], lost


ENGLISH = ["k{", "sI", "tA", "dV", "bE", "I t", "{ t-", "V n-",        # what marks the kind
           "- st", "st", "- tA", "A r", "r t-", "r t", "- aI", "aI", "aI m", "m@", "@", "- @",
           "@ w", "weI", "eI k-", "eI k", "- weI", "tu", "u", "- tu", "t", "mi", "i", "i h",
           "V", "- V", "pV", "V p", "- pV"]


def test_an_english_bank_is_recognised_and_a_japanese_one_is_not():
    from pathlib import Path
    e = {a: utau.Entry(a, Path(a), 0, 0, 0, 0, 0) for a in ENGLISH}
    assert utau.UtauBank("x", Path("."), e, {}).english
    assert not utau.UtauBank("x", Path("."), {"か": e["k{"], "a か": e["k{"]}, {}).english


def test_an_english_syllable_is_a_cluster_a_vowel_and_what_closes_it():
    # "start": the cluster, the consonant-vowel piece on the beat, the vowel
    # closing into r, and r into the released t that ends the phrase.
    got, lost = _names(ENGLISH, [(["s", "t"], "aa", ["r", "t"])])
    assert got == [("- st", "bare"), ("tA", "main"), ("A r", "whole"), ("r t-", "whole")]
    assert not lost
    # "I'm a-wake": a word's last consonant opens the next when that starts
    # on a vowel, and a vowel closes into the consonant that follows it.
    got, _ = _names(ENGLISH, [([], "ay", ["m"]), ([], "ah", []), (["w"], "ey", ["k"])])
    assert got == [("- aI", "main"), ("aI m", "whole"), ("m@", "main"), ("@ w", "whole"),
                   ("weI", "main"), ("eI k-", "whole")]
    # After a silence the phrase starts again from nothing.
    got, _ = _names(ENGLISH, [(["t"], "uw", []), (["m"], "iy", [])], gaps={1})
    assert got == [("- tu", "main"), ("mi", "main")]
    # What the bank lacks is named, and the vowel is still sung.
    got, lost = _names(ENGLISH, [(["z"], "iy", [])])
    assert got == [("i", "main")] and lost == {"zi"}


def test_consonants_never_take_most_of_a_short_note(home):
    """At speed, what closes one syllable and opens the next is squeezed so
    the vowel keeps nearly half the note: every note still sounds."""
    utau.add("test", _bank(home / "bank"))
    s = Studio(home / "fast")
    s.create("u", key="C major", tempo=200, sections=[("A", 2)])
    s.set_harmony("u", [["1", "I"]])
    s.add_voice("u", "vox", "singer", role="melody", bank="utau:test", octave=4)
    s.add_op("u", "vox", "phrase", at="1", steps=" ".join(["0:1/8"] * 12))
    s.add_op("u", "vox", "lyrics", text="shi tsu shi tsu su shi tsu su shi tsu su shi")
    got, sr, beat = _sing(s, strict=True)
    x = got["vox"][0]
    levels = []
    for k in range(12):
        a = int((k * 0.5 + 0.2) * beat * sr)
        levels.append(float(np.sqrt((x[a:a + int(0.2 * beat * sr)] ** 2).mean())))
    assert min(levels) > 0.25 * max(levels), levels
