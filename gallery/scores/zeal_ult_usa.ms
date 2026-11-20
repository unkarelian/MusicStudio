# STAR SPANGLED STRIKE -- the American ult. The first line of the anthem, played like an air raid.
piece zeal_ult_usa key="Bb major" tempo=132 meter=3/4 style=electronic
master room.decay=1.6 room.wet=0.2 push=3

section a bars=5 dynamic=ff

harmony
  1: I I vi V I

motif banner = r:1/2 4:3/16 2:1/16 | 0:1/4! 2:1/4 4:1/4 | 7:1/2! 9:3/16 8:1/16 | 7:1/4! 2:1/4 #3:1/4 | 4:3/4!
motif roots = r:3/4 | 0:3/4! | 0:3/4! | 5:1/2! 5:1/4 | 4:3/4!

voice lead monster_lead role=melody octave=4 engine=soundfont
  l1: play motif=banner at=1 dynamic=ff
  lvl_l: gain db=8
voice brass heavy_square role=counter octave=3 engine=soundfont
  s1: play motif=banner at=1 dynamic=ff
voice gtr amp_guitar role=harmony octave=2 engine=soundfont
  g1: play motif=roots at=1 dynamic=ff
  g2: play motif=roots at=1 transpose=4 dynamic=ff
  fx_g: drive amount=0.2
  lvl_g: gain db=-5
voice bass rbx_picked_bass role=bass octave=1 engine=soundfont
  b1: play motif=roots at=1 dynamic=ff
  lvl_b: gain db=5
voice drums kit_rock role=percussion engine=soundfont
  d0: beat at=1 bars=1 snare=....xxxxxxxx res=1/16 dynamic=ff
  d1: beat at=2 bars=3 kick=x.xx.x snare=..x.x. crash=x..... res=1/8 dynamic=ff
  d2: beat at=5 bars=1 kick=x..... crash=x..... res=1/8 dynamic=ff
  lvl_d: gain db=7
