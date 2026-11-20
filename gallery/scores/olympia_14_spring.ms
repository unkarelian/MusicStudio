# Olympia 14: Spring. Ivy's song, plain, with the Hermes figure once at the end of it, slowed;
# then Cole's theme, then the opened version on a piano. It ends on the fourth chord with the
# second degree held: it does not come home.
piece olympia_14_spring key="G major" tempo=84 style=orchestral
master room.decay=2.6 room.wet=0.26
meta title = "Spring"
meta soundfont = "hq"

section ivy   bars=16 meter=6/8 dynamic=mp   -- oboe and harp
section phone bars=4  meter=6/8 dynamic=p    -- the rocking bar, twice; the figure, at half speed, on a clarinet
section cole  bars=8  meter=4/4 tempo=72 dynamic=mp   -- cello
section open  bars=8  meter=4/4 tempo=72 dynamic=mf   -- the piano has the open version; the cello stays on the old one
section table bars=5  meter=4/4 tempo=72 tempo_end=56 dynamic=p   -- the oboe's rocking bar over Cole's head; stop on IV

harmony
  @ivy:   I . IV I | I IV V I | I . IV I | vi IV V .
  @phone: I . IV .
  @cole:  I . IV I | vi . V I
  @open:  I . IV I | vi IV V .
  @table: I . IV . .

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
motif hermes_kind < hermes : augment:2
motif boat4 < boat : rhythmize:1/4. 1/8 1/4 1/4          -- the rocking bar counted in four

voice ob oboe role=melody octave=4 pan=0.1 engine=soundfont bank=hq
  i_1: play motif=ivy at=@ivy dynamic=mf articulation=legato
  i_2: play motif=ivy_a at=@ivy.9 dynamic=mf articulation=legato
  i_3: play motif=ivy_b at=@ivy.13 transpose=2 dynamic=mp articulation=legato
  i_4: play motif=boat at=@phone dynamic=p articulation=legato
  i_5: play motif=boat at=@phone.3 transpose=-1 dynamic=p articulation=legato
  i_6: play motif=boat4 at=@table dynamic=p articulation=legato
  i_7: play motif=boat4 at=@table.3 dynamic=pp articulation=legato
  i_shape: shape amount=0.5

voice hp harp role=harmony octave=3 pan=-0.3 engine=soundfont bank=hq
  h_1: chords at=@ivy bars=20 figure="0 2 1 2 1 2" ring=true dynamic=p
  lvl_hp: gain db=-5

voice cl clarinet role=counter octave=4 pan=0.3 engine=soundfont bank=hq
  k_1: play motif=hermes_kind at=@phone.2 dynamic=p articulation=legato
  lvl_cl: gain db=-4

voice vc cello role=melody octave=3 pan=-0.2 engine=soundfont bank=hq
  c_1: play motif=cole at=@cole dynamic=mf articulation=legato
  c_2: play motif=cole at=@cole.5 transpose=2 dynamic=mf articulation=legato
  c_3: play motif=cole at=@open dynamic=p articulation=legato
  c_4: play motif=cole at=@open.5 dynamic=p articulation=legato
  c_5: play motif=cole_head at=@table.2 dynamic=p articulation=legato
  c_6: phrase at=@table.3 steps="0:1/1 | 1:1/1~ | 1:1/1" dynamic=pp articulation=legato
  c_shape: shape amount=0.5

voice pno concert_grand role=melody octave=4 pan=0 engine=soundfont
  p_c: chords at=@cole bars=8 voicing=broken lead=true octave=3 dynamic=p
  p_1: play motif=cole_open at=@open dynamic=mf
  p_2: play motif=cole_open at=@open.5 transpose=1 dynamic=mf
  p_t: chords at=@table bars=5 voicing=pad lead=true octave=3 dynamic=pp
  p_shape: shape amount=0.4
  p_h: humanize amount=0.4 timing=8

voice cb contrabass role=bass octave=2 engine=soundfont bank=hq
  b_1: bass at=@ivy bars=16 pattern=root dynamic=p
  b_2: bass at=@cole bars=21 pattern=root dynamic=p
  cb_h: humanize amount=0.8 timing=5
  lvl_cb: gain db=-3
