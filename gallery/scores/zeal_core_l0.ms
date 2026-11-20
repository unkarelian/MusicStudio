# THE HELL CORE -- the last fight. The combat track's 7/8 lurch becomes the whole meter (2+2+3), in the
# same key, and the game's theme is finally played whole by the band. 188 BPM, E phrygian.
# Layer 0: the band and the theme, kept lean. Layer 1 (rage): the grinding synth bass, drum machine, choir, siren, the theme an octave up.

piece zeal_core_l0 key="E minor" tempo=188 meter=7/8 style=electronic
master room.decay=1.6 room.wet=0.18 push=3

section a bars=8 dynamic=ff
section b bars=8 dynamic=ff
section c bars=8 dynamic=ff
section d bars=8 dynamic=ff

harmony
  @a: i5 i5 i5 bII5 i5 i5 VI5 bII5
  @b: i5 i5 VI5 VI5 iv5 iv5 bII5 V
  @c: i5 bII5 i5 bII5 VI5 VII5 i5 bII5
  @d: iv5 iv5 iv5 iv5 v5 v5 v5 V

motif hc1e = 0! 0 b1 0 0! 0 2 0 0! b1 b4 4 b4 2          -- fourteen sixteenths: 4+4+6, the tail through the tritone
motif hc2e = 0! 0 b1 0 0! 0 2 0 7! 6 b4 4 b1 0
motif hp1e = 0! 0 7 0 0! 0 6 0 0! 0 5 b4 4 2             -- pedal point, the top voice falling
motif hp2e = 0! 0 5 0 0! 0 4 0 b1! b1 b4 b4 2 b1
motif hc1 < hc1e : diminish:2
motif hc2 < hc2e : diminish:2
motif hp1 < hp1e : diminish:2
motif hp2 < hp2e : diminish:2
motif hstomp = 0! r 0! r 0! 0 b1                         -- under the theme: 2+2+3 and nothing else
motif hend = 0! r 0! r b4! b4! b4!                       -- the unison hit that ended every phrase of the combat track
motif zeal = 0:1/4 b1:1/8 2:1/4 4:1/4 | b4:1/4 4:1/8 7:1/2          -- the theme in seven
motif zeal_ans = 7:1/4 6:1/8 5:1/4 b4:1/4 | 4:1/4 2:1/8 b1:1/2
motif theme < zeal : then:zeal_ans
motif theme_up < theme : transpose:2
motif frantic < theme : diminish:2
motif seqe = 0! r 0 0 r 0 b1 r 0! r 7 r 0 b4
motif seq < seqe : diminish:2

lanes SEVEN
  kick:  x.xx..x.x.x.xx
  snare: ....X.....X...
  hat:   x.x.x.x.x.x.x.
lanes PEDAL
  kick:  x.xxx.xxx.xxxx
  snare: ..X...X...X.X.
  ride:  x.x.x.x.x.x.x.
lanes HALF
  kick:  x.....x...x...|x..x..x...x.xx
  snare: ........X.....
  crash: x.............
lanes BLAST
  kick:  xxxxxxxxxxxxxx
  snare: x.x.x.x.x.x.x.
  ride:  x...x...x.x.x.
lanes END
  kick:  x...x...x.x.x.
  snare: X...X...X.X.X.
  crash: x...x.........
lanes MANIA
  snare: ......x.......|..........xxxx
  hat:   xxxxxxxxxxxxxx
  open:  ..x...x...x...
set ONE = "x............."

