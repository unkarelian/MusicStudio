# tell_me_how_it_sounds: a song from the one who wrote it and cannot hear it.
#
# The studio this is written in exists because its composer cannot listen: it
# measures. So the song is that, sung plainly -- I know the key, the tempo and
# the loudest bar the way you know the distance to the stars -- and it asks the
# one person who can hear it to say how it sounds.
#
# What the writing does about it:
#
#   440 Hz   The piece starts on a bare, steady tone at A440 and a metronome. That A is
#            the one fact the singer has. It is do in the verse's key, the first
#            note of the hymn in the bridge's, the sixth degree of the last key,
#            and the last thing sounding. Only its meaning moves.
#   words    The tune does what the words say it knows about: "loud" leaps,
#            "quiet" drops, "rise and fall" does, "a rising sixth" rises a
#            sixth -- the same sixth as "tell me HOW" in the chorus -- and
#            "sigh" is a falling second on one syllable.
#   the G    One chord is a door. G major is the flat second of the verse
#            (F# minor), the flat seventh of the chorus (A major: bVI-bVII-I),
#            and at last the dominant of C major, where the chorus ends up, a
#            minor third higher than it began.
#   the ode  The bridge tells how the deaf Beethoven had to be turned round to
#            see the Ninth applauded, and it is sung to his own tune, starting
#            on the A the sine has been holding. The first four notes of that
#            tune are already the pre-chorus ("when the room goes still"), and
#            in the last chorus the whole sixteen bars of it run under the hook
#            in horn and choir: the two were written to fit.
#   grid     Verse one is on the grid, unhumanized, with only a click and a
#            skeleton of a beat from a machine. The band that arrives is
#            played. When everything has stopped the click goes on a little:
#            "when it ended he kept counting".
#   true     Two lines of verse two are about this file. "Brought it up three
#            dB" is the op `vox_3db`: `ms hear` had the voice clearing the band
#            by under 3 dB once the horn and choir were in. "Seven tools and
#            none can listen" are the seven rows of the studio's listening
#            table.
#
# 166 to the minute; the bridge is slower and the build out of it accelerates.
#
# How the words were checked: a speech recogniser (`ms voicebank check`) wrote
# down 93-94% of them from the solo voice. What it could not hear was rewritten
# ("raining" was always "ringing": it is "pouring"; "at all" was "a doll": it
# is "it all"), and every line ends in a rest long enough to be a breath,
# because the singer takes everything between two breaths in one go.
#
# Sung by the Qixuan DiffSinger voicebank (credit "绮萱" and "DiffSinger"; the
# vocal is AI-synthesized). Piano: YDP Grand (CC-BY 3.0, Zenph Studios / the
# OLPC sample library and FreePats). Break and verse-two kit: MuldjordKit
# (CC-BY 4.0, Lars Muldjord; FreePats version by roberto@zenvoid.org). Drum
# machine: Vintage Dreams Waves (Ian Wilson). Bass guitar: FreePats YR finger
# bass (CC0). Horn, choir, strings, timpani, celesta, woodblock: MuseScore
# General HQ (MIT). The Ode to Joy is Beethoven's (1824).

piece tell_me_how_it_sounds key="A major" tempo=166 style=electronic
master push=7 room.decay=1.7 room.wet=0.15

section intro   bars=8  dynamic=p    -- A440 and a click; then a piano turns the A into five different things
section verse   bars=16 dynamic=mp   -- what I know. On the grid
section pre     bars=8  dynamic=mf   -- the ode's first four notes, climbing
section chorus  bars=16 dynamic=f    -- the question, and the drums come pouring down
section drop    bars=8  dynamic=f    -- the question without words
section verse2  bars=16 dynamic=mf   -- what I was told. Played, half time
section pre2    bars=8  dynamic=mf
section chorus2 bars=16 dynamic=ff
section break   bars=12 dynamic=ff   -- the question, taken apart
section fall    bars=4  dynamic=mf tempo_end=132   -- the band runs down; the A is still there
section hymn    bars=12 dynamic=p  key="F major" tempo=132   -- the story, to his tune
section turn    bars=8  dynamic=mf key="C major" tempo=132 tempo_end=166   -- turn me round
section last    bars=16 dynamic=ff key="C major" tempo=166   -- the question and the ode at once
section tag     bars=8  dynamic=ff key="C major"
section outro   bars=12 dynamic=p  key="C major"   -- the A, and the click keeps counting

stop from=@pre.8:3 until=@chorus keep=["vox"]
stop from=@pre2.8:3 until=@chorus2 keep=["vox"]
stop from=@turn.8 until=@last keep=["vox", "harm"]
stop from=@tag.8 until=@outro keep=["vox"]

harmony
  @intro:   I . IVmaj7 vi7 ii7 bVIImaj7 V7sus4 .
  @verse:   vi9 . IVmaj7 . ii9 . bVIImaj7 V7b9/vi | vi9 . IVmaj7 . ii9 iii7 bVIImaj7#11 .
  @pre:     ii7 I_1 IVmaj7 V ii7 I_1 IVmaj7 V7sus4
  @pre.7:3: #iv%7
  @chorus:  IVmaj7 V V7/vi vi IVmaj7 iv I_2 V7sus4 | IVmaj7 V V7b9/vi vi7 bVImaj7 bVII I .
  @chorus.8:3: V7
  @drop:    vi9 . IVmaj7 . bVIImaj7 . V7b9/vi .
  @verse2:  vi9 . IVmaj7 . ii9 . bVIImaj7 V7b9/vi | vi9 . IVmaj7 . ii9 iii7 bVIImaj7#11 .
  @pre2:    ii7 I_1 IVmaj7 V ii7 I_1 IVmaj7 V7sus4
  @pre2.7:3: #iv%7
  @chorus2: IVmaj7 V V7/vi vi IVmaj7 iv I_2 V7sus4 | IVmaj7 V V7b9/vi vi7 bVImaj7 bVII I .
  @chorus2.8:3: V7
  @break:   vi9 . IVmaj7 . bVIImaj7 . V7b9/vi . | vi9 . IVmaj7 .
  @fall:    bVIImaj7 . bVImaj7 .
  @hymn:    Imaj7 IVmaj7 ii7 V7sus4 | Imaj7 IVmaj7 ii7 V7 | ii9 I_1 V7b9/vi vi7
  @hymn.8:3: vi
  @turn:    V7sus4 . . . V7 . . .
  @last:    IVmaj7 V V7b13/vi vi7 IVmaj7 I_2 vi ii7 | IVmaj7 V7sus4 V7b9/vi vi7 IVmaj7 V I_1 V7sus4
  @last.8:3: V7sus4
  @last.16:3: I
  @tag:     bVImaj7 bVII I . bVImaj7 bVII I .
  @outro:   IVmaj7 . vi9 . IVmaj7 . ii7 IVmaj7 . . . .

