# Olympia 4: Paphos Market. A sunny island; Ivy's boat song in six, and from one stall
# a dance in seven that nobody is playing very loudly yet.
piece olympia_04_paphos_market key="A mixolydian" tempo=92 style=orchestral
master room.decay=1.6 room.wet=0.18
meta title = "Paphos Market"
meta soundfont = "hq"

section sun   bars=8  meter=6/8 dynamic=mp   -- guitar alone, rocking
section ivy1  bars=16 meter=6/8 dynamic=mf   -- the whole song on an oboe, twice
section stall bars=12 meter=7/8 dynamic=p    -- the dance, small: a recorder and a tambourine
section ivy2  bars=16 meter=6/8 dynamic=mf   -- the song again; a fiddle has picked up the dance's head under it
section out   bars=4  meter=6/8 dynamic=p

harmony
  @sun:   I . IV I | I . VII I
  @ivy1:  [I . IV I | I IV V I]*2
  @stall: [i . VII i]*3
  @ivy2:  [I . IV I | I IV VII I]*2
  @out:   I IV I .

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
motif stroll = 0:1/4. 2:1/4. | 0:1/4. 2:1/4 1:1/8 anchor=chord

voice gtr classical_guitar role=harmony octave=3 pan=-0.3 engine=soundfont
  g_sun:  chords at=@sun bars=8 figure="0 2 1 2 1 2" ring=true dynamic=mp
  g_ivy1: chords at=@ivy1 bars=16 figure="0 2 1 2 1 2" ring=true dynamic=mp
  g_stall: chords at=@stall bars=12 figure="0 . 1 . 0 1 2" dynamic=p
  g_ivy2: chords at=@ivy2 bars=16 figure="0 2 1 2 1 2" ring=true dynamic=mp
  g_out:  chords at=@out bars=4 figure="0 2 1 2 1 2" ring=true dynamic=p
  g_h: humanize amount=0.5 timing=8
  lvl_gtr: gain db=-5

voice ob oboe role=melody octave=4 pan=0.1 engine=soundfont bank=hq
  i_sun: play motif=boat at=@sun.5 times=2 every="6/8" dynamic=p
  i_1: play motif=ivy at=@ivy1 dynamic=mf articulation=legato
  i_2: play motif=ivy at=@ivy1.9 transform=["embellish:neighbor,2 6"] dynamic=mf articulation=legato
  i_3: play motif=ivy at=@ivy2 dynamic=mf articulation=legato
  i_4: play motif=ivy_b at=@ivy2.9 dynamic=mf articulation=legato
  i_5: play motif=ivy_b at=@ivy2.13 transpose=2 dynamic=mp articulation=legato
  i_out: play motif=boat at=@out dynamic=p
  i_end: phrase at=@out.2 steps="4:1/4. 1:1/4. | 0:1/2. | r:1/2." dynamic=p
  i_shape: shape amount=0.5

voice rec recorder role=melody octave=5 pan=0.5 engine=soundfont bank=hq
  d_1: play motif=dance at=@stall dynamic=p
  d_2: play motif=dance at=@stall.5 dynamic=mp
  d_3: play motif=dance_head at=@stall.9 times=2 every="7/8" dynamic=p
  d_4: play motif=dance_head at=@stall.11 dynamic=pp

voice tamb tambourine role=percussion pan=0.5
  t_1: groove at=@stall.3 bars=10 pattern="X.x.X.x" res=1/8 dynamic=p
  lvl_tamb: gain db=12

voice fid fiddle role=counter octave=4 pan=-0.5 engine=soundfont bank=hq
  f_1: play motif=dance_head at=@ivy2.3 transform=["rhythmize:1/8 1/8 1/8 1/8 1/8 1/8 1/4."] dynamic=p
  f_2: play motif=dance_head at=@ivy2.7 transform=["rhythmize:1/8 1/8 1/8 1/8 1/8 1/8 1/4."] dynamic=p
  f_3: play motif=dance_head at=@ivy2.11 transform=["rhythmize:1/8 1/8 1/8 1/8 1/8 1/8 1/4."] transpose=-3 dynamic=p
  f_4: play motif=dance_head at=@ivy2.15 transform=["rhythmize:1/8 1/8 1/8 1/8 1/8 1/8 1/4."] dynamic=pp

voice bass upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_1: play motif=stroll at=@ivy1 times=8 dynamic=mp
  b_2: play motif=stroll at=@ivy2 times=8 dynamic=mp
  b_st: bass at=@stall bars=12 pattern=root dynamic=p
  b_out: bass at=@out bars=4 pattern=root dynamic=p
  b_h: humanize amount=0.8 timing=6
