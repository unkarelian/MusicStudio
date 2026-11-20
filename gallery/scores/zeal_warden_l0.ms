# THE WARDEN -- boss of act 1. A jailer the size of a gatehouse: slow, swung, crushing.
# 12/8 (four dotted beats a bar) in D phrygian, chains on every beat. Layer 0 is the fight; layer 1 is its rage (below half health).

piece zeal_warden_l0 key="D minor" tempo=156 meter=12/8 style=electronic
master room.decay=2.2 room.wet=0.24 push=3

section a  bars=4 dynamic=ff
section b  bars=4 dynamic=ff
section a2 bars=4 dynamic=ff
section c  bars=4 dynamic=ff

harmony
  @a:  i5 i5 i5 bII5
  @b:  VI5 VI5 iv5 bII5
  @a2: i5 i5 i5 bII5
  @c:  i5 i5 bII5 V

motif wa1 = 0! r 0 0! r 0 b1! r b1 0! r r            -- the swing: long-short, long-short, a lean on the flat second
motif wa2 = 0! r 0 0! r 0 b4! 4 b4 2! b1 0           -- answered through the tritone
motif wa3 = 0! r 0 0! r 0 7! 6 5 b4! 2 b1            -- and a fall from the octave
motif wb1 = 5! r 5 5! r 5 4! r 4 b4! r r             -- the same swing a sixth up, sinking by half steps
motif wb2 = 2! r 2 2! r 2 b1! b1 b1 b1! b1 b1
motif wb3 = 5! r 5 4! r 4 b4! r b4 2! b1 0
motif wc1 = 0:3/8! r:3/8 0:3/8! b1:3/8!              -- the stomp: three blows and a lean
motif wc2 = b1:3/8! r:3/8 b1:3/8! b4:3/8!
motif wc3 = 0! 0 0 b1! b1 b1 b4! b4 b4 4! b4 7       -- twelve eighths straight up the wall
motif zeal = 0:3/4 b1:3/8 2:3/8 | 4:3/4 b4:3/4 | 4:3/8 b4:3/8 4:3/8 7:3/8 | 7:3/2      -- the game's theme, stretched over the swing
motif zeal_inv < zeal : invert
motif chain = 4:3/4! 4:3/4                            -- iron on beats one and three
motif knell = 0:3/2                                  -- one bell a bar

lanes DOOM
  kick:  x.x.....x...|x.x..x..x.x.
  snare: ......X.....
  bell:  x..x..x..x..
lanes DOOMFILL
  kick:  x.x.....x...
  snare: ......X..xxx
  tom_lo: .........x.x
  tom_mid: ..........x.
lanes STOMP
  kick:  x..x..x..x..
  snare: ...X.....X..
  crash: x.....x.....
lanes RAGE
  snare: .....x.....x|..x..x..x.xx
  hat:   x.xx.xx.xx.x
  open:  ..x.....x...
set ONE = "x..........."

voice drums kit_rock role=percussion engine=soundfont
  for sec in a b a2
    d_{sec}: beat at=@{sec} bars=3 lanes=$DOOM res=1/8 dynamic=ff
    d_{sec}f: beat at=@{sec}.4 bars=1 lanes=$DOOMFILL res=1/8 dynamic=ff
    d_{sec}c: beat at=@{sec} bars=1 crash=$ONE res=1/8 dynamic=ff
  d_c: beat at=@c bars=3 lanes=$STOMP res=1/8 dynamic=ff
  d_c4: beat at=@c.4 bars=1 kick=xxxxxxxxxxxx snare=x..x..x..xxx tom_lo=.x..x..x.... res=1/8 dynamic=ff
  fx_slab: compress ratio=6 threshold=-22
  fx_room: drive amount=0.3
  fx_kick_weight: eq freq=64 gain=5 width=0.8
  fx_snare_body: eq freq=190 gain=4 width=1.0
  fx_snare_crack: eq freq=4000 gain=3 width=1.0
  fx_cym_sheen: eq freq=8500 gain=-4 width=1.0
  lvl_drums: gain db=8
  feel_drums: humanize amount=0.5 timing=4