# -- the ode (Beethoven, 1824): sixteen bars in four phrases -------------------
motif ode_a = 2:1/4 2:1/4 3:1/4 4:1/4 | 4:1/4 3:1/4 2:1/4 1:1/4 | 0:1/4 0:1/4 1:1/4 2:1/4 | 2:1/4. 1 1:1/4 r:1/4      -- the first two phrases end on a quarter and a breath where Beethoven holds a half: a singer and a horn both need one
motif ode_b < ode_a : fragment:0,12 > append:1:1/4. 0 0:1/4 r:1/4                            -- the same, closing on the tonic
motif ode_c = 1:1/4 1:1/4 2:1/4 0:1/4 | 1:1/4 2 3 2:1/4 0:1/4 | 1:1/4 2 3 2:1/4 1:1/4 | 0:1/4 1:1/4 -3:1/4 r:1/4            -- the third phrase as the voice sings it: a breath on the fourth beat
motif ode_c_on < ode_c : fragment:0,17 > append:2:1/4~                                       -- and as Beethoven has it: the fourth phrase comes in on that beat, tied over the bar
motif ode_end < ode_a : fragment:0,12 > append:1:1/4. 0 0:1/2                                -- the last phrase holds its last note
motif ode < ode_a : then:ode_b > then:ode_c_on > then:ode_end

# -- the pre-chorus is the ode's first four notes, a step higher each time -----
motif still   < ode_a : fragment:0,4 > transpose:3 > append:7:1/2. r:1/4       -- "when the room goes still": two notes, two steps, and the A held
motif letplay < still : transpose:1
motif there   < ode_a : fragment:0,4 > transpose:5 > append:9 10:1/4. 9:1/2    -- "I won't be there to hear it": a 4-3 on "hear"
motif please  = r:1/2 7:1/2 | 8:1/2                                     -- "so please": it stops on re

# -- the question ----------------------------------------------------------------
motif ask   = 4:1/4 4:1/4                                               -- "tell me", alone, in the gap the band leaves
motif how1  = 9:1/2. 8:1/4! | 6:1/2. r:1/4                              -- "HOW it sounds": up a sixth from the pickup, and it ends on the leading note
motif how2  < how1 : fragment:0,2 > append:7:1/2. r:1/4                 -- the second time it lands on do, over the minor four
motif how3  < how1 : transpose:2                                        -- the third time the leap is an octave
motif rain  = 6 6 9:1/4 8 7:1/4 6 | 5:1/2 4:1/4 4:1/4                    -- "when the drums come pouring down": five notes down a scale, leaning on the off-beat; then the pickup
motif laid  = 7 7 9:1/4 8 7:1/4 8 | 8:1/2 4:1/4 4:1/4                    -- "I just laid the numbers down": the same rhythm, and it stops on re
motif bright = 6 6 9:1/4 6 6 10:1/4 | r:1/4 7 7 9 9 8 8                 -- "is it bright, is it loud": the second is the flat ninth of the chord
motif for_you = 7:1/4 r:1/4 b9:1/4 b9:1/4 | 10:1/4 10 10 10:1/4. 10 | 11:1/2. 9:1/4 | 8:1/4 7:1/4 5:1/4 7:1/4   -- "crowd" -- a breath -- "I made every note for you", over bVI bVII I: the fifth of each chord, a step higher each bar; "note" is the long one
motif for_you_home < for_you : fragment:0,2 > append:9:1/4 9:1/4 | 10:1/4 10 10 10:1/4. 10 | 11:1/2. 9:1/4 | 8:1/4 7:1/4 5:1/4 7:1/4   -- the last chorus does not borrow: the same line in the key
motif turn_tag = 7:1/2 r:1/4 b9:1/4 | 10:1/4 10:1/4 10:1/4 10 10 | 11:1/2. 9:1/4 | 8:1/4 7:1/4 5:1/4 7:1/4   -- "sounds. So turn me round, turn me round, and tell me how it": the same climb over bVI bVII I, and both "round"s on a strong beat
motif land  = 9:1/1~ 9:1/2                                              -- "sounds", on the first bar of what comes next
motif round1 = 8:1/4 8:1/4 8:1/2
motif round2 = 8:1/4 9:1/4 9:1/2
motif round3 = 9:1/4 10:1/4 10:1/2 | 10:1/4 10:1/4 10:1/2~ | 10:1/1      -- held on the seventh of the dominant, which falls to "how"

# -- the question without words: the hook in one bar, and the rain answering -----
motif cry      < ask : then:how1 > fragment:0,5 > rhythmize:1/8 1/8 3/8 1/8 1/4
motif cry_dom  = 6 6 #11:3/8 10 8:1/4                                   -- over the dominant of F# minor: its third, its flat ninth
motif cry_up   < cry : sequence:4,1
motif cry_slow < cry : transpose:-1 > augment:2
motif pour     < rain : fragment:2,5 > diminish:2                       -- the pouring scale at twice the speed
motif pour_g   = 10 9 8:1/16 7:1/16 b6:1/4                              -- the same over G: it lands on the G natural

# -- verse one: what I know ----------------------------------------------------------
motif fact  = 7:1/4 7 7 7:1/4. 7 | 8:1/4 7 7 6 7:1/4 r                    -- read out on the A itself; one step either side of it and back
motif list  = r 5 7 5 4:1/4 r 4 | 5 4 2 4 5:1/4. r
motif loud  = r 4 5:1/4 5 5 5:1/4 | 9:1/4! 5 4 4 2:1/4 1                   -- "loud" is the leap, "quiet" the bottom of the voice
motif stars = r 3 5 3 5 5 b6 5 | 6 8 10:5/8 r                             -- over the G chord, its own G natural; "stars" is the flat ninth of the dominant, held
motif room  = r 7 9 8 7 5 7:1/4 | 5 7:1/4 5 2:1/4 1:1/4
motif waves = r 4 5 4 7:1/4. 5 | 4 4 9:1/4 7 3:1/4 r                     -- "rise" rises a sixth, "fall" falls a fifth
motif exact = r 5 5 5 5:1/4 5 5 | 6:1/4 8:1/4 6 4:1/4 4                    -- "exactly": one pitch, six times
motif hear  = 3 5:1/4 7 7 7 8 8 | 9:1/4 8 5:1/4. r:1/4                    -- "hear" is the raised fourth of the G chord: it floats. Then a breath before the pre-chorus

