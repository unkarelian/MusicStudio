# ZEAL — combat loop, written as five stacked layers for the game to mix by zeal.
# 176 BPM, E phrygian with a tritone. Each 8-bar phrase is seven bars of 4/4 and one of 7/8,
# so the loop lurches forward an eighth early every phrase. Four phrases of assault (a b c d), then a
# breakdown (x: half-time, stripped, the theme alone) and a build (y) that climbs back into a. 48 bars = 189 beats.
# `# @layer N` lines split this file into per-layer scores (tools/music.py); built whole it is the full mix.

piece zeal_l4 key="E minor" tempo=176 style=electronic
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
