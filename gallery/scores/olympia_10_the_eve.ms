# Olympia 10: The Eve. Kallipolis the night before. The dance at full size: fiddle alone,
# then the band; Ivy's song in six rides across it once; then the whole thing a step up.
piece olympia_10_the_eve key="A dorian" tempo=132 style=orchestral
master room.decay=1.8 room.wet=0.2
meta title = "The Eve"
meta soundfont = "hq"

section tune  bars=8  meter=7/8 dynamic=mf   -- fiddle and tambourine
section band  bars=16 meter=7/8 dynamic=f    -- accordion on the tune too, guitar, bass, drum
section ivy   bars=8  meter=6/8 dynamic=mf   -- the band drops to six; Ivy's song on the oboe
section up    bars=16 meter=7/8 dynamic=ff key="B dorian"   -- everybody, a step higher, a flute on top
section last  bars=4  meter=7/8 dynamic=f key="B dorian"

harmony
  @tune: [i . VII i]*2
  @band: [i . VII i | i IV VII i]*2
  @ivy:  i . IV i | i IV VII i
  @up:   [i . VII i | i IV VII i]*2
  @last: i VII i .

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
motif dance_b = 7:1/8 6:1/8 4:1/8 6:1/8 7:1/8 9:1/8 7:1/8 | 6:1/4 4:1/8 2:1/8 4:1/8 5:1/8 4:1/8 | 7:1/8 6:1/8 4:1/8 6:1/8 4:1/8 2:1/8 1:1/8 | 2:1/4 1:1/4 0:3/8      -- the turn: starts where the tune tops out
motif thump = 0:1/4 0:1/4 4:1/4. anchor=scale

voice fid fiddle role=melody octave=4 pan=-0.3 engine=soundfont bank=hq
  d_1: play motif=dance at=@tune times=2 dynamic=mf
  d_2: play motif=dance at=@band dynamic=f
  d_3: play motif=dance_b at=@band.5 dynamic=f
  d_4: play motif=dance at=@band.9 transform=["embellish:neighbor,7 20"] dynamic=f
  d_5: play motif=dance_b at=@band.13 dynamic=f
  d_6: play motif=dance at=@up dynamic=ff
  d_7: play motif=dance_b at=@up.5 dynamic=ff
  d_8: play motif=dance at=@up.9 dynamic=ff
  d_9: play motif=dance_b at=@up.13 dynamic=ff
  d_10: play motif=dance at=@last dynamic=f
  d_h: humanize amount=0.5 timing=7

voice acc accordion role=melody octave=4 pan=0.3 engine=soundfont bank=hq
  a_1: double source=fid dynamic=mf in=@band
  a_ivy: chords at=@ivy bars=8 voicing=pad lead=true dynamic=p
  a_2: double source=fid interval=2 dynamic=f in=@up
  a_3: double source=fid interval=2 dynamic=mf in=@last
  lvl_acc: gain db=-5

voice fl flute role=counter octave=5 pan=0.1 engine=soundfont bank=hq
  f_1: double source=fid octaves=1 dynamic=mf in=@up.9-16
  f_h: play motif=hermes_tag at=@up.4:3 dynamic=mf
  lvl_fl: gain db=-4

voice ob oboe role=melody octave=4 pan=0 engine=soundfont bank=hq
  i_1: play motif=ivy at=@ivy dynamic=f articulation=legato
  i_shape: shape amount=0.5

voice gtr classical_guitar role=harmony octave=3 pan=-0.5 engine=soundfont
  g_1: chords at=@band bars=16 figure="0+1+2 . 1+2 . 0+1+2 1+2 1+2" dynamic=mf
  g_ivy: chords at=@ivy bars=8 figure="0 2 1 2 1 2" ring=true dynamic=mp
  g_2: chords at=@up bars=20 figure="0+1+2 . 1+2 . 0+1+2 1+2 1+2" dynamic=f
  lvl_gtr: gain db=-10

voice bass upright_bass role=bass octave=2 engine=soundfont bank=hq
  b_1: play motif=thump at=@band times=16 dynamic=mf
  b_ivy: bass at=@ivy bars=8 pattern=root dynamic=mp
  b_2: play motif=thump at=@up times=20 dynamic=f
  b_h: humanize amount=0.8 timing=5

voice tamb tambourine role=percussion pan=0.5
  t_1: groove at=@tune.3 bars=22 pattern="X.x.X.x" res=1/8 dynamic=mf
  t_2: groove at=@up bars=20 pattern="X.x.Xxx" res=1/8 dynamic=f
  lvl_tamb: gain db=14

voice drum taiko role=percussion pan=-0.1
  x_1: groove at=@band bars=16 pattern="X...x..|X...x.x" res=1/8 dynamic=mf
  x_2: groove at=@up bars=20 pattern="X...x..|X...x.x" res=1/8 dynamic=f
  lvl_drum: gain db=6
