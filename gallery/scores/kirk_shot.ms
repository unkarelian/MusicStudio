piece kirk_shot key="C minor" tempo=154 style=electronic
master push=1 level=-7 room.decay=0.7 room.wet=0.08
meta soundfont = "hq"
meta note = "Arrangement for the user's original sung performance. AI conversion and vocal mix are in the Kirk project folder."

section intro bars=4 dynamic=mp
section hook bars=8 dynamic=f
section turn bars=2 dynamic=mf
section verse bars=8 dynamic=mp
section chorus bars=8 dynamic=f
section breakdown bars=4 dynamic=p
section bridge bars=8 dynamic=mp
section build bars=2 dynamic=mf
section final bars=16 dynamic=ff
section outro bars=4 dynamic=mp

harmony
  @intro: i i VI VII
  @hook: [i i VI VII]*2
  @turn: VI VII
  @verse: [i VI III VII]*2
  @chorus: [i i VI VII]*2
  @breakdown: iv iv VI VII
  @bridge: iv iv VI VI III III VII VII
  @build: iv V7
  @final: [i i VI VII]*3 i VI V7 i
  @outro: i VI VII i

motif spark = 0:1/8 r:1/8 4:1/8 7:1/8 r:1/8 6:1/8 4:1/8 2:1/8
motif spark_up < spark : transpose:7
motif spark_cut < spark : thin:2
motif lift = 0:1/8 2:1/8 4:1/4 3:1/8 2:1/8 0:1/4
motif lift_turn < lift : invert
motif pulse = 0:1/8 r:1/8 0:1/8 1:1/8 r:1/8 0:1/8 2:1/8 r:1/8

lanes DANCE
  kick: X...x...X...x...
  clap: ....X.......X...
  hat: ..x...x...x...x.
  open: ......x.......x.

lanes LIGHT
  kick: X.......x.......
  rim: ....x.......x...
  hat: ..x...x...x...x.

lanes FILL
  kick: X...x...x.......
  snare: ....X.......x.xX
  tom_lo: ..........x..x..
  hat: x.x.x.x.x.xxxxxx

voice drums kit_tr909 role=percussion engine=soundfont pan=0
  intro_tick: beat at=@intro.3 bars=2 lanes=$LIGHT dynamic=mp
  hook_beat: beat at=@hook bars=8 lanes=$DANCE dynamic=f
  hook_fill_4: beat at=@hook.4 bars=1 lanes=$FILL dynamic=mf
  hook_fill_8: beat at=@hook.8 bars=1 lanes=$FILL dynamic=mf
  turn_beat: beat at=@turn bars=2 lanes=$LIGHT dynamic=mp
  verse_beat: beat at=@verse bars=8 lanes=$LIGHT dynamic=mp
  chorus_beat: beat at=@chorus bars=8 lanes=$DANCE dynamic=f
  chorus_fill_4: beat at=@chorus.4 bars=1 lanes=$FILL dynamic=mf
  chorus_fill_8: beat at=@chorus.8 bars=1 lanes=$FILL dynamic=mf
  bridge_beat: beat at=@bridge bars=8 lanes=$LIGHT dynamic=mp
  final_beat: beat at=@final bars=16 lanes=$DANCE dynamic=f
  final_fill_4: beat at=@final.4 bars=1 lanes=$FILL dynamic=mf
  final_fill_8: beat at=@final.8 bars=1 lanes=$FILL dynamic=mf
  final_fill_12: beat at=@final.12 bars=1 lanes=$FILL dynamic=mf
  final_fill_16: beat at=@final.16 bars=1 lanes=$FILL dynamic=mf
  build_roll: beat at=@build bars=2 lanes={"snare":"x.x.x.x.x.x.x.x.|x.x.x.x.xxxxxxxx","kick":"x.......x......."} dynamic=mf
  last_groove: beat at=@outro bars=2 lanes=$LIGHT dynamic=mp
  kit_glue: compress ratio=2.5 threshold=-12
  kit_fader: gain db=-1
voice bass lately_bass role=bass octave=2 engine=soundfont pan=0
  hook_bass: bass at=@hook bars=8 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=f
  turn_bass: bass at=@turn bars=2 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=mf
  verse_bass: bass at=@verse bars=8 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=mf
  chorus_bass: bass at=@chorus bars=8 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=f
  bridge_bass: bass at=@bridge bars=8 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=mf
  final_bass: bass at=@final bars=16 pattern=root rhythm="1/8 1/8 1/4 1/8 1/8 1/4" dynamic=f
  outro_bass: bass at=@outro bars=4 pattern=root rhythm="1/1" dynamic=mp
  bass_shape: filter start=2400
  bass_pump: duck source=drums drum=kick depth=4 release=0.12
  bass_live: humanize amount=0.18 timing=3 seed=34
  bass_level: gain db=-4
