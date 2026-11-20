# Olympia B3-56: the Saturnalia dance let out on a road with no rail: huge, in seven, too many voices; then one voice left, and it is Ivy's.
piece olympia_b3_56_the_revel key="E minor" tempo=150 style=orchestral
master room.decay=2.6 room.wet=0.26
meta title = "The Revel"
meta soundfont = "hq"

section walk  bars=8  meter=7/8 dynamic=p tempo=120
section out   bars=16 meter=7/8 dynamic=f
section whole bars=12 meter=7/8 dynamic=ff tempo=162
section edge  bars=2  meter=7/8 dynamic=ff tempo=162
section cap   bars=8  meter=6/8 dynamic=pp tempo=54 tempo_end=46

harmony
  @walk:  i . . . i . VII .
  @out:   i . VII . i . VI V | i . VII . iv . V .
  @whole: i VII VI V | i VII VI V | bII . V .
  @edge:  bII .
  @cap:   i . iv . i . v i

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
motif dance_up < dance : transpose:2
motif dance_low < dance : transpose:-3
motif dance_wrong < dance : invert

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@walk bars=8 degree=0 dynamic=p
  b_2: bass at=@out bars=16 dynamic=f
  b_3: bass at=@whole bars=12 dynamic=ff
  b_4: drone at=@edge bars=2 degree=1 dynamic=ff
  b_5: drone at=@cap bars=8 degree=0 dynamic=pp

voice tk taiko role=percussion pan=-0.1
  x_1: groove at=@walk.5 bars=4 pattern="X.x.X.." res=1/8 dynamic=p
  x_2: groove at=@out bars=16 pattern="X.x.X.x" res=1/8 dynamic=mf
  x_3: groove at=@whole bars=12 pattern="X.X.Xxx|XxX.Xxx" res=1/8 dynamic=f
  x_4: groove at=@edge bars=2 pattern="XXXXXXX" res=1/8 dynamic=ff
  lvl_tk: gain db=-5

voice tb tambourine role=percussion pan=0.5
  y_1: groove at=@out bars=16 pattern="xxxxxxx" res=1/8 dynamic=mp
  y_2: groove at=@whole bars=12 pattern="xXxXxxX" res=1/8 dynamic=mf
  lvl_tb: gain db=-8

voice fd fiddle role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  d_0: play motif=dance_head at=@walk.5 dynamic=p
  d_0b: play motif=dance_head at=@walk.7 dynamic=mp
  d_1: play motif=dance at=@out dynamic=f
  d_2: play motif=dance at=@out.5 dynamic=f
  d_3: play motif=dance_up at=@out.9 dynamic=f
  d_4: play motif=dance at=@out.13 dynamic=f
  d_5: play motif=dance at=@whole dynamic=ff
  d_6: play motif=dance_up at=@whole.5 dynamic=ff
  d_7: play motif=dance_wrong at=@whole.9 octave=5 dynamic=ff

voice tp trumpet role=melody octave=4 pan=0.25 engine=soundfont bank=hq
  e_1: play motif=dance at=@out.9 dynamic=mf
  e_2: play motif=dance_low at=@out.13 dynamic=f
  e_3: play motif=dance at=@whole.2 dynamic=ff
  e_4: play motif=dance_up at=@whole.6 dynamic=ff
  e_5: play motif=dance at=@whole.10 dynamic=ff
  lvl_tp: gain db=-3

voice trb trombone role=counter octave=3 pan=0.4 engine=soundfont bank=hq
  f_1: play motif=dance_low at=@whole.3 dynamic=ff
  f_2: play motif=dance_wrong at=@whole.7 dynamic=ff
  lvl_trb: gain db=-3

voice br brass_section role=harmony octave=3 pan=0.1 engine=soundfont bank=hq
  h_1: chords at=@whole bars=12 dynamic=f
  h_2: chords at=@edge bars=2 dynamic=ff
  lvl_br: gain db=-6

voice cl clarinet role=melody octave=4 pan=0 engine=soundfont bank=hq
  i_1: play motif=ivy_b at=@cap dynamic=pp articulation=legato
  i_2: play motif=boat at=@cap.5 dynamic=pp articulation=legato
  i_shape: shape amount=0.4
