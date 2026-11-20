# Olympia B2-36: a bakers' comedy. The throne motif in a cotton-wool beard: tuba and bassoon, a piccolo making fun. He laughs a second late. A shutter.
piece olympia_b2_36_the_dionysia key="C major" tempo=116 style=orchestral
master room.decay=1.8 room.wet=0.18
meta title = "The Dionysia"
meta soundfont = "hq"

section march   bars=8 meter=4/4 dynamic=mf
section pies    bars=8 meter=4/4 dynamic=mf
section late    bars=4 meter=4/4 dynamic=p tempo=88
section wreath  bars=8 meter=4/4 dynamic=f
section shutter bars=3 meter=4/4 dynamic=pp tempo=70

harmony
  @march:   I . V I | IV . V I
  @pies:    vi . ii V | I IV V I
  @late:    i . bVI V
  @wreath:  I . V I | IV I V I
  @shutter: i . .

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
motif oom = 0:1/4 r:1/4 4:1/4 r:1/4
motif throne_up < throne : transpose:4
motif throne_inv < throne : invert
motif throne_head < throne : fragment:0,3
motif titter = r:1/4 7:1/16 6:1/16 7:1/16 6:1/16 7:1/8 r:1/8 r:1/4

voice tba tuba role=bass octave=2 engine=soundfont bank=hq
  o_1: play motif=oom at=@march times=16 dynamic=mf articulation=staccato
  o_2: play motif=oom at=@wreath times=8 dynamic=f articulation=staccato
  o_3: drone at=@shutter bars=3 degree=0 dynamic=pp

voice bsn bassoon role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  t_1: play motif=throne at=@march dynamic=mf articulation=staccato
  t_2: play motif=throne at=@march.5 dynamic=mf articulation=staccato
  t_3: play motif=throne_inv at=@pies dynamic=mf articulation=staccato
  t_4: play motif=throne at=@wreath dynamic=f articulation=staccato
  t_5: play motif=throne_up at=@wreath.5 dynamic=f articulation=staccato

voice picc piccolo role=counter octave=5 pan=0.3 engine=soundfont bank=hq
  p_1: play motif=titter at=@march.2 times=1 dynamic=mf
  p_2: play motif=titter at=@march.4 times=1 dynamic=mf
  p_3: play motif=titter at=@march.6 times=3 dynamic=mf
  p_4: play motif=hermes at=@wreath.2 octave=6 dynamic=mf
  p_5: play motif=titter at=@wreath.5 times=4 dynamic=f
  lvl_picc: gain db=-5

voice tpt trumpet role=melody octave=4 pan=0.15 engine=soundfont bank=hq
  r_1: play motif=throne_up at=@pies.5 dynamic=mf articulation=staccato
  r_2: play motif=throne at=@wreath dynamic=f
  lvl_tpt: gain db=-3

voice tbn trombone role=melody octave=3 pan=-0.35 engine=soundfont bank=hq
  z_1: play motif=throne_head at=@late dynamic=p articulation=legato
  z_2: play motif=throne_head at=@late.3 transpose=-1 dynamic=p articulation=legato
  z_3: play motif=throne_head at=@shutter dynamic=pp articulation=legato

voice sn snare role=percussion pan=0.1
  x_1: groove at=@march bars=16 pattern="x.xxx.x.|x.xxX.xx" res=1/8 dynamic=mp
  x_2: groove at=@wreath bars=8 pattern="x.xxx.x.|x.xxX.xx" res=1/8 dynamic=mf
  lvl_sn: gain db=-6
