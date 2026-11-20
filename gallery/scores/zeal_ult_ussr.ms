# GREAT PROLETARIAN MANIA -- the Soviet ult. Only the anthem's opening notes: the pickup, the leap, and one held chord.
piece zeal_ult_ussr key="D major" tempo=152 meter=4/4 style=electronic
master room.decay=1.8 room.wet=0.22 push=3

section a bars=3 dynamic=ff

harmony
  1: V I iii

motif hymn = r:3/4 4:1/4 | 7:1/2! 4:1/4. 5:1/8 | 6:1/1!
motif roots = r:3/4 4:1/4 | 0:1/2! 0:1/4 0:1/4 | 2:1/1!

voice lead monster_lead role=melody octave=5 engine=soundfont
  l1: play motif=hymn at=1 dynamic=ff
  lvl_l: gain db=8
voice choir heavy_square role=counter octave=3 engine=soundfont
  s1: play motif=hymn at=1 dynamic=ff
voice gtr amp_guitar role=harmony octave=2 engine=soundfont
  g1: play motif=roots at=1 dynamic=ff
  g2: play motif=roots at=1 transpose=4 dynamic=ff
  fx_g: drive amount=0.2
  lvl_g: gain db=-5
voice bass rbx_picked_bass role=bass octave=1 engine=soundfont
  b1: play motif=roots at=1 dynamic=ff
  lvl_b: gain db=5
voice drums kit_rock role=percussion engine=soundfont
  d0: beat at=1 bars=1 snare=........xxxxxxxx res=1/16 dynamic=ff
  d1: beat at=2 bars=1 kick=xxxxxxxx snare=..x...x. crash=x....... res=1/8 dynamic=ff
  d2: beat at=3 bars=1 kick=x....... crash=x....... res=1/8 dynamic=ff
  lvl_d: gain db=7
