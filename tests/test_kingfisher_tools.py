"""What `kingfisher` needed that the studio did not have: altered dominants,
a voicing without its root, a chord held over a bar line in a score file, an
echo that follows the tempo, and the surface of a record."""

from __future__ import annotations

import pytest

from musicstudio import Key, Piece, Section, Voice, audio, render
from musicstudio import lint as run_lint
from musicstudio.doc import HarmonyEntry
from musicstudio.score import compile_score, decompile
from musicstudio.theory import parse_chord


def test_altered_dominants_and_major_ninths_are_spelled():
    key = Key.parse("E minor")
    assert parse_chord("V7b9", key).intervals == (0, 4, 7, 10, 13)
    assert parse_chord("V7#9", key).intervals == (0, 4, 7, 10, 15)
    assert parse_chord("V7b13", key).intervals == (0, 4, 7, 10, 20)
    assert parse_chord("bIImaj7#11", key).intervals == (0, 4, 7, 11, 18)
    # A major ninth on a root from outside the key keeps its major seventh:
    # the ninth must not bring a minor seventh in with it.
    assert parse_chord("bIImaj9", key).intervals == (0, 4, 7, 11, 14)
    assert parse_chord("IIImaj9", key).intervals == (0, 4, 7, 11, 14)
    assert parse_chord("V7b9/ii", Key.parse("C major")).root_offset == 9
    # What was understood before is understood the same way.
    assert parse_chord("V9", Key.parse("C major")).intervals == (0, 4, 7, 10, 14)
    assert parse_chord("ii%7", key).intervals == (0, 3, 6, 10)


def _chord_piece() -> Piece:
    p = Piece("c", "C major", tempo=120)
    p.sections.append(Section("A", 2))
    p.harmony = [HarmonyEntry("1", "ii9"), HarmonyEntry("2", "V")]
    p.voices.append(Voice("keys", "piano", "harmony"))
    return p


def test_a_rootless_voicing_starts_on_the_third():
    p = _chord_piece()
    p.add_op("keys", "chords", id="c", at="1", bars=2, tones=4, octave=4, rhythm="1/1")
    rooted = sorted(n.pitch for n in render(p).notes if n.start == 0)
    p.update_op("c", rootless=True)
    notes = render(p).notes
    rootless = sorted(n.pitch for n in notes if n.start == 0)
    assert [x % 12 for x in rooted] == [2, 5, 9, 0]            # D F A C
    assert [x % 12 for x in rootless] == [5, 9, 0, 4]          # F A C E
    # A triad has no tone to spare: it keeps its root.
    assert 7 in {n.pitch % 12 for n in notes if n.start > 0}


SCORE = """
piece held key="A minor" tempo=120
section A bars=4
harmony
  @A: iv9 . V7b9 .
voice gtr guitar role=harmony octave=3
  arp: chords at=@A bars=4 tones=4 rhythm=1/4 figure="0 1 2 3 | 3 2 1 0"
"""


def test_a_dot_in_a_harmony_line_holds_the_chord_and_the_figure_runs_on():
    p = compile_score(SCORE)
    assert [(h.at, h.chord) for h in p.harmony] == [("1", "iv9"), ("3", "V7b9")]
    pitches = [n.pitch for n in sorted(render(p).notes, key=lambda n: n.start)]
    # One chord over two bars is one span, so a two-bar figure is played
    # through once -- up, then down -- and not restarted at the bar line.
    assert pitches[:8] == pitches[:4] + pitches[:4][::-1]
    assert compile_score(decompile(p)).to_json() == p.to_json()


def _one_note(instrument: str = "synth_lead") -> Piece:
    p = Piece("e", "A minor", tempo=120, style="electronic")
    p.sections.append(Section("A", 4))
    p.voices.append(Voice("v", instrument, "melody", pan=0.0))
    p.add_op("v", "phrase", id="f", steps="0:1/8 r:1/8 r:1/4 r:1/2", at="1", octave=4)
    return p


def test_an_echo_repeats_on_the_grid_each_time_quieter_and_duller():
    np = pytest.importorskip("numpy")
    p = _one_note()
    before = render(p).notes
    dry, _ = audio.synthesize(p, reverb=False)
    p.add_op("v", "echo", id="e", time="1/4", feedback=0.5, mix=0.5, spread=0.0, tone=1500)
    assert render(p).notes == before                     # the notes are untouched
    left, right = audio.synthesize(p, reverb=False)
    assert len(left) == len(dry)

    def power(x, beat):                                  # a quarter is 0.5 s at 120
        a = int(beat * 0.5 * audio.SR)
        return float(np.mean(x[a:a + int(0.2 * audio.SR)] ** 2))

    def top(x, beat):
        a = int(beat * 0.5 * audio.SR)
        spec = np.abs(np.fft.rfft(x[a:a + int(0.2 * audio.SR)])) ** 2
        f = np.fft.rfftfreq(int(0.2 * audio.SR), 1 / audio.SR)
        return spec[f > 2000].sum() / spec.sum()

    assert power(dry, 1) < power(dry, 0) * 1e-4          # dry: nothing on beat two
    assert power(left, 0) == pytest.approx(power(dry, 0), rel=1e-6)
    repeats = [power(left, k) for k in (1, 2, 3)]
    assert repeats[0] > power(dry, 0) * 0.05
    assert repeats[0] > repeats[1] * 2 > repeats[2] * 4
    assert top(left, 3) < top(left, 1) < top(dry, 0)     # every pass loses top
    assert np.allclose(left, right)                      # spread=0 stays in the middle

    p.update_op("e", spread=1.0)
    left, right = audio.synthesize(p, reverb=False)
    assert power(left, 1) > power(right, 1) * 100        # first repeat to the left,
    assert power(right, 2) > power(left, 2) * 100        # the second to the right

    # An echo over one bar is a throw: a note outside the span is not repeated.
    p.update_op("e", **{"from": "3", "until": "4"})
    thrown, _ = audio.synthesize(p, reverb=False)
    assert power(thrown, 1) < power(dry, 0) * 1e-4


def test_a_record_crackles_the_same_way_every_time_and_is_not_harmony():
    np = pytest.importorskip("numpy")
    p = Piece("r", "C major", tempo=120)
    p.sections.append(Section("A", 2))
    p.harmony = [HarmonyEntry("1", "I")]
    p.voices.append(Voice("dust", "vinyl", "ornament"))
    p.voices.append(Voice("gtr", "guitar", "harmony"))
    p.add_op("dust", "drone", id="d", at="1", bars=2, degree=1, octave=2)
    p.add_op("gtr", "chords", id="c", at="1", bars=2, octave=2)
    assert all(n.percussive for n in render(p).notes if n.voice == "dust")
    # A second low against the guitar's root: mud if it were a pitch.
    assert not [f for f in run_lint(p) if f.code in ("low_interval_limit", "chord_clash")]

    p.voices[1].muted = True
    left, right = audio.synthesize(p, reverb=False)
    again, _ = audio.synthesize(p, reverb=False)
    assert np.array_equal(left, again)
    body = left[:int(3.5 * audio.SR)]
    assert np.abs(body).max() > 0
    # Pops, not hiss: one sample in a hundred holds a third of the energy
    # (of steady noise it would hold a fifteenth).
    loud = np.sort(body ** 2)[::-1]
    assert loud[:len(loud) // 100].sum() > 0.3 * loud.sum()
    assert not np.allclose(left, right)                  # each side has its own dust
