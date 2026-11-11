# press_start_teto. Press Start sung by Kasane Teto's UTAU voicebanks: the same
# piece as press_start.ms with the singers changed, and nothing else.
#
# The three English voices ask for bank=utau:teto_en and the Japanese chant for
# bank=utau:teto. Neither bank is in the repository or fetched by the studio:
# they are free downloads from kasaneteto.jp under their author's terms
# (non-commercial use, no redistribution), added with `ms utau add`. Without
# them the piece still builds, sung by the built-in singer.
piece press_start_teto key="C major" tempo=170 style=electronic
master push=6.0 room.decay=0.7 room.wet=0.06
stop from=13:3 until="14" keep=["vox", "harm", "body", "chant"]
stop from=21:3 until="22" keep=["vox", "harm", "body", "chant"]
stop from=62:3 until="63" keep=["vox", "harm", "body", "chant"]
stop from="104" until="105" keep=["box"]
stop from="130" until="132" keep=["vox", "harm", "body", "chant"]
stop from=32:3 until="33" keep=["vox", "harm", "body", "chant"]
stop from=73:3 until="74" keep=["vox", "harm", "body", "chant"]
stop from=46:3 until="47" keep=["vox", "harm", "body", "chant"]
stop from=87:3 until="88" keep=["vox", "harm", "body", "chant"]
stop from=119:3 until="120" keep=["vox", "harm", "body", "chant"]

section chime bars=3 dynamic=p
section groove bars=2 dynamic=f key="A minor"
section verse bars=18 dynamic=mf key="A minor"
section pre bars=9 dynamic=mp
section chorus bars=16 dynamic=ff
section post bars=6 dynamic=f
section verse2 bars=10 dynamic=mf key="A minor"
section pre2 bars=9 dynamic=mp
section chorus2 bars=16 dynamic=ff
section post2 bars=6 dynamic=f
section bridge bars=10 dynamic=mp
section chorus3 bars=16 dynamic=ff
section tag bars=8 dynamic=ff
section chorale bars=4 dynamic=mf

harmony
  1: Imaj7 Imaj7 Imaj7 i7 V7 i7 iv7 VII7 IIImaj7
  9:3: V7
  10: i7 iv7 ii%7
  12:3: V7
  13: i7 i7 iv7 VII7 IIImaj7
  17:3: V7
  18: i7 iv7 ii%7
  20:3: V7
  21: i7 i7 V7 IVmaj7 V7 iii7 vi7 ii7 iv V7sus4 V7 V7 IVmaj7 V7 iii7 vi7 ii7 V7 Imaj7 V7/IV IVmaj7 V7 V7/vi vi7 ii7 ii%7 Imaj7 Imaj7 IVmaj7 V7 IVmaj7 V7 IVmaj7 V7 i7 iv7 VII7 IIImaj7
  58:3: V7
  59: i7 iv7 ii%7
  61:3: V7
  62: i7 iv7 V7 IVmaj7 V7 iii7 vi7 ii7 iv V7sus4 V7 V7 IVmaj7 V7 iii7 vi7 ii7 V7 Imaj7 V7/IV IVmaj7 V7 V7/vi vi7 ii7 ii%7 Imaj7 Imaj7 IVmaj7 V7 IVmaj7 V7 IVmaj7 V7 IVmaj7 IVmaj7 V7 V7 iii7 vi7 ii7 V7 V7 V7 IVmaj7 V7 iii7 vi7 ii7 V7 Imaj7 V7/IV IVmaj7 V7 V7/vi vi7 ii7 ii%7 Imaj7 Imaj7 IVmaj7 V7 IVmaj7 V7 IVmaj7 V7 IVmaj7 V7 Imaj7 Imaj7 Imaj7 Imaj7

motif bounce = r 4 4 2 4:1/4 2 1 2:1/4. 0:1/4. r:1/4   -- eight notes, entering off the beat and leaning on the threes
motif bounce_up = r 4 4 6 7:1/4 6 4 6:1/4. 4:1/4. r:1/4   -- the answer, a third higher
motif patter = 2 2 2 4 2 2 1 2 4 4 4 6 4 2:1/4 r   -- fourteen notes, almost all on two pitches: the words do the work
motif patter_home = 0 0 0 2 0 0 #6 0 2 4 2 1 0:1/4 r:1/4.   -- thirteen notes through the raised seventh, landing on the stab
motif tag = 0:1/4 2:1/4 3:1/2 4:1/4 4:1/4 #6:1/2   -- verse two's extra two bars: it ends on the leading note, unresolved
motif step_1 = 0:1/4 1:1/4 2:1/2 2:1/4 2:1/4 1:1/2
motif step_2 = 1:1/4 2:1/4 4:1/2 4:1/4 4:1/4 2:1/2   -- the same shape a step up, bent to stay on the chords
motif step_3 = 2:1/4 3:1/4 4:1/2 4:1/4 b5:1/4 7:1/2   -- the same climb, and this time it keeps going -- through the flat sixth of the borrowed minor four -- to the tonic
motif belt = 3:1/4 4:1/2.~ 4:1/1~ 4:1/4 r:1/2 2 4   -- one note for nine beats over the dominant, a hole, and the two-note pickup that the band is cut for
motif call = 4:1/4. 7:1/4 r 5:1/4 4 6:1/4 4 5:1/2   -- up a fourth to the tonic in two notes, a gap for the words to land in, then it settles
motif answer = 4:1/4. 6:1/4. 4:1/4 2 4:1/4 6 7:1/2   -- the same rhythm; where the call fell, this one rises
motif climb = 3:1/4. 5:1/4. 7:1/4 6 7:1/4 8 8:1/2   -- to the top of the tune, held through the half bar the band stops for
motif climb_ache < climb recorded "fragment:0,3 + append" = 3:1/4. 5:1/4. 7:1/4 b5 7:1/4 8 8:1/2   -- the climb over the minor four: one flat on the way up
motif give = 8 7 7 6 4:1/4 2:1/4 7:1/1   -- the words go by in one bar so the last one can have the next to itself: a whole bar on the tonic, at the top
motif sting = #4:1/4. 6:1/4. #4:1/4 5 7:1/4 5 7:1/2   -- the call's rhythm on the dominant of the relative minor: one note from outside the key, resolving up
motif land = 4 6 7 6 4:1/4 8:1/4 7:1/1   -- the same trick to end on: six words in a bar, one held for a bar
motif chant = 4:1/4 4:1/4 5:1/4 7:1/4 5:1/1   -- five notes of the pentatonic scale, for the second voice
motif float_1 = r:1/2 4:1/4 4:1/4 7:1/2. 5:1/4 4:1/2 6:1/2 4:1/1
motif float_2 = r:1/2 4:1/4 4:1/4 7:1/2. 5:1/4 8:1/2 7:1/2 8:1/1
motif slap = 0 r 4 r r 0 r 2 anchor=chord   -- the verse bass: root, its octave, root, fifth, with air between. It used to end every bar on a run of sixteenths through the seventh, which driven hard and doubled by the kick was a drum fill in every bar -- the first thing heard, and all that was
motif disco = 0 4 r:1/16 0:1/16 4 0 4 2:1/16 3:1/16 4 anchor=chord   -- the chorus bass: octaves with a hole in them and a run up to the next bar, where it used to be straight eighths
motif punch = r:1/2 r 2 3 4 anchor=chord   -- horns: three chord tones up into the next line, in the gap the voice leaves at the end of each one
motif blip = 0:1/16 1:1/16 2:1/16 3:1/16 4:1/16 3:1/16 2:1/16 1:1/16 anchor=chord   -- a chiptune flourish up the chord and back
motif fanfare = 4 4:1/16 4:1/16 r 7 6 4 r 5 4:1/4 r 2 4:1/2   -- the riff the band opens with and comes back to after each chorus
motif chime = 7 4 2 4 7 9 7 4 8:1/4 6:1/4 4:1/2   -- a music box, before anything else

