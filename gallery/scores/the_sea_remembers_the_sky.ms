# The Sea Remembers the Sky — a symphonic instrumental in nine scenes.
# Small rising fifth, falling answer; the storm compresses it into seven.
piece the_sea_remembers_the_sky key="D minor" tempo=104 style=orchestral
master room.decay=2.6 room.wet=0.23
meta title = "The Sea Remembers the Sky"
meta soundfont = "hq"

section shore bars=8 tempo=84 tempo_end=96 dynamic=p
section horizon bars=16 tempo=104 dynamic=mf
section current bars=8 tempo=108 tempo_end=116 dynamic=mf
section storm bars=16 meter=7/8 tempo=116 dynamic=f
section suspended bars=8 tempo=76 key="F major" dynamic=p
section ascent bars=16 tempo=104 tempo_end=116 dynamic=mf
section sky bars=16 tempo=108 dynamic=ff
section home bars=8 tempo=88 tempo_end=58 dynamic=p

harmony
  @shore: i . VImaj7 . iv . V7 .
  @horizon: [i VImaj7 iv V7 i III V7 i]*2
  @current: VImaj7 III iv V7 ii%7 . V7 .
  @storm: [i VII VImaj7 V7]*2 iv VImaj7 ii%7 V7 VImaj7 iv V7 .
  @suspended: I . vi7 . IVmaj7 . V7 .
  @ascent: i . VImaj7 . iv . V7 . i . III . V7 . V7 .
  @sky: i VImaj7 iv V7 i III V7 i VImaj7 III iv V7 ii%7 V7 i .
  @home: VImaj7 . iv V7 i . . .

motif call = 0:1/4 4:1/4. 3:1/8 2:1/4 | 2:1/4. 1:1/8 0:1/4 -3:1/4 | 3:1/4 5:1/4 4:1/4 3:1/8 2:1/8 | 1:1/4 #6:1/4 4:1/4 r:1/4
motif answer = 0:1/4 2:1/4 4:1/2 | 6:1/4 5:1/8 4:1/8 3:1/4 1:1/4 | 1:1/4 4:1/4 #6:1/4 5:1/8 4:1/8 | 0:1/2. r:1/4
motif theme < call : then:answer
motif seed < call : fragment:0,4
motif distant < seed : augment:2
motif glint < seed : embellish:passing
motif theme_bloom < theme : embellish:neighbor,1 5
motif tide = 0:1/8 2:1/8 4:1/8 3:1/8 2:1/8 1:1/8 2:1/8
motif storm_call < seed : rhythmize:1/8 1/4 1/4 1/4
motif storm_answer < storm_call : invert > transpose:4
motif tide_return < tide : rotate:2
motif quiet = 2:1/2 4:1/4 3:1/4 | 2:1/4 1:1/4 0:1/2 | 2:1/4 3:1/4 5:1/2 | 4:1/2. r:1/4
motif quiet_reply < quiet : invert:2
motif remembrance < theme : augment:2
motif counter = 1:1/2 2:1/2 | 1:1/2 0:1/2 | 1:1/2 2:1/2 | 1:1/2 r:1/2 anchor=chord
motif crest < seed : transpose:7
motif farewell < seed : augment:2 > append:1:1/2 0:1/1. 

lanes PULSE
  kick: x.......x.....x.|x.........x.....
  snare: ....x.......x...|....x.......x..o
  hat: x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.o.
lanes SEVEN
  kick: X.....x...x...|x.....x.....x.
  snare: ......X.......|......X....o..
  hat: X.x.x.X.x.X.x.|X.x.x.X.x.X.oo
lanes SKY
  kick: X.....x.x.......|x.....x...x...x.
  snare: ....X.......X...|....X..o....X...
  ride: x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.o.
lanes FILL
  kick: x.......x.......
  snare: ....x...o.o.xx..
  tom_mid: ............x.x.
  tom_lo: ...............x

voice piano concert_grand role=melody octave=4 pan=-0.12 engine=soundfont
  opening: play motif=seed at=@shore dynamic=mp
  opening_answer: play motif=distant at=@shore.5 transform=["transpose:-2"] dynamic=p
  storm_spray: play motif=tide at=@storm.2 times=3 every="7/4" octave=5 dynamic=mp
  storm_spray_return: play motif=tide_return at=@storm.8 times=4 every="7/4" octave=5 dynamic=mp
  quiet_left: play motif=quiet at=@suspended dynamic=mp
  quiet_right: play motif=quiet_reply at=@suspended.5 dynamic=p
  quiet_resolution: rest from=@suspended.8 until=@suspended.end
  quiet_dominant: phrase at=@suspended.8 steps="1:1/2. r:1/4" dynamic=p
  climb_fragment: play motif=glint at=@ascent.9 times=4 every="1/1" octave=4 dynamic=p
  return_seed: play motif=distant at=@home dynamic=mp
  ending: phrase at=@home.5 steps="2:1/4 1:1/4 0:1/2~ 0:1/1 r:1/1 r:1/1" dynamic=p
  piano_shape: shape amount=0.65
  piano_human: humanize amount=0.25 timing=8 seed=71
  piano_level: gain db=1

