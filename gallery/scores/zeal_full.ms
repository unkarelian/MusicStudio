# ZEAL — combat loop, written as five stacked layers for the game to mix by zeal.
# 176 BPM, E phrygian with a tritone. Each 8-bar phrase is seven bars of 4/4 and one of 7/8,
# so the loop lurches forward an eighth early every phrase. Four phrases of assault (a b c d), then a
# breakdown (x: half-time, stripped, the theme alone) and a build (y) that climbs back into a. 48 bars = 189 beats.
# `# @layer N` lines split this file into per-layer scores (tools/music.py); built whole it is the full mix.

piece zeal_full key="E minor" tempo=176 style=electronic
master room.decay=1.4 room.wet=0.16 push=3

section a  bars=7 dynamic=f
section a7 bars=1 meter=7/8 dynamic=f
section b  bars=7 dynamic=f
section b7 bars=1 meter=7/8 dynamic=f
section c  bars=7 dynamic=ff
section c7 bars=1 meter=7/8 dynamic=ff
section d  bars=7 dynamic=ff
section d7 bars=1 meter=7/8 dynamic=ff
section x  bars=7 dynamic=mf
section x7 bars=1 meter=7/8 dynamic=mf
section y  bars=7 dynamic=f
section y7 bars=1 meter=7/8 dynamic=ff

harmony
  @a: i5 i5 i5 bII5 i5 i5 VI5 bII5
  @b: i5 i5 VI5 VI5 iv5 iv5 bII5 V
  @c: i5 i5 i5 i5 bII5 bII5 i5 bII5
  @d: iv5 iv5 iv5 iv5 v5 v5 bII5 V
  @x: VII5 VII5 VII5 VII5 VII5 VII5 bII5 VII5
  @y: v5 v5 VI5 VI5 VII5 VII5 bII5 V

# -- riffs: written in eighths, played in sixteenths ---------------------------
motif ra1e = 0! 0 b1 0 0! 0 2 0 0! 0 b1 0 b4! 4 2 b1        -- the chug: root, flat second, and a tritone tail
motif ra2e = 0! 0 b1 0 0! 0 2 0 6! 5 4 2 b4! 2 b1 0         -- its answer falls from the seventh
motif ra7e = 0! 0 b1 0 b4! 4 b4 2 b1! 0 b1 b4 7! 7          -- the 7/8 bar: fourteen sixteenths and out
motif rb1e = 0! 0 7 0 0! 0 6 0 0! 0 5 0 b4! 4 b4 2          -- pedal-point thrash: the top voice walks down
motif rb2e = 0! 0 5 0 0! 0 4 0 b1! b1 b1 b1 b4! b4 2 b1
motif rb7e = 7! 6 5 4 b4! 2 b1 0 b1! 2 b4 4 7! 7            -- a run down and back up
motif ra1 < ra1e : diminish:2
motif ra2 < ra2e : diminish:2
motif ra7 < ra7e : diminish:2
motif rb1 < rb1e : diminish:2
motif rb2 < rb2e : diminish:2
motif rb7 < rb7e : diminish:2
motif rc1 = 0! r 0 0 b1! r 0 r                              -- the stomp: half the notes, twice the weight
motif rc2 = 0! r 0 0 b4! 4 b4 2
motif rc7 = 0! 0 b1! b1 b4! b4 7
motif hit7gap = 0! r 0! r r r r                             -- the last bar of the loop: two stabs, then nothing, so the top of the loop detonates
motif hit7 = 0! r 0! r b4! b4! b4!                          -- the 7/8 bar as one gesture: two stabs and a triple on the tritone (2+2+3), everyone together
motif ra2he = 0! 0 b1 0 0! 0 2 0 6! 5 4 2 r r r r           -- bar 4 of each phrase: the riff, then a beat of nothing
motif rb2he = 0! 0 5 0 0! 0 4 0 b1! b1 b1 b1 r r r r
motif ra2h < ra2he : diminish:2
motif rb2h < rb2he : diminish:2
motif rc2h = 0! r 0 0 b4! 4 r r
motif rx1 = -1! r r -1 r r b1 r                              -- the breakdown: three notes a bar on D, leaning on F
motif rx2 = -1! r r -1 r b1 0 r
motif ring7 = -1:7/8!                                       -- its 7/8 bar is one chord left to ring
motif chug = 4! 4 4 4 4! 4 4 4                      -- the build: one note, climbing a step every two bars
motif chug7 = b1! b1 b1 b1 b4! b4 b4 b4
motif seqe = 0! r 0 0 r 0 b1 r 0! r 0 7 r 0 b4 r            -- a sequencer line with holes in it, not an arpeggio
motif seq < seqe : diminish:2

