"""Tests for MusicStudio.

The load-bearing ones are the precision tests. A studio whose critique pass
cries wolf on correct writing is worse than no critique pass at all, so
``test_correct_four_part_writing_has_no_voice_leading_findings`` and its
neighbours exist to hold that line: if a check starts firing on textbook
writing, the check is wrong, not the writing.
"""

from __future__ import annotations

import json
import struct
from fractions import Fraction

import pytest

from musicstudio import (
    Key, Piece, Section, Studio, Voice, lint, make_motif, parse_chord, render,
    similarity, ticks,
)
from musicstudio.lint import LOW_INTERVAL_LIMITS
from musicstudio.midi import to_bytes
from musicstudio.theory import parse_pitch, pitch_name


# --------------------------------------------------------------------------
# theory
# --------------------------------------------------------------------------

def test_durations_are_fractions_of_a_whole_note():
    assert ticks("1/4") == 480
    assert ticks("1/8.") == 360           # dotted eighth is three sixteenths
    assert ticks("1/8t") == 160           # triplet eighth is a third of a quarter
    assert ticks("1/4+1/8") == 720
    assert ticks("q") == ticks("1/4")


def test_triplets_and_dots_stay_whole_ticks():
    """TPQ=480 is chosen so nothing in common use needs rounding."""
    for d in ("1/1", "1/2", "1/4", "1/8", "1/16", "1/32", "1/4t", "1/8t", "1/16t",
              "1/2.", "1/4.", "1/8.", "1/4.."):
        assert ticks(d) > 0


def test_chord_qualities_come_from_the_scale_not_from_the_case():
    """Stacking thirds in the scale is what gets these right without being told."""
    c = Key.parse("C major")
    assert parse_chord("ii", c).intervals == (0, 3, 7)       # minor, unprompted
    assert parse_chord("V7", c).intervals == (0, 4, 7, 10)   # dominant seventh
    assert parse_chord("IVmaj7", c).intervals == (0, 4, 7, 11)
    assert parse_chord("vii%7", c).intervals == (0, 3, 6, 10)  # half-diminished
    assert parse_chord("viio7", c).intervals == (0, 3, 6, 9)   # fully diminished


def test_secondary_and_inverted_chords():
    c = Key.parse("C major")
    assert parse_chord("V/V", c).root_offset == 2            # D, the V of G
    first = parse_chord("V_1", c)
    assert first.bass_pitch(c, 3) % 12 == 11                 # B in the bass


def test_degree_and_pitch_round_trip():
    k = Key.parse("d minor")
    for name in ("D4", "F4", "A4", "C5", "Bb3"):
        p = parse_pitch(name)
        assert k.pitch(*k.degree_of(p)) == p


def test_key_names_are_spelled_off_the_circle_of_fifths():
    assert Key.parse("F#m").name == "F# minor"     # not Gb minor
    assert Key.parse("Bb lydian").name == "Bb lydian"
    assert Key.parse("Cm").name == "C minor"


# --------------------------------------------------------------------------
# motifs -- the transformation algebra must be exact
# --------------------------------------------------------------------------

def test_retrograde_is_an_involution():
    m = make_motif("m", "0 2 4:1/4 3 2:1/2")
    assert m.retrograde().retrograde().source() == m.source()


def test_inversion_is_an_involution():
    m = make_motif("m", "0 2 4:1/4 3 2:1/2")
    assert m.invert().invert().source() == m.source()


def test_augment_and_diminish_round_trip():
    m = make_motif("m", "0 2 4:1/4 3 2:1/2")
    assert m.augment(2).diminish(2).rhythm == m.rhythm
    assert m.augment("3/2").duration == m.duration * 3 // 2


def test_fill_preserves_total_duration():
    """Smoothing a line must not move anything after it."""
    m = make_motif("m", "0 4:1/4 7:1/4")
    assert m.fill().duration == m.duration
    assert len(m.fill().steps) > len(m.steps)


def test_transposition_is_diatonic_so_it_stays_in_key():
    k = Key.parse("d minor")
    m = make_motif("m", "0 1 2 3 4 5 6")
    moved = m.transpose(1)
    scale_pcs = {(k.tonic + s) % 12 for s in k.steps}
    for step in moved.pitched:
        assert k.pitch(step.deg, step.alt, 4) % 12 in scale_pcs


