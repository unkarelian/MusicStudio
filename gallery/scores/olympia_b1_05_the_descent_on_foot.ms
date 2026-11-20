# Olympia B1-5: Cole walks up the Descent at night with the duffel, the dog behind him; sees the rim; walks back.
piece olympia_b1_05_the_descent_on_foot key="D dorian" tempo=66 style=orchestral
master room.decay=2.8 room.wet=0.3
meta title = "The Terminal"
meta soundfont = "hq"

section walk  bars=8 meter=4/4 dynamic=p
section climb bars=8 meter=4/4 dynamic=mp
section rim   bars=4 meter=4/4 dynamic=pp
section down  bars=6 meter=4/4 dynamic=p tempo_end=54

harmony
  @walk:  i . VII i | IV . v i
  @climb: III . VII i | IV . VII .
  @rim:   IV . i .
  @down:  i . VII i | IV i

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
motif steps = 0:1/4 r:1/4 4:1/4 r:1/4 | 0:1/4 r:1/4 2:1/4 4:1/4
motif under = 4:1/1 | 3:1/2 2:1/2 | 4:1/1 | 5:1/2 4:1/2 | 2:1/1 | 3:1/2 4:1/2 | 2:1/2 1:1/2 | 0:1/1

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  s_1: play motif=steps at=@walk times=4 dynamic=p articulation=staccato
  s_2: play motif=steps at=@climb times=4 dynamic=mp articulation=staccato
  s_3: drone at=@rim bars=4 degree=0 dynamic=pp
  s_4: play motif=steps at=@down times=3 dynamic=pp articulation=staccato

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@walk dynamic=mp articulation=legato
  c_2: play motif=cole at=@walk.5 transpose=-3 dynamic=p articulation=legato
  c_3: play motif=cole at=@climb transpose=2 dynamic=mf articulation=legato
  c_4: play motif=cole at=@climb.5 transpose=4 dynamic=mf articulation=legato
  c_5: play motif=cole at=@down dynamic=p articulation=legato
  c_6: play motif=cole_head at=@down.5 dynamic=pp articulation=legato
  c_shape: shape amount=0.45

voice cl clarinet role=counter octave=4 pan=-0.4 engine=soundfont bank=hq
  u_1: play motif=under at=@climb dynamic=p articulation=legato
  u_shape: shape amount=0.4
  lvl_cl: gain db=-6

voice fl flute role=melody octave=5 pan=0.2 engine=soundfont bank=hq
  f_1: play motif=cole_open at=@rim dynamic=p articulation=legato
  lvl_fl: gain db=-4

voice hp harp role=harmony octave=4 pan=0.35 engine=soundfont bank=hq
  h_1: chords at=@rim bars=4 voicing=broken ring=true dynamic=pp
  lvl_hp: gain db=-5
