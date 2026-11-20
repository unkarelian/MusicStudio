# Olympia 11: Saturnalia. The procession in four, stiff; the dance in seven, everybody;
# the Hermes figure comes in over the dance three times, nearer each time; the fourth time
# it is on a trumpet, and the dance is cut off in the middle of its second bar.
piece olympia_11_saturnalia key="A dorian" tempo=138 style=orchestral
master room.decay=2.0 room.wet=0.22
meta title = "Saturnalia"
meta soundfont = "hq"

section procession bars=12 meter=4/4 tempo=84 dynamic=f key="A major"   -- the throne tune, the king pouring the wine
section dance      bars=16 meter=7/8 dynamic=f     -- the square
section pour       bars=12 meter=7/8 dynamic=mf    -- the dance goes on, lower; the flute figure, three times
section stab       bars=2  meter=7/8 dynamic=ff    -- the tune starts again and does not get through its second bar
section after      bars=3  meter=4/4 tempo=60 dynamic=pp   -- one bar of nothing; then a low note that is not the tonic

stop from=@stab.2:3 until=@after.2 keep=[]

harmony
  @procession: I . IV V | I . IV V | vi IV V I
  @dance: [i . VII i | i IV VII i]*2
  @pour:  i . VII i | i . VII i | IV . VII i
  @stab:  i .
  @after: i bII .

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
motif dance_b = 7:1/8 6:1/8 4:1/8 6:1/8 7:1/8 9:1/8 7:1/8 | 6:1/4 4:1/8 2:1/8 4:1/8 5:1/8 4:1/8 | 7:1/8 6:1/8 4:1/8 6:1/8 4:1/8 2:1/8 1:1/8 | 2:1/4 1:1/4 0:3/8
motif thump = 0:1/4 0:1/4 4:1/4.
motif knife < hermes : fragment:0,5                      -- the run up and the first note back: as far as it gets

voice hn horn role=melody octave=3 pan=-0.3 engine=soundfont bank=hq
  t_1: play motif=throne at=@procession dynamic=f articulation=marcato
  t_2: play motif=throne at=@procession.5 dynamic=f articulation=marcato
  t_3: play motif=throne at=@procession.9 transpose=2 dynamic=ff articulation=marcato
  lvl_hn: gain db=3

voice brass brass_section role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  br_1: chords at=@procession bars=12 voicing=block lead=true dynamic=mf
  lvl_brass: gain db=-12

voice timp timpani role=bass octave=2 engine=soundfont bank=hq
  tp_1: bass at=@procession bars=12 pattern=root rhythm="1/4 1/4 1/8 1/8 1/4" dynamic=f
  tp_st: phrase at=@stab steps="0:1/8 0:1/8 0:1/8 0:1/8 0:1/8 0:1/8 0:1/8 | 0:1/4" dynamic=ff
  lvl_timp: gain db=-4

voice fid fiddle role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  d_1: play motif=dance at=@dance dynamic=f
  d_2: play motif=dance_b at=@dance.5 dynamic=f
  d_3: play motif=dance at=@dance.9 dynamic=ff
  d_4: play motif=dance_b at=@dance.13 dynamic=ff
  d_5: play motif=dance at=@pour octave=3 dynamic=mf
  d_6: play motif=dance at=@pour.5 octave=3 dynamic=mf
  d_7: play motif=dance_b at=@pour.9 dynamic=f
  d_8: play motif=dance at=@stab dynamic=ff
  d_h: humanize amount=0.5 timing=7

voice acc accordion role=melody octave=4 pan=0.3 engine=soundfont bank=hq
  a_1: double source=fid interval=2 dynamic=f in=@dance.9-16
  a_2: chords at=@pour bars=12 voicing=pad lead=true dynamic=mp
  a_3: double source=fid interval=2 dynamic=ff in=@stab
  lvl_acc: gain db=-5

voice gtr classical_guitar role=harmony octave=3 pan=-0.5 engine=soundfont
  g_1: chords at=@dance bars=30 figure="0+1+2 . 1+2 . 0+1+2 1+2 1+2" dynamic=mf
  lvl_gtr: gain db=-10

voice bass upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_p: bass at=@procession bars=12 pattern=root dynamic=mf
  b_1: play motif=thump at=@dance times=30 dynamic=f
  b_after: phrase at=@after.2 steps="1:1/1~ | 1:1/1" dynamic=pp
  b_h: humanize amount=0.8 timing=5

voice tamb tambourine role=percussion pan=0.5
  t_d: groove at=@dance bars=30 pattern="X.x.Xxx" res=1/8 dynamic=f
  t_pour: dynamics from=@pour until=@stab start=p end=mp
  lvl_tamb: gain db=10

voice drum taiko role=percussion pan=-0.1
  x_d: groove at=@dance bars=30 pattern="X...x..|X...x.x" res=1/8 dynamic=f
  x_pour: dynamics from=@pour until=@stab start=p end=mf
  lvl_drum: gain db=4

voice fl flute role=counter octave=5 pan=0.1 engine=soundfont bank=hq
  h_p: play motif=hermes_tag at=@procession.8:3 dynamic=mp
  h_1: play motif=hermes at=@pour.3 dynamic=mp
  h_2: play motif=hermes at=@pour.7 transpose=2 dynamic=mf
  h_3: play motif=hermes at=@pour.11 transpose=3 dynamic=f
  lvl_fl: gain db=-3

voice tpt trumpet role=melody octave=4 pan=0 engine=soundfont bank=hq
  k_1: play motif=hermes_tag at=@stab dynamic=ff articulation=marcato
  k_2: play motif=knife at=@stab.2 transpose=2 dynamic=ff articulation=marcato
  lvl_tpt: gain db=2
