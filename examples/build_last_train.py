"""Builds `last_train`, a fast pop song with a sung lead: the studio taking risks.

`first_words` proved the voice worked and was otherwise as plain as a song can
be: four diatonic chords, a tune that moved by step, the same bar twice. This
one was written against a reference measured at 175 beats a minute in a bright
major key, with a bass that walks through chords from outside the key and a
vocal line where four intervals in ten are a fourth or wider. So:

    intro     a riff over I - bVII - bVI - V: two chords borrowed from the minor
    verse     eleven syllables to a line, in eighths; the second bar of each
              couplet climbs through V7/vi, a chord with a note outside the key
    pre       IV - V, then bVI - bVII: the tune rises by chromatic thirds and
              the drums go from quarters to a pitched roll
    chorus    IV - V - iii - vi, long notes, a tenth of range, a second voice;
              it ends on bVI - bVII, so it never lands -- the next section does
    break     the riff, stop-time
    verse 2   half as long, then the pre again
    chorus    the whole song a tone higher. The key change is one argument:
              nothing names a pitch, so the tune, the chords and the bass move.
    outro     the last word on the new tonic

The lead is a `singer` whose bank is a neural singer (``bank="qixuan"``, a
DiffSinger voicebank: see SINGERS.md for where it comes from and what its terms
ask -- a published render must credit "绮萱" (Qixuan) and "DiffSinger" and say
the vocal is AI-synthesized). The studio writes the notes and the syllables;
the voicebank decides how they are sung. It is not part of the studio: without
it the voice falls back to the synthesized singer, and the piece still builds.
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
           "sing-ing to the sat-el-lites and half a moon"]
PRE = ["all the win-dows are like heart-beats",
       "count-ing down and count-ing up so"]
CHORUS = ["don't let the mor-ning in",
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
            ("chorus", 8, "ff", None), ("break", 2, "f", None), ("verse2", 4, "mf", None),
            ("pre2", 4, "mf", None), ("chorus2", 8, "ff", "B major"),
            ("outro", 4, "f", "B major")]:
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
              + dark                                  # verse2    27-30
              + lift                                  # pre2      31-34
              + royal + ["IV", "V", "IV", "V"]        # chorus2   35-42 (in E)
              + ["I", "bVII", "bVI", "I"])            # outro     43-46
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
    s.add_voice(P, "vox", "singer", role="melody", octave=3, bank="qixuan")
    s.add_voice(P, "harmony", "singer", role="counter", pan=0.3, bank="qixuan")
    s.add_voice(P, "lead", "supersaw", role="ornament", octave=3)
    s.add_voice(P, "saws", "supersaw", role="pad", octave=3)
    s.add_voice(P, "keys", "piano", role="harmony", octave=3)
    s.add_voice(P, "bass", "electric_bass", role="bass", octave=1)
    s.add_voice(P, "wall", "noise_wall", role="ornament", octave=4)
    s.add_voice(P, "drums", "kit_power", role="percussion", engine="soundfont")

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
    add("vox", "play", id="v2_0", motif="line_a", at="27")
    add("vox", "play", id="v2_1", motif="line_b_dark", at="29")
    add("vox", "play", id="p2_a", motif="climb", at="31")
    add("vox", "play", id="p2_b", motif="climb_out", at="33")
    for i, m in enumerate(("shout", "spin", "jar", "hold_home")):
        add("vox", "play", id=f"c2_{i}", motif=m, at=str(35 + 2 * i))
    add("vox", "phrase", id="last", at="43", steps="9:1/2 7:1/2~ | 7:1/1 | 7:1/1",
        note="the last word, on the new tonic")
    add("vox", "articulate", id="vox_legato", **span(1, 47), style="legato")
    add("vox", "lyrics", id="w_v1", **span(5, 13), text=" | ".join(VERSE_1))
    add("vox", "lyrics", id="w_p1", **span(13, 17), text=" | ".join(PRE))
    add("vox", "lyrics", id="w_c1", **span(17, 25), text=" | ".join(CHORUS))
    add("vox", "lyrics", id="w_v2", **span(27, 31), text=" | ".join(VERSE_2))
    add("vox", "lyrics", id="w_p2", **span(31, 35), text=" | ".join(PRE))
    add("vox", "lyrics", id="w_c2", **span(35, 43), text=" | ".join(CHORUS))
    add("vox", "lyrics", id="w_out", **span(43, 47), text=OUTRO)
    add("vox", "shape", id="vox_shape", amount=0.4)
    # A second voice a third under the two lines that stay in the key.
    for op_id, a, z in (("h1", 17, 19), ("h2", 21, 23), ("h3", 35, 37), ("h4", 39, 41)):
        add("harmony", "double", id=op_id, source="vox", interval=-2, dynamic="mf",
            **span(a, z))

    # -- the riff -------------------------------------------------------------
    add("lead", "play", id="riff_intro", motif="spark", at="1", times=4, every="1/1")
    add("lead", "play", id="riff_break", motif="spark", at="25", times=2, every="1/1")
    add("lead", "play", id="riff_chorus", motif="spark", at="17", times=8, every="1/1",
        dynamic="mp", note="over the chorus, further back")
    add("lead", "play", id="riff_chorus2", motif="spark", at="35", times=8, every="1/1",
        dynamic="mp")
    add("lead", "play", id="riff_outro", motif="spark", at="43", times=3, every="1/1")

    # -- chords ---------------------------------------------------------------
    add("keys", "chords", id="keys_verse", at="5", bars=8, rhythm="1/8", lead=True,
        tones=3, figure="0+1+2 . . 0+1+2 . . 0+1+2 .", dynamic="mf",
        note="3+3+2 stabs against the straight eighths of the tune")
    add("keys", "chords", id="keys_verse2", at="27", bars=4, rhythm="1/8", lead=True,
        tones=3, figure="0+1+2 . . 0+1+2 . . 0+1+2 .", dynamic="mf")
    for sec, first, n in (("i", 1, 4), ("p1", 13, 4), ("c1", 17, 10), ("p2", 31, 4),
                          ("c2", 35, 12)):
        add("saws", "chords", id=f"saws_{sec}", at=str(first), bars=n, rhythm="1/8",
            lead=True, tones=3, figure=". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2",
            articulation="staccato",
            note="every off-beat: the pump a side-chained pad makes")
    add("saws", "dynamics", id="saws_build1", **span(13, 17), start="mp", end="f")
    add("saws", "dynamics", id="saws_build2", **span(31, 35), start="mp", end="f")

    # -- bass -----------------------------------------------------------------
    add("bass", "bass", id="bass_all", at="1", bars=46, pattern="octaves", rhythm="1/8",
        note="root and octave in eighths: it walks the borrowed chords for free")
    add("bass", "rest", id="bass_stop", **{"from": "26:3", "until": "27"})

    # -- drums ----------------------------------------------------------------
    DRIVE = {"kick": "x.....x.x.......", "snare": "....x.......x..o",
             "hat": "x.x.x.x.x.x.x.x."}
    FLOOR = {"kick": "x...x...x...x...", "snare": "....x.......x...",
             "open": "..x...x...x...x.", "hat": "x...x...x...x..."}
    add("drums", "beat", id="d_intro", at="1", bars=4, lanes={**FLOOR, "crash": "x" + "." * 63})
    add("drums", "beat", id="d_verse", at="5", bars=8, lanes=DRIVE)
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
    add("drums", "beat", id="d_verse2", at="27", bars=4, lanes=DRIVE)
    add("drums", "beat", id="d_pre2", at="31", bars=4,
        lanes={"kick": "x...x...x...x...|x...x...x...x...|x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.x.",
               "snare": "....x.......x...|....x.......x...|x.x.x.x.x.x.x.x.|xxxxxxxxxxxxxxxx"})
    add("drums", "chop", id="d_pre2_climb", **span(34, 35), slices=4,
        order="0*2 1*2^0>3 2*4^3>7 3*8^7>14")
    add("drums", "beat", id="d_chorus2", at="35", bars=8, lanes={**FLOOR, "crash": "x" + "." * 63})
    add("drums", "chop", id="d_chorus2_fill", **span(42, 43), slices=8,
        order="0 1 2 3 2*2 2*2 2*4 2*4^0>7")
    add("drums", "beat", id="d_outro", at="43", bars=3, lanes={**FLOOR, "crash": "x" + "." * 63})
    add("drums", "beat", id="d_end", at="46", bars=1,
        lanes={"kick": "x...............", "crash": "x...............",
               "snare": "x..............."})

    # -- risers ---------------------------------------------------------------
    for op_id, first in (("rise1", 13), ("rise2", 31)):
        add("wall", "chords", id=op_id, at=str(first), bars=4, voicing="pad", tones=2)
    add("wall", "filter", id="fx_rise1", **span(13, 17), mode="highpass", start=300,
        end=9000, resonance=0.4)
    add("wall", "filter", id="fx_rise2", **span(31, 35), mode="highpass", start=300,
        end=9000, resonance=0.4)
    add("wall", "dynamics", id="wall_swell1", **span(13, 17), start="pp", end="f")
    add("wall", "dynamics", id="wall_swell2", **span(31, 35), start="pp", end="f")

    # -- sound ----------------------------------------------------------------
    add("drums", "compress", id="fx_drums", ratio=4, threshold=-18)
    add("drums", "drive", id="fx_drums_drive", amount=0.3)
    add("bass", "drive", id="fx_bass", amount=0.5)
    add("saws", "filter", id="fx_saws_open1", **span(13, 17), start=600, end=6000,
        resonance=0.3, note="the chords open up through the pre-chorus")
    add("saws", "filter", id="fx_saws_open2", **span(31, 35), start=600, end=6000,
        resonance=0.3)
    add("vox", "compress", id="fx_vox", ratio=3, threshold=-16)
    # Levels, set from `ms hear`: the first mix had the drums 8 dB over the
    # voice and the bass over it too.
    add("vox", "gain", id="lvl_vox", db=6)
    add("harmony", "gain", id="lvl_harmony", db=1)
    add("drums", "gain", id="lvl_drums", db=-8)
    add("bass", "gain", id="lvl_bass", db=-6)
    add("saws", "gain", id="lvl_saws", db=-5)
    add("lead", "gain", id="lvl_lead", db=-4)
    add("wall", "gain", id="lvl_wall", db=-6)
    add("drums", "humanize", id="feel_drums", amount=0.3, timing=3)
    add("keys", "humanize", id="feel_keys", amount=0.4, timing=5)
    s.save(p)
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
