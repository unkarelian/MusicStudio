# Olympia 8: Latmos. The observatory; a man who has been asleep a very long time.
# Ivy's song at half speed in a bar of six slow beats, high, with nothing moving under it.
piece olympia_08_latmos key="F# phrygian" tempo=60 style=ambient
master room.decay=4.5 room.wet=0.42
meta title = "Latmos"
meta soundfont = "hq"

section dome   bars=4 meter=6/4 dynamic=pp   -- two held notes and a glockenspiel
section sleep  bars=8 meter=6/4 dynamic=p    -- the song, augmented, celesta
section watch  bars=8 meter=6/4 dynamic=p    -- its second half upside down, low flute; the celesta keeps only the rocking bar
section still  bars=3 meter=6/4 dynamic=pp

harmony
  @dome:  i . . .
  @sleep: i . bII i | i . bII i
  @watch: i . VII i | bII . i .
  @still: i . .

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
motif ivy_slow < ivy : augment:2
motif ivy_low < ivy_b : invert:4 > augment:2
motif boat_slow < boat : augment:2
motif star = r:1/1 7:1/2 | r:1/2 4:1/1 | r:1/1. | r:1/4 9:1/4 r:1/1

voice hi1 violin role=pad octave=6 pan=-0.5 engine=soundfont bank=hq
  d_1: drone at=@dome bars=23 degree=0 dynamic=pp
  lvl_hi1: gain db=-12
voice hi2 violin role=pad octave=5 pan=0.5 engine=soundfont bank=hq
  d_2: drone at=@dome.2 bars=22 degree=4 dynamic=pp
  lvl_hi2: gain db=-12

voice glock glockenspiel role=ornament octave=6 pan=0.3 engine=soundfont bank=hq
  g_1: play motif=star at=@dome dynamic=pp
  g_2: play motif=star at=@watch.5 dynamic=pp
  g_3: phrase at=@still.2 steps="7:1/1. | 4:1/1." dynamic=pp
  lvl_glock: gain db=-6

voice cel celesta role=melody octave=5 pan=-0.1 engine=soundfont bank=hq
  i_1: play motif=ivy_slow at=@sleep dynamic=p
  i_2: play motif=boat_slow at=@watch.2 dynamic=pp
  i_3: play motif=boat_slow at=@watch.4 dynamic=pp
  i_4: play motif=boat_slow at=@watch.6 transpose=-2 dynamic=pp
  i_5: play motif=boat_slow at=@still dynamic=pp

voice fl flute role=melody octave=4 pan=0.1 engine=soundfont bank=hq
  w_1: play motif=ivy_low at=@watch dynamic=p articulation=legato
  w_2: play motif=ivy_low at=@watch.5 transpose=-1 dynamic=p articulation=legato
  w_shape: shape amount=0.6
  lvl_fl: gain db=-7