voice bass rbx_picked_bass role=bass octave=1 engine=soundfont
  bass_a1: play motif=wa1 at=@a.1 dynamic=ff
  bass_a2: play motif=wa2 at=@a.2 dynamic=ff
  bass_a3: play motif=wa1 at=@a.3 dynamic=ff
  bass_a4: play motif=wa3 at=@a.4 dynamic=ff
  bass_b1: play motif=wb1 at=@b.1 dynamic=ff
  bass_b2: play motif=wb2 at=@b.2 dynamic=ff
  bass_b3: play motif=wb1 at=@b.3 dynamic=ff
  bass_b4: play motif=wb3 at=@b.4 dynamic=ff
  bass_a21: play motif=wa1 at=@a2.1 dynamic=ff
  bass_a22: play motif=wa2 at=@a2.2 dynamic=ff
  bass_a23: play motif=wa1 at=@a2.3 dynamic=ff
  bass_a24: play motif=wa3 at=@a2.4 dynamic=ff
  bass_c1: play motif=wc1 at=@c.1 dynamic=ff
  bass_c2: play motif=wc1 at=@c.2 dynamic=ff
  bass_c3: play motif=wc2 at=@c.3 dynamic=ff
  bass_c4: play motif=wc3 at=@c.4 dynamic=ff
  fx_bass_grit: drive amount=0.5
  fx_bass_even: compress ratio=6 threshold=-20
  fx_bass_weight: eq freq=75 gain=7 width=1.5
  lvl_bass: gain db=6
voice sub sub_bass role=bass octave=1
  sub_all: bass at=1 bars=16 pattern=pedal dynamic=f
  lvl_sub: gain db=15
voice gtrL amp_guitar role=harmony octave=2 pan=-0.9 engine=soundfont
  gtrL_a1: play motif=wa1 at=@a.1 dynamic=ff
  gtrL_a2: play motif=wa2 at=@a.2 dynamic=ff
  gtrL_a3: play motif=wa1 at=@a.3 dynamic=ff
  gtrL_a4: play motif=wa3 at=@a.4 dynamic=ff
  gtrL_b1: play motif=wb1 at=@b.1 dynamic=ff
  gtrL_b2: play motif=wb2 at=@b.2 dynamic=ff
  gtrL_b3: play motif=wb1 at=@b.3 dynamic=ff
  gtrL_b4: play motif=wb3 at=@b.4 dynamic=ff
  gtrL_a21: play motif=wa1 at=@a2.1 dynamic=ff
  gtrL_a22: play motif=wa2 at=@a2.2 dynamic=ff
  gtrL_a23: play motif=wa1 at=@a2.3 dynamic=ff
  gtrL_a24: play motif=wa3 at=@a2.4 dynamic=ff
  gtrL_c1: play motif=wc1 at=@c.1 dynamic=ff
  gtrL_c2: play motif=wc1 at=@c.2 dynamic=ff
  gtrL_c3: play motif=wc2 at=@c.3 dynamic=ff
  gtrL_c4: play motif=wc3 at=@c.4 dynamic=ff
  fx_gl: drive amount=0.2
  fx_gl_hp: filter mode=highpass start=105 end=105
  fx_gl_wool: eq freq=260 gain=-3 width=1.0
  fx_gl_pick: eq freq=2400 gain=3 width=1.0
  fx_gl_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gl: humanize amount=0.6 timing=6 seed=1
  lvl_gl: gain db=10
