# ZEAL — combat loop, written as five stacked layers for the game to mix by zeal.
# 176 BPM, E phrygian with a tritone. Each 8-bar phrase is seven bars of 4/4 and one of 7/8,
# so the loop lurches forward an eighth early every phrase. Four phrases of assault (a b c d), then a
# breakdown (x: half-time, stripped, the theme alone) and a build (y) that climbs back into a. 48 bars = 189 beats.
# `# @layer N` lines split this file into per-layer scores (tools/music.py); built whole it is the full mix.

piece zeal_l3 key="E minor" tempo=176 style=electronic
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