voice violin violin role=melody octave=5 pan=-0.25 engine=soundfont bank=hq
  first_theme: play motif=theme at=@horizon dynamic=mf articulation=legato
  fuller_theme: play motif=theme_bloom at=@horizon.9 dynamic=f articulation=legato
  current_call: play motif=call at=@current dynamic=mf
  current_rise: play motif=glint transpose=1 at=@current.5 times=4 every="1/1" dynamic=mf
  storm_signal: play motif=storm_call at=@storm times=4 every="7/4" dynamic=f
  storm_reply: play motif=storm_answer at=@storm.9 dynamic=f
  storm_reply_shift: play motif=storm_answer at=@storm.11 transpose=1 dynamic=f
  storm_reply_end: play motif=storm_answer at=@storm.13 dynamic=f
  storm_end: phrase at=@storm.15 steps="1:1/4 2:1/8 1:1/4 #6:1/4 | 4:1/2 r:3/8" dynamic=f
  long_return: play motif=remembrance at=@ascent dynamic=mp articulation=legato
  ascent_breath: rest from=@ascent.15 until=@ascent.end
  ascent_last: phrase at=@ascent.15 steps="1:1/2 3:1/2 | 4:1/2 #6:1/4 r:1/4" dynamic=f
  sky_theme: play motif=theme_bloom at=@sky dynamic=ff articulation=legato
  sky_call: play motif=call at=@sky.9 dynamic=ff
  high_water: play motif=crest at=@sky.13 dynamic=ff
  cadence: phrase at=@sky.14 steps="8:1/4 #6:1/4 4:1/4 #6:1/4 | 7:1/1~ 7:1/2 r:1/2" dynamic=f
  final_echo: play motif=farewell at=@home.3 dynamic=p
  violin_shape: shape amount=0.6
  violin_build: dynamics in=@ascent start=mp end=f
  violin_level: gain db=1
  violin_human: humanize amount=0.18 timing=5 seed=12

voice cello cello role=counter octave=3 pan=0.22 engine=soundfont bank=hq
  shore_reply: play motif=distant at=@shore.3 dynamic=p
  shore_last: phrase at=@shore.7 steps="3:1/2 2:1/2 | 1:1/2 r:1/2" dynamic=p
  a_counter: play motif=counter at=@horizon.5 dynamic=p articulation=legato
  a_counter2: play motif=counter at=@horizon.13 transform=["invert:1"] dynamic=mp articulation=legato
  beneath_current: bass at=@current bars=8 octave=3 rhythm=1/2 dynamic=p
  storm_bow: bass at=@storm bars=15 octave=3 rhythm=1/8 pattern=root_fifth dynamic=mp articulation=staccato
  quiet_floor: bass at=@suspended bars=8 octave=2 rhythm=1/1 dynamic=pp
  climb_counter: play motif=counter at=@ascent.9 times=2 dynamic=mp
  sky_counter: play motif=counter at=@sky times=4 dynamic=mf articulation=legato
  home_reply: phrase at=@home.3 steps="3:1/2 2:1/2 | 1:1/2 #6:1/2" dynamic=p
  home_root: drone at=@home.5 bars=4 degree=0 octave=3 dynamic=pp
  cello_shape: shape amount=0.45
  cello_human: humanize amount=0.2 timing=6 seed=31
  cello_level: gain db=-1

voice water concert_grand role=harmony octave=4 pan=0.12 engine=soundfont
  shore_water: chords at=@shore bars=8 voicing=broken rhythm=1/4 tones=3 lead=true dynamic=pp
  a_water: chords at=@horizon bars=16 figure="0 2 1 2" rhythm=1/8 tones=3 lead=true dynamic=p
  current_water: chords at=@current bars=8 figure="0 1 2 1 0 2 1 2" rhythm=1/8 lead=true dynamic=mp
  storm_water: chords at=@storm bars=16 figure="0 2 1 2 0 1 2" rhythm=1/8 lead=true dynamic=p
  suspended_water: chords at=@suspended bars=8 voicing=broken rhythm=1/2 octave=3 tones=3 lead=true dynamic=pp
  ascent_water: chords at=@ascent bars=16 figure="0 2 1 2" rhythm=1/8 lead=true dynamic=p
  sky_water: chords at=@sky bars=16 figure="0 2 1 2" rhythm=1/8 lead=true dynamic=mp
  home_water: chords at=@home bars=6 voicing=pad rhythm=1/1 roll=1/32 lead=true dynamic=p
  last_chord: chords at=@home.7 bars=2 voicing=pad tones=3 octave=3 dynamic=pp
  water_shape: shape amount=0.3
  water_human: humanize amount=0.25 timing=7 seed=4
  water_opening: dynamics in=@shore start=ppp end=ppp
  water_current: dynamics in=@current start=p end=p
  water_ending: dynamics in=@home start=p end=pp
  water_level: gain db=-6

