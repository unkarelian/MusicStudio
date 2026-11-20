# Olympia B3-49: the old order's tune with pieces missing, over a night drive down the Descent.
piece olympia_b3_49_the_station_wagon key="D minor" tempo=72 style=orchestral
master room.decay=2.8 room.wet=0.28
meta title = "The Station Wagon"
meta soundfont = "hq"

section road   bars=8 meter=4/4 dynamic=pp
section gold   bars=8 meter=4/4 dynamic=p
section rim    bars=4 meter=4/4 dynamic=mp
section down   bars=6 meter=4/4 dynamic=pp tempo=66 tempo_end=54

harmony
  @road: i . VI . | iv . i .
  @gold: i . VII VI | iv . V .
  @rim:  VI . iv V
  @down: i . VI . iv i

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
motif throne_head < throne : fragment:0,3
motif throne_mid < throne : fragment:3,6
motif throne_fall < throne_head : invert
motif throne_slow < throne_head : augment:2

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@road bars=8 degree=0 dynamic=pp
  b_2: bass at=@gold bars=8 dynamic=p
  b_3: bass at=@rim bars=4 dynamic=mp
  b_4: drone at=@down bars=6 degree=0 dynamic=pp

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  p_1: chords at=@road bars=8 figure="0 1 2 1 0 1 2 1" dynamic=pp
  p_2: chords at=@gold bars=8 figure="0 1 2 1 0 1 2 1" dynamic=pp
  p_3: chords at=@rim bars=4 figure="0 1 2 1 0 1 2 1" dynamic=p
  p_4: chords at=@down bars=6 figure="0 . 1 . 2 . 1 ." dynamic=pp
  lvl_hp: gain db=-5

voice hn horn role=melody octave=3 pan=-0.3 engine=soundfont bank=hq
  t_1: play motif=throne_head at=@road.3 dynamic=p articulation=legato
  t_2: play motif=throne_mid at=@road.6 dynamic=pp articulation=legato
  t_3: play motif=throne_head at=@gold dynamic=mp articulation=legato
  t_4: play motif=throne_fall at=@gold.3 dynamic=mp articulation=legato
  t_5: play motif=throne_mid at=@gold.6 dynamic=p articulation=legato
  t_6: play motif=throne at=@rim dynamic=mf
  t_7: play motif=throne_slow at=@down dynamic=pp articulation=legato
  t_shape: shape amount=0.4

voice vc cello role=counter octave=3 pan=-0.1 engine=soundfont bank=hq
  c_1: play motif=cole_head at=@road.5 dynamic=pp articulation=legato
  c_2: play motif=cole at=@gold.5 dynamic=p articulation=legato
  c_3: play motif=cole_head at=@down.3 dynamic=pp articulation=legato
  lvl_vc: gain db=-3

voice st strings role=pad octave=4 pan=0 engine=soundfont bank=hq
  s_1: chords at=@gold bars=8 voicing=pad lead=true dynamic=pp
  s_2: chords at=@rim bars=4 voicing=pad lead=true dynamic=p
  lvl_st: gain db=-10
