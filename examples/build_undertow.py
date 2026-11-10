"""Builds `undertow`, a breakcore track: the studio's electronic vocabulary at work.

Where `lanterns` is a theme developed by an orchestra, this is a loop developed
by violence done to it. A dark four-bar cycle, a sub, a distorted reese, and one
drum break -- which is stated, then cut differently every few bars, then cut
differently every bar.

    intro      a hollow drone on open fifths, and a low piano tolling over it
    rise       sub and reese arrive; the drums are heard through a wall
    beat       the break at half density, ghost notes, the first cuts
    breakdown  no drums: the drone and the toll again, then a roll that climbs
    drop       the full break, a different cut every other bar
    core       every bar cut into sixteenths and re-ordered: stutters, buzz
               rolls, pitch climbs, dropouts, a four-on-the-floor kick under it
    outro      everything stops mid-phrase; sub and the opening pulse

The drums are a sampled kit (``engine="soundfont"``) played inside the built-in
render: tuned up five semitones the way a sped-up break is, then compressed
hard, driven and filtered. Without a SoundFont they fall back to the modelled
kit and the piece still builds. Nothing here names a pitch or a sample: the
break is a `beat` and every variation is a `chop` of it, so it all stays
editable -- change one lane and every cut follows.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "undertow"

# One break, two bars. Slice numbers in the cuts below are sixteenths of it:
# 0 is the kick on one, 4 and 12 are the snares, 10-11 the double kick.
BREAK = {"kick":  "x.x.......xx....|x.x.......x.....",
         "snare": "....x..o.o..x..o|....x..o.o...x.o",
         "hat":   "xoxoxoxoxoxoxoxo"}
STEADY = {"kick":  "x.....x...x.....",
          "snare": "....x..o....x..o",
          "hat":   "x.x.x.x.x.x.x.x.",
          "open":  "..............x."}

# Cuts in sixteenths. '4*2' is a 32nd retrigger of the snare, '4*4' a buzz,
# '^0>12' climbs an octave across the roll, 'r' plays the slice backwards.
CUTS = {
    "roll":    "0 1 2 3 4 5 6 7 8 9 10 11 4*2 4*2 4*4^0>7 4*4^7>12",
    "stumble": "0 0 2 3 4 . 4*2 7 0*2 0*2 10 11 12 12*2 14 12*4",
    "stutter": "0*2 . 0*2 . 4 4*2 . 4*4 8 9 4 4*2 12r 13 4*4^0>12 .",
    "snares":  "4 . 4 . 4*2 4*2 4*4 4*4^0>5 0*4 . . . 12*8^12>0 . 4 .",
    "dive":    "0 1 4*2 3 0 1 4*2 7 0*4^0>-12 . 10 11 4*2^5 4*2^7 4*4^9 4*4^12",
    "hole":    ". . . . 4 . . . 0*2 0*2 0*4 0*4 4*8^0>12 . . .",
    "ladder":  "0 4 0 4 0*2 4*2 0*2 4*2 0*4 4*4 0*4 4*4 4*4^0>4 4*4^4>8 4*4^8>12 4*4^12",
    "stop":    "0 1 2 3 4 5 6 7 . . . . 12*4 . 4*4 .",
}


def build() -> Studio:
    s = Studio(PROJECT)
    # G minor puts the tonic of the sub at G1, 49 Hz: low enough to be felt,
    # high enough that speakers can produce it. A one-word decision, because
    # nothing below names a pitch.
    s.create(P, key="g minor", tempo=112, style="electronic", overwrite=True)
    for name, bars, dyn in [("intro", 8, "p"), ("rise", 8, "mp"), ("beat", 16, "f"),
                            ("breakdown", 8, "mp"), ("drop", 16, "ff"),
                            ("core", 16, "ff"), ("outro", 6, "p")]:
        s.add_section(P, name, bars=bars, dynamic=dyn)

    # -- harmony: minor, flat second, no sevenths -----------------------------
    dark = ["i", "i", "VI", "iv"]              # Gm  Gm  Eb  Cm
    hard = ["i", "i", "bII", "i"]              # Gm  Gm  Ab  Gm: the phrygian shove
    cycle: list[str] = []
    # Open fifths to begin with: no third, so neither minor nor major yet.
    hollow = ["i5", "i5", "VI5", "iv5"]
    cycle += hollow * 2                         # intro      1-8
    cycle += hollow * 2                         # rise       9-16
    cycle += dark * 4                           # beat       17-32
    cycle += ["i", "i", "III", "III", "bII", "bII", "V", "V"]   # breakdown  33-40
    cycle += (hard + dark) * 2                  # drop       41-56
    cycle += hard * 4                           # core       57-72
    cycle += hollow + ["i5", "i5"]              # outro      73-78
    s.set_harmony(P, [[str(i + 1), c] for i, c in enumerate(cycle)])

    # -- material -----------------------------------------------------------
    s.add_motif(P, "signal", "0 2 3 2 0 2 0:1/4", anchor="chord",
                note="the pulse: root, fifth, octave in eighths. Chord tones, so "
                     "it turns with the cycle")
    s.add_motif(P, "cry", "7:1/4. b8 7:1/4 4:1/4 | 5:1/4. 4 2:1/2",
                note="the tune: the tonic, a flat second above it, and a fall "
                     "through the flat sixth")
    s.derive_motif(P, "cry_head", "cry", ["fragment:0,3", "sequence:2,2"],
                   note="just the flat-second turn, twice, climbing: all that "
                        "survives the core")
    s.add_motif(P, "toll", "4:1/1 | 5:1/2. 4:1/4 | 2:1/1 | r:1/1",
                note="the opening: the fifth held, the flat sixth leaning on it, "
                     "then down to the third -- three notes in four bars, and a "
                     "bar of nothing")
    s.add_motif(P, "pulse", "0:1/4. 0 r 0 0:1/4", anchor="chord",
                note="the bass: a long root and three short ones")
    s.derive_motif(P, "pound", "pulse", ["rhythmize:1/8 1/8 1/8 1/8 1/8 1/8 1/8 1/8"],
                   note="the same root in straight eighths, under the core")

    # -- players ------------------------------------------------------------
    s.add_voice(P, "keys", "piano", role="counter", octave=3)
    s.add_voice(P, "keys_low", "piano", role="counter")
    s.add_voice(P, "tone", "synth_lead", role="harmony", octave=3)
    s.add_voice(P, "lead", "supersaw", role="melody", octave=3)
    s.add_voice(P, "pad", "tremolo_strings", role="pad", octave=3)
    s.add_voice(P, "sub", "sub_bass", role="bass", octave=1)
    s.add_voice(P, "reese", "reese_bass", role="bass", octave=2)
    s.add_voice(P, "drums", "kit_room", role="percussion", engine="soundfont")

    def span(a: int, z: int) -> dict:
        return {"from": str(a), "until": str(z)}

    def cut(op_id: str, bar: int, name: str) -> None:
        s.add_op(P, "drums", "chop", id=op_id, **span(bar, bar + 1), slices=16,
                 order=CUTS[name], note=name)

    # -- intro: the pulse, alone, behind a filter ----------------------------
    s.add_op(P, "pad", "chords", id="i_pad", at="1", bars=8, voicing="pad", tones=3,
             dynamic="p", note="root, fifth, octave: a drone with no third in it")
    s.add_op(P, "keys", "play", id="i_toll", motif="toll", at="1", times=2,
             dynamic="mp", articulation="legato")

    s.add_op(P, "keys_low", "double", id="toll_octave", source="keys", octaves=-1,
             **span(5, 79), note="from its second statement on, an octave below too")

    # -- rise: the low end arrives; drums through a wall ---------------------
    s.add_op(P, "keys", "play", id="r_toll", motif="toll", at="9", times=2,
             dynamic="mf", articulation="legato")
    s.add_op(P, "pad", "chords", id="r_pad", at="9", bars=8, voicing="pad", tones=3,
             dynamic="p")
    s.add_op(P, "sub", "bass", id="r_sub", at="9", bars=8, pattern="pedal", dynamic="mf")
    s.add_op(P, "reese", "double", id="r_reese", source="sub", octaves=1, dynamic="mp",
             **span(9, 17))
    s.add_op(P, "drums", "beat", id="r_drums", at="13", bars=4, tune=5, lanes=STEADY,
             dynamic="mf", note="heard through the filter below, opening")
    cut("r_fill", 16, "roll")

    # -- beat: half density, ghost notes, the first cuts ---------------------
    s.add_op(P, "drums", "beat", id="b_drums", at="17", bars=16, tune=5, lanes=STEADY)
    for i, (bar, name) in enumerate([(20, "roll"), (24, "stumble"), (28, "roll"),
                                     (32, "hole")]):
        cut(f"b_cut{i + 1}", bar, name)
    s.add_op(P, "sub", "play", id="b_sub", motif="pulse", at="17", times=16,
             every="1/1", dynamic="f")
    s.add_op(P, "reese", "double", id="b_reese", source="sub", octaves=1, dynamic="mf",
             **span(17, 33))
    s.add_op(P, "keys", "play", id="b_toll", motif="toll", at="17", times=4,
             dynamic="mf", articulation="legato",
             note="the toll carries on over the beat; nothing brighter joins it")
    s.add_op(P, "pad", "chords", id="b_pad", at="17", bars=16, voicing="pad", tones=3,
             dynamic="p")

    # -- breakdown: take everything away -------------------------------------
    s.add_op(P, "pad", "chords", id="k_pad", at="33", bars=8, voicing="pad", tones=3,
             dynamic="mp")
    s.add_op(P, "pad", "dynamics", id="k_swell", **span(37, 41), start="mp", end="f")
    s.add_op(P, "keys", "play", id="k_toll", motif="toll", at="33", dynamic="mp",
             articulation="legato", transform=["invert:4"],
             note="the opening again, alone and upside down: it leans upward now")
    s.add_op(P, "lead", "phrase", id="k_hold", at="37", anchor="chord",
             steps="0:1/1~ 0:1/1 | 1:1/1~ 1:1/1", dynamic="mf", articulation="legato",
             note="one held note per chord -- the flat second, then the leading "
                  "tone -- behind a filter that opens as the roll climbs")
    s.add_op(P, "sub", "bass", id="k_sub", at="37", bars=4, pattern="pedal",
             dynamic="mf")
    s.add_op(P, "drums", "beat", id="k_roll", at="39", bars=2, tune=5,
             lanes={"snare": "x...x...x.x.x.x.|xxxxxxxxxxxxxxxx", "kick": "x.......x......."},
             note="the roll back in")
    s.add_op(P, "drums", "dynamics", id="k_roll_swell", **span(39, 41),
             start="p", end="ff")
    s.add_op(P, "drums", "chop", id="k_climb", **span(40, 41), slices=4,
             order="0*4 1*4^0>4 2*8^4>9 3*8^9>14",
             note="the last bar accelerates and climbs more than an octave")

    # -- drop: the full break, a different cut every other bar ---------------
    s.add_op(P, "drums", "beat", id="d_drums", at="41", bars=32, tune=5,
             lanes={**BREAK, "crash": "x" + "." * 127}, dynamic="ff")
    for i, (bar, name) in enumerate([(42, "stumble"), (44, "roll"), (46, "stutter"),
                                     (48, "snares"), (50, "stumble"), (52, "dive"),
                                     (54, "stutter"), (56, "stop")]):
        cut(f"d_cut{i + 1}", bar, name)
    s.add_op(P, "sub", "play", id="d_sub", motif="pulse", at="41", times=16,
             every="1/1", dynamic="ff")
    s.add_op(P, "reese", "double", id="d_reese", source="sub", octaves=1, dynamic="f",
             **span(41, 73))
    s.add_op(P, "tone", "play", id="d_signal", motif="signal", at="41", times=16,
             dynamic="mf", articulation="staccato")
    s.add_op(P, "lead", "play", id="d_cry", motif="cry", at="45", times=3,
             every="4/1", dynamic="f",
             note="on the two tonic bars of each cycle; the other two are the drums'")
    s.add_op(P, "pad", "chords", id="d_pad", at="41", bars=32, voicing="pad", tones=3,
             dynamic="mp")

    # -- core: every bar cut up ----------------------------------------------
    core = ["dive", "stutter", "stumble", "ladder", "dive", "hole", "stutter", "snares",
            "stumble", "dive", "ladder", "roll", "stutter", "hole", "ladder", "stop"]
    for i, name in enumerate(core):
        cut(f"c_cut{i + 1}", 57 + i, name)
    # Added after the cuts, so it is not cut: a kick on every beat, under them.
    s.add_op(P, "drums", "beat", id="c_stomp", at="57", bars=16, tune=0,
             lanes={"kick": "X...X...X...X..."}, dynamic="ff",
             note="four on the floor, untuned and unchopped, holding the bar "
                  "together while the break falls apart over it")
    s.add_op(P, "sub", "play", id="c_sub", motif="pound", at="57", times=16,
             every="1/1", dynamic="ff")
    s.add_op(P, "lead", "play", id="c_head", motif="cry_head", at="57", times=4,
             every="4/1", dynamic="f", octave=4)
    s.add_op(P, "tone", "play", id="c_signal", motif="signal", at="57", times=16,
             transform=["invert"], dynamic="mf", articulation="staccato", octave=4,
             note="the pulse upside down: it now falls from the root")
    s.add_op(P, "lead", "chop", id="c_glitch", **span(61, 73), slices=8,
             order="0 0*2 2 2*4 4 . 6*2 6*4^0>12 | _ _ _ _ _ _ _ _",
             note="the tune stutters too, every other bar")

    # -- outro: the floor is still there -------------------------------------
    s.add_op(P, "sub", "bass", id="o_sub", at="73", bars=6, pattern="pedal",
             dynamic="mf")
    s.add_op(P, "keys", "play", id="o_toll", motif="toll", at="73", dynamic="mp",
             articulation="legato")
    s.add_op(P, "pad", "chords", id="o_pad", at="73", bars=6, voicing="pad", tones=3,
             dynamic="pp")

    # -- sound ---------------------------------------------------------------
    # Drums: through a wall on the way in, then squashed into one slab, driven,
    # and with the top taken off -- a break is dark and dense, not crisp.
    s.add_op(P, "drums", "filter", id="fx_wall", **span(13, 17), start=220, end=7000,
             resonance=0.35)
    s.add_op(P, "drums", "filter", id="fx_dark", **span(17, 79), start=5500, end=5500)
    s.add_op(P, "drums", "compress", id="fx_slab", ratio=8, threshold=-24)
    s.add_op(P, "drums", "drive", id="fx_drums", amount=0.55)
    s.add_op(P, "drums", "crush", id="fx_grit", rate=22050, bits=12)
    s.add_op(P, "drums", "gain", id="fx_drums_level", db=-7,
             note="drive and compression made them 10 dB hotter than the bass; "
                  "`ms hear` and a stem table put them back level with it")
    # Reese: opens over the rise, then again over the drop.
    s.add_op(P, "reese", "filter", id="fx_reese_in", **span(9, 17), start=90, end=500,
             resonance=0.4)
    s.add_op(P, "reese", "filter", id="fx_reese_drop", **span(41, 49), start=200,
             end=2400, resonance=0.5)
    s.add_op(P, "reese", "drive", id="fx_growl", amount=0.85)
    s.add_op(P, "sub", "drive", id="fx_sub", amount=0.3,
             note="a little, so the sub can be found on small speakers")
    # The drone: closed at first, opening slowly through the intro and rise.
    s.add_op(P, "pad", "filter", id="fx_drone", **span(1, 17), start=300, end=2200,
             resonance=0.3)
    # The pulse in the drop: crushed and kept dark.
    s.add_op(P, "tone", "crush", id="fx_tone_grit", rate=14000, bits=9)
    s.add_op(P, "tone", "filter", id="fx_tone_dark", start=2200, end=2200)
    # The tune: an old sampler shouting.
    s.add_op(P, "lead", "filter", id="fx_lead_swell", **span(37, 41), start=250,
             end=3500, resonance=0.4, note="it opens as the roll climbs")
    s.add_op(P, "lead", "drive", id="fx_lead", amount=0.7)
    s.add_op(P, "lead", "crush", id="fx_lead_grit", rate=16000, bits=10)
    s.add_op(P, "lead", "gain", id="fx_lead_level", db=-3)
    s.add_op(P, "keys", "gain", id="fx_keys_level", db=5,
             note="played softly for the tone, then brought forward")
    s.add_op(P, "keys_low", "gain", id="fx_keys_low_level", db=3)
    s.add_op(P, "pad", "filter", id="fx_lift", **span(37, 41), mode="highpass",
             start=80, end=1200, note="the floor drops out before the drop")

    # -- feel ---------------------------------------------------------------
    s.add_op(P, "drums", "humanize", id="feel_drums", amount=0.5, timing=4)
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
