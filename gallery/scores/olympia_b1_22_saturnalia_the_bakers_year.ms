# Olympia B1-22: the dance whole and happy. A paper crown; the square goes quiet for four bars of the old order; then very loud.
piece olympia_b1_22_saturnalia_the_bakers_year key="D mixolydian" tempo=132 style=orchestral
master room.decay=2.2 room.wet=0.22
meta title = "Saturnalia"
meta soundfont = "hq"

section a      bars=8  meter=7/8 dynamic=mf
section b      bars=8  meter=7/8 dynamic=mf
section decree bars=4  meter=4/4 tempo=76 dynamic=pp
section roar   bars=16 meter=7/8 dynamic=f
section cup    bars=2  meter=7/8 dynamic=mf

harmony
  @a:      I . IV I | I . VII I
  @b:      IV . I . | VII . IV I
  @decree: I . IV .
  @roar:   I . IV I | I . VII I | IV . I . | VII IV V I
  @cup:    I .

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
motif stamp = 0:1/4 4:1/4 0:1/8 4:1/8 4:1/8
motif dance_up < dance : transpose:2

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  s_1: play motif=stamp at=@a times=16 dynamic=mf articulation=staccato
  s_2: drone at=@decree bars=4 degree=0 dynamic=pp
  s_3: play motif=stamp at=@roar times=18 dynamic=f articulation=staccato

voice ob oboe role=melody octave=4 pan=-0.2 engine=soundfont bank=hq
  d_1: play motif=dance at=@a dynamic=mf
  d_2: play motif=dance at=@a.5 dynamic=mf
  d_3: play motif=dance at=@roar dynamic=f
  d_4: play motif=dance_up at=@roar.5 dynamic=f
  d_5: play motif=dance at=@roar.9 dynamic=f
  d_6: play motif=dance at=@roar.13 dynamic=ff
  d_h: humanize amount=0.4 timing=6

voice fl flute role=melody octave=5 pan=0.2 engine=soundfont bank=hq
  e_1: play motif=dance_up at=@b dynamic=mf
  e_2: play motif=dance at=@b.5 dynamic=mf
  e_3: play motif=dance at=@roar.5 dynamic=mf
  e_4: play motif=dance at=@roar.13 dynamic=f
  e_5: play motif=dance_head at=@cup dynamic=mf
  lvl_fl: gain db=-2

voice cl clarinet role=counter octave=4 pan=-0.4 engine=soundfont bank=hq
  k_1: play motif=dance_head at=@a.5 times=4 transpose=-3 dynamic=mp
  k_2: play motif=dance_head at=@roar.9 times=8 transpose=-3 dynamic=mf
  lvl_cl: gain db=-4

voice hp harp role=harmony octave=3 pan=0.35 engine=soundfont bank=hq
  h_1: chords at=@a bars=16 figure="0 2 1 2 0 1 2" dynamic=mp
  h_2: chords at=@roar bars=18 figure="0 2 1 2 0 1 2" dynamic=mf
  lvl_hp: gain db=-4

voice vc cello role=melody octave=3 pan=0.05 engine=soundfont bank=hq
  t_1: play motif=throne at=@decree dynamic=p articulation=legato
  t_shape: shape amount=0.3