voice drums kit_rock role=percussion engine=soundfont
  d_a: beat at=@a bars=7 lanes=$SEVEN dynamic=ff
  d_b: beat at=@b bars=7 lanes=$PEDAL dynamic=ff
  d_c: beat at=@c bars=7 lanes=$HALF dynamic=ff
  d_d: beat at=@d bars=7 lanes=$BLAST dynamic=ff
  for sec in a b c d
    d_end_{sec}: beat at=@{sec}.8 bars=1 lanes=$END dynamic=ff
    d_crash_{sec}: beat at=@{sec} bars=1 crash=$ONE dynamic=ff
  for sec in b d
    d_rip_{sec}: chop in=@{sec}.6-7 slices=7 order="0 1 2*2 3*2 4*2 5*4 6*4 0 1*2 2*2 3*4 4*4 5*8 6*8^0>12"
  fx_slab: compress ratio=6 threshold=-22
  fx_room: drive amount=0.3
  fx_kick_weight: eq freq=64 gain=5 width=0.8
  fx_snare_body: eq freq=190 gain=4 width=1.0
  fx_snare_crack: eq freq=4000 gain=3 width=1.0
  fx_cym_sheen: eq freq=8500 gain=-4 width=1.0
  lvl_drums: gain db=8
  feel_drums: humanize amount=0.5 timing=4
voice bass rbx_picked_bass role=bass octave=1 engine=soundfont
  bass_a1: play motif=hc1 at=@a.1 dynamic=ff
  bass_a2: play motif=hc2 at=@a.2 dynamic=ff
  bass_a3: play motif=hc1 at=@a.3 dynamic=ff
  bass_a4: play motif=hc2 at=@a.4 dynamic=ff
  bass_a5: play motif=hc1 at=@a.5 dynamic=ff
  bass_a6: play motif=hc2 at=@a.6 dynamic=ff
  bass_a7: play motif=hc1 at=@a.7 dynamic=ff
  bass_a8: play motif=hend at=@a.8 dynamic=ff
  bass_b1: play motif=hp1 at=@b.1 dynamic=ff
  bass_b2: play motif=hp2 at=@b.2 dynamic=ff
  bass_b3: play motif=hp1 at=@b.3 dynamic=ff
  bass_b4: play motif=hp2 at=@b.4 dynamic=ff
  bass_b5: play motif=hp1 at=@b.5 dynamic=ff
  bass_b6: play motif=hp2 at=@b.6 dynamic=ff
  bass_b7: play motif=hp1 at=@b.7 dynamic=ff
  bass_b8: play motif=hend at=@b.8 dynamic=ff
  bass_d1: play motif=hc1 at=@d.1 transpose=3 dynamic=ff
  bass_d2: play motif=hc2 at=@d.2 transpose=3 dynamic=ff
  bass_d3: play motif=hc1 at=@d.3 transpose=3 dynamic=ff
  bass_d4: play motif=hc2 at=@d.4 transpose=3 dynamic=ff
  bass_d5: play motif=hc1 at=@d.5 transpose=3 dynamic=ff
  bass_d6: play motif=hc2 at=@d.6 transpose=3 dynamic=ff
  bass_d7: play motif=hc1 at=@d.7 transpose=3 dynamic=ff
  bass_d8: play motif=hend at=@d.8 dynamic=ff
  bass_c1: play motif=hstomp at=@c.1 dynamic=ff
  bass_c2: play motif=hstomp at=@c.2 dynamic=ff
  bass_c3: play motif=hstomp at=@c.3 dynamic=ff
  bass_c4: play motif=hstomp at=@c.4 dynamic=ff
  bass_c5: play motif=hstomp at=@c.5 dynamic=ff
  bass_c6: play motif=hstomp at=@c.6 dynamic=ff
  bass_c7: play motif=hstomp at=@c.7 dynamic=ff
  bass_c8: play motif=hend at=@c.8 dynamic=ff
  fx_bass_grit: drive amount=0.5
  fx_bass_even: compress ratio=6 threshold=-20
  fx_bass_weight: eq freq=75 gain=7 width=1.5
  lvl_bass: gain db=6
voice sub sub_bass role=bass octave=1
  sub_all: bass at=1 bars=32 pattern=pedal dynamic=f
  lvl_sub: gain db=15