# -- the theme ------------------------------------------------------------------
motif zeal = 0:1/4. b1:1/8 2:1/4 4:1/4 | b4:1/4. 4:1/8 7:1/2            -- climbs through the flat second to the tritone, resolves up
motif zeal_ans = 7:1/4. 6:1/8 5:1/4 b4:1/4 | 4:1/4. 2:1/8 b1:1/2        -- and falls back onto the flat second, unresolved
motif theme < zeal : then:zeal_ans
motif frantic < theme : diminish:2                                      -- the whole theme in two bars
motif zeal_inv < zeal : invert
motif toll < zeal : augment:2                                           -- the theme as bells, far off
motif toll_ans < zeal_ans : augment:2
motif lead7 = 7 6 5 b4 4 2 b1                                           -- the 7/8 scream down
motif arpe = 0 4 7 9 11 9 7 4 0 4 7 9 b4 9 7 4
motif arp < arpe : diminish:2
motif treme = 7! b8 7 b8 7! b8 7 b8 9! b8 9 b8 b11! 9 b8 7
motif trem < treme : diminish:2
motif tick = 4:3/16! 4:3/16 4:3/16 4:3/16 4:1/4                         -- three against four

lanes THRASH
  kick:  x.xx..x.x.xx..x.|x.xx..x.x.xxx.xx
  snare: ....X.......X...|....X.......X.oo
  hat:   x.x.x.x.x.x.x.x.
lanes SKANK
  kick:  x.xxx.xxx.xxx.xx
  snare: ..X...X...X...X.
  ride:  x.x.x.x.x.x.x.x.
lanes HALF
  kick:  x..x..x.....x.xx|x..x..x...x.xxxx
  snare: ........X.......
  ride:  x...x...x...x...
  tom_lo: ................|..............oo
lanes SEVEN
  kick:  x...x...x.x.x.
  snare: X...X...X.X.X.
  crash: x...x.........
lanes STOMP
  kick:  x.........x.....|x.......x.x.....
  snare: ........X.......
  pedal: x...x...x...x...
  tom_lo: ..............o.|............o.o.
lanes MANIA
  snare: ..x.o.x...x.oxxx|o.x...xx..x.o.xx
  hat:   xxxxxxxxxxxxxxxx
  open:  ..x...x...x...x.
lanes MANIA7
  snare: ........xxxxxx
  hat:   x...x...xxxxxx
set ROLL = "0 1 2 3 4 4 4*2 4*2 8 9 4*2 4*2 12*4 12*4 12*4^0>7 12*4^0>12"
set ONE = "x..............."

voice pad dark_pad role=pad octave=2
  pad_floor: drone at=1 bars=48 degree=0 dynamic=mf
  lvl_pad: gain db=20
voice pad5 dark_pad role=pad octave=3 pan=0.3
  pad_fifth: drone at=1 bars=48 degree=4 dynamic=mp
  lvl_pad5: gain db=16
voice wind noise_wall role=pad octave=3 pan=-0.3
  wind_all: drone at=1 bars=48 dynamic=mp
  fx_wind: filter start=500 end=1400 from=@a until=@c
  fx_wind2: filter start=1400 end=500 from=@c until=@y7.end
  lvl_wind: gain db=6
voice bells fm_bells role=melody octave=4 engine=soundfont
  bell_a: play motif=toll at=@a dynamic=mf
  bell_b: play motif=toll_ans at=@b dynamic=mf
  bell_c: play motif=toll at=@c dynamic=mf
  bell_d: play motif=toll_ans at=@d dynamic=mf
  bell_x: play motif=toll at=@x.5 dynamic=mf
  bell_y: play motif=toll_ans at=@y dynamic=mf
  fx_bell: echo time=1/4. feedback=0.5 mix=0.4 spread=0.8
  lvl_bell: gain db=14
voice heart kit_tr909 role=percussion engine=soundfont
  for sec in a b c d x y
    heart_{sec}: beat at=@{sec} bars=7 kick=x.....x......... rim=....o.......o..o dynamic=mf
    heart_{sec}7: beat at=@{sec}7 bars=1 kick=x.....x.....x. dynamic=mf
  fx_heart: filter start=1200 end=1200
  lvl_heart: gain db=26
voice clank clank role=ornament octave=5 pan=0.4
  for sec in a b c d x y
    tick_{sec}: play motif=tick at=@{sec} times=7 dynamic=mp
  fx_clank: crush rate=14000 bits=9
  lvl_clank: gain db=12