voice strings strings role=pad octave=4 pan=-0.42 engine=soundfont bank=hq
  first_air: chords at=@horizon.9 bars=8 voicing=pad tones=3 lead=true dynamic=pp
  current_air: chords at=@current bars=8 voicing=pad tones=3 lead=true dynamic=p
  storm_air: chords at=@storm.9 bars=8 voicing=pad tones=3 lead=true dynamic=mp
  suspended_air: chords at=@suspended.5 bars=3 voicing=pad tones=3 lead=true dynamic=pp
  ascent_air: chords at=@ascent bars=16 voicing=pad tones=3 lead=true dynamic=p
  sky_air: chords at=@sky bars=16 voicing=pad tones=3 lead=true dynamic=mf
  strings_crescendo: dynamics in=@ascent start=pp end=mf
  strings_quiet: dynamics in=@suspended start=ppp end=ppp
  strings_home: dynamics in=@home start=ppp end=ppp
  strings_level: gain db=-9

voice horn horn role=counter octave=4 pan=0.35 engine=soundfont bank=hq
  horn_foreshadow: play motif=counter at=@current.5 octave=3 dynamic=p
  horn_climb: drone at=@ascent.15 bars=2 degree=4 dynamic=p
  horn_arrival: play motif=theme at=@sky dynamic=mf articulation=legato
  horn_last: play motif=counter at=@sky.13 dynamic=mf articulation=legato
  horn_shape: shape amount=0.55
  horn_level: gain db=0

voice light harp role=ornament octave=5 pan=0.5 engine=soundfont bank=hq
  shore_glimmer: play motif=glint at=@shore.8 dynamic=pp
  end_a: play motif=glint at=@horizon.8 dynamic=p
  end_a2: play motif=glint at=@horizon.16 dynamic=p
  quiet_glimmer: play motif=glint at=@suspended.4 dynamic=pp
  quiet_glimmer2: play motif=glint at=@suspended.8 dynamic=pp
  sky_glimmer: chords at=@sky bars=16 voicing=arpeggio_updown rhythm=1/8 tones=3 dynamic=p
  last_glimmer: play motif=distant at=@home.7 dynamic=pp
  light_level: gain db=3

voice bass contrabass role=bass octave=2 pan=0.05 engine=soundfont bank=hq
  a_ground: bass at=@horizon bars=16 rhythm=1/2 dynamic=p
  current_ground: bass at=@current bars=8 rhythm=1/4 dynamic=mp
  storm_ground: bass at=@storm bars=16 rhythm=1/4 dynamic=mf
  climb_ground: bass at=@ascent bars=16 rhythm=1/2 dynamic=p
  sky_ground: bass at=@sky bars=16 rhythm=1/2 dynamic=mf
  home_ground: bass at=@home bars=6 rhythm=1/1 dynamic=pp
  bass_build: dynamics in=@ascent start=p end=mf
  bass_level: gain db=0

voice drums kit_rock role=percussion pan=0 engine=soundfont
  first_pulse: beat at=@horizon.9 bars=7 lanes=$PULSE dynamic=p
  first_fill: beat at=@horizon.16 bars=1 lanes=$FILL dynamic=p
  current_pulse: beat at=@current bars=7 lanes=$PULSE dynamic=mp
  current_fill: beat at=@current.8 bars=1 lanes=$FILL dynamic=mf
  storm_pulse: beat at=@storm bars=16 lanes=$SEVEN dynamic=mf
  storm_breath: rest from=@storm.16:3 until=@storm.end
  ascent_pulse: beat at=@ascent.9 bars=7 lanes=$PULSE dynamic=mp
  ascent_fill: beat at=@ascent.16 bars=1 lanes=$FILL dynamic=f
  sky_pulse: beat at=@sky bars=15 lanes=$SKY dynamic=f
  sky_last: beat at=@sky.16 bars=1 lanes={"kick":"x...............","crash":"x..............."} dynamic=mf
  sky_crash: beat at=@sky bars=1 lanes={"crash":"x..............."} dynamic=mf
  second_crash: beat at=@sky.9 bars=1 lanes={"crash":"x..............."} dynamic=mf
  drums_human: humanize amount=0.25 timing=5 seed=41
  drums_level: gain db=-2
