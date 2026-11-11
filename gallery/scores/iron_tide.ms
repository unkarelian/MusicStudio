# iron_tide: driving industrial post-punk, written against a reference.
#
# The reference was the user's favourite "Pacific Hatred" (TNO OST). It was
# measured (`ms match`), described by a listening model, and the two checked
# against each other before anything was written. What the track turned out to
# be -- not the jungle it is remembered as, but this:
#
#   108 beats a minute, straight, and it never moves
#   a picked bass in unbroken eighths, dry and in front: the hook is the bass
#   two bass roots a major third apart, four bars each, with a chromatic
#     neighbour-note turn at the end of every second bar
#   the pad changes every *two* bars over that, in fifths and sixths, no thirds
#   a raw acoustic kit, snare on two and four
#   a whistling lead that glides and echoes -- a signal more than a tune --
#     saved for the second cycle
#   a hard cut into found sound -- a megaphone and a crowd -- with a metal
#     clank that is then locked to the grid and never leaves
#   a wall of distorted guitars that only ring; no solo, no new tune
#   terraces, not swells: things arrive and leave on the bar line
#
# This piece keeps that recipe and none of the notes: its own key, its own
# riff, its own signal. It has no megaphone: the studio has no archive to
# sample and a synthesized speaker sounded like a robot, so the breakdown is a
# crowd (a clipped choir cluster under noise) and the metal.
#
# The bass, kit and guitars are recorded instruments from their own SoundFonts
# (`ms soundfont install bass_picked muldjord guitar_dist`); the pad, whistle
# and clank are synthesizer models. Without the banks it still builds.

piece iron_tide key="D minor" tempo=108 style=electronic
master room.decay=2.4 room.wet=0.36     # a larger, darker room than the style's

section intro  bars=8  dynamic=p    -- the pad alone: one chord every two bars
section bass   bars=8  dynamic=mf   -- the riff arrives, dry
section drive  bars=8  dynamic=f    -- the kit
section signal bars=16 dynamic=f    -- the whistle over all of it, twice
section rally  bars=8  dynamic=mp   -- hard cut: a crowd, a drone, metal
section build  bars=8  dynamic=mf   -- the kit comes back tight; the crowd recedes
section wall   bars=16 dynamic=ff   -- guitars left, right and middle
section strip  bars=8  dynamic=f    -- the wall is taken down; the signal, slower
section fade   bars=8  dynamic=f    -- snare and hats go; a sparse kick and the bass do not let up
section tail   bars=2  dynamic=p    -- a breathy flute, fluttering

# The bass has two notes (D for four bars, B flat for four); the chords over it
# change every two, so bars 3-6 of the loop are first inversions:
# Dm | Bb/D | Gm/Bb | Bb.
harmony
  @intro:  [i i VI_1 VI_1 iv_1 iv_1 VI VI]*5
  @rally:  i5*8
  @build:  [i i VI_1 VI_1 iv_1 iv_1 VI VI]*5
  @tail:   i5*2

# -- material -----------------------------------------------------------------
motif tread   = 0! 0 0 r 0! 0 4 0        -- the riff's first bar: the root in eighths, leaning on one and three, a breath after the third note, one fifth popped on four
motif turn    = 0! 0 0 0 -1! -3 b1 0     -- its answer: half a bar of root, then under it -- the seventh, the fifth -- and back by way of the flat second
motif turn_hi = 0! r 0 0 0! -1 b1 0      -- the fourth bar: a hole where the second note was, the same flat second home
motif riff < tread : then:turn > then:tread > then:turn_hi     -- four bars. Everything else stands on this
motif riff_low < riff : transpose:-2     -- the same on B flat

motif alarm = 4:1/4. 7:1/4. 4:1/4 | 4:1/4. 6:1/4. r:1/4      -- the whistle: two bars, three-three-two, a fourth up and back, then a third. A signal, not a tune
motif alarm_out < alarm : fragment:0,2 > append:8:1/4~ 8:1/2. r:1/4   -- its first two notes, then the one note that fits nothing under it, held
motif signal < alarm : then:alarm > then:alarm > then:alarm_out      -- eight bars: the signal three times and its way out
motif alarm_far < alarm : augment:2      -- the signal at half speed: what is left after the wall