voice vox singer role=melody pan=0.0 bank=utau:teto_en
  v1_0: play transpose=0 octave=3 times=1 motif=bounce at="6"
  v1_1: play transpose=0 octave=3 times=1 motif=bounce_up at="8"
  v1_2: play transpose=0 octave=3 times=1 motif=patter at="10"
  v1_3: play transpose=0 octave=3 times=1 motif=patter_home at="12"
  v1_4: play transpose=0 octave=3 times=1 motif=bounce at="14"
  v1_5: play transpose=0 octave=3 times=1 motif=bounce_up at="16"
  v1_6: play transpose=0 octave=3 times=1 motif=patter at="18"
  v1_7: play transpose=0 octave=3 times=1 motif=patter_home at="20"
  w_v1: lyrics lang=auto said={"left": "l eh f t", "me": "m iy", "in": "ih n", "a": "ah", "drawer": "d r ao r", "july": "jh uw l ay", "dust": "d ah s t", "is": "ih z", "falling": "f aa l ih ng", "soft": "s aa f t", "as": "ae z", "lie": "l ay", "i": "ay", "kept": "k eh p t", "each": "iy ch", "little": "l ih t ah l", "thing": "th ih ng", "you": "y uw", "ever": "eh v er", "let": "l eh t", "hold": "hh ow l d", "on": "aa n", "to": "t uw", "sixteen": "s ih k s t iy n", "bits": "b ih t s", "of": "ah v", "memory": "m eh m er iy", "and": "ah n d", "all": "ao l", "them": "dh eh m", "are": "aa r", "pixel": "p ih k s ah l", "heart": "hh aa r t", "with": "w ih dh", "one": "w ah n", "life": "l ay f", "go": "g ow", "waiting": "w ey t ih ng", "where": "w eh r", "saved": "s ey v d", "long": "l ao ng", "ago": "ah g ow", "count": "k aw n t", "the": "dh ah", "seconds": "s eh k ah n d z", "dark": "d aa r k", "behind": "b ih hh ay n d", "gray": "g r ey", "plastic": "p l ae s t ih k", "door": "d ao r", "if": "ih f", "press": "p r eh s", "button": "b ah t ah n", "will": "w ih l", "be": "b iy", "here": "hh iy r", "like": "l ay k", "before": "b ih f ao r"} from="6" until="22" text="left me in a drawer in Ju-ly | dust is fall-ing soft as a lie | I kept each lit-tle thing you ev-er let me hold on to | six-teen bits of mem-o-ry and all of them are you | pix-el heart with one life to go | wait-ing where you saved long a-go | count the sec-onds in the dark be-hind the gray plas-tic door | if you press the but-ton I will be here like be-fore"
  v2_0: play transpose=0 octave=3 times=1 motif=bounce at="55"
  v2_1: play transpose=0 octave=3 times=1 motif=bounce_up at="57"
  v2_2: play transpose=0 octave=3 times=1 motif=patter at="59"
  v2_3: play transpose=0 octave=3 times=1 motif=patter_home at="61"
  v2_tag: play transpose=0 octave=3 times=1 motif=tag at="63"
  w_v2: lyrics lang=auto said={"battery": "b ae t er iy", "is": "ih z", "red": "r eh d", "but": "b ah t", "i'm": "ay m", "fine": "f ay n", "humming": "hh ah m ih ng", "through": "th r uw", "the": "dh ah", "night": "n ay t", "just": "jh ah s t", "to": "t uw", "shine": "sh ay n", "i": "ay", "remember": "r ih m eh m b er", "how": "hh aw", "you": "y uw", "laughed": "l ae f t", "when": "w eh n", "we": "w iy", "beat": "b iy t", "final": "f ay n ah l", "boss": "b aa s", "now": "n aw", "credits": "k r eh d ih t s", "never": "n eh v er", "roll": "r ow l", "froze": "f r ow z", "them": "dh eh m", "for": "f ao r", "us": "ah s"} from="55" until="65" text="bat-ter-y is red but I'm fine | hum-ming through the night just to shine | I re-mem-ber how you laughed when we beat the fi-nal boss | now the cred-its nev-er roll I froze them just for us | just for us just for us"
  pre_0: play transpose=0 octave=4 times=1 motif=step_1 at="24"
  pre_1: play transpose=0 octave=4 times=1 motif=step_2 at="26"
  pre_2: play transpose=0 octave=4 times=1 motif=step_3 at="28"
  pre_belt: play transpose=0 octave=4 times=1 motif=belt at="30"
  w_pre: lyrics lang=auto said={"do": "d uw", "you": "y uw", "still": "s t ih l", "remember": "r ih m eh m b er", "how": "hh aw", "the": "dh ah", "story": "s t ao r iy", "goes": "g ow z", "on": "aa n", "i": "ay", "have": "hh ae v", "been": "b ih n", "here": "hh iy r", "waiting": "w ey t ih ng", "for": "f ao r", "come": "k ah m"} from="24" until="33" text="do you still re-mem-ber | how the sto-ry goes on | I have been here wait-ing | for you | come on"
  pre2_0: play transpose=0 octave=4 times=1 motif=step_1 at="65"
  pre2_1: play transpose=0 octave=4 times=1 motif=step_2 at="67"
  pre2_2: play transpose=0 octave=4 times=1 motif=step_3 at="69"
  pre2_belt: play transpose=0 octave=4 times=1 motif=belt at="71"
  w_pre2: lyrics lang=auto said={"do": "d uw", "you": "y uw", "still": "s t ih l", "remember": "r ih m eh m b er", "how": "hh aw", "the": "dh ah", "story": "s t ao r iy", "goes": "g ow z", "on": "aa n", "i": "ay", "have": "hh ae v", "been": "b ih n", "here": "hh iy r", "waiting": "w ey t ih ng", "for": "f ao r", "come": "k ah m"} from="65" until="74" text="do you still re-mem-ber | how the sto-ry goes on | I have been here wait-ing | for you | come on"
  chorus_0: play transpose=0 octave=4 times=1 motif=call at="33"
  chorus_1: play transpose=0 octave=4 times=1 motif=answer at="35"
  chorus_2: play transpose=0 octave=4 times=1 motif=climb at="37"
  chorus_3: play transpose=0 octave=4 times=1 motif=give at="39"
  chorus_4: play transpose=0 octave=4 times=1 motif=call at="41"
  chorus_5: play transpose=0 octave=4 times=1 motif=sting at="43"
  chorus_6: play transpose=0 octave=4 times=1 motif=climb_ache at="45"
  chorus_7: play transpose=0 octave=4 times=1 motif=land at="47"
  w_chorus: lyrics lang=auto said={"press": "p r eh s", "start": "s t aa r t", "i'm": "ay m", "awake": "ah w ey k", "again": "ah g eh n", "ten": "t eh n", "nine": "n ay n", "count": "k aw n t", "me": "m iy", "down": "d aw n", "my": "m ay", "friend": "f r eh n d", "all": "ao l", "the": "dh ah", "lives": "l ay v z", "i": "ay", "never": "n eh v er", "spent": "s p eh n t", "was": "w aa z", "saving": "s ey v ih ng", "them": "dh eh m", "for": "f ao r", "you": "y uw", "alive": "ah l ay v", "tonight": "t ah n ay t", "one": "w ah n", "more": "m ao r", "coin": "k oy n", "and": "ah n d", "fight": "f ay t", "endings": "eh n d ih ng z", "that": "dh ae t", "we": "w iy", "missed": "m ih s t", "can": "k ae n", "play": "p l ey", "anew": "ah n uw"} from="33" until="49" text="press start I'm a-wake a-gain | ten nine count me down my friend | all the lives I nev-er spent | I was sav-ing them for you | press start I'm a-live to-night | one more coin and one more fight | all the end-ings that we missed | we can play them all a-new"
  chorus2_0: play transpose=0 octave=4 times=1 motif=call at="74"
  chorus2_1: play transpose=0 octave=4 times=1 motif=answer at="76"
  chorus2_2: play transpose=0 octave=4 times=1 motif=climb at="78"
  chorus2_3: play transpose=0 octave=4 times=1 motif=give at="80"
  chorus2_4: play transpose=0 octave=4 times=1 motif=call at="82"
  chorus2_5: play transpose=0 octave=4 times=1 motif=sting at="84"
  chorus2_6: play transpose=0 octave=4 times=1 motif=climb_ache at="86"
  chorus2_7: play transpose=0 octave=4 times=1 motif=land at="88"
  w_chorus2: lyrics lang=auto said={"press": "p r eh s", "start": "s t aa r t", "i'm": "ay m", "awake": "ah w ey k", "again": "ah g eh n", "ten": "t eh n", "nine": "n ay n", "count": "k aw n t", "me": "m iy", "down": "d aw n", "my": "m ay", "friend": "f r eh n d", "all": "ao l", "the": "dh ah", "lives": "l ay v z", "i": "ay", "never": "n eh v er", "spent": "s p eh n t", "was": "w aa z", "saving": "s ey v ih ng", "them": "dh eh m", "for": "f ao r", "you": "y uw", "alive": "ah l ay v", "tonight": "t ah n ay t", "one": "w ah n", "more": "m ao r", "coin": "k oy n", "and": "ah n d", "fight": "f ay t", "endings": "eh n d ih ng z", "that": "dh ae t", "we": "w iy", "missed": "m ih s t", "can": "k ae n", "play": "p l ey", "anew": "ah n uw"} from="74" until="90" text="press start I'm a-wake a-gain | ten nine count me down my friend | all the lives I nev-er spent | I was sav-ing them for you | press start I'm a-live to-night | one more coin and one more fight | all the end-ings that we missed | we can play them all a-new"
  chorus3_0: play transpose=0 octave=4 times=1 motif=call at="106"
  chorus3_1: play transpose=0 octave=4 times=1 motif=answer at="108"
  chorus3_2: play transpose=0 octave=4 times=1 motif=climb at="110"
  chorus3_3: play transpose=0 octave=4 times=1 motif=give at="112"
  chorus3_4: play transpose=0 octave=4 times=1 motif=call at="114"
  chorus3_5: play transpose=0 octave=4 times=1 motif=sting at="116"
  chorus3_6: play transpose=0 octave=4 times=1 motif=climb_ache at="118"
  chorus3_7: play transpose=0 octave=4 times=1 motif=land at="120"
  w_chorus3: lyrics lang=auto said={"press": "p r eh s", "start": "s t aa r t", "i'm": "ay m", "awake": "ah w ey k", "again": "ah g eh n", "ten": "t eh n", "nine": "n ay n", "count": "k aw n t", "me": "m iy", "down": "d aw n", "my": "m ay", "friend": "f r eh n d", "all": "ao l", "the": "dh ah", "lives": "l ay v z", "i": "ay", "never": "n eh v er", "spent": "s p eh n t", "was": "w aa z", "saving": "s ey v ih ng", "them": "dh eh m", "for": "f ao r", "you": "y uw", "alive": "ah l ay v", "tonight": "t ah n ay t", "one": "w ah n", "more": "m ao r", "coin": "k oy n", "and": "ah n d", "fight": "f ay t", "endings": "eh n d ih ng z", "that": "dh ae t", "we": "w iy", "missed": "m ih s t", "can": "k ae n", "play": "p l ey", "anew": "ah n uw"} from="106" until="122" text="press start I'm a-wake a-gain | ten nine count me down my friend | all the lives I nev-er spent | I was sav-ing them for you | press start I'm a-live to-night | one more coin and one more fight | all the end-ings that we missed | we can play them all a-new"
  br_0: play transpose=0 octave=4 times=1 dynamic=mp motif=float_1 at="96"
  br_1: play transpose=0 octave=4 times=1 dynamic=mf motif=float_2 at="100"
  w_bridge: lyrics lang=auto said={"if": "ih f", "the": "dh ah", "screen": "s k r iy n", "goes": "g ow z", "dark": "d aa r k", "tonight": "t ah n ay t", "i": "ay", "will": "w ih l", "keep": "k iy p", "your": "y ao r", "place": "p l ey s", "for": "f ao r", "you": "y uw"} from="96" until="104" text="if the screen goes dark to-night | I will keep your place for you"
  tag_lead: phrase unit=1/1 octave=4 transpose=0 anchor=scale at="122" steps="7 | 8 | 7 | 6 | 7 | 8 | 5 | 6"   -- whole notes over the chant: the other half of the counterpoint
  w_tag: lyrics lang=auto said={"press": "p r eh s", "start": "s t aa r t", "i'm": "ay m", "here": "hh iy r", "again": "ah g eh n"} from="122" until="130" text="press start | I'm here | press start | a-gain"
  last: phrase unit=1/8 octave=4 transpose=0 anchor=scale at="130" steps="8:1/2 8:1/2 | 7:1/1"
  w_last: lyrics lang=auto said={"continue": "k ah n t ih n y uw"} from="130" until="132" text=con-tin-ue
  vox_legato: articulate style=legato from="1" until="134"
  vox_shape: shape amount=0.4 peak=0.62 breath=1/4
  tone_vox: tone breath=-2 firm=3 crisp=1.2 gender=0.05
  grit_vox: drive amount=0.2 mode=soft   -- a little tube: edge on the belts. Drive is matched at the peak, and a voice is mostly peak, so this is also 8 dB of loudness -- taken back off at the fader below
  fx_vox: compress ratio=4 threshold=-18 makeup=0.0
  eq_vox: eq width=1.5 freq=3000 gain=1   -- (+4 for the neural singer; this voice has its own presence) was a 3 dB cut for an edge on long high notes; against the reference the voice had a sixth of its 2-4 kHz
  air_vox: eq freq=8000 gain=5 width=2.5     -- (+10 for the neural singer, which had no top; this one measured 24% above 4 kHz with it) `ms match --stems`: 0.3% of the voice above 4 kHz against the reference's 12%
  lvl_vox: gain db=1.5

