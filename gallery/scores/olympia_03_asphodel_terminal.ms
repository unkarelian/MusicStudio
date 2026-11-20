# Olympia 3: Asphodel Terminal. The Styx ferry terminal: the dead come in, get counted, sit down.
# Five in a bar for the hall (a queue that never quite lines up), four for Cole watching it.
piece olympia_03_asphodel_terminal key="D dorian" tempo=72 style=orchestral
master room.decay=2.8 room.wet=0.3
meta title = "Asphodel Terminal"
meta soundfont = "hq"

section hall    bars=8 meter=5/4 dynamic=pp   -- the queue: plucked bass, a vibraphone counting
section watch   bars=8 meter=4/4 dynamic=p    -- Cole's theme, cello, plain
section courier bars=8 meter=5/4 dynamic=p    -- Hermes drops somebody off: his figure on a flute, over the queue
section again   bars=8 meter=4/4 dynamic=mp   -- Cole again; the clarinet moves when he holds
section ferry   bars=4 meter=5/4 dynamic=pp tempo_end=60

harmony
  @hall:    i . VII . i . IV .
  @watch:   i . VII i | IV . v i
  @courier: i . VII . III . IV .
  @again:   i . VII i | IV . VII i
  @ferry:   i . IV i

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
motif queue = 0:1/4 r:1/4 4:1/4 0:1/8 0:1/8 r:1/4                      -- five: root, a gap, fifth, root twice, a gap
motif count = r:1/4 4:1/4 r:1/2 2:1/4 | r:1/4 4:1/4 r:1/4 1:1/4 r:1/4  -- the vibraphone: somebody ticking names off
motif under = 4:1/1 | 3:1/2 2:1/2 | 4:1/1 | 5:1/2 4:1/2 | 2:1/1 | 3:1/2 4:1/2 | 2:1/2 1:1/2 | 0:1/1      -- moves when Cole holds

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  q_hall: play motif=queue at=@hall times=8 dynamic=p articulation=staccato
  q_cour: play motif=queue at=@courier times=8 dynamic=p articulation=staccato
  q_ferry: play motif=queue at=@ferry times=3 dynamic=pp articulation=staccato
  b_watch: bass at=@watch bars=8 pattern=root dynamic=pp
  b_again: bass at=@again bars=8 pattern=root dynamic=p
  b_end: phrase at=@ferry.4 steps="0:1/1~ 0:1/4" dynamic=pp

voice vib vibraphone role=ornament octave=5 pan=0.3 engine=soundfont bank=hq
  v_hall: play motif=count at=@hall.3 times=3 dynamic=pp
  v_cour: play motif=count at=@courier times=4 dynamic=pp
  v_ferry: play motif=count at=@ferry times=2 dynamic=pp
  lvl_vib: gain db=-4

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_watch: play motif=cole at=@watch dynamic=mp articulation=legato
  c_watch2: play motif=cole at=@watch.5 transpose=-3 dynamic=p articulation=legato
  c_again: play motif=cole at=@again dynamic=mp articulation=legato
  c_again2: play motif=cole at=@again.5 transform=["invert"] dynamic=mp articulation=legato
  u_hall: drone at=@hall.5 bars=4 degree=4 dynamic=pp
  u_ferry: phrase at=@ferry steps="0:1/2. -2:1/2 | 0:1/1 r:1/4" dynamic=pp
  c_shape: shape amount=0.4

voice fl flute role=melody octave=5 pan=0.15 engine=soundfont bank=hq
  h_1: play motif=hermes at=@courier.2 dynamic=mp
  h_2: play motif=hermes_tag at=@courier.4:3 transpose=2 dynamic=p
  h_3: play motif=hermes at=@courier.6 transpose=-1 dynamic=mp
  h_4: play motif=hermes_tag at=@courier.8:2 dynamic=pp
  lvl_fl: gain db=-6

voice cl clarinet role=counter octave=4 pan=-0.4 engine=soundfont bank=hq
  u_again: play motif=under at=@again dynamic=p articulation=legato
  u_shape: shape amount=0.4
  lvl_cl: gain db=-7