voice drums kit_rock role=percussion engine=soundfont
  d_a: beat at=@a bars=7 lanes=$THRASH dynamic=ff
  d_b: beat at=@b bars=7 lanes=$SKANK dynamic=ff
  d_c: beat at=@c bars=7 lanes=$HALF dynamic=ff
  d_d: beat at=@d bars=7 lanes=$THRASH open=..............x. dynamic=ff
  for sec in a b c d
    d_{sec}7: beat at=@{sec}7 bars=1 lanes=$SEVEN dynamic=ff
    d_crash_{sec}: beat at=@{sec} bars=1 crash=$ONE dynamic=ff
    d_crash_{sec}5: beat at=@{sec}.5 bars=1 crash=$ONE dynamic=ff
    d_stop_{sec}: cut from=@{sec}.4:4 until=@{sec}.5          -- the whole band stops for a beat, then slams back
  d_x: beat at=@x bars=7 lanes=$STOMP dynamic=f
  d_x7: beat at=@x7 bars=1 kick=x............. crash=x............. dynamic=ff
  d_crash_x: beat at=@x bars=1 crash=$ONE dynamic=ff
  d_y12: beat at=@y bars=2 kick=x...x...x...x... snare=....x.......x... dynamic=mf
  d_y34: beat at=@y.3 bars=2 kick=x...x...x...x... snare=..x...x...x...x. dynamic=f
  d_y56: beat at=@y.5 bars=2 kick=x.x.x.x.x.x.x.x. snare=x.x.x.x.x.x.x.x. dynamic=f
  d_y7: beat at=@y.7 bars=1 kick=xxxxxxxxxxxxxxxx snare=xxxxxxxxxxxxxxxx dynamic=ff
  d_y8: beat at=@y7 bars=1 kick=x...x......... snare=X...X......... crash=x...x......... dynamic=ff
  d_y8_gap: cut from=@y7:3 until=@y7.end
  d_y_swell: dynamics from=@y until=@y7 start=mp end=ff
  fx_slab: compress ratio=6 threshold=-22
  fx_room: drive amount=0.3
  fx_kick_weight: eq freq=64 gain=5 width=0.8
  fx_snare_crack: eq freq=4000 gain=3 width=1.0
  fx_cym_sheen: eq freq=8500 gain=-4 width=1.0
  for sec in b d
    d_rip_{sec}: chop in=@{sec}.6-7 slices=8 order="0 1 2 2*2 4 4*2 6*2 6*4 0 1*2 2 2*4 4*2 4*4 6*4 6*8^0>12"      -- every second phrase the kit itself is torn up before the 7/8 hit
  fx_snare_body: eq freq=190 gain=4 width=1.0
  lvl_drums: gain db=8
  feel_drums: humanize amount=0.5 timing=4
