# Olympia B1-11: the harbor wall at night. The water rocks in six; Cole has to say it in four.
piece olympia_b1_11_thalassa key="E dorian" tempo=60 style=orchestral
master room.decay=3.0 room.wet=0.32
meta title = "Thalassa"
meta soundfont = "hq"

section swell bars=8 meter=6/8 dynamic=p
section wall  bars=8 meter=4/4 dynamic=mp
section water bars=8 meter=6/8 dynamic=p
section shoes bars=3 meter=4/4 dynamic=pp tempo_end=50

harmony
  @swell: i . IV . i . VII .
  @wall:  i . VII i | IV . v .
  @water: i . IV . III . IV .
  @shoes: i IV .

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
motif tide = 0:3/8 4:3/8 | 2:3/8 4:1/4 2:1/8 | 0:3/8 4:3/8 | -1:3/8 0:3/8
motif tide_up < tide : transpose:2

voice hp harp role=harmony octave=3 pan=-0.3 engine=soundfont bank=hq
  h_1: chords at=@swell bars=8 figure="0 2 1 2 1 2" ring=true dynamic=p
  h_2: chords at=@water bars=8 figure="0 2 1 2 1 2" ring=true dynamic=p
  lvl_hp: gain db=-4

voice cl clarinet role=melody octave=4 pan=0.3 engine=soundfont bank=hq
  t_1: play motif=tide at=@swell.5 dynamic=p articulation=legato
  t_2: play motif=tide_up at=@water dynamic=mp articulation=legato
  t_3: play motif=tide at=@water.5 dynamic=p articulation=legato
  t_shape: shape amount=0.4
  lvl_cl: gain db=-3

voice vc cello role=melody octave=3 pan=-0.15 engine=soundfont bank=hq
  c_1: play motif=cole at=@wall dynamic=mf articulation=legato
  c_2: play motif=cole at=@wall.5 transform=["invert"] dynamic=mp articulation=legato
  c_3: phrase at=@shoes steps="0:1/2. -2:1/4 | 0:1/1~ | 0:1/1" dynamic=pp articulation=legato
  c_shape: shape amount=0.45

voice ob oboe role=counter octave=4 pan=0.1 engine=soundfont bank=hq
  o_1: play motif=boat at=@water.3 dynamic=pp articulation=legato
  lvl_ob: gain db=-6

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@swell bars=27 pattern=root dynamic=p
  lvl_cb: gain db=-3
