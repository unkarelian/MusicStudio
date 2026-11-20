# Olympia B1-24: Nysa under frost. Ivy's song on the kitchen piano; the Hermes figure once, slowed, on the porch; the second verse goes wrong and is sung anyway.
piece olympia_b1_24_midwinter key="G major" tempo=76 style=orchestral
master room.decay=2.4 room.wet=0.24
meta title = "Midwinter"
meta soundfont = "hq"

section frost   bars=8  meter=6/8 dynamic=p
section porch   bars=4  meter=6/8 dynamic=pp
section kitchen bars=16 meter=6/8 dynamic=mp
section verse   bars=4  meter=6/8 dynamic=p tempo_end=60

harmony
  @frost:   I . IV I | vi IV V .
  @porch:   vi . IV .
  @kitchen: I . IV I | I IV V I | I . IV I | ii IV V I
  @verse:   I IV I .

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
motif hermes_kind < hermes : augment:2
motif wrong < ivy_b : transpose:1

voice pno concert_grand role=melody octave=4 pan=0 engine=soundfont
  p_1: play motif=ivy_a at=@frost dynamic=p
  p_2: play motif=boat at=@frost.5 times=2 dynamic=pp
  p_3: chords at=@kitchen bars=20 figure="0 2 1 2 1 2" octave=3 dynamic=p
  p_shape: shape amount=0.4
  p_h: humanize amount=0.5 timing=9

voice cl clarinet role=counter octave=4 pan=0.3 engine=soundfont bank=hq
  k_1: play motif=hermes_kind at=@porch.2 dynamic=p articulation=legato
  lvl_cl: gain db=-3

voice hp harp role=harmony octave=3 pan=-0.3 engine=soundfont bank=hq
  h_1: chords at=@porch bars=4 voicing=broken ring=true dynamic=pp
  lvl_hp: gain db=-4

voice ob oboe role=melody octave=4 pan=0.1 engine=soundfont bank=hq
  i_1: play motif=ivy at=@kitchen dynamic=mf articulation=legato
  i_2: play motif=ivy_a at=@kitchen.9 dynamic=mf articulation=legato
  i_3: play motif=wrong at=@kitchen.13 dynamic=mp articulation=legato
  i_4: play motif=ivy_b at=@verse dynamic=p articulation=legato
  i_shape: shape amount=0.5

voice vc cello role=counter octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=boat at=@kitchen.9 times=2 dynamic=p articulation=legato
  lvl_vc: gain db=-5

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@frost bars=8 pattern=root dynamic=pp
  b_2: bass at=@kitchen bars=20 pattern=root dynamic=p
  lvl_cb: gain db=-3
