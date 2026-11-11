"""Builds `last_train`, a fast pop song with a sung lead: the studio taking risks.

`first_words` proved the voice worked and was otherwise as plain as a song can
be: four diatonic chords, a tune that moved by step, the same bar twice. This
one was written against a reference measured at 175 beats a minute in a bright
major key, with a bass that walks through chords from outside the key and a
vocal line where four intervals in ten are a fourth or wider. So:

    intro     a riff over I - bVII - bVI - V: two chords borrowed from the minor.
              It starts with the riff nearly alone and the band arrives in bar 3
    verse     eleven syllables to a line, in eighths; the second bar of each
              couplet climbs through V7/vi, a chord with a note outside the key
    pre       IV - V, then bVI - bVII: the tune rises by chromatic thirds and
              the drums go from quarters to a pitched roll
    chorus    IV - V - iii - vi, long notes, a tenth of range, a second voice;
              it ends on bVI - bVII, so it never lands -- the next section does
    break     the riff, stop-time
    verse 2   the same length as the first, then the pre again
    drop      the roll climbs and the band is not there: the first half of the
              chorus, quietly, over held chords. Its last bar is the dominant
              of the key a tone up, and the tune ends on that key's leading note
    chorus    the whole song a tone higher. The key change is one argument:
              nothing names a pitch, so the tune, the chords and the bass move.
    outro     the last word on the new tonic

The lead is a `singer` whose bank is a neural singer (``bank="qixuan"``, a
DiffSinger voicebank: see SINGERS.md for where it comes from and what its terms
ask -- a published render must credit "绮萱" (Qixuan) and "DiffSinger" and say
the vocal is AI-synthesized). The studio writes the notes and the syllables;
the voicebank decides how they are sung. It is not part of the studio: without
it the voice falls back to the synthesized singer, and the piece still builds.

A listening model (Gemini, given only the audio) said of the first version that
it began at full energy and never dropped, that the second verse was cut short,
that the key change was unearned, and wrote the chorus's first line down as
"hold on to the morning". That line was "don't let the mor-ning in", which put
"the" on the longest, highest note of the tune; it is now "no sun-rise not
to-night", with a stressed open vowel there. The form above is the answer to
the rest.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "last_train"

VERSE_1 = ["ne-on in the pud-dles and the last train's gone",
           "all the signs are say-ing that it won't be long",
           "pock-ets full of bat-ter-ies and bub-ble gum",
           "I can run for-ev-er on a sin-gle crumb"]
VERSE_2 = ["stat-ic on the ra-di-o a bro-ken tune",
           "sing-ing to the sat-el-lites and half a moon",
           "all the stops we nev-er made are still out there",
           "wait-ing in the dark for us with time to spare"]
PRE = ["all the win-dows are like heart-beats",
       "count-ing down and count-ing up so"]
CHORUS = ["no sun-rise not to-night",
          "not while the sky is spin-ning",
          "we are light-ning in a jar",
          "hold on hold on hold on"]
OUTRO = "hold on -"


def build() -> Studio:
    s = Studio(PROJECT)
    # A major, then B: the tune runs from B3 to E5 and, after the key change,
    # to F#5. It was first written a fourth higher and a speech recogniser
    # could not follow the chorus -- above about 700 Hz a voice has so few
    # harmonics that one vowel sounds much like another.
    s.create(P, key="A major", tempo=172, style="electronic", overwrite=True)
    for name, bars, dyn, key in [
            ("intro", 4, "f", None), ("verse", 8, "mf", None), ("pre", 4, "mf", None),
            ("chorus", 8, "ff", None), ("break", 2, "f", None), ("verse2", 8, "mf", None),
            ("pre2", 4, "mf", None), ("drop", 4, "mp", None),
            ("chorus2", 8, "ff", "B major"),
            ("outro", 4, "f", "B major"), ("ring", 1, "f", "B major")]:
        s.add_section(P, name, bars=bars, dynamic=dyn, key=key)

    riff = ["I", "bVII", "bVI", "V"]
    couplet = ["I", "V7/vi", "vi", "IV"]
    dark = ["I", "V7/vi", "vi", "iv"]                 # the minor four, borrowed
    lift = ["IV", "V", "bVI", "bVII"]
    royal = ["IV", "V", "iii", "vi"]
    chords = (riff                                    # intro     1-4
              + couplet + dark                        # verse     5-12
              + lift                                  # pre       13-16
              + royal + ["IV", "V", "bVI", "bVII"]    # chorus    17-24
              + ["I", "V"]                            # break     25-26
              + couplet + dark                        # verse2    27-34
              + lift                                  # pre2      35-38
              # The drop ends on F#7, the dominant of B: the chord that makes
              # the key change an arrival and not a gear shift.
              + ["IV", "V", "iii", "V7/ii"]           # drop      39-42
              + royal + ["IV", "V", "IV", "V"]        # chorus2   43-50 (in B)
              + ["I", "bVII", "bVI", "I"]             # outro     51-54
              + ["I"])                                # ring      55: the last hit dies away
    s.set_harmony(P, [[str(i + 1), c] for i, c in enumerate(chords)])

    # -- the tune -------------------------------------------------------------
    # Each motif has exactly as many notes as its line has syllables.
    s.add_motif(P, "line_a", "4 4 7 4 5:1/4 4 2 | 1 2 #4 6:1/4. r:1/4",
                note="eleven notes. Bar two climbs the secondary dominant, through "
                     "a note that is not in the key")
    s.add_motif(P, "line_b", "7 7 9 7 5:1/4 4 5 | 5 7 5 3:1/4. r:1/4",
                note="the answer, from the top")
    s.derive_motif(P, "line_b_dark", "line_b", ["fragment:0,7", "append:7 b5 7 3:1/4. r:1/4"],
                   note="the same answer over the borrowed minor four: one flat")
    s.add_motif(P, "climb", "3:1/4 5:1/4 7 5 7:1/4 | 8:1/4 6:1/4 4:1/2",
                note="eight notes, over IV and V")
    s.add_motif(P, "climb_out", "b5:1/4 7:1/4 b9 7 b9:1/4 | b6:1/4 8:1/4 10:1/2",
                note="the same shape a chromatic third higher, over bVI and bVII: "
                     "three notes from outside the key in two bars")
    s.add_motif(P, "shout", "7:1/4. 9 11:1/2 | 11:1/4 9:1/4 8:1/2",
                note="the chorus: up a sixth in three notes and hold the top")
    s.add_motif(P, "spin", "9:1/4 9 11 9:1/4 6:1/4 | 7:1/2 5:1/2",
                note="seven notes, falling a fifth mid-bar")
    s.derive_motif(P, "spin_turn", "spin", ["fragment:0,5", "append:9:1/2 #7:1/2"],
                   note="the drop's version: it ends on the raised note that leads "
                        "into the key a tone up")
    s.add_motif(P, "jar", "7 7 10:1/4. 9 7:1/4 | 8:1/4 11:1/2.",
                note="seven notes, ending on a leap of a fourth to the top")
    s.add_motif(P, "hold", "b9:1/4. 7:1/4. b9:1/4 | 8:1/4. 10:1/4. 8:1/4",
                note="six notes in 3+3+2 over bVI and bVII: it does not resolve")
    s.add_motif(P, "hold_home", "7:1/4. 10:1/4. 7:1/4 | 8:1/4. 11:1/4. 8:1/4",
                note="the last chorus's version, over IV and V, which does")
    s.add_motif(P, "spark", "3:3/16 4:3/16 5:1/8 4:3/16 3:3/16 2:1/8", anchor="chord",
                note="the riff: 3+3+2 in sixteenths, on chord tones so it follows "
                     "the borrowed chords without being told")

    # -- players --------------------------------------------------------------
    # Dead centre, by hand: left to the automatic seating (which spreads a
    # band like an orchestra) the lead sang from the left and the kick and bass
    # sat a little right.
    s.add_voice(P, "vox", "singer", role="melody", octave=3, bank="qixuan", pan=0.0)
    s.add_voice(P, "harmony", "singer", role="counter", pan=0.5, bank="qixuan")
    # The band is spread out: the middle is for the voice, the kick and the bass.
    s.add_voice(P, "lead", "supersaw", role="ornament", octave=3, pan=0.35)
    s.add_voice(P, "saws", "supersaw", role="pad", octave=3, pan=-0.7)
    s.add_voice(P, "saws_r", "supersaw", role="pad", octave=3, pan=0.7)
    s.add_voice(P, "keys", "piano", role="harmony", octave=3, pan=-0.3)
    s.add_voice(P, "bass", "electric_bass", role="bass", octave=1, pan=0.0)
    s.add_voice(P, "wall", "noise_wall", role="ornament", octave=4)
    s.add_voice(P, "drums", "kit_power", role="percussion", engine="soundfont", pan=0.0)
    # The sampled kit's kick is all click and room: under an eighth-note bass
    # it could not be found. A synthesized one is laid under it for the weight.
    s.add_voice(P, "thump", "kit_808", role="percussion", pan=0.0)
    # An octave under the lead in the last chorus, where the tune sits at the
    # top of the voice and comes out thin on its own.
    s.add_voice(P, "body", "singer", role="counter", pan=-0.4, bank="qixuan")

    p = s.get(P)
    add = p.add_op

    def span(a: int, z: int) -> dict:
        return {"from": str(a), "until": str(z)}

    # -- voice ----------------------------------------------------------------
    for i, m in enumerate(("line_a", "line_b", "line_a", "line_b_dark")):
        add("vox", "play", id=f"v1_{i}", motif=m, at=str(5 + 2 * i))
    add("vox", "play", id="p1_a", motif="climb", at="13")
    add("vox", "play", id="p1_b", motif="climb_out", at="15")
    for i, m in enumerate(("shout", "spin", "jar", "hold")):
        add("vox", "play", id=f"c1_{i}", motif=m, at=str(17 + 2 * i))
    for i, m in enumerate(("line_a", "line_b", "line_a", "line_b_dark")):
        add("vox", "play", id=f"v2_{i}", motif=m, at=str(27 + 2 * i))
    add("vox", "play", id="p2_a", motif="climb", at="35")
    add("vox", "play", id="p2_b", motif="climb_out", at="37")
    add("vox", "play", id="drop_0", motif="shout", at="39", dynamic="mp")
    add("vox", "play", id="drop_1", motif="spin_turn", at="41", dynamic="mp")
    for i, m in enumerate(("shout", "spin", "jar", "hold_home")):
        add("vox", "play", id=f"c2_{i}", motif=m, at=str(43 + 2 * i))
    add("vox", "phrase", id="last", at="51", steps="9:1/2 7:1/2~ | 7:1/1 | 7:1/1",
        note="the last word, on the new tonic")
    add("vox", "articulate", id="vox_legato", **span(1, 55), style="legato")
    add("vox", "lyrics", id="w_v1", **span(5, 13), text=" | ".join(VERSE_1))
    add("vox", "lyrics", id="w_p1", **span(13, 17), text=" | ".join(PRE))
    add("vox", "lyrics", id="w_c1", **span(17, 25), text=" | ".join(CHORUS))
    add("vox", "lyrics", id="w_v2", **span(27, 35), text=" | ".join(VERSE_2))
    add("vox", "lyrics", id="w_p2", **span(35, 39), text=" | ".join(PRE))
    add("vox", "lyrics", id="w_drop", **span(39, 43), text=" | ".join(CHORUS[:2]))
    add("vox", "lyrics", id="w_c2", **span(43, 51), text=" | ".join(CHORUS))
    add("vox", "lyrics", id="w_out", **span(51, 55), text=OUTRO)
    add("vox", "shape", id="vox_shape", amount=0.4)
    # A second voice a third under the two lines that stay in the key.
    # A third below a right note is not always in the chord. Twice in the
    # first line it is a semitone off one: under "-rise" (a seventh against the
    # IV chord's root, held for a beat and a half) and under "to-" (a fourth
    # against the V chord's third). There the voice drops to the chord tone
    # instead -- a fifth below, then a fourth -- and is a third again after.
    def under(op_id, start, end, interval):
        add("harmony", "double", id=op_id, source="vox", interval=interval,
            dynamic="mf", **{"from": start, "until": end})
    for op_id, a in (("h1", 17), ("h3", 43)):
        under(op_id, f"{a}", f"{a}:3", -2)
        under(op_id + "_rise", f"{a}:3", f"{a + 1}", -4)
        under(op_id + "_not", f"{a + 1}", f"{a + 1}:2", -2)
        under(op_id + "_to", f"{a + 1}:2", f"{a + 1}:3", -3)
        under(op_id + "_night", f"{a + 1}:3", f"{a + 2}", -2)
    add("body", "double", id="body_c2", source="vox", octaves=-1, dynamic="mf",
        **span(43, 51))
    for op_id, a, z in (("h2", 21, 23), ("h4", 47, 49)):
        add("harmony", "double", id=op_id, source="vox", interval=-2, dynamic="mf",
            **span(a, z))

    # -- the riff -------------------------------------------------------------
    add("lead", "play", id="riff_intro", motif="spark", at="1", times=4, every="1/1")
    add("lead", "play", id="riff_break", motif="spark", at="25", times=2, every="1/1")
    add("lead", "play", id="riff_chorus", motif="spark", at="17", times=8, every="1/1",
        dynamic="p", note="over the chorus, well back: it shares the voice's "
                          "register and was fighting it")
    add("lead", "play", id="riff_chorus2", motif="spark", at="43", times=8, every="1/1",
        dynamic="p")
    add("lead", "play", id="riff_outro", motif="spark", at="51", times=3, every="1/1")

    # -- chords ---------------------------------------------------------------
    add("keys", "chords", id="keys_verse", at="5", bars=8, rhythm="1/8", lead=True,
        tones=3, figure="0+1+2 . . 0+1+2 . . 0+1+2 .", dynamic="mf",
        note="3+3+2 stabs against the straight eighths of the tune")
    add("keys", "chords", id="keys_verse2", at="27", bars=8, rhythm="1/8", lead=True,
        tones=3, figure="0+1+2 . . 0+1+2 . . 0+1+2 .", dynamic="mf")
    add("keys", "chords", id="keys_drop", at="39", bars=4, rhythm="1/1", lead=True,
        tones=4, ring=True, dynamic="mp",
        note="one held chord a bar: all that is left under the voice")
    add("keys", "chords", id="keys_end", at="54", bars=2, rhythm="1/1", lead=True,
        tones=4, ring=True, dynamic="mf",
        note="the last chord, held and left to die away: the song used to stop "
             "as if the tape had been cut")
    for sec, first, n in (("i", 3, 2), ("p1", 13, 4), ("c1", 17, 10), ("p2", 35, 4),
                          ("c2", 43, 12)):
        add("saws", "chords", id=f"saws_{sec}", at=str(first), bars=n, rhythm="1/8",
            lead=True, tones=3, figure=". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2",
            articulation="staccato",
            note="every off-beat: the pump a side-chained pad makes")
    add("saws", "dynamics", id="saws_build1", **span(13, 17), start="mp", end="f")
    add("saws", "dynamics", id="saws_build2", **span(35, 39), start="mp", end="f")
    add("saws_r", "double", id="saws_twin", source="saws",
        note="the same chords on the other side: a second player, not an echo")

    # -- bass -----------------------------------------------------------------
    add("bass", "bass", id="bass_intro", at="3", bars=2, pattern="octaves", rhythm="1/8")
    add("bass", "bass", id="bass_verse_a", at="5", bars=4, pattern="root", rhythm="1/2",
        note="half the first verse on long roots: the band has somewhere to go")
    add("bass", "bass", id="bass_all", at="9", bars=30, pattern="octaves", rhythm="1/8",
        note="root and octave in eighths: it walks the borrowed chords for free")
    add("bass", "rest", id="bass_stop", **{"from": "26:3", "until": "27"})
    add("bass", "bass", id="bass_drop", at="39", bars=4, pattern="root", rhythm="1/1",
        dynamic="mp")
    add("bass", "bass", id="bass_end", at="43", bars=12, pattern="octaves", rhythm="1/8")

    # -- drums ----------------------------------------------------------------
    DRIVE = {"kick": "x.....x.x.......", "snare": "....x.......x..o",
             "hat": "x.x.x.x.x.x.x.x."}
    # One open hat a bar. Open on every off-beat it was a wash of noise over
    # the whole chorus, in the band the voice needs.
    FLOOR = {"kick": "x...x...x...x...", "snare": "....x.......x...",
             "open": "..............x.", "hat": "x.x.x.x.x.x.x..."}
    # Half-time under the first half-verse: the snare on three, not two and four.
    HALF = {"kick": "x.........x.....", "snare": "........x.......",
            "hat": "x.x.x.x.x.x.x.x."}
    add("drums", "beat", id="d_intro_a", at="1", bars=2,
        lanes={"hat": "x.x.x.x.x.x.x.x.", "kick": "x...............|x...........x.x."})
    add("drums", "beat", id="d_intro", at="3", bars=2, lanes={**FLOOR, "crash": "x" + "." * 31})
    add("drums", "beat", id="d_verse_a", at="5", bars=4, lanes=HALF)
    add("drums", "beat", id="d_verse", at="9", bars=4, lanes=DRIVE)
    add("drums", "beat", id="d_pre", at="13", bars=4,
        lanes={"kick": "x...x...x...x...|x...x...x...x...|x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
               "snare": "....x.......x...|....x.......x...|x.x.x.x.x.x.x.x.|xxxxxxxxxxxxxxxx"})
    add("drums", "chop", id="d_pre_climb", **span(16, 17), slices=4,
        order="0*2 1*2^0>3 2*4^3>7 3*4^7>12", note="the roll climbs into the chorus")
    add("drums", "beat", id="d_chorus", at="17", bars=8, lanes={**FLOOR, "crash": "x" + "." * 127})
    add("drums", "chop", id="d_chorus_fill", **span(24, 25), slices=8,
        order="0 1 2 3 2*2 2*2 2*4 2*4^0>7")
    add("drums", "beat", id="d_break", at="25", bars=2,
        lanes={"kick": "x.....x...x.....|x...x...........", "snare": "....x.......x...|....x...x.x.xxxx",
               "crash": "x...............|................"},
        note="stop-time: the band drops out under the riff")
    add("drums", "beat", id="d_verse2", at="27", bars=8, lanes=DRIVE)
    add("drums", "beat", id="d_pre2", at="35", bars=4,
        lanes={"kick": "x...x...x...x...|x...x...x...x...|x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
               "snare": "....x.......x...|....x.......x...|x.x.x.x.x.x.x.x.|xxxxxxxxxxxxxxxx"})
    add("drums", "chop", id="d_pre2_climb", **span(38, 39), slices=4,
        order="0*2 1*2^0>3 2*4^3>7 3*8^7>14")
    add("drums", "beat", id="d_drop", at="39", bars=4,
        lanes={"kick": "x" + "." * 47 + "x...x...x.x.x.x.",
               "crash": "x" + "." * 63,
               "snare": "." * 48 + "....x...x.x.xxxx"},
        note="one hit, three bars of nothing, and a bar to wind back up")
    add("drums", "beat", id="d_chorus2", at="43", bars=8, lanes={**FLOOR, "crash": "x" + "." * 63})
    add("drums", "chop", id="d_chorus2_fill", **span(50, 51), slices=8,
        order="0 1 2 3 2*2 2*2 2*4 2*4^0>7")
    add("drums", "beat", id="d_outro", at="51", bars=3, lanes={**FLOOR, "crash": "x" + "." * 63})
    # A roll that does not get louder is a machine: each one swells.
    for op_id, a in (("roll1", 16), ("roll2", 38), ("roll3", 42)):
        add("drums", "dynamics", id=op_id, **span(a, a + 1), start="mp", end="ff")
    for op_id, a, z in (("roll4", "24:3", "25"), ("roll5", "26:3", "27"), ("roll6", "50:3", "51")):
        add("drums", "dynamics", id=op_id, **{"from": a, "until": z}, start="mp", end="ff")
    add("drums", "beat", id="d_end", at="54", bars=1,
        lanes={"kick": "x...............", "crash": "x...............",
               "snare": "x..............."})

    # The same kicks again on the synthesized drum, wherever the kit plays a
    # plain pattern (the rolls are left to the kit alone).
    for op in list(p.get_voice("drums").ops):
        if op.kind == "beat" and "kick" in op.params["lanes"]:
            add("thump", "beat", id="t_" + op.id, at=op.params["at"],
                bars=op.params["bars"], lanes={"kick": op.params["lanes"]["kick"]})
    add("thump", "rest", id="t_roll1", **span(15, 17))
    add("thump", "rest", id="t_roll2", **span(37, 39))

    # -- risers ---------------------------------------------------------------
    for op_id, first in (("rise1", 13), ("rise2", 35)):
        add("wall", "chords", id=op_id, at=str(first), bars=4, voicing="pad", tones=2)
    add("wall", "filter", id="fx_rise1", **span(13, 17), mode="highpass", start=300,
        end=9000, resonance=0.4)
    add("wall", "filter", id="fx_rise2", **span(35, 39), mode="highpass", start=300,
        end=9000, resonance=0.4)
    add("wall", "dynamics", id="wall_swell1", **span(13, 17), start="pp", end="f")
    add("wall", "dynamics", id="wall_swell2", **span(35, 39), start="pp", end="f")
    add("wall", "chords", id="rise3", at="42", bars=1, voicing="pad", tones=2)
    add("wall", "filter", id="fx_rise3", **span(42, 43), mode="highpass", start=300,
        end=9000, resonance=0.4)
    add("wall", "dynamics", id="wall_swell3", **span(42, 43), start="pp", end="f")

    # -- sound ----------------------------------------------------------------
    add("drums", "compress", id="fx_drums", ratio=4, threshold=-18)
    add("drums", "drive", id="fx_drums_drive", amount=0.3)
    add("bass", "drive", id="fx_bass", amount=0.5)
    for side in ("saws", "saws_r"):
        add(side, "filter", id=f"fx_{side}_open1", **span(13, 17), start=600, end=6000,
            resonance=0.3, note="the chords open up through the pre-chorus")
        add(side, "filter", id=f"fx_{side}_open2", **span(35, 39), start=600, end=6000,
            resonance=0.3)
    add("vox", "compress", id="fx_vox", ratio=3, threshold=-16)
    # After the key change the tune reaches F#5 and the voice turns hard: the
    # very top is rolled off there, and the band's bright parts are kept under
    # the voice's presence range in both choruses.
    add("vox", "filter", id="fx_vox_top", **span(43, 56), start=6500, end=6500)
    add("vox", "eq", id="eq_vox_top", **span(43, 56), freq=3300, gain=-5, width=1.2,
        note="where a voice at the top of its range turns from bright to hard")
    add("harmony", "eq", id="eq_harmony", freq=3300, gain=-6, width=1.5,
        note="the same singer twice stacks the same edge: the second one gives it up")
    add("body", "eq", id="eq_body", freq=3300, gain=-6, width=1.5)
    add("keys", "eq", id="eq_keys", freq=3000, gain=-4, width=1.5,
        note="room for consonants in the verses")
    for a, z, tag in ((17, 27, "1"), (43, 56, "2")):
        for side in ("saws", "saws_r"):
            add(side, "filter", id=f"fx_{side}_dark{tag}", **span(a, z), start=2800, end=2800)
        add("lead", "filter", id=f"fx_lead_dark{tag}", **span(a, z), start=2600, end=2600)
    add("thump", "filter", id="fx_thump", start=160, end=160)
    add("thump", "gain", id="lvl_thump", db=5)
    add("body", "gain", id="lvl_body", db=-3)
    # Levels, set from `ms hear`: the first mix had the drums 8 dB over the
    # voice and the bass over it too.
    add("vox", "gain", id="lvl_vox", db=6)
    add("harmony", "gain", id="lvl_harmony", db=-2,
        note="under the lead and off to one side: at +1 and near the middle it "
             "sat in the lead's own space and masked it")
    add("drums", "gain", id="lvl_drums", db=-8)
    add("bass", "gain", id="lvl_bass", db=-7)
    add("saws", "gain", id="lvl_saws", db=-7)
    add("saws_r", "gain", id="lvl_saws_r", db=-7)
    add("lead", "gain", id="lvl_lead", db=-4)
    add("wall", "gain", id="lvl_wall", db=-6)
    add("drums", "humanize", id="feel_drums", amount=0.5, timing=4)
    add("keys", "humanize", id="feel_keys", amount=0.4, timing=5)
    s.save(p)
    # Less into the limiter than the style's default (9 dB): pushed that hard,
    # the verse came out as loud as the chorus and the drop would not drop.
    s.set_master(P, push=5)
    return s


def main() -> int:
    s = build()
    print(s.squint(P))
    print()
    r = s.render(P)
    for w in r.warnings:
        print(f"warning: {w}")
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