motif ring = 0 0 r 0 0 r 0 0 | 0 0 r 0 0 2 b1 0                -- the guitars: the riff's eighths with holes punched in them, and its flat second (`ms match`: the reference's wall has five hits a second)
motif mute = 0! 0 0 0 0! 0 0 0           -- one note, eight times, leaning on one and three: the guitar before it is a wall
motif mute_hi < mute : transpose:5
motif ground = 0:1/1~ 0:1/1~ 0:1/1~ 0:1/1 -2:1/1~ -2:1/1~ -2:1/1~ -2:1/1   -- the pad's floor: the two bass notes
motif watch = 4:1/1~ 4:1/1 5:1/1~ 5:1/1 3:1/1~ 3:1/1 2:1/1~ 2:1/1          -- the pad's top: with the ground, a fifth, a sixth, a sixth, a fifth
motif anvil = 4:3/16! 4:3/16 4:1/4 4:3/16! 4:3/16 | 4:3/16! 4:3/16 4:1/4 4:1/8! 4:1/16 4:3/16   -- the clank: three against four, and a stumble. One pitch; metal does not follow the chords

# -- drums: two-bar patterns; the second bar always differs from the first ----
lanes ROCK
  kick:  x.....x...x.....|x.....x.......x.
  snare: ....X.......X...|....X.......X..o
  hat:   X.x.X.x.X.x.X.x.|X.x.X.x.X.x.X...
  open:  ................|..............o.
lanes TIGHT
  kick:  x.....x.x.......|x.....x.x.x.....
  snare: ....x.......x...
  hat:   X.x.X.x.X.x.X.xo
lanes WIDE
  kick:  x.....x.....x...|x...x.x.......x.
  snare: ....X.......X...|....X..o....X.oo
  ride:  x...x...x...x...
  hat:   X.x.X.x.X.x.X.x.
  open:  ................|..............o.
lanes LOOSE
  kick:  x.....x.x.......|x.....x...x.....
  snare: ....x..o....x...|....x.......x..o
  tom_lo: ..........o.....|..........o..o..
  hat:   X.x.X.xoX.x.X.x.
lanes FILL
  snare: x.x.xxx.x.xxxxxx
  tom_mid: ....x.......x...
  tom_lo: ..........x...x.
  kick:  x...x...x...x...
set EVERY_4 = "x..............................................................."

# -- the pad: from the first bar to the last ------------------------------------
voice pad dark_pad role=pad octave=4
  pad_ground: play motif=ground at=@intro times=11 dynamic=mp articulation=legato
voice pad_top warm_pad role=pad octave=4 pan=-0.5
  pad_watch: play motif=watch at=@intro times=11 dynamic=mp articulation=legato
  pad_rally: rest in=@rally
voice pad_hi warm_pad role=pad octave=5 pan=0.5
  pad_octave: double source=pad_top octaves=1 dynamic=p

# -- the bass: the front of the mix ----------------------------------------------
voice bass rbx_picked_bass role=bass octave=2 pan=0 engine=soundfont
  for sec in bass drive signal strip
    r_{sec}:    play motif=riff at=@{sec} dynamic=f
    r_{sec}_lo: play motif=riff_low at=@{sec}.5 dynamic=f
  r_build_lo: play motif=riff_low at=@build.5 dynamic=f     -- `ms match --stems`: the reference's bass sits out the first half of the build
  r_signal2:    play motif=riff at=@signal.9 dynamic=f
  r_signal2_lo: play motif=riff_low at=@signal.13 dynamic=f
  for bar in 1 9
    r_wall{bar}:    play motif=riff at=@wall.{bar} dynamic=ff
    r_wall{bar}_lo: play motif=riff_low at=@wall.{bar + 4} dynamic=ff
  r_fade:    play motif=riff at=@fade dynamic=f
  r_fade_lo: play motif=riff_low at=@fade.5 dynamic=f
  fx_bass_grit:  drive amount=0.35
  fx_bass_even:  compress ratio=6 threshold=-20
  fx_bass_round: filter start=750 end=750     -- `ms match`: 15 dB brighter than the reference's bass above 1 kHz
  fx_bass_weight: eq freq=70 gain=7 width=1.5
  lvl_bass:  gain db=-1
  feel_bass: humanize amount=1.0 timing=5

