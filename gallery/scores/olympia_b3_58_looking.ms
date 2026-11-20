# Olympia B3-58: Ivy's song with an older voice under it singing the same tune slower; Hermes's figure asks three times and nothing answers.
piece olympia_b3_58_looking key="G major" tempo=63 style=orchestral
master room.decay=2.9 room.wet=0.3
meta title = "Looking"
meta soundfont = "hq"

section cup    bars=4  meter=6/8 dynamic=pp
section porch  bars=16 meter=6/8 dynamic=p
section laugh  bars=4  meter=6/8 dynamic=mp
section stop   bars=6  meter=6/8 dynamic=pp tempo=56 tempo_end=46

harmony
  @cup:   I . vi .
  @porch: I . IV I | vi . IV . | I . ii V | vi . IV V
  @laugh: I IV I V
  @stop:  vi . IV . ii .

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
motif ivy_old < ivy_a : augment:2
motif hermes_slow < hermes : augment:2
motif hermes_ask < hermes_tag : augment:2

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@cup bars=4 degree=0 dynamic=pp
  b_2: bass at=@porch bars=16 dynamic=pp
  b_3: bass at=@laugh bars=4 dynamic=p
  b_4: drone at=@stop bars=6 degree=5 dynamic=pp

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  p_1: chords at=@cup bars=4 figure="0 . . 1 2 ." ring=true dynamic=pp
  p_2: chords at=@porch bars=16 figure="0 1 2 1 2 1" dynamic=pp
  p_3: chords at=@laugh bars=4 figure="0 2 1 2 1 2" ring=true dynamic=p
  p_4: chords at=@stop bars=6 figure="0 . . 1 . ." ring=true dynamic=pp
  lvl_hp: gain db=-5

voice cl clarinet role=melody octave=4 pan=-0.15 engine=soundfont bank=hq
  i_1: play motif=boat at=@cup.3 dynamic=pp articulation=legato
  i_2: play motif=ivy at=@porch dynamic=p articulation=legato
  i_3: play motif=ivy at=@porch.9 dynamic=mp articulation=legato
  i_4: play motif=ivy_a at=@laugh dynamic=mp articulation=legato
  i_shape: shape amount=0.4

voice vc cello role=counter octave=3 pan=-0.3 engine=soundfont bank=hq
  o_1: play motif=ivy_old at=@porch.5 dynamic=p articulation=legato
  o_2: play motif=ivy_old at=@porch.13 dynamic=mp articulation=legato
  o_3: play motif=ivy_b at=@laugh dynamic=mp articulation=legato
  lvl_vc: gain db=-2

voice fl flute role=counter octave=5 pan=0.3 engine=soundfont bank=hq
  h_1: play motif=hermes_slow at=@porch.8 dynamic=p articulation=legato
  h_2: play motif=hermes_slow at=@porch.16 dynamic=p articulation=legato
  h_3: play motif=hermes_ask at=@stop dynamic=p articulation=legato
  h_4: play motif=hermes_ask at=@stop.3 dynamic=pp articulation=legato
  h_5: play motif=hermes_ask at=@stop.5 dynamic=pp articulation=legato
  lvl_fl: gain db=-3