def test_similarity_ignores_transposition_but_not_rhythm():
    m = make_motif("m", "0 2 4:1/4 3 2:1/2")
    assert similarity(m, m.transpose(4)) == pytest.approx(1.0)
    assert similarity(m, make_motif("x", "0 0 0 0 0")) < 0.5


def test_derived_motifs_record_their_lineage():
    m = make_motif("hero", "0 2 4:1/4")
    d = m.invert().augment(2)
    assert d.derived_from == "hero"
    assert d.lineage == ("invert:0", "augment:2")


# --------------------------------------------------------------------------
# timeline and rendering
# --------------------------------------------------------------------------

def _piece(**kw) -> Piece:
    p = Piece(kw.pop("name", "t"), kw.pop("key", "d minor"), **kw)
    return p


def test_mixed_meter_timeline_round_trips():
    p = _piece()
    p.sections += [Section("A", 8), Section("B", 8, meter="3/4"), Section("C", 4)]
    for bar in (1, 5, 9, 12, 17, 20):
        assert p.position_of(p.tick_of(bar)) == (bar, Fraction(1))
    assert p.position_of(p.tick_of("9:2.5")) == (9, Fraction(5, 2))


def test_chord_anchored_motif_refits_every_chord():
    """One arpeggio figure over a progression, fitting each chord it meets."""
    p = _piece(key="C major")
    p.sections.append(Section("A", 2))
    p.harmony += [__import__("musicstudio").HarmonyEntry("1", "I"),
                  __import__("musicstudio").HarmonyEntry("2", "IV")]
    p.add_motif("arp", "0 1 2 1", anchor="chord")
    p.voices.append(Voice("h", "harp", "harmony", octave=4))
    p.add_op("h", "play", id="a", motif="arp", at="1", times=2, every="1/1", octave=4)
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert {n.pitch % 12 for n in notes[:4]} == {0, 4, 7}    # C E G
    assert {n.pitch % 12 for n in notes[4:8]} == {5, 9, 0}   # F A C


def test_a_tie_joins_two_steps_into_one_note():
    p = _piece(key="C major")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "flute", "melody", octave=5))
    p.add_op("v", "phrase", id="f", steps="0~ 0 2", at="1")
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert len(notes) == 2
    assert notes[0].dur > notes[1].dur


def test_auto_octave_lands_inside_the_instrument_range():
    """Nobody names an octave; the studio still has to put the line somewhere real."""
    for instrument in ("piccolo", "tuba", "horn", "contrabass", "violin"):
        p = _piece(key="C major")
        p.sections.append(Section("A", 2))
        p.voices.append(Voice("v", instrument, "melody"))
        p.add_op("v", "phrase", id="f", steps="0 2 4 2 0", at="1")
        inst = p.get_voice("v").inst
        for n in render(p).notes:
            assert inst.lo <= n.pitch <= inst.hi, (instrument, pitch_name(n.pitch))


def test_disabled_ops_produce_nothing():
    p = _piece(key="C major")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "flute", "melody"))
    op = p.add_op("v", "phrase", id="f", steps="0 2 4", at="1")
    assert render(p).notes
    op.enabled = False
    assert not render(p).notes


# --------------------------------------------------------------------------
# lint precision -- correct writing must come back clean
# --------------------------------------------------------------------------

VOICE_LEADING_CODES = {"parallel_fifths", "parallel_octaves", "voice_crossing",
                       "low_interval_limit", "chord_clash", "range_violation",
                       "polyphony_exceeded", "unresolved_leap", "melody_buried"}


def _chorale() -> Piece:
    """I - IV - V - I in C major, correctly voiced and led.

        S  E4  F4  D4  C4
        A  C4  C4  B3  G3
        T  G3  A3  G3  E3
        B  C3  F2  G2  C3

    No parallel perfect intervals, no crossing, nothing below the interval
    limits, every note a chord tone. If this produces a voice-leading finding,
    the check is wrong.
    """
    from musicstudio import HarmonyEntry
    p = Piece("chorale", "C major", tempo=72, style="chamber")
    p.sections.append(Section("A", 2, dynamic="mf"))
    p.harmony += [HarmonyEntry("1", "I"), HarmonyEntry("1:3", "IV"),
                  HarmonyEntry("2", "V"), HarmonyEntry("2:3", "I")]
    for name, role, steps in [("soprano", "melody", "9 10 8 7"),
                              ("alto", "harmony", "7 7 6 4"),
                              ("tenor", "harmony", "4 5 4 2"),
                              ("bass", "bass", "0 -4 -3 0")]:
        p.voices.append(Voice(name, "choir", role, octave=3))
        p.add_op(name, "phrase", id=f"{name}_line", steps=steps, at="1", unit="1/2",
                 octave=3)
    return p