voice gtrL amp_guitar role=harmony octave=2 pan=-0.9 engine=soundfont
  gtrL_a1: play motif=hc1 at=@a.1 dynamic=ff
  gtrL_a2: play motif=hc2 at=@a.2 dynamic=ff
  gtrL_a3: play motif=hc1 at=@a.3 dynamic=ff
  gtrL_a4: play motif=hc2 at=@a.4 dynamic=ff
  gtrL_a5: play motif=hc1 at=@a.5 dynamic=ff
  gtrL_a6: play motif=hc2 at=@a.6 dynamic=ff
  gtrL_a7: play motif=hc1 at=@a.7 dynamic=ff
  gtrL_a8: play motif=hend at=@a.8 dynamic=ff
  gtrL_b1: play motif=hp1 at=@b.1 dynamic=ff
  gtrL_b2: play motif=hp2 at=@b.2 dynamic=ff
  gtrL_b3: play motif=hp1 at=@b.3 dynamic=ff
  gtrL_b4: play motif=hp2 at=@b.4 dynamic=ff
  gtrL_b5: play motif=hp1 at=@b.5 dynamic=ff
  gtrL_b6: play motif=hp2 at=@b.6 dynamic=ff
  gtrL_b7: play motif=hp1 at=@b.7 dynamic=ff
  gtrL_b8: play motif=hend at=@b.8 dynamic=ff
  gtrL_d1: play motif=hc1 at=@d.1 transpose=3 dynamic=ff
  gtrL_d2: play motif=hc2 at=@d.2 transpose=3 dynamic=ff
  gtrL_d3: play motif=hc1 at=@d.3 transpose=3 dynamic=ff
  gtrL_d4: play motif=hc2 at=@d.4 transpose=3 dynamic=ff
  gtrL_d5: play motif=hc1 at=@d.5 transpose=3 dynamic=ff
  gtrL_d6: play motif=hc2 at=@d.6 transpose=3 dynamic=ff
  gtrL_d7: play motif=hc1 at=@d.7 transpose=3 dynamic=ff
  gtrL_d8: play motif=hend at=@d.8 dynamic=ff
  gtrL_c1: play motif=hstomp at=@c.1 dynamic=ff
  gtrL_c2: play motif=hstomp at=@c.2 dynamic=ff
  gtrL_c3: play motif=hstomp at=@c.3 dynamic=ff
  gtrL_c4: play motif=hstomp at=@c.4 dynamic=ff
  gtrL_c5: play motif=hstomp at=@c.5 dynamic=ff
  gtrL_c6: play motif=hstomp at=@c.6 dynamic=ff
  gtrL_c7: play motif=hstomp at=@c.7 dynamic=ff
  gtrL_c8: play motif=hend at=@c.8 dynamic=ff
  fx_gl: drive amount=0.2
  fx_gl_hp: filter mode=highpass start=105 end=105
  fx_gl_wool: eq freq=260 gain=-3 width=1.0
  fx_gl_pick: eq freq=2400 gain=3 width=1.0
  fx_gl_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gl: humanize amount=0.6 timing=6 seed=1
  lvl_gl: gain db=8