voice keys dx_piano role=harmony octave=4 engine=soundfont pan=-0.27
  intro_keys: chords at=@intro bars=4 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  hook_keys: chords at=@hook bars=8 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  turn_keys: chords at=@turn bars=2 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  verse_keys: chords at=@verse bars=8 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=p articulation=staccato
  chorus_keys: chords at=@chorus bars=8 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  breakdown_keys: chords at=@breakdown bars=4 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=p articulation=staccato
  bridge_keys: chords at=@bridge bars=8 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=p articulation=staccato
  build_keys: chords at=@build bars=2 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  final_keys: chords at=@final bars=16 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  outro_keys: chords at=@outro bars=4 voicing=block rhythm="1/8 1/8 1/4 1/4 1/4" rootless=true tones=3 lead=true dynamic=mp articulation=staccato
  key_pocket: humanize amount=0.25 timing=6 seed=41
  key_space: eq freq=1900 gain=-4 width=1.7
  keys_low_cut: filter start=230 mode=highpass
  key_fader: gain db=-10
voice pad dreamy_pad role=pad octave=4 engine=soundfont pan=0.3
  intro_air: chords at=@intro bars=4 voicing=pad tones=2 lead=true dynamic=p
  hook_air: chords at=@hook bars=8 voicing=pad tones=2 lead=true dynamic=p
  verse_air: chords at=@verse bars=8 voicing=pad tones=2 lead=true dynamic=p
  chorus_air: chords at=@chorus bars=8 voicing=pad tones=2 lead=true dynamic=p
  breakdown_air: chords at=@breakdown bars=4 voicing=pad tones=2 lead=true dynamic=p
  bridge_air: chords at=@bridge bars=8 voicing=pad tones=2 lead=true dynamic=p
  build_air: chords at=@build bars=2 voicing=pad tones=2 lead=true dynamic=p
  final_air: chords at=@final bars=16 voicing=pad tones=2 lead=true dynamic=mp
  air_low: filter start=230 mode=highpass
  air_ceiling: filter start=5500
  air_hole: eq freq=1800 gain=-5 width=2
  air_pump: duck source=drums drum=kick depth=5 release=0.2
  air_fader: gain db=-9
voice guitar strat_clean role=harmony octave=4 engine=soundfont pan=0.55
  hook_guitar: chords at=@hook bars=8 figure="r 0+1 r 1+2" rhythm="1/8" lead=true dynamic=mp articulation=staccato
  chorus_guitar: chords at=@chorus bars=8 figure="r 0+1 r 1+2" rhythm="1/8" lead=true dynamic=mp articulation=staccato
  final_guitar: chords at=@final bars=16 figure="r 0+1 r 1+2" rhythm="1/8" lead=true dynamic=mp articulation=staccato
  guitar_fader: gain db=-11
voice arp polysynth role=ornament octave=5 engine=soundfont pan=-0.5
  intro_arp: play motif=pulse at=@intro times=4 anchor=chord dynamic=p
  hook_arp: play motif=pulse at=@hook times=8 anchor=chord dynamic=p
  chorus_arp: play motif=pulse at=@chorus times=8 anchor=chord dynamic=p
  final_arp: play motif=pulse at=@final times=16 anchor=chord dynamic=mp
  outro_arp: play motif=pulse at=@outro times=4 anchor=chord dynamic=p
  arp_body: filter start=900 mode=highpass
  arp_ceiling: filter start=6500
  arp_echo: echo time="1/8." feedback=0.25 mix=0.16 spread=0.9
  arp_fader: gain db=-11
voice reply fm_bells role=melody octave=5 engine=soundfont pan=0.2
  reply_intro_1: play motif=lift at=@intro.1 dynamic=mp
  reply_intro_3: play motif=lift at=@intro.3 dynamic=mp
  reply_turn_1: play motif=lift at=@turn.1 dynamic=mp
  reply_breakdown_1: play motif=lift_turn at=@breakdown.1 dynamic=mp
  reply_breakdown_3: play motif=lift_turn at=@breakdown.3 dynamic=mp
  reply_outro_1: play motif=lift at=@outro.1 dynamic=mp
  reply_outro_3: play motif=lift at=@outro.3 dynamic=mp
  reply_shape: shape amount=0.35
  reply_delay: echo time="1/8." feedback=0.32 mix=0.2
  reply_fader: gain db=-5
voice synth detuned_saws role=ornament octave=5 engine=soundfont pan=-0.1
  opening_spark: play motif=spark at=@intro.3 dynamic=mp
  hook_spark: play motif=spark_cut at=@hook.8 dynamic=p
  chorus_spark: play motif=spark at=@chorus.8 dynamic=p
  final_spark: play motif=spark_up at=@final.8 dynamic=mp
  closing_spark: play motif=spark at=@final.16 dynamic=mp
  synth_cut: filter start=4200
  synth_fader: gain db=-12
