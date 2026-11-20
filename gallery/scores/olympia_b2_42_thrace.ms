# Olympia B2-42: the cold north. Drums, a parade square, two parents in a parking lot, and a boy on a fence asking if that was the worst thing or the first good one.
piece olympia_b2_42_thrace key="B minor" tempo=104 style=orchestral
master room.decay=2.0 room.wet=0.2
meta title = "Thrace"
meta soundfont = "hq"

section wire   bars=6  meter=4/4 dynamic=mp
section parade bars=12 meter=4/4 dynamic=f
section lot    bars=8  meter=4/4 dynamic=mf
section fence  bars=8  meter=4/4 dynamic=pp tempo=72 tempo_end=60

harmony
  @wire:   i . . . . .
  @parade: i . VII i | VI . VII i | iv . v i
  @lot:    iv . v . | iv . V .
  @fence:  VI . i . | iv . i .

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
motif north = 0:1/4. 0:1/8 2:1/4 4:1/4 | 4:1/4. 2:1/8 0:1/2 | 0:1/4. 0:1/8 2:1/4 4:1/4 | 6:1/4 4:1/4 2:1/2
motif north_up < north : transpose:2
motif north_head < north : fragment:0,4
motif north_soft < north : augment:2
motif pound = 0:1/4 0:1/8 0:1/8 0:1/4 4:1/4
motif shout_a = 4:1/4 4:1/8 5:1/8 4:1/2
motif shout_b = r:1/2 2:1/8 2:1/8 1:1/4

voice drum taiko role=percussion pan=-0.1
  x_1: groove at=@wire bars=6 pattern="X...x.x.|X.x.X.xx" res=1/8 dynamic=mf
  x_2: groove at=@parade bars=12 pattern="X.x.X.xx" res=1/8 dynamic=f
  x_3: groove at=@lot bars=8 pattern="X.......|X...x..." res=1/8 dynamic=mp
  lvl_drum: gain db=-4

voice timp timpani role=bass octave=2 pan=0.1 engine=soundfont bank=hq
  p_1: play motif=pound at=@parade times=12 dynamic=mf
  lvl_timp: gain db=-4

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@wire bars=6 degree=0 dynamic=mp
  b_2: bass at=@parade bars=20 dynamic=mf
  b_3: drone at=@fence bars=8 degree=0 dynamic=pp

voice tbn trombone role=melody octave=3 pan=-0.3 engine=soundfont bank=hq
  n_1: play motif=north_head at=@wire.5 dynamic=mp
  n_2: play motif=north at=@parade dynamic=f
  n_3: play motif=north at=@parade.9 dynamic=f
  n_4: play motif=shout_a at=@lot times=8 dynamic=f

voice tpt trumpet role=melody octave=4 pan=0.25 engine=soundfont bank=hq
  r_1: play motif=north_up at=@parade.5 dynamic=f
  r_2: play motif=north at=@parade.9 dynamic=f
  lvl_tpt: gain db=-3

voice ob oboe role=counter octave=4 pan=0.35 engine=soundfont bank=hq
  a_1: play motif=shout_b at=@lot times=8 dynamic=mf
  lvl_ob: gain db=-2

voice cl clarinet role=melody octave=4 pan=0 engine=soundfont bank=hq
  j_1: play motif=north_soft at=@fence transpose=0 dynamic=p articulation=legato
  d_1: play motif=dance_head at=@lot.7 dynamic=p
  j_shape: shape amount=0.4

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  h_1: chords at=@fence bars=8 voicing=broken lead=true dynamic=pp
  lvl_hp: gain db=-4
