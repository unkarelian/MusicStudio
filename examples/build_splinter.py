"""Builds `splinter`, the extreme end of what the studio can do: breakcore.

`undertow` cuts its break up every few bars. This one never plays it straight.
174 beats a minute, a different cut on every bar, a distorted kick on every
beat, a noise wall under all of it, and a master that is driven past full scale
on purpose. It was aimed at four reference tracks measured the same way
`ms hear` measures: eleven to fourteen hits a second, a spectrum closer to noise
than to notes, and almost no difference between the loudest moment and the
average one.

    slam     two bars: a snare roll climbing out of a noise riser
    A        the break, cut every bar; the kick; the reese
    B        the riff -- two bars on a wall of saws, a question and its answer
             -- and the whole mix starts to stutter with the drums
    void     half a minute's worth of tension in eight bars: no break, a sub,
             a held wail, one bar of almost nothing, a roll back in
    C        everything, with the cuts at their most violent and the kick
             rolling in sixty-fourths
    melt     the tempo climbs from 174 to 208 while it is all crushed further
    end      it stops

The cuts are *generated*: a seeded rule, not seventy hand-typed bars. Each bar's
order is drawn from the same small grammar `chop` understands -- keep the slice,
swap it for a snare or a kick, retrigger it, roll it up or down in pitch, drop
it -- with one number, intensity, deciding how far from the written break it
strays. The seed is the bar number, so the piece is the same on every build.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "splinter"

# The break. Slices are sixteenths: 0 the kick on one, 4 and 12 the snares.
# Four bars, laid out the way the classic funk break is: two bars the same, a
# third that drops a kick, and a fourth that displaces the snare and pushes
# into the next phrase -- so the break itself is a sentence with an ending.
BREAK = {"kick":  "x.x.......xx....|x.x.......xx....|x.x.......x.....|..xx......x.....",
         "snare": "....x..o.o..x..o|....x..o.o..x..o|....x..o.o....x.|.o..x..o.o....x.",
         "hat":   "o.o.o.o.o.o.o.o.",
         "open":  "..............o."}
SNARES, KICKS = (4, 12), (0, 2, 10)


def cut_order(bar: int, intensity: float, anchor: bool = True) -> str:
    """One bar's cut, as a `chop` order of sixteen slots.

    ``intensity`` 0 is the break as written; 1 is unrecognisable. Seeded by the
    bar number (a string seed, which Python hashes the same in every process).

    ``anchor`` leaves the four beats alone -- the kick on one and the two
    backbeat snares above all. The first version cut everything, and measured
    like it: nothing repeated at the beat or the bar, so there was no rhythm to
    hear, only events. A break can be wrecked between the beats and still be
    felt, as long as the beats themselves keep arriving.
    """
    rng = random.Random(f"splinter-cut-{bar}")
    out: list[str] = []
    slot = 0
    while slot < 16:
        roll = rng.random()
        if (anchor and slot % 4 == 0) or roll > intensity:  # leave it alone
            out.append(str(slot))
            slot += 1
            continue
        kind = rng.random()
        if kind < 0.10:                                   # a hole
            out.append(".")
            slot += 1
        elif kind < 0.40:                                 # a retrigger, maybe pitched
            src = rng.choice(SNARES + KICKS)
            reps = rng.choice((2, 2, 2, 4))
            pitch = rng.choice(("", "", "^5", "^7", "^-5", "^12"))
            out.append(f"{src}*{reps}{pitch}")
            slot += 1
        elif kind < 0.62 and slot <= 13:                  # a roll across 2-3 slots, climbing or diving
            src = rng.choice(SNARES)
            span = rng.choice((2, 3))
            if anchor:                                    # never across a beat
                span = min(span, 3 - slot % 4)
            if span < 1:
                out.append(str(slot))
                slot += 1
                continue
            lo, hi = rng.choice(((0, 12), (12, 0), (0, 7), (-12, 0), (0, 19)))
            for k in range(span):
                a = lo + (hi - lo) * k / span
                b = lo + (hi - lo) * (k + 1) / span
                out.append(f"{src}*4^{a:.0f}>{b:.0f}")
            slot += span
        elif kind < 0.72:                                 # backwards
            out.append(f"{rng.choice(SNARES)}r")
            slot += 1
        else:                                             # the wrong slice
            out.append(str(rng.choice(SNARES + KICKS + (slot ^ 1, (slot + 8) % 16))))
            slot += 1
    return " ".join(out[:16])


def build() -> Studio:
    s = Studio(PROJECT)
    # F minor: the sub's tonic is F1, 44 Hz.
    s.create(P, key="f minor", tempo=174, style="electronic", overwrite=True)
    for name, bars, extra in [("slam", 2, {}), ("A", 16, {}), ("B", 16, {}),
                              ("void", 8, {}), ("C", 32, {}),
                              ("melt", 16, {"tempo_end": 208}), ("end", 2, {})]:
        s.add_section(P, name, bars=bars, dynamic="ff", **extra)
    s.update_section(P, "void", dynamic="mf")

    hard = ["i", "i", "bII", "i"]              # Fm  Fm  Gb  Fm
    torn = ["i", "VI", "bII", "V"]             # Fm  Db  Gb  C
    cycle: list[str] = ["V", "V"]                                # slam   1-2
    cycle += hard * 4                                            # A      3-18
    cycle += (hard + torn) * 2                                   # B      19-34
    cycle += ["VI", "VI", "iv", "iv", "bII", "bII", "V", "V"]    # void   35-42
    cycle += (hard + torn) * 4                                   # C      43-74
    cycle += ["i", "bII"] * 8                                    # melt   75-90
    cycle += ["i", "i"]                                          # end    91-92
    s.set_harmony(P, [[str(i + 1), c] for i, c in enumerate(cycle)])

    # -- material -----------------------------------------------------------
    s.add_motif(P, "riff",
                "0 0 r 0 2 r 4 4 r r 6 4 r r 3 r | 0 0 r 0 2 r 4 4 r r 3 2 r 0:3/16",
                unit="1/16",
                note="two bars in 3+3+2. The first climbs to the seventh and is "
                     "left hanging on the fourth; the second starts the same way "
                     "and comes down to the tonic and stays on it. The first "
                     "version of this was one bar that stopped mid-figure and "
                     "repeated -- a question asked sixteen times")
    s.derive_motif(P, "riff_up", "riff", ["transpose:2"],
                   note="the same riff a third higher, for the second half of C")
    s.add_motif(P, "wail", "7:1/2. b8:1/4 | 7:1/2 4:1/2 | 5:1/2 4:1/4 5:1/4 | 7:1/1",
                note="the only slow thing in the piece: the tonic, the flat second "
                     "over it, and a fall through the flat sixth")
    s.derive_motif(P, "wail_cut", "wail", ["fragment:0,2", "diminish:2"],
                   note="its first two notes at double speed, for the melt")
    s.add_motif(P, "pound", "r 0 r 0 r 0 r 0", anchor="chord",
                note="the bass: the root on every off-beat, in the gaps the kick "
                     "leaves -- so the low end alternates kick, sub, kick, sub "
                     "instead of being one continuous rumble")
    s.derive_motif(P, "lurch", "pound", ["rhythmize:1/4. 1/8 1/4 1/4"],
                   note="the same root, half-time and limping, for the void")

    # -- players ------------------------------------------------------------
    s.add_voice(P, "lead", "supersaw", role="melody", octave=4)
    s.add_voice(P, "shred", "supersaw", role="ornament", octave=4)
    s.add_voice(P, "pad", "tremolo_strings", role="pad", octave=3)
    s.add_voice(P, "wall", "noise_wall", role="pad", octave=4)
    s.add_voice(P, "sub", "sub_bass", role="bass", octave=1)
    s.add_voice(P, "reese", "reese_bass", role="bass", octave=2)
    s.add_voice(P, "drums", "kit_room", role="percussion", engine="soundfont")
    s.add_voice(P, "stomp", "kit_808", role="percussion")

    def span(a: int, z: int) -> dict:
        return {"from": str(a), "until": str(z)}

    # Everything from here is placed on the piece directly and saved once: a
    # hundred cuts do not each need their own view and lint pass.
    p = s.get(P)
    add = p.add_op

    # -- slam ---------------------------------------------------------------
    add("drums", "beat", id="s_roll", at="1", bars=2, tune=4,
        lanes={"snare": "x.x.x.x.xxxxxxxx|xxxxxxxxxxxxxxxx", "kick": "x...x...x...x..."})
    add("drums", "chop", id="s_climb", **span(2, 3), slices=4,
        order="0*4^0>3 1*4^3>7 2*8^7>12 3*8^12>19")
    add("wall", "drone", id="s_riser", at="1", bars=2, degree=4)

    # -- the break, under A, B, C and the melt -------------------------------
    for sec, first, bars in (("a", 3, 16), ("b", 19, 16), ("c", 43, 32), ("m", 75, 16)):
        add("drums", "beat", id=f"{sec}_break", at=str(first), bars=bars, tune=4,
            lanes={**BREAK, "crash": "x" + "." * (16 * 8 - 1)})
    # Each four bars: the break as written, then nudged, then cut, then wrecked.
    # The straight bar is what makes the wrecked one a fill and not just noise.
    plan = [(3, 18, 0.5), (19, 34, 0.65), (43, 74, 0.8), (75, 90, 0.95)]
    shape = (0.0, 0.25, 0.6, 1.0)
    for first, last, peak in plan:
        for bar in range(first, last + 1):
            place = (bar - first) % 4
            t = peak * shape[place]
            if t <= 0:
                continue
            add("drums", "chop", id=f"cut{bar}", **span(bar, bar + 1), slices=16,
                order=cut_order(bar, t, anchor=place < 3))

    # -- the kick: on every beat, then rolling --------------------------------
    for sec, first, bars in (("a", 3, 16), ("b", 19, 16), ("c", 43, 32), ("m", 75, 16)):
        add("stomp", "beat", id=f"{sec}_stomp", at=str(first), bars=bars,
            lanes={"kick": "X...X...X...X..."})
    for bar in list(range(46, 75, 4)) + list(range(76, 91, 2)):
        add("stomp", "chop", id=f"kick_roll{bar}", **span(bar, bar + 1), slices=16,
            order="0 _ _ _ 0 _ _ _ 0 _ 0*2 _ 0*4^0>-7 0*4^-7>-12 0*8^-12>0 0*8^0>12",
            note="the kick rolls and dives at the end of the phrase")

    # -- bass ---------------------------------------------------------------
    for sec, first, n in (("a", 3, 16), ("b", 19, 16), ("c", 43, 32), ("m", 75, 16)):
        add("sub", "play", id=f"{sec}_sub", motif="pound", at=str(first), times=n,
            every="1/1")
    add("sub", "play", id="v_sub", motif="lurch", at="35", times=6, every="1/1",
        dynamic="f")
    add("reese", "double", id="reese_all", source="sub", octaves=1)

    # -- the wall ------------------------------------------------------------
    add("wall", "chords", id="a_wall", at="3", bars=32, voicing="pad", tones=2)
    add("wall", "chords", id="c_wall", at="43", bars=48, voicing="pad", tones=2)
    add("wall", "chords", id="v_wall", at="39", bars=4, voicing="pad", tones=2,
        dynamic="mp")
    # Never a wash: the wall is gated to the off-beats, where an open hat would
    # be, so it adds to the rhythm instead of burying it.
    add("wall", "chop", id="a_gate", **span(3, 35), slices=8, order=". 0 . 0 . 0 . 0")
    add("wall", "chop", id="c_gate", **span(43, 91), slices=8, order=". 0 . 0 . 0 . 0*2")

    # -- lead ---------------------------------------------------------------
    add("lead", "play", id="a_wail", motif="wail", at="11", times=2, every="4/1",
        articulation="legato")
    # The riff takes the two tonic bars of each four; the other two are left
    # to the drums' fill, so every statement completes and then has room.
    add("shred", "play", id="b_riff", motif="riff", at="19", times=4, every="4/1")
    add("lead", "play", id="v_wail", motif="wail", at="35", articulation="legato",
        dynamic="mf", transform=["augment:2"])
    add("shred", "play", id="c_riff", motif="riff", at="43", times=4, every="4/1")
    add("shred", "play", id="c_riff_up", motif="riff_up", at="59", times=4, every="4/1")
    add("shred", "play", id="m_riff", motif="riff", at="75", times=4, every="4/1")
    add("lead", "play", id="c_wail", motif="wail", at="59", times=4, every="4/1",
        articulation="legato", octave=5)
    add("lead", "play", id="m_cut", motif="wail_cut", at="75", times=16, every="1/1")
    add("pad", "chords", id="v_pad", at="35", bars=8, voicing="pad", tones=3,
        dynamic="mp")
    add("pad", "chords", id="c_pad", at="43", bars=48, voicing="pad", tones=3,
        dynamic="mf")

    # -- the mix stutters with the drums --------------------------------------
    # The same order on every pitched voice at once is a stutter of the whole
    # track -- the sound of a sampler retriggering the mix.
    glitches = {26: "0 0 0*2 0*2 4 4 4*2 4*4 8 8*2 8*2 8*4 12*4^0>12 12*4^12>0 . .",
                34: "0*2 0*2 0*4 0*4 0*8 0*8 . . 8*2 8*2 8*4 8*4 8*8^0>12 8*8^12>24 . .",
                50: "0 0*2 . 0*4 4 4*2 . 4*4 0^5 0*2^5 . 0*4^5 0^12 0*2^12 0*4^12 .",
                58: "0*4 . 0*4 . 0*8 . . . 8*4^0>-12 8*4^-12>-24 . . 0*8^0>12 0*8^12>24 . .",
                66: "0 . . 0 . . 0*2 . 0 . . 0*4 . . 0*8^0>19 .",
                74: "0*2 0*2 0*2 0*2 0*4 0*4 0*4 0*4 0*8 0*8 0*8 0*8 . . . ."}
    for bar, order in glitches.items():
        for voice in ("lead", "shred", "reese", "sub", "wall"):
            add(voice, "chop", id=f"glitch{bar}_{voice}", **span(bar, bar + 1),
                slices=16, order=order)
    # In the melt it happens every other bar, generated like the drum cuts.
    for bar in range(76, 91, 2):
        order = cut_order(1000 + bar, 0.9).replace("12", "8").replace("10", "0")
        for voice in ("lead", "reese"):
            add(voice, "chop", id=f"melt{bar}_{voice}", **span(bar, bar + 1),
                slices=16, order=order)

    # -- void: take it all away ----------------------------------------------
    add("drums", "beat", id="v_hits", at="35", bars=4, tune=-5,
        lanes={"kick": "x...............|..........x.....", "snare": "........x......."},
        dynamic="f", note="the same kit an octave of speed lower: half-time, huge")
    add("drums", "beat", id="v_roll", at="41", bars=2, tune=4,
        lanes={"snare": "x...x...x.x.x.x.|xxxxxxxxxxxxxxxx", "kick": "x.......x.x.x.x."})
    add("drums", "dynamics", id="v_roll_swell", **span(41, 43), start="mp", end="ff")
    add("drums", "chop", id="v_climb", **span(42, 43), slices=4,
        order="0*4^-5>0 1*4^0>5 2*8^5>12 3*16^12>24")
    for voice in ("sub", "reese", "pad", "lead"):
        add(voice, "rest", id=f"v_hole_{voice}", **{"from": "39", "until": "40"})
    add("lead", "rest", id="v_lead_out", **{"from": "41", "until": "43"},
        note="the wail is cut off by the roll before it can resolve")

    # -- end ----------------------------------------------------------------
    add("drums", "beat", id="e_hit", at="91", bars=1, tune=4,
        lanes={"kick": "X...............", "crash": "X...............",
               "snare": "X..............."})
    add("sub", "drone", id="e_sub", at="91", bars=2, degree=0)

    # -- sound: nothing is clean ----------------------------------------------
    # Drums are processed far less than anything else here. Crushed, clipped
    # and compressed 10:1, the hits stood 4 dB above the hiss between them and
    # the kit sounded like scratching; `undertow`'s stand 12 dB clear. A break
    # is transients, and transients are what heavy processing removes first.
    add("drums", "filter", id="fx_top", start=9000, end=9000)
    add("drums", "compress", id="fx_slab", ratio=4, threshold=-18)
    add("drums", "drive", id="fx_drums", amount=0.45)
    add("drums", "gain", id="fx_drums_level", db=-3)
    add("stomp", "drive", id="fx_stomp", amount=2.5, mode="clip",
        note="a drum-machine kick clipped until it is a square wave with a thud")
    add("stomp", "gain", id="fx_stomp_level", db=-21,
        note="clipping made it 15 dB hotter than everything else put together; "
             "this puts it just under the break, where it is the pulse")
    add("sub", "drive", id="fx_sub", amount=0.6)
    add("sub", "gain", id="fx_sub_level", db=-2)
    add("reese", "filter", id="fx_reese_a", **span(3, 11), start=250, end=3500,
        resonance=0.5)
    add("reese", "filter", id="fx_reese_c", **span(43, 51), start=300, end=5000,
        resonance=0.6)
    add("reese", "drive", id="fx_growl", amount=1.0, mode="clip")
    add("reese", "gain", id="fx_reese_level", db=-6)
    for voice in ("lead", "shred"):
        add(voice, "drive", id=f"fx_{voice}", amount=1.4, mode="clip")
        add(voice, "crush", id=f"fx_{voice}_grit", rate=9000, bits=7)
        add(voice, "gain", id=f"fx_{voice}_level", db=-9)
    add("wall", "filter", id="fx_riser", **span(1, 3), mode="highpass", start=200,
        end=6000, resonance=0.4)
    add("wall", "filter", id="fx_wall_void", **span(39, 43), mode="highpass", start=150,
        end=8000, resonance=0.5, note="the riser out of the void")
    add("wall", "gain", id="fx_wall_level", db=-8)
    add("pad", "drive", id="fx_pad", amount=0.8)
    add("pad", "gain", id="fx_pad_level", db=-6)
    s.save(p)

    # The master is part of the sound: driven past full scale and cut off flat --
    # but only a little. At 13 dB every hit came out the same height and the
    # rhythm vanished into the clipping. Then it is turned down: loud-sounding
    # is the style, loud is not a requirement.
    s.set_master(P, clip=4, level=-9)
    return s


def main() -> int:
    s = build()
    print(s.squint(P))
    print()
    print(s.motifs(P).split("\n\n")[-2] if "\n\n" in s.motifs(P) else s.motifs(P))
    print()
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