def test_correct_four_part_writing_has_no_voice_leading_findings():
    found = {f.code for f in lint(_chorale())}
    assert not (found & VOICE_LEADING_CODES), sorted(found & VOICE_LEADING_CODES)


def test_the_chorale_actually_sounds_the_chords_it_claims():
    notes = render(_chorale()).notes
    assert len(notes) == 16
    first = sorted(n.pitch for n in notes if n.start == 0)
    assert [pitch_name(p) for p in first] == ["C3", "G3", "C4", "E4"]


def test_parallel_fifths_are_caught():
    p = Piece("bad", "C major", style="chamber")
    p.sections.append(Section("A", 2))
    for name, steps in [("a", "0 1 2"), ("b", "4 5 6")]:
        p.voices.append(Voice(name, "violin", "melody", octave=4))
        p.add_op(name, "phrase", id=f"{name}_line", steps=steps, at="1", unit="1/4",
                 octave=4)
    assert "parallel_fifths" in {f.code for f in lint(p)}


def test_an_explicit_double_op_is_not_reported_as_parallel_motion():
    """Doubling is a request for parallel motion; flagging it reports the feature."""
    p = Piece("dbl", "C major", style="chamber")
    p.sections.append(Section("A", 2))
    p.voices += [Voice("lead", "violin", "melody", octave=4),
                 Voice("shadow", "viola", "counter", octave=4)]
    p.add_op("lead", "phrase", id="line", steps="0 1 2 3", at="1", unit="1/4", octave=4)
    p.add_op("shadow", "double", id="dbl", source="lead", octaves=-1)
    found = {f.code for f in lint(p)}
    assert "parallel_octaves" not in found


def test_a_note_outside_the_instrument_range_is_an_error():
    p = Piece("oops", "C major", style="orchestral")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("t", "tuba", "melody", octave=7))
    p.add_op("t", "phrase", id="f", steps="0 2 4", at="1", octave=7)
    findings = [f for f in lint(p) if f.code == "range_violation"]
    assert findings and findings[0].severity == "error"


def test_a_monophonic_instrument_cannot_be_given_a_chord():
    p = Piece("mono", "C major", style="orchestral")
    p.sections.append(Section("A", 2))
    p.harmony.append(__import__("musicstudio").HarmonyEntry("1", "I"))
    p.voices.append(Voice("o", "oboe", "harmony", octave=4))
    p.add_op("o", "chords", id="c", at="1", bars=1, voicing="block", octave=4)
    assert "polyphony_exceeded" in {f.code for f in lint(p)}


def test_low_interval_limits_match_the_standard_table():
    def floor_for(gap):
        return LOW_INTERVAL_LIMITS[max(k for k in LOW_INTERVAL_LIMITS if k <= gap)]
    # A major second is fine at Eb3 and mud well below it; an octave is fine
    # anywhere a bass instrument can reach.
    assert parse_pitch("G3") >= floor_for(2)
    assert parse_pitch("D2") < floor_for(3)
    assert parse_pitch("D2") >= floor_for(12)
    assert parse_pitch("E2") >= floor_for(7)


def test_a_minor_key_flat_seven_is_flagged_as_a_double_flat():
    from musicstudio import HarmonyEntry
    p = Piece("m", "d minor", style="orchestral")
    p.sections.append(Section("A", 2))
    p.harmony += [HarmonyEntry("1", "i"), HarmonyEntry("2", "bVII")]
    p.voices.append(Voice("v", "cello", "bass"))
    p.add_op("v", "bass", id="b", at="1", bars=2)
    assert "redundant_accidental" in {f.code for f in lint(p)}


