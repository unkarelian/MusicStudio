# Olympia 12: Misrule. The city that night. Three tunes that do not fit: the dance in seven
# (the crowd), the throne tune still in four laid across it (the old guard), and the Hermes
# figure climbing in sequence over both. Ivy's rocking bar, once, in the middle.
piece olympia_12_misrule key="D minor" tempo=144 style=orchestral
master room.decay=2.0 room.wet=0.2
meta title = "Misrule"
meta soundfont = "hq"

section riot  bars=16 meter=7/8 dynamic=f    -- the dance, minor now, low strings driving
section guard bars=8  meter=4/4 dynamic=ff   -- the throne tune, trombones; the figure answers every bar
section chase bars=16 meter=7/8 dynamic=f    -- dance a fourth up; throne tune across the bar lines; the figure in sequence
section ivy   bars=8  meter=6/8 dynamic=mp   -- tremolo; the rocking bar on an oboe
section all   bars=12 meter=7/8 dynamic=ff   -- all three
section out   bars=2  meter=7/8 dynamic=f

harmony
  @riot:  [i . VII i | i iv VII i]*2
  @guard: i . VI V | i . iv V
  @chase: [iv . III iv | iv VII III iv]*2
  @ivy:   i . VI . | iv . V .
  @all:   [i . VII i]*2 | i iv V .
  @out:   i .

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
motif drive = 0:1/8 0:1/8 0:1/8 0:1/8 4:1/8 0:1/8 0:1/8 anchor=scale
motif hermes_run < hermes : sequence:3,1

voice vn violin role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  d_1: play motif=dance at=@riot dynamic=f
  d_2: play motif=dance_b at=@riot.5 dynamic=f
  d_3: play motif=dance at=@riot.9 transform=["invert"] octave=5 dynamic=f
  d_4: play motif=dance_b at=@riot.13 dynamic=f
  d_5: play motif=dance at=@chase transpose=3 dynamic=f
  d_6: play motif=dance_b at=@chase.5 transpose=3 dynamic=f
  d_7: play motif=dance at=@chase.9 transpose=3 dynamic=ff
  d_8: play motif=dance_b at=@chase.13 transpose=3 dynamic=ff
  tr_ivy: chords at=@ivy bars=8 voicing=pad tones=2 dynamic=pp
  d_9: play motif=dance at=@all dynamic=ff
  d_10: play motif=dance_b at=@all.5 dynamic=ff
  d_11: play motif=dance at=@all.9 dynamic=ff
  d_12: play motif=dance_head at=@out dynamic=ff
  d_13: phrase at=@out.2 steps="0:1/4! r:5/8" dynamic=ff
  d_h: humanize amount=0.4 timing=6

voice tbn trombone role=counter octave=3 pan=0.4 engine=soundfont bank=hq
  t_1: play motif=throne at=@guard dynamic=ff articulation=marcato
  t_2: play motif=throne at=@guard.5 transpose=-2 dynamic=ff articulation=marcato
  t_3: play motif=throne at=@chase.5 dynamic=f articulation=marcato
  t_4: play motif=throne at=@chase.11 dynamic=f articulation=marcato
  t_5: play motif=throne at=@all dynamic=ff articulation=marcato
  t_6: play motif=throne at=@all.6 dynamic=ff articulation=marcato
  lvl_tbn: gain db=-3

voice picc piccolo role=counter octave=5 pan=0.1 engine=soundfont bank=hq
  h_1: play motif=hermes at=@guard.2 dynamic=f
  h_2: play motif=hermes at=@guard.4 transpose=1 dynamic=f
  h_3: play motif=hermes at=@guard.6 transpose=2 dynamic=f
  h_4: play motif=hermes at=@guard.8 transpose=4 dynamic=f
  h_5: play motif=hermes_run at=@chase.2 dynamic=mf
  h_6: play motif=hermes_run at=@chase.9 transpose=2 dynamic=f
  h_7: play motif=hermes_run at=@all.3 dynamic=f
  h_8: play motif=hermes_run at=@all.8 transpose=2 dynamic=ff
  lvl_picc: gain db=-3

voice ob oboe role=melody octave=4 pan=0 engine=soundfont bank=hq
  i_1: play motif=boat at=@ivy times=2 every="6/8" dynamic=mf articulation=legato
  i_2: play motif=ivy_b at=@ivy.3 dynamic=mf articulation=legato
  i_3: play motif=boat at=@ivy.7 transpose=1 dynamic=mp articulation=legato
  i_4: phrase at=@ivy.8 steps="4:1/2." dynamic=mp
  i_shape: shape amount=0.5

voice vc cello role=bass octave=2 pan=-0.1 engine=soundfont bank=hq
  b_1: play motif=drive at=@riot times=16 dynamic=f articulation=marcato
  b_g: bass at=@guard bars=8 pattern=octaves rhythm="1/8 1/8 1/8 1/8 1/8 1/8 1/8 1/8" dynamic=f
  b_2: play motif=drive at=@chase transpose=3 times=16 dynamic=f articulation=marcato
  b_i: drone at=@ivy bars=8 dynamic=p
  b_3: play motif=drive at=@all times=13 dynamic=ff articulation=marcato
  b_h: humanize amount=0.9 timing=4

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  cb_1: bass at=@riot bars=16 pattern=root dynamic=f
  cb_2: bass at=@guard bars=8 pattern=root dynamic=f
  cb_3: bass at=@chase bars=16 pattern=root dynamic=f
  cb_4: bass at=@all bars=13 pattern=root dynamic=ff
  cb_h: humanize amount=0.8 timing=5
  lvl_cb: gain db=-3

voice drum taiko role=percussion pan=-0.1
  x_1: groove at=@riot bars=16 pattern="X...x.x|X.x.x.x" res=1/8 dynamic=f
  x_g: groove at=@guard bars=8 pattern="X.x.X.xx" res=1/8 dynamic=f
  x_2: groove at=@chase bars=16 pattern="X...x.x|X.x.x.x" res=1/8 dynamic=f
  x_3: groove at=@all bars=13 pattern="X.x.X.x|X.x.xxx" res=1/8 dynamic=ff
  lvl_drum: gain db=3

voice tamb tambourine role=percussion pan=0.5
  t_r: groove at=@riot.9 bars=8 pattern="X.x.Xxx" res=1/8 dynamic=mf
  t_a: groove at=@all bars=12 pattern="X.x.Xxx" res=1/8 dynamic=f
  lvl_tamb: gain db=12