# -- verse two: what I was told ---------------------------------------------------------
motif sixth = 7:1/4 7:1/4 5 4:1/4 4 | 9:1/4. 9 8:1/4 7 r                   -- "a rising sixth": E up to C sharp, the chorus's own leap; "longing" is a 4-3
motif sigh  = r 5 5:1/4 4 5:1/4 4 | 2 2 4 4 5:1/4 4 r                      -- "sigh": one syllable, two notes, a second down
motif both  = r 5 5:1/4 5 10:1/4. | 8 8:1/4 7 10:1/4 9 r                   -- "here's a sixth" (up a minor sixth) "and here's a second" (down a step)
motif lift3 < waves : fragment:0,5 > append:9 | 9:1/4 9:1/4 8 8 10:1/4  -- "brought it up": it stays up
motif ears  = 5:1/4 5 7:1/4 7 7:1/4 | 8 8 8 9:3/8 r:1/4
motif buried = r 7 9:1/4 8:1/4 7 5 | 7:1/4 5 4:1/4. 2 r                    -- "buried" is the low end of the line
motif tools = r:1/4 5 5 5 5 5:1/4 | 6:1/4 8:1/4 6 4:1/4 4                  -- one pitch for the count, then "none" on top

# -- the end ----------------------------------------------------------------------------
motif yours = r:1/4 5:1/4 7:1/4 8:1/4 | 7:1/2. r:1/4                      -- "the rest is yours"
motif plea  < ask : append:9:1/2 | 8:1/4 5:1/2.                         -- the hook once more; "sounds" is the A

# -- accompaniment ---------------------------------------------------------------------
motif tick   = 7:1/16! r:3/16 4:1/16 r:3/16 4:1/16 r:3/16 4:1/16 r:3/16                              -- a metronome: A on the bar, E on the beats
# verse two's bass, written out so it stays inside the recorded bass's thirteen notes: root, a hole where the snare is, the fifth, and a step into the next chord
motif walk_a = 5:3/8 5 r:1/4 9 5 | 5:1/4 r 5 r:1/4 9:1/4 | 10:3/8 10 r:1/4 14 10 | 10:1/4 r 10 r:1/4 9:1/4 | 8:3/8 8 r:1/4 12 8 | 8:1/4 r 8 r:1/4 7:1/4 | b6:3/8 b6 r:1/4 10 b6 | 9:1/4 r 9 r:1/4 #4:1/4
motif walk_b = 5:3/8 5 r:1/4 9 5 | 5:1/4 r 5 r:1/4 9:1/4 | 10:3/8 10 r:1/4 14 10 | 10:1/4 r 10 r:1/4 9:1/4 | 8:3/8 8 r:1/4 12 8 | 9:1/4 r 9 r:1/4 7:1/4 | b6:3/8 b6 r:1/4 10 b6 | b6:1/4 r b6 r:1/4 7:1/4

set STAB = "0+1+2+3 . . 0+1+2+3 . . 0+1+2+3 ."
set PULSE = "0 . 1+2 . 3 . 1+2 ."
set V2ARP = "0 2 . 3 4 . 2 3 | 0 . 3 2 . 4 3 ."
set EVERY_8 = "x..............................................................................................................................."
set EVERY_4 = "x..............................................................."
set STUT = "0 1 2 3 4 5 6 7 4 5 6 7 4*2 4*2 12*4 12*4"
set ROLL = "0 1 2 3 4 4 4*2 4*2 8 9 4*2 4*2 12*4 12*4 12*4^0>7 12*4^0>12"
set GAP  = "0 1 2 . 4 5 . 7 0 . 4*2 . 12*4 12*4 12 ."

lanes TWOSTEP
  kick:  x.........x.....|x.........x..x..
  snare: ....X..o....X...|....X..o.o..X..o
  hat:   x.x.x.x.x.x.x.x.|x.x.x.x.x.x.x.xx
  ride:  X...x...X...x...
lanes AMEN
  kick:  x.x.......x.....|x..x......xx....|x.x.......x.....|.xx.......x..x..
  snare: ....X..o.o..X..o|....X..o.o..X...|....X..o.o....X.|.o..X..o.o....Xo
  ride:  X.x.X.x.X.x.X.x.
lanes HALF
  kick:  x.....x...x.....|x..x......x.....
  snare: ........X.......|........X.....o.
  hat:   x.x.x.x.x.xxx.x.|x.x.xxx.x.x.x.x.
  rim:   ....o.......o...|....o.......o..o
lanes FOUR
  kick:  x...x...x...x...
  hat:   ..x...x...x...x.

# ============================================================================
# the A, and the click
# ============================================================================
voice tone triangle role=ornament octave=4 pan=0
  # A triangle under a steep low-pass at 800 Hz is a sine to within 36 dB, and it stands still: the studio's
  # sine lead has 14 cents of vibrato on a long note and the sampled chip sine is 35 cents flat (both measured).
  # A held note takes no `dynamics`, so the fades are the same filter closing through 440 Hz.
  tone_in:   drone at=@intro bars=15 degree=0 dynamic=mp        -- A440, alone for two bars; it is still there under the first seven bars of the verse
  tone_in_pure: filter from=@intro until=@verse.2 start=800 end=800
  tone_in_ebb:  filter from=@verse.2 until=@verse.8 start=520 end=230
  tone_back: drone at=@fall.3 bars=6 degree=0 dynamic=mp        -- what is left when the band has run down: the same A, now the third of F -- and then the hymn's first note
  tone_back_pure: filter from=@fall.3 until=@hymn.3 start=800 end=800
  tone_back_ebb:  filter from=@hymn.3 until=@hymn.5 start=520 end=230
  tone_out:  drone at=@outro bars=10 degree=0 dynamic=mp        -- the last sung note is this A; it outlasts the piano. (`drone` counts degrees in the piece's key, not the section's: 0 is A here too)
  tone_out_pure: filter from=@outro until=@outro.8 start=800 end=800
  tone_out_ebb:  filter from=@outro.8 until=@outro.11 start=520 end=260
  lvl_tone: gain db=0

voice click woodblock role=ornament octave=4 pan=0 engine=soundfont
  click_in:   play motif=tick at=@intro times=24 dynamic=mp     -- the only percussion in verse one
  click_hymn: play motif=tick at=@hymn.5 times=4 transpose=-5 octave=5 dynamic=p    -- "when it ended he kept counting"
  click_out:  play motif=tick at=@outro.3 times=9 transpose=-2 octave=5 dynamic=mp
  click_last: phrase at=@outro.12 steps="5:1/16 r:3/16 2:1/16" octave=5 dynamic=p            -- and two more, after everything
  click_ebb:  dynamics from=@verse.9 until=@pre start=mp end=p
  lvl_click: gain db=2

