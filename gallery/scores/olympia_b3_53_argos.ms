# Olympia B3-53: Hera's city. Clocks that are right; the throne tune exact and without warmth; Cole's theme allowed in once.
piece olympia_b3_53_argos key="A minor" tempo=60 style=orchestral
master room.decay=3.0 room.wet=0.3
meta title = "Argos"
meta soundfont = "hq"

section clocks bars=4 meter=4/4 dynamic=pp
section court  bars=8 meter=4/4 dynamic=mp
section pen    bars=6 meter=4/4 dynamic=p
section train  bars=4 meter=4/4 dynamic=pp tempo_end=52

harmony
  @clocks: i . . .
  @court:  i . v . | VI . v .
  @pen:    iv . i . bII V
  @train:  i . v i

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
motif tick = 0:1/4 4:1/4 0:1/4 4:1/4
motif tock = 0:1/8 r:1/8 0:1/8 r:1/8 0:1/8 r:1/8 0:1/8 r:1/8
motif throne_head < throne : fragment:0,3
motif throne_up < throne : transpose:2

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@clocks bars=4 degree=0 dynamic=pp
  b_2: bass at=@court bars=8 dynamic=p
  b_3: bass at=@pen bars=6 dynamic=p
  b_4: drone at=@train bars=4 degree=0 dynamic=pp

voice cel celesta role=ornament octave=5 pan=0.4 engine=soundfont bank=hq
  k_1: play motif=tick at=@clocks times=4 dynamic=p
  k_2: play motif=tick at=@court times=8 dynamic=pp
  k_3: play motif=tick at=@pen times=6 dynamic=pp
  k_4: play motif=tick at=@train times=3 dynamic=pp
  lvl_cel: gain db=-6

voice vib vibraphone role=ornament octave=4 pan=-0.4 engine=soundfont bank=hq
  v_1: play motif=tock at=@clocks.3 times=2 dynamic=pp
  v_2: play motif=tock at=@pen times=6 dynamic=pp
  lvl_vib: gain db=-9

voice ob oboe role=melody octave=4 pan=0 engine=soundfont bank=hq
  t_1: play motif=throne at=@court dynamic=mp
  t_2: play motif=throne_up at=@court.5 dynamic=mp
  t_3: play motif=throne_head at=@pen.5 dynamic=p
  t_shape: shape amount=0.15

voice vc cello role=counter octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@pen dynamic=p articulation=legato
  c_2: play motif=cole_head at=@train dynamic=pp articulation=legato
  c_shape: shape amount=0.4