voice sub sub_bass role=bass octave=1
  sub_a: bass at=@bass bars=32 pattern=pedal dynamic=mf
  sub_rally: drone at=@rally bars=8 dynamic=pp
  sub_b: bass at=@build bars=40 pattern=pedal dynamic=f
  sub_tail: drone at=@tail bars=2 dynamic=pp
  fx_sub_level: gain db=14      -- `ms match`: the reference has 45% of its energy under 80 Hz

# -- the kit -----------------------------------------------------------------------
voice drums kit_rock role=percussion engine=soundfont
  d_pick:   beat at=@bass.8:4.5 bars=1 res=1/16 snare=xx dynamic=f      -- two sixteenths of snare before the downbeat
  d_drive:  beat at=@drive bars=8 lanes=$ROCK crash=$EVERY_4 dynamic=f
  d_drive_fill: beat at=@drive.8:3 bars=1 snare=x.xxx.xx tom_mid=....x... kick=x...x... dynamic=f
  d_signal: beat at=@signal bars=16 lanes=$ROCK crash=$EVERY_4 dynamic=f
  for bar in 4 12
    d_sig_cut{bar}: chop in=@signal.{bar}-{bar} slices=16 order="0 1 2 3 4 5 6 7 8 9 10 11 12 12*2 4 4*2"   -- a snare stumble at the end of the fourth bar
  d_sig_fill: beat at=@signal.8:3 bars=1 snare=x.x.xxxx tom_lo=..x...x. kick=x...x... dynamic=f
  d_build:  beat at=@build bars=8 lanes=$TIGHT dynamic=mf
  d_build_fill: beat at=@build.8 bars=1 lanes=$FILL dynamic=f
  d_build_swell: dynamics in=@build.8-8 start=mf end=ff
  d_wall:   beat at=@wall bars=16 lanes=$WIDE crash=$EVERY_4 dynamic=mf
  d_wall_fill: beat at=@wall.8:3 bars=1 snare=xxx.xxxx tom_mid=..x..... tom_lo=......x. dynamic=ff
  d_strip:  beat at=@strip bars=8 lanes=$LOOSE dynamic=mf
  d_fade:   beat at=@fade bars=8 kick=......x.....x...|....o.......x... dynamic=ff     -- `ms match --stems`: in the reference's last section the top of the kit is gone and its backbeat band is 14 dB down; what holds is a sparse kick
  # a room, hit hard, one slab
  fx_slab: compress ratio=8 threshold=-24
  fx_room: drive amount=0.55
  fx_drums_dark: filter start=6500 end=6500     -- the kit carries the top of the mix now, and the reference's top is 8 dB darker
  lvl_drums: gain db=8       -- `ms match --stems`: the reference's kit is level with its bass; this one was 11 dB under
  feel_drums: humanize amount=0.8 timing=6

# -- metal ---------------------------------------------------------------------------
voice pipe metal_pipe role=ornament octave=3 pan=-0.2
  k_toll: phrase at=@rally steps="r:1/2 4:1/2 | r:1/1 | r:1/2 4:1/2 | r:1/1" dynamic=mp     -- struck twice, far off, under the crowd
voice clank clank role=ornament octave=5 pan=0.3
  k_all: play motif=anvil at=@rally.5 times=22 dynamic=mf      -- locked to the grid from here to the end
  k_in:  dynamics from=@rally.5 until=@build start=pp end=mf
  fx_clank_grit: crush rate=14000 bits=9                       -- through a bad microphone
  lvl_clank: gain db=16
  feel_clank: humanize amount=1.0 timing=3

# -- the whistle, and itself again a dotted eighth later, three times ----------------
voice whistle sine_lead role=melody octave=5 pan=0
  w_signal: play motif=signal at=@signal times=2 dynamic=mf articulation=legato
  w_far:    play motif=alarm_far at=@strip times=2 dynamic=mp articulation=legato     -- the signal, half speed, twice
  fx_whistle_edge: drive amount=0.6       -- a sine pushed until it has an edge
  lvl_whistle: gain db=3
voice echo sine_lead role=counter octave=5 pan=-0.6
  e_echo: double source=whistle delay=3/16 dynamic=p from=@signal until=@tail.end
  fx_echo_edge: drive amount=0.6
  fx_echo: filter start=2200 end=2200
  lvl_echo: gain db=3
voice echo2 sine_lead role=counter octave=5 pan=0.6
  e_echo2: double source=whistle delay=3/8 dynamic=pp from=@signal until=@tail.end
  fx_echo2: filter start=1500 end=1500
  lvl_echo2: gain db=5
