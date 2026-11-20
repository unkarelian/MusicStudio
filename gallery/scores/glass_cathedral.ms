# glass_cathedral: symphonic art-rock / progressive epic in D minor -> D major.
#
# Form: 7/8 prelude -> 4/4 verse -> 5/4 lift -> 4/4 chorus -> 7/8 fugato interlude
#       -> hard stop -> 4/4 D-major apotheosis -> 7/8 -> 4/4 coda.

piece glass_cathedral key="D minor" tempo=106 style=orchestral
meta soundfont = "hq"
master room.decay=2.8 room.wet=0.34

section prelude    bars=8  meter=7/8 dynamic=p
section verse_1    bars=12 meter=4/4 dynamic=mp
section lift       bars=8  meter=5/4 dynamic=mf
section chorus_1   bars=16 meter=4/4 dynamic=f
section interlude  bars=12 meter=7/8 dynamic=mf
section apotheosis bars=16 meter=4/4 key="D major" dynamic=ff
section coda_a     bars=8  meter=7/8 dynamic=mp
section coda_b     bars=4  meter=4/4 key="D major" dynamic=pp

stop from=@interlude.12:6 until=@apotheosis

harmony
  @prelude:    [i i9 VImaj7 iv7]*2
  @verse_1:    i . VImaj7 . | iv9 . i_1 V7 | VImaj7 III iv7 V7
  @lift:       iv7 VImaj7 III V7 | iv7 iv7 VImaj7 V7
  @chorus_1:   [VImaj7 III i VII | iv9 VImaj7 VII V7]*2
  @interlude:  i . bIImaj7 . | i . VImaj7 V7 | iv7 VImaj7 bIImaj7 V7
  @apotheosis: I V vi IV | iii7 V bVI bVII | I V vi IV | ii7 V IV I
  @coda_a:     i i9 VImaj7 iv7 | i i9 VImaj7 V7
  @coda_b:     I . IV I

# -- motifs -------------------------------------------------------------------
# 7/8 crystalline arpeggio & ostinato cell (3+2+2 = 7/8)
motif cell_78      = 0:1/8 2:1/8 4:1/8 3:1/8 2:1/8 4:1/8 5:1/8
motif cell_78_inv  < cell_78 : invert
motif cell_78_hi   < cell_78 : transpose:2

# Verse A-theme (9, 9, 10 syllables -> 28 notes over 12 bars)
motif glass_cell   = 0:1/4 2:1/4 4:1/2 | 3:1/4. 2:1/8 1:1/2
motif glass_cad    = 0:1/4 -1:1/4 0:1/2 | r:1/1
motif verse_a      < glass_cell : then:glass_cad
motif verse_b      < glass_cell : transpose:2 > then:glass_cad
motif verse_c_tail = 1:1/4 0:1/4 2:1/2~ | 2:1/1
motif verse_c      < glass_cell : transpose:2 > then:verse_c_tail

# 5/4 Lift (9 + 9 = 18 notes over 8 bars)
motif lift_a       = 4:1/4 5:1/4 6:1/2 4:1/4 | 5:1/2 4:1/4 2:1/2 | 3:1/2 2:3/4 | r:1/1 r:1/4
motif lift_b       < lift_a : transpose:1

# Chorus B-theme (9, 9, 9, 10 = 37 notes over 16 bars)
motif chorus_head  = 4:1/4 5:1/4 7:1/2 | 6:1/4. 5:1/8 4:1/2
motif chorus_tail  = 2:1/4 3:1/4 4:1/2 | r:1/1
motif chorus_a     < chorus_head : then:chorus_tail
motif chorus_b     < chorus_a : transpose:1
motif chorus_c     < chorus_head : transpose:2 > then:chorus_tail
motif chorus_end   = 3:1/4 2:1/4 1:1/2~ | 1:1/1
motif chorus_d     < chorus_head : then:chorus_end