voice bass rbx_picked_bass role=bass octave=1 engine=soundfont
  bass_a1: play motif=ra1 at=@a.1 dynamic=ff
  bass_a2: play motif=ra2 at=@a.2 dynamic=ff
  bass_a3: play motif=ra1 at=@a.3 dynamic=ff
  bass_a4: play motif=ra2h at=@a.4 dynamic=ff
  bass_a5: play motif=ra1 at=@a.5 dynamic=ff
  bass_a6: play motif=ra2 at=@a.6 dynamic=ff
  bass_a7: play motif=ra1 at=@a.7 dynamic=ff
  bass_b1: play motif=rb1 at=@b.1 dynamic=ff
  bass_b2: play motif=rb2 at=@b.2 dynamic=ff
  bass_b3: play motif=rb1 at=@b.3 dynamic=ff
  bass_b4: play motif=rb2h at=@b.4 dynamic=ff
  bass_b5: play motif=rb1 at=@b.5 dynamic=ff
  bass_b6: play motif=rb2 at=@b.6 dynamic=ff
  bass_b7: play motif=rb1 at=@b.7 dynamic=ff
  bass_c1: play motif=rc1 at=@c.1 dynamic=ff
  bass_c2: play motif=rc2 at=@c.2 dynamic=ff
  bass_c3: play motif=rc1 at=@c.3 dynamic=ff
  bass_c4: play motif=rc2h at=@c.4 dynamic=ff
  bass_c5: play motif=rc1 at=@c.5 dynamic=ff
  bass_c6: play motif=rc2 at=@c.6 dynamic=ff
  bass_c7: play motif=rc1 at=@c.7 dynamic=ff
  bass_d1: play motif=ra1 at=@d.1 transpose=3 dynamic=ff
  bass_d2: play motif=ra2 at=@d.2 transpose=3 dynamic=ff
  bass_d3: play motif=ra1 at=@d.3 transpose=3 dynamic=ff
  bass_d4: play motif=ra2h at=@d.4 transpose=3 dynamic=ff
  bass_d5: play motif=ra1 at=@d.5 transpose=4 dynamic=ff
  bass_d6: play motif=ra2 at=@d.6 transpose=4 dynamic=ff
  bass_d7: play motif=rb2 at=@d.7 dynamic=ff
  bass_x1: play motif=rx1 at=@x.1 dynamic=f
  bass_x2: play motif=rx2 at=@x.2 dynamic=f
  bass_x3: play motif=rx1 at=@x.3 dynamic=f
  bass_x4: play motif=rx2 at=@x.4 dynamic=f
  bass_x5: play motif=rx1 at=@x.5 dynamic=f
  bass_x6: play motif=rx2 at=@x.6 dynamic=f
  bass_x7: play motif=rx1 at=@x.7 dynamic=f
  bass_x8: play motif=ring7 at=@x7 dynamic=ff
  bass_y1: play motif=chug at=@y.1 transpose=0 dynamic=ff
  bass_y2: play motif=chug at=@y.2 transpose=0 dynamic=ff
  bass_y3: play motif=chug at=@y.3 transpose=1 dynamic=ff
  bass_y4: play motif=chug at=@y.4 transpose=1 dynamic=ff
  bass_y5: play motif=chug at=@y.5 transpose=2 dynamic=ff
  bass_y6: play motif=chug at=@y.6 transpose=2 dynamic=ff
  bass_y7: play motif=chug7 at=@y.7 dynamic=ff
  bass_y8: play motif=hit7gap at=@y7 dynamic=ff
  bass_gap: cut from=@y7:3 until=@y7.end
  bass_a8: play motif=hit7 at=@a7 dynamic=ff
  bass_stop_a: cut from=@a.4:4 until=@a.5
  bass_b8: play motif=hit7 at=@b7 dynamic=ff
  bass_stop_b: cut from=@b.4:4 until=@b.5
  bass_c8: play motif=hit7 at=@c7 dynamic=ff
  bass_stop_c: cut from=@c.4:4 until=@c.5
  bass_d8: play motif=hit7 at=@d7 dynamic=ff
  bass_stop_d: cut from=@d.4:4 until=@d.5
  fx_bass_grit: drive amount=0.5
  fx_bass_even: compress ratio=6 threshold=-20
  fx_bass_weight: eq freq=75 gain=7 width=1.5
  lvl_bass: gain db=6
voice sub sub_bass role=bass octave=1
  sub_all: bass at=1 bars=48 pattern=pedal dynamic=f
  for sec in a b c d
    sub_stop_{sec}: cut from=@{sec}.4:4 until=@{sec}.5
  lvl_sub: gain db=15

