"""Builds `dusk`, the gallery cue, entirely from studio ops.

Not one pitch is named anywhere in this file. Every note comes from a motif in
degree space realized against the scaffold, which is the claim the studio makes
and this script is the proof of.

Read it as a worked example of the intended order: form, then harmony, then
themes, then texture -- and only then the details.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"


def build() -> Studio:
    s = Studio(PROJECT)

    # -- form first. The cue has a shape before it has a note in it. ---------
    s.create("dusk", key="d minor", tempo=76, style="orchestral", form="cue",
             overwrite=True)
    s.update_section("dusk", "intro", dynamic="pp", note="one line, alone")
    s.update_section("dusk", "build", dynamic="mp", note="theme states, then fragments")
    s.update_section("dusk", "climax", dynamic="f", key="F major",
                     note="the relative major - the theme finally opens out")
    s.update_section("dusk", "resolve", dynamic="p", tempo=66,
                     note="augmented, and back to the dark")

    # -- then the scaffold everything is written against. -------------------
    # Bars 13-20 are in F major, so those numerals read against F.
    s.set_harmony("dusk", [
        ["1", "i"], ["3", "iv"],
        ["5", "i"], ["6", "VII"], ["7", "VI"], ["8", "iv"],
        ["9", "i"], ["9:3", "iv"], ["10", "III"], ["11", "V7"], ["12", "V7"],
        ["13", "I"], ["14", "IV"], ["15", "V"], ["16", "vi"],
        ["17", "IV"], ["18", "I_1"], ["19", "V7"], ["20", "I"],
        ["21", "i"], ["22", "iv"], ["23", "V7"], ["24", "i"],
    ])

    # -- then the themes, as objects. ---------------------------------------
    s.add_motif("dusk", "hero", "0 2 4:1/4 3 2:1/2",
                note="the main theme: rise a third, fall back and settle")
    s.add_motif("dusk", "fate", "0 -1:1/8 -3:1/4", unit="1/8",
                note="three notes falling away - the answer to hero")

    # Development is derivation, not retyping. Each of these is provably the
    # same theme, and the motif map will say so.
    s.derive_motif("dusk", "hero_climb", "hero", ["fragment:0,3", "sequence:3,1"],
                   note="the head of the theme, sequenced up a step each time")
    s.derive_motif("dusk", "hero_wide", "hero", ["augment:2"],
                   note="the theme at half speed, for the end")
    s.derive_motif("dusk", "fate_up", "fate", ["invert"],
                   note="fate turned upward - the same cell, hopeful")

    # -- then the players. --------------------------------------------------
    s.add_voice("dusk", "horn", "horn", role="melody")
    s.add_voice("dusk", "violin", "violin", role="counter")
    s.add_voice("dusk", "cello", "cello", role="bass")
    s.add_voice("dusk", "pad", "strings", role="pad", octave=3)
    s.add_voice("dusk", "harp", "harp", role="harmony")
    s.add_voice("dusk", "drum", "timpani", role="percussion")

    # -- intro: one line over a pedal. --------------------------------------
    s.add_op("dusk", "cello", "drone", id="i_pedal", at="1", bars=4, degree=0,
             dynamic="pp", note="the ground the whole cue sits on")
    s.add_op("dusk", "harp", "chords", id="i_harp", at="1", bars=4,
             voicing="arpeggio_up", rhythm="1/8", tones=3, dynamic="pp")
    s.add_op("dusk", "horn", "play", id="i_fate", motif="fate", at="3:3",
             dynamic="p", articulation="tenuto",
             note="the answering cell, before the theme it answers")

    # -- build: state the theme plainly, then take it apart. ----------------
    s.add_op("dusk", "horn", "play", id="b_theme", motif="hero", at="5",
             articulation="tenuto", note="first full statement")
    s.add_op("dusk", "horn", "play", id="b_theme2", motif="hero", at="7",
             transpose=3, note="restated a fourth higher, landing on VI's own root")
    s.add_op("dusk", "violin", "play", id="b_climb", motif="hero_climb", at="9",
             note="the head of the theme, sequenced upward into the climax")
    s.add_op("dusk", "cello", "bass", id="b_bass", at="5", bars=8, pattern="root_fifth",
             rhythm="1/4")
    s.add_op("dusk", "pad", "chords", id="b_pad", at="5", bars=8, voicing="pad", tones=3)
    s.add_op("dusk", "drum", "groove", id="b_drum", at="9", bars=4,
             pattern="x...x...x...x.xx", res="1/16", dynamic="mp")
    s.add_op("dusk", "violin", "dynamics", id="b_swell", **{"from": "9", "until": "13"},
             start="mp", end="f", note="the crescendo that carries into the climax")

    # -- climax: the same theme, in the major, with the ensemble behind it. --
    s.add_op("dusk", "horn", "play", id="c_theme", motif="hero", at="13",
             dynamic="f", articulation="marcato",
             note="the theme in the relative major, unchanged - that is the point")
    s.add_op("dusk", "violin", "double", id="c_double", source="horn", interval=2,
             **{"from": "13", "until": "17"},
             note="a third above, so the parallel motion is deliberate")
    s.add_op("dusk", "horn", "play", id="c_answer", motif="fate_up", at="17",
             dynamic="f", note="fate, inverted - the cell that fell now rises")
    s.add_op("dusk", "cello", "bass", id="c_bass", at="13", bars=8, pattern="octaves",
             rhythm="1/4", dynamic="f")
    s.add_op("dusk", "pad", "chords", id="c_pad", at="13", bars=8, voicing="pad", tones=4)
    s.add_op("dusk", "harp", "chords", id="c_harp", at="13", bars=8,
             voicing="arpeggio_up", rhythm="1/8", tones=4)
    s.add_op("dusk", "drum", "groove", id="c_drum", at="13", bars=8,
             pattern="X...x...X...x...", res="1/16", dynamic="f")

    # -- resolve: the theme at half speed, back in the dark. ----------------
    s.add_op("dusk", "horn", "play", id="r_theme", motif="hero_wide", at="21",
             dynamic="p", articulation="legato",
             note="augmented - the same shape, too slow to be triumphant")
    s.add_op("dusk", "cello", "drone", id="r_pedal", at="21", bars=4, degree=0,
             dynamic="pp")
    s.add_op("dusk", "pad", "chords", id="r_pad", at="21", bars=4, voicing="pad",
             tones=3, dynamic="pp")
    s.add_op("dusk", "harp", "play", id="r_fate", motif="fate", at="23:3", dynamic="pp",
             note="the cue ends on the cell it opened with")
    s.add_op("dusk", "pad", "dynamics", id="r_fade", **{"from": "21", "until": "25"},
             start="p", end="ppp")
    return s


def main() -> int:
    s = build()
    print(s.chart("dusk"))
    print()
    print(s.motifs("dusk"))
    print()
    print(s.squint("dusk"))
    print()
    print(report(s.lint("dusk")))
    print()
    print(f"midi: {s.export_midi('dusk')}")
    print(f"wav:  {s.export_wav('dusk')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
