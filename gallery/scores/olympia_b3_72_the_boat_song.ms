# Olympia B3-72: Ivy's song as a kitchen song, both halves, twice, resolved; then Hermes's figure once, alone, stopping on the fifth.
piece olympia_b3_72_the_boat_song key="G major" tempo=66 style=orchestral
master room.decay=2.0 room.wet=0.2
meta title = "The Boat Song"
meta soundfont = "hq"

section sink   bars=4  meter=6/8 dynamic=p
section verse  bars=8  meter=6/8 dynamic=mp
section second bars=8  meter=6/8 dynamic=mf
section both   bars=8  meter=6/8 dynamic=mf
section door   bars=4  meter=6/8 dynamic=pp tempo_end=54

harmony
  @sink:   I . IV I
  @verse:  I . IV I | vi . V I
  @second: I . IV I | vi . V I
  @both:   IV . I . | ii V I .
  @door:   I . . V

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
motif ivy_third < ivy_a : transpose:2
motif hermes_slow < hermes : augment:2

voice pno concert_grand role=harmony octave=3 pan=0 engine=soundfont
  p_1: chords at=@sink bars=4 figure="0 1 2 1 2 1" dynamic=p
  p_2: chords at=@verse bars=8 figure="0 1 2 1 2 1" dynamic=p
  p_3: chords at=@second bars=8 figure="0 2 1 2 1 2" dynamic=mp
  p_4: chords at=@both bars=8 figure="0 2 1 2 1 2" dynamic=mp
  p_5: chords at=@door bars=3 figure="0 . . 1 . ." ring=true dynamic=pp
  p_h: humanize amount=0.6 timing=8
  lvl_pno: gain db=-5

voice ub upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@verse bars=8 dynamic=p
  b_2: bass at=@second bars=8 dynamic=mp
  b_3: bass at=@both bars=8 dynamic=mp

voice cl clarinet role=melody octave=4 pan=-0.15 engine=soundfont bank=hq
  i_1: play motif=boat at=@sink.3 dynamic=p articulation=legato
  i_2: play motif=ivy at=@verse dynamic=mp articulation=legato
  i_3: play motif=ivy at=@second dynamic=mf articulation=legato
  i_4: play motif=ivy at=@both dynamic=mf articulation=legato
  i_shape: shape amount=0.4

voice acc accordion role=counter octave=3 pan=0.3 engine=soundfont bank=hq
  n_1: play motif=ivy_third at=@second dynamic=mp articulation=legato
  n_2: play motif=ivy_b at=@second.5 dynamic=mp articulation=legato
  n_3: play motif=ivy_third at=@both dynamic=mp articulation=legato
  n_4: play motif=ivy_b at=@both.5 transpose=2 dynamic=mp articulation=legato
  lvl_acc: gain db=-6

voice fl flute role=counter octave=5 pan=0.3 engine=soundfont bank=hq
  h_1: play motif=hermes_slow at=@door.2 dynamic=p articulation=legato
  lvl_fl: gain db=-2