voice gtrL amp_guitar role=harmony octave=2 pan=-0.9 engine=soundfont
  gtrL_a1: play motif=ra1 at=@a.1 dynamic=ff
  gtrL_a2: play motif=ra2 at=@a.2 dynamic=ff
  gtrL_a3: play motif=ra1 at=@a.3 dynamic=ff
  gtrL_a4: play motif=ra2h at=@a.4 dynamic=ff
  gtrL_a5: play motif=ra1 at=@a.5 dynamic=ff
  gtrL_a6: play motif=ra2 at=@a.6 dynamic=ff
  gtrL_a7: play motif=ra1 at=@a.7 dynamic=ff
  gtrL_b1: play motif=rb1 at=@b.1 dynamic=ff
  gtrL_b2: play motif=rb2 at=@b.2 dynamic=ff
  gtrL_b3: play motif=rb1 at=@b.3 dynamic=ff
  gtrL_b4: play motif=rb2h at=@b.4 dynamic=ff
  gtrL_b5: play motif=rb1 at=@b.5 dynamic=ff
  gtrL_b6: play motif=rb2 at=@b.6 dynamic=ff
  gtrL_b7: play motif=rb1 at=@b.7 dynamic=ff
  gtrL_c1: play motif=rc1 at=@c.1 dynamic=ff
  gtrL_c2: play motif=rc2 at=@c.2 dynamic=ff
  gtrL_c3: play motif=rc1 at=@c.3 dynamic=ff
  gtrL_c4: play motif=rc2h at=@c.4 dynamic=ff
  gtrL_c5: play motif=rc1 at=@c.5 dynamic=ff
  gtrL_c6: play motif=rc2 at=@c.6 dynamic=ff
  gtrL_c7: play motif=rc1 at=@c.7 dynamic=ff
  gtrL_d1: play motif=ra1 at=@d.1 transpose=3 dynamic=ff
  gtrL_d2: play motif=ra2 at=@d.2 transpose=3 dynamic=ff
  gtrL_d3: play motif=ra1 at=@d.3 transpose=3 dynamic=ff
  gtrL_d4: play motif=ra2h at=@d.4 transpose=3 dynamic=ff
  gtrL_d5: play motif=ra1 at=@d.5 transpose=4 dynamic=ff
  gtrL_d6: play motif=ra2 at=@d.6 transpose=4 dynamic=ff
  gtrL_d7: play motif=rb2 at=@d.7 dynamic=ff
  gtrL_x1: play motif=rx1 at=@x.1 dynamic=f
  gtrL_x2: play motif=rx2 at=@x.2 dynamic=f
  gtrL_x3: play motif=rx1 at=@x.3 dynamic=f
  gtrL_x4: play motif=rx2 at=@x.4 dynamic=f
  gtrL_x5: play motif=rx1 at=@x.5 dynamic=f
  gtrL_x6: play motif=rx2 at=@x.6 dynamic=f
  gtrL_x7: play motif=rx1 at=@x.7 dynamic=f
  gtrL_x8: play motif=ring7 at=@x7 dynamic=ff
  gtrL_y1: play motif=chug at=@y.1 transpose=0 dynamic=ff
  gtrL_y2: play motif=chug at=@y.2 transpose=0 dynamic=ff
  gtrL_y3: play motif=chug at=@y.3 transpose=1 dynamic=ff
  gtrL_y4: play motif=chug at=@y.4 transpose=1 dynamic=ff
  gtrL_y5: play motif=chug at=@y.5 transpose=2 dynamic=ff
  gtrL_y6: play motif=chug at=@y.6 transpose=2 dynamic=ff
  gtrL_y7: play motif=chug7 at=@y.7 dynamic=ff
  gtrL_y8: play motif=hit7gap at=@y7 dynamic=ff
  gtrL_gap: cut from=@y7:3 until=@y7.end
  gtrL_a8: play motif=hit7 at=@a7 dynamic=ff
  gtrL_stop_a: cut from=@a.4:4 until=@a.5
  gtrL_b8: play motif=hit7 at=@b7 dynamic=ff
  gtrL_stop_b: cut from=@b.4:4 until=@b.5
  gtrL_c8: play motif=hit7 at=@c7 dynamic=ff
  gtrL_stop_c: cut from=@c.4:4 until=@c.5
  gtrL_d8: play motif=hit7 at=@d7 dynamic=ff
  gtrL_stop_d: cut from=@d.4:4 until=@d.5
  fx_gl: drive amount=0.2
  fx_gl_hp: filter mode=highpass start=105 end=105
  fx_gl_wool: eq freq=260 gain=-3 width=1.0
  fx_gl_pick: eq freq=2400 gain=3 width=1.0
  fx_gl_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gl: humanize amount=0.6 timing=5 seed=1
  lvl_gl: gain db=10
