# Olympia 5: The Old Man's Fields. Farmland going to weeds. Cole's theme over one held note;
# then, over a farmhouse door, the Saturnalia dance at half speed in a bar of seven slow beats,
# which is the first time it sounds like what it is.
piece olympia_05_the_old_mans_fields key="E minor" tempo=66 style=orchestral
master room.decay=3.0 room.wet=0.3
meta title = "The Old Man's Fields"
meta soundfont = "hq"

section field   bars=8 meter=4/4 dynamic=p    -- a drone, and Cole on the cello
section door    bars=4 meter=7/4 dynamic=mp   -- the sickle: the dance, augmented, english horn
section demeter bars=8 meter=4/4 dynamic=mp   -- Cole upside down; a viola that will not let the harmony move
section door2   bars=4 meter=7/4 dynamic=mf   -- the dance again with a bassoon under it, an octave down
section weeds   bars=4 meter=4/4 dynamic=pp tempo_end=54

harmony
  @field:   i . . VI | i . iv i
  @door:    i VII i v
  @demeter: iv . i . | iv . VI i
  @door2:   i VII VI v
  @weeds:   i . iv i

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
motif sickle < dance : augment:2                       -- the dance at half speed: seven slow beats to the bar
motif keep = 4:1/1~ 4:1/1 | 4:1/1~ 4:1/2 3:1/2 | 4:1/1~ 4:1/1 | 5:1/1 4:1/1     -- Demeter's viola: one note, kept

voice hi violin role=pad octave=5 pan=0.3 engine=soundfont bank=hq
  d_field: drone at=@field bars=8 degree=4 dynamic=pp
  d_door: drone at=@door bars=4 degree=0 dynamic=pp
  d_door2: drone at=@door2 bars=4 degree=0 dynamic=p
  d_weeds: drone at=@weeds bars=4 degree=4 dynamic=pp
  lvl_hi: gain db=-11

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@field dynamic=mp articulation=legato
  c_2: play motif=cole at=@field.5 transpose=2 dynamic=mp articulation=legato
  c_3: play motif=cole at=@demeter transform=["invert"] dynamic=mp articulation=legato
  c_4: play motif=cole at=@demeter.5 dynamic=mf articulation=legato
  c_end: play motif=cole_head at=@weeds dynamic=p articulation=legato
  c_last: phrase at=@weeds.2 steps="-2:1/1 | 0:1/1~ | 0:1/1" dynamic=pp
  c_shape: shape amount=0.5

voice eh english_horn role=melody octave=4 pan=0.1 engine=soundfont bank=hq
  s_1: play motif=sickle at=@door dynamic=mp articulation=legato
  s_2: play motif=sickle at=@door2 dynamic=mf articulation=legato
  s_shape: shape amount=0.4

voice bn bassoon role=counter octave=3 pan=-0.4 engine=soundfont bank=hq
  s_low: double source=eh octaves=-1 dynamic=mp in=@door2

voice va viola role=counter octave=4 pan=0.4 engine=soundfont bank=hq
  k_1: play motif=keep at=@demeter dynamic=p articulation=legato
  lvl_va: gain db=-5

voice cb contrabass role=bass octave=1 engine=soundfont bank=hq
  b_field: drone at=@field bars=8 dynamic=pp
  b_door: bass at=@door bars=4 pattern=root dynamic=p
  b_dem: bass at=@demeter bars=8 pattern=root dynamic=p
  b_door2: bass at=@door2 bars=4 pattern=root dynamic=mp
  b_weeds: drone at=@weeds bars=4 dynamic=pp