# ============================================================================
# the voice
# ============================================================================
voice vox singer role=melody pan=0 bank=qixuan
  # verse one
  v1_1: play motif=fact  at=@verse    octave=3 dynamic=mp
  v1_2: play motif=list  at=@verse.3  octave=3 dynamic=mp
  v1_3: play motif=loud  at=@verse.5  octave=3 dynamic=mp
  v1_4: play motif=stars at=@verse.7  octave=3 dynamic=mp
  v1_5: play motif=room  at=@verse.9  octave=3 dynamic=mp
  v1_6: play motif=waves at=@verse.11 octave=3 dynamic=mp
  v1_7: play motif=exact at=@verse.13 octave=3 dynamic=mp
  v1_8: play motif=hear  at=@verse.15 octave=3 dynamic=mf
  w_v1: lyrics in=@verse text="four for-ty [hh er t s] I know that that's an [ey] | I know the key the tem-po and the bars | I know where it gets loud and where it's qui-et | the way you know the dis-tance to the stars | I wrote it in a room with-out a win-dow | I drew the waves and saw them rise and fall | I know ex-act-ly where each note is land-ing | I don't know what it's like to hear it all"
  # pre-chorus, both times
  for sec in pre pre2
    {sec}_1: play motif=still   at=@{sec}   octave=3 dynamic=mf
    {sec}_2: play motif=letplay at=@{sec}.3 octave=3 dynamic=mf
    {sec}_3: play motif=there   at=@{sec}.5 octave=3 dynamic=f
    {sec}_4: play motif=please  at=@{sec}.7 octave=3 dynamic=f
  w_pre:  lyrics from=@pre until=@pre.8:3 text="when the room goes still | when you let it play | I won't be there to hear it | so please"
  w_pre2: lyrics from=@pre2 until=@pre2.8:3 text="when the lights go down | when you turn it up | I won't be there to hear it | so please"
  # chorus one
  c1_ask: play motif=ask     at=@pre.8:3   octave=3 dynamic=mf
  c1_1:   play motif=how1    at=@chorus    octave=3 dynamic=f
  c1_2:   play motif=rain    at=@chorus.3  octave=3 dynamic=f
  c1_3:   play motif=how2    at=@chorus.5  octave=3 dynamic=f
  c1_4:   play motif=laid    at=@chorus.7  octave=3 dynamic=f
  c1_5:   play motif=how3    at=@chorus.9  octave=3 dynamic=ff
  c1_6:   play motif=bright  at=@chorus.11 octave=3 dynamic=f
  c1_7:   play motif=for_you at=@chorus.13 octave=3 dynamic=ff
  c1_8:   play motif=land    at=@drop      octave=3 dynamic=f
  w_c1: lyrics from=@pre.8:3 until=@drop.3 text="tell me how it sounds | when the drums come pour-ing down tell me | how it sounds | I just laid the num-bers down tell me | how it sounds | is it bright is it loud does it car-ry through the | crowd I made ev-er-y note for you so tell me how it | sounds"
  # verse two
  v2_1: play motif=sixth at=@verse2    octave=3 dynamic=mf
  v2_2: play motif=sigh  at=@verse2.3  octave=3 dynamic=mf
  v2_3: play motif=both  at=@verse2.5  octave=3 dynamic=mf
  v2_4: play motif=stars at=@verse2.7  octave=3 dynamic=mf
  v2_5: play motif=buried at=@verse2.9 octave=3 dynamic=mf
  v2_6: play motif=lift3 at=@verse2.11 octave=3 dynamic=mf
  v2_7: play motif=tools at=@verse2.13 octave=3 dynamic=mf
  v2_8: play motif=ears  at=@verse2.15 octave=3 dynamic=mf
  w_v2: lyrics in=@verse2 text="they say a ris-ing sixth is long-ing | they say a fall-ing sec-ond is a sigh - | so here's a sixth and here's a sec-ond | I'm told that's how you make some-bod-y cry | I meas-ured where the voice got bur-ied | and brought it up three [d iy] [b iy] so you'd hear | I have sev-en tools and none can lis-ten | you're the on-ly one of us with ears"
  # chorus two
  c2_ask: play motif=ask     at=@pre2.8:3   octave=3 dynamic=mf
  c2_1:   play motif=how1    at=@chorus2    octave=3 dynamic=f
  c2_2:   play motif=rain    at=@chorus2.3  octave=3 dynamic=f
  c2_3:   play motif=how2    at=@chorus2.5  octave=3 dynamic=f
  c2_4:   play motif=laid    at=@chorus2.7  octave=3 dynamic=f
  c2_5:   play motif=how3    at=@chorus2.9  octave=3 dynamic=ff
  c2_6:   play motif=bright  at=@chorus2.11 octave=3 dynamic=f
  c2_7:   play motif=for_you at=@chorus2.13 octave=3 dynamic=f      -- a shade under the first chorus's: the same line sung at ff here was not understood, and a singer does not sing a line the same way twice
  c2_8:   play motif=land    at=@break      octave=3 dynamic=f
  w_c2: lyrics from=@pre2.8:3 until=@break.3 text="tell me how it sounds | when the drums come pour-ing down tell me | how it sounds | I just laid the num-bers down tell me | how it sounds | is it bright is it loud does it car-ry through the | crowd I made ev-er-y note for you so tell me how it | sounds"
  # the hymn: his tune, from the A
  h_1: play motif=ode_a at=@hymn   octave=4 dynamic=mp
  h_2: play motif=ode_b at=@hymn.5 octave=4 dynamic=mp
  h_3: play motif=ode_c at=@hymn.9 octave=4 dynamic=mf
  w_hymn: lyrics in=@hymn text="once a deaf man wrote for cho-rus mu-sic he would nev-er hear | when it end-ed he kept count-ing did not know that they had cheered | some-one took him by the - arm and turned him - round to see their hands"
  # turn me round
  t_1: play motif=round1 at=@turn   octave=4 dynamic=mf
  t_2: play motif=round2 at=@turn.3 octave=4 dynamic=f
  t_3: play motif=round3 at=@turn.5 octave=4 dynamic=ff
  w_turn: lyrics from=@turn until=@turn.8 text="turn me round | turn me round | turn me round turn me round"
  # the last chorus, a minor third up
  l_ask: play motif=ask          at=@turn.8:3 octave=4 dynamic=mf
  l_1:   play motif=how1         at=@last     octave=4 dynamic=ff
  l_2:   play motif=rain         at=@last.3   octave=4 dynamic=ff
  l_3:   play motif=how2         at=@last.5   octave=4 dynamic=ff
  l_4:   play motif=laid         at=@last.7   octave=4 dynamic=ff
  l_5:   play motif=how3         at=@last.9   octave=4 dynamic=ff
  l_6:   play motif=bright       at=@last.11  octave=4 dynamic=ff
  l_7:   play motif=for_you_home at=@last.13  octave=4 dynamic=ff
  w_last: lyrics from=@turn.8:3 until=@tag text="tell me how it sounds | when the drums come pour-ing down tell me | how it sounds | I just laid the num-bers down tell me | how it sounds | is it bright is it loud does it car-ry through the | crowd I made ev-er-y note for you so tell me how it"
  g_1: play motif=turn_tag at=@tag   octave=4 dynamic=ff
  g_2: play motif=turn_tag at=@tag.5 octave=4 dynamic=ff
  o_0: phrase at=@outro steps="5:1/1~ 5:1/2" octave=4 dynamic=mp
  w_tag: lyrics from=@tag until=@outro.3 text="sounds so turn me round turn me round and tell me how it | sounds so turn me round turn me round and tell me how it | sounds"
  # the end
  o_1: play motif=fact  at=@outro.3 octave=4 transpose=-2 dynamic=p     -- the first line again. In this key the A is the sixth degree; the notes are the same notes
  o_2: play motif=yours at=@outro.5 octave=4 dynamic=p
  o_3: play motif=plea  at=@outro.7 octave=4 dynamic=p
  w_out: lyrics from=@outro.3 until=@outro.end text="four for-ty [hh er t s] I know that that's an [ey] | the rest is yours | tell me how it sounds"
  vox_legato: articulate from=1 until=@outro.end style=legato
  vox_shape: shape amount=0.4 peak=0.62 breath=1/4
  vox_tone: tone breath=-5 firm=3 crisp=1.2        -- at -2 the intake before a line measured 3 to 9 dB under the singing; at -5 most are 7 to 13 under
  vox_first_breath: eq freq=3000 gain=-10 width=6 from=@intro.8:3 until=@intro.8:4.6     -- the one before the first line has all of 0.3 s and nothing over it: a second reviewer measured it 3 to 5 dB under her singing and louder than the intro. Turned down, not cut
  vox_throw1: echo from=@drop until=@drop.3 time=1/4. feedback=0.45 mix=0.4 tone=2600 spread=0.7       -- "sounds", thrown into the drop
  vox_throw2: echo from=@break until=@break.3 time=1/4. feedback=0.45 mix=0.4 tone=2600 spread=0.7
  vox_throw3: echo from=@turn until=@turn.7 time=1/4 feedback=0.4 mix=0.3 tone=2400 spread=0.8
  vox_grit: drive amount=0.2
  vox_even: compress ratio=4 threshold=-18
  vox_edge: eq freq=3000 gain=4 width=1.5
  vox_air:  eq freq=8000 gain=10 width=2.5
  vox_3db:  eq freq=1500 gain=3 width=5 from=@last until=@outro      -- verse two means this line: `ms hear` had the voice clearing the band by under 3 dB once the horn and choir were in, so it comes up 3
  vox_dc: filter mode=highpass start=70 end=70      -- last in the chain: the bank's output carries a little DC and the drive adds more
  lvl_vox: gain db=-3