# Countermelodies & Coda
motif counter_chor = r:1/2 0:1/2 | 2:1/2 3:1/2 | 2:1/2. 4:1/4 | 3:1/4 r:3/4
motif inter_soar   = 4:1/2. 3:1/8 | 2:1/2 1:1/4. | 2:1/2. 4:1/8 | 5:1/2 4:1/4.
motif coda_tail    = 1:1/2 3:1/2 | 2:1/1
motif coda_vox     < glass_cell : retrograde > then:coda_tail

# -- drum lanes ---------------------------------------------------------------
lanes LIFT_54
  kick:   x.....x...x.........|x.....x...x...x.....
  snare:  ........x.......o...|........x.......x...
  rim:    ....x.......x.......|....x.......x.......
  hat:    X.x.x.X.x.x.x.x.x.x.

lanes LIFT_FILL_54
  kick:    x.....x...x...x.....
  snare:   ....x...x...x.x.xxxx
  tom_mid: ............x.......
  tom_lo:  ..............x.....
  hat:     X.x.x.X.x.x.........

lanes CHORUS_44
  kick:   x.....x...x.....|x...x.x.......x.
  snare:  ....X.......X...|....X..o....X..o
  hat:    X.x.X.x.X.x.X.x.
  open:   ................|..............o.
  crash:  x...............................

lanes INTER_78
  kick:   x.....x...x...|x.....x...x.x.
  snare:  ......x.....o.|......x.....x.
  hat:    X.x.X.x.X.x.X.

lanes APOTH_44
  kick:   x.....x...x...x.|x...x.x...x...x.
  snare:  ....X.......X...|....X..o....X.oo
  ride:   X.x.X.x.X.x.X.x.
  crash:  x...............................

# -- lead & harmony vocals ----------------------------------------------------
voice vocal singer role=melody octave=4 pan=0 bank="shisakune:symphonic"
  v_verse1: play motif=verse_a at=@verse_1 dynamic=mf
  v_verse2: play motif=verse_b at=@verse_1.5 dynamic=mf
  v_verse3: play motif=verse_c at=@verse_1.9 dynamic=mf
  v_lift1:  play motif=lift_a at=@lift dynamic=mf
  v_lift2:  play motif=lift_b at=@lift.5 dynamic=f
  v_chor1:  play motif=chorus_a at=@chorus_1 dynamic=f
  v_chor2:  play motif=chorus_b at=@chorus_1.5 dynamic=f
  v_chor3:  play motif=chorus_c at=@chorus_1.9 dynamic=ff
  v_chor4:  play motif=chorus_d at=@chorus_1.13 dynamic=f
  v_apoth1: play motif=chorus_a at=@apotheosis dynamic=ff
  v_apoth2: play motif=chorus_b at=@apotheosis.5 dynamic=ff
  v_apoth3: play motif=chorus_c at=@apotheosis.9 dynamic=ff
  v_apoth4: play motif=chorus_d at=@apotheosis.13 dynamic=ff
  v_coda:   play motif=coda_vox at=@coda_b dynamic=mp
  v_words: lyrics text="Cold stone and si-lence, be-neath the frost We raise a tow-er of glass and ghost Each fra-gile win-dow will hold the dawn Hear the bells ring-ing through hol-low stone Light breaks the sha-dow we walk a-lone Burn through the glass, let the spires a-wake Sing for the walls that the storm will break High-er than sor-row, and bright as flame Call out the light by its tru-est name Burn through the glass, let the spires a-wake Shine on the ru-ins that we re-make Gold in the raf-ters, the dark-ness gone Stand in the blaze of a new-born dawn Still in the glass, the light re-mains -"
  shape amount=0.55
  humanize amount=0.25 timing=8
  eq freq=280 gain=2.0
  echo from=@coda_b.2 until=@coda_b.end time="1/4." feedback=0.50 mix=0.45

