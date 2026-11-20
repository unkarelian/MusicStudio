# Olympia B3-69: Wilkes-Barre. Cole's theme plain on a piano with a little guitar, no orchestra: nothing works here. The bus leaves on time.
piece olympia_b3_69_the_615 key="C major" tempo=72 style=orchestral
master room.decay=1.6 room.wet=0.16
meta title = "The 6:15"
meta soundfont = "hq"

section station bars=8 meter=4/4 dynamic=p
section street  bars=8 meter=4/4 dynamic=pp
section bus     bars=8 meter=4/4 dynamic=mp
section asleep  bars=4 meter=4/4 dynamic=pp tempo_end=60

harmony
  @station: I . IV I | vi . IV V
  @street:  vi . iii . | IV . ii V
  @bus:     I . IV I | vi IV V .
  @asleep:  IV . I .

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
motif cole_inv < cole_head : invert

voice pno concert_grand role=melody octave=4 pan=0 engine=soundfont
  t_1: play motif=cole at=@station dynamic=mp articulation=legato
  t_2: play motif=cole at=@station.5 transpose=2 dynamic=mp articulation=legato
  t_3: play motif=cole_inv at=@street dynamic=p articulation=legato
  t_4: play motif=cole_slow at=@street.3 dynamic=pp articulation=legato
  t_5: play motif=cole_open at=@bus dynamic=mf articulation=legato
  t_6: play motif=cole at=@bus.5 dynamic=mf articulation=legato
  t_7: play motif=cole_head at=@asleep dynamic=pp articulation=legato
  t_h: humanize amount=0.7 timing=10

voice gt classical_guitar role=harmony octave=3 pan=-0.4 engine=soundfont
  g_1: chords at=@station.3 bars=6 figure="0 . 1 2 . 1 2 ." ring=true dynamic=p
  g_2: chords at=@street bars=8 figure="0 . . 1 2 . . ." ring=true dynamic=pp
  g_3: chords at=@bus bars=8 figure="0 2 1 2 0 2 1 2" ring=true dynamic=mp
  g_4: chords at=@asleep bars=4 figure="0 . 1 . 2 . . ." ring=true dynamic=pp
  lvl_gt: gain db=-4

voice ub upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@bus bars=8 dynamic=p
  b_2: drone at=@asleep bars=4 degree=0 dynamic=pp
  lvl_ub: gain db=-3
