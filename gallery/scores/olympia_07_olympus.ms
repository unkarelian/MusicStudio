# Olympia 7: Olympus. The nine are presented. The throne's tune is dotted and square and
# says everything twice; at the end of each phrase, at its elbow, the Hermes figure fills the gap.
piece olympia_07_olympus key="Eb major" tempo=76 style=orchestral
master room.decay=3.4 room.wet=0.3
meta title = "Olympus"
meta soundfont = "hq"

section hall   bars=8 dynamic=f     -- horns and trombones; a flute after every phrase
section cole   bars=8 dynamic=mp key="C minor"   -- Cole at the back of the room, cello; the throne tune goes on under him, quietly
section throne bars=8 dynamic=ff    -- everybody; the flute a third higher each time
section elbow  bars=4 dynamic=mp tempo_end=66    -- the brass stop; the figure is still going

harmony
  @hall:   I . IV V | I . IV V
  @cole:   i . VI VII | i . iv V
  @throne: I . IV V | vi IV V I
  @elbow:  I . IV I

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
motif throne_low < throne : augment:2

voice hn horn role=melody octave=3 pan=-0.3 engine=soundfont bank=hq
  t_1: play motif=throne at=@hall dynamic=f articulation=marcato
  t_2: play motif=throne at=@hall.5 dynamic=f articulation=marcato
  t_c: play motif=throne_low at=@cole dynamic=pp articulation=legato
  t_3: play motif=throne at=@throne transpose=2 dynamic=ff articulation=marcato
  t_4: play motif=throne at=@throne.5 dynamic=ff articulation=marcato
  t_end: phrase at=@elbow steps="0:1/1~ | 0:1/1 | r:1/1 | r:1/1" dynamic=mp
  lvl_hn: gain db=4

voice tbn brass_section role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  tb_1: chords at=@hall bars=8 voicing=block lead=true dynamic=mf
  tb_3: chords at=@throne bars=8 voicing=block lead=true dynamic=f
  tb_end: chords at=@elbow bars=2 voicing=block lead=true dynamic=mp
  lvl_tbn: gain db=-12

voice timp timpani role=bass octave=2 engine=soundfont bank=hq
  tp_1: phrase at=@hall steps="0:1/4 r:1/4 0:1/8 0:1/8 0:1/4 | r:1/1" dynamic=f
  tp_2: phrase at=@hall.5 steps="0:1/4 r:1/4 0:1/8 0:1/8 0:1/4 | r:1/1" dynamic=f
  tp_3: bass at=@throne bars=8 pattern=root rhythm="1/4 1/4 1/8 1/8 1/4" dynamic=f
  lvl_timp: gain db=-10

voice fl flute role=counter octave=5 pan=0.1 engine=soundfont bank=hq
  h_1: play motif=hermes at=@hall.2:3 dynamic=mf
  h_2: play motif=hermes_tag at=@hall.4:3 dynamic=mf
  h_3: play motif=hermes at=@hall.6:3 transpose=1 dynamic=mf
  h_4: play motif=hermes_tag at=@hall.8:3 transpose=2 dynamic=mf
  h_c: play motif=hermes_tag at=@cole.4:3 dynamic=p
  h_5: play motif=hermes at=@throne.2:3 transpose=2 dynamic=f
  h_6: play motif=hermes at=@throne.4:3 transpose=4 dynamic=f
  h_7: play motif=hermes at=@throne.6:3 transpose=2 dynamic=f
  h_8: play motif=hermes at=@throne.8:3 dynamic=f
  h_9: play motif=hermes at=@elbow.2 dynamic=mp
  h_10: play motif=hermes at=@elbow.3 transform=["retrograde"] dynamic=p
  h_11: phrase at=@elbow.4 steps="4:1/1" dynamic=pp
  lvl_fl: gain db=-8

voice vc cello role=melody octave=3 pan=-0.1 engine=soundfont bank=hq
  c_1: play motif=cole at=@cole dynamic=mf articulation=legato
  c_2: play motif=cole at=@cole.5 transform=["invert"] dynamic=mf articulation=legato
  c_shape: shape amount=0.5

voice str strings role=pad octave=4 pan=0 engine=soundfont bank=hq
  s_c: chords at=@cole bars=8 voicing=pad lead=true dynamic=p
  s_t: chords at=@throne bars=8 voicing=pad lead=true dynamic=mf
  s_e: chords at=@elbow bars=4 voicing=pad lead=true dynamic=p
  lvl_str: gain db=-10

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_all: bass at=@hall bars=28 pattern=root dynamic=mf
  b_h: humanize amount=0.8 timing=5
