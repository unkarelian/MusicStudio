# Olympia B2-44: shutters in the city; then the porch at Nysa, Ivy's song against Hermes's figure at half speed, and the dance a long way off, in seven.
piece olympia_b2_44_the_ban key="G major" tempo=76 style=orchestral
master room.decay=2.8 room.wet=0.28
meta title = "The Ban"
meta soundfont = "hq"

section shutters bars=4  meter=4/4 dynamic=f
section porch    bars=12 meter=6/8 dynamic=p tempo=66
section far      bars=8  meter=7/8 dynamic=pp tempo=132
section tap      bars=6  meter=6/8 dynamic=pp tempo=60 tempo_end=50

harmony
  @shutters: i . bVI V
  @porch:    I . IV I | vi . IV . | I . ii V
  @far:      I . . . bVII . I .
  @tap:      IV . vi . IV I

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
motif hermes_slow < hermes : augment:2
motif hermes_tired < hermes_tag : augment:4
motif throne_head < throne : fragment:0,3

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@shutters bars=4 dynamic=f
  b_2: drone at=@porch bars=12 degree=0 dynamic=pp
  b_3: drone at=@far bars=8 degree=0 dynamic=pp
  b_4: drone at=@tap bars=6 degree=0 dynamic=pp

voice hn horn role=melody octave=3 pan=-0.3 engine=soundfont bank=hq
  t_1: play motif=throne at=@shutters dynamic=f
  lvl_hn: gain db=-2

voice sn snare role=percussion pan=0.1
  x_1: groove at=@shutters bars=4 pattern="X..x..X.|X.xxX..." res=1/8 dynamic=mf
  lvl_sn: gain db=-6

voice cl clarinet role=melody octave=4 pan=-0.15 engine=soundfont bank=hq
  i_1: play motif=ivy at=@porch dynamic=p articulation=legato
  i_2: play motif=boat at=@porch.9 dynamic=p articulation=legato
  i_3: play motif=ivy_b at=@tap dynamic=pp articulation=legato
  i_shape: shape amount=0.4

voice fl flute role=counter octave=5 pan=0.3 engine=soundfont bank=hq
  h_1: play motif=hermes_slow at=@porch.5 dynamic=p articulation=legato
  h_2: play motif=hermes_slow at=@porch.11 dynamic=pp articulation=legato
  h_3: play motif=hermes_tired at=@tap.4 dynamic=pp articulation=legato
  lvl_fl: gain db=-3

voice hp harp role=harmony octave=3 pan=0.25 engine=soundfont bank=hq
  p_1: chords at=@porch bars=12 figure="0 1 2 1 2 1" dynamic=pp
  p_2: chords at=@tap bars=6 voicing=broken lead=true dynamic=pp
  lvl_hp: gain db=-4

voice picc piccolo role=melody octave=5 pan=0.5 engine=soundfont bank=hq
  d_1: play motif=dance at=@far dynamic=pp
  d_2: play motif=dance at=@far.5 dynamic=pp
  lvl_picc: gain db=-12
