# Olympia 13: Kaukasos. A cold mountain and a chain. Cole's theme as it has always been;
# then the chain is struck and the same contour comes back with every step turned into a third,
# high violins and a horn, with the old theme under it on the cello as its own countermelody.
piece olympia_13_kaukasos key="E minor" tempo=72 style=orchestral
master room.decay=3.6 room.wet=0.32
meta title = "Kaukasos"
meta soundfont = "hq"

section wind  bars=8  dynamic=pp   -- a high fifth; metal, irregular
section cole  bars=8  dynamic=p    -- the theme, cello
section chain bars=8  dynamic=mf   -- the theme upside down on a horn; the metal finds a pulse; last bar, the blow
section open  bars=16 dynamic=f key="G major"   -- cole_open above, cole below
section air   bars=4  dynamic=p key="G major" tempo_end=58

stop from=@chain.8:3 until=@open keep=[]

harmony
  @wind:  i . . . | i . VI .
  @cole:  i . VI i | iv . v i
  @chain: i . VI VII | i iv V .
  @open:  I . IV I | vi IV V I | I . IV I | vi IV V .
  @air:   I IV I .

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
motif link = r:1/4 4:1/4 r:1/2 | r:1/2. 4:1/4 | r:1/1 | 4:1/4 r:1/2.          -- the chain: one pitch, no pattern you could tap
motif haul = 4:1/4 r:1/4 4:1/8 4:1/8 r:1/4                                   -- the chain, pulled

voice hi violin role=pad octave=6 pan=0.4 engine=soundfont bank=hq
  w_1: drone at=@wind bars=24 degree=4 dynamic=pp
  lvl_hi: gain db=-12

voice pipe metal_pipe role=ornament octave=3 pan=-0.4
  l_1: play motif=link at=@wind times=4 dynamic=p
  l_2: play motif=haul at=@chain times=7 dynamic=mf
  l_3: phrase at=@chain.8 steps="4:1/4! 4:1/4! r:1/2" dynamic=ff
  lvl_pipe: gain db=-2

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@cole dynamic=mp articulation=legato
  c_2: play motif=cole at=@cole.5 transpose=2 dynamic=mp articulation=legato
  c_3: play motif=cole at=@open dynamic=mf articulation=legato
  c_4: play motif=cole at=@open.5 transpose=2 dynamic=mf articulation=legato
  c_5: play motif=cole at=@open.9 dynamic=mf articulation=legato
  c_6: play motif=cole at=@open.13 transform=["invert"] dynamic=mf articulation=legato
  c_7: play motif=cole_head at=@air dynamic=mf articulation=legato
  c_8: phrase at=@air.2 steps="2:1/1 | 1:1/1~ | 1:1/1" dynamic=mp articulation=legato
  c_shape: shape amount=0.5
  lvl_vc: gain db=-2

voice hn horn role=melody octave=3 pan=0.2 engine=soundfont bank=hq
  n_1: play motif=cole at=@chain transform=["invert"] dynamic=mf articulation=legato
  n_2: play motif=cole at=@chain.5 transform=["invert"] transpose=2 dynamic=f articulation=legato
  n_3: play motif=cole_open at=@open.9 dynamic=f articulation=legato
  n_4: play motif=cole_open at=@open.13 transpose=-2 dynamic=f articulation=legato
  n_shape: shape amount=0.5

voice vn violin role=melody octave=4 pan=-0.4 engine=soundfont bank=hq
  o_1: play motif=cole_open at=@open dynamic=f articulation=legato
  o_2: play motif=cole_open at=@open.5 transpose=1 dynamic=f articulation=legato
  o_3: play motif=cole_open at=@open.9 octave=5 dynamic=ff articulation=legato
  o_4: play motif=cole_open at=@open.13 octave=5 transpose=-2 dynamic=ff articulation=legato
  o_shape: shape amount=0.6

voice str strings role=pad octave=4 pan=0 engine=soundfont bank=hq
  s_c: chords at=@cole bars=8 voicing=pad lead=true dynamic=pp
  s_o: chords at=@open bars=16 voicing=pad lead=true dynamic=mf
  s_a: chords at=@air bars=4 voicing=pad lead=true dynamic=pp
  lvl_str: gain db=-8

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_c: bass at=@cole bars=16 pattern=root dynamic=p
  b_o: bass at=@open bars=20 pattern=root dynamic=mf
  b_h: humanize amount=0.8 timing=5
