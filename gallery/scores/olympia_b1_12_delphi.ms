# Olympia B1-12: Leo plays for the crowd, easy and bright. Then he sits on the tripod: three flat sentences on one note. Hermes writes it down.
piece olympia_b1_12_delphi key="D mixolydian" tempo=96 style=orchestral
master room.decay=2.4 room.wet=0.25
meta title = "Delphi"
meta soundfont = "hq"

section tune   bars=16 meter=4/4 dynamic=mf
section tripod bars=9  meter=4/4 tempo=60 dynamic=pp
section pencil bars=3  meter=4/4 tempo=60 dynamic=pp

harmony
  @tune:   I . VII I | IV . V I | I . VII IV | I IV V I
  @tripod: I . . . . . . . .
  @pencil: VII . I

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
motif leo = 4:1/8 5:1/8 7:1/4 5:1/8 4:1/8 2:1/4 | 3:1/8 4:1/8 5:1/4 4:1/2 | 4:1/8 5:1/8 7:1/4 8:1/8 7:1/8 5:1/4 | 4:1/4 2:1/4 0:1/2
motif leo_b = 7:1/4 8:1/8 7:1/8 5:1/4 4:1/4 | 5:1/4 4:1/8 2:1/8 4:1/2 | 2:1/8 4:1/8 5:1/4 4:1/8 2:1/8 1:1/4 | 0:1/1
motif said = 0:1/8 0:1/8 0:1/4 0:1/8 0:1/8 0:1/4 | 0:1/4 0:1/4 -1:1/2 | r:1/1
motif hermes_kind < hermes : augment:2

voice gtr harp role=harmony octave=3 pan=-0.25 engine=soundfont bank=hq
  g_1: chords at=@tune bars=16 voicing=broken lead=true dynamic=mp
  lvl_g: gain db=-4

voice fl flute role=melody octave=5 pan=0.15 engine=soundfont bank=hq
  l_1: play motif=leo at=@tune dynamic=mf
  l_2: play motif=leo_b at=@tune.5 dynamic=mf
  l_3: play motif=leo at=@tune.9 transpose=1 dynamic=mf
  l_4: play motif=leo_b at=@tune.13 dynamic=mp
  l_shape: shape amount=0.5
  l_h: humanize amount=0.5 timing=8

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@tune bars=16 pattern=root dynamic=mp
  b_2: drone at=@tripod bars=9 degree=0 dynamic=pp
  lvl_cb: gain db=-3

voice cl clarinet role=melody octave=4 pan=0 engine=soundfont bank=hq
  s_1: play motif=said at=@tripod dynamic=mp
  s_2: play motif=said at=@tripod.4 dynamic=mp
  s_3: play motif=said at=@tripod.7 dynamic=mp
  k_1: play motif=hermes_kind at=@pencil dynamic=pp articulation=legato