voice gtrR amp_guitar role=harmony octave=2 pan=0.9 engine=soundfont
  gtrR_a1: play motif=hc1 at=@a.1 dynamic=ff
  gtrR_a2: play motif=hc2 at=@a.2 dynamic=ff
  gtrR_a3: play motif=hc1 at=@a.3 dynamic=ff
  gtrR_a4: play motif=hc2 at=@a.4 dynamic=ff
  gtrR_a5: play motif=hc1 at=@a.5 dynamic=ff
  gtrR_a6: play motif=hc2 at=@a.6 dynamic=ff
  gtrR_a7: play motif=hc1 at=@a.7 dynamic=ff
  gtrR_a8: play motif=hend at=@a.8 dynamic=ff
  gtrR_b1: play motif=hp1 at=@b.1 dynamic=ff
  gtrR_b2: play motif=hp2 at=@b.2 dynamic=ff
  gtrR_b3: play motif=hp1 at=@b.3 dynamic=ff
  gtrR_b4: play motif=hp2 at=@b.4 dynamic=ff
  gtrR_b5: play motif=hp1 at=@b.5 dynamic=ff
  gtrR_b6: play motif=hp2 at=@b.6 dynamic=ff
  gtrR_b7: play motif=hp1 at=@b.7 dynamic=ff
  gtrR_b8: play motif=hend at=@b.8 dynamic=ff
  gtrR_d1: play motif=hc1 at=@d.1 transpose=3 dynamic=ff
  gtrR_d2: play motif=hc2 at=@d.2 transpose=3 dynamic=ff
  gtrR_d3: play motif=hc1 at=@d.3 transpose=3 dynamic=ff
  gtrR_d4: play motif=hc2 at=@d.4 transpose=3 dynamic=ff
  gtrR_d5: play motif=hc1 at=@d.5 transpose=3 dynamic=ff
  gtrR_d6: play motif=hc2 at=@d.6 transpose=3 dynamic=ff
  gtrR_d7: play motif=hc1 at=@d.7 transpose=3 dynamic=ff
  gtrR_d8: play motif=hend at=@d.8 dynamic=ff
  gtrR_c1: play motif=hstomp at=@c.1 dynamic=ff
  gtrR_c2: play motif=hstomp at=@c.2 dynamic=ff
  gtrR_c3: play motif=hstomp at=@c.3 dynamic=ff
  gtrR_c4: play motif=hstomp at=@c.4 dynamic=ff
  gtrR_c5: play motif=hstomp at=@c.5 dynamic=ff
  gtrR_c6: play motif=hstomp at=@c.6 dynamic=ff
  gtrR_c7: play motif=hstomp at=@c.7 dynamic=ff
  gtrR_c8: play motif=hend at=@c.8 dynamic=ff
  fx_gr: drive amount=0.2
  fx_gr_hp: filter mode=highpass start=105 end=105
  fx_gr_wool: eq freq=260 gain=-3 width=1.0
  fx_gr_pick: eq freq=2400 gain=3 width=1.0
  fx_gr_fizz: eq freq=6500 gain=-5 width=1.0
  feel_gr: humanize amount=0.6 timing=8 seed=2
  lvl_gr: gain db=8
voice lead monster_lead role=melody octave=4 engine=soundfont
  l_a: play motif=zeal at=@a.5 dynamic=ff
  l_b: play motif=zeal_ans at=@b.5 dynamic=ff
  l_c: play motif=theme at=@c dynamic=ff
  l_c5: play motif=theme_up at=@c.5 dynamic=ff
  l_d: play motif=frantic at=@d times=2 transpose=3 dynamic=ff
  l_d5: play motif=frantic at=@d.5 transpose=3 dynamic=ff
  l_d7: phrase at=@d.7 steps="7:1/4 9:1/8 11:1/2" dynamic=ff
  for sec in a b c d
    l_end_{sec}: play motif=hend at=@{sec}.8 dynamic=ff
  fx_lead: drive amount=0.4
  fx_lead_dark: filter start=4200 end=4200
  fx_lead_hp: filter mode=highpass start=180 end=180
  fx_lead_cut: eq freq=1800 gain=2 width=1.2
  lvl_lead: gain db=3
voice harm monster_lead role=counter octave=4 pan=0.3 engine=soundfont
  h_c: double source=lead interval=2 from=@c until=@c.8 dynamic=f
  fx_harm: drive amount=0.4
  fx_harm_dark: filter start=4200 end=4200
  fx_harm_hp: filter mode=highpass start=180 end=180
  fx_harm_cut: eq freq=1800 gain=2 width=1.2
  lvl_harm: gain db=0
voice bell fm_bells role=ornament octave=4 pan=-0.3 engine=soundfont
  for sec in a b c d
    bell_{sec}: phrase at=@{sec} steps="0:7/8" dynamic=ff
    bell_{sec}5: phrase at=@{sec}.5 steps="b1:7/8" dynamic=ff
  fx_bell: echo time=1/4. feedback=0.45 mix=0.35 spread=0.8
  lvl_bell: gain db=10

