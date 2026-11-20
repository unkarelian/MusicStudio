# Olympia B2-29: Cole against Hermes on the Hall steps; one hit; then the telling of the arm, on a piano, badly and plainly.
piece olympia_b2_29_what_he_knew key="G minor" tempo=76 style=orchestral
master room.decay=2.4 room.wet=0.24
meta title = "What He Knew"
meta soundfont = "hq"

section steps   bars=8  meter=4/4 dynamic=mp
section hit     bars=2  meter=4/4 dynamic=ff
section telling bars=10 meter=4/4 dynamic=pp tempo=56
section sink    bars=3  meter=4/4 dynamic=pp tempo=56 tempo_end=48

harmony
  @steps:   i . v i | iv . V .
  @hit:     i .
  @telling: i . VI . iv . | i . VI VII
  @sink:    iv . i

# -- the Olympia motifs: the same four in every cue ---------------------------
motif cole = 0:1/4. 0:1/8 1:1/4 0:1/4 | -2:1/2 0:1/2 | 0:1/4. 0:1/8 2:1/4 1:1/4 | 0:1/1      -- Cole: keeps coming back to one note, never further than a third from it
motif cole_head < cole : fragment:0,4
motif cole_slow < cole : augment:2
motif cole_open < cole : expand:2 > transpose:2                                              -- the same contour with every step a third: the theme with its arms down
motif ivy_a = 4:1/4 5:1/8 4:1/4 2:1/8 | 3:1/4 4:1/8 2:3/8 | 0:1/4 2:1/4 4:1/4 | 7:1/4 6:1/8 4:3/8     -- Ivy: a boat song in six, with one bar that counts in three instead
motif ivy_b = 4:1/4 5:1/8 4:1/4 2:1/8 | 3:1/4 4:1/8 2:3/8 | 1:1/4 0:1/4 -1:1/4 | 0:1/2.
motif ivy < ivy_a : then:ivy_b
motif boat < ivy_a : fragment:0,4                                                            -- the rocking bar on its own
motif hermes = 0:1/16 2:1/16 4:1/16 7:1/16 6:1/8 4:1/8 5:1/16 4:1/16 2:1/8 4:1/4             -- Hermes: up the chord in a hurry, a skip back down, a stop on the fifth
motif hermes_tag < hermes : fragment:0,6
motif dance = 0:1/8 2:1/8 4:1/8 2:1/8 4:1/8 5:1/8 4:1/8 | 7:1/4 6:1/8 4:1/8 5:1/8 4:1/8 2:1/8 | 0:1/8 2:1/8 4:1/8 2:1/8 6:1/8 5:1/8 4:1/8 | 2:1/4 1:1/4 0:3/8     -- Saturnalia: seven, counted two-two-three
motif dance_head < dance : fragment:0,7
motif throne = 0:1/4. 0:1/8 4:1/2 | 5:1/4. 4:1/8 2:1/2 | 0:1/4. 0:1/8 4:1/4 7:1/4 | 6:1/2 4:1/2             -- the old order: dotted, square, four in a bar
motif hermes_low < hermes : transpose:-3
motif blow = 0:1/8 0:1/8 r:1/4 0:1/2
motif cole_inv < cole_head : invert

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@steps bars=8 degree=0 dynamic=p
  b_2: play motif=blow at=@hit times=2 dynamic=ff
  b_3: drone at=@sink bars=3 degree=0 dynamic=pp

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@steps dynamic=mf
  c_2: play motif=cole at=@steps.5 transpose=2 dynamic=f
  c_3: play motif=blow at=@hit times=2 transpose=4 dynamic=ff
  c_shape: shape amount=0.4

voice cl clarinet role=counter octave=4 pan=0.3 engine=soundfont bank=hq
  h_1: play motif=hermes at=@steps.2 dynamic=mp
  h_2: play motif=hermes_low at=@steps.4 dynamic=mp
  h_3: play motif=hermes_tag at=@steps.6 dynamic=p
  h_4: play motif=hermes_tag at=@steps.8 dynamic=pp
  lvl_cl: gain db=-3

voice pno concert_grand role=melody octave=4 pan=0 engine=soundfont
  t_1: play motif=cole_open at=@telling dynamic=mf articulation=legato
  t_2: play motif=cole_inv at=@telling.5 dynamic=mp articulation=legato
  t_3: play motif=cole_slow at=@telling.7 dynamic=mf articulation=legato
  t_h: humanize amount=0.7 timing=10

voice va strings role=harmony octave=3 pan=-0.35 engine=soundfont bank=hq
  v_1: chords at=@telling.5 bars=9 voicing=pad lead=true dynamic=pp
  lvl_va: gain db=-13
