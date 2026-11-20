# Olympia B2-32: Leo's tune on a guitar, easy and a little tired. A bigger, warmer sound takes it over, and it stops. Two notes after.
piece olympia_b2_32_delos key="E major" tempo=84 style=orchestral
master room.decay=2.8 room.wet=0.28
meta title = "Delos"
meta soundfont = "hq"

section tune bars=12 meter=4/4 dynamic=mp
section arms bars=8  meter=4/4 dynamic=mf
section lake bars=5  meter=4/4 dynamic=pp tempo=60 tempo_end=50

harmony
  @tune: I . vi . | IV . V . | I . IV V
  @arms: I . vi . | IV . . .
  @lake: vi . . . .

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
motif leo = 4:1/4 2:1/8 4:1/8 5:1/4 4:1/4 | 2:1/4. 1:1/8 0:1/2 | 4:1/4 2:1/8 4:1/8 7:1/4 6:1/4 | 4:1/2. r:1/4
motif leo_slow < leo : augment:2
motif leo_head < leo : fragment:0,5
motif dee = 4:1/2 2:1/1

voice gtr guitar role=melody octave=3 pan=-0.15 engine=soundfont bank=hq
  l_1: play motif=leo at=@tune dynamic=mp
  l_2: play motif=leo at=@tune.5 transpose=1 dynamic=mp
  l_3: play motif=leo at=@tune.9 dynamic=mf
  l_4: play motif=leo_head at=@arms dynamic=mp
  l_5: play motif=leo_head at=@arms.3 dynamic=p
  l_h: humanize amount=0.7 timing=10

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@tune.5 bars=8 dynamic=p
  b_2: drone at=@arms bars=8 degree=0 dynamic=mf

voice st strings role=harmony octave=3 pan=0 engine=soundfont bank=hq
  s_1: chords at=@arms bars=8 voicing=pad lead=true dynamic=mf
  s_sw: shape amount=0.6

voice hn horn role=melody octave=3 pan=0.25 engine=soundfont bank=hq
  a_1: play motif=leo_slow at=@arms dynamic=mf articulation=legato
  a_shape: shape amount=0.5

voice vn violin role=counter octave=5 pan=-0.3 engine=soundfont bank=hq
  v_1: play motif=leo_slow at=@arms.3 transpose=2 dynamic=mf articulation=legato
  lvl_vn: gain db=-3

voice fl flute role=melody octave=5 pan=0.2 engine=soundfont bank=hq
  d_1: play motif=dee at=@lake.2 dynamic=pp articulation=legato
  d_2: play motif=dee at=@lake.4 dynamic=pp articulation=legato
