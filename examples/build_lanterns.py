"""Builds `lanterns`, a two-minute piece for cello, violin, winds, piano and strings.

Where `build_dusk.py` shows the order of work, this one shows the reach: a long
theme built out of four cells and still tracked as one idea, a decorated repeat
that is derived rather than retyped, a counter-melody, a contrasting middle that
is a single cell sequenced, chords that are voice-led and pedalled, phrasing,
slurs and a ritardando. As in `dusk`, not one pitch is named anywhere.

    intro    piano alone; a flute foreshadows the first four notes
    A        the cello sings the theme, eight bars, over the piano
    A2       the violin takes it, ornamented; a horn answers underneath
    B        G major: a lighter cell falls in sequence through the winds
    climax   the theme in three octaves, the counter-line walking in the horn
    coda     the theme's head at half speed, its tail, and a slowing close
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "lanterns"


def build() -> Studio:
    s = Studio(PROJECT)

    # -- form ---------------------------------------------------------------
    s.create(P, key="e minor", tempo=80, style="orchestral", overwrite=True)
    for name, bars, dyn, extra in [
        ("intro", 4, "mp", {}),
        ("A", 8, "mf", {}),
        ("A2", 8, "mf", {}),
        ("B", 8, "mf", {"key": "G major"}),
        ("climax", 8, "f", {}),
        ("coda", 7, "mp", {"tempo_end": 52}),
    ]:
        s.add_section(P, name, bars=bars, dynamic=dyn, **extra)

    # -- harmony ------------------------------------------------------------
    # A and the climax share a progression; B reads against G major and ends on
    # the dominant of E minor (V7/vi), which is what turns it back home.
    period = ["i", "iv", "VII", "III", "VI", "iv", ("ii%7", "V7"), "i"]

    def bars(first: int, chords: list) -> list:
        out = []
        for k, c in enumerate(chords):
            if isinstance(c, tuple):
                out += [[f"{first + k}", c[0]], [f"{first + k}:3", c[1]]]
            else:
                out.append([f"{first + k}", c])
        return out

    s.set_harmony(P, (
        bars(1, ["i", "VI", "i", "V"])
        + bars(5, period)
        + bars(13, period[:-1] + [("i", "VII7")])
        + bars(21, ["I", "V_1", "vi", "iii", "IV", "I_1", "ii7", "V7/vi"])
        + bars(29, period)
        + bars(37, ["i", "i_1", "iv", "iv", ("ii%7", "V7"), "i", "i"])))

    # -- themes -------------------------------------------------------------
    # Four two-bar cells. Each is singable alone; joined, they are one period:
    # a question that climbs to the high G, and an answer that goes further
    # (the high A) before closing through the leading tone.
    s.add_motif(P, "call", "4:1/4. 2 4:1/4 7:1/4 | 7 6 5:1/4 3:1/4. 5",
                note="the head: a long B, down a third, then up to the tonic")
    s.add_motif(P, "rise", "6:1/4. 3 6:1/4 8:1/4 | 9:1/4 8 6 4:1/2",
                note="the same gesture a step higher, cresting on the high G")
    s.add_motif(P, "reply", "5:1/4. 4 5:1/4 7:1/4 | 10:1/4. 9 7:1/4 5:1/4",
                note="the answer starts lower and reaches the top note of the theme")
    s.add_motif(P, "close", "8:1/4 7 5 #6:1/4. 8 | 7:1/2. r:1/4",
                note="down through the leading tone to the tonic")
    s.derive_motif(P, "theme", "call", ["then:rise", "then:reply", "then:close"],
                   note="the whole eight-bar period, still traceable to its head")

    # The repeat is the same theme with the leaps walked through, a grace note
    # on each crest and a trill on the leading tone. Derived, so the motif map
    # knows it is the theme and a change to `call` changes it here too.
    s.derive_motif(P, "rise_sung", "rise", ["embellish:passing", "ornament:gr+1,-4"])
    s.derive_motif(P, "reply_sung", "reply", ["embellish:passing", "ornament:run-3,5"])
    s.derive_motif(P, "close_sung", "close", ["ornament:tr,3", "ornament:gr,0"])
    s.derive_motif(P, "theme_sung", "call",
                   ["embellish:passing", "ornament:mord,0", "then:rise_sung",
                    "then:reply_sung", "then:close_sung"],
                   note="the decorated repeat")

    s.add_motif(P, "under",
                "4:1/2 2:1/2 | 0:1/1 | -1:1/2 1:1/2 | 2:1/2. r:1/4 | "
                "0:1/2 2:1/2 | 3:1/2 0:1/2 | 1:1/2 -3:1/2 | 0:1/2 -1:1/2",
                note="the counter-line: slow, mostly falling while the theme climbs")

    s.add_motif(P, "lift", "r 4 7 9 8:1/4 7 4 | 6:1/4. 4 8:1/4 r:1/4",
                note="B's cell: an upbeat leap that leans on the ninth and lets go")
    s.derive_motif(P, "lift_echo", "lift", ["fragment:0,4", "augment:2"],
                   note="just the upbeat leap, twice as slow, for the coda")

    s.derive_motif(P, "call_wide", "call", ["augment:2"],
                   note="the head at half speed")
    s.derive_motif(P, "call_first", "call", ["fragment:0,4"],
                   note="the first four notes, as a foreshadowing")

    # -- players ------------------------------------------------------------
    s.add_voice(P, "violin", "violin", role="melody")
    s.add_voice(P, "flute", "flute", role="counter")
    s.add_voice(P, "clarinet", "clarinet", role="counter")
    s.add_voice(P, "horn", "horn", role="counter")
    s.add_voice(P, "cello", "cello", role="melody", octave=3)
    s.add_voice(P, "strings", "strings", role="pad", octave=3)
    s.add_voice(P, "pizz", "pizz_strings", role="harmony", octave=3)
    s.add_voice(P, "harp", "harp", role="ornament", octave=4)
    s.add_voice(P, "piano", "piano", role="harmony", octave=2)
    s.add_voice(P, "bass", "contrabass", role="bass")
    s.add_voice(P, "timpani", "timpani", role="percussion")
    s.add_voice(P, "cymbal", "crash", role="percussion")

    # The piano's figure throughout: root, fifth, tenth -- an open left-hand
    # arpeggio, pedalled, so it supports without crowding the tune above it.
    NOCTURNE = "0 1 2 1 3 1 2 1"

    def piano(op_id: str, at: int, n: int, **kw) -> None:
        s.add_op(P, "piano", "chords", id=op_id, at=str(at), bars=n, spread=True,
                 ring=True, **{"rhythm": "1/8", "figure": NOCTURNE, **kw})

    # -- intro: the piano alone, and four notes of what is coming -------------
    piano("i_piano", 1, 4)
    s.add_op(P, "flute", "play", id="i_hint", motif="call_first", at="3", dynamic="p",
             articulation="legato", note="the theme's first four notes, far off")

    # -- A: the cello sings the theme ----------------------------------------
    s.add_op(P, "cello", "play", id="a_theme", motif="theme", at="5", octave=3,
             articulation="legato", note="first statement, plain")
    piano("a_piano", 5, 8, dynamic="p")

    # -- A2: the violin, decorated; the cello turns into the counter-line -----
    s.add_op(P, "violin", "play", id="a2_theme", motif="theme_sung", at="13",
             articulation="legato", note="the same theme, sung rather than stated")
    s.add_op(P, "horn", "play", id="a2_under", motif="under", at="13", octave=3,
             articulation="legato", dynamic="mp",
             note="the counter-line, quietly, while the cello rests")
    piano("a2_piano", 13, 8, dynamic="p")
    s.add_op(P, "strings", "chords", id="a2_pad", at="13", bars=8, voicing="pad",
             lead=True, tones=3, dynamic="p")
    s.add_op(P, "harp", "chords", id="a2_harp", at="17", bars=4, voicing="arpeggio_updown",
             rhythm="1/8", tones=4, lead=True, ring=True, dynamic="p")
    s.add_op(P, "bass", "bass", id="a2_bass", at="13", bars=8, pattern="root",
             rhythm="1/1", dynamic="p", articulation="tenuto")

    # -- B: G major. One cell, falling in sequence, passed between the winds --
    s.add_op(P, "flute", "play", id="b_lift1", motif="lift", at="21",
             note="the new idea")
    s.add_op(P, "clarinet", "play", id="b_lift2", motif="lift", at="23", transpose=-2,
             note="a third lower, in the clarinet")
    s.add_op(P, "flute", "play", id="b_lift3", motif="lift", at="25", transpose=3,
             note="over IV, back in the flute")
    s.add_op(P, "clarinet", "double", id="b_thirds", source="flute", interval=-2,
             **{"from": "25", "until": "27"}, note="a third below, deliberately parallel")
    s.add_op(P, "violin", "phrase", id="b_turn", at="27",
             steps="1 3 5 7 8:1/4 7 5 | 6:1/4 #4:1/4 6 8 9:1/4@tr",
             articulation="legato",
             note="connective tissue: up the ii7, then the dominant of E minor, "
                  "trilling into the return")
    s.add_op(P, "violin", "dynamics", id="b_swell", **{"from": "27", "until": "29"},
             start="mp", end="f")
    s.add_op(P, "pizz", "chords", id="b_pizz", at="21", bars=8, rhythm="1/4",
             figure="0 1+2 . 1+2", lead=True, tones=3, dynamic="mp")
    s.add_op(P, "bass", "bass", id="b_bass", at="21", bars=8, pattern="root",
             rhythm="1/2", articulation="portato", dynamic="p")
    s.add_op(P, "harp", "chords", id="b_harp", at="25", bars=4, voicing="arpeggio_up",
             rhythm="1/16", tones=4, lead=True, ring=True, dynamic="p")
    s.add_op(P, "harp", "dynamics", id="b_harp_swell", **{"from": "25", "until": "29"},
             start="pp", end="mp")

    # -- climax: everything, and the theme on top of it ----------------------
    s.add_op(P, "violin", "play", id="c_theme", motif="theme", at="29", dynamic="ff",
             articulation="legato", note="the theme returns, plain again and at full voice")
    s.add_op(P, "flute", "double", id="c_octave", source="violin", octaves=1, dynamic="f",
             **{"from": "29", "until": "37"}, note="an octave above the violins")
    s.add_op(P, "cello", "double", id="c_cello", source="violin", octaves=-1,
             **{"from": "29", "until": "37"}, note="and the cellos an octave below")
    s.add_op(P, "horn", "play", id="c_under", motif="under", at="29", dynamic="f",
             octave=4, articulation="tenuto",
             transform=["fragment:0,13", "append:0:1/1", "embellish:passing"],
             note="the counter-line an octave up, walking in quarters, and "
                  "ending on the tonic this time")
    s.add_op(P, "strings", "chords", id="c_pad", at="29", bars=8, voicing="pad",
             lead=True, tones=3, octave=3, dynamic="mf")
    piano("c_piano", 29, 8, rhythm="1/16", dynamic="mf",
          figure="0 1 2 3 4 3 2 1")
    s.add_op(P, "bass", "bass", id="c_bass", at="29", bars=8, pattern="root",
             rhythm="1/2", dynamic="f", articulation="tenuto")
    s.add_op(P, "timpani", "phrase", id="c_timp1", at="28:3", unit="1/16",
             steps="-3 -3 -3 -3 -3 -3 -3! -3! | 0:1/2!!", dynamic="mf",
             note="a roll on the dominant into the downbeat")
    s.add_op(P, "timpani", "dynamics", id="c_timp_swell",
             **{"from": "28:3", "until": "29"}, start="p", end="f")
    s.add_op(P, "timpani", "phrase", id="c_timp2", at="35:3", unit="1/8",
             steps="-3 -3 -3! -3! | 0:1/2!", dynamic="f")
    s.add_op(P, "cymbal", "groove", id="c_crash", at="29", bars=1, res="1/4",
             pattern="x...", dynamic="f")

    # -- coda: the head at half speed, the tail, and the slowing -------------
    piano("z_piano", 37, 6, dynamic="p")
    s.add_op(P, "piano", "dynamics", id="z_piano_fade", **{"from": "37", "until": "43"},
             start="mp", end="pp")
    s.add_op(P, "cello", "play", id="z_wide", motif="call_wide", at="37", octave=3,
             dynamic="mp", articulation="legato",
             note="the head of the theme, augmented")
    s.add_op(P, "cello", "play", id="z_close", motif="close", at="41", octave=3,
             dynamic="p", articulation="legato", note="and its tail, to finish")
    s.add_op(P, "flute", "play", id="z_echo1", motif="lift_echo", at="38", dynamic="pp",
             articulation="legato", note="B's leap, remembered")
    s.add_op(P, "clarinet", "play", id="z_echo2", motif="lift_echo", at="40",
             transpose=-4, dynamic="pp", articulation="legato")
    s.add_op(P, "strings", "chords", id="z_pad", at="42", bars=2, voicing="pad",
             tones=3, dynamic="pp", note="under the cello's last note, not over it")
    s.add_op(P, "strings", "dynamics", id="z_fade", **{"from": "42", "until": "44"},
             start="pp", end="ppp")
    s.add_op(P, "harp", "chords", id="z_harp", at="43", bars=1, voicing="block",
             rhythm="1/1", tones=4, roll="1/16", ring=True, dynamic="p",
             note="one rolled chord to close")
    s.add_op(P, "piano", "chords", id="z_last", at="43", bars=1, voicing="block",
             rhythm="1/1", tones=3, spread=True, roll="1/16", ring=True, dynamic="pp")

    # -- performance: phrasing and a human hand, last, over everything -------
    for voice, amount in [("violin", 0.8), ("cello", 0.8), ("flute", 0.6),
                          ("clarinet", 0.6), ("horn", 0.5)]:
        s.add_op(P, voice, "shape", id=f"{voice}_shape", amount=amount)
    for voice, timing in [("violin", 9), ("cello", 9), ("flute", 8), ("clarinet", 8),
                          ("horn", 8), ("piano", 7), ("harp", 9), ("pizz", 9),
                          ("bass", 6)]:
        s.add_op(P, voice, "humanize", id=f"{voice}_human", amount=0.5, timing=timing)
    return s


def main() -> int:
    s = build()
    print(s.chart(P))
    print()
    print(s.motifs(P))
    print()
    print(s.squint(P))
    print()
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
