# THE CHOIR -- boss of act 2. Many mouths, one chant, in five. 200 BPM, 5/4 counted 3+3+2+2, C phrygian.
# Layer 0: the chant over a break and an acid bass. Layer 1 (rage): a real kit blasting under it, guitars, the theme screamed.

piece zeal_choir_l1 key="C minor" tempo=200 meter=5/4 style=electronic
master room.decay=2.6 room.wet=0.26 push=3

section a bars=8 dynamic=f
section b bars=8 dynamic=ff
section c bars=8 dynamic=ff

harmony
  @a: i i bII bII i i bVI bII
  @b: iv iv i i bII bII V V
  @c: i bII i bII bVI bVI bII V

# the chant: 3+3+2+2 in eighths, three parts
motif ch_s = 7:3/8! 7:3/8! b8:1/4! 7:1/4!
motif ch_a = 4:3/8! 4:3/8! 5:1/4! 4:1/4!
motif ch_t = 2:3/8! 2:3/8! 2:1/4! 2:1/4!
motif ch_s2 = b8:3/8! b8:3/8! 9:1/4! b8:1/4!        -- the same chant a half step higher: the flat second as a place to stand
motif ch_a2 = 5:3/8! 5:3/8! 5:1/4! 5:1/4!
motif ch_t2 = b1:3/8! b1:3/8! 3:1/4! b1:1/4!
motif zeal = 0:1/4. b1:1/8 2:1/4 4:1/2 | b4:1/4. 4:1/8 7:3/4           -- the game's theme, bent into five
motif zeal_ans = 7:1/4. 6:1/8 5:1/4 b4:1/2 | 4:1/4. 2:1/8 b1:3/4
motif theme < zeal : then:zeal_ans
motif acid = 0! 0 7 0! 0 7 b1! 7 0! 7                                   -- the bass: octaves jumping on the chant's accents
motif acid2 = b1! b1 b8 b1! b1 b8 0! 7 b4! 4
motif glasse = 0 4 7 9 7 4 0 4 7 11 9 7 4 7 9 7 4 2 4 7
motif glass < glasse : diminish:2                                      -- twenty sixteenths of bells

lanes BREAK
  kick:  x.....x...x.......x.|x.....x...x...x.....
  snare: ....X.......X...X...|....X..o....X...X.oo
  hat:   x.x.x.x.x.x.x.x.x.x.
  open:  ..........x.........
lanes BLAST
  kick:  x.xx..x.xx..x.x.x.x.
  snare: ......X.....X...X...
  tom_lo: ....xx....xx........
  crash: x...................
lanes BLAST2
  kick:  x.....x.....x...x...
  snare: ............X.......
set ROLL = "0 1 2 3 4 5 6*2 7*2 8 9 10*2 11*2 12*4 13*4 14*4 15*4 16*4^0>7 17*4^0>7 18*8^0>12 19*8^0>12"

voice drums kit_rock role=percussion engine=soundfont
  d_a: beat at=@a bars=8 lanes=$BLAST dynamic=ff
  d_b: beat at=@b bars=8 lanes=$BLAST2 dynamic=ff
  d_c: beat at=@c bars=8 lanes=$BLAST dynamic=ff
  for sec in a c
    d_rip_{sec}: chop in=@{sec}.8-8 slices=10 order="0 1 2*2 3*2 4 5*2 6*4 7*4 8*4 9*8^0>12"
  fx_slab: compress ratio=6 threshold=-22
  fx_room: drive amount=0.3
  fx_kick_weight: eq freq=64 gain=5 width=0.8
  fx_snare_body: eq freq=190 gain=4 width=1.0
  fx_snare_crack: eq freq=4000 gain=3 width=1.0
  fx_cym_sheen: eq freq=8500 gain=-4 width=1.0
  lvl_drums: gain db=8
  feel_drums: humanize amount=0.5 timing=4
voice gtrL amp_guitar role=harmony octave=3 pan=-0.9 engine=soundfont
  for sec in a c
    for bar in 1 2 5 6
      gtrL_{sec}{bar}: play motif=acid at=@{sec}.{bar} dynamic=ff
    for bar in 3 4 7 8
      gtrL_{sec}{bar}: play motif=acid2 at=@{sec}.{bar} dynamic=ff
  fx_gl: drive amount=0.2
  fx_gl_hp: filter mode=highpass start=105 end=105
  fx_gl_wool: eq freq=260 gain=-3 width=1.0
  fx_gl_pick: eq freq=2400 gain=3 width=1.0
  fx_gl_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gl: humanize amount=0.6 timing=6 seed=1
  lvl_gl: gain db=5
voice gtrR amp_guitar role=harmony octave=3 pan=0.9 engine=soundfont
  for sec in a c
    for bar in 1 2 5 6
      gtrR_{sec}{bar}: play motif=acid at=@{sec}.{bar} dynamic=ff
    for bar in 3 4 7 8
      gtrR_{sec}{bar}: play motif=acid2 at=@{sec}.{bar} dynamic=ff
  fx_gr: drive amount=0.2
  fx_gr_hp: filter mode=highpass start=105 end=105
  fx_gr_wool: eq freq=260 gain=-3 width=1.0
  fx_gr_pick: eq freq=2400 gain=3 width=1.0
  fx_gr_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gr: humanize amount=0.6 timing=8 seed=2
  lvl_gr: gain db=5
voice lead monster_lead role=melody octave=4 engine=soundfont
  l_a: play motif=theme at=@a dynamic=ff
  l_a5: play motif=theme at=@a.5 transpose=2 dynamic=ff
  l_c: play motif=theme at=@c octave=5 dynamic=ff
  l_c5: play motif=theme at=@c.5 octave=5 transpose=2 dynamic=ff
  fx_lead: drive amount=0.4
  fx_lead_dark: filter start=4200 end=4200
  fx_lead_hp: filter mode=highpass start=180 end=180
  fx_lead_cut: eq freq=1800 gain=2 width=1.2
  lvl_lead: gain db=-1