voice gtrR amp_guitar role=harmony octave=2 pan=0.9 engine=soundfont
  gtrR_a1: play motif=wa1 at=@a.1 dynamic=ff
  gtrR_a2: play motif=wa2 at=@a.2 dynamic=ff
  gtrR_a3: play motif=wa1 at=@a.3 dynamic=ff
  gtrR_a4: play motif=wa3 at=@a.4 dynamic=ff
  gtrR_b1: play motif=wb1 at=@b.1 dynamic=ff
  gtrR_b2: play motif=wb2 at=@b.2 dynamic=ff
  gtrR_b3: play motif=wb1 at=@b.3 dynamic=ff
  gtrR_b4: play motif=wb3 at=@b.4 dynamic=ff
  gtrR_a21: play motif=wa1 at=@a2.1 dynamic=ff
  gtrR_a22: play motif=wa2 at=@a2.2 dynamic=ff
  gtrR_a23: play motif=wa1 at=@a2.3 dynamic=ff
  gtrR_a24: play motif=wa3 at=@a2.4 dynamic=ff
  gtrR_c1: play motif=wc1 at=@c.1 dynamic=ff
  gtrR_c2: play motif=wc1 at=@c.2 dynamic=ff
  gtrR_c3: play motif=wc2 at=@c.3 dynamic=ff
  gtrR_c4: play motif=wc3 at=@c.4 dynamic=ff
  fx_gr: drive amount=0.2
  fx_gr_hp: filter mode=highpass start=105 end=105
  fx_gr_wool: eq freq=260 gain=-3 width=1.0
  fx_gr_pick: eq freq=2400 gain=3 width=1.0
  fx_gr_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gr: humanize amount=0.6 timing=8 seed=2
  lvl_gr: gain db=10
voice grind grunge_bass role=harmony octave=2 engine=soundfont
  grind_a1: play motif=wa1 at=@a.1 dynamic=ff
  grind_a2: play motif=wa2 at=@a.2 dynamic=ff
  grind_a3: play motif=wa1 at=@a.3 dynamic=ff
  grind_a4: play motif=wa3 at=@a.4 dynamic=ff
  grind_b1: play motif=wb1 at=@b.1 dynamic=ff
  grind_b2: play motif=wb2 at=@b.2 dynamic=ff
  grind_b3: play motif=wb1 at=@b.3 dynamic=ff
  grind_b4: play motif=wb3 at=@b.4 dynamic=ff
  grind_a21: play motif=wa1 at=@a2.1 dynamic=ff
  grind_a22: play motif=wa2 at=@a2.2 dynamic=ff
  grind_a23: play motif=wa1 at=@a2.3 dynamic=ff
  grind_a24: play motif=wa3 at=@a2.4 dynamic=ff
  grind_c1: play motif=wc1 at=@c.1 dynamic=ff
  grind_c2: play motif=wc1 at=@c.2 dynamic=ff
  grind_c3: play motif=wc2 at=@c.3 dynamic=ff
  grind_c4: play motif=wc3 at=@c.4 dynamic=ff
  fx_grind: drive amount=0.9 mode=clip
  fx_grind_dark: filter start=2600 end=2600
  fx_grind_hp: filter mode=highpass start=90 end=90
  fx_grind_teeth: eq freq=1100 gain=5 width=1.2
  lvl_grind: gain db=-3
voice chains clank role=ornament octave=5 pan=0.35
  ch_all: play motif=chain at=1 times=16 dynamic=f
  fx_chain: crush rate=12000 bits=8
  fx_chain_dark: filter start=2800 end=2800
  lvl_chain: gain db=9
voice bell fm_bells role=ornament octave=3 pan=-0.3 engine=soundfont
  for sec in a a2
    bell_{sec}: play motif=knell at=@{sec} times=4 dynamic=ff
  fx_bell: echo time=3/8 feedback=0.4 mix=0.3 spread=0.7
  lvl_bell: gain db=10
voice mob choir role=pad octave=3 engine=soundfont
  for deg in 0 4
    mob_{deg}: drone at=@b bars=4 degree={deg} dynamic=ff
    mobc_{deg}: drone at=@c bars=4 degree={deg} dynamic=ff
  fx_mob: drive amount=1.0 mode=clip
  fx_mob_dark: filter start=2800 end=2800
  fx_mob_hp: filter mode=highpass start=250 end=250
  fx_mob_dip: eq freq=450 gain=-4 width=1.0
  fx_mob_form: eq freq=1500 gain=5 width=1.4
  lvl_mob: gain db=-6