voice gtrR amp_guitar role=harmony octave=2 pan=0.9 engine=soundfont
  gtrR_a1: play motif=ra1 at=@a.1 dynamic=ff
  gtrR_a2: play motif=ra2 at=@a.2 dynamic=ff
  gtrR_a3: play motif=ra1 at=@a.3 dynamic=ff
  gtrR_a4: play motif=ra2h at=@a.4 dynamic=ff
  gtrR_a5: play motif=ra1 at=@a.5 dynamic=ff
  gtrR_a6: play motif=ra2 at=@a.6 dynamic=ff
  gtrR_a7: play motif=ra1 at=@a.7 dynamic=ff
  gtrR_b1: play motif=rb1 at=@b.1 dynamic=ff
  gtrR_b2: play motif=rb2 at=@b.2 dynamic=ff
  gtrR_b3: play motif=rb1 at=@b.3 dynamic=ff
  gtrR_b4: play motif=rb2h at=@b.4 dynamic=ff
  gtrR_b5: play motif=rb1 at=@b.5 dynamic=ff
  gtrR_b6: play motif=rb2 at=@b.6 dynamic=ff
  gtrR_b7: play motif=rb1 at=@b.7 dynamic=ff
  gtrR_c1: play motif=rc1 at=@c.1 dynamic=ff
  gtrR_c2: play motif=rc2 at=@c.2 dynamic=ff
  gtrR_c3: play motif=rc1 at=@c.3 dynamic=ff
  gtrR_c4: play motif=rc2h at=@c.4 dynamic=ff
  gtrR_c5: play motif=rc1 at=@c.5 dynamic=ff
  gtrR_c6: play motif=rc2 at=@c.6 dynamic=ff
  gtrR_c7: play motif=rc1 at=@c.7 dynamic=ff
  gtrR_d1: play motif=ra1 at=@d.1 transpose=3 dynamic=ff
  gtrR_d2: play motif=ra2 at=@d.2 transpose=3 dynamic=ff
  gtrR_d3: play motif=ra1 at=@d.3 transpose=3 dynamic=ff
  gtrR_d4: play motif=ra2h at=@d.4 transpose=3 dynamic=ff
  gtrR_d5: play motif=ra1 at=@d.5 transpose=4 dynamic=ff
  gtrR_d6: play motif=ra2 at=@d.6 transpose=4 dynamic=ff
  gtrR_d7: play motif=rb2 at=@d.7 dynamic=ff
  gtrR_x1: play motif=rx1 at=@x.1 dynamic=f
  gtrR_x2: play motif=rx2 at=@x.2 dynamic=f
  gtrR_x3: play motif=rx1 at=@x.3 dynamic=f
  gtrR_x4: play motif=rx2 at=@x.4 dynamic=f
  gtrR_x5: play motif=rx1 at=@x.5 dynamic=f
  gtrR_x6: play motif=rx2 at=@x.6 dynamic=f
  gtrR_x7: play motif=rx1 at=@x.7 dynamic=f
  gtrR_x8: play motif=ring7 at=@x7 dynamic=ff
  gtrR_y1: play motif=chug at=@y.1 transpose=0 dynamic=ff
  gtrR_y2: play motif=chug at=@y.2 transpose=0 dynamic=ff
  gtrR_y3: play motif=chug at=@y.3 transpose=1 dynamic=ff
  gtrR_y4: play motif=chug at=@y.4 transpose=1 dynamic=ff
  gtrR_y5: play motif=chug at=@y.5 transpose=2 dynamic=ff
  gtrR_y6: play motif=chug at=@y.6 transpose=2 dynamic=ff
  gtrR_y7: play motif=chug7 at=@y.7 dynamic=ff
  gtrR_y8: play motif=hit7gap at=@y7 dynamic=ff
  gtrR_gap: cut from=@y7:3 until=@y7.end
  gtrR_a8: play motif=hit7 at=@a7 dynamic=ff
  gtrR_stop_a: cut from=@a.4:4 until=@a.5
  gtrR_b8: play motif=hit7 at=@b7 dynamic=ff
  gtrR_stop_b: cut from=@b.4:4 until=@b.5
  gtrR_c8: play motif=hit7 at=@c7 dynamic=ff
  gtrR_stop_c: cut from=@c.4:4 until=@c.5
  gtrR_d8: play motif=hit7 at=@d7 dynamic=ff
  gtrR_stop_d: cut from=@d.4:4 until=@d.5
  fx_gr: drive amount=0.2
  fx_gr_hp: filter mode=highpass start=105 end=105
  fx_gr_wool: eq freq=260 gain=-3 width=1.0
  fx_gr_pick: eq freq=2400 gain=3 width=1.0
  fx_gr_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gr: humanize amount=0.6 timing=7 seed=2
  lvl_gr: gain db=10
