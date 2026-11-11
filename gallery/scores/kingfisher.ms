# kingfisher: a loop that hovers, then dives.
#
# One sixteen-bar cycle of chords and one tune, heard at two speeds without the
# tempo ever moving: 168 to the minute throughout, first counted in half time
# (a nylon guitar, a dusty kit, a bass that walks into every chord), then with
# the drums at full speed under the same guitar and the same tune.
#
#   needle   the last half of the cycle on the guitar alone, off a record
#   loop     the kit and the bass
#   theme    the tune, on a piano: it moves for two bars and holds for two
#   again    a second tune on a vibraphone, which holds where the first moved
#            and climbs where it held
#   bridge   somewhere else: C major, a bossa, a third tune that only falls
#   turn     the end of the first tune written out as an accelerando: its
#            top phrase at half speed, its last phrase at speed -- while the
#            break is heard coming nearer through a wall
#   dive     the same cycle, the same guitar, the drums at full speed; the
#            tune's first five notes climb a step every two bars
#   deep     two chords a semitone apart, a sub, struck piano chords
#   hush     no drums. The piano alone, and a door into another key
#   lift     four bars of the new key's dominant
#   crest    the whole first tune a minor third higher
#   peak     both tunes at once: they were written to fit
#   ember    half time again; the guitar is the last thing left
#
# The cycle starts on the fourth degree and reaches home in its seventh chord,
# by way of the flat second: Am9 D13 Gmaj7 Cmaj7 | Fmaj9 B7b9 Em9 E9.

piece kingfisher key="E minor" tempo=168 style=electronic
master room.decay=1.9 room.wet=0.2 push=4.5

section needle bars=8  dynamic=mp
section loop   bars=16 dynamic=mf
section theme  bars=16 dynamic=mf
section again  bars=16 dynamic=mf
section bridge bars=16 dynamic=mp key="C major"
section turn   bars=12 dynamic=mf
section dive   bars=16 dynamic=f
section deep   bars=16 dynamic=f
section hush   bars=12 dynamic=p
section lift   bars=4  dynamic=mf key="G minor"
section crest  bars=16 dynamic=ff key="G minor"
section peak   bars=16 dynamic=ff key="G minor"
section ember  bars=16 dynamic=mp key="G minor" tempo_end=140

stop from=@turn.12:4 until=@dive keep=[]

