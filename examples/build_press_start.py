"""Builds `press_start`: minor-key funk verses that lift into a major chorus.

Written against a listening model's description of a reference track (Gemini,
given the audio and asked for its musical language, not its content): about
170 beats a minute; verses in the relative minor over seventh chords with a
dominant borrowed from the harmonic minor; a pre-chorus that drops the bass,
builds, and holds one note over an extra ninth bar; choruses in the relative
major that *start on the four chord* and take eight bars to find the tonic;
fast syllabic verses against long chorus notes; the whole band cut dead for a
dry vocal pickup; chiptune arpeggios beside an electric piano and side-chained
saws; and a five-note chant in another voice and another language that comes
back underneath the last chorus as a second tune. None of its notes or words
are here. The song is about a game left in a drawer, waiting to be continued.

    chime     a crushed music box, alone
    groove    two bars of the band, in B minor
    verse     16 bars: two bouncing lines, then two of patter, twice; each
              half ends on a stab and a hole. Then a two-bar break
    pre       9 bars. No bass, no snare; the kick comes in at bar 5; the voice
              holds the fifth of the key for the last three and the band is
              cut for the two words that lead in
    chorus    16 bars in D major: IVmaj7 V7 iii7 vi7 | ii7 V7 Imaj7 V7/IV, then
              the same road with the dominant of the relative minor in it.
              The band stops for half a bar before the last line
    post      6 bars: a riff, then the chant ("mo u i chi do": once more)
    verse 2   8 bars and a two-bar tag
    pre, chorus, post again
    bridge    half-speed harmony, no drums, then a build; one bar of the chant
              alone and dry; one bar of stabs
    chorus 3  six bars with only the chips under the voice, a two-bar roll,
              then all of it
    tag       the chant under long notes: two tunes at once
    chorale   three voices, dry: "continue"

The lead and its harmonies are a neural singer (``bank="qixuan"``, a DiffSinger
voicebank: see SINGERS.md -- a published render must credit "绮萱" (Qixuan) and
"DiffSinger" and say the vocal is AI-synthesized). The chant is the studio's
own formant singer on purpose: an older kind of synthetic voice beside a newer
one. Without the voicebank the lead falls back to that singer too.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from musicstudio import Studio  # noqa: E402
from musicstudio.lint import report  # noqa: E402

PROJECT = Path(__file__).resolve().parents[1] / "gallery"
P = "press_start"

# Syllables per line: 8, 8, 14, 13 -- the motifs below have exactly that many notes.
VERSE_1 = ["left me in a drawer in Ju-ly",
           "dust is fall-ing soft as a lie",
           "I kept each lit-tle thing you ev-er let me hold on to",
           "six-teen bits of mem-o-ry and all of them are you",
           "pix-el heart with one life to go",
           "wait-ing where you saved long a-go",
           "count the sec-onds in the dark be-hind the gray plas-tic door",
           "if you press the but-ton I will be here like be-fore"]
VERSE_2 = ["bat-ter-y is red but I'm fine",
           "hum-ming through the night just to shine",
           "I re-mem-ber how you laughed when we beat the fi-nal boss",
           "now the cred-its nev-er roll I froze them just for us",
           "just for us just for us"]
PRE = ["do you still re-mem-ber", "how the sto-ry goes on",
       "I have been here wait-ing", "for you", "come on"]
CHORUS = ["press start I'm a-wake a-gain",
          "ten nine count me down my friend",
          "all the lives I nev-er spent",
          "I was sav-ing them for you",
          "press start I'm a-live to-night",
          "one more coin and one more fight",
          "all the end-ings that we missed",
          "we can play them all a-new"]
BRIDGE = ["if the screen goes dark to-night", "I will keep your place for you"]
TAG = ["press start", "I'm here", "press start", "a-gain"]
CHANT = "mo u i chi do"

SECTIONS = [("chime", 3, "p", None), ("groove", 2, "f", "A minor"),
            ("verse", 18, "mf", "A minor"), ("pre", 9, "mp", None),
            ("chorus", 16, "ff", None), ("post", 6, "f", None),
            ("verse2", 10, "mf", "A minor"), ("pre2", 9, "mp", None),
            ("chorus2", 16, "ff", None), ("post2", 6, "f", None),
            ("bridge", 10, "mp", None), ("chorus3", 16, "ff", None),
            ("tag", 8, "ff", None), ("chorale", 4, "mf", None)]
START, _bar = {}, 1
for _name, _bars, _, _ in SECTIONS:
    START[_name] = _bar
    _bar += _bars
LENGTH = {name: bars for name, bars, _, _ in SECTIONS}


def at(section: str, bar: int = 1, beat: float | None = None) -> str:
    """A position by section: ``at('chorus', 14, 3)`` is beat 3 of its 14th bar."""
    n = START[section] + bar - 1
    return f"{n}:{beat:g}" if beat else str(n)


def span(section: str, first: int = 1, last: int | None = None) -> dict:
    """Bars ``first..last`` of a section (inclusive), as from/until."""
    last = LENGTH[section] if last is None else last
    return {"from": at(section, first), "until": str(START[section] + last)}


VERSE_8 = ["i7", "iv7", "VII7", ("IIImaj7", "V7"), "i7", "iv7", ("ii%7", "V7"), "i7"]
# The second time down the road it turns: the dominant of the relative minor
# in bar 11, and in bar 14 the half-diminished two (the minor four with the
# tune's held note in the bass), borrowed, where the band stops -- the ache
# before the only line that lands.
ROAD = ["IVmaj7", "V7", "iii7", "vi7", "ii7", "V7", "Imaj7", "V7/IV",
        "IVmaj7", "V7", "V7/vi", "vi7", "ii7", "ii%7", "Imaj7", "Imaj7"]
PRE_CHORDS = ["IVmaj7", "V7", "iii7", "vi7", "ii7", "iv", "V7sus4", "V7", "V7"]
CHORDS = {
    "chime": ["Imaj7"] * 3,
    "groove": ["i7", "V7"],
    "verse": VERSE_8 * 2 + ["i7", "V7"],
    "pre": PRE_CHORDS, "pre2": PRE_CHORDS,
    "chorus": ROAD, "chorus2": ROAD, "chorus3": ROAD,
    "post": ["IVmaj7", "V7"] * 3, "post2": ["IVmaj7", "V7"] * 3,
    "verse2": VERSE_8 + ["iv7", "V7"],
    "bridge": ["IVmaj7", "IVmaj7", "V7", "V7", "iii7", "vi7", "ii7", "V7", "V7", "V7"],
    "tag": ["IVmaj7", "V7"] * 4,
    "chorale": ["Imaj7"] * 4,
}


def build() -> Studio:
    s = Studio(PROJECT)
    s.create(P, key="C major", tempo=170, style="electronic", overwrite=True)
    for name, bars, dyn, key in SECTIONS:
        s.add_section(P, name, bars=bars, dynamic=dyn, key=key)
    harmony = []
    for name, _, _, _ in SECTIONS:
        for i, chord in enumerate(CHORDS[name]):
            if isinstance(chord, tuple):                 # two chords in the bar
                harmony += [[at(name, i + 1), chord[0]], [at(name, i + 1, 3), chord[1]]]
            else:
                harmony.append([at(name, i + 1), chord])
    s.set_harmony(P, harmony)

    # -- tunes ----------------------------------------------------------------
    # Verse, in B minor. Two bars a line; the note counts are the syllable counts.
    s.add_motif(P, "bounce", "r 4 4 2 4:1/4 2 1 | 2:3/8 0:3/8 r:1/4",
                note="eight notes, entering off the beat and leaning on the threes")
    s.add_motif(P, "bounce_up", "r 4 4 6 7:1/4 6 4 | 6:3/8 4:3/8 r:1/4",
                note="the answer, a third higher")
    s.add_motif(P, "patter", "2 2 2 4 2 2 1 2 | 4 4 4 6 4 2:1/4 r",
                note="fourteen notes, almost all on two pitches: the words do the work")
    s.add_motif(P, "patter_home", "0 0 0 2 0 0 #6 0 | 2 4 2 1 0:1/4 r:1/4.",
                note="thirteen notes through the raised seventh, landing on the stab")
    s.add_motif(P, "tag", "0:1/4 2:1/4 3:1/2 | 4:1/4 4:1/4 #6:1/2",
                note="verse two's extra two bars: it ends on the leading note, unresolved")
    # Pre-chorus, in D: longer notes, stepping up to the fifth and staying there.
    s.add_motif(P, "step_1", "0:1/4 1:1/4 2:1/2 | 2:1/4 2:1/4 1:1/2")
    s.add_motif(P, "step_2", "1:1/4 2:1/4 4:1/2 | 4:1/4 4:1/4 2:1/2",
                note="the same shape a step up, bent to stay on the chords")
    s.add_motif(P, "step_3", "2:1/4 3:1/4 4:1/2 | 4:1/4 b5:1/4 7:1/2",
                note="the same climb, and this time it keeps going -- through the "
                     "flat sixth of the borrowed minor four -- to the tonic")
    s.add_motif(P, "belt", "3:1/4 4:1/2.~ | 4:1/1~ | 4:1/4 r:1/2 2 4",
                note="one note for nine beats over the dominant, a hole, and the "
                     "two-note pickup that the band is cut for")
    # Chorus, in D. Seven notes a line: two long, a push, and a held last note.
    s.add_motif(P, "call", "4:3/8 7:1/4 r 5:1/4 | 4 6:1/4 4 5:1/2",
                note="up a fourth to the tonic in two notes, a gap for the words to "
                     "land in, then it settles")
    s.add_motif(P, "answer", "4:3/8 6:3/8 4:1/4 | 2 4:1/4 6 7:1/2",
                note="the same rhythm; where the call fell, this one rises")
    s.add_motif(P, "climb", "3:3/8 5:3/8 7:1/4 | 6 7:1/4 8 8:1/2",
                note="to the top of the tune, held through the half bar the band stops for")
    s.derive_motif(P, "climb_ache", "climb", ["fragment:0,3", "append:b5 7:1/4 8 8:1/2"],
                   note="the climb over the minor four: one flat on the way up")
    s.add_motif(P, "give", "8 7 7 6 4:1/4 2:1/4 | 7:1/1",
                note="the words go by in one bar so the last one can have the next "
                     "to itself: a whole bar on the tonic, at the top")
    s.add_motif(P, "sting", "#4:3/8 6:3/8 #4:1/4 | 5 7:1/4 5 7:1/2",
                note="the call's rhythm on the dominant of the relative minor: one "
                     "note from outside the key, resolving up")
    s.add_motif(P, "land", "4 6 7 6 4:1/4 8:1/4 | 7:1/1",
                note="the same trick to end on: six words in a bar, one held for a bar")
    s.add_motif(P, "chant", "4:1/4 4:1/4 5:1/4 7:1/4 | 5:1/1",
                note="five notes of the pentatonic scale, for the second voice")
    s.add_motif(P, "float_1", "r:1/2 4:1/4 4:1/4 | 7:1/2. 5:1/4 | 4:1/2 6:1/2 | 4:1/1")
    s.add_motif(P, "float_2", "r:1/2 4:1/4 4:1/4 | 7:1/2. 5:1/4 | 8:1/2 7:1/2 | 8:1/1")
    # Band figures.
    s.add_motif(P, "slap", "0:1/8 r:1/8 4:1/8 r:1/8 r:1/8 0:1/8 r:1/8 2:1/8", anchor="chord",
                note="the verse bass: root, its octave, root, fifth, with air between. "
                     "It used to end every bar on a run of sixteenths through the "
                     "seventh, which driven hard and doubled by the kick was a drum "
                     "fill in every bar -- the first thing heard, and all that was")
    s.add_motif(P, "disco", "0:1/8 4:1/8 r:1/16 0:1/16 4:1/8 0:1/8 4:1/8 2:1/16 3:1/16 4:1/8",
                anchor="chord",
                note="the chorus bass: octaves with a hole in them and a run up to "
                     "the next bar, where it used to be straight eighths")
    s.add_motif(P, "punch", "r:1/2 r:1/8 2:1/8 3:1/8 4:1/8", anchor="chord",
                note="horns: three chord tones up into the next line, in the gap "
                     "the voice leaves at the end of each one")
    s.add_motif(P, "blip", "0:1/16 1:1/16 2:1/16 3:1/16 4:1/16 3:1/16 2:1/16 1:1/16",
                anchor="chord", note="a chiptune flourish up the chord and back")
    s.add_motif(P, "fanfare", "4:1/8 4:1/16 4:1/16 r:1/8 7:1/8 6:1/8 4:1/8 r:1/8 5:1/8 | "
                              "4:1/4 r:1/8 2:1/8 4:1/2",
                note="the riff the band opens with and comes back to after each chorus")
    s.add_motif(P, "chime", "7 4 2 4 7 9 7 4 | 8:1/4 6:1/4 4:1/2",
                note="a music box, before anything else")

    # -- players --------------------------------------------------------------
    # The middle is the voice's, the kick's and the bass's; the band is spread.
    s.add_voice(P, "vox", "singer", role="melody", bank="qixuan", pan=0.0)
    s.add_voice(P, "harm", "singer", role="counter", bank="qixuan", pan=0.5)
    s.add_voice(P, "body", "singer", role="counter", bank="qixuan", pan=-0.45)
    s.add_voice(P, "chant", "singer", role="counter", pan=-0.2)
    s.add_voice(P, "keys", "rhodes", role="harmony", octave=4, pan=-0.3)
    s.add_voice(P, "chip", "pulse", role="ornament", octave=5, pan=0.4)
    s.add_voice(P, "blip", "pulse25", role="ornament", octave=5, pan=-0.5)
    s.add_voice(P, "box", "music_box", role="ornament", octave=5, pan=0.1)
    s.add_voice(P, "saws", "supersaw", role="pad", octave=3, pan=-0.75)
    s.add_voice(P, "saws_r", "supersaw", role="pad", octave=3, pan=0.75)
    s.add_voice(P, "brass", "synth_lead", role="ornament", octave=4, pan=0.25)
    s.add_voice(P, "horn1", "trumpet", role="ornament", octave=4, pan=0.3)
    s.add_voice(P, "horn2", "trumpet", role="ornament", octave=4, pan=0.5)
    s.add_voice(P, "horn3", "trombone", role="ornament", octave=3, pan=0.1)
    s.add_voice(P, "bass", "synth_bass", role="bass", octave=1, pan=0.0)
    s.add_voice(P, "wall", "noise_wall", role="ornament", octave=4)
    s.add_voice(P, "drums", "kit_electronic", role="percussion", engine="soundfont", pan=0.0)
    s.add_voice(P, "thump", "kit_808", role="percussion", pan=0.0)

    p = s.get(P)
    add = p.add_op
    VERSES = ("verse", "verse2")
    PRES = ("pre", "pre2")
    CHORUSES = ("chorus", "chorus2", "chorus3")
    POSTS = ("post", "post2")

    # -- the lead -------------------------------------------------------------
    lines = ("bounce", "bounce_up", "patter", "patter_home")
    for i in range(8):
        add("vox", "play", id=f"v1_{i}", motif=lines[i % 4], at=at("verse", 1 + 2 * i), octave=3)
    add("vox", "lyrics", id="w_v1", **span("verse", 1, 16), text=" | ".join(VERSE_1))
    for i in range(4):
        add("vox", "play", id=f"v2_{i}", motif=lines[i], at=at("verse2", 1 + 2 * i), octave=3)
    add("vox", "play", id="v2_tag", motif="tag", at=at("verse2", 9), octave=3)
    add("vox", "lyrics", id="w_v2", **span("verse2"), text=" | ".join(VERSE_2))
    for sec in PRES:
        for i, m in enumerate(("step_1", "step_2", "step_3")):
            add("vox", "play", id=f"{sec}_{i}", motif=m, at=at(sec, 1 + 2 * i), octave=4)
        add("vox", "play", id=f"{sec}_belt", motif="belt", at=at(sec, 7), octave=4)
        add("vox", "lyrics", id=f"w_{sec}", **span(sec), text=" | ".join(PRE))
    for sec in CHORUSES:
        for i, m in enumerate(("call", "answer", "climb", "give",
                               "call", "sting", "climb_ache", "land")):
            add("vox", "play", id=f"{sec}_{i}", motif=m, at=at(sec, 1 + 2 * i), octave=4)
        # The dictionary's first "lives" is the verb; these are the noun.
        add("vox", "lyrics", id=f"w_{sec}", **span(sec), text=" | ".join(CHORUS),
            said={"lives": "l ay v z"})
    add("vox", "play", id="br_0", motif="float_1", at=at("bridge", 1), octave=4, dynamic="mp")
    add("vox", "play", id="br_1", motif="float_2", at=at("bridge", 5), octave=4, dynamic="mf")
    add("vox", "lyrics", id="w_bridge", **span("bridge", 1, 8), text=" | ".join(BRIDGE))
    add("vox", "phrase", id="tag_lead", at=at("tag"), octave=4, unit="1/1",
        steps="7 | 8 | 7 | 6 | 7 | 8 | 5 | 6",
        note="whole notes over the chant: the other half of the counterpoint")
    add("vox", "lyrics", id="w_tag", **span("tag"), text=" | ".join(TAG))
    add("vox", "phrase", id="last", at=at("chorale"), octave=4, steps="8:1/2 8:1/2 | 7:1/1")
    add("vox", "lyrics", id="w_last", **span("chorale", 1, 2), text="con-tin-ue")
    add("vox", "articulate", id="vox_legato", style="legato",
        **{"from": "1", "until": str(START["chorale"] + 4)})
    add("vox", "shape", id="vox_shape", amount=0.4)

    # -- the other voices -----------------------------------------------------
    # A third under the answering lines of the chorus; `harmony_fits` below
    # reports any note of it that rubs the chord, and those are revoiced here.
    for sec in CHORUSES:
        # (first bar, last bar): the "sting" line is joined only in its second
        # bar -- a third under its raised note is a semitone off the chord.
        # ...and under the held "you" it sings a fourth below, not a third: the
        # chord there is the dominant of the four, and a third is its neighbour.
        for tag_, first, last, interval in (("b", 3, 4, -2), ("d", 7, 7, -2), ("d2", 8, 8, -3),
                                            ("f", 12, 12, -2), ("h", 15, 16, -2)):
            add("harm", "double", id=f"h_{sec}_{tag_}", source="vox", interval=interval,
                dynamic="mf", **span(sec, first, last))
    add("harm", "double", id="h_tag", source="vox", interval=-2, dynamic="mf", **span("tag"))
    add("harm", "double", id="h_last", source="vox", interval=-3, **span("chorale", 1, 2))
    # Not under the line that starts on the fourth: an octave down is below
    # this voice.
    add("body", "double", id="b_c3", source="vox", octaves=-1, dynamic="mf",
        **span("chorus3", 9, 12))
    add("body", "double", id="b_c3_end", source="vox", octaves=-1, dynamic="mf",
        **span("chorus3", 15, 16))
    add("body", "double", id="b_tag", source="vox", octaves=-1, **span("tag"))
    add("body", "double", id="b_last", source="vox", octaves=-1, **span("chorale", 1, 2))
    for sec in POSTS:
        add("chant", "play", id=f"ch_{sec}", motif="chant", at=at(sec, 3), times=2,
            every="2/1", octave=4)
        add("chant", "lyrics", id=f"w_ch_{sec}", **span(sec, 3, 6), text=f"{CHANT} | {CHANT}")
    add("chant", "play", id="ch_tag", motif="chant", at=at("tag"), times=4, every="2/1", octave=4,
        dynamic="f")
    add("chant", "lyrics", id="w_ch_tag", **span("tag"), text=" | ".join([CHANT] * 4))

    # -- keys -----------------------------------------------------------------
    STAB = ". 0+1+2+3 . . 0+1+2+3 . 0+1+2+3 ."
    DRIVE = "0+1+2+3 . 0+1+2+3 . 0+1+2+3 . 0+1+2+3 0+1+2+3"
    add("keys", "chords", id="k_groove", at=at("groove"), bars=2, rhythm="1/8", lead=True,
        tones=4, figure=STAB, articulation="staccato")
    add("keys", "chords", id="k_verse", at=at("verse"), bars=18, rhythm="1/8", lead=True,
        tones=4, figure=STAB, articulation="staccato", octave=3, dynamic="ff",
        note="off-beat seventh chords, short: the funk is in the gaps")
    add("keys", "chords", id="k_verse2", at=at("verse2"), bars=10, rhythm="1/8", lead=True,
        tones=4, figure=STAB, articulation="staccato", octave=3, dynamic="ff")
    for sec in PRES:
        add("keys", "chords", id=f"k_{sec}", at=at(sec), bars=9, rhythm="1/2", lead=True,
            tones=4, dynamic="mp", note="held, two to the bar: the floor has gone")
    for sec in CHORUSES:
        first = 9 if sec == "chorus3" else 1
        add("keys", "chords", id=f"k_{sec}", at=at(sec, first), bars=17 - first, rhythm="1/8",
            lead=True, tones=4, figure=DRIVE)
    for sec in POSTS + ("tag",):
        add("keys", "chords", id=f"k_{sec}", at=at(sec), bars=LENGTH[sec], rhythm="1/8",
            lead=True, tones=4, figure=DRIVE, dynamic="mp")
    add("keys", "chords", id="k_c3_bare", at=at("chorus3"), bars=8, rhythm="1/1", lead=True,
        tones=4, ring=True, dynamic="mf",
        note="the stripped half of the last chorus: held chords, nothing else moving")
    add("keys", "chords", id="k_bridge", at=at("bridge"), bars=8, rhythm="1/1", lead=True,
        tones=4, ring=True, dynamic="mp")
    add("keys", "chords", id="k_end", at=at("chorale", 3), bars=2, rhythm="1/1", lead=True,
        tones=4, ring=True, note="the last chord, left to ring")

    # -- chips ----------------------------------------------------------------
    for sec in CHORUSES:
        add("chip", "chords", id=f"c_{sec}", at=at(sec), bars=16, voicing="arpeggio_updown",
            rhythm="1/16", tones=4, dynamic="pp",
            note="sixteenths up and down the chord, the way a sound chip fakes one: "
                 "seasoning under the full band, the whole dish when it drops out")
    add("chip", "dynamics", id="c_solo", **span("chorus3", 1, 6), start="mf", end="mf")
    add("chip", "chords", id="c_tag", at=at("tag"), bars=8, voicing="arpeggio_updown",
        rhythm="1/16", tones=4, dynamic="mp")
    add("chip", "chords", id="c_bridge", at=at("bridge", 5), bars=4, voicing="arpeggio_up",
        rhythm="1/8", tones=4, dynamic="p")
    for sec, bars in (("verse", (4, 8, 12, 16)), ("verse2", (4, 8))):
        for b in bars:
            add("blip", "play", id=f"bl_{sec}_{b}", motif="blip", at=at(sec, b, 3))
    add("blip", "play", id="bl_break", motif="blip", at=at("verse", 17), times=4, every="1/2")
    add("box", "play", id="box_open", motif="chime", at=at("chime"), octave=5)
    add("box", "play", id="box_bridge", motif="chime", at=at("bridge", 9), octave=5,
        note="the silent bar before the stabs: the music box, alone and dry")
    add("box", "play", id="box_c3", motif="chime", at=at("chorus3"), octave=5, dynamic="mp",
        note="the music box again, as the stripped chorus starts")
    add("box", "play", id="box_close", motif="chime", at=at("chorale", 3), octave=5)

    # -- saws and brass -------------------------------------------------------
    OFFBEAT = ". 0+1+2 . 0+1+2 . 0+1+2 . 0+1+2"
    for sec in CHORUSES + POSTS + ("tag",):
        first = 9 if sec == "chorus3" else 1
        add("saws", "chords", id=f"s_{sec}", at=at(sec, first), bars=LENGTH[sec] + 1 - first,
            rhythm="1/2", lead=True, tones=4,
            note="held chords; the kick's duck is what makes them pump")
    for sec in PRES:
        add("saws", "chords", id=f"s_{sec}", at=at(sec, 5), bars=5, rhythm="1/8", lead=True,
            tones=3, figure=OFFBEAT, articulation="staccato", octave=4)
        add("saws", "dynamics", id=f"s_{sec}_build", **span(sec, 5, 9), start="p", end="f")
    add("saws", "chords", id="s_bridge", at=at("bridge", 5), bars=4, rhythm="1/8", lead=True,
        tones=3, figure=OFFBEAT, articulation="staccato")
    add("saws", "dynamics", id="s_bridge_build", **span("bridge", 5, 8), start="p", end="f")
    HITS = "0+1+2 . . 0+1+2 . . 0+1+2 . . . 0+1+2 . 0+1+2 . 0+1+2 0+1+2"
    add("saws", "chords", id="s_drop", at=at("bridge", 10), bars=1, rhythm="1/16", tones=3,
        figure=HITS, articulation="staccato", dynamic="ff",
        note="the stabs after the silent bar")
    add("saws_r", "double", id="saws_twin", source="saws")
    add("brass", "play", id="br_groove", motif="fanfare", at=at("groove"))
    for sec in POSTS:
        add("brass", "play", id=f"br_{sec}", motif="fanfare", at=at(sec))
    add("brass", "play", id="br_break", motif="fanfare", at=at("verse", 17), dynamic="mf")
    add("brass", "play", id="br_tag", motif="fanfare", at=at("tag"), times=4, every="2/1",
        dynamic="mp")

    # -- horns ----------------------------------------------------------------
    for sec in CHORUSES:
        for bar in range(2, 17, 2):
            if bar == 14 or (sec == "chorus3" and bar < 9):
                continue                    # the stop, and the stripped half
            add("horn1", "play", id=f"hn_{sec}_{bar}", motif="punch", at=at(sec, bar),
                articulation="staccato", octave=4)
    for sec in POSTS:
        add("horn1", "play", id=f"hn_{sec}", motif="fanfare", at=at(sec), octave=4)
    add("horn1", "play", id="hn_tag", motif="fanfare", at=at("tag"), times=4, every="2/1",
        octave=4)
    for sec in CHORUSES:                    # a third under the punches only: under
        add("horn2", "double", id=f"hn2_{sec}", source="horn1", interval=-2,   # the riff
            **span(sec))                    # it lands a semitone off the dominant
    add("horn3", "double", id="hn3", source="horn1", octaves=-1)

    # -- bass -----------------------------------------------------------------
    # Loud, and driven hard below: played politely the figure read as
    # "buried straight root notes".
    add("bass", "play", id="bs_groove", motif="slap", at=at("groove"), times=2, every="1/1",
        dynamic="f")
    add("bass", "play", id="bs_verse", motif="slap", at=at("verse"), times=18, every="1/1",
        dynamic="f")
    add("bass", "play", id="bs_verse2", motif="slap", at=at("verse2"), times=10, every="1/1",
        dynamic="f")
    for sec in PRES:
        add("bass", "bass", id=f"bs_{sec}", at=at(sec, 5), bars=5, pattern="root",
            rhythm="1/2", note="long roots, once the kick is back")
    for sec in CHORUSES + POSTS + ("tag",):
        first = 9 if sec == "chorus3" else 1
        add("bass", "play", id=f"bs_{sec}", motif="disco", at=at(sec, first),
            times=LENGTH[sec] + 1 - first, every="1/1")
    add("bass", "bass", id="bs_bridge", at=at("bridge"), bars=8, pattern="root", rhythm="1/1",
        dynamic="mp")
    add("bass", "bass", id="bs_drop", at=at("bridge", 10), bars=1, pattern="octaves",
        rhythm="1/8")
    add("bass", "bass", id="bs_end", at=at("chorale", 3), bars=1, pattern="root", rhythm="1/1")

    # -- drums ----------------------------------------------------------------
    # The grooves are written as patterns (`pattern.py`): the shape of a bar,
    # with the turns a drummer would take -- a pickup every other bar, a drag
    # into every fourth -- said once instead of typed out sixteen steps at a
    # time. The first version also had ghost notes and a shaker that played
    # "some of the time" (`o?`), and under a vocal that read as distracting:
    # the ear follows whatever is irregular. What varies here varies on a
    # two- or four-bar cycle, which is a phrase; nothing is left to chance.
    # Space is the groove: ghosted hats between the played ones, nothing ringing.
    # Three kicks a bar and a pickup every other one. With five, plus the bass
    # landing on each, the low end was a continuous rumble of hits.
    FUNK = {"kick": "x [. . x .] [. . x .] <. [. . . x]>",
            "snare": ". x . <x x x [x . o o]>",
            "hat": "x o x o x o x .",
            "open": ". . . . . . . <x x x .>"}
    FUNK_STOP = {"kick": "x [. . x .] . .", "snare": ". x . .",
                 "hat": "x x x x . . . .", "crash": "x . . ."}
    TICK = {"hat": "o*8", "rim": ". x . <x [x . . x]>"}
    FOUR = {"kick": "x*4", "hat": "[. x]*4"}
    # Accented on the beat, so eight hats to the bar have a pulse in them, and
    # a kick that pushes into every fourth bar. The fills belong to the toms.
    BIG = {"kick": "[x . . .] [. . x .] [x . . .] <[. . x .]!3 [. x x .]>",
           "snare": ". x . x", "clap": ". x . x", "hat": "[X x]*4"}
    ONCE = "<x .!15>"                        # a crash at the start, and not again

    def drums(op_id, where, bars, lanes, **kw):
        add("drums", "beat", id=op_id, at=where, bars=bars, lanes=lanes, **kw)

    def groove(op_id, where, bars, lanes):
        drums(op_id, where, bars, lanes, cycle=1)

    groove("d_groove", at("groove"), 2, {**FUNK, "crash": ONCE})
    for sec in VERSES:
        for half, first in enumerate((1, 9) if sec == "verse" else (1,)):
            groove(f"d_{sec}_{half}", at(sec, first), 7, FUNK)
            groove(f"d_{sec}_{half}_stop", at(sec, first + 7), 1, FUNK_STOP)
    drums("d_break", at("verse", 17), 2,
          {"kick": "x.....x...x.....|x...x...x.x.x.x.", "snare": "....x.......x...|....x...x.x.xxxx",
           "hat": "x.x.x.x.x.x.x.x.|x.x.x.x........."})
    groove("d_verse2_tag", at("verse2", 9), 2,
           {**FUNK, "snare": ". x . x | . x [x . x .] x*4"})
    for sec in PRES:
        groove(f"d_{sec}_a", at(sec), 4, TICK)
        drums(f"d_{sec}_b", at(sec, 5), 5,
              {"kick": "|".join(["x...x...x...x..."] * 4 + ["x...x..........."]),
               "hat": "|".join(["..x...x...x...x."] * 4 + ["................"]),
               "snare": "................|................|....x.......x...|"
                        "x.x.x.x.xxxxxxxx|................"})
        # ...and the last half bar before the cut in thirty-seconds.
        add("drums", "beat", id=f"d_{sec}_32", at=at(sec, 9), bars=1, res="1/32",
            lanes={"snare": "x" * 16 + "." * 16})
        add("drums", "dynamics", id=f"d_{sec}_swell", **span(sec, 7, 9), start="mp", end="ff")
    for sec in CHORUSES:
        if sec != "chorus3":
            groove(f"d_{sec}_a", at(sec), 8, {**BIG, "crash": ONCE})
        groove(f"d_{sec}_b", at(sec, 9), 5, {**BIG, "crash": ONCE})
        drums(f"d_{sec}_hole", at(sec, 14), 1, {"kick": "x.....x.........",
                                               "snare": "....x...........",
                                               "hat": "x.x.x.x........."})
        groove(f"d_{sec}_c", at(sec, 15), 2,
               {**BIG, "crash": ONCE})
    # Toms into the half-way point and out of the end of every chorus.
    for sec in CHORUSES:
        for tag_, bar in (("mid", 8), ("end", 16)):
            if sec == "chorus3" and bar == 8:
                continue
            drums(f"d_{sec}_toms_{tag_}", at(sec, bar), 1,
                  {"tom_hi": "........x.x.....", "tom_mid": "............x.x.",
                   "tom_lo": "..............xx"} if bar == 8 else
                  {"tom_hi": "........xx......", "tom_mid": "..........xx....",
                   "tom_lo": "............xxxx"})
            add("drums", "dynamics", id=f"d_{sec}_toms_{tag_}_sw",
                **{"from": at(sec, bar, 3), "until": str(START[sec] + bar)}, start="mf", end="ff")
    drums("d_c3_roll", at("chorus3", 7), 2,
          {"snare": "x...x...x...x...|x.x.x.x.xxxxxxxx", "kick": "x.......x.......|x...x...x...x..."})
    add("drums", "dynamics", id="d_c3_swell", **span("chorus3", 7, 8), start="mp", end="ff")
    groove("d_post", at("post"), 6, {**BIG, "crash": ONCE})
    groove("d_post2", at("post2"), 4, {**BIG, "crash": ONCE})
    groove("d_bridge", at("bridge", 5), 4,
           {**FOUR, "snare": ". | . x . x | . x x x | x*2 x*2 x*8@2"})
    add("drums", "dynamics", id="d_bridge_swell", **span("bridge", 5, 8), start="mp", end="ff")
    drums("d_drop", at("bridge", 10), 1,
          {"kick": "x..x..x...x.x.xx", "snare": "x..x..x...x.x.xx", "crash": "x.....x.....x..."})
    groove("d_tag", at("tag"), 8, {**BIG, "crash": "<x .>", "open": ". [. x] . [. x]"})
    drums("d_end", at("chorale", 3), 1, {"kick": "x" + "." * 15, "crash": "x" + "." * 15,
                                        "snare": "x" + "." * 15})
    # The same kicks on a synthesized drum: the sampled kit's is all click.
    for op in list(p.get_voice("drums").ops):
        if op.kind == "beat" and "kick" in op.params["lanes"]:
            add("thump", "beat", id="t_" + op.id, at=op.params["at"], bars=op.params["bars"],
                lanes={"kick": op.params["lanes"]["kick"]}, cycle=op.params.get("cycle"))

    # -- risers ---------------------------------------------------------------
    for op_id, sec, first, last in (("r_pre", "pre", 5, 9), ("r_pre2", "pre2", 5, 9),
                                    ("r_bridge", "bridge", 5, 8), ("r_c3", "chorus3", 7, 8)):
        add("wall", "chords", id=op_id, at=at(sec, first), bars=last - first + 1,
            voicing="pad", tones=2)
        add("wall", "filter", id="fx_" + op_id, **span(sec, first, last), mode="highpass",
            start=300, end=9000, resonance=0.4)
        add("wall", "dynamics", id="sw_" + op_id, **span(sec, first, last), start="pp", end="f")

    # -- sound ----------------------------------------------------------------
    for side in ("saws", "saws_r"):
        add(side, "duck", id=f"pump_{side}", source="thump", drum="kick", depth=9, release=0.16,
            note="the pads breathe against the kick")
        add(side, "filter", id=f"dark_{side}", start=3000, end=3000,
            note="under the voice's presence range")
        add(side, "gain", id=f"lvl_{side}", db=-7)
    for voice in ("keys", "chip", "horn1", "horn2", "horn3"):
        add(voice, "duck", id=f"pump_{voice}", source="thump", drum="kick", depth=5,
            release=0.12)
    add("keys", "filter", id="hp_keys", mode="highpass", start=220, end=220,
        note="out of the bass's way")
    add("bass", "eq", id="eq_bass", freq=300, gain=-3, width=1.5)
    for voice, db in (("horn1", 2), ("horn2", -1), ("horn3", 0)):
        add(voice, "gain", id=f"lvl_{voice}", db=db)
    add("bass", "duck", id="pump_bass", source="thump", drum="kick", depth=6, release=0.08,
        note="a little, so the kick's front edge is the kick's")
    add("bass", "drive", id="fx_bass", amount=0.45)
    add("bass", "gain", id="lvl_bass", db=-3)
    add("drums", "compress", id="fx_drums", ratio=4, threshold=-18)
    add("drums", "gain", id="lvl_drums", db=-1)
    add("thump", "filter", id="fx_thump", start=160, end=160)
    add("thump", "gain", id="lvl_thump", db=5)
    # Less air, more voice, quicker consonants, a slightly bigger mouth: the
    # bank's own delivery is sweet and breathy, and this song wants it to belt.
    for voice in ("vox", "harm", "body"):
        add(voice, "tone", id=f"tone_{voice}", breath=-6, firm=3, crisp=1.2, gender=0.05)
    add("vox", "drive", id="grit_vox", amount=0.2,
        note="a little tube: edge on the belts. Drive is matched at the peak, and "
             "a voice is mostly peak, so this is also 8 dB of loudness -- taken "
             "back off at the fader below")
    add("vox", "compress", id="fx_vox", ratio=4, threshold=-18)
    add("vox", "eq", id="eq_vox", freq=3300, gain=-3, width=1.2,
        note="the edge the voice gets on long high notes")
    add("vox", "gain", id="lvl_vox", db=-2)
    for voice, db in (("harm", -2), ("body", -3)):
        add(voice, "eq", id=f"eq_{voice}", freq=3300, gain=-6, width=1.5,
            note="the same singer again stacks the same edge: this one gives it up")
        add(voice, "gain", id=f"lvl_{voice}", db=db)
    add("chant", "crush", id="fx_chant", rate=16000, bits=8,
        note="an older machine: fewer bits. (At 9 kHz it lost everything above "
             "4.5 kHz too and sounded like a voice in another room.)")
    add("chant", "eq", id="eq_chant", freq=2800, gain=4, width=1.5)
    add("chant", "gain", id="lvl_chant", db=5)
    add("box", "crush", id="fx_box", rate=7000, bits=6)
    add("keys", "eq", id="eq_keys", freq=3000, gain=-4, width=1.5)
    add("keys", "gain", id="lvl_keys", db=-4)
    add("chip", "eq", id="eq_chip", freq=3500, gain=-5, width=1.5,
        note="square waves are all odd harmonics, and they land on the consonants")
    add("chip", "gain", id="lvl_chip", db=-9)
    add("blip", "gain", id="lvl_blip", db=-8)
    add("brass", "filter", id="fx_brass", start=3200, end=3200)
    add("brass", "gain", id="lvl_brass", db=-5)
    add("wall", "gain", id="lvl_wall", db=-6)
    add("drums", "humanize", id="feel_drums", amount=0.5, timing=4)
    add("keys", "humanize", id="feel_keys", amount=0.4, timing=5)
    add("bass", "humanize", id="feel_bass", amount=0.3, timing=3)
    s.save(p)

    # -- stops ----------------------------------------------------------------
    # The band and the room cut dead; the voices named carry on, dry.
    singers = ["vox", "harm", "body", "chant"]
    stops = [{"from": at("verse", 8, 3), "until": at("verse", 9), "keep": singers},
             {"from": at("verse", 16, 3), "until": at("verse", 17), "keep": singers},
             {"from": at("verse2", 8, 3), "until": at("verse2", 9), "keep": singers},
             {"from": at("bridge", 9), "until": at("bridge", 10), "keep": ["box"]},
             {"from": at("chorale"), "until": at("chorale", 3), "keep": singers}]
    for sec in PRES:
        stops.append({"from": at(sec, 9, 3), "until": str(START[sec] + 9), "keep": singers})
    for sec in CHORUSES:
        stops.append({"from": at(sec, 14, 3), "until": at(sec, 15), "keep": singers})
    # A short, quiet room: the voice is meant to be close and dry.
    s.set_master(P, push=6, stops=stops, room={"decay": 0.7, "wet": 0.06})
    return s


def harmony_fits(s: Studio) -> list[str]:
    """Sung notes of a quarter or longer that sit a semitone from a chord tone
    and are not one themselves: the rubs worth revoicing."""
    from musicstudio.theory import pitch_name
    p = s.get(P)
    r = s.render(P)
    out = []
    for n in sorted(r.notes, key=lambda n: (n.voice, n.start)):
        if n.voice not in ("vox", "harm", "body", "chant") or n.dur < 480:
            continue
        chord, key = p.chord_at(n.start)
        tones = {chord.tone(key, i, 4) % 12 for i in range(4)}
        pc = n.pitch % 12
        if pc not in tones and ({(pc + 1) % 12, (pc - 1) % 12} & tones):
            bar, beat = p.position_of(n.start)
            out.append(f"{n.voice} {bar}:{float(beat):g} {pitch_name(n.pitch)} "
                       f"({n.lyric}) against {chord.symbol if hasattr(chord, 'symbol') else ''}"
                       f" {sorted(tones)}")
    return out


def main() -> int:
    s = build()
    print(s.squint(P))
    print()
    r = s.render(P)
    for w in r.warnings:
        print(f"warning: {w}")
    for line in harmony_fits(s):
        print(f"rub: {line}")
    print(report(s.lint(P)))
    print()
    print(f"midi: {s.export_midi(P)}")
    if "--no-wav" not in sys.argv:
        print(f"wav:  {s.export_wav(P)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