voice grind grunge_bass role=harmony octave=2 engine=soundfont
  grind_a1: play motif=ra1 at=@a.1 dynamic=ff
  grind_a2: play motif=ra2 at=@a.2 dynamic=ff
  grind_a3: play motif=ra1 at=@a.3 dynamic=ff
  grind_a4: play motif=ra2h at=@a.4 dynamic=ff
  grind_a5: play motif=ra1 at=@a.5 dynamic=ff
  grind_a6: play motif=ra2 at=@a.6 dynamic=ff
  grind_a7: play motif=ra1 at=@a.7 dynamic=ff
  grind_b1: play motif=rb1 at=@b.1 dynamic=ff
  grind_b2: play motif=rb2 at=@b.2 dynamic=ff
  grind_b3: play motif=rb1 at=@b.3 dynamic=ff
  grind_b4: play motif=rb2h at=@b.4 dynamic=ff
  grind_b5: play motif=rb1 at=@b.5 dynamic=ff
  grind_b6: play motif=rb2 at=@b.6 dynamic=ff
  grind_b7: play motif=rb1 at=@b.7 dynamic=ff
  grind_c1: play motif=rc1 at=@c.1 dynamic=ff
  grind_c2: play motif=rc2 at=@c.2 dynamic=ff
  grind_c3: play motif=rc1 at=@c.3 dynamic=ff
  grind_c4: play motif=rc2h at=@c.4 dynamic=ff
  grind_c5: play motif=rc1 at=@c.5 dynamic=ff
  grind_c6: play motif=rc2 at=@c.6 dynamic=ff
  grind_c7: play motif=rc1 at=@c.7 dynamic=ff
  grind_d1: play motif=ra1 at=@d.1 transpose=3 dynamic=ff
  grind_d2: play motif=ra2 at=@d.2 transpose=3 dynamic=ff
  grind_d3: play motif=ra1 at=@d.3 transpose=3 dynamic=ff
  grind_d4: play motif=ra2h at=@d.4 transpose=3 dynamic=ff
  grind_d5: play motif=ra1 at=@d.5 transpose=4 dynamic=ff
  grind_d6: play motif=ra2 at=@d.6 transpose=4 dynamic=ff
  grind_d7: play motif=rb2 at=@d.7 dynamic=ff
  grind_x1: play motif=rx1 at=@x.1 dynamic=f
  grind_x2: play motif=rx2 at=@x.2 dynamic=f
  grind_x3: play motif=rx1 at=@x.3 dynamic=f
  grind_x4: play motif=rx2 at=@x.4 dynamic=f
  grind_x5: play motif=rx1 at=@x.5 dynamic=f
  grind_x6: play motif=rx2 at=@x.6 dynamic=f
  grind_x7: play motif=rx1 at=@x.7 dynamic=f
  grind_x8: play motif=ring7 at=@x7 dynamic=ff
  grind_y1: play motif=chug at=@y.1 transpose=0 dynamic=ff
  grind_y2: play motif=chug at=@y.2 transpose=0 dynamic=ff
  grind_y3: play motif=chug at=@y.3 transpose=1 dynamic=ff
  grind_y4: play motif=chug at=@y.4 transpose=1 dynamic=ff
  grind_y5: play motif=chug at=@y.5 transpose=2 dynamic=ff
  grind_y6: play motif=chug at=@y.6 transpose=2 dynamic=ff
  grind_y7: play motif=chug7 at=@y.7 dynamic=ff
  grind_y8: play motif=hit7gap at=@y7 dynamic=ff
  grind_gap: cut from=@y7:3 until=@y7.end
  grind_a8: play motif=hit7 at=@a7 dynamic=ff
  grind_stop_a: cut from=@a.4:4 until=@a.5
  grind_b8: play motif=hit7 at=@b7 dynamic=ff
  grind_stop_b: cut from=@b.4:4 until=@b.5
  grind_c8: play motif=hit7 at=@c7 dynamic=ff
  grind_stop_c: cut from=@c.4:4 until=@c.5
  grind_d8: play motif=hit7 at=@d7 dynamic=ff
  grind_stop_d: cut from=@d.4:4 until=@d.5
  fx_grind: drive amount=0.9 mode=clip
  fx_grind_dark: filter start=2600 end=2600
  fx_grind_hp: filter mode=highpass start=90 end=90
  fx_grind_teeth: eq freq=1100 gain=5 width=1.2
  lvl_grind: gain db=-3

voice lead monster_lead role=melody octave=4 engine=soundfont
  l_a: play motif=theme at=@a dynamic=ff
  l_a7b: phrase at=@a.7 steps="7:1/4 r:1/4 b4:1/4 r:1/4" dynamic=ff
  l_b: play motif=zeal at=@b transpose=2 dynamic=ff
  l_b5: play motif=zeal_ans at=@b.5 dynamic=ff
  l_c: phrase at=@c steps="7:1/1 | b4:1/1 | 9:1/1 | 7:1/2. r:1/4" dynamic=ff
  l_d: play motif=theme at=@d transpose=3 dynamic=ff
  l_d5: play motif=frantic at=@d.5 transpose=4 dynamic=ff          -- the one place the theme goes berserk
  l_x: play motif=toll at=@x dynamic=ff                     -- the theme at half speed, alone above the stomp
  l_x5: play motif=zeal_ans at=@x.5 dynamic=ff
  l_y1: play motif=frantic at=@y dynamic=f
  l_y3: play motif=frantic at=@y.3 transpose=1 dynamic=ff
  l_y5: play motif=frantic at=@y.5 transpose=2 dynamic=ff
  l_y7: phrase at=@y.7 steps="4:1/8 b4 4 7 b8 7 9 11" dynamic=ff
  for sec in a b c d
    l_hit_{sec}: play motif=hit7 at=@{sec}7 dynamic=ff
    l_stop_{sec}: cut from=@{sec}.4:4 until=@{sec}.5
  l_hit_y: play motif=hit7gap at=@y7 dynamic=ff
  l_gap: cut from=@y7:3 until=@y7.end
  fx_lead: drive amount=0.4
  fx_lead_dark: filter start=3300 end=3300
  fx_lead_hp: filter mode=highpass start=180 end=180
  fx_lead_cut: eq freq=1800 gain=2 width=1.2
  lvl_lead: gain db=1