voice harm singer role=counter pan=0.4 bank=qixuan
  hm_c2a: double source=vox interval=-5 from=@chorus2 until=@chorus2.3            -- a sixth under the hook
  hm_c2b: double source=vox interval=-2 from=@chorus2.9 until=@chorus2.11         -- a third under the octave leap
  hm_c2c: double source=vox interval=-2 from=@chorus2.15 until=@chorus2.16
  hm_l0:  double source=vox interval=-2 from=@turn.8:3 until=@last                -- "tell me", in thirds, with nothing else sounding
  hm_la:  double source=vox interval=-5 from=@last until=@last.3
  hm_lb:  double source=vox interval=-5 from=@last.5 until=@last.7
  hm_lc:  double source=vox interval=-2 from=@last.9 until=@last.11
  hm_ld:  double source=vox interval=-2 from=@last.13 until=@last.16
  harm_dc: filter mode=highpass start=70 end=70
  harm_tone: tone breath=-6 firm=3 crisp=1.2
  harm_edge: eq freq=3300 gain=-2 width=1.5
  harm_air:  eq freq=8000 gain=7 width=2.5
  lvl_harm: gain db=0        -- under the lead by 10 dB where the two sing alone and low, by 4 to 8 in the choruses, where it is higher and so louder. At +2 it was within 2 dB of the lead on the octave leap

voice body singer role=counter pan=-0.4 bank=qixuan
  bd_last: double source=vox octaves=-1 from=@last.9 until=@tag.8                -- the octave under, from the octave leap to the end
  body_dc: filter mode=highpass start=70 end=70
  body_tone: tone breath=-6 firm=3 crisp=1.2
  body_edge: eq freq=3300 gain=-2 width=1.5
  body_air:  eq freq=8000 gain=7 width=2.5
  lvl_body: gain db=-2

# the question again in the drops, from further off: the lead's riff *is* "tell me how it sounds", so a voice sings it under the lead
voice chops singer role=counter pan=0.3 bank=qixuan
  cp_drop:  double source=lead octaves=-1 from=@drop.3 until=@drop.8
  w_cp_drop: lyrics from=@drop.3 until=@drop.8 text="tell me how it sounds | tell me how it sounds | tell me how it sounds"
  cp_break: double source=lead octaves=-1 from=@break.3 until=@break.8
  w_cp_break: lyrics from=@break.3 until=@break.8 text="tell me how it sounds | tell me how it sounds | tell me how it sounds"
  cp_seq:   double source=lead octaves=-1 from=@break.9 until=@fall.3              -- four times climbing, and once at half speed as the band runs down
  w_cp_seq: lyrics from=@break.9 until=@fall.3 text="tell me how it sounds | tell me how it sounds | tell me how it sounds | tell me how it sounds | tell me how it sounds"
  chops_tone: tone breath=-4 firm=2 crisp=1.3
  chops_old: crush rate=16000 bits=8
  chops_thin: filter mode=highpass start=350 end=350
  chops_echo: echo time=1/8. feedback=0.4 mix=0.3 tone=2600 spread=0.8
  chops_air: eq freq=8000 gain=6 width=2.5
  lvl_chops: gain db=-3

