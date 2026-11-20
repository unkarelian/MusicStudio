# Olympia B2-30: the flower festival. Ivy's boat song as a town's dance; then the dead walk through it, slower, and are sent home.
piece olympia_b2_30_anthesteria key="G major" tempo=104 style=orchestral
master room.decay=2.2 room.wet=0.22
meta title = "Anthesteria"
meta soundfont = "hq"

section jars  bars=8  meter=6/8 dynamic=mp
section feast bars=16 meter=6/8 dynamic=f
section dead  bars=8  meter=6/8 dynamic=pp tempo=66
section pour  bars=4  meter=6/8 dynamic=p tempo=66 tempo_end=54

harmony
  @jars:  I . IV I | vi . V I
  @feast: I . IV I | vi . V I | IV . I . | ii V I .
  @dead:  vi . IV . | ii . vi .
  @pour:  IV . I .

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
motif ivy_up < ivy_a : transpose:2
motif lilt = 0:1/4 4:1/8 4:1/4 4:1/8
motif walkers = 0:3/8 -1:3/8 | -2:3/8 0:3/8
motif walk_up < walkers : transpose:2

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: play motif=lilt at=@jars times=24 dynamic=mf articulation=staccato
  b_2: drone at=@dead bars=12 degree=0 dynamic=pp

voice cl clarinet role=melody octave=4 pan=-0.2 engine=soundfont bank=hq
  i_1: play motif=ivy at=@jars dynamic=mp articulation=legato
  i_2: play motif=ivy at=@feast.9 dynamic=f
  i_3: play motif=boat at=@pour dynamic=p articulation=legato
  i_shape: shape amount=0.4

voice ob oboe role=melody octave=4 pan=0.2 engine=soundfont bank=hq
  o_1: play motif=ivy at=@feast dynamic=mf
  o_2: play motif=ivy_up at=@feast.9 dynamic=mf
  lvl_ob: gain db=-2

voice fl flute role=counter octave=5 pan=0.35 engine=soundfont bank=hq
  f_1: play motif=boat at=@feast.5 times=1 dynamic=mf
  f_2: play motif=boat at=@feast.13 times=1 transpose=4 dynamic=f
  lvl_fl: gain db=-3

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  h_1: chords at=@jars bars=24 figure="0 1 2 1 2 1" dynamic=mp
  h_2: chords at=@pour bars=4 voicing=broken lead=true dynamic=pp
  lvl_hp: gain db=-4

voice tamb tambourine role=percussion pan=0.5
  t_1: groove at=@feast bars=16 pattern="X.xX.x" res=1/8 dynamic=mf
  lvl_t: gain db=-6

voice vc cello role=melody octave=3 pan=-0.1 engine=soundfont bank=hq
  w_1: play motif=walkers at=@dead times=2 dynamic=p articulation=legato
  w_2: play motif=walk_up at=@dead.5 times=2 dynamic=p articulation=legato
  w_shape: shape amount=0.4

voice vn strings role=harmony octave=4 pan=-0.35 engine=soundfont bank=hq
  d_1: chords at=@dead bars=8 voicing=pad lead=true dynamic=pp
  lvl_vn: gain db=-6
