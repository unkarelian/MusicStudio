# Olympia 6: Nysa, Empty House. Ivy's song with nobody under it; then a harp finds the chords;
# then, from down in the town, the dance, far off, while the oboe only holds notes.
piece olympia_06_nysa_empty_house key="E dorian" tempo=84 style=orchestral
master room.decay=3.2 room.wet=0.34
meta title = "Nysa, Empty House"
meta soundfont = "hq"

section alone bars=8  meter=6/8 dynamic=p    -- oboe, unaccompanied
section rooms bars=16 meter=6/8 dynamic=mp   -- the song backwards, then upside down, over a harp
section far   bars=12 meter=7/8 dynamic=pp   -- the town choosing its king: fiddle, tambourine, a long way off
section back  bars=8  meter=6/8 dynamic=p tempo_end=66   -- the second half of the song only; it stops on the wrong chord

harmony
  @alone: i . . . | i . . .
  @rooms: i . IV i | i IV VII i | i . IV i | VI IV v .
  @far:   [i . VII i]*3
  @back:  i . IV i | i IV . .

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
motif ivy_back < ivy_a : retrograde
motif ivy_under < ivy_b : invert:4

voice ob oboe role=melody octave=4 pan=0.05 engine=soundfont bank=hq
  i_1: play motif=ivy at=@alone dynamic=mp articulation=legato
  i_2: play motif=ivy_back at=@rooms dynamic=mp articulation=legato
  i_3: play motif=ivy_b at=@rooms.5 dynamic=mp articulation=legato
  i_4: play motif=ivy_a at=@rooms.9 transpose=2 dynamic=mf articulation=legato
  i_5: play motif=ivy_under at=@rooms.13 dynamic=mp articulation=legato
  i_far: phrase at=@far.3 steps="4:7/8~ | 4:7/8 | r:7/8 | r:7/8 | 2:7/8~ | 2:7/8 | r:7/8 | r:7/8 | 1:7/8~ | 1:7/8" dynamic=pp articulation=legato
  i_6: play motif=ivy_b at=@back dynamic=p articulation=legato
  i_7: phrase at=@back.5 steps="4:1/4 5:1/8 4:1/4 2:1/8 | 1:1/2.~ | 1:1/2.~ | 1:1/2." dynamic=pp articulation=legato
  i_shape: shape amount=0.55
  i_farlvl: dynamics from=@far until=@far.end start=pp end=pp

voice hp harp role=harmony octave=3 pan=-0.3 engine=soundfont bank=hq
  h_rooms: chords at=@rooms bars=16 figure="0 . 1 2 . 1" ring=true dynamic=p
  h_back: chords at=@back bars=8 figure="0 . . 1 2 ." ring=true dynamic=pp
  lvl_hp: gain db=-5

voice fid fiddle role=melody octave=4 pan=0.7 engine=soundfont bank=hq
  d_1: play motif=dance at=@far dynamic=pp
  d_2: play motif=dance at=@far.5 dynamic=p
  d_3: play motif=dance at=@far.9 dynamic=pp
  d_fade: dynamics from=@far.9 until=@far.end start=p end=pp
  fx_far: filter start=1400 end=1400
  lvl_fid: gain db=-3

voice tamb tambourine role=percussion pan=0.7
  t_1: groove at=@far bars=12 pattern="X.x.X.x" res=1/8 dynamic=pp
  fx_tfar: filter start=3000 end=3000
  lvl_tamb: gain db=30

voice vc cello role=bass octave=2 pan=-0.1 engine=soundfont bank=hq
  b_rooms: drone at=@rooms.9 bars=8 dynamic=pp
  b_far: drone at=@far bars=12 dynamic=pp
  b_back: drone at=@back bars=4 dynamic=pp
  b_last: drone at=@back.5 bars=4 degree=3 dynamic=pp