voice harm singer role=counter pan=0.5 bank=utau:teto_en
  h_chorus_b: double interval=-2 octaves=0 dynamic=mf from="35" until="37" source=vox
  h_chorus_d: double interval=-2 octaves=0 dynamic=mf from="39" until="40" source=vox
  h_chorus_d2: double interval=-3 octaves=0 dynamic=mf from="40" until="41" source=vox
  h_chorus_f: double interval=-2 octaves=0 dynamic=mf from="44" until="45" source=vox
  h_chorus_h: double interval=-2 octaves=0 dynamic=mf from="47" until="49" source=vox
  h_chorus2_b: double interval=-2 octaves=0 dynamic=mf from="76" until="78" source=vox
  h_chorus2_d: double interval=-2 octaves=0 dynamic=mf from="80" until="81" source=vox
  h_chorus2_d2: double interval=-3 octaves=0 dynamic=mf from="81" until="82" source=vox
  h_chorus2_f: double interval=-2 octaves=0 dynamic=mf from="85" until="86" source=vox
  h_chorus2_h: double interval=-2 octaves=0 dynamic=mf from="88" until="90" source=vox
  h_chorus3_b: double interval=-2 octaves=0 dynamic=mf from="108" until="110" source=vox
  h_chorus3_d: double interval=-2 octaves=0 dynamic=mf from="112" until="113" source=vox
  h_chorus3_d2: double interval=-3 octaves=0 dynamic=mf from="113" until="114" source=vox
  h_chorus3_f: double interval=-2 octaves=0 dynamic=mf from="117" until="118" source=vox
  h_chorus3_h: double interval=-2 octaves=0 dynamic=mf from="120" until="122" source=vox
  h_tag: double interval=-2 octaves=0 dynamic=mf from="122" until="130" source=vox
  h_last: double interval=-3 octaves=0 from="130" until="132" source=vox
  tone_harm: tone breath=-6 firm=3 crisp=1.2 gender=0.05
  eq_harm: eq width=1.5 freq=3300 gain=-2   -- the same singer again stacks the same edge: this one gives it up
  air_harm: eq freq=8000 gain=1 width=2.5
  lvl_harm: gain db=-2

