# Olympia B3-57: one chord for the whole cue. Nothing changes behind the gate; Cole's theme walks down to it and back.
piece olympia_b3_57_the_gate key="C minor" tempo=48 style=orchestral
master room.decay=3.6 room.wet=0.36
meta title = "The Gate"
meta soundfont = "hq"

section stair bars=6 meter=4/4 dynamic=pp
section bars_ bars=8 meter=4/4 dynamic=p
section up    bars=5 meter=4/4 dynamic=pp tempo_end=42

harmony
  @stair: i . . . . .
  @bars_: i . . . . . . .
  @up:    i . . . .

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
motif throne_old < throne : augment:2
motif throne_head < throne : fragment:0,3
motif cole_inv < cole_head : invert
motif heart = 0:1/4 0:1/4 r:1/2

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@stair bars=19 degree=0 dynamic=p

voice tmp timpani role=bass octave=3 engine=soundfont bank=hq
  k_1: play motif=heart at=@stair times=6 dynamic=pp
  k_2: play motif=heart at=@bars_ times=8 dynamic=p
  k_3: play motif=heart at=@up times=4 dynamic=pp
  lvl_tmp: gain db=-6

voice st strings role=pad octave=4 pan=0 engine=soundfont bank=hq
  s_1: chords at=@stair bars=19 voicing=pad dynamic=pp
  lvl_st: gain db=-8

voice tu tuba role=melody octave=2 pan=0.1 engine=soundfont bank=hq
  t_1: play motif=throne_old at=@bars_ dynamic=p articulation=legato
  lvl_tu: gain db=-2

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@stair.2 dynamic=p articulation=legato
  c_2: play motif=cole_inv at=@bars_.5 dynamic=pp articulation=legato
  c_3: play motif=cole at=@up dynamic=p articulation=legato
  c_shape: shape amount=0.4

voice hp harp role=ornament octave=4 pan=0.35 engine=soundfont bank=hq
  h_1: play motif=throne_head at=@bars_.7 dynamic=pp
  lvl_hp: gain db=-6
