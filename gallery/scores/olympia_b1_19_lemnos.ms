# Olympia B1-19: the shipyard, hammering in four with a bar dropped; then the night ferry in six, Cole's theme rocked.
piece olympia_b1_19_lemnos key="E minor" tempo=104 style=orchestral
master room.decay=2.5 room.wet=0.26
meta title = "Lemnos"
meta soundfont = "hq"

section yard  bars=12 meter=4/4 dynamic=mf
section ferry bars=16 meter=6/8 tempo=60 dynamic=p
section door  bars=2  meter=6/8 tempo=60 tempo_end=48 dynamic=pp

harmony
  @yard:  i . VII . i . iv . i . VII v
  @ferry: i . iv . i . VII . VI . iv . i . VII .
  @door:  i .

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
motif hammer = 0:1/8 r:1/8 0:1/8 0:1/8 r:1/4 4:1/4
motif anvil = r:1/4 4:1/8 r:1/8 r:1/4 4:1/8 4:1/8
motif cole6 = 0:3/8 0:1/8 1:1/4 | -2:3/8 0:3/8 | 0:3/8 2:1/4 1:1/8 | 0:3/4
motif cole6_up < cole6 : transpose:2

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  y_1: play motif=hammer at=@yard times=12 dynamic=mf articulation=staccato
  f_1: bass at=@ferry bars=18 pattern=root dynamic=p

voice vib vibraphone role=ornament octave=5 pan=0.3 engine=soundfont bank=hq
  a_1: play motif=anvil at=@yard.3 times=10 dynamic=mp
  lvl_vib: gain db=-5

voice cl clarinet role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  c_1: play motif=cole at=@yard.5 dynamic=mf
  c_2: play motif=cole_head at=@yard.9 transpose=2 dynamic=mf
  c_3: play motif=cole_head at=@yard.11 dynamic=mp

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  h_1: chords at=@ferry bars=18 figure="0 2 1 2 1 2" ring=true dynamic=p
  lvl_hp: gain db=-7

voice vc cello role=melody octave=3 pan=-0.15 engine=soundfont bank=hq
  k_1: play motif=cole6 at=@ferry dynamic=mp articulation=legato
  k_2: play motif=cole6_up at=@ferry.5 dynamic=mp articulation=legato
  k_3: play motif=cole6 at=@ferry.9 dynamic=mf articulation=legato
  k_4: play motif=cole6 at=@ferry.13 dynamic=p articulation=legato
  k_shape: shape amount=0.5

voice ob oboe role=counter octave=4 pan=0.1 engine=soundfont bank=hq
  o_1: play motif=boat at=@ferry.9 dynamic=pp articulation=legato
  lvl_ob: gain db=-6