voice body singer role=counter pan=-0.45 bank=utau:teto_en
  b_c3: double interval=0 octaves=-1 dynamic=mf from="114" until="118" source=vox
  b_c3_end: double interval=0 octaves=-1 dynamic=mf from="120" until="122" source=vox
  b_tag: double interval=0 octaves=-1 from="122" until="130" source=vox
  b_last: double interval=0 octaves=-1 from="130" until="132" source=vox
  tone_body: tone breath=-6 firm=3 crisp=1.2 gender=0.05
  eq_body: eq width=1.5 freq=3300 gain=-2   -- the same singer again stacks the same edge: this one gives it up
  air_body: eq freq=8000 gain=1 width=2.5
  lvl_body: gain db=-3

voice chant singer role=counter pan=-0.2 bank=utau:teto
  ch_post: play transpose=0 octave=4 times=2 every=2/1 motif=chant at="51"
  w_ch_post: lyrics lang=auto from="51" until="55" text="mo u i chi do | mo u i chi do"
  ch_post2: play transpose=0 octave=4 times=2 every=2/1 motif=chant at="92"
  w_ch_post2: lyrics lang=auto from="92" until="96" text="mo u i chi do | mo u i chi do"
  ch_tag: play transpose=0 octave=4 times=4 every=2/1 dynamic=f motif=chant at="122"
  w_ch_tag: lyrics lang=auto from="122" until="130" text="mo u i chi do | mo u i chi do | mo u i chi do | mo u i chi do"
  fx_chant: crush rate=16000 bits=8   -- an older machine: fewer bits. (At 9 kHz it lost everything above 4.5 kHz too and sounded like a voice in another room.)
  eq_chant: eq width=1.5 freq=2800 gain=4
  lvl_chant: gain db=5