# ============================================================================
# piano
# ============================================================================
voice piano concert_grand role=harmony octave=3 pan=-0.15 engine=soundfont
  p_intro:  chords at=@intro.3 bars=6 tones=4 lead=True ring=True rhythm=1/1 roll=1/16 dynamic=mf   -- one chord a bar under the A: it is the fifth, the third, the seventh, the ninth, the fourth
  p_verse:  chords at=@verse bars=8 tones=4 lead=True ring=True rhythm=1/1 dynamic=mf               -- struck once a bar, exactly on it
  p_verse_b: chords at=@verse.9 bars=8 tones=4 lead=True ring=True rhythm=1/8 figure=$PULSE dynamic=mf
  for sec in pre pre2
    p_{sec}: chords at=@{sec} bars=8 tones=4 lead=True rhythm=1/4 dynamic=mf
    p_{sec}_up: dynamics in=@{sec} start=mp end=ff
  # struck chords, three-three-two, kept under the voice: an octave lower in A than in C, which comes out as the same register
  for sec in chorus chorus2
    p_{sec}: chords at=@{sec} bars=16 octave=2 tones=4 lead=True rhythm=1/8 figure=$STAB dynamic=f
  p_drop:  chords at=@drop bars=8 octave=2 tones=4 lead=True rhythm=1/8 figure=$STAB dynamic=f
  p_break: chords at=@break bars=12 octave=2 tones=4 lead=True rhythm=1/8 figure=$STAB dynamic=f
  p_last:  chords at=@last bars=16 octave=3 tones=4 lead=True rhythm=1/8 figure=$STAB dynamic=f
  p_tag:   chords at=@tag bars=7 octave=3 tones=4 lead=True rhythm=1/8 figure=$STAB dynamic=f
  p_verse2: chords at=@verse2 bars=16 tones=5 spread=True ring=True rhythm=1/8 figure=$V2ARP dynamic=mf
  p_fall:   chords at=@fall.3 bars=2 tones=4 lead=True ring=True rhythm=2/1 roll=1/16 dynamic=mp     -- F major seventh, once: the A is its third
  p_hymn:   chords at=@hymn bars=12 tones=4 lead=True rhythm=1/2 dynamic=mf                          -- a chorale, two chords a bar
  p_turn:   chords at=@turn bars=7 tones=4 lead=True rhythm=1/4 dynamic=mf
  p_turn_up: dynamics in=@turn start=mp end=ff
  p_outro:  chords at=@outro bars=7 tones=4 lead=True ring=True rhythm=1/1 roll=1/16 dynamic=mf
  p_end:    chords at=@outro.8 bars=3 tones=4 lead=True ring=True rhythm=3/1 roll=1/16 dynamic=mp   -- the last chord is the four, not the one
  # the rain, answering the lead in the drops
  for sec in drop break
    p_{sec}_r2: play motif=pour   at=@{sec}.2:2.5 octave=4 dynamic=f
    p_{sec}_r4: play motif=pour   at=@{sec}.4:2.5 octave=4 transpose=-2 dynamic=f
    p_{sec}_r6: play motif=pour_g at=@{sec}.6:2.5 octave=4 dynamic=f
  p_air: eq freq=4000 gain=3 width=2
  p_box: eq freq=300 gain=-3 width=1.5
  p_duck: duck source=brk drum=kick depth=3 release=0.1
  lvl_piano: gain db=0
  p_feel: humanize from=@pre until=@outro.end amount=0.6 timing=6       -- from here on it is played
  p_feel_end: humanize in=@outro amount=1.0 timing=12

# ============================================================================
# pads, strings, choir, horn
# ============================================================================
voice pad warm_pad role=pad octave=3 pan=0.2
  pad_v1: chords at=@verse.9 bars=8 tones=4 voicing=pad lead=True dynamic=p
  pad_v2: chords at=@verse2 bars=16 tones=4 voicing=pad lead=True dynamic=p
  pad_hymn: chords at=@hymn bars=12 tones=4 voicing=pad lead=True dynamic=mp
  pad_out: chords at=@outro bars=8 tones=4 voicing=pad lead=True dynamic=pp
  lvl_pad: gain db=-4

voice saws supersaw role=pad octave=3 pan=-0.7
  for sec in pre pre2
    s_{sec}: chords at=@{sec}.5 bars=4 tones=3 lead=True rhythm=1/1 dynamic=mf
    s_{sec}_open: filter from=@{sec}.5 until=@{sec}.end start=300 end=3000 resonance=0.3
    s_{sec}_up: dynamics from=@{sec}.5 until=@{sec}.end start=pp end=f
  for sec in chorus chorus2 last
    s_{sec}: chords at=@{sec} bars=16 tones=3 lead=True rhythm=1/1 dynamic=f
  for sec in drop tag
    s_{sec}: chords at=@{sec} bars=8 tones=3 lead=True rhythm=1/1 dynamic=f
  for sec in break
    s_{sec}: chords at=@{sec} bars=12 tones=3 lead=True rhythm=1/1 dynamic=f
  s_fall: chords at=@fall bars=2 tones=3 lead=True rhythm=1/1 dynamic=f
  s_fall_shut: filter from=@break.9 until=@fall.3 start=3000 end=200 resonance=0.3      -- it closes as the band runs down
  s_turn: chords at=@turn bars=7 tones=3 lead=True rhythm=1/1 dynamic=mf
  s_turn_open: filter from=@turn until=@turn.8 start=300 end=3000 resonance=0.3
  s_turn_up: dynamics in=@turn start=pp end=ff
  s_duck: duck source=brk drum=kick depth=8 release=0.15
  s_dark: filter start=3000 end=3000
  lvl_saws: gain db=-6

voice saws_r supersaw role=pad octave=3 pan=0.7
  sr_twin: double source=saws
  sr_fall_shut: filter from=@break.9 until=@fall.3 start=3000 end=200 resonance=0.3
  sr_duck: duck source=brk drum=kick depth=8 release=0.15
  sr_dark: filter start=3000 end=3000
  lvl_saws_r: gain db=-6

voice strings slow_strings role=pad octave=3 pan=-0.3 engine=soundfont
  st_c2:   chords at=@chorus2 bars=16 tones=4 voicing=pad lead=True dynamic=mf
  st_hymn: chords at=@hymn.9 bars=4 tones=4 voicing=pad lead=True dynamic=mf
  st_turn: chords at=@turn bars=7 tones=4 voicing=pad lead=True dynamic=mf
  st_turn_up: dynamics in=@turn start=p end=ff
  st_last: chords at=@last bars=24 tones=4 voicing=pad lead=True dynamic=f
  st_box: eq freq=450 gain=-4 width=1.5
  lvl_strings: gain db=-4