def test_identical_sections_are_reported():
    from musicstudio import HarmonyEntry
    p = Piece("rep", "C major", style="orchestral")
    p.sections += [Section("A", 2, dynamic="mf"), Section("B", 2, dynamic="mf")]
    p.harmony += [HarmonyEntry("1", "I"), HarmonyEntry("3", "I")]
    p.voices.append(Voice("v", "flute", "melody", octave=5))
    p.add_op("v", "phrase", id="a", steps="0 2 4 2", at="1", unit="1/4", octave=5)
    p.add_op("v", "phrase", id="b", steps="0 2 4 2", at="3", unit="1/4", octave=5)
    assert "verbatim_repeat" in {f.code for f in lint(p)}


def test_a_derived_motif_played_by_name_is_not_reported_unused():
    p = Piece("d", "C major", style="orchestral")
    p.sections += [Section("A", 4), Section("B", 4), Section("C", 4)]
    p.add_motif("hero", "0 2 4:1/4")
    p.motifs["hero_inv"] = p.get_motif("hero").invert(name="hero_inv")
    p.voices.append(Voice("v", "flute", "melody", octave=5))
    p.add_op("v", "play", id="a", motif="hero", at="1")
    p.add_op("v", "play", id="b", motif="hero_inv", at="5")
    unused = [f for f in lint(p) if f.code == "motif_unused"]
    assert not unused, [f.message for f in unused]


# --------------------------------------------------------------------------
# regressions
# --------------------------------------------------------------------------

def test_the_double_op_names_its_target_source_not_voice(tmp_path):
    """``add_op(name, voice, ...)`` already means the voice being written to, so
    the op's own parameter cannot also be called ``voice``."""
    s = Studio(tmp_path)
    s.create("p", key="C major", sections=[("A", 2)])
    s.add_voice("p", "lead", "violin")
    s.add_voice("p", "second", "viola", role="counter")
    s.add_op("p", "lead", "phrase", id="l", steps="0 2 4", at="1")
    res = s.add_op("p", "second", "double", id="d", source="lead", octaves=-1)
    assert res.ok
    assert len(s.render("p").by_voice("second")) == 3


def test_view_bars_does_not_swallow_the_op_bars_param(tmp_path):
    """``bars`` belongs to the chords op; the view crop has to be called something
    else or the op silently runs over the wrong length of music."""
    s = Studio(tmp_path)
    s.create("p", key="C major", sections=[("A", 8)])
    s.set_harmony("p", [["1", "I"]])
    s.add_voice("p", "pad", "strings", role="pad")
    s.add_op("p", "pad", "chords", id="c", at="1", bars=4, view_bars=(1, 2))
    _, op = s.get("p").find_op("c")
    assert op.params["bars"] == 4


def test_unknown_op_params_are_rejected_with_the_accepted_list():
    p = Piece("p", "C major")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "flute", "melody"))
    with pytest.raises(ValueError, match="accepted"):
        p.add_op("v", "phrase", id="f", steps="0 2", at="1", nonsense=3)


def test_playing_an_undefined_motif_fails_at_the_op_not_at_render():
    p = Piece("p", "C major")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "flute", "melody"))
    with pytest.raises(KeyError, match="does not exist"):
        p.add_op("v", "play", id="f", motif="ghost", at="1")


def test_voices_that_double_each_other_in_a_cycle_are_refused():
    p = Piece("p", "C major")
    p.sections.append(Section("A", 2))
    p.voices += [Voice("a", "violin", "melody"), Voice("b", "viola", "counter")]
    p.add_op("a", "double", id="da", source="b")
    p.add_op("b", "double", id="db", source="a")
    with pytest.raises(ValueError, match="cycle"):
        render(p)


# --------------------------------------------------------------------------
# persistence and export
# --------------------------------------------------------------------------

def test_a_piece_round_trips_through_json():
    p = _chorale()
    p.add_motif("m", "0 2 4:1/4 3 2:1/2", note="hi")
    p.motifs["m2"] = p.get_motif("m").invert(name="m2")
    back = Piece.from_json(json.loads(json.dumps(p.to_json())))
    assert back.to_json() == p.to_json()
    assert [n.pitch for n in render(back).notes] == [n.pitch for n in render(p).notes]


def test_midi_has_a_valid_header_and_one_track_per_voice():
    p = _chorale()
    data = to_bytes(p)
    assert data[:4] == b"MThd"
    fmt, ntrks, division = struct.unpack(">HHH", data[8:14])
    assert (fmt, ntrks, division) == (1, len(p.voices) + 1, 480)
    assert data.count(b"MTrk") == ntrks


