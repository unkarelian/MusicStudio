"""Builds `first_light`: a ninety-second opening theme, piano and orchestra.

Two idioms that turn out to want the same things. The Egyptian television
theme, as its best-known pianist-composer writes it: the piano is the singer,
ornamented, in a minor key that leans on the augmented second above its
dominant (hijaz) and on the flat second; the strings answer in unison; a tune
is carried down a cycle of fifths in sequence; the percussion plays maqsum
(dum tak . tak dum . tak .). And the anime opening: a slow hook alone, a riff
with the whole band, a low verse, a pre-chorus in the relative major that
builds and stops, a chorus that leaps, and the chorus again a step higher.
None of anybody's notes are here.

    solo      the piano alone, slowly: the chorus's first two bars, a turn over
              the flat second, and a trill on the dominant
    riff      everyone. Strings, piano and a plucked double in unison
    verse     the piano, low and ornamented, over pizzicato maqsum
    verse2    the same tune decorated; a cello under it, a flute on top
    pre       F major. The violins sing, the piano turns to arpeggios; it ends
              on the dominant of D minor, and the piano runs up two octaves of
              hijaz while the band holds its breath
    chorus    D minor, down the fifths: the piano's tune, the strings answering
              in the gaps and joining for the climb
    chorus2   E minor: the tune in three octaves, the horn walking up under
              it, the flat second where the half-diminished chord was
    outro     the riff, in the new key, and one last note
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "first_light"

SECTIONS = [("solo", 4, "mp", {"tempo": 92, "tempo_end": 70}),
            ("riff", 4, "f", {}),
            ("verse", 8, "mf", {}),
            ("verse2", 8, "mf", {}),
            ("pre", 8, "mp", {"key": "F major"}),
            ("chorus", 8, "ff", {}),
            ("chorus2", 8, "ff", {"key": "E minor"}),
            ("outro", 5, "ff", {"key": "E minor"})]
START, _bar = {}, 1
for _name, _bars, _, _ in SECTIONS:
    START[_name] = _bar
    _bar += _bars
LENGTH = {name: bars for name, bars, _, _ in SECTIONS}

CHORDS = {
    "solo": ["i", "iv", "bII", "V7"],
    "riff": ["i", "VI", "bII", "V7"],
    "verse": ["i", "VI", "iv", "V7", "i", "VII", "bII", "V7"],
    "verse2": ["i", "VI", "iv", "V7", "i", "VII", "VI", "V7/III"],
    # The royal road, and then the chord that does not belong to F at all.
    "pre": ["IVmaj7", "V", "iii7", "vi", "IVmaj7", "V", "V7/vi", "V7/vi"],
    "chorus": ["i", "iv7", "VII7", "IIImaj7", "VImaj7", "ii%7", "V7", ("i", "V7/ii")],
    "chorus2": ["i", "iv7", "VII7", "IIImaj7", "VImaj7", "bII", "V7", "i"],
    "outro": ["i", "VI", "bII", "V7", "i"],
}


def at(section: str, bar: int = 1, beat: float | None = None) -> str:
    n = START[section] + bar - 1
    return f"{n}:{beat:g}" if beat else str(n)


def span(section: str, first: int = 1, last: int | None = None) -> dict:
    last = LENGTH[section] if last is None else last
    return {"from": at(section, first), "until": str(START[section] + last)}


def build() -> Studio:
    s = Studio(PROJECT)
    s.create(P, key="D minor", tempo=156, style="orchestral", overwrite=True)
    for name, bars, dyn, extra in SECTIONS:
        s.add_section(P, name, bars=bars, dynamic=dyn, **extra)
    harmony = []
    for name, _, _, _ in SECTIONS:
        for i, chord in enumerate(CHORDS[name]):
            if isinstance(chord, tuple):
                harmony += [[at(name, i + 1), chord[0]], [at(name, i + 1, 3), chord[1]]]
            else:
                harmony.append([at(name, i + 1), chord])
    s.set_harmony(P, harmony)

    # -- the chorus -----------------------------------------------------------
    s.add_motif(P, "soar", "4:1/4. 9:1/4. 8:1/4 | 7:1/4. 5 7:1/2",
                note="up a sixth off the fifth, in three-three-two; then it "
                     "waits, and the wait is where the strings answer")
    s.add_motif(P, "climb", "2 5 7 9:1/4. 10:1/4~ | 10:1/4. 9 8:1/4 7:1/4",
                note="up the sixth chord to the top of the tune, held across "
                     "the barline")
    s.add_motif(P, "hijaz", "#6:1/4.@tr 5 4:1/4 #6:1/4 | 7:1/2. r:1/4",
                note="the cadence: leading note, flat sixth, fifth -- the "
                     "augmented second -- and home")
    s.derive_motif(P, "climb_neap", "climb",
                   ["fragment:0,7", "append:b8:1/4 7:1/4"],
                   note="the climb over the flat second: one note bends")
    s.derive_motif(P, "hijaz_last", "hijaz", ["fragment:0,4", "append:7:1/1"],
                   note="the cadence with nothing after it")
    s.derive_motif(P, "sabi", "soar", ["sequence:2,-1", "then:climb", "then:hijaz"],
                   note="the chorus, eight bars: the cell twice, a step lower "
                        "the second time, down the fifths; the climb; the cadence")
    s.derive_motif(P, "sabi_up", "soar",
                   ["sequence:2,-1", "then:climb_neap", "then:hijaz_last"],
                   note="the chorus as it goes the second time")
    s.add_motif(P, "taqsim",
                "b8:1/4.@gr+1 7 5:1/4 3:1/4 | 4:1/4@gr 5 #6 4:1/2@tr",
                note="the solo's own two bars: down the flat-second chord, then "
                     "a turn through the augmented second onto a trill")
    s.derive_motif(P, "prelude", "soar", ["then:taqsim"],
                   note="the chorus's head, and where the solo takes it instead")

    # -- the riff -------------------------------------------------------------
    s.add_motif(P, "riff_a", "7! 7 4 7 8! 7 5 4 | 5:1/4.! 7:1/4.! 9:1/4!",
                note="a bar of eighths around the tonic, a bar of three-three-two")
    s.add_motif(P, "riff_b", "b8! b8 5 b8 9! b8 7 5 | 4:1/4.! #6:1/4.! 8:1/4!",
                note="the same on the flat second, then up the dominant")
    s.derive_motif(P, "riff", "riff_a", ["then:riff_b"])
    s.derive_motif(P, "riff_end", "riff", ["append:7:1/4!!"],
                   note="the riff and its last note")

    # -- the verse ------------------------------------------------------------
    s.add_motif(P, "ask", "r 0 1 2 4:1/4@mord 3 2 | 2:1/4. 1 0:1/4 r:1/4",
                note="enters off the beat, climbs a fifth, bites, comes back")
    s.add_motif(P, "ask_2", "r 0 2 3 5:1/4@mord 4 3 | 4:1/4. 5 #6:1/4 4:1/4",
                note="a step further, and out through the augmented second")
    s.add_motif(P, "reach", "r 4 5 7 9:1/4@gr 8 7 | 8:1/4. 7 6:1/2",
                note="the same entry a fifth up: the verse's high point")
    s.add_motif(P, "turn_home", "r b8 7 5 3:1/4 5 b8 | 7:1/4 #6:1/4.@mord 5 4:1/4",
                note="down and up the flat-second chord, to the dominant")
    s.add_motif(P, "turn_away", "r 9 7 5 2:1/4 5 7 | 8:1/4 6:1/4 8:1/4 10:1/4",
                note="verse two's ending: it does not go home, it climbs the "
                     "dominant of the relative major")
    s.derive_motif(P, "verse", "ask", ["then:ask_2", "then:reach", "then:turn_home"])
    s.derive_motif(P, "ask_2_sung", "ask_2", ["embellish:neighbor,1 2", "ornament:tr,-1"])
    s.derive_motif(P, "reach_sung", "reach", ["ornament:run-3,1", "ornament:mord,-1"])
    s.derive_motif(P, "verse_sung", "ask",
                   ["embellish:passing", "ornament:gr,1", "then:ask_2_sung", "then:reach_sung", "then:turn_away"],
                   note="the verse decorated, with the other ending")

    # -- the pre-chorus (read against F major) --------------------------------
    s.add_motif(P, "long_1", "2:1/2 3:1/4 5:1/4 | 4:1/2. 3 4 | "
                             "4:1/2 6:1/4 8:1/4 | 7:1/2. 5:1/4",
                note="long notes that keep rising: everything the verse was not")
    s.add_motif(P, "long_2", "5:1/2 7:1/4 9:1/4 | 8:1/2. 9 8 | 9:1/1~ | 9:1/1",
                note="higher, and then it stays on one note for two bars while "
                     "the chord under it turns into D minor's dominant")
    s.derive_motif(P, "bridge", "long_1", ["then:long_2"])
    s.add_motif(P, "run", "2 3 #4 5 6 7 8 9 10 #11 12 13 14 15 16:1/8!", unit="1/16",
                note="two octaves of hijaz, from the dominant to the dominant")

    # -- under the tune -------------------------------------------------------
    s.add_motif(P, "under", "4:1/1 | 5:1/1 | 5:1/2 6:1/2 | 6:1/2. r:1/4 | "
                            "7:1/1 | 8:1/1 | 8:1/1 | 7:1/1",
                note="the counter-line: it only ever goes up, a step at a time, "
                     "while the tune falls in sequence")
    s.derive_motif(P, "under_neap", "under",
                   ["fragment:0,7", "append:b8:1/1 | 8:1/1 | 7:1/2. r:1/4"],
                   note="through the flat second")
    s.add_motif(P, "answer", "7 8 9 10 11 10 9 8", unit="1/16",
                note="the strings' reply in the tune's gap: up a fifth and back")
    s.add_motif(P, "reply", "7 8 9 8 7 5 4:1/8", unit="1/16",
                note="the strings in the verse's gaps: a turn and a fall, in unison")
    s.add_motif(P, "pivot", "#5! #7! #9! 11!",
                note="up the dominant seventh of the key a step above: four "
                     "notes that are not in D minor, and then it is E minor")
    s.add_motif(P, "thrum", "0:1/4. 0 r 2 0:1/4", anchor="chord",
                note="the bass under the verse, on the dums of the maqsum")
    s.add_motif(P, "sigh", "4:1/1 | 5:1/2. 4:1/4 | 3:1/1 | 4:1/2 #6:1/2 | "
                           "4:1/1 | 3:1/2. 4:1/4 | 5:1/1 | 6:1/2 8:1/2",
                note="the cello under verse two")

    # -- players --------------------------------------------------------------
    s.add_voice(P, "piano", "piano", role="melody", octave=4, pan=0.0)
    s.add_voice(P, "piano_top", "piano", role="ornament", octave=5, pan=0.05)
    s.add_voice(P, "hands", "piano", role="harmony", octave=3, pan=-0.05)
    s.add_voice(P, "violins", "strings", role="counter", octave=5, pan=-0.35)
    s.add_voice(P, "flute", "flute", role="ornament", pan=0.3)
    s.add_voice(P, "horn", "horn", role="counter", pan=0.2)
    s.add_voice(P, "cello", "cello", role="counter", octave=3, pan=0.3)
    s.add_voice(P, "pad", "strings", role="pad", octave=3, pan=0.1)
    s.add_voice(P, "pizz", "pizz_strings", role="harmony", octave=3, pan=-0.2)
    s.add_voice(P, "qanun", "harpsichord", role="ornament", octave=4, pan=0.4)
    s.add_voice(P, "bass", "electric_bass", role="bass", pan=0.0)
    s.add_voice(P, "timpani", "timpani", role="percussion", pan=-0.1)
    s.add_voice(P, "drums", "kit_room", role="percussion", pan=0.0)

    p = s.get(P)
    add = p.add_op

    MAQSUM = {"kick": "X.......x.......", "tom_lo": "X.......x.......",
              "rim": "..x...x.....x...", "tamb": "x.xox.x.x.xox.x."}
    DRIVE = {"kick": "x.......x.x.....", "snare": "....x.......x...",
             "hat": "x.o.x.o.x.o.x.o.", "tamb": "..x...x.....x..."}
    FILL = {"kick": "x.......x.......", "snare": "....x.....x.xxxx",
            "tom_hi": "........xx......", "tom_mid": "..........x.....",
            "hat": "x.x.x.x........."}
    HITS = {"kick": "x.x.....x.......|x.....x.....x...",
            "snare": "....x.......x...|x.....x.....x...",
            "hat": "x.x.x.x.x.x.x.x.|................",
            "crash": "x...............|................"}

    def drums(op_id, where, bars, lanes, **kw):
        add("drums", "beat", id=op_id, at=where, bars=bars, lanes=lanes, **kw)

    def nocturne(op_id, where, bars, **kw):
        add("hands", "chords", id=op_id, at=where, bars=bars, spread=True, ring=True,
            lead=True, **{"rhythm": "1/8", "figure": "0 1 2 1 3 1 2 1", **kw})

    def stabs(op_id, where, bars, **kw):
        add("hands", "chords", id=op_id, at=where, bars=bars, tones=3, lead=True, octave=4,
            rhythm="1/8", figure="0+1+2 . . 0+1+2 . . 0+1+2 .",
            articulation="marcato", **kw)

    # -- solo -----------------------------------------------------------------
    add("piano", "play", id="solo_tune", motif="prelude", at=at("solo"), octave=4,
        articulation="legato", note="the hook, alone, before anything has a pulse")
    add("hands", "chords", id="solo_hands", at=at("solo"), bars=4, voicing="block",
        rhythm="1/1", tones=4, spread=True, roll="1/16", ring=True, dynamic="p")
    add("piano", "dynamics", id="solo_fade", **span("solo", 3, 4), start="mf", end="p")

    add("timpani", "phrase", id="solo_roll", at=at("solo", 4, 3), unit="1/16",
        steps="-3 -3 -3 -3 -3 -3! -3! -3!", dynamic="mf",
        note="under the trill: the first sign that this is not a nocturne")
    add("timpani", "dynamics", id="solo_roll_swell",
        **{"from": at("solo", 4, 3), "until": at("riff")}, start="pp", end="f")
    drums("solo_pickup", at("solo", 4), 1, {"snare": "............o.xx",
                                           "tom_mid": "..........o.....",
                                           "tom_lo": "........o......."})

    # -- riff -----------------------------------------------------------------
    add("violins", "play", id="riff_vln", motif="riff", at=at("riff"), octave=4,
        articulation="marcato")
    add("piano", "play", id="riff_pno", motif="riff", at=at("riff"), octave=4,
        articulation="marcato", dynamic="f")
    add("piano_top", "double", id="riff_top", source="piano", octaves=1, **span("riff"))
    add("qanun", "double", id="riff_qanun", source="violins", octaves=1, dynamic="mf",
        **span("riff"))
    add("cello", "double", id="riff_cello", source="violins", octaves=-1, **span("riff"))
    add("bass", "bass", id="riff_bass", at=at("riff"), bars=4, pattern="root",
        rhythm="1/8", dynamic="f", octave=2)
    drums("riff_d", at("riff"), 4, HITS)
    add("timpani", "phrase", id="riff_timp", at=at("riff"), steps="0:1/4!! r:1/4 r:1/2",
        dynamic="f")

    # -- verse ----------------------------------------------------------------
    add("piano", "play", id="v_tune", motif="verse", at=at("verse"), octave=4, dynamic="f",
        note="the tune, plainly")
    add("pizz", "chords", id="v_pizz", at=at("verse"), bars=8, rhythm="1/8", tones=3,
        lead=True, figure="0 1+2 . 1+2 0 . 1+2 .", dynamic="p",
        note="maqsum in the strings: the low note on the dums, the chord on the taks")
    add("bass", "play", id="v_bass", motif="thrum", at=at("verse"), times=8, every="1",
        dynamic="mf", octave=2)
    drums("v_d", at("verse"), 7, MAQSUM, dynamic="mp")
    add("violins", "play", id="v_reply1", motif="reply", at=at("verse", 2, 3), octave=4,
        dynamic="mf", note="the strings answer the piano, as they do in this music")
    add("violins", "play", id="v_reply2", motif="reply", at=at("verse", 6, 3), octave=4,
        transpose=1, dynamic="mf")
    add("qanun", "double", id="v_reply_q", source="violins", dynamic="pp", **span("verse"))
    drums("v_d_end", at("verse", 8), 1,
          {"kick": "x.......x.......", "tom_lo": "x.......x.......", "rim": "..x...x.....x.xx",
           "tamb": "x.xxx.x.x.xxxxxx"})

    # -- verse 2 --------------------------------------------------------------
    add("piano", "play", id="v2_tune", motif="verse_sung", at=at("verse2"), octave=4, dynamic="f",
        note="decorated, and it ends by climbing away")
    add("piano_top", "double", id="v2_top", source="piano", octaves=1, dynamic="mp",
        **span("verse2", 5, 8), note="octaves for the second half")
    add("flute", "double", id="v2_flute", source="piano", octaves=1, dynamic="pp",
        **span("verse2", 5, 8))
    add("cello", "play", id="v2_cello", motif="sigh", at=at("verse2"), octave=3,
        articulation="legato", dynamic="p")
    add("pad", "chords", id="v2_pad", at=at("verse2"), bars=8, voicing="pad", lead=True,
        tones=3, dynamic="pp")
    add("pizz", "chords", id="v2_pizz", at=at("verse2"), bars=8, rhythm="1/8", tones=3,
        lead=True, figure="0 1+2 . 1+2 0 . 1+2 .", dynamic="p")
    add("bass", "play", id="v2_bass", motif="thrum", at=at("verse2"), times=8, every="1",
        dynamic="mf", octave=2)
    drums("v2_d", at("verse2"), 7, {**MAQSUM, "hat": "..x...x...x...x."}, dynamic="mp")
    drums("v2_fill", at("verse2", 8), 1, FILL)

    # -- pre ------------------------------------------------------------------
    add("violins", "play", id="pre_tune", motif="bridge", at=at("pre"), octave=4,
        articulation="legato", dynamic="f")
    add("violins", "dynamics", id="pre_swell", **span("pre", 5, 8), start="f", end="fff")
    nocturne("pre_hands", at("pre"), 7, dynamic="pp")
    add("piano", "chords", id="pre_sparkle", at=at("pre", 5), bars=3,
        voicing="arpeggio_updown", rhythm="1/16", tones=4, lead=True, octave=5,
        dynamic="p", note="the piano stops singing and glitters")
    add("piano", "dynamics", id="pre_sparkle_swell", **span("pre", 5, 7),
        start="pp", end="mp")
    add("piano", "play", id="pre_run", motif="run", at=at("pre", 8), octave=3,
        dynamic="f", note="alone but for a held note and a snare")
    add("piano", "dynamics", id="pre_run_swell", **span("pre", 8, 8), start="mf", end="ff")
    add("piano_top", "double", id="pre_run_top", source="piano", octaves=1, **span("pre", 8, 8))
    add("qanun", "double", id="pre_run_q", source="piano", octaves=0, dynamic="mf",
        **span("pre", 8, 8))
    add("cello", "double", id="pre_run_vc", source="piano", octaves=0, dynamic="mf",
        **span("pre", 8, 8), note="the run is the orchestra's, not one hand's")
    add("cello", "phrase", id="pre_cello", at=at("pre"), articulation="legato",
        dynamic="mp", octave=3,
        steps="3:1/1 | 4:1/1 | 2:1/1 | 5:1/1 | 3:1/1 | 4:1/1 | 2:1/1",
        note="the roots, sung")
    add("bass", "bass", id="pre_bass", at=at("pre", 5), bars=3, pattern="root",
        rhythm="1/2", dynamic="mp", articulation="tenuto", octave=2)
    add("pad", "chords", id="pre_pad", at=at("pre"), bars=7, voicing="pad", lead=True,
        tones=4, dynamic="p")
    add("pad", "dynamics", id="pre_pad_swell", **span("pre", 5, 7), start="p", end="mf")
    drums("pre_d_a", at("pre"), 4, {"hat": "x.x.x.x.x.x.x.x.", "rim": "....x.......x...",
                                   "tamb": "..............x."}, dynamic="p")
    drums("pre_d_b", at("pre", 5), 3,
          {"kick": "x...x...x...x...", "hat": "x.x.x.x.x.x.x.x.",
           "snare": "................|....x.......x...|x.x.x.x.x.x.xxxx"})
    drums("pre_d_roll", at("pre", 8), 1, {"snare": "x.x.x.x.xxxxxxxx", "kick": "x..............."})
    add("drums", "dynamics", id="pre_d_swell", **span("pre", 5, 8), start="mp", end="ff")
    add("timpani", "phrase", id="pre_timp", at=at("pre", 8, 3), unit="1/16",
        steps="-3 -3 -3 -3 -3! -3! -3! -3!", dynamic="mf",
        note="a roll on A, which is the fifth of the key that is about to arrive")

    # -- chorus ---------------------------------------------------------------
    add("piano", "play", id="c_tune", motif="sabi", at=at("chorus"), octave=4,
        dynamic="ff", note="the tune the solo promised")
    add("piano", "rest", id="c_gap", **{"from": at("chorus", 8, 3), "until": at("chorus2")})
    add("piano", "play", id="c_pivot", motif="pivot", at=at("chorus", 8, 3), octave=4,
        articulation="marcato", dynamic="ff", note="the key change, announced")
    add("piano_top", "double", id="c_top", source="piano", octaves=1, **span("chorus"))
    add("violins", "play", id="c_ans1", motif="answer", at=at("chorus", 2, 3), octave=4,
        dynamic="mf", note="in the first gap")
    add("violins", "play", id="c_ans2", motif="answer", at=at("chorus", 4, 3), octave=4,
        transpose=-1, dynamic="mf", note="and the second, a step lower like the tune")
    add("violins", "double", id="c_vln", source="piano", octaves=0, dynamic="mf",
        **span("chorus", 5, 8), note="the strings stop answering and join")
    add("cello", "play", id="c_under", motif="under", at=at("chorus"), octave=3,
        articulation="tenuto", dynamic="mp")
    add("pad", "chords", id="c_pad", at=at("chorus"), bars=8, voicing="pad", lead=True,
        tones=4, octave=4, dynamic="p")
    stabs("c_hands", at("chorus"), 8, dynamic="p")
    add("bass", "bass", id="c_bass", at=at("chorus"), bars=8, pattern="root",
        rhythm="1/8", dynamic="f", octave=2)
    drums("c_d", at("chorus"), 7, {**DRIVE, "crash": "x..............." + "." * 16 * 6})
    drums("c_fill", at("chorus", 8), 1, FILL)
    add("timpani", "phrase", id="c_timp", at=at("chorus"), steps="0:1/4!! r:1/4 r:1/2",
        dynamic="f")

    # -- chorus 2 -------------------------------------------------------------
    add("piano", "play", id="c2_tune", motif="sabi_up", at=at("chorus2"), octave=4,
        dynamic="ff", note="a whole step up")
    add("piano_top", "double", id="c2_top", source="piano", octaves=1, **span("chorus2"))
    add("violins", "double", id="c2_vln", source="piano", octaves=1, dynamic="mf",
        **span("chorus2"), note="the tune in the strings from the first note")
    add("flute", "double", id="c2_flute", source="piano", octaves=1, dynamic="pp",
        **span("chorus2"))
    add("horn", "play", id="c2_under", motif="under_neap", at=at("chorus2"),
        articulation="tenuto", dynamic="mf", note="the counter-line, in brass now")
    add("cello", "double", id="c2_cello", source="horn", octaves=-1, **span("chorus2"))
    add("qanun", "chords", id="c2_qanun", at=at("chorus2"), bars=8, voicing="arpeggio_up",
        rhythm="1/16", tones=4, lead=True, octave=4, dynamic="pp",
        note="a tremolo of plucks behind everything")
    add("pad", "chords", id="c2_pad", at=at("chorus2"), bars=8, voicing="pad", lead=True,
        tones=4, octave=4, dynamic="p")
    stabs("c2_hands", at("chorus2"), 8, dynamic="p")
    add("bass", "bass", id="c2_bass", at=at("chorus2"), bars=8, pattern="octaves",
        rhythm="1/8", dynamic="f", octave=2)
    drums("c2_d", at("chorus2"), 7, {**DRIVE, "kick": "x.....x.x.x.....",
                                    "crash": "x..............." + "." * 16 * 3})
    drums("c2_fill", at("chorus2", 8), 1, FILL)
    add("timpani", "phrase", id="c2_timp", at=at("chorus2"), steps="0:1/4!! r:1/4 r:1/2",
        dynamic="f")

    # -- outro ----------------------------------------------------------------
    add("violins", "play", id="o_vln", motif="riff_end", at=at("outro"), octave=4,
        articulation="marcato", dynamic="ff")
    add("piano", "play", id="o_pno", motif="riff_end", at=at("outro"), octave=4,
        articulation="marcato", dynamic="ff")
    add("piano_top", "double", id="o_top", source="piano", octaves=1, **span("outro"))
    add("qanun", "double", id="o_qanun", source="violins", octaves=0, dynamic="mf",
        **span("outro"))
    add("cello", "double", id="o_cello", source="violins", octaves=-1, **span("outro"))
    add("bass", "bass", id="o_bass", at=at("outro"), bars=4, pattern="root",
        rhythm="1/8", dynamic="f", octave=2)
    add("bass", "phrase", id="o_bass_end", at=at("outro", 5), steps="0:1/4!!", dynamic="ff", octave=2)
    drums("o_d", at("outro"), 4, HITS)
    drums("o_d_end", at("outro", 5), 1, {"kick": "x...............",
                                        "snare": "x...............",
                                        "crash": "x..............."})
    add("timpani", "phrase", id="o_timp", at=at("outro", 4, 3), unit="1/16",
        steps="-3 -3 -3 -3 -3! -3! -3! -3! | 0:1/4!!", dynamic="f")

    # -- performance ----------------------------------------------------------
    for voice, amount in [("piano", 0.6), ("violins", 0.7), ("cello", 0.7),
                          ("horn", 0.5), ("flute", 0.5)]:
        add(voice, "shape", id=f"{voice}_shape", amount=amount)
    for voice, timing in [("piano", 6), ("piano_top", 6), ("hands", 6), ("violins", 8),
                          ("cello", 8), ("horn", 8), ("flute", 7), ("pizz", 7),
                          ("qanun", 6), ("bass", 4), ("drums", 4)]:
        add(voice, "humanize", id=f"{voice}_human", amount=0.4, timing=timing)
    add("drums", "eq", id="eq_drums", freq=8000, gain=-5, width=2.0,
        note="the cymbals were washing over the snare")
    add("drums", "gain", id="lvl_drums", db=3)
    add("bass", "gain", id="lvl_bass", db=6)
    add("pad", "eq", id="eq_pad", freq=1200, gain=-4, width=1.5,
        note="room in the middle for the tune")
    s.save(p)

    s.set_master(P, room={"decay": 1.8, "wet": 0.16})
    return s


def main() -> int:
    s = build()
    print(s.chart(P))
    print()
    print(s.motifs(P))
    print()
    print(s.squint(P))
    print()
    for w in s.render(P).warnings:
        print(f"warning: {w}")
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    if "--no-wav" not in sys.argv:
        print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