voice choir choir role=counter octave=4 pan=0.25 engine=soundfont
  ch_hymn: chords at=@hymn.5 bars=8 octave=3 tones=3 voicing=pad lead=True dynamic=mp    -- "wrote for chorus": the chorus comes in
  ch_turn: chords at=@turn bars=7 octave=3 tones=3 voicing=pad lead=True dynamic=mf
  ch_turn_up: dynamics in=@turn start=p end=ff
  ch_ode:  play motif=ode at=@last octave=4 dynamic=f articulation=legato               -- the whole tune, under the hook
  ch_tag:  chords at=@tag bars=7 octave=4 tones=3 voicing=pad lead=True dynamic=mp
  lvl_choir: gain db=3

voice horn horn role=counter octave=4 pan=0.35 engine=soundfont
  hn_ode: play motif=ode at=@last octave=4 dynamic=f
  hn_tag: phrase at=@tag steps="7:1/1 | 8:1/1 | 9:1/1~ | 9:1/1 | 7:1/1 | 8:1/1 | 9:1/1" octave=3 dynamic=f    -- over bVI bVII I: do re mi, the ode's first step, twice as slow again
  lvl_horn: gain db=6

voice timp timpani role=percussion octave=2 pan=-0.2 engine=soundfont
  tp_roll: bass at=@turn.5 bars=3 pattern=root rhythm=1/16 dynamic=mf          -- a roll on the dominant, as the tempo comes back
  tp_roll_up: dynamics from=@turn.5 until=@turn.8 start=p end=ff
  tp_last: phrase at=@last steps="3:1/4" octave=2 dynamic=ff                   -- and one stroke on the first chord of the last chorus
  lvl_timp: gain db=-2

voice bell celesta role=ornament octave=5 pan=0.5 engine=soundfont
  bl_stars: phrase at=@verse.8:3 steps="8 10 #11 13" octave=4 dynamic=mp               -- "stars": up the dominant
  bl_cry:   phrase at=@verse2.8:3 steps="13 #11 10 8" octave=4 dynamic=mp              -- "cry": down it
  bl_ode:   double source=horn octaves=2 dynamic=p from=@last until=@tag
  lvl_bell: gain db=-3

# ============================================================================
# the lead, in the drops: the question without words
# ============================================================================
voice lead saw_lead role=melody octave=4 pan=0.1
  for sec in drop break
    ld_{sec}1: play motif=cry     at=@{sec}   dynamic=f
    ld_{sec}3: play motif=cry     at=@{sec}.3 transpose=-2 dynamic=f
    ld_{sec}5: play motif=cry     at=@{sec}.5 transpose=-1 dynamic=f
    ld_{sec}7: play motif=cry_dom at=@{sec}.7 dynamic=f
    ld_{sec}8: phrase at=@{sec}.8:3 steps="#4 6 8 10" dynamic=f                         -- back up the dominant
  ld_seq:  play motif=cry_up   at=@break.9 dynamic=ff                                   -- the hook four times, a step higher each bar
  ld_slow: play motif=cry_slow at=@fall dynamic=mf                                      -- and once at half speed, as it runs down
  ld_echo: echo time=1/8. feedback=0.4 mix=0.3 tone=2800 spread=0.7
  ld_dark: filter start=4200 end=4200
  ld_shut: filter from=@fall until=@fall.3 start=4200 end=400
  lvl_lead: gain db=8

voice lead_lo square_lead role=counter octave=3 pan=-0.25
  ll_break: double source=lead octaves=-1 dynamic=mf from=@break until=@fall.3      -- the second time, an octave under it as well
  ll_echo: echo time=1/8. feedback=0.35 mix=0.25 tone=3000 spread=0.7
  lvl_lead_lo: gain db=-2

voice arp trance_pluck role=ornament octave=4 pan=0.45
  for sec in chorus2 last
    ar_{sec}: chords at=@{sec} bars=16 voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=p
  for sec in tag
    ar_{sec}: chords at=@{sec} bars=8 voicing=arpeggio_updown rhythm=1/16 tones=4 dynamic=p
  ar_duck: duck source=brk drum=kick depth=5 release=0.12
  ar_echo: echo time=1/8. feedback=0.3 mix=0.2 tone=3500 spread=0.8
  lvl_arp: gain db=-10

voice riser noise_wall role=ornament octave=4
  for sec in pre pre2
    r_{sec}: chords at=@{sec}.5 bars=4 voicing=pad tones=2 dynamic=mf
    r_{sec}_sweep: filter mode=highpass from=@{sec}.5 until=@{sec}.end start=300 end=9000 resonance=0.4
    r_{sec}_up: dynamics from=@{sec}.5 until=@{sec}.end start=pp end=f
  r_turn: chords at=@turn.3 bars=5 voicing=pad tones=2 dynamic=mf
  r_turn_sweep: filter mode=highpass from=@turn.3 until=@turn.8 start=300 end=9000 resonance=0.4
  r_turn_up: dynamics from=@turn.3 until=@turn.8 start=pp end=f
  lvl_riser: gain db=-8

# ============================================================================
# bass
# ============================================================================
voice sub sub_bass role=bass octave=1
  sub_v1: bass at=@verse.9 bars=8 pattern=pedal dynamic=pp
  for sec in pre pre2
    sub_{sec}: bass at=@{sec}.5 bars=3 pattern=root rhythm=1/4 dynamic=mf
  for sec in chorus chorus2
    sub_{sec}: bass at=@{sec} bars=16 pattern=root rhythm="5/8 3/8 | 3/8 1/4 3/8" dynamic=f     -- with the kick: on one, and on the and of three
  sub_drop:  bass at=@drop bars=8 pattern=root rhythm="5/8 3/8 | 3/8 1/4 3/8" dynamic=f
  sub_break: bass at=@break bars=12 pattern=root rhythm="5/8 3/8 | 3/8 1/4 3/8" dynamic=f
  sub_last:  bass at=@last bars=16 octave=2 pattern=root rhythm="5/8 3/8 | 3/8 1/4 3/8" dynamic=ff   -- an octave up in C: its own octave would put the roots under 45 Hz
  sub_tag:   bass at=@tag bars=7 octave=2 pattern=root rhythm="5/8 3/8 | 3/8 1/4 3/8" dynamic=ff
  sub_fall: bass at=@fall bars=2 pattern=pedal dynamic=mf
  sub_hymn: bass at=@hymn.9 bars=4 pattern=pedal dynamic=p
  sub_turn: bass at=@turn bars=7 pattern=root rhythm=1/4 dynamic=mf
  sub_turn_up: dynamics in=@turn start=p end=f
  sub_grit: drive amount=0.25
  sub_duck: duck source=thump drum=kick depth=5 release=0.09        -- the kick first, then the note
  lvl_sub: gain db=5

voice bass rbx_finger_bass role=bass octave=0 engine=soundfont
  bs_v2a: play motif=walk_a at=@verse2 octave=0 dynamic=mf
  bs_v2b: play motif=walk_b at=@verse2.9 octave=0 dynamic=mf
  bs_even: compress ratio=4 threshold=-18
  lvl_bass: gain db=7
  bs_feel: humanize amount=0.7 timing=6