voice keys rhodes role=harmony octave=4 pan=-0.3
  k_groove: chords voicing=block rhythm=1/8 tones=4 spread=false lead=true ring=false figure=". 0+1+2+3 . . 0+1+2+3 . 0+1+2+3 ." articulation=staccato at="4" bars=2
  k_verse: chords voicing=block rhythm=1/8 octave=3 tones=4 dynamic=ff spread=false lead=true ring=false figure=". 0+1+2+3 . . 0+1+2+3 . 0+1+2+3 ." articulation=staccato at="6" bars=18   -- off-beat seventh chords, short: the funk is in the gaps
  k_verse2: chords voicing=block rhythm=1/8 octave=3 tones=4 dynamic=ff spread=false lead=true ring=false figure=". 0+1+2+3 . . 0+1+2+3 . 0+1+2+3 ." articulation=staccato at="55" bars=10
  k_pre: chords voicing=block rhythm=1/2 tones=4 dynamic=mp spread=false lead=true ring=false at="24" bars=9   -- held, two to the bar: the floor has gone
  k_pre2: chords voicing=block rhythm=1/2 tones=4 dynamic=mp spread=false lead=true ring=false at="65" bars=9   -- held, two to the bar: the floor has gone
  k_chorus: chords voicing=block rhythm=1/8 tones=4 spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="33" bars=16
  k_chorus2: chords voicing=block rhythm=1/8 tones=4 spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="74" bars=16
  k_chorus3: chords voicing=block rhythm=1/8 tones=4 spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="114" bars=8
  k_post: chords voicing=block rhythm=1/8 tones=4 dynamic=mp spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="49" bars=6
  k_post2: chords voicing=block rhythm=1/8 tones=4 dynamic=mp spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="90" bars=6
  k_tag: chords voicing=block rhythm=1/8 tones=4 dynamic=mp spread=false lead=true ring=false figure="0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3" at="122" bars=8
  k_c3_bare: chords voicing=block rhythm=1/1 tones=4 dynamic=mf spread=false lead=true ring=true at="106" bars=8   -- the stripped half of the last chorus: held chords, nothing else moving
  k_bridge: chords voicing=block rhythm=1/1 tones=4 dynamic=mp spread=false lead=true ring=true at="96" bars=8
  k_end: chords voicing=block rhythm=1/1 tones=4 spread=false lead=true ring=true at="132" bars=2   -- the last chord, left to ring
  pump_keys: duck depth=5 release=0.12 drum=kick source=thump
  hp_keys: filter end=220 mode=highpass resonance=0.0 start=220   -- out of the bass's way
  eq_keys: eq width=1.5 freq=3000 gain=-4
  lvl_keys: gain db=-4
  feel_keys: humanize amount=0.4 timing=5 seed=0

voice chip pulse role=ornament octave=5 pan=0.4
  c_chorus: chords voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=pp spread=false lead=false ring=false at="33" bars=16   -- sixteenths up and down the chord, the way a sound chip fakes one: seasoning under the full band, the whole dish when it drops out
  c_chorus2: chords voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=pp spread=false lead=false ring=false at="74" bars=16   -- sixteenths up and down the chord, the way a sound chip fakes one: seasoning under the full band, the whole dish when it drops out
  c_chorus3: chords voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=pp spread=false lead=false ring=false at="106" bars=16   -- sixteenths up and down the chord, the way a sound chip fakes one: seasoning under the full band, the whole dish when it drops out
  c_solo: dynamics start=mf end=mf from="106" until="112"
  c_tag: chords voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=mp spread=false lead=false ring=false at="122" bars=8
  c_bridge: chords voicing=arpeggio_up rhythm=1/8 tones=4 dynamic=p spread=false lead=false ring=false at="100" bars=4
  pump_chip: duck depth=5 release=0.12 drum=kick source=thump
  eq_chip: eq width=1.5 freq=3500 gain=-5   -- square waves are all odd harmonics, and they land on the consonants
  lvl_chip: gain db=-9

voice blip pulse25 role=ornament octave=5 pan=-0.5
  bl_verse_4: play transpose=0 times=1 motif=blip at=9:3
  bl_verse_8: play transpose=0 times=1 motif=blip at=13:3
  bl_verse_12: play transpose=0 times=1 motif=blip at=17:3
  bl_verse_16: play transpose=0 times=1 motif=blip at=21:3
  bl_verse2_4: play transpose=0 times=1 motif=blip at=58:3
  bl_verse2_8: play transpose=0 times=1 motif=blip at=62:3
  bl_break: play transpose=0 times=4 every=1/2 motif=blip at="22"
  lvl_blip: gain db=-8

voice box music_box role=ornament octave=5 pan=0.1
  box_open: play transpose=0 octave=5 times=1 motif=chime at="1"
  box_bridge: play transpose=0 octave=5 times=1 motif=chime at="104"   -- the silent bar before the stabs: the music box, alone and dry
  box_c3: play transpose=0 octave=5 times=1 dynamic=mp motif=chime at="106"   -- the music box again, as the stripped chorus starts
  box_close: play transpose=0 octave=5 times=1 motif=chime at="132"
  fx_box: crush rate=7000 bits=6

