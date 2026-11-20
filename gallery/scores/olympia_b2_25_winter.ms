# Olympia B2-25: Erebus in a hard winter. The queue is long; the theme is slow and never gets past a third. An edict arrives.
piece olympia_b2_25_winter key="D minor" tempo=60 style=orchestral
master room.decay=3.0 room.wet=0.3
meta title = "Winter"
meta soundfont = "hq"

section queue  bars=8 meter=4/4 dynamic=p
section edict  bars=4 meter=4/4 dynamic=mp
section double bars=6 meter=4/4 dynamic=p
section floor  bars=3 meter=4/4 dynamic=pp tempo_end=50

harmony
  @queue:  i . VI i | iv . i .
  @edict:  VI . VII .
  @double: i . iv i | VI i
  @floor:  iv . i

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
motif frost = r:1/4 7:1/8 4:1/8 r:1/2
motif tread = 0:1/2 0:1/4 r:1/4
motif throne_head < throne : fragment:0,3

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: play motif=tread at=@queue times=8 dynamic=p
  b_2: drone at=@edict bars=4 degree=0 dynamic=p
  b_3: play motif=tread at=@double times=6 dynamic=p
  b_4: drone at=@floor bars=3 degree=0 dynamic=pp

voice eh english_horn role=melody octave=4 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole_slow at=@queue dynamic=mp articulation=legato
  c_2: play motif=cole at=@double dynamic=mp articulation=legato
  c_3: play motif=cole_head at=@double.5 transpose=2 dynamic=p articulation=legato
  c_4: play motif=cole_head at=@floor dynamic=pp articulation=legato
  c_shape: shape amount=0.4

voice cel celesta role=ornament octave=5 pan=0.4 engine=soundfont bank=hq
  f_1: play motif=frost at=@queue.2 times=3 dynamic=pp
  f_2: play motif=frost at=@double.2 times=4 dynamic=pp
  lvl_cel: gain db=-6

voice fl flute role=counter octave=5 pan=0.25 engine=soundfont bank=hq
  h_1: play motif=hermes at=@edict dynamic=mp
  lvl_fl: gain db=-3

voice hn horn role=counter octave=3 pan=-0.4 engine=soundfont bank=hq
  t_1: play motif=throne_head at=@edict.2 dynamic=mf
  lvl_hn: gain db=-3

voice hp harp role=harmony octave=3 pan=0.3 engine=soundfont bank=hq
  p_1: chords at=@queue bars=8 voicing=broken lead=true dynamic=pp
  p_2: chords at=@double bars=9 voicing=broken lead=true dynamic=pp
  lvl_hp: gain db=-4
  hp_h: humanize amount=0.5 timing=6