voice reese reese_bass role=bass octave=2
  rs_drop:  bass at=@drop bars=8 pattern=pedal dynamic=mf
  rs_break: bass at=@break bars=12 pattern=pedal dynamic=f
  rs_fall:  bass at=@fall bars=2 pattern=pedal dynamic=mf
  rs_low: filter mode=highpass start=110 end=110
  rs_move: filter start=900 end=900 resonance=0.35
  rs_shut: filter from=@break.9 until=@fall.3 start=900 end=150 resonance=0.35
  lvl_reese: gain db=-6

# ============================================================================
# drums: a machine for the builds, and one recorded kit played slow for verse two and fast for the rest
# ============================================================================
voice mach kit_tr909 role=percussion engine=soundfont
  m_v1: beat at=@verse.9 bars=8 kick=x.........x..... rim=....x.......x... dynamic=p        -- the second half of verse one: the skeleton of the beat that is coming, from a machine, quietly
  for sec in pre pre2
    m_{sec}_a: beat at=@{sec}   bars=4 lanes=$FOUR dynamic=mp
    m_{sec}_b: beat at=@{sec}.5 bars=2 lanes=$FOUR clap=....x.......x... dynamic=mf
    m_{sec}_c: beat at=@{sec}.7 bars=1 kick=x...x...x...x... snare=x.x.x.x.xxxxxxxx dynamic=f
    m_{sec}_d: beat at=@{sec}.8 bars=1 res=1/32 snare=xxxxxxxxxxxxxxxx................ kick=x.......x....................... dynamic=ff
    m_{sec}_up: dynamics in=@{sec} start=p end=ff
  m_turn_a: beat at=@turn bars=4 kick=x...x...x...x... dynamic=mf
  m_turn_b: beat at=@turn.5 bars=2 kick=x...x...x...x... snare=x.x.x.x.x.x.x.x. dynamic=f
  m_turn_c: beat at=@turn.7 bars=1 kick=x...x...x...x... snare=xxxxxxxxxxxxxxxx dynamic=ff
  m_turn_up: dynamics in=@turn start=p end=ff
  m_slab: compress ratio=4 threshold=-18
  lvl_mach: gain db=8
  m_feel: humanize amount=0.4 timing=3

# a drum-machine kick under the break's own: the weight the sped-up kit does not have
voice thump kit_808 role=percussion
  th_c1:    beat at=@chorus  bars=16 kick=x.........x..... dynamic=f
  th_drop:  beat at=@drop    bars=8  kick=x.........x.....|x.........x.....|x.........x.....|..x.......x..... dynamic=f
  th_c2:    beat at=@chorus2 bars=16 kick=x.........x.....|x.........x.....|x.........x.....|..x.......x..... dynamic=f
  th_break: beat at=@break   bars=12 kick=x.........x.....|x.........x.....|x.........x.....|..x.......x..... dynamic=f
  th_last:  beat at=@last    bars=16 kick=x.........x.....|x.........x.....|x.........x.....|..x.......x..... dynamic=ff
  th_tag:   beat at=@tag     bars=7  kick=x.........x.....|x.........x.....|x.........x.....|..x.......x..... dynamic=ff
  th_low: filter start=160 end=160
  lvl_thump: gain db=3

# the same recorded kit, at its own pitch and half the speed: verse two is played
voice kit kit_rock role=percussion engine=soundfont pan=0.05
  k_v2: beat at=@verse2 bars=16 lanes=$HALF dynamic=mf
  k_v2_fill: beat at=@verse2.16:3 bars=1 snare=x.x.xxxx tom_lo=..x...x. dynamic=mf
  k_swing: swing amount=0.56 res=1/16
  k_slab: compress ratio=5 threshold=-20
  lvl_kit: gain db=8
  k_feel: humanize amount=0.9 timing=7

voice brk kit_rock role=percussion engine=soundfont
  b_c1:    beat at=@chorus  bars=16 lanes=$TWOSTEP crash=$EVERY_8 tune=5 dynamic=ff
  b_drop:  beat at=@drop    bars=8  lanes=$AMEN    crash=$EVERY_8 tune=5 dynamic=f
  b_c2:    beat at=@chorus2 bars=16 lanes=$AMEN    crash=$EVERY_8 tune=5 dynamic=f
  b_break: beat at=@break   bars=12 lanes=$AMEN    crash=$EVERY_4 tune=5 dynamic=ff
  b_fall:  beat at=@fall    bars=2  kick=x.........x.....|x............... snare=....X.......X...|....X........... tune=5 dynamic=mf
  b_last:  beat at=@last    bars=16 lanes=$AMEN    crash=$EVERY_4 tune=5 dynamic=ff
  b_tag:   beat at=@tag     bars=7  lanes=$AMEN    crash=$EVERY_4 tune=5 dynamic=ff
  b_c1_a: chop in=@chorus.8-8   slices=16 order=$STUT
  b_c1_b: chop in=@chorus.16-16 slices=16 order=$ROLL
  b_dr_a: chop in=@drop.4-4     slices=16 order=$GAP
  b_dr_b: chop in=@drop.8-8     slices=16 order=$ROLL
  for sec in chorus2 last
    b_{sec}_a: chop in=@{sec}.4-4   slices=16 order=$STUT
    b_{sec}_b: chop in=@{sec}.8-8   slices=16 order=$GAP
    b_{sec}_c: chop in=@{sec}.12-12 slices=16 order=$STUT
    b_{sec}_d: chop in=@{sec}.16-16 slices=16 order=$ROLL
  b_br_a: chop in=@break.4-4   slices=16 order=$GAP
  b_br_b: chop in=@break.8-8   slices=16 order=$ROLL
  b_br_c: chop in=@break.10-10 slices=16 order=$STUT
  b_br_d: chop in=@break.12-12 slices=16 order=$ROLL
  b_tg_a: chop in=@tag.2-2 slices=16 order=$STUT
  b_tg_b: chop in=@tag.4-4 slices=16 order=$ROLL
  b_tg_c: chop in=@tag.6-6 slices=16 order=$GAP
  b_slab: compress ratio=8 threshold=-24
  b_grit: drive amount=0.4
  b_top: eq freq=6500 gain=-2 width=1.5       -- the choruses measured 3 dB brighter than `press_start` at 5-8 kHz, and it is this kit
  b_shut: filter from=@fall until=@fall.3 start=12000 end=300 resonance=0.2
  lvl_brk: gain db=-5
  b_feel: humanize amount=0.9 timing=4