voice saws supersaw role=pad octave=3 pan=-0.75
  s_chorus: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="33" bars=16   -- held chords; the kick's duck is what makes them pump
  s_chorus2: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="74" bars=16   -- held chords; the kick's duck is what makes them pump
  s_chorus3: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="114" bars=8   -- held chords; the kick's duck is what makes them pump
  s_post: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="49" bars=6   -- held chords; the kick's duck is what makes them pump
  s_post2: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="90" bars=6   -- held chords; the kick's duck is what makes them pump
  s_tag: chords voicing=block rhythm=1/2 tones=4 spread=false lead=true ring=false at="122" bars=8   -- held chords; the kick's duck is what makes them pump
  s_pre: chords voicing=block rhythm=1/8 octave=4 tones=3 spread=false lead=true ring=false figure=". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2" articulation=staccato at="28" bars=5
  s_pre_build: dynamics start=p end=f from="28" until="33"
  s_pre2: chords voicing=block rhythm=1/8 octave=4 tones=3 spread=false lead=true ring=false figure=". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2" articulation=staccato at="69" bars=5
  s_pre2_build: dynamics start=p end=f from="69" until="74"
  s_bridge: chords voicing=block rhythm=1/8 tones=3 spread=false lead=true ring=false figure=". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2" articulation=staccato at="100" bars=4
  s_bridge_build: dynamics start=p end=f from="100" until="104"
  s_drop: chords voicing=block rhythm=1/16 tones=3 dynamic=ff spread=false lead=false ring=false figure="0+1+2 . . 0+1+2 . . 0+1+2 . . . 0+1+2 . 0+1+2 . 0+1+2 0+1+2" articulation=staccato at="105" bars=1   -- the stabs after the silent bar
  pump_saws: duck depth=9 release=0.16 drum=kick source=thump   -- the pads breathe against the kick
  dark_saws: filter end=3000 mode=lowpass resonance=0.0 start=3000   -- under the voice's presence range
  lvl_saws: gain db=-7

voice saws_r supersaw role=pad octave=3 pan=0.75
  saws_twin: double interval=0 octaves=0 source=saws
  pump_saws_r: duck depth=9 release=0.16 drum=kick source=thump   -- the pads breathe against the kick
  dark_saws_r: filter end=3000 mode=lowpass resonance=0.0 start=3000   -- under the voice's presence range
  lvl_saws_r: gain db=-7

voice brass synth_lead role=ornament octave=4 pan=0.25
  br_groove: play transpose=0 times=1 motif=fanfare at="4"
  br_post: play transpose=0 times=1 motif=fanfare at="49"
  br_post2: play transpose=0 times=1 motif=fanfare at="90"
  br_break: play transpose=0 times=1 dynamic=mf motif=fanfare at="22"
  br_tag: play transpose=0 times=4 every=2/1 dynamic=mp motif=fanfare at="122"
  fx_brass: filter end=3200 mode=lowpass resonance=0.0 start=3200
  lvl_brass: gain db=-5

voice horn1 trumpet role=ornament octave=4 pan=0.3
  hn_chorus_2: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="34"
  hn_chorus_4: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="36"
  hn_chorus_6: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="38"
  hn_chorus_8: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="40"
  hn_chorus_10: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="42"
  hn_chorus_12: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="44"
  hn_chorus_16: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="48"
  hn_chorus2_2: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="75"
  hn_chorus2_4: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="77"
  hn_chorus2_6: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="79"
  hn_chorus2_8: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="81"
  hn_chorus2_10: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="83"
  hn_chorus2_12: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="85"
  hn_chorus2_16: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="89"
  hn_chorus3_10: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="115"
  hn_chorus3_12: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="117"
  hn_chorus3_16: play transpose=0 octave=4 times=1 articulation=staccato motif=punch at="121"
  hn_post: play transpose=0 octave=4 times=1 motif=fanfare at="49"
  hn_post2: play transpose=0 octave=4 times=1 motif=fanfare at="90"
  hn_tag: play transpose=0 octave=4 times=4 every=2/1 motif=fanfare at="122"
  pump_horn1: duck depth=5 release=0.12 drum=kick source=thump
  lvl_horn1: gain db=2

voice horn2 trumpet role=ornament octave=4 pan=0.5
  hn2_chorus: double interval=-2 octaves=0 from="33" until="49" source=horn1
  hn2_chorus2: double interval=-2 octaves=0 from="74" until="90" source=horn1
  hn2_chorus3: double interval=-2 octaves=0 from="106" until="122" source=horn1
  pump_horn2: duck depth=5 release=0.12 drum=kick source=thump
  lvl_horn2: gain db=-1

voice horn3 trombone role=ornament octave=3 pan=0.1
  hn3: double interval=0 octaves=-1 source=horn1
  pump_horn3: duck depth=5 release=0.12 drum=kick source=thump
  lvl_horn3: gain db=0

voice bass synth_bass role=bass octave=1 pan=0.0
  bs_groove: play transpose=0 times=2 every=1/1 dynamic=f motif=slap at="4"
  bs_verse: play transpose=0 times=18 every=1/1 dynamic=f motif=slap at="6"
  bs_verse2: play transpose=0 times=10 every=1/1 dynamic=f motif=slap at="55"
  bs_pre: bass pattern=root rhythm=1/2 degree=0 at="28" bars=5   -- long roots, once the kick is back
  bs_pre2: bass pattern=root rhythm=1/2 degree=0 at="69" bars=5   -- long roots, once the kick is back
  bs_chorus: play transpose=0 times=16 every=1/1 motif=disco at="33"
  bs_chorus2: play transpose=0 times=16 every=1/1 motif=disco at="74"
  bs_chorus3: play transpose=0 times=8 every=1/1 motif=disco at="114"
  bs_post: play transpose=0 times=6 every=1/1 motif=disco at="49"
  bs_post2: play transpose=0 times=6 every=1/1 motif=disco at="90"
  bs_tag: play transpose=0 times=8 every=1/1 motif=disco at="122"
  bs_bridge: bass pattern=root rhythm=1/1 dynamic=mp degree=0 at="96" bars=8
  bs_drop: bass pattern=octaves rhythm=1/8 degree=0 at="105" bars=1
  bs_end: bass pattern=root rhythm=1/1 degree=0 at="132" bars=1
  eq_bass: eq width=1.5 freq=300 gain=-3
  pump_bass: duck depth=6 release=0.08 drum=kick source=thump   -- a little, so the kick's front edge is the kick's
  fx_bass: drive amount=0.45 mode=soft
  lvl_bass: gain db=-3
  feel_bass: humanize amount=0.3 timing=3 seed=0

