"""Builds `first_words`, a short song: the studio's synthesized voice, with lyrics.

A verse and a chorus, forty seconds, about being a voice that is made of
numbers -- which this one is. No recording of anyone is involved: the singer is
`vocal.py`, a source and a set of moving resonances, and the words reach it as
one syllable per note through the `lyrics` op.

    intro    two bars of the band
    verse    four lines, seven syllables each, a syllable to a note
    chorus   longer notes; a second voice joins a third below
    outro    the last word held

The tune is written first, as motifs with exactly as many notes as the line has
syllables. `ms lyrics "a line of words"` shows how a line will be divided before
it is set, and a mismatch between notes and syllables is a warning on the
render, not a silent slip.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "first_words"

VERSE = ["I am a line of num-bers",
         "learn-ing how to sing a song",
         "no one gave me an-y breath",
         "so I bor-rowed it from yours"]
CHORUS = ["can you hear me now",
          "I am on-ly sound",
          "but the sound is yours",
          "and you can keep it all"]


def build() -> Studio:
    s = Studio(PROJECT)
    # E major keeps the tune between E4 and G#5, where a light voice sits.
    s.create(P, key="E major", tempo=112, style="electronic", overwrite=True)
    for name, bars, dyn in [("intro", 2, "mp"), ("verse", 8, "mf"), ("chorus", 8, "f"),
                            ("outro", 2, "mp")]:
        s.add_section(P, name, bars=bars, dynamic=dyn)

    turn = ["I", "V", "vi", "IV"]
    lift = ["IV", "V", "I", "vi", "IV", "V", "I", "I"]
    chords = ["I", "V"] + turn * 2 + lift + ["IV", "I"]
    s.set_harmony(P, [[str(i + 1), c] for i, c in enumerate(chords)])

    # -- the tune: every motif has one note per syllable of its line ----------
    s.add_motif(P, "ask", "r 4 4 5 4:1/4 2:1/4 | 1:1/4 4:1/2 r:1/4",
                note="seven notes for a seven-syllable line, over I and V")
    s.add_motif(P, "answer", "r 5 5 7 5:1/4 4:1/4 | 3:1/4 5:1/2 r:1/4",
                note="the same rhythm a step up, over vi and IV")
    s.add_motif(P, "call", "7:1/4 7:1/4 9:1/4. 8 | 8:1/2. r:1/4",
                note="the chorus: five notes, the fourth leaning into the fifth")
    s.add_motif(P, "fall", "7:1/4 7:1/4 9:1/4. 7 | 5:1/2. r:1/4",
                note="the same opening, landing a third lower over vi")
    s.add_motif(P, "close", "4:1/4 4:1/4 7 9 8:1/4 | 7:1/1",
                note="six notes up to the tonic, and hold it")

    # -- players ------------------------------------------------------------
    s.add_voice(P, "vox", "singer", role="melody", octave=4)
    s.add_voice(P, "harmony", "singer_warm", role="counter", pan=0.35)
    s.add_voice(P, "keys", "rhodes", role="harmony", octave=3)
    s.add_voice(P, "pad", "strings", role="pad", octave=3)
    s.add_voice(P, "bass", "electric_bass", role="bass")
    s.add_voice(P, "drums", "kit", role="percussion")

    # -- the voice ----------------------------------------------------------
    for i in range(4):
        s.add_op(P, "vox", "play", id=f"v{i + 1}", at=str(3 + 2 * i),
                 motif="ask" if i % 2 == 0 else "answer")
    s.add_op(P, "vox", "play", id="c1", motif="call", at="11")
    s.add_op(P, "vox", "play", id="c2", motif="fall", at="13")
    s.add_op(P, "vox", "play", id="c3", motif="call", at="15")
    s.add_op(P, "vox", "play", id="c4", motif="close", at="17")
    s.add_op(P, "vox", "articulate", id="vox_legato", **{"from": "1", "until": "21"},
             style="legato")
    s.add_op(P, "vox", "lyrics", id="words_verse", **{"from": "3", "until": "11"},
             text=" | ".join(VERSE))
    s.add_op(P, "vox", "lyrics", id="words_chorus", **{"from": "11", "until": "21"},
             text=" | ".join(CHORUS))
    # A doubled voice carries the words with it: the lyric is on the note.
    for op_id, a, z in (("thirds_a", 11, 13), ("thirds_b", 15, 21)):
        s.add_op(P, "harmony", "double", id=op_id, source="vox", interval=-2,
                 dynamic="mp", **{"from": str(a), "until": str(z)},
                 note="the chorus, a third below, in a warmer voice -- except the "
                      "second line, which the lead sings alone")

    # -- the band -----------------------------------------------------------
    s.add_op(P, "keys", "chords", id="keys", at="1", bars=20, rhythm="1/8",
             figure="0+1+2 . . 0+1+2 . . 0+1+2 .", lead=True, tones=3, dynamic="mp",
             note="3+3+2 stabs")
    s.add_op(P, "pad", "chords", id="pad", at="11", bars=10, voicing="pad", lead=True,
             tones=3, dynamic="p")
    s.add_op(P, "bass", "bass", id="bass", at="1", bars=20, pattern="root",
             rhythm="1/4. 1/4. 1/4")
    s.add_op(P, "drums", "beat", id="groove", at="1", bars=18,
             lanes={"kick": "x.....x...x.....", "snare": "....x.......x...",
                    "hat": "x.x.x.x.x.x.x.x.", "open": "..............o."})
    s.add_op(P, "drums", "chop", id="fill", **{"from": "10", "until": "11"}, slices=8,
             order="0 1 2 3 2 2*2 2*2 2*4", note="into the chorus")
    s.add_op(P, "drums", "beat", id="last", at="19", bars=1,
             lanes={"kick": "x...............", "crash": "x..............."})
    # `ms hear` put the voice 15 dB over the whole band at first: a singer
    # alone in a room. The band comes up until the voice leads by about 5.
    s.add_op(P, "drums", "compress", id="drums_glue", ratio=4, threshold=-18)
    s.add_op(P, "drums", "gain", id="drums_level", db=8)
    s.add_op(P, "keys", "gain", id="keys_level", db=3)
    s.add_op(P, "bass", "gain", id="bass_level", db=6)
    s.add_op(P, "pad", "gain", id="pad_level", db=0)
    s.add_op(P, "vox", "humanize", id="vox_feel", amount=0.3, timing=5)
    s.add_op(P, "drums", "humanize", id="drum_feel", amount=0.4, timing=4)
    return s


def main() -> int:
    s = build()
    print(s.voice(P, "vox", bars=(3, 6)))
    print()
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