voice echo3 sine_lead role=counter octave=5 pan=-0.2
  e_echo3: double source=whistle delay=9/16 dynamic=pp from=@signal until=@tail.end
  fx_echo3: filter start=1000 end=1000
  lvl_echo3: gain db=5

# -- the crowd: noise for its breath, a clipped cluster of sung notes for its voices --
voice crowd noise_wall role=pad octave=3
  c_roar: drone at=@rally bars=12 dynamic=f    -- there the moment the band is cut; swells for six bars; takes the build to go away
  crowd_swell: dynamics from=@rally until=@rally.7 start=mp end=ff
  crowd_ebb:   dynamics from=@rally.7 until=@build.5 start=ff end=pp
  # no sweep: a sweep is a riser, and a riser is a different kind of record
  fx_crowd_band: filter start=1800 end=1800
  fx_crowd_low:  filter mode=highpass start=350 end=350
  lvl_crowd: gain db=18
voice mob choir role=pad octave=3 engine=soundfont
  for deg in 0 1 2 4
    m_roar{deg}: drone at=@rally bars=10 degree={deg} dynamic=f
  mob_swell: dynamics from=@rally until=@rally.7 start=mp end=ff
  mob_ebb:   dynamics from=@rally.7 until=@build.3 start=ff end=pp
  fx_mob: drive amount=1.8                     -- until no one pitch can be picked out
  fx_mob_band: filter start=2200 end=2200
  lvl_mob: gain db=4

# -- guitars ----------------------------------------------------------------------------
voice palm muted_guitar role=harmony octave=2 pan=-0.35 engine=soundfont
  g_mute_r: play motif=mute at=@rally.5 times=4 dynamic=mp articulation=staccato
  for sec in build strip
    g_mute_{sec}0: play motif=mute at=@{sec} times=4 dynamic=mf articulation=staccato
    g_mute_{sec}1: play motif=mute_hi at=@{sec}.5 times=4 dynamic=mf articulation=staccato
  fx_palm: drive amount=0.5
  fx_palm_in:  filter from=@rally.5 until=@wall start=500 end=1800
  fx_palm_out: filter in=@strip start=1800 end=500
  lvl_palm: gain db=8
  feel_palm: humanize amount=1.0 timing=4      -- `ms hear`: one recording thirty-two times in a row
voice gtr_l amp_guitar role=harmony octave=2 pan=-0.9 engine=soundfont
  for i in 0..3
    g_ring{i}: play motif=ring transpose={[0, 5][i % 2]} at=@wall.{1 + 4*i} times=2 dynamic=ff
voice gtr_r amp_guitar role=harmony octave=2 pan=0.9 engine=soundfont
  g_fifth: double source=gtr_l interval=4 in=@wall      -- a fifth above: between them, power chords
voice gtr_hi amp_guitar role=harmony octave=3 pan=0 engine=soundfont
  g_octave: double source=gtr_l octaves=1 dynamic=mf in=@wall     -- the octave, in the middle and further back

# the amp is in the recording; this takes the fizz off the top
on gtr_l gtr_r gtr_hi
  fx_{v}_fuzz: drive amount=0.4
  fx_{v}_amp:  filter start=2600 end=2600
on gtr_l gtr_r
  lvl_{v}: gain db=3
on gtr_hi
  lvl_gtr_hi: gain db=-2

# -- the end ------------------------------------------------------------------------------
voice tape shakuhachi role=counter octave=5 engine=soundfont
  t_hold: phrase at=@fade.8 steps="4:1/1~@tr | 4:1/1~ | 4:1/2 r:1/2" dynamic=mp articulation=legato    -- a breathy flute, fluttering, as the band goes
  t_dim: dynamics in=@tail start=mf end=pp
  lvl_tape: gain db=8

# the pad's filter never sits still, and it closes at the end
on pad pad_top pad_hi
  for k in 0..9
    fx_{v}_move{k}: filter from={1 + 8*k} until={9 + 8*k} start={[450, 1300][k % 2]} end={[1300, 450][k % 2]} resonance=0.45
  fx_{v}_out: filter from=@fade until=@tail.end start=1300 end=200
on pad
  lvl_pad: gain db=8
on pad_top pad_hi
  lvl_{v}: gain db=12
