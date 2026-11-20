# Olympia B3-60: the charter bus going north. A road tune made from Cole's theme with its arms down and Ivy's rocking bar, in a plain four, hopeful.
piece olympia_b3_60_north key="D major" tempo=112 style=orchestral
master room.decay=2.2 room.wet=0.22
meta title = "North"
meta soundfont = "hq"

section pull   bars=4  meter=4/4 dynamic=mp
section road   bars=16 meter=4/4 dynamic=mf
section thrace bars=8  meter=4/4 dynamic=p
section peak   bars=8  meter=4/4 dynamic=f tempo_end=96

harmony
  @pull:   I . IV .
  @road:   I . IV I | vi . IV V | I . IV I | ii . V .
  @thrace: vi . iii . IV . V .
  @peak:   I . IV . vi IV I .

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
motif road = 0:1/8 2:1/8 4:1/4 4:1/8 5:1/8 4:1/4 | 2:1/4 4:1/4 7:1/2 | 6:1/8 5:1/8 4:1/4 2:1/4 1:1/4 | 0:1/1
motif road_up < road : transpose:2

voice ub upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@pull bars=4 dynamic=mp
  b_2: bass at=@road bars=16 dynamic=mf
  b_3: bass at=@thrace bars=8 dynamic=p
  b_4: bass at=@peak bars=8 dynamic=mf

voice gt classical_guitar role=harmony octave=3 pan=-0.5 engine=soundfont
  g_1: chords at=@pull bars=4 figure="0 2 1 2 0 2 1 2" dynamic=mp
  g_2: chords at=@road bars=16 figure="0 2 1 2 0 2 1 2" dynamic=mp
  g_3: chords at=@thrace bars=8 figure="0 . 1 . 2 . 1 ." dynamic=p
  g_4: chords at=@peak bars=8 figure="0 2 1 2 0 2 1 2" dynamic=mf
  lvl_gt: gain db=-4

voice tb tambourine role=percussion pan=0.5
  y_1: groove at=@road bars=16 pattern="..x...x." res=1/8 dynamic=p
  y_2: groove at=@peak bars=8 pattern="..x...x." res=1/8 dynamic=p
  lvl_tb: gain db=-10

voice fd fiddle role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  r_1: play motif=road at=@road dynamic=mf
  r_2: play motif=road_up at=@road.5 dynamic=mf
  r_3: play motif=road at=@road.9 dynamic=mf
  r_4: play motif=cole_open at=@road.13 dynamic=mf
  r_5: play motif=road at=@peak dynamic=f
  r_6: play motif=road at=@peak.5 dynamic=mf
  r_shape: shape amount=0.3

voice acc accordion role=counter octave=3 pan=0.3 engine=soundfont bank=hq
  a_1: play motif=boat at=@road.5 dynamic=p
  a_2: play motif=boat at=@road.11 dynamic=p
  a_3: play motif=cole at=@thrace dynamic=mp
  a_4: play motif=cole_head at=@thrace.5 dynamic=p
  a_5: play motif=hermes_tag at=@peak.4 dynamic=p
  lvl_acc: gain db=-5

voice hn horn role=counter octave=3 pan=0.1 engine=soundfont bank=hq
  n_1: play motif=cole_slow at=@peak dynamic=mf articulation=legato
  lvl_hn: gain db=-4
