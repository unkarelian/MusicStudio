"""Builds `nightshade`: acid / dark trance.

142 beats a minute in G minor, on the `acid_bass` model -- one saw through a
resonant filter that every note re-opens. The same instrument plays both low
parts: struck softly it is the rolling bass in the gaps the kick leaves, and
struck hard it is the line on top. Its velocity is its cutoff knob, so every
build in this piece is a `dynamics` op on the acid voice, not a new sound.

    intro    kick, and the acid line nearly shut
    rise     the bass rolls in; the line opens bar by bar; the kick is taken
             away for the last bar
    drop     everything. Sixteen bars on the tonic and its flat second, then
             sixteen where the harmony starts to move and the hook's first
             bar is heard twice, far back
    break    no drums. The hook, whole, over a choir; the acid line climbs
             under it from a whisper; a roll; half a bar of the line alone
    drop2    the hook on a wall of saws over the full machine
    lift     the same thing a minor third up, in Bb minor, with a second
             acid line -- the square wave -- answering the first backwards
    outro    the filter closes

The acid line is written in *chord tones* (anchor="chord"): 0 the root, 1 the
third, 2 the fifth, 3 the octave. So it is one two-bar pattern for the whole
piece, and it re-seats itself on the flat second, the sixth and the dominant
without a note being retyped.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "nightshade"

SECTIONS = [("intro", 16, "mp", None), ("rise", 16, "mf", None),
            ("drop", 32, "f", None), ("break", 24, "mp", None),
            ("drop2", 16, "ff", None), ("lift", 16, "ff", "bb minor"),
            ("outro", 16, "mf", "bb minor")]
FIRST = {}
_bar = 1
for _name, _bars, _dyn, _key in SECTIONS:
    FIRST[_name] = _bar
    _bar += _bars
LAST_BAR = _bar - 1

PEDAL = ["i", "i", "i", "i", "i", "i", "bII", "bII"]       # Gm ...... Ab Ab
TURN = ["i", "i", "VI", "VI", "iv", "iv", "bII", "V"]      # Gm Eb Cm Ab D


def span(a: int, z: int) -> dict:
    return {"from": str(a), "until": str(z)}


def build() -> Studio:
    s = Studio(PROJECT)
    s.create(P, key="g minor", tempo=142, style="electronic", overwrite=True)
    for name, bars, dyn, key in SECTIONS:
        s.add_section(P, name, bars=bars, dynamic=dyn, **({"key": key} if key else {}))

    cycle = PEDAL * 2                                          # intro
    cycle += PEDAL + ["i", "i", "i", "i", "bII", "bII", "V", "V"]   # rise
    cycle += PEDAL * 2 + TURN * 2                              # drop
    cycle += TURN * 3                                          # break
    cycle += TURN * 2                                          # drop2
    cycle += TURN * 2                                          # lift
    cycle += ["i", "i", "VI", "VI", "iv", "iv", "bII", "bII"] + ["i"] * 8   # outro
    assert len(cycle) == LAST_BAR
    s.set_harmony(P, [[str(i + 1), c] for i, c in enumerate(cycle)])

    # -- material -----------------------------------------------------------
    s.add_motif(P, "acid",
                "0 0 3! 0 r 0 1@leg 2! 0 r 3 0 bb3! r 0@leg 3 | "
                "0 0 3! 0 r #0@leg 0 5!! 3 r 0 0 1! 2@leg 4! r",
                unit="1/16", anchor="chord",
                note="the line: two bars of sixteenths in chord tones. Root and "
                     "octave, accents off the beat, a slide into the fifth; the "
                     "second bar leans on the flat second and leaps to the high "
                     "fifth. The rests are where the kick is heard")
    s.derive_motif(P, "acid_turn", "acid", ["rotate:6"],
                   note="the same pattern started six steps in: every accent "
                        "lands somewhere new against the kick")
    s.derive_motif(P, "acid_back", "acid", ["retrograde"],
                   note="backwards, for the square-wave machine an octave above")
    s.add_motif(P, "roll", "r 0 0 0", unit="1/16", anchor="chord",
                note="the rolling bass: the root on the three sixteenths the "
                     "kick does not take")
    s.derive_motif(P, "roll_push", "roll", ["accentuate:2"],
                   note="the same, leaning on the off-beat eighth")
    s.add_motif(P, "hook",
                "4:3/16 7:3/16 6:3/16 4:3/16 2:1/4 | 4:1/2. 2:1/8 4:1/8 | "
                "5:3/16 9:3/16 7:3/16 5:3/16 9:1/4 | 7:1/2. 6:1/8 5:1/8 | "
                "3:3/16 7:3/16 5:3/16 3:3/16 2:1/4 | 3:1/2. 2:1/8 3:1/8 | "
                "b1:3/16 b8:3/16 5:3/16 3:3/16 b1:1/4 | #6:1/2 4:1/2",
                note="eight bars. A figure in dotted eighths -- three, three, "
                     "three, three, four -- that leaps a fourth and falls back, "
                     "then a held note; restated on the sixth and the fourth, "
                     "each time reaching higher, then on the flat second, and "
                     "left on the leading tone, unresolved")
    s.derive_motif(P, "hook_head", "hook", ["fragment:0,5"],
                   note="its first bar alone: heard in the drop before the theme "
                        "has been stated")

    # -- players ------------------------------------------------------------
    s.add_voice(P, "acid", "acid_bass", role="melody", octave=2, pan=0.08)
    s.add_voice(P, "acid2", "acid_square", role="counter", octave=3, pan=-0.3)
    s.add_voice(P, "lead", "supersaw", role="melody", octave=4)
    s.add_voice(P, "echo", "supersaw", role="ornament", octave=4, pan=0.45)
    s.add_voice(P, "stab", "supersaw", role="harmony", octave=3, pan=-0.2)
    s.add_voice(P, "pad", "synth_pad", role="pad", octave=3)
    s.add_voice(P, "choir", "choir", role="pad", octave=3)
    s.add_voice(P, "wall", "noise_wall", role="pad", octave=4)
    s.add_voice(P, "bass", "acid_bass", role="bass", octave=1)
    s.add_voice(P, "kick", "kit_power", role="percussion")
    s.add_voice(P, "drums", "kit_electronic", role="percussion")

    p = s.get(P)
    add = p.add_op
    B = FIRST
    intro, rise, drop, brk, drop2, lift, outro = (B[n] for n, *_ in SECTIONS)
    end = LAST_BAR + 1

    # -- kick: four on the floor, and the places it is taken away -------------
    four = "X...x...x...x..."
    add("kick", "beat", id="k_intro", at=str(intro), bars=31, lanes={"kick": four},
        note="bar 32 has no kick: the drop is a subtraction first")
    add("kick", "beat", id="k_drop", at=str(drop), bars=32, lanes={"kick": four})
    add("kick", "beat", id="k_back", at=str(brk + 20), bars=2, lanes={"kick": four},
        dynamic="mf", note="it comes back under the roll")
    add("kick", "beat", id="k_rush", at=str(brk + 22), bars=2,
        lanes={"kick": "x.x.x.x.x.x.x.x.|x.x.x.x.xxxxxxxx"}, dynamic="mf")
    add("kick", "beat", id="k_drop2", at=str(drop2), bars=32, lanes={"kick": four})
    add("kick", "beat", id="k_outro", at=str(outro), bars=12, lanes={"kick": four})
    add("kick", "beat", id="k_last", at=str(outro + 12), bars=1,
        lanes={"kick": "X..............."})
    # Every eighth bar the kick leaves the last two beats to a fill.
    for bar in (drop + 7, drop + 15, drop + 23, drop + 31, drop2 + 7, drop2 + 15,
                lift + 7, lift + 15):
        add("kick", "rest", id=f"k_gap{bar}", **{"from": f"{bar}:3", "until": str(bar + 1)})

    # -- hats, claps, rolls ---------------------------------------------------
    hat16 = "o.xoo.xoo.xoo.xo"
    off = "..x...x...x...x."
    clap = "....x.......x..."
    add("drums", "beat", id="d_intro", at=str(intro + 4), bars=12,
        lanes={"hat": "..o...o...o...o."}, dynamic="mp")
    add("drums", "beat", id="d_intro2", at=str(intro + 8), bars=8,
        lanes={"shaker": "o.o.o.o.o.o.o.o."}, dynamic="p")
    add("drums", "beat", id="d_rise", at=str(rise), bars=14,
        lanes={"hat": hat16, "open": off})
    add("drums", "beat", id="d_rise_clap", at=str(rise + 8), bars=6, lanes={"clap": clap})
    add("drums", "beat", id="d_rise_roll", at=str(rise + 14), bars=2,
        lanes={"snare": "x...x...x...x...|x.x.x.x.xxxxxxxx", "open": off})
    add("drums", "dynamics", id="d_rise_swell", **span(rise + 14, drop), start="mp", end="ff")
    add("drums", "chop", id="d_rise_climb", **span(rise + 15, drop), slices=4,
        order="0 1 2*2^0>4 3*2^4>9", note="the roll climbs in pitch into the drop")

    full = {"hat": hat16, "open": off, "clap": clap}
    add("drums", "beat", id="d_drop", at=str(drop), bars=32,
        lanes={**full, "crash": "X" + "." * (16 * 16 - 1)})
    add("drums", "beat", id="d_drop2", at=str(drop2), bars=32,
        lanes={**full, "ride": "x...x...x...x...", "crash": "X" + "." * (16 * 16 - 1)})
    fill = {"snare": "........x.x.xxxx", "tom_hi": "..............x.", "tom_lo": "...............x"}
    for bar in (drop + 7, drop + 15, drop + 23, drop + 31, drop2 + 7, drop2 + 15,
                lift + 7, lift + 15):
        add("drums", "rest", id=f"d_gap{bar}", **{"from": f"{bar}:3", "until": str(bar + 1)})
        add("drums", "beat", id=f"d_fill{bar}", at=str(bar), bars=1, lanes=fill)
    # The break: nothing, then a roll that takes four bars to arrive.
    add("drums", "beat", id="d_break_roll", at=str(brk + 20), bars=4,
        lanes={"snare": "x...x...x...x...|x...x...x.x.x.x.|x.x.x.x.x.x.x.x.|xxxxxxxxxxxxxxxx"})
    add("drums", "dynamics", id="d_break_swell", **span(brk + 20, drop2), start="p", end="ff")
    add("drums", "chop", id="d_break_climb", **span(brk + 23, drop2), slices=4,
        order="0 1^2 2*2^2>5 3*2^5>12")
    add("drums", "beat", id="d_outro", at=str(outro), bars=12,
        lanes={"hat": hat16, "open": off, "crash": "X" + "." * (16 * 12 - 1)})
    add("drums", "dynamics", id="d_outro_fade", **span(outro, outro + 12), start="f", end="p")
    add("drums", "beat", id="d_last", at=str(outro + 12), bars=1,
        lanes={"crash": "X..............."})
    add("drums", "swing", id="d_swing", amount=0.54, res="1/16",
        note="a few percent: enough that the sixteenths lean")

    # -- bass ---------------------------------------------------------------
    def roll(id_: str, motif: str, first: int, bars: int, **kw) -> None:
        add("bass", "play", id=id_, motif=motif, at=str(first), times=bars * 4,
            every="1/4", articulation="staccato", **kw)

    roll("b_rise", "roll", rise, 15, dynamic="mp")
    roll("b_drop", "roll_push", drop, 32, dynamic="mf")
    roll("b_drop2", "roll_push", drop2, 32, dynamic="mf")
    roll("b_outro", "roll", outro, 12, dynamic="mp")
    add("bass", "bass", id="b_break", at=str(brk), bars=20, pattern="root", rhythm="1/1",
        dynamic="p", articulation="legato",
        note="in the break it only holds the root, shut")
    add("bass", "bass", id="b_end", at=str(outro + 12), bars=4, pattern="root",
        rhythm="1/1", dynamic="p", articulation="legato")

    # -- the acid line --------------------------------------------------------
    def line(id_: str, voice: str, motif: str, first: int, bars: int, **kw) -> None:
        add(voice, "play", id=id_, motif=motif, at=str(first), times=bars // 2,
            every="2/1", articulation="portato", **kw)

    line("a_intro", "acid", "acid", intro, 16)
    line("a_rise", "acid", "acid", rise, 16)
    add("acid", "dynamics", id="a_shut", **span(intro, rise), start="pp", end="p")
    add("acid", "dynamics", id="a_open", **span(rise, drop), start="p", end="ff")
    line("a_drop", "acid", "acid", drop, 16, dynamic="f")
    for k in range(4):                       # B: two bars as written, two turned
        line(f"a_drop_b{k}", "acid", "acid" if k % 2 == 0 else "acid_turn",
             drop + 16 + 4 * k, 4, dynamic="ff" if k % 2 else "f")
    line("a_break", "acid", "acid", brk + 8, 16)
    add("acid", "dynamics", id="a_climb", **span(brk + 8, drop2), start="pp", end="fff")
    line("a_drop2", "acid", "acid_turn", drop2, 16, dynamic="ff")
    line("a_lift", "acid", "acid", lift, 16, dynamic="ff")
    line("a_lift2", "acid2", "acid_back", lift, 16, dynamic="f")
    line("a_outro", "acid", "acid", outro, 16)
    line("a_outro2", "acid2", "acid_back", outro, 8)
    add("acid", "dynamics", id="a_close", **span(outro, end), start="ff", end="pp")
    add("acid2", "dynamics", id="a2_close", **span(outro, outro + 8), start="f", end="pp")
    # Before each drop the line is left alone for half a bar and slides up.
    add("acid", "rest", id="a_hole", **{"from": f"{drop2 - 1}:3", "until": str(drop2)})
    add("acid", "phrase", id="a_scream", at=f"{drop2 - 1}:3", unit="1/16",
        steps="0!!@leg 1!!@leg 2!!@leg 3!!@leg 4!!@leg 5!!@leg 6!!@leg 8!!",
        anchor="chord", dynamic="fff", octave=2,
        note="up through the dominant chord, two octaves and a fifth, every note slid: the one bar "
             "where nothing else plays")

    # -- the hook -------------------------------------------------------------
    add("lead", "play", id="h_tease1", motif="hook_head", at=str(drop + 16), dynamic="p")
    add("lead", "play", id="h_tease2", motif="hook_head", at=str(drop + 24), dynamic="mp")
    add("lead", "play", id="h_break1", motif="hook", at=str(brk + 8), dynamic="mp",
        articulation="tenuto")
    add("lead", "play", id="h_break2", motif="hook", at=str(brk + 16), dynamic="f",
        articulation="tenuto")
    add("lead", "rest", id="h_hole", **{"from": f"{drop2 - 1}:3", "until": str(drop2)})
    add("lead", "play", id="h_drop2", motif="hook", at=str(drop2), times=2, every="8/1",
        dynamic="ff", articulation="tenuto")
    add("lead", "play", id="h_lift", motif="hook", at=str(lift), times=2, every="8/1",
        dynamic="ff", articulation="tenuto")
    add("echo", "double", id="h_echo", source="lead", delay="3/16", dynamic="p",
        note="the hook again a dotted eighth later, off to one side")

    # -- chords: a gate, a pad, a choir ---------------------------------------
    gate = "_ . _ _ . _ . _ _ . _ _ . _ . ."
    for id_, first, bars in (("s_drop", drop + 16, 16), ("s_drop2", drop2, 32)):
        add("stab", "chords", id=id_, at=str(first), bars=bars, voicing="block",
            rhythm="1/16", tones=3, lead=True, articulation="staccato", dynamic="mf")
        add("stab", "chop", id=f"{id_}_gate", **span(first, first + bars), slices=16,
            order=gate)
    add("pad", "chords", id="p_intro", at=str(intro + 8), bars=24, voicing="pad",
        tones=3, lead=True, dynamic="p")
    add("pad", "dynamics", id="p_intro_swell", **span(intro + 8, drop), start="pp", end="mf")
    add("pad", "chords", id="p_drop", at=str(drop), bars=32, voicing="pad", tones=3,
        lead=True, dynamic="mp")
    add("pad", "chords", id="p_break", at=str(brk), bars=24, voicing="pad", tones=4,
        lead=True, spread=True, dynamic="mf")
    add("pad", "chords", id="p_drop2", at=str(drop2), bars=32, voicing="pad", tones=3,
        lead=True, dynamic="mf")
    add("pad", "chords", id="p_outro", at=str(outro), bars=16, voicing="pad", tones=4,
        lead=True, spread=True, dynamic="mf")
    add("pad", "dynamics", id="p_outro_fade", **span(outro + 8, end), start="mf", end="pp")
    add("choir", "chords", id="c_break", at=str(brk), bars=24, voicing="pad", tones=3,
        lead=True, dynamic="mp")
    add("choir", "dynamics", id="c_break_swell", **span(brk + 8, drop2), start="mp", end="f")
    add("choir", "chords", id="c_lift", at=str(lift), bars=16, voicing="pad", tones=3,
        lead=True, dynamic="f")
    add("choir", "chords", id="c_outro", at=str(outro), bars=8, voicing="pad", tones=3,
        lead=True, dynamic="mp")
    for voice in ("pad", "choir", "bass"):
        add(voice, "rest", id=f"{voice}_hole", **{"from": f"{drop2 - 1}:3", "until": str(drop2)})

    # -- noise: risers --------------------------------------------------------
    for id_, first, bars in (("w_rise", rise + 8, 8), ("w_break", brk + 16, 8),
                             ("w_lift", lift - 1, 1)):
        add("wall", "drone", id=id_, at=str(first), bars=bars, degree=4, dynamic="mf")
        add("wall", "filter", id=f"{id_}_sweep", **span(first, first + bars),
            mode="highpass", start=300, end=7000, resonance=0.5)
        add("wall", "dynamics", id=f"{id_}_swell", **span(first, first + bars),
            start="pp", end="f")
    add("wall", "rest", id="w_hole", **{"from": f"{drop2 - 1}:3", "until": str(drop2)})

    # -- sound ----------------------------------------------------------------
    # The drum-machine kick rings for 0.9 s -- longer than a beat at this
    # tempo, so four of them to the bar was one unbroken 45 Hz drone holding
    # 70% of the mix's energy. This one is over in time for the next.
    add("kick", "filter", id="fx_kick_tight", mode="highpass", start=38, end=38)
    add("kick", "eq", id="fx_kick_click", freq=3200, gain=9, width=1.5)
    add("kick", "drive", id="fx_kick", amount=0.5)
    add("kick", "gain", id="fx_kick_level", db=-3)
    add("drums", "compress", id="fx_drums_slab", ratio=3, threshold=-16)
    add("drums", "gain", id="fx_drums_level", db=8)
    add("bass", "duck", id="fx_bass_duck", source="kick", depth=5, release=0.09)
    add("bass", "gain", id="fx_bass_level", db=-2)
    add("acid", "filter", id="fx_acid_intro", **span(intro, rise), start=500, end=2500,
        resonance=0.3, note="a second filter over the machine's own, for the long moves")
    add("acid", "filter", id="fx_acid_break", **span(brk + 8, drop2), start=600, end=9000,
        resonance=0.4)
    add("acid", "filter", id="fx_acid_close", **span(outro, end), start=9000, end=350,
        resonance=0.4)
    add("acid", "drive", id="fx_acid_bite", amount=0.8)
    add("acid", "gain", id="fx_acid_level", db=0)
    add("acid2", "drive", id="fx_acid2_bite", amount=0.6)
    add("acid2", "gain", id="fx_acid2_level", db=-5)
    add("lead", "filter", id="fx_lead_far", **span(drop + 16, brk), start=1400, end=1400)
    add("lead", "filter", id="fx_lead_break", **span(brk + 8, drop2), start=900, end=7000,
        resonance=0.2, note="the hook starts dull and opens as the roll arrives")
    add("lead", "duck", id="fx_lead_duck", source="kick", depth=3, release=0.12)
    add("lead", "gain", id="fx_lead_level", db=2)
    add("echo", "filter", id="fx_echo_dark", start=2200, end=2200)
    add("stab", "filter", id="fx_stab_thin", mode="highpass", start=350, end=350)
    add("stab", "duck", id="fx_stab_duck", source="kick", depth=6, release=0.14)
    add("stab", "gain", id="fx_stab_level", db=0)
    for voice in ("pad", "choir"):
        add(voice, "duck", id=f"fx_{voice}_pump", source="kick", depth=9, release=0.22,
            note="the pump")
    add("wall", "gain", id="fx_wall_level", db=-6)
    s.save(p)

    s.set_master(P, push=9, room={"decay": 2.6, "wet": 0.22},
                 stops=[{"from": f"{drop2 - 1}:3", "until": str(drop2), "keep": ["acid"]}])
    return s


def main() -> int:
    s = build()
    print(s.squint(P))
    print()
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
