# Olympia 9: The Gate. Tartarus. Almost nothing moves. Cole's theme at half speed at the bottom
# of a bassoon; once, lower still, the head of the dance stretched out past recognising.
# On the road up, in a major key, the Hermes figure slowed down until it is nearly kind.
piece olympia_09_the_gate key="D phrygian" tempo=54 style=ambient
master room.decay=5.0 room.wet=0.4
meta title = "The Gate"
meta soundfont = "hq"

section dark   bars=6 dynamic=pp    -- a low D and a drum, twice
section gate   bars=8 dynamic=p     -- Cole, augmented
section kronos bars=6 dynamic=p     -- the dance head at a quarter speed, tuba
section road   bars=8 dynamic=mp key="F major" tempo=63 tempo_end=54   -- Hermes, at half speed, clarinet and harp

harmony
  @dark:   i . . . . .
  @gate:   i . bII . i . . .
  @kronos: i . . bII i .
  @road:   I . IV . | I vi IV .

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
motif old < dance_head : augment:4
motif hermes_kind < hermes : augment:2

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  d_1: drone at=@dark bars=20 dynamic=pp retrigger="2/1"
  b_road: bass at=@road bars=8 pattern=root octave=1 dynamic=p

voice drum taiko role=percussion
  x_1: groove at=@dark.3 bars=1 pattern="X..." res=1/4 dynamic=p
  x_2: groove at=@dark.6 bars=1 pattern="X..." res=1/4 dynamic=p
  x_3: groove at=@gate.8 bars=1 pattern="..X." res=1/4 dynamic=p
  x_4: groove at=@kronos.4 bars=1 pattern="X..." res=1/4 dynamic=mp
  lvl_drum: gain db=14

voice bn bassoon role=melody octave=2 pan=-0.1 engine=soundfont bank=hq
  c_1: play motif=cole_slow at=@gate dynamic=p articulation=legato
  c_shape: shape amount=0.4

voice tuba tuba role=melody octave=2 pan=0.1 engine=soundfont bank=hq
  k_1: play motif=old at=@kronos dynamic=mf articulation=legato
  k_end: phrase at=@kronos.5 steps="r:1/2 0:1/2~ | 0:1/1" dynamic=pp

voice cl clarinet role=melody octave=4 pan=0.15 engine=soundfont bank=hq
  h_1: play motif=hermes_kind at=@road dynamic=mp articulation=legato
  h_2: play motif=hermes_kind at=@road.3 transpose=-1 dynamic=mp articulation=legato
  h_3: play motif=hermes_kind at=@road.5 dynamic=mp articulation=legato
  h_end: phrase at=@road.7 steps="2:1/2 1:1/2 | 1:1/1" dynamic=p articulation=legato
  h_shape: shape amount=0.6

voice hp harp role=harmony octave=3 pan=-0.3 engine=soundfont bank=hq
  hp_1: chords at=@road bars=8 voicing=arpeggio_up ring=true dynamic=p
  lvl_hp: gain db=-5

voice vc cello role=counter octave=3 pan=-0.2 engine=soundfont bank=hq
  c_road: play motif=cole_head at=@road.6 dynamic=p articulation=legato
  c_last: phrase at=@road.7 steps="0:1/1~ | 0:1/1" dynamic=pp