voice seq heavy_square role=counter octave=3 pan=0.3 engine=soundfont
  for sec in a b c
    s_{sec}: play motif=seq at=@{sec} times=7 dynamic=f
  s_d: play motif=seq at=@d times=7 transpose=3 dynamic=f
  s_y: play motif=seq at=@y times=7 dynamic=f
  for sec in a b c d
    s_hit_{sec}: play motif=hit7 at=@{sec}7 dynamic=ff
    s_stop_{sec}: cut from=@{sec}.4:4 until=@{sec}.5
  s_hit_y: play motif=hit7gap at=@y7 dynamic=ff
  s_gap: cut from=@y7:3 until=@y7.end
  fx_seq_hp: filter mode=highpass start=380 end=380
  fx_seq_grit: drive amount=0.7 mode=clip
  fx_seq_sweep: filter start=900 end=2200 resonance=0.4 from=@a until=@b7.end
  fx_seq_sweep2: filter start=2200 end=900 resonance=0.4 from=@c until=@d7.end
  fx_seq_sweep3: filter start=600 end=2600 resonance=0.5 from=@y until=@y7.end
  lvl_seq: gain db=2

voice machine kit_tr909 role=percussion engine=soundfont
  for sec in a b c d
    m_{sec}: beat at=@{sec} bars=2 lanes=$MANIA tune=5 dynamic=ff
    m_{sec}5: beat at=@{sec}.5 bars=3 lanes=$MANIA tune=5 dynamic=ff
    m_{sec}7: beat at=@{sec}7 bars=1 lanes=$MANIA7 tune=8 dynamic=ff
    m_roll_{sec}a: chop in=@{sec}.2-2 slices=16 order=$ROLL
    m_roll_{sec}c: chop in=@{sec}.6-7 slices=8 order="0 1 2 2*2 4*2 4*4 6*4 6*8^0>12"
  m_x: beat at=@x.5 bars=3 hat=x.x.x.x.x.x.x.x. tune=5 dynamic=mf               -- the breakdown gets only a nervous hat, then one chop
  m_x_chop: chop in=@x.7-7 slices=16 order="0 1 2 3 4*2 5*2 6*2 7*2 8*4 9*4 10*4 11*4 12*8 13*8 14*8^0>7 15*8^0>12"
  m_y: beat at=@y bars=7 lanes=$MANIA tune=5 dynamic=ff
  m_y7: beat at=@y7 bars=1 hat=x...x......... tune=8 dynamic=ff
  m_gap: cut from=@y7:3 until=@y7.end
  m_y_roll: chop in=@y.5-7 slices=8 order="0 1 2 2*2 4 4*2 6*2 6*4 0*2 1*2 2*4 2*4 4*4 4*8 6*8 6*8^0>12"
  m_y_swell: dynamics from=@y until=@y7 start=mp end=ff
  for sec in b d
    m_hole_{sec}: beat at=@{sec}.4 bars=1 snare=............xxxx tune=8 dynamic=ff
    m_ratchet_{sec}: chop in=@{sec}.4-4 slices=16 order="_ _ _ _ _ _ _ _ _ _ _ _ 12*2 13*2 14*4 15*4^0>12"
  fx_m_thin: filter mode=highpass start=300 end=300
  fx_m_teeth: eq freq=1300 gain=5 width=1.4
  fx_m_crush: crush rate=16000 bits=8
  fx_m_drive: drive amount=0.8 mode=clip
  fx_m_slab: compress ratio=8 threshold=-24
  lvl_m: gain db=4
voice siren screamer role=counter octave=5 pan=-0.3 engine=soundfont
  for sec in b d                                    # every second phrase only: every phrase wore thin on repeat
    sir_{sec}: phrase at=@{sec}.7 steps="7:1/2 b8:1/2" dynamic=f
  sir_y: phrase at=@y.5 steps="4:1/1 | 7:1/1 | b8:1/1" dynamic=f              -- a three-bar rising alarm into the return
  for sec in b d
    sir_scr_{sec}: phrase at=@{sec}7 steps="r:1/2 b11:3/8" dynamic=f
  fx_siren_lo: filter mode=highpass start=700 end=700
  fx_siren_hi: filter start=3400 end=3400
  fx_siren_edge: eq freq=3200 gain=-3 width=1.0
  lvl_siren: gain db=18
voice mob choir role=pad octave=3 engine=soundfont
  for deg in 0 4
    mob_{deg}: drone at=1 bars=48 degree={deg} dynamic=ff
  fx_mob: drive amount=1.0 mode=clip
  fx_mob_dark: filter start=2800 end=2800
  fx_mob_hp: filter mode=highpass start=250 end=250
  fx_mob_dip: eq freq=450 gain=-4 width=1.0
  fx_mob_form: eq freq=1500 gain=5 width=1.4
  lvl_mob: gain db=-8
