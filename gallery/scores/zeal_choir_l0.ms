# THE CHOIR -- boss of act 2. Many mouths, one chant, in five. 200 BPM, 5/4 counted 3+3+2+2, C phrygian.
# Layer 0: the chant over a break and an acid bass. Layer 1 (rage): a real kit blasting under it, guitars, the theme screamed.

piece zeal_choir_l0 key="C minor" tempo=200 meter=5/4 style=electronic
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

voice sop choir role=melody octave=4 pan=-0.4 engine=soundfont
  for bar in 1 2 5 6
    sop_a{bar}: play motif=ch_s at=@a.{bar} dynamic=ff
    sop_c{bar}: play motif=ch_s at=@c.{bar} dynamic=ff
  for bar in 3 4 7 8
    sop_a{bar}: play motif=ch_s2 at=@a.{bar} dynamic=ff
    sop_c{bar}: play motif=ch_s2 at=@c.{bar} dynamic=ff
  sop_b: play motif=theme at=@b dynamic=ff
  sop_b5: play motif=theme at=@b.5 transpose=1 dynamic=ff
  fx_sop: drive amount=0.6 mode=clip
  fx_sop_hp: filter mode=highpass start=300 end=300
  fx_sop_form: eq freq=1600 gain=5 width=1.4
  lvl_sop: gain db=2
voice alt choir role=harmony octave=4 pan=0.4 engine=soundfont
  for sec in a b c
    for bar in 1 2 5 6
      alt_{sec}{bar}: play motif=ch_a at=@{sec}.{bar} dynamic=ff
    for bar in 3 4 7 8
      alt_{sec}{bar}: play motif=ch_a2 at=@{sec}.{bar} dynamic=ff
  fx_alt: drive amount=0.6 mode=clip
  fx_alt_hp: filter mode=highpass start=280 end=280
  lvl_alt: gain db=0
voice ten choir role=harmony octave=3 engine=soundfont
  for sec in a b c
    for bar in 1 2 5 6
      ten_{sec}{bar}: play motif=ch_t at=@{sec}.{bar} dynamic=ff
    for bar in 3 4 7 8
      ten_{sec}{bar}: play motif=ch_t2 at=@{sec}.{bar} dynamic=ff
  fx_ten: drive amount=0.8 mode=clip
  fx_ten_hp: filter mode=highpass start=220 end=220
  lvl_ten: gain db=0
voice brk kit_tr909 role=percussion engine=soundfont
  for sec in a b c
    brk_{sec}: beat at=@{sec} bars=8 lanes=$BREAK tune=3 dynamic=ff
    brk_chop_{sec}4: chop in=@{sec}.4-4 slices=20 order=$ROLL
    brk_chop_{sec}8: chop in=@{sec}.7-8 slices=10 order="0 1 2 2*2 4 4*2 6*2 6*4 8*4 8*8^0>12"
  fx_brk_crush: crush rate=18000 bits=9
  fx_brk_drive: drive amount=0.7 mode=clip
  fx_brk_slab: compress ratio=8 threshold=-24
  fx_brk_weight: eq freq=62 gain=6 width=1.0
  lvl_brk: gain db=6
voice acidb acid_sub_bass role=bass octave=1 engine=soundfont
  for sec in a b c
    for bar in 1 2 5 6
      ac_{sec}{bar}: play motif=acid at=@{sec}.{bar} dynamic=ff
    for bar in 3 4 7 8
      ac_{sec}{bar}: play motif=acid2 at=@{sec}.{bar} dynamic=ff
  fx_acid: drive amount=0.8 mode=clip
  fx_acid_sweep: filter start=500 end=2400 resonance=0.6 from=@a until=@b.end
  fx_acid_sweep2: filter start=2400 end=500 resonance=0.6 from=@c until=@c.end
  lvl_acid: gain db=4
voice sub sub_bass role=bass octave=1
  sub_all: bass at=1 bars=24 pattern=pedal dynamic=f
  lvl_sub: gain db=14
voice glassv fm_bells role=ornament octave=5 pan=0.2 engine=soundfont
  gl_b: play motif=glass at=@b times=8 dynamic=mf
  gl_c: play motif=glass at=@c.5 times=4 transpose=2 dynamic=mf
  fx_glass: echo time=1/8. feedback=0.35 mix=0.3 spread=0.9
  lvl_glass: gain db=4