harmony
  @needle: bIImaj9 . V7b9 . i9 . V9/iv .
  @loop:   [iv9 . VII13 . IIImaj9 . VImaj9 . bIImaj9 . V7b9 . i9 . V9/iv .]*3
  @bridge: Imaj7 . #io7 . ii9 . bII7 . Imaj7 . bVII13 . #iv%7 . V7b9/iii .
  @turn:   bIImaj7#11 . . . V7b9 . . . i9 . V9/iv .
  @dive:   iv9 . VII13 . IIImaj9 . VImaj9 . bIImaj9 . V7b9 . i9 . V9/iv .
  @deep:   [i9 . bIImaj7#11 .]*4
  @hush:   i9 . VImaj7 . bIImaj7#11 . i9 . VImaj7 . iv9 .
  @lift:   V7b9 . V9/iv .
  @crest:  [iv9 . VII13 . IIImaj9 . VImaj9 . bIImaj9 . V7b9 . i9 . V9/iv .]*2
  @ember:  iv9 . VII13 . IIImaj9 . VImaj9 . bIImaj9 . V7b9 . i9 . . .

# -- the first tune: four cells of four bars ---------------------------------
motif fall    = 7:1/2. 6:1/4 4:1/2 2:1/4 3:1/4 | 4:1/1~ 4:1/2 7:1/4 8:1/4      -- down a sixth by thirds, a step back up, and the note it was looking for held; two notes to climb out on
motif fall_up < fall : transpose:2                                             -- the same a third higher while the chords go down
motif crest   = 11:1/2. 10:1/4 7:1/2 5:1/4 7:1/4 | #6:1/1 | 8:1/2 4:1/4 5:1/4  -- the top: the raised fourth of the flat-two chord, then the leading note held a whole bar
motif settle  = 7:1/2. 6:1/4 4:1/2 3:1/4 2:1/4 | 1:1/1~ 1:1/2 4:1/4 6:1/4      -- the first cell again, turned to land on the ninth
motif tune < fall : then:fall_up > then:crest > then:settle
motif crest_wide < crest : fragment:0,6 > augment:2                            -- the top at half speed: the turn
motif head < fall : fragment:0,5                                               -- the five notes everything else is made of
motif climb < head : sequence:4,1                                              -- the head four times, a step higher each time: the run
motif spike = 12:1/2. 11:1/4 8:1/2 #6:1/4 8:1/4                                -- the head's shape bent onto the dominant: it starts on the flat ninth

# -- the second tune: it holds while the first moves and moves while the first holds --
motif lift1 = 9:1/1~ | 9:1/2. r:1/4 | r:1/4 8:1/4 10:1/4 11:1/4 | 10:1/2. 8:1/4      -- the seventh of the first chord held, falling to the third of the next, then up through its sixth
motif lift2 = 11:1/1~ | 11:1/2. r:1/4 | r:1/4 9:1/4 11:1/4 13:1/4 | 11:1/2. 9:1/4    -- higher; the climb is in thirds now
motif lift3 = 7:1/1~ | 7:1/2. r:1/4 | r:1/4 8:1/4 10:1/4 12:1/4 | 11:1/2. 10:1/4     -- under the first tune's top note, then up the dominant to its flat ninth
motif lift4 = 9:1/1~ | 9:1/2. r:1/4 | r:1/4 11:1/4 #9:1/4 8:1/4 | 7:1/1              -- after three climbs, a fall: home
motif rise < lift1 : then:lift2 > then:lift3 > then:lift4

# what the guitar says in the two bars where the first tune holds still: one answer for each chord it is held over
motif answer = r:1/1 | r:1/1 | r:1/2 8:1/4 6:1/4 | 5:1/4 3:1/4 1:1/2 | r:1/1 | r:1/1 | r:1/2 6:1/4 4:1/4 | 2:1/4 4:1/4 6:1/2 | r:1/1 | r:1/1 | r:1/2 5:1/4 3:1/4 | 1:1/4 3:1/4 #6:1/2 | r:1/1 | r:1/1 | r:1/2 7:1/4 6:1/4 | 4:1/4 #2:1/4 0:1/2

# the bridge's tune: it only falls, and it ends on a note that belongs to the old key
motif lounge = r:1/4 2:1/4 4:1/2 | 6:1/2 5:1/4 4:1/4 | 2:1/1 | r:1/4 4:1/4 b6:1/4 5:1/4 | 5:1/2. 3:1/4 | 2:1/1 | r:1/4 3:1/4 b5:1/2 | 6:1/2 b8:1/2
motif lounge_b = 7:1/2. 6:1/4 | 4:1/2 2:1/2 | 4:1/1 | 3:1/2 1:1/2 | 2:1/1 | 0:1/2 -2:1/2 | #1:1/1~ | #1:1/1

# the bass: root, a hole, the root again with the kick, the fifth, and a step into the next chord
motif walk = 3:3/8 r:1/2 3:1/8 | 3:1/4 7:1/4 r:1/4 0:1/4 | -1:3/8 r:1/2 -1:1/8 | -1:1/4 3:1/4 r:1/4 1:1/4 | 2:3/8 r:1/2 2:1/8 | 2:1/4 6:1/4 r:1/4 -1:1/4 | -2:3/8 r:1/2 -2:1/8 | -2:1/4 2:1/4 r:1/4 0:1/4 | b1:3/8 r:1/2 b1:1/8 | b1:1/4 5:1/4 r:1/4 -2:1/4 | -3:3/8 r:1/2 -3:1/8 | -3:1/4 1:1/4 r:1/4 b1:1/4 | 0:3/8 r:1/2 0:1/8 | 0:1/4 4:1/4 r:1/4 -1:1/4 | 0:3/8 r:1/2 0:1/8 | 0:1/4 4:1/4 r:1/4 #2:1/4
motif thud = 0:1/2. r:1/8 0:1/8 | r:1/4 0:1/4. r:1/8 2:1/4 anchor=chord       -- the sub under the cycle: long, a hole where the snare is, the fifth on the way out
motif prowl = 0:3/8 0:1/8 r:1/4 0:1/4 | r:1/8 0:3/8 -1:1/4 0:1/4 | b1:3/8 b1:1/8 r:1/4 b1:1/4 | r:1/8 b1:3/8 4:1/4 b1:1/4      -- the sub under the dive: home and the semitone above it

# -- drums ----------------------------------------------------------------------
# half time: sixteen eighths are one slow bar
lanes BAP
  kick:  x......xx.......|x..x...x..x.....
  snare: ....X.......X...|....X.......X..o
  hat:   X.x.X.x.X.x.X.x.|X.x.X.x.X.x.X.xo
lanes BAP2
  kick:  x......xx.x.....|x..x...x..x..x..
  snare: ....X..o....X...|....X.....o.X..o
  hat:   X.x.X.x.X.x.X.xo|X.x.X.x.X.x.X.x.
  open:  ................|..............o.
lanes BOSSA
  rim:    x..x..x...x..x..
  kick:   x..xo..xx..xo..x
  shaker: X.x.X.x.X.x.X.x.
# full speed: sixteen sixteenths are one bar
lanes BREAK
  kick:  x.x.......xx....|x.x.......xx....|x.x.......x.....|..xx......x.....
  snare: ....X..o.o..X..o|....X..o.o..X..o|....X..o.o....X.|.o..X..o.o....X.
  hat:   x.x.x.x.x.x.x.x.
  open:  ..............o.|................
lanes STEP
  kick:  x.........x.....|x.....x...x.....
  snare: ....X..o....X...|....X..o.o..X.oo
  hat:   x.xxx.xxx.xxx.xx
  open:  ..........o.....
set EVERY_8 = "x..............................................................................................................................."
set CUT_A = "0 1 2 3 4 5 6 7 4 5 6 7 12 12*2 4*2 4*4"
set CUT_B = "0 1 2 3 4 4 6 7 8 9 4*2 4*2 12*4 12*4 12*4^0>7 12*4^0>7"
set CUT_C = "10 11 4 . 10 11 4 . 0 . 4*2 . 12*4 12*4 12 ."
set ARP = "0 . 2 4 . 3 2 . | 4 3 . 0 2 . 4 ."
set COMP = ". . . 0+1+2+3 . . . . | . . 0+1+2+3 . . . . ."
set STAB = "0+1+2+3 . . 0+1+2+3 . . 0+1+2+3 . | . 0+1+2+3 . . 0+1+2+3 . 0+1+2+3 ."

# -- the record: the needle goes down at the start and comes up at the end -----------
voice dust vinyl role=ornament octave=3
  dust_a: drone at=@needle bars=16 dynamic=mp
  dust_a_out: dynamics from=@loop until=@loop.9 start=mp end=pp
  dust_end: drone at=@ember bars=16 dynamic=mp
  lvl_dust: gain db=8

# -- the guitar: the loop itself --------------------------------------------------
voice gtr classical_guitar role=harmony octave=2 pan=-0.25 engine=soundfont
  g_needle: chords at=@needle bars=8 tones=5 spread=True ring=True rhythm=1/8 figure=$ARP dynamic=mf
  g_loop:   chords at=@loop bars=48 tones=5 spread=True ring=True rhythm=1/8 figure=$ARP dynamic=mf
  g_bossa:  chords at=@bridge bars=16 octave=3 tones=4 spread=True rhythm=1/8 figure="0 . . 1+2+3 . . 1+2+3 . | 0 . 1+2+3 . . 1+2+3 . ." dynamic=mp
  g_turn:   chords at=@turn bars=12 tones=5 spread=True ring=True rhythm=1/8 figure=$ARP dynamic=mf
  g_fast:   chords at=@dive bars=16 tones=5 spread=True ring=True rhythm=1/8 figure=$ARP dynamic=mf
  g_crest:  chords at=@crest bars=48 tones=5 spread=True ring=True rhythm=1/8 figure=$ARP dynamic=mf
  for bar in 8 16
    g_cut_d{bar}: chop in=@dive.{bar}-{bar} slices=8 order="0 0*2 2 2*2 2*4 . 6*2 6*4"      -- the loop caught and stuttered, the way a sampler would
    g_cut_p{bar}: chop in=@peak.{bar}-{bar} slices=8 order="0 0*2 2 2*2 2*4 . 6*2 6*4"
  fx_gtr_needle: filter from=@needle until=@loop start=600 end=7000
  fx_gtr_air: eq freq=3000 gain=5 width=2
  fx_gtr_top: eq freq=7000 gain=5 width=2
  fx_gtr_box: eq freq=220 gain=-4 width=1.5
  lvl_gtr: gain db=-5
  feel_gtr: humanize amount=1.3 timing=10

voice gtr2 classical_guitar role=counter octave=4 pan=0.2 engine=soundfont
  a_needle: play motif=answer at=@needle transform=["fragment:16,16"] dynamic=mp
  a_loop:   play motif=answer at=@loop times=2 dynamic=mf
  a_crest:  play motif=answer at=@crest dynamic=mf
  a_ember:  play motif=answer at=@ember transform=["fragment:0,24"] dynamic=mp
  fx_gtr2_needle: filter from=@needle until=@loop start=600 end=7000
  fx_gtr2_echo: echo time=1/4. feedback=0.3 mix=0.22 tone=2400
  fx_gtr2_air: eq freq=3500 gain=4 width=2
  lvl_gtr2: gain db=-3
  feel_gtr2: humanize amount=1.2 timing=10

# -- keys ----------------------------------------------------------------------------
voice keys dx_piano role=harmony octave=3 pan=0.35 engine=soundfont
  k_theme: chords at=@theme bars=32 tones=4 rootless=True lead=True rhythm=1/8 figure=$COMP dynamic=mp
  k_bridge: chords at=@bridge bars=16 tones=4 rootless=True lead=True voicing=pad dynamic=p
  k_dive:  chords at=@dive bars=16 tones=4 rootless=True lead=True rhythm=1/8 figure=$COMP dynamic=mf
  k_hush:  chords at=@hush bars=16 tones=4 rootless=True lead=True voicing=pad dynamic=p
  k_crest: chords at=@crest bars=16 tones=4 rootless=True lead=True rhythm=1/8 figure=$COMP dynamic=mf
  k_ember: chords at=@ember bars=16 tones=4 rootless=True lead=True voicing=pad dynamic=p
  fx_keys_box: eq freq=350 gain=-4 width=1.5
  fx_keys_air: eq freq=4500 gain=4 width=2
  lvl_keys: gain db=2
  feel_keys: humanize amount=0.7 timing=8

voice piano concert_grand role=melody octave=4 pan=0.1 engine=soundfont
  p_pick:  phrase at=@loop.16:3 steps="4:1/4 6:1/4" dynamic=mp
  p_tune:  play motif=tune at=@theme dynamic=mf
  p_turn:  play motif=crest_wide at=@turn dynamic=mf
  p_leap:  phrase at=@turn.7 steps="4:1/4 #6:1/4 8:1/4 10:1/4 | 12:1/2 11:1/2" dynamic=mf
  p_home:  play motif=settle at=@turn.9 dynamic=f
  p_dive1: play motif=climb at=@dive dynamic=f
  p_dive2: play motif=crest at=@dive.9 transform=["fragment:0,5"] dynamic=f
  p_dive3: play motif=spike at=@dive.11 dynamic=f
  p_dive4: play motif=settle at=@dive.13 transform=["fragment:0,7"] dynamic=f
  p_hush1: play motif=fall at=@hush dynamic=mp
  p_hush2: play motif=crest at=@hush.5 transform=["fragment:0,5"] dynamic=mp
  p_hush3: phrase at=@hush.7 steps="6:1/1~ 6:1/1" dynamic=p
  p_hush4: play motif=fall_up at=@hush.9 dynamic=mf
  p_lift:  phrase at=@lift steps="4:1/2 #6:1/2 | 8:1/2 10:1/2 | 11:1/1 | #9:1/2 4:1/4 6:1/4" dynamic=f
  p_crest: play motif=tune at=@crest times=2 dynamic=f
  p_last:  phrase at=@ember.13 steps="7:1/2. 6:1/4 4:1/2 3:1/4 2:1/4 | 1:1/1~ | 1:1/1~ | 1:1/1" dynamic=mp
  p_shape: shape amount=0.6
  lvl_piano: gain db=4
  feel_piano: humanize amount=1.0 timing=7

# the same piano an octave up once the drums are at full speed: octaves, the way a tune is played when it has to be heard over a kit
voice piano_hi concert_grand role=melody octave=5 pan=0.2 engine=soundfont
  ph_dive:  double source=piano octaves=1 in=@dive
  ph_crest: double source=piano octaves=1 from=@crest until=@peak.13
  lvl_piano_hi: gain db=-2

# struck chords, three-three-two: what a piano does on this kind of record
voice stab concert_grand role=harmony octave=4 pan=-0.4 engine=soundfont
  st_deep: chords at=@deep bars=16 tones=4 rootless=True lead=True rhythm=1/8 figure=$STAB articulation=staccato dynamic=f
  st_peak: chords at=@peak bars=16 octave=3 tones=4 rootless=True lead=True rhythm=1/8 figure=$STAB articulation=staccato dynamic=mf
  fx_stab_open: filter from=@deep until=@deep.13 start=400 end=7000 resonance=0.35
  fx_stab_echo: echo time=1/8. feedback=0.35 mix=0.25 tone=2600
  lvl_stab: gain db=-4
  feel_stab: humanize amount=0.5 timing=4

voice vibes vibraphone role=melody octave=4 pan=0.4 engine=soundfont
  v_rise: play motif=rise at=@again dynamic=mp
  v_deep: play motif=head at=@deep every=4 times=4 dynamic=mf
  v_peak: play motif=rise at=@peak dynamic=ff
  v_ember: play motif=crest at=@ember.9 dynamic=mp
  fx_vibes_echo: echo time=1/4. feedback=0.4 mix=0.22 tone=3500 spread=0.8
  fx_vibes_air: eq freq=6000 gain=4 width=2
  lvl_vibes: gain db=2.5

voice flute flute role=melody octave=4 pan=-0.1 engine=soundfont
  f_tune:   play motif=tune at=@again dynamic=mf articulation=legato
  f_lounge: play motif=lounge at=@bridge octave=5 dynamic=mf articulation=legato
  f_lounge_b: play motif=lounge_b at=@bridge.9 octave=5 dynamic=mf articulation=legato
  f_shape:  shape amount=0.6
  fx_flute_echo: echo time=1/4. feedback=0.3 mix=0.18 tone=3000
  lvl_flute: gain db=-1

voice strings slow_strings role=pad octave=3 engine=soundfont
  s_again:  chords at=@again bars=16 tones=4 voicing=pad lead=True dynamic=p
  s_bridge: chords at=@bridge bars=16 tones=4 voicing=pad lead=True dynamic=mp
  s_dive:   chords at=@dive bars=16 tones=4 voicing=pad lead=True dynamic=mp
  s_hush:   chords at=@hush bars=16 tones=4 voicing=pad lead=True dynamic=p
  s_swell:  dynamics from=@hush.9 until=@crest start=p end=f
  s_crest:  chords at=@crest bars=32 tones=4 voicing=pad lead=True dynamic=mf
  fx_strings_pump: duck source=brk drum=kick depth=4 release=0.12
  fx_strings_box: eq freq=450 gain=-4 width=1.5
  lvl_strings: gain db=-4

voice violins strings role=melody octave=4 pan=-0.3 engine=soundfont
  vn_tune: play motif=tune at=@crest times=2 dynamic=f articulation=legato
  vn_shape: shape amount=0.6
  lvl_violins: gain db=3

# -- bass ------------------------------------------------------------------------------
voice bass upright_bass role=bass octave=2 pan=0 engine=soundfont
  b_loop:  play motif=walk at=@loop times=3 dynamic=mf
  b_bridge: bass at=@bridge bars=16 pattern=root rhythm="3/8 1/8 1/2" dynamic=mp
  b_turn:  bass at=@turn bars=8 pattern=root rhythm="3/8 1/8 1/2" dynamic=mf
  b_turn2: play motif=walk at=@turn.9 transform=["fragment:42,14"] dynamic=mf
  b_hush:  bass at=@hush bars=12 pattern=pedal dynamic=p
  b_ember: play motif=walk at=@ember transform=["fragment:0,42"] dynamic=mp
  b_last:  phrase at=@ember.13 steps="0:1/1~ 0:1/1 | 0:1/1~ 0:1/1" dynamic=mp
  fx_bass_even: compress ratio=4 threshold=-18
  lvl_bass: gain db=4
  feel_bass: humanize amount=0.8 timing=6

voice sub sub_bass role=bass octave=1
  sub_dive:  play motif=thud at=@dive times=8 dynamic=f
  sub_deep:  play motif=prowl at=@deep times=4 dynamic=f
  sub_crest: play motif=thud at=@crest times=14 dynamic=f
  fx_sub_grit: drive amount=0.25
  lvl_sub: gain db=0

# -- kits: one recorded kit, played slow and then played fast ----------------------------
voice drums kit_rock role=percussion engine=soundfont
  d_loop:  beat at=@loop bars=16 res=1/8 lanes=$BAP dynamic=f
  d_theme: beat at=@theme bars=32 res=1/8 lanes=$BAP2 dynamic=f
  d_fill1: beat at=@theme.16:3 bars=1 res=1/8 snare=x.xx tom_mid=.x.. dynamic=mf
  d_fill2: beat at=@again.16:3 bars=1 res=1/16 snare=x.x.xxxx tom_lo=..x..... dynamic=mf
  d_turn:  beat at=@turn bars=8 res=1/8 lanes=$BAP dynamic=mf
  d_ember: beat at=@ember bars=12 res=1/8 lanes=$BAP dynamic=mf
  d_swing: swing amount=0.57 res=1/8
  fx_drums_slab: compress ratio=6 threshold=-22
  fx_drums_grit: drive amount=0.3
  fx_drums_old:  crush rate=26000 bits=12      -- a twelve-bit sampler
  fx_drums_dust: filter start=13000 end=13000
  fx_drums_air: eq freq=8500 gain=5 width=2
  lvl_drums: gain db=-2
  feel_drums: humanize amount=0.8 timing=7

voice perc kit_brush role=percussion engine=soundfont pan=0.15
  pc_bossa: beat at=@bridge bars=16 res=1/8 lanes=$BOSSA dynamic=mp
  feel_perc: humanize amount=0.8 timing=6

voice brk kit_rock role=percussion engine=soundfont
  br_wall:  beat at=@turn.5 bars=8 lanes=$BREAK tune=5 dynamic=mf      -- the break before the break: through a wall, getting nearer
  br_wall_up: dynamics from=@turn.5 until=@dive start=pp end=f
  br_dive:  beat at=@dive bars=16 lanes=$STEP crash=$EVERY_8 tune=5 dynamic=f
  br_deep:  beat at=@deep bars=16 lanes=$BREAK crash=$EVERY_8 tune=5 dynamic=f
  br_back:  beat at=@lift bars=4 lanes=$BREAK tune=5 dynamic=mf
  br_back_up: dynamics from=@lift until=@crest start=pp end=f
  br_crest: beat at=@crest bars=32 lanes=$BREAK crash=$EVERY_8 tune=5 dynamic=ff
  br_dive_a: chop in=@dive.8-8 slices=16 order=$CUT_B
  br_dive_b: chop in=@dive.16-16 slices=16 order=$CUT_C
  for sec in deep crest
    br_{sec}_a: chop in=@{sec}.4-4 slices=16 order=$CUT_A
    br_{sec}_b: chop in=@{sec}.8-8 slices=16 order=$CUT_B
    br_{sec}_c: chop in=@{sec}.12-12 slices=16 order=$CUT_A
    br_{sec}_d: chop in=@{sec}.16-16 slices=16 order=$CUT_C
  br_peak_a: chop in=@peak.4-4 slices=16 order=$CUT_A
  br_peak_b: chop in=@peak.8-8 slices=16 order=$CUT_B
  br_peak_c: chop in=@peak.12-12 slices=16 order=$CUT_A
  fx_brk_slab: compress ratio=8 threshold=-24
  fx_brk_grit: drive amount=0.4
  fx_brk_air: eq freq=9000 gain=2 width=2
  fx_brk_wall: filter from=@turn.5 until=@dive start=220 end=5000 resonance=0.2
  fx_brk_back: filter from=@lift until=@crest start=300 end=9000 resonance=0.2
  fx_brk_away: filter from=@peak.13 until=@ember start=12000 end=400 resonance=0.2      -- and it goes back behind the wall
  fx_brk_throw: echo from=@deep.16:3 until=@hush time=1/8. feedback=0.55 mix=0.5 tone=2200      -- the last snare, thrown into the quiet
  lvl_brk: gain db=-5.5
  feel_brk: humanize amount=0.9 timing=4