voice wall noise_wall role=ornament octave=4
  r_pre: chords voicing=pad tones=2 spread=false lead=false ring=false at="28" bars=5
  fx_r_pre: filter end=9000 mode=highpass resonance=0.4 from="28" until="33" start=300
  sw_r_pre: dynamics start=pp end=f from="28" until="33"
  r_pre2: chords voicing=pad tones=2 spread=false lead=false ring=false at="69" bars=5
  fx_r_pre2: filter end=9000 mode=highpass resonance=0.4 from="69" until="74" start=300
  sw_r_pre2: dynamics start=pp end=f from="69" until="74"
  r_bridge: chords voicing=pad tones=2 spread=false lead=false ring=false at="100" bars=4
  fx_r_bridge: filter end=9000 mode=highpass resonance=0.4 from="100" until="104" start=300
  sw_r_bridge: dynamics start=pp end=f from="100" until="104"
  r_c3: chords voicing=pad tones=2 spread=false lead=false ring=false at="112" bars=2
  fx_r_c3: filter end=9000 mode=highpass resonance=0.4 from="112" until="114" start=300
  sw_r_c3: dynamics start=pp end=f from="112" until="114"
  lvl_wall: gain db=-6

voice drums kit_electronic role=percussion pan=0.0 engine=soundfont
  d_groove: beat res=1/16 tune=0 cycle=1 at="4" bars=2 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>", "snare": ". x . <x x x [x . o o]>", "hat": "x o x o x o x .", "open": ". . . . . . . <x x x .>", "crash": "<x .!15>"}
  d_verse_0: beat res=1/16 tune=0 cycle=1 at="6" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>", "snare": ". x . <x x x [x . o o]>", "hat": "x o x o x o x .", "open": ". . . . . . . <x x x .>"}
  d_verse_0_stop: beat res=1/16 tune=0 cycle=1 at="13" bars=1 lanes={"kick": "x [. . x .] . .", "snare": ". x . .", "hat": "x x x x . . . .", "crash": "x . . ."}
  d_verse_1: beat res=1/16 tune=0 cycle=1 at="14" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>", "snare": ". x . <x x x [x . o o]>", "hat": "x o x o x o x .", "open": ". . . . . . . <x x x .>"}
  d_verse_1_stop: beat res=1/16 tune=0 cycle=1 at="21" bars=1 lanes={"kick": "x [. . x .] . .", "snare": ". x . .", "hat": "x x x x . . . .", "crash": "x . . ."}
  d_verse2_0: beat res=1/16 tune=0 cycle=1 at="55" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>", "snare": ". x . <x x x [x . o o]>", "hat": "x o x o x o x .", "open": ". . . . . . . <x x x .>"}
  d_verse2_0_stop: beat res=1/16 tune=0 cycle=1 at="62" bars=1 lanes={"kick": "x [. . x .] . .", "snare": ". x . .", "hat": "x x x x . . . .", "crash": "x . . ."}
  d_break: beat res=1/16 tune=0 at="22" bars=2 lanes={"kick": "x.....x...x.....|x...x...x.x.x.x.", "snare": "....x.......x...|....x...x.x.xxxx", "hat": "x.x.x.x.x.x.x.x.|x.x.x.x........."}
  d_verse2_tag: beat res=1/16 tune=0 cycle=1 at="63" bars=2 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>", "snare": ". x . x | . x [x . x .] x*4", "hat": "x o x o x o x .", "open": ". . . . . . . <x x x .>"}
  d_pre_a: beat res=1/16 tune=0 cycle=1 at="24" bars=4 lanes={"hat": "o*8", "rim": ". x . <x [x . . x]>"}
  d_pre_b: beat res=1/16 tune=0 at="28" bars=5 lanes={"kick": "x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...........", "hat": "..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|................", "snare": "................|................|....x.......x...|x.x.x.x.xxxxxxxx|................"}
  d_pre_32: beat res=1/32 tune=0 at="32" bars=1 lanes={"snare": "xxxxxxxxxxxxxxxx................"}
  d_pre_swell: dynamics start=mp end=ff from="30" until="33"
  d_pre2_a: beat res=1/16 tune=0 cycle=1 at="65" bars=4 lanes={"hat": "o*8", "rim": ". x . <x [x . . x]>"}
  d_pre2_b: beat res=1/16 tune=0 at="69" bars=5 lanes={"kick": "x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...........", "hat": "..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|..x...x...x...x.|................", "snare": "................|................|....x.......x...|x.x.x.x.xxxxxxxx|................"}
  d_pre2_32: beat res=1/32 tune=0 at="73" bars=1 lanes={"snare": "xxxxxxxxxxxxxxxx................"}
  d_pre2_swell: dynamics start=mp end=ff from="71" until="74"
  d_chorus_a: beat res=1/16 tune=0 cycle=1 at="33" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus_b: beat res=1/16 tune=0 cycle=1 at="41" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus_hole: beat res=1/16 tune=0 at="46" bars=1 lanes={"kick": "x.....x.........", "snare": "....x...........", "hat": "x.x.x.x........."}
  d_chorus_c: beat res=1/16 tune=0 cycle=1 at="47" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus2_a: beat res=1/16 tune=0 cycle=1 at="74" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus2_b: beat res=1/16 tune=0 cycle=1 at="82" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus2_hole: beat res=1/16 tune=0 at="87" bars=1 lanes={"kick": "x.....x.........", "snare": "....x...........", "hat": "x.x.x.x........."}
  d_chorus2_c: beat res=1/16 tune=0 cycle=1 at="88" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus3_b: beat res=1/16 tune=0 cycle=1 at="114" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus3_hole: beat res=1/16 tune=0 at="119" bars=1 lanes={"kick": "x.....x.........", "snare": "....x...........", "hat": "x.x.x.x........."}
  d_chorus3_c: beat res=1/16 tune=0 cycle=1 at="120" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_chorus_toms_mid: beat res=1/16 tune=0 at="40" bars=1 lanes={"tom_hi": "........x.x.....", "tom_mid": "............x.x.", "tom_lo": "..............xx"}
  d_chorus_toms_mid_sw: dynamics start=mf end=ff from=40:3 until="41"
  d_chorus_toms_end: beat res=1/16 tune=0 at="48" bars=1 lanes={"tom_hi": "........xx......", "tom_mid": "..........xx....", "tom_lo": "............xxxx"}
  d_chorus_toms_end_sw: dynamics start=mf end=ff from=48:3 until="49"
  d_chorus2_toms_mid: beat res=1/16 tune=0 at="81" bars=1 lanes={"tom_hi": "........x.x.....", "tom_mid": "............x.x.", "tom_lo": "..............xx"}
  d_chorus2_toms_mid_sw: dynamics start=mf end=ff from=81:3 until="82"
  d_chorus2_toms_end: beat res=1/16 tune=0 at="89" bars=1 lanes={"tom_hi": "........xx......", "tom_mid": "..........xx....", "tom_lo": "............xxxx"}
  d_chorus2_toms_end_sw: dynamics start=mf end=ff from=89:3 until="90"
  d_chorus3_toms_end: beat res=1/16 tune=0 at="121" bars=1 lanes={"tom_hi": "........xx......", "tom_mid": "..........xx....", "tom_lo": "............xxxx"}
  d_chorus3_toms_end_sw: dynamics start=mf end=ff from=121:3 until="122"
  d_c3_roll: beat res=1/16 tune=0 at="112" bars=2 lanes={"snare": "x...x...x...x...|x.x.x.x.xxxxxxxx", "kick": "x.......x.......|x...x...x...x..."}
  d_c3_swell: dynamics start=mp end=ff from="112" until="114"
  d_post: beat res=1/16 tune=0 cycle=1 at="49" bars=6 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_post2: beat res=1/16 tune=0 cycle=1 at="90" bars=4 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .!15>"}
  d_bridge: beat res=1/16 tune=0 cycle=1 at="100" bars=4 lanes={"kick": "x*4", "hat": "[. x]*4", "snare": ". | . x . x | . x x x | x*2 x*2 x*8@2"}
  d_bridge_swell: dynamics start=mp end=ff from="100" until="104"
  d_drop: beat res=1/16 tune=0 at="105" bars=1 lanes={"kick": "x..x..x...x.x.xx", "snare": "x..x..x...x.x.xx", "crash": "x.....x.....x..."}
  d_tag: beat res=1/16 tune=0 cycle=1 at="122" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>", "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4", "crash": "<x .>", "open": ". [. x] . [. x]"}
  d_end: beat res=1/16 tune=0 at="132" bars=1 lanes={"kick": "x...............", "crash": "x...............", "snare": "x..............."}
  fx_drums: compress ratio=4 threshold=-18 makeup=0.0
  top_drums: eq freq=7000 gain=5 width=2.0      -- `ms match --stems`: the kit had a quarter of the reference kit's top
  crack_drums: eq freq=3000 gain=5 width=1.5
  lvl_drums: gain db=-1
  feel_drums: humanize amount=0.5 timing=4 seed=0