voice harmony_vox singer role=counter octave=4 pan=0.22 bank=qixuan
  hv_chor1: phrase at=@chorus_1.4 steps="1:1/2 3:1/2" dynamic=mf
  hv_chor2: phrase at=@chorus_1.8 steps="4:1/2 3:1/2" dynamic=mf
  hv_chor3: phrase at=@chorus_1.12 steps="3:1/2 1:1/2" dynamic=mf
  hv_apoth1: phrase at=@apotheosis.4 steps="3:1/2 5:1/2" dynamic=f
  hv_apoth2: phrase at=@apotheosis.8 steps="3:1/2 1:1/2" dynamic=f
  hv_apoth3: phrase at=@apotheosis.12 steps="5:1/2 3:1/2" dynamic=f
  hv_words: lyrics text="a-wake will break as flame a-wake re-make is gone"
  shape amount=0.5
  gain db=6.0

# -- keys & guitars -----------------------------------------------------------
voice piano concert_grand role=harmony octave=3 pan=-0.25 engine=soundfont
  p_pre:   play motif=cell_78 at=@prelude times=8 octave=4 dynamic=p
  p_ver:   chords at=@verse_1 bars=12 voicing=block roll="1/24" lead=true ring=true dynamic=mp
  p_chor:  chords at=@chorus_1 bars=8 voicing=arpeggio_up lead=true ring=false dynamic=mf
  p_inter: play motif=cell_78_hi at=@interlude times=12 octave=4 dynamic=mp
  p_coda:  play motif=cell_78 at=@coda_a times=8 octave=4 dynamic=p
  p_end:   chords at=@coda_b bars=4 octave=4 voicing=pad lead=true dynamic=pp
  eq freq=2500 gain=-2.5
  gain db=-4.5

voice bell celesta role=ornament octave=5 pan=0.35 engine=soundfont
  b_pre:  play motif=cell_78 at=@prelude.3 times=6 dynamic=pp
  b_coda: play motif=cell_78 at=@coda_a times=8 dynamic=pp
  gain db=-5.0

voice clean_gtr strat_clean role=harmony octave=3 pan=0.42 engine=soundfont
  cg_ver:  chords at=@verse_1 bars=12 voicing=arpeggio_up lead=true ring=true dynamic=mp
  cg_lift: chords at=@lift bars=8 voicing=arpeggio_updown lead=true ring=true dynamic=mf
  eq freq=2800 gain=-2.0
  gain db=-3.5

voice dist_gtr_l amp_guitar role=harmony octave=3 pan=-0.65 engine=soundfont
  dgl_ch: chords at=@chorus_1 bars=16 tones=2 voicing=block lead=false rhythm="1/2" articulation=legato dynamic=mp
  dgl_ap: chords at=@apotheosis bars=16 tones=2 voicing=block lead=false rhythm="1/2" articulation=legato dynamic=mf
  filter mode=lowpass start=4200
  eq freq=2600 gain=-4.5
  duck source=drums drum=kick depth=4.5 release=0.15
  gain db=-4.0

voice dist_gtr_r amp_guitar role=harmony octave=3 pan=0.65 engine=soundfont
  dgr_ch: chords at=@chorus_1 bars=16 tones=2 voicing=block lead=false rhythm="1/2" articulation=legato dynamic=mp
  dgr_ap: chords at=@apotheosis bars=16 tones=2 voicing=block lead=false rhythm="1/2" articulation=legato dynamic=mf
  filter mode=lowpass start=4200
  eq freq=2600 gain=-4.5
  duck source=drums drum=kick depth=4.5 release=0.15
  gain db=-4.0

voice organ hammond_rock role=pad octave=3 pan=-0.32 engine=soundfont
  org_lift: chords at=@lift bars=8 tones=2 voicing=pad lead=true dynamic=mp
  eq freq=2400 gain=-3.0
  gain db=-5.5

