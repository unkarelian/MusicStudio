# Olympia B2-38: the ones who weren't locked up, at dinner. Old, slow and cold. The throne tune at half speed, remembered by people who were there before it.
piece olympia_b2_38_the_titans_table key="E phrygian" tempo=50 style=orchestral
master room.decay=3.6 room.wet=0.34
meta title = "The Titans' Table"
meta soundfont = "hq"

section table bars=8 meter=4/4 dynamic=pp
section old   bars=6 meter=4/4 dynamic=mf
section asked bars=2 meter=4/4 dynamic=pp
section out   bars=3 meter=4/4 dynamic=pp tempo_end=42

harmony
  @table: i . bII i | iv . i .
  @old:   VI . bII i | iv i
  @asked: bII .
  @out:   i . .

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
motif throne_old < throne : augment:2
motif throne_inv < throne : invert > augment:2
motif moon = r:1/2 7:1/4 4:1/4 | 5:1/1
motif moon_low < moon : transpose:-2

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: drone at=@table bars=19 degree=0 dynamic=pp

voice tr tremolo_strings role=harmony octave=4 pan=0 engine=soundfont bank=hq
  s_1: chords at=@table bars=16 voicing=pad lead=true dynamic=pp
  lvl_tr: gain db=-7

voice hn horn role=melody octave=3 pan=-0.25 engine=soundfont bank=hq
  t_1: play motif=throne_old at=@table dynamic=p articulation=legato
  t_2: play motif=throne_inv at=@old dynamic=f articulation=legato
  t_shape: shape amount=0.4

voice cel celesta role=ornament octave=5 pan=0.4 engine=soundfont bank=hq
  m_1: play motif=moon at=@table.3 dynamic=pp
  m_2: play motif=moon_low at=@table.7 dynamic=pp
  m_3: play motif=moon at=@old.3 dynamic=pp
  m_4: play motif=moon at=@out dynamic=pp
  lvl_cel: gain db=-5

voice fl flute role=counter octave=5 pan=0.2 engine=soundfont bank=hq
  h_1: play motif=hermes_tag at=@asked dynamic=pp
  i_1: play motif=boat at=@old.5 dynamic=pp articulation=legato
  lvl_fl: gain db=-5

voice bsn bassoon role=counter octave=2 pan=0.1 engine=soundfont bank=hq
  k_1: phrase at=@old steps="0:1/1 | -1:1/1 | 1:1/1 | 0:1/1 | 3:1/1 | 0:1/1" dynamic=p articulation=legato
  lvl_bsn: gain db=-4