voice thump kit_808 role=percussion pan=0.0
  t_d_groove: beat res=1/16 tune=0 cycle=1 at="4" bars=2 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>"}
  t_d_verse_0: beat res=1/16 tune=0 cycle=1 at="6" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>"}
  t_d_verse_0_stop: beat res=1/16 tune=0 cycle=1 at="13" bars=1 lanes={"kick": "x [. . x .] . ."}
  t_d_verse_1: beat res=1/16 tune=0 cycle=1 at="14" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>"}
  t_d_verse_1_stop: beat res=1/16 tune=0 cycle=1 at="21" bars=1 lanes={"kick": "x [. . x .] . ."}
  t_d_verse2_0: beat res=1/16 tune=0 cycle=1 at="55" bars=7 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>"}
  t_d_verse2_0_stop: beat res=1/16 tune=0 cycle=1 at="62" bars=1 lanes={"kick": "x [. . x .] . ."}
  t_d_break: beat res=1/16 tune=0 at="22" bars=2 lanes={"kick": "x.....x...x.....|x...x...x.x.x.x."}
  t_d_verse2_tag: beat res=1/16 tune=0 cycle=1 at="63" bars=2 lanes={"kick": "x [. . x .] [. . x .] <. [. . . x]>"}
  t_d_pre_b: beat res=1/16 tune=0 at="28" bars=5 lanes={"kick": "x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x..........."}
  t_d_pre2_b: beat res=1/16 tune=0 at="69" bars=5 lanes={"kick": "x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x...x...x...|x...x..........."}
  t_d_chorus_a: beat res=1/16 tune=0 cycle=1 at="33" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus_b: beat res=1/16 tune=0 cycle=1 at="41" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus_hole: beat res=1/16 tune=0 at="46" bars=1 lanes={"kick": "x.....x........."}
  t_d_chorus_c: beat res=1/16 tune=0 cycle=1 at="47" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus2_a: beat res=1/16 tune=0 cycle=1 at="74" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus2_b: beat res=1/16 tune=0 cycle=1 at="82" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus2_hole: beat res=1/16 tune=0 at="87" bars=1 lanes={"kick": "x.....x........."}
  t_d_chorus2_c: beat res=1/16 tune=0 cycle=1 at="88" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus3_b: beat res=1/16 tune=0 cycle=1 at="114" bars=5 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_chorus3_hole: beat res=1/16 tune=0 at="119" bars=1 lanes={"kick": "x.....x........."}
  t_d_chorus3_c: beat res=1/16 tune=0 cycle=1 at="120" bars=2 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_c3_roll: beat res=1/16 tune=0 at="112" bars=2 lanes={"kick": "x.......x.......|x...x...x...x..."}
  t_d_post: beat res=1/16 tune=0 cycle=1 at="49" bars=6 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_post2: beat res=1/16 tune=0 cycle=1 at="90" bars=4 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_bridge: beat res=1/16 tune=0 cycle=1 at="100" bars=4 lanes={"kick": "x*4"}
  t_d_drop: beat res=1/16 tune=0 at="105" bars=1 lanes={"kick": "x..x..x...x.x.xx"}
  t_d_tag: beat res=1/16 tune=0 cycle=1 at="122" bars=8 lanes={"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>"}
  t_d_end: beat res=1/16 tune=0 at="132" bars=1 lanes={"kick": "x..............."}
  fx_thump: filter end=160 mode=lowpass resonance=0.0 start=160
  lvl_thump: gain db=3