# -- bass & drums -------------------------------------------------------------
voice bass rbx_finger_bass role=bass octave=1 pan=0 engine=soundfont
  bs_ver:   bass at=@verse_1.5 bars=8 pattern=root dynamic=mp
  bs_lift:  bass at=@lift bars=8 pattern=root_fifth rhythm="1/4" dynamic=mf
  bs_chor:  bass at=@chorus_1 bars=16 pattern=root_fifth rhythm="1/8" dynamic=f
  bs_inter: play motif=cell_78 at=@interlude times=12 octave=1 dynamic=f
  bs_apoth: bass at=@apotheosis bars=16 pattern=root_fifth rhythm="1/8" dynamic=ff
  bs_coda:  bass at=@coda_a bars=8 pattern=pedal dynamic=p
  gain db=2.0

voice drums kit_rock role=percussion pan=0 engine=soundfont
  dr_lift:      beat at=@lift bars=7 lanes=$LIFT_54 dynamic=mf
  dr_lift_fill: beat at=@lift.8 bars=1 lanes=$LIFT_FILL_54 dynamic=f
  dr_chor:  beat at=@chorus_1 bars=16 lanes=$CHORUS_44 dynamic=f
  dr_inter: beat at=@interlude bars=12 lanes=$INTER_78 dynamic=f
  dr_apoth: beat at=@apotheosis bars=16 lanes=$APOTH_44 dynamic=f
  compress ratio=3.0 threshold=-16.0
  humanize amount=0.32 timing=9
  gain db=-2.5

# -- orchestra ----------------------------------------------------------------
voice cello cello role=counter octave=3 pan=0.30 engine=soundfont
  vc_pre:   drone at=@prelude bars=8 degree=0 dynamic=pp
  vc_ver:   drone at=@verse_1.5 bars=8 degree=4 dynamic=p
  vc_inter: play motif=cell_78_inv at=@interlude.3 times=10 octave=4 dynamic=mf
  vc_apoth: drone at=@apotheosis bars=16 degree=4 octave=3 dynamic=mp
  vc_coda:  play motif=cell_78 at=@coda_a times=8 octave=3 dynamic=mp
  vc_end:   drone at=@coda_b bars=4 degree=0 octave=2 dynamic=pp

voice violin violin role=counter octave=4 pan=-0.35 engine=soundfont
  vn_chor:   play motif=counter_chor at=@chorus_1.9 transform=[transpose:-2] times=1 dynamic=mf
  vn_inter1: play motif=inter_soar at=@interlude.5 times=1 articulation=legato dynamic=f
  vn_inter2: play motif=inter_soar at=@interlude.9 transform=[ornament:mord] times=1 articulation=legato dynamic=f
  vn_apoth:  play motif=counter_chor at=@apotheosis transform=[transpose:-2] times=1 dynamic=f
  vn_apoth2: play motif=counter_chor at=@apotheosis.9 transform=[transpose:-2,ornament:mord] times=1 dynamic=f
  shape amount=0.5

voice strings strings role=pad octave=3 pan=0 engine=soundfont
  st_chor:  chords at=@chorus_1 bars=16 tones=2 voicing=pad spread=true lead=true dynamic=mp
  st_apoth: chords at=@apotheosis bars=16 tones=2 voicing=pad spread=true lead=true dynamic=mf
  eq freq=2800 gain=-4.0
  duck source=drums drum=kick depth=4.5 release=0.18
  gain db=-3.5

voice horn horn role=counter octave=3 pan=0.25 engine=soundfont
  hn_chor:  play motif=counter_chor at=@chorus_1.9 times=1 dynamic=mp
  hn_apoth: play motif=counter_chor at=@apotheosis.9 times=1 dynamic=mf
  gain db=4.0

voice flute flute role=ornament octave=5 pan=-0.20 engine=soundfont
  fl_coda:  play motif=cell_78_hi at=@coda_a.3 times=2 dynamic=p
  fl_coda2: play motif=cell_78_hi at=@coda_a.6 times=3 dynamic=p
  fl_end:   phrase at=@coda_b steps="4:1/1 2:1/1 4:1/1~" dynamic=pp
  gain db=-4.5