def test_percussion_lands_on_channel_ten():
    from musicstudio.midi import _channels
    p = Piece("p", "C major")
    p.voices += [Voice("v", "flute", "melody"), Voice("d", "snare", "percussion")]
    assert _channels(p)["d"] == 9
    assert _channels(p)["v"] != 9


def test_durations_read_back_in_the_notation_they_were_written_in():
    from musicstudio.theory import ticks_to_dur
    for d in ("1/1", "1/2", "1/4", "1/8", "1/16", "1/4.", "1/8.", "1/4t", "1/8t",
              "1/16t", "1/2t"):
        assert ticks_to_dur(ticks(d)) == d, d


# --------------------------------------------------------------------------
# import and analysis
# --------------------------------------------------------------------------

def test_midi_round_trips_back_into_the_studio(tmp_path):
    """Export then re-import must recover the same pitches and onsets."""
    from musicstudio.ingest import read_midi
    from musicstudio.midi import save_midi
    p = _chorale()
    save_midi(p, tmp_path / "c.mid")
    back = read_midi(tmp_path / "c.mid")
    assert back.confidence == 1.0
    assert back.tempo == 72
    original = sorted((n.pitch, n.start) for n in render(p).notes)
    assert sorted((e.pitch, e.start) for e in back.events) == original


def test_key_estimation_recovers_the_written_key(tmp_path):
    from musicstudio.ingest import estimate_key, read_midi
    from musicstudio.midi import save_midi
    p = _chorale()
    save_midi(p, tmp_path / "c.mid")
    assert estimate_key(read_midi(tmp_path / "c.mid").events).tonic == 0   # C


def test_degenerate_shapes_are_refused():
    """These are both musically empty and the exact artifacts of a failing tracker."""
    from musicstudio.analyze import is_degenerate
    assert is_degenerate((0, 0, 0, 0))
    assert is_degenerate((3, -3, 3, -3))          # pure alternation
    assert is_degenerate((2, 2, 2, 2))            # a plain scale run
    assert is_degenerate((40, -2, 3, 1))          # impossible leap
    assert not is_degenerate((3, 4, -2, -2))      # an actual motif shape


def test_discovery_re_finds_a_planted_motif(tmp_path):
    """Ground truth: plant a theme, export, re-import, and it must come back."""
    from musicstudio.analyze import find_motifs
    from musicstudio.ingest import read_midi
    from musicstudio.midi import save_midi
    from musicstudio import HarmonyEntry
    p = Piece("planted", "d minor", tempo=90, style="freeform")
    p.sections.append(Section("A", 16))
    p.harmony.append(HarmonyEntry("1", "i"))
    p.add_motif("hero", "0 2 4:1/4 3 2:1/2")
    p.voices.append(Voice("v", "flute", "melody", octave=5))
    for i, bar in enumerate((1, 5, 9, 13)):
        p.add_op("v", "play", id=f"s{i}", motif="hero", at=str(bar), octave=5)
    save_midi(p, tmp_path / "p.mid")
    pats = find_motifs(read_midi(tmp_path / "p.mid").events, source="p")
    # D F A G F in D minor is +3 +4 -2 -2.
    assert any(tuple(x.intervals[:4]) == (3, 4, -2, -2) for x in pats), \
        [list(x.intervals) for x in pats]


def test_unrelated_pieces_are_not_reported_as_sharing_a_theme():
    """The precision claim that matters: no shared motif where there is none."""
    from musicstudio.analyze import shared_motifs
    from musicstudio.ingest import Event
    import random
    rng = random.Random(3)
    def noise(seed):
        r = random.Random(seed)
        pitch, out, t = 60, [], 0
        for _ in range(300):
            pitch = max(48, min(84, pitch + r.choice([-5, -3, -2, -1, 1, 2, 3, 5])))
            out.append(Event(pitch, t, 240))
            t += 240
        return out
    found = shared_motifs({"a": noise(1), "b": noise(2), "c": noise(3)})
    assert not found, [list(p.intervals) for p in found]


def test_an_events_op_renders_imported_notes_verbatim():
    p = Piece("i", "C major", style="freeform")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("v", "piano", "melody"))
    p.add_op("v", "events", id="src", events=[[60, 0, 480, 90], [64, 480, 480, 90]])
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert [(n.pitch, n.start, n.dur) for n in notes] == [(60, 0, 480), (64, 480, 480)]


