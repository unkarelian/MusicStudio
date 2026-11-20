# Olympia B1-17: Cole shouts at his father for the first time. The bass does not move. It ends on the wrong chord, with soup on.
piece olympia_b1_17_the_casting_vote key="D minor" tempo=84 style=orchestral
master room.decay=2.4 room.wet=0.24
meta title = "The Casting Vote"
meta soundfont = "hq"

section table bars=8 meter=4/4 dynamic=p
section shout bars=8 meter=4/4 dynamic=f
section out   bars=4 meter=4/4 dynamic=pp tempo=66
section soup  bars=6 meter=4/4 dynamic=p tempo=66 tempo_end=56

harmony
  @table: i . VII i | iv . v i
  @shout: i . . . iv . . .
  @out:   VI . VII .
  @soup:  i . VI . VII .

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
motif hold = 0:1/2 0:1/2
motif jab = r:1/8 0:1/8 r:1/4 0:1/8 0:1/8 r:1/4

voice bass contrabass role=bass octave=2 engine=soundfont bank=hq
  h_1: play motif=hold at=@table times=8 dynamic=p
  h_2: play motif=hold at=@shout times=8 dynamic=mp
  h_3: drone at=@out bars=4 degree=0 dynamic=pp
  h_4: play motif=hold at=@soup times=6 dynamic=pp

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@table dynamic=mp articulation=legato
  c_2: play motif=cole at=@table.5 transpose=2 dynamic=mf articulation=legato
  c_3: play motif=cole at=@shout transpose=4 dynamic=f
  c_4: play motif=cole at=@shout.5 transpose=5 dynamic=ff
  c_5: play motif=cole_head at=@soup.3 dynamic=p articulation=legato
  c_6: phrase at=@soup.5 steps="1:1/1~ | 1:1/1" dynamic=pp articulation=legato
  c_shape: shape amount=0.5

voice vn violin role=counter octave=4 pan=0.25 engine=soundfont bank=hq
  j_1: play motif=jab at=@shout times=8 dynamic=mf articulation=staccato
  lvl_vn: gain db=-5

voice cl clarinet role=counter octave=4 pan=-0.4 engine=soundfont bank=hq
  o_1: phrase at=@out steps="4:1/1 | 3:1/2 2:1/2 | 4:1/1 | 5:1/2 4:1/2" dynamic=p articulation=legato
  lvl_cl: gain db=-3

voice pno concert_grand role=harmony octave=3 pan=0 engine=soundfont
  p_1: chords at=@soup bars=6 voicing=pad lead=true dynamic=pp
  p_2: chords at=@table bars=8 voicing=broken lead=true dynamic=pp
  lvl_pno: gain db=-4
  b_h: humanize amount=0.6 timing=6
