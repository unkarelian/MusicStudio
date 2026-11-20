# Olympia B1-16: the hill. A water clock in five; the old order's theme, courteous; the pebbles counted; a tie; one vote.
piece olympia_b1_16_the_areopagus key="A dorian" tempo=72 style=orchestral
master room.decay=2.6 room.wet=0.28
meta title = "The Areopagus"
meta soundfont = "hq"

section clock  bars=6 meter=5/4 dynamic=pp
section answer bars=8 meter=4/4 dynamic=mp
section count  bars=8 meter=5/4 dynamic=p
section vote   bars=3 meter=4/4 dynamic=mp tempo_end=54

harmony
  @clock:  i . IV . i .
  @answer: i . IV i | VII . IV v
  @count:  i . . . IV . . v
  @vote:   i v .

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
motif drip = 4:1/4 r:1/4 4:1/4 r:1/4 2:1/4 | 4:1/4 r:1/4 4:1/4 r:1/4 1:1/4
motif pebble = 0:1/4 0:1/4 r:1/4 0:1/4 r:1/4 | 0:1/4 0:1/4 0:1/4 r:1/4 0:1/4
motif pebble_b < pebble : transpose:4
motif tess = 4:1/8 4:1/8 5:1/4 4:1/4 2:1/4 | 4:1/8 5:1/8 7:1/4 5:1/2 | 4:1/8 4:1/8 5:1/4 7:1/4 8:1/4 | 7:1/2 4:1/2

voice vib vibraphone role=ornament octave=5 pan=0.3 engine=soundfont bank=hq
  d_1: play motif=drip at=@clock times=3 dynamic=p
  d_2: play motif=drip at=@count times=4 dynamic=pp
  lvl_vib: gain db=-3

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_0: drone at=@clock.3 bars=4 degree=0 dynamic=pp
  b_1: bass at=@answer bars=8 pattern=root dynamic=p
  p_1: play motif=pebble at=@count times=4 dynamic=mp articulation=staccato
  b_2: phrase at=@vote steps="0:1/1 | 4:1/1~ | 4:1/1" dynamic=mp

voice ob oboe role=melody octave=4 pan=-0.2 engine=soundfont bank=hq
  t_1: play motif=tess at=@clock.3 dynamic=mp
  t_2: play motif=tess at=@count.5 transpose=2 dynamic=mp
  t_shape: shape amount=0.4
  lvl_ob: gain db=-2

voice vc cello role=melody octave=3 pan=0.1 engine=soundfont bank=hq
  a_1: play motif=throne at=@answer dynamic=mf articulation=legato
  a_2: play motif=throne at=@answer.5 transpose=-2 dynamic=mf articulation=legato
  p_2: play motif=pebble_b at=@count.5 times=2 dynamic=p articulation=staccato
  a_3: phrase at=@vote steps="0:1/4. 0:1/8 4:1/2 | 4:1/1~ | 4:1/1" dynamic=mf articulation=legato
  a_shape: shape amount=0.4

voice hp harp role=harmony octave=3 pan=-0.35 engine=soundfont bank=hq
  h_1: chords at=@answer bars=8 voicing=broken dynamic=p
  lvl_hp: gain db=-5