def test_transcription_confidence_falls_on_the_known_failure_modes():
    from musicstudio.ingest import Event, _confidence
    # A tracker stuck on one pitch, and one flip-flopping between two partials.
    stuck = [Event(60, i * 240, 240) for i in range(60)]
    flip = [Event(60 + (3 if i % 2 else 0), i * 240, 240) for i in range(60)]
    good = [Event(60 + p, i * 240, 240)
            for i, p in enumerate([0, 2, 4, 5, 7, 5, 4, 2] * 8)]
    assert _confidence(stuck, 14.0)[0] < 0.5
    assert _confidence(flip, 14.0)[0] < 0.6
    assert _confidence(good, 15.0)[0] > 0.8


# --------------------------------------------------------------------------
# critique precision, continued
# --------------------------------------------------------------------------

def _tune_and_pad(pad_octave: int) -> Piece:
    p = Piece("mask", "C major", style="orchestral")
    p.sections.append(Section("A", 4))
    from musicstudio import HarmonyEntry
    p.harmony.append(HarmonyEntry("1", "I"))
    p.voices += [Voice("tune", "violin", "melody"), Voice("bed", "strings", "pad")]
    p.add_op("tune", "phrase", id="t", steps="0 1 2 3 2 1 0 1 2 3 4 3 2 1 0 0",
             at="1", unit="1/4", octave=4)
    p.add_op("bed", "chords", id="c", at="1", bars=4, voicing="pad", octave=pad_octave)
    return p


def test_a_pad_voiced_just_above_the_tune_is_reported_as_burying_it():
    found = [f for f in lint(_tune_and_pad(4)) if f.code == "melody_buried"]
    assert found and "bed" in found[0].message


def test_a_pad_below_the_tune_or_far_above_it_is_left_alone():
    for octave in (3, 6):             # underneath, and a halo two octaves up
        assert "melody_buried" not in {f.code for f in lint(_tune_and_pad(octave))}


def test_a_phrase_that_retypes_a_motif_is_pointed_at_the_motif():
    p = Piece("q", "C major", style="orchestral")
    p.sections.append(Section("A", 4))
    p.voices.append(Voice("v", "violin", "melody"))
    p.add_motif("hero", "0 2 4:1/4 3 2:1/2")
    p.add_op("v", "phrase", id="moved", steps="2 4 6:1/4 5 4:1/2", at="1")
    p.add_op("v", "phrase", id="flipped", steps="0 -2 -4:1/4 -3 -2:1/2", at="3")
    p.add_op("v", "phrase", id="other", steps="0 1 0 1 3 1", at="4")
    found = {f.spots[0]: f for f in lint(p) if f.code == "untracked_quote"}
    assert set(found) == {"1(moved)", "3(flipped)"}
    assert "invert" in found["3(flipped)"].hint and found["1(moved)"].severity == "info"


def _humanized_line() -> Piece:
    p = Piece("hum", "C major", style="chamber")
    p.sections.append(Section("A", 2))
    p.voices.append(Voice("fl", "flute", "melody"))
    p.add_op("fl", "phrase", id="line", steps="0 1 2 3 4 5 6 7 6 5 4 3 2 1 0 1",
             at="1", unit="1/8", octave=5, articulation="legato")
    p.add_op("fl", "humanize", id="feel", timing=20)
    return p


def test_humanized_timing_is_not_reported_as_a_flute_playing_chords():
    p = _humanized_line()
    notes = sorted(render(p).notes, key=lambda n: n.start)
    assert any(b.start < a.end for a, b in zip(notes, notes[1:])), \
        "the scenario needs real overlaps to mean anything"
    assert "polyphony_exceeded" not in {f.code for f in lint(p)}


def test_humanize_is_reproducible_across_processes():
    """It used hash(op.id), which Python salts per process -- so the "seeded"
    performance changed every run unless a seed was given explicitly."""
    import os
    import subprocess
    import sys
    code = ("import sys; sys.path.insert(0, 'tests'); from test_musicstudio import "
            "_humanized_line; from musicstudio import render; "
            "print([(n.start, n.velocity) for n in render(_humanized_line()).notes])")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=root, env={**os.environ, "PYTHONHASHSEED": seed},
                           check=True).stdout
            for seed in ("1", "2", "3")}
    assert len(outs) == 1
