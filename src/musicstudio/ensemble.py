"""Instruments and ensembles -- what a voice can actually play.

This is the palette. A voice is not a MIDI channel with a program number; it is
a named instrument that knows its own range, the register where it blends, and
whether it can hold a chord at all. The studio therefore knows the things an
agent reliably gets wrong from memory: that a horn cannot play a low E, that a
flute in its bottom octave will be buried under anything, that asking a solo
oboe for a triad is asking for something that does not exist.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from .theory import parse_pitch


@dataclass(frozen=True, slots=True)
class Instrument:
    name: str
    family: str
    #: Absolute playable range, as sounding pitch. Outside this is an error.
    low: str
    high: str
    #: Where it sounds characteristic and blends. Outside this is a warning.
    comfort_low: str
    comfort_high: str
    #: General MIDI program number.
    program: int
    #: 1 means monophonic -- two notes at once is a mistake, not a chord.
    polyphony: int = 1
    #: Synthesis recipe for the WAV render; see ``audio.VOICES``.
    timbre: str = "bow"
    percussive: bool = False
    #: GM percussion key, for instruments that live on channel 10.
    drum_key: int | None = None
    notes: tuple[str, ...] = ()
    #: A SoundFont this instrument is sampled from, by its name in
    #: ``soundfonts.BANKS``, and the ``(bank, program)`` of its preset there.
    #: Only for ``engine="soundfont"``; without that bank installed it is
    #: played from the General MIDI bank's ``program`` instead, and MIDI
    #: export always writes ``program``.
    font: str | None = None
    preset: tuple[int, int] | None = None
    #: The instrument whose model plays this one when its bank is not there.
    like: str | None = None
    #: For a kit whose bank does not lay its drums out the General MIDI way:
    #: ``(General MIDI key, the key that drum is on in the bank)`` pairs. Read
    #: out of the bank's own zone table, not guessed.
    keymap: tuple[tuple[int, int], ...] = ()

    @property
    def lo(self) -> int:
        return parse_pitch(self.low)

    @property
    def hi(self) -> int:
        return parse_pitch(self.high)

    @property
    def clo(self) -> int:
        return parse_pitch(self.comfort_low)

    @property
    def chi(self) -> int:
        return parse_pitch(self.comfort_high)

    @property
    def centre(self) -> int:
        return (self.clo + self.chi) // 2

    def to_json(self) -> dict:
        return {"name": self.name, "family": self.family,
                "range": [self.low, self.high],
                "comfort": [self.comfort_low, self.comfort_high],
                "polyphony": self.polyphony, "timbre": self.timbre,
                "program": self.program, "notes": list(self.notes),
                **({"font": self.font} if self.font else {})}


def _i(name, family, low, high, clow, chigh, program, **kw) -> Instrument:
    return Instrument(name, family, low, high, clow, chigh, program, **kw)


#: Ranges are sounding pitch, taken at the conservative end -- the bottom of a
#: professional range is not somewhere to write a exposed melody, and the studio
#: should not encourage it just because the note technically exists.
INSTRUMENTS: dict[str, Instrument] = {i.name: i for i in [
    # -- strings ----------------------------------------------------------
    _i("violin", "strings", "G3", "A7", "G3", "E6", 40, polyphony=2, timbre="bow",
       notes=("Double stops only across adjacent strings; three-note chords are rolled.",)),
    _i("viola", "strings", "C3", "E6", "C3", "C5", 41, polyphony=2, timbre="bow"),
    _i("cello", "strings", "C2", "A5", "C2", "E5", 42, polyphony=2, timbre="bow",
       notes=("The tenor register (C3-E4) is the singing one; use it for melody.",)),
    _i("contrabass", "strings", "E1", "C4", "E1", "G3", 43, polyphony=1, timbre="bow",
       notes=("Sounds an octave below where it reads. Doubling cello at the octave is the norm.",)),
    _i("strings", "strings", "C2", "C7", "C3", "C6", 48, polyphony=8, timbre="pad",
       notes=("A section, not a soloist. Write it as real voices, not as a block.",)),
    _i("pizz_strings", "strings", "C2", "C6", "C3", "C5", 45, polyphony=6, timbre="pluck"),
    _i("tremolo_strings", "strings", "C2", "C7", "C3", "C6", 44, polyphony=8, timbre="pad"),
    # -- woodwinds --------------------------------------------------------
    _i("flute", "winds", "C4", "D7", "D5", "G6", 73, polyphony=1, timbre="flute",
       notes=("The bottom octave (C4-C5) is weak and will be covered by anything else.",)),
    _i("piccolo", "winds", "D5", "C8", "G5", "G7", 72, polyphony=1, timbre="flute"),
    _i("oboe", "winds", "Bb3", "G6", "D4", "D6", 68, polyphony=1, timbre="reed",
       notes=("Cuts through everything. One oboe line is enough; two fight.",)),
    _i("english_horn", "winds", "E3", "A5", "G3", "G5", 69, polyphony=1, timbre="reed"),
    _i("clarinet", "winds", "D3", "Bb6", "E3", "C6", 71, polyphony=1, timbre="reed",
       notes=("The chalumeau (D3-G4) is dark and hollow; the top is bright and thin.",)),
    _i("bassoon", "winds", "Bb1", "Eb5", "C2", "G4", 70, polyphony=1, timbre="reed",
       notes=("Its tenor register (C3-G4) is a genuine melodic voice, not just a bass.",)),
    # -- brass ------------------------------------------------------------
    _i("horn", "brass", "B1", "F5", "C3", "C5", 60, polyphony=1, timbre="brass",
       notes=("The heroic register is C4-G4. Below C3 it is soft and unfocused.",)),
    _i("trumpet", "brass", "E3", "D6", "G3", "Bb5", 56, polyphony=1, timbre="brass"),
    _i("trombone", "brass", "E2", "Bb4", "G2", "F4", 57, polyphony=1, timbre="brass"),
    _i("tuba", "brass", "D1", "F4", "F1", "C3", 58, polyphony=1, timbre="brass"),
    # -- keyboards and plucked -------------------------------------------
    _i("piano", "keys", "A0", "C8", "E1", "C7", 0, polyphony=10, timbre="struck",
       notes=("Two hands. Keep each hand inside a tenth, and leave the low register open.",)),
    _i("celesta", "keys", "C4", "C8", "C5", "C7", 8, polyphony=6, timbre="bell"),
    _i("music_box", "keys", "C5", "C8", "C5", "C7", 10, polyphony=4, timbre="bell"),
    _i("harpsichord", "keys", "F1", "F6", "C2", "C6", 6, polyphony=8, timbre="pluck"),
    _i("organ", "keys", "C2", "C7", "C3", "C6", 19, polyphony=8, timbre="pad"),
    _i("rhodes", "keys", "E1", "E6", "C2", "C6", 4, polyphony=8, timbre="bell"),
    _i("harp", "plucked", "C1", "G7", "C2", "C6", 46, polyphony=8, timbre="pluck",
       notes=("Glissandi and rolled chords are its idiom; repeated single notes are not.",)),
    _i("guitar", "plucked", "E2", "E6", "E2", "E5", 24, polyphony=6, timbre="pluck"),
    _i("choir", "voice", "F2", "A5", "C3", "F5", 52, polyphony=8, timbre="pad",
       notes=("Wordless 'ah'. Slow moving lines only; it cannot articulate fast rhythm.",)),
    # Solo voices that sing words. Without lyrics they vocalise on "ah".
    _i("singer", "voice", "G3", "E6", "C4", "G5", 53, polyphony=1, timbre="pad",
       notes=("A bright, light voice, synthesized. Give it words with the `lyrics` "
              "op: one syllable per note. Vowels are what carry -- write long "
              "notes on them and let consonants be quick.",)),
    _i("singer_warm", "voice", "G3", "E6", "C4", "G5", 53, polyphony=1, timbre="pad",
       notes=("The same voice sung like a person: it slides between notes and "
              "has vibrato. `singer` steps and holds, like a synthesized one.",)),
    _i("singer_low", "voice", "E2", "A4", "A2", "E4", 52, polyphony=1, timbre="pad",
       notes=("The same throat, larger: a low voice.",)),
    _i("singer_breathy", "voice", "G3", "E6", "A3", "E5", 53, polyphony=1, timbre="pad",
       notes=("More air than tone. For close, quiet lines.",)),
    # -- tuned percussion -------------------------------------------------
    _i("glockenspiel", "perc", "F5", "C8", "C6", "C8", 9, polyphony=4, timbre="bell"),
    _i("vibraphone", "perc", "F3", "F6", "F3", "F6", 11, polyphony=4, timbre="bell"),
    _i("marimba", "perc", "C2", "C7", "C3", "C6", 12, polyphony=4, timbre="pluck"),
    _i("timpani", "perc", "D2", "A3", "F2", "F3", 47, polyphony=2, timbre="struck",
       notes=("Tuned to two or three pitches per cue; retuning takes bars, not beats.",)),
    # -- synth ------------------------------------------------------------
    _i("synth_pad", "synth", "C1", "C7", "C2", "C6", 89, polyphony=8, timbre="pad"),
    _i("synth_lead", "synth", "C2", "C7", "C4", "C6", 81, polyphony=1, timbre="saw"),
    _i("supersaw", "synth", "C1", "C7", "C2", "C6", 81, polyphony=4, timbre="saw",
       notes=("Seven saws spread a quarter-tone wide: thick, harsh and wide. The "
              "opposite of a chip lead -- it sounds like a wall, not a whistle.",)),
    _i("noise_wall", "synth", "C1", "C7", "C2", "C6", 122, polyphony=2, timbre="saw",
       notes=("Almost pure noise. Hold it under everything, sweep a filter across "
              "it for a riser, or gate it with `chop`.",)),
    _i("synth_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="saw"),
    _i("sub_bass", "synth", "C0", "C3", "D1", "G2", 39, polyphony=1, timbre="tri",
       notes=("Nearly a sine: felt more than heard, and inaudible on small speakers. "
              "Keep it between D1 and G2 and let something brighter carry the line.",)),
    _i("reese_bass", "synth", "C0", "C4", "E1", "C3", 38, polyphony=1, timbre="saw",
       notes=("Detuned saws under a low filter: it growls and slowly phases. A long "
              "note is its idiom; it smears fast lines.",)),
    _i("acid_bass", "synth", "C1", "C7", "E1", "C5", 38, polyphony=1, timbre="saw",
       notes=("The bass-line machine: a saw through a resonant filter that every "
              "note re-opens. Velocity is the cutoff knob -- soft is a round "
              "pluck, loud squelches, an accent ('!') screams -- so shape it with "
              "`dynamics`. A note marked @leg slides into the next without "
              "re-opening the filter. Write sixteenths with rests in them.",)),
    _i("acid_square", "synth", "C1", "C7", "E1", "C5", 38, polyphony=1, timbre="pulse50",
       notes=("The same machine on its square wave: hollower, more nasal. A "
              "second line an octave above the saw.",)),
    _i("electric_bass", "plucked", "E1", "G4", "E1", "G3", 33, polyphony=1, timbre="pluck",
       notes=("Fingered bass guitar. Notes speak at once and die away: write the "
              "rests, they are half the groove.",)),
    _i("upright_bass", "plucked", "E1", "G4", "E1", "D3", 32, polyphony=1, timbre="pluck",
       notes=("Plucked double bass. Short sustain and a woody thump; walk it.",)),
    # -- a rock band ---------------------------------------------------------
    _i("picked_bass", "plucked", "D1", "G4", "E1", "G3", 34, polyphony=1, timbre="pluck",
       notes=("Bass guitar with a pick: a hard, clanking attack that carries a "
              "line of straight eighths by itself. Drive it a little and keep "
              "it dry.",)),
    _i("distortion_guitar", "plucked", "D2", "E6", "D2", "E5", 30, polyphony=6,
       timbre="saw",
       notes=("An electric guitar through a loud amplifier: it sustains, and "
              "anything closer than a fifth turns to noise below the middle of "
              "the neck. Write roots and fifths (two voices panned apart are "
              "double-tracking). Reaches a dropped low D.",)),
    _i("muted_guitar", "plucked", "D2", "E6", "D2", "E5", 28, polyphony=6,
       timbre="pluck",
       notes=("The same guitar with the palm on the strings: a short, dull "
              "thud with a pitch. For the chug before the wall.",)),
    _i("whistle", "winds", "C4", "C8", "C5", "C7", 78, polyphony=1, timbre="flute",
       notes=("Almost a sine, with breath on it. Long notes; it is eerie because "
              "it is plain, so leave the ornaments off.",)),
    # -- synthesizers: leads ------------------------------------------------
    _i("saw_lead", "synth", "C2", "C7", "C4", "C6", 81, polyphony=1, timbre="saw",
       notes=("Two saws and a filter that opens with each note. Slurred notes "
              "glide; long ones get vibrato.",)),
    _i("square_lead", "synth", "C2", "C7", "C4", "C6", 80, polyphony=1, timbre="pulse50",
       notes=("Hollow and steady: the lead that sits above a busy track without "
              "thickening it.",)),
    _i("pwm_lead", "synth", "C2", "C7", "C4", "C6", 80, polyphony=1, timbre="pulse25",
       notes=("A pulse whose width moves: it chorus-es itself.",)),
    _i("sine_lead", "synth", "C3", "C8", "C5", "C7", 79, polyphony=1, timbre="tri",
       notes=("One sine with a glide. Carries a tune over anything, and is "
              "inaudible below C4.",)),
    _i("resonant_lead", "synth", "C2", "C7", "C3", "C6", 84, polyphony=1, timbre="saw",
       notes=("The filter whistles as it closes on each note. Velocity is how "
              "far it opens.",)),
    _i("theremin", "synth", "C3", "C7", "C4", "C6", 79, polyphony=1, timbre="tri",
       notes=("Slides everywhere and never stops wavering. Write it legato; "
              "leaps are the point.",)),
    _i("hoover", "synth", "C2", "C6", "C3", "C5", 81, polyphony=3, timbre="saw",
       notes=("Five detuned pulses that swoop up into every note: rave. Loud "
              "and wide; one line, or bare fifths.",)),
    # -- synthesizers: plucks, stabs, brass -----------------------------------
    _i("synth_pluck", "synth", "C2", "C7", "C3", "C6", 87, polyphony=6, timbre="pluck",
       notes=("A filter snapping shut: the note is over in half a second "
              "however long it is written. Arpeggios and off-beat chords.",)),
    _i("trance_pluck", "synth", "C2", "C7", "C3", "C6", 87, polyphony=6, timbre="pluck",
       notes=("The same on five detuned saws: wide, and it rings a little.",)),
    _i("rave_stab", "synth", "C2", "C6", "C3", "C5", 81, polyphony=6, timbre="saw",
       notes=("A short hard chord. Write it as block chords on the off-beats.",)),
    _i("synth_brass", "synth", "C2", "C6", "C3", "C5", 62, polyphony=6, timbre="brass",
       notes=("Saws whose filter opens a moment late, like brass speaking.",)),
    _i("fm_brass", "synth", "C2", "C6", "C3", "C5", 63, polyphony=4, timbre="brass",
       notes=("FM brass: thinner and more metallic than synth_brass.",)),
    # -- synthesizers: pads ----------------------------------------------------
    _i("warm_pad", "synth", "C1", "C7", "C2", "C6", 89, polyphony=8, timbre="pad",
       notes=("Slow and soft-edged. It takes half a second to arrive, so write "
              "it early.",)),
    _i("pwm_pad", "synth", "C1", "C7", "C2", "C6", 90, polyphony=8, timbre="pad",
       notes=("Moving pulse widths: a pad that shimmers without a chorus.",)),
    _i("sweep_pad", "synth", "C1", "C7", "C2", "C6", 95, polyphony=8, timbre="pad",
       notes=("Its filter opens over two seconds on every note and falls back: "
              "hold chords for at least a bar.",)),
    _i("dark_pad", "synth", "C1", "C6", "C2", "C5", 89, polyphony=8, timbre="pad",
       notes=("Nearly closed, slowly breathing, with a little noise in it. For "
              "under things.",)),
    _i("string_machine", "synth", "C2", "C7", "C3", "C6", 50, polyphony=8, timbre="pad",
       notes=("Six saws and an ensemble wobble: the string synthesizer of the "
              "seventies, not strings.",)),
    _i("glass_pad", "synth", "C2", "C7", "C3", "C6", 92, polyphony=8, timbre="bell",
       notes=("FM: a slow bell with no strike. Cold.",)),
    # -- synthesizers: basses ---------------------------------------------------
    _i("saw_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="saw",
       notes=("A saw, a sub under it, and a filter that plucks each note.",)),
    _i("square_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="pulse50",
       notes=("Hollower than the saw: it leaves the middle of the mix alone.",)),
    _i("round_bass", "synth", "C0", "C4", "C1", "C3", 39, polyphony=1, timbre="tri",
       notes=("Soft and nearly all fundamental. Sits under a busy kick.",)),
    _i("pluck_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="pluck",
       notes=("Short however long it is written. For sixteenth-note lines.",)),
    _i("wobble_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="saw",
       notes=("The filter swings four times a second and restarts with every "
              "note -- so the wobble's rhythm is the rhythm you write: repeat "
              "the note to re-trigger it.",)),
    _i("bass_808", "synth", "C0", "C3", "C1", "G2", 39, polyphony=1, timbre="tri",
       notes=("A sine that drops into its pitch and rings for two seconds: a "
              "kick drum with a note. One at a time; let it ring or cut it "
              "with the next.",)),
    _i("fm_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="pluck",
       notes=("FM: a hard, glassy attack on a round note. Speaks on the smallest "
              "speaker.",)),
    _i("donk_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="pluck",
       notes=("A short hollow knock with a pitch: the off-beat bass of hard "
              "dance music.",)),
    # -- synthesizers: FM keys, bells, effects -----------------------------------
    _i("fm_epiano", "keys", "E1", "C7", "C2", "C6", 5, polyphony=8, timbre="bell",
       notes=("The digital electric piano: a bell on the attack, a sine under it.",)),
    _i("fm_bell", "perc", "C3", "C8", "C4", "C7", 98, polyphony=6, timbre="bell",
       notes=("Inharmonic and long. A few notes; let them ring.",)),
    _i("fm_organ", "keys", "C1", "C7", "C2", "C6", 17, polyphony=8, timbre="pad",
       notes=("On at once and off at once, no dynamics: the house-music organ. "
              "Bass lines and off-beat chords.",)),
    _i("kalimba", "perc", "C3", "C7", "C4", "C6", 108, polyphony=4, timbre="bell"),
    _i("clank", "perc", "C2", "C6", "C3", "C5", 113, polyphony=2, timbre="bell",
       notes=("Metal hit and stopped: a fifth of a second, no ring. Industrial "
              "percussion; the pitch is a colour, so keep it on one note.",)),
    _i("metal_pipe", "perc", "C2", "C6", "C3", "C5", 113, polyphony=2, timbre="bell",
       notes=("The same metal left to ring for a second. Sparse: once a bar "
              "is a lot.",)),
    _i("zap", "synth", "C2", "C7", "C3", "C6", 127, polyphony=1, timbre="saw",
       notes=("Falls three octaves onto its note in a tenth of a second: a "
              "laser. An effect, not a line.",)),
    _i("siren", "synth", "C3", "C6", "C4", "C5", 125, polyphony=1, timbre="tri",
       notes=("Rises and falls a fourth around its note every two seconds. "
              "Hold one long note.",)),
    # -- more of the General MIDI set, for a SoundFont to play -------------------
    _i("bright_piano", "keys", "A0", "C8", "E1", "C7", 1, polyphony=10, timbre="struck"),
    _i("honky_tonk", "keys", "A0", "C8", "E1", "C7", 3, polyphony=10, timbre="struck"),
    _i("clavinet", "keys", "C2", "C7", "C2", "C6", 7, polyphony=8, timbre="pluck"),
    _i("drawbar_organ", "keys", "C2", "C7", "C3", "C6", 16, polyphony=8, timbre="pad"),
    _i("rock_organ", "keys", "C2", "C7", "C3", "C6", 18, polyphony=8, timbre="pad"),
    _i("accordion", "keys", "F2", "A6", "C3", "C6", 21, polyphony=6, timbre="reed"),
    _i("harmonica", "winds", "C4", "C7", "C4", "C6", 22, polyphony=2, timbre="reed"),
    _i("steel_guitar", "plucked", "E2", "E6", "E2", "E5", 25, polyphony=6, timbre="pluck"),
    _i("jazz_guitar", "plucked", "E2", "E6", "E2", "E5", 26, polyphony=6, timbre="pluck"),
    _i("clean_guitar", "plucked", "E2", "E6", "E2", "E5", 27, polyphony=6, timbre="pluck"),
    _i("overdrive_guitar", "plucked", "D2", "E6", "D2", "E5", 29, polyphony=6,
       timbre="saw",
       notes=("Between clean and distorted: chords survive it.",)),
    _i("fretless_bass", "plucked", "E1", "G4", "E1", "G3", 35, polyphony=1, timbre="pluck"),
    _i("slap_bass", "plucked", "E1", "G4", "E1", "G3", 36, polyphony=1, timbre="pluck"),
    _i("sitar", "plucked", "C3", "C6", "C3", "C5", 104, polyphony=2, timbre="pluck"),
    _i("banjo", "plucked", "C3", "C6", "C3", "C5", 105, polyphony=4, timbre="pluck"),
    _i("shamisen", "plucked", "C3", "C6", "C3", "C5", 106, polyphony=2, timbre="pluck"),
    _i("koto", "plucked", "C2", "C6", "C3", "C5", 107, polyphony=4, timbre="pluck"),
    _i("xylophone", "perc", "F4", "C8", "C5", "C7", 13, polyphony=4, timbre="pluck"),
    _i("tubular_bells", "perc", "C4", "F5", "C4", "F5", 14, polyphony=2, timbre="bell"),
    _i("dulcimer", "perc", "C3", "C6", "C3", "C6", 15, polyphony=4, timbre="pluck"),
    _i("steel_drums", "perc", "C3", "C6", "C4", "C6", 114, polyphony=4, timbre="bell"),
    _i("soprano_sax", "winds", "Ab3", "E6", "C4", "C6", 64, polyphony=1, timbre="reed"),
    _i("alto_sax", "winds", "Db3", "Ab5", "F3", "F5", 65, polyphony=1, timbre="reed"),
    _i("tenor_sax", "winds", "Ab2", "E5", "C3", "C5", 66, polyphony=1, timbre="reed"),
    _i("baritone_sax", "winds", "C2", "A4", "E2", "E4", 67, polyphony=1, timbre="reed"),
    _i("muted_trumpet", "brass", "E3", "D6", "G3", "Bb5", 59, polyphony=1, timbre="brass"),
    _i("brass_section", "brass", "C2", "C6", "C3", "C5", 61, polyphony=6, timbre="brass"),
    _i("recorder", "winds", "C4", "D7", "C5", "C7", 74, polyphony=1, timbre="flute"),
    _i("pan_flute", "winds", "C4", "C7", "C4", "C6", 75, polyphony=1, timbre="flute"),
    _i("shakuhachi", "winds", "D4", "D7", "D4", "D6", 77, polyphony=1, timbre="flute"),
    _i("ocarina", "winds", "C4", "C7", "C5", "C7", 79, polyphony=1, timbre="flute"),
    _i("bagpipe", "winds", "Bb3", "C6", "Bb3", "Bb5", 109, polyphony=2, timbre="reed"),
    _i("fiddle", "strings", "G3", "A7", "G3", "E6", 110, polyphony=2, timbre="bow"),
    _i("slow_strings", "strings", "C2", "C7", "C3", "C6", 49, polyphony=8, timbre="pad"),
    _i("orchestra_hit", "strings", "C2", "C6", "C3", "C5", 55, polyphony=4, timbre="pad",
       notes=("A whole orchestra on one chord, short. Use it like a drum.",)),
    _i("choir_oohs", "voice", "F2", "A5", "C3", "F5", 53, polyphony=8, timbre="pad"),
    _i("melodic_tom", "perc", "C2", "C5", "C2", "C4", 117, polyphony=2, timbre="struck"),
    _i("woodblock", "perc", "C4", "C7", "C5", "C6", 115, polyphony=2, timbre="pluck"),
    # -- chip -------------------------------------------------------------
    _i("pulse", "chip", "C1", "C8", "C3", "C6", 80, polyphony=1, timbre="pulse50"),
    _i("pulse25", "chip", "C1", "C8", "C3", "C6", 80, polyphony=1, timbre="pulse25"),
    _i("pulse12", "chip", "C1", "C8", "C3", "C6", 80, polyphony=1, timbre="pulse12"),
    _i("triangle", "chip", "C0", "C6", "C1", "C4", 83, polyphony=1, timbre="tri",
       notes=("The DMG bass voice. One note at a time, and no volume control.",)),
    # -- untuned percussion ----------------------------------------------
    _i("kick", "drums", "C1", "C1", "C1", "C1", 0, timbre="noise", percussive=True, drum_key=36),
    _i("snare", "drums", "D1", "D1", "D1", "D1", 0, timbre="noise", percussive=True, drum_key=38),
    _i("hat", "drums", "F#1", "F#1", "F#1", "F#1", 0, timbre="noise", percussive=True, drum_key=42),
    _i("ride", "drums", "D#2", "D#2", "D#2", "D#2", 0, timbre="noise", percussive=True, drum_key=51),
    _i("crash", "drums", "C#2", "C#2", "C#2", "C#2", 0, timbre="noise", percussive=True, drum_key=49),
    _i("taiko", "drums", "A1", "A1", "A1", "A1", 0, timbre="noise", percussive=True, drum_key=41),
    _i("tambourine", "drums", "F#2", "F#2", "F#2", "F#2", 0, timbre="noise", percussive=True, drum_key=54),
    _i("noise", "chip", "D1", "D1", "D1", "D1", 0, timbre="noise", percussive=True, drum_key=38),
    # -- drum kits: one player, the whole set --------------------------------
    # The program number is the General MIDI kit, sent on the drum channel.
    _i("kit", "drums", "B0", "B5", "B0", "B5", 0, polyphony=8, timbre="noise",
       percussive=True,
       notes=("A whole kit as one voice. Write it with the `beat` op, one lane per "
              "drum; rearrange it with `chop`.",)),
    _i("kit_room", "drums", "B0", "B5", "B0", "B5", 8, polyphony=8, timbre="noise",
       percussive=True),
    _i("kit_power", "drums", "B0", "B5", "B0", "B5", 16, polyphony=8, timbre="noise",
       percussive=True),
    _i("kit_electronic", "drums", "B0", "B5", "B0", "B5", 24, polyphony=8, timbre="noise",
       percussive=True),
    _i("kit_808", "drums", "B0", "B5", "B0", "B5", 25, polyphony=8, timbre="noise",
       percussive=True,
       notes=("Drum machine: a kick that is mostly sub, a snappy snare, tin hats.",)),
    _i("kit_jazz", "drums", "B0", "B5", "B0", "B5", 32, polyphony=8, timbre="noise",
       percussive=True),
    _i("kit_brush", "drums", "B0", "B5", "B0", "B5", 40, polyphony=8, timbre="noise",
       percussive=True),
]}

def _f(name, family, low, high, font, preset, like, program, polyphony=1,
       notes=(), **kw) -> Instrument:
    """An instrument that lives in a particular SoundFont."""
    src = INSTRUMENTS[like]
    return Instrument(name, family, low, high, low, high, program, polyphony=polyphony,
                      timbre=src.timbre, percussive=src.percussive, notes=tuple(notes),
                      font=font, preset=preset, like=like, **kw)


def _kit(name, font, preset, like, note, keymap=None) -> Instrument:
    return _f(name, "drums", "B0", "B5", font, preset, like, INSTRUMENTS[like].program,
              polyphony=8, notes=(note,), keymap=tuple(sorted((keymap or {}).items())))


# MuldjordKit: two kicks, snare, hats, two rides and their bells, two crashes,
# a china, four toms, a rim. What it has no drum for is given its nearest.
_MULDJORD = {36: 48, 35: 49, 38: 50, 40: 51, 37: 65, 39: 50, 42: 52, 44: 52, 46: 53,
             51: 54, 53: 55, 59: 56, 56: 57, 49: 58, 57: 59, 55: 59, 52: 60, 50: 61,
             48: 62, 47: 62, 45: 63, 43: 64, 41: 64, 54: 52, 70: 52}
_SYNTH_PERC = {36: 48, 35: 49, 38: 50, 40: 51, 42: 52, 44: 53, 46: 54, 49: 55, 51: 55,
               57: 56, 55: 56, 53: 56, 45: 57, 41: 58, 43: 58, 47: 59, 48: 60, 50: 61,
               39: 63, 70: 64, 54: 65, 37: 66, 56: 66}


_V = "vintage"
#: Sampled from particular banks (`ms soundfont install <font>`). Each needs
#: ``engine="soundfont"`` on its voice; without the bank, ``like`` plays it.
INSTRUMENTS.update({i.name: i for i in [
    # -- a rock band, recorded ------------------------------------------------
    _f("amp_guitar", "plucked", "D2", "E6", "guitar_dist", (0, 0), "distortion_guitar",
       30, 6, ("A real guitar through a real amplifier, bridge pickup. Roots "
               "and fifths; two voices panned apart are double-tracking.",)),
    _f("strat_clean", "plucked", "E2", "E6", "guitar_clean", (0, 0), "guitar", 27, 6,
       ("Clean electric guitar, bridge pickup: thin and bright. Arpeggios and "
        "funk chords; add `drive` for crunch.",)),
    _f("rbx_picked_bass", "plucked", "B0", "G4", "bass_picked", (0, 0), "picked_bass",
       34, 1, ("A recorded bass guitar played with a pick. Reaches a low B.",)),
    _f("rbx_finger_bass", "plucked", "B0", "G4", "bass_finger", (0, 0), "electric_bass",
       33, 1, ("The same bass, fingers: rounder, less attack.",)),
    _kit("kit_rock", "muldjord", (0, 0), "kit_power",
         "A recorded rock kit, close and room microphones mixed: big toms, a "
         "long snare. The lanes are the usual ones; `splash` is its second "
         "crash, `cow` a ride bell, and there is no clap.", _MULDJORD),
    _f("hammond_rock", "keys", "C2", "C7", "organ_rock", (0, 0), "organ", 18, 8,
       ("Tonewheel organ through a spinning speaker.",)),
    _f("hammond", "keys", "C2", "C7", "organ_drawbar", (0, 0), "organ", 16, 8,
       ("Tonewheel organ, plain.",)),
    _f("concert_grand", "keys", "A0", "C8", "piano_ydp", (0, 0), "piano", 0, 10,
       ("A recorded concert grand with many dynamic layers.",)),
    # -- sampled digital -------------------------------------------------------
    _f("dx_piano", "keys", "E1", "C7", "fm_piano", (0, 0), "fm_epiano", 5, 8,
       ("A sampled FM electric piano.",)),
    _f("lately_bass", "synth", "C1", "C4", "lately_bass", (0, 0), "fm_bass", 38, 1,
       ("The FM bass of late-eighties house and pop: hard, hollow, short.",)),
    _kit("kit_synth", "synth_drums", (0, 0), "kit_electronic",
         "A synthesized drum machine: analog-style kick, snare, hats, toms, "
         "clap, shaker, claves (on `rim`).", _SYNTH_PERC),
    _kit("kit_tr808", _V, (128, 2), "kit_808", "The 808: a boom, a snap, tin hats."),
    _kit("kit_tr909", _V, (128, 3), "kit_electronic",
         "The 909: the kick and hats of house and techno."),
    _kit("kit_cr78", _V, (128, 1), "kit_808",
         "The CR-78: a preset-rhythm box. Small, soft, ticking."),
    _kit("kit_analog", _V, (128, 4), "kit_electronic", "A generic analog drum machine."),
    _kit("kit_robot", _V, (128, 5), "kit_electronic",
         "Zaps and clicks: electro, in the manner of the Dusseldorf school."),
    # -- Vintage Dreams: leads --------------------------------------------------
    _f("detuned_saws", "synth", "C2", "C7", _V, (0, 4), "supersaw", 81, 4),
    _f("thin_saw", "synth", "C2", "C7", _V, (0, 14), "saw_lead", 81, 2),
    _f("monster_lead", "synth", "C2", "C7", _V, (0, 80), "saw_lead", 81, 2),
    _f("stack_lead", "synth", "C2", "C7", _V, (0, 81), "supersaw", 81, 2),
    _f("distorted_lead", "synth", "C2", "C7", _V, (0, 111), "resonant_lead", 84, 1),
    _f("heavy_square", "synth", "C2", "C7", _V, (0, 110), "square_lead", 80, 2),
    _f("screamer", "synth", "C2", "C7", _V, (0, 125), "resonant_lead", 84, 1,
       ("Gated: it stutters as it is held.",)),
    _f("sine_whistle", "synth", "C3", "C8", _V, (0, 37), "sine_lead", 78, 1),
    _f("square_flute", "synth", "C3", "C7", _V, (0, 23), "square_lead", 80, 1),
    _f("dream_flute", "synth", "C3", "C7", _V, (0, 15), "sine_lead", 79, 1),
    _f("space_flute", "synth", "C3", "C7", _V, (0, 127), "sine_lead", 79, 1),
    _f("melodic_vibrato", "synth", "C3", "C7", _V, (0, 63), "theremin", 79, 1),
    # -- Vintage Dreams: basses ---------------------------------------------------
    _f("grunge_bass", "synth", "C0", "C4", _V, (0, 9), "saw_bass", 38, 1),
    _f("ramp_bass", "synth", "C0", "C4", _V, (0, 3), "saw_bass", 38, 1),
    _f("sheet_bass", "synth", "C0", "C4", _V, (0, 7), "round_bass", 39, 1),
    _f("classic_fm_bass", "synth", "C0", "C4", _V, (0, 13), "fm_bass", 38, 1),
    _f("sweep_bass", "synth", "C0", "C4", _V, (0, 22), "wobble_bass", 38, 1),
    _f("rubber_bass", "synth", "C0", "C4", _V, (0, 57), "pluck_bass", 38, 1),
    _f("acid_sub_bass", "synth", "C0", "C4", _V, (0, 77), "acid_bass", 38, 1),
    _f("killer_bass", "synth", "C0", "C4", _V, (0, 99), "saw_bass", 38, 1),
    _f("analog_bass", "synth", "C0", "C4", _V, (0, 104), "round_bass", 39, 1),
    _f("harsh_fm_bass", "synth", "C0", "C4", _V, (0, 52), "fm_bass", 38, 1),
    _f("sequencer_bass", "synth", "C0", "C4", _V, (0, 76), "fm_bass", 38, 1),
    _f("woody_bass", "synth", "C0", "C4", _V, (0, 121), "donk_bass", 38, 1),
    # -- Vintage Dreams: pads and strings -------------------------------------------
    _f("resonating_pad", "synth", "C1", "C7", _V, (0, 8), "sweep_pad", 89, 8),
    _f("dragon_sweep", "synth", "C1", "C7", _V, (0, 6), "sweep_pad", 95, 6),
    _f("banshee_pad", "synth", "C1", "C7", _V, (0, 71), "dark_pad", 89, 6),
    _f("undulating_pad", "synth", "C1", "C7", _V, (0, 72), "pwm_pad", 90, 8),
    _f("warble_pad", "synth", "C1", "C7", _V, (0, 74), "pwm_pad", 90, 8),
    _f("dreamy_pad", "synth", "C1", "C7", _V, (0, 90), "warm_pad", 89, 8),
    _f("breath_pad", "synth", "C1", "C7", _V, (0, 91), "dark_pad", 91, 8),
    _f("wavepad", "synth", "C1", "C7", _V, (0, 59), "glass_pad", 92, 8),
    _f("screaming_wavepad", "synth", "C1", "C7", _V, (0, 62), "sweep_pad", 95, 6),
    _f("fantasy_pad", "synth", "C1", "C7", _V, (0, 29), "glass_pad", 88, 8),
    _f("phasing_strings", "synth", "C2", "C7", _V, (0, 35), "string_machine", 50, 8),
    _f("monster_strings", "synth", "C2", "C7", _V, (0, 101), "string_machine", 50, 8),
    _f("rough_strings", "synth", "C2", "C7", _V, (0, 88), "string_machine", 50, 8),
    _f("phasing_choir", "synth", "C2", "C6", _V, (0, 54), "choir", 52, 8),
    _f("synth_chorale", "synth", "C2", "C6", _V, (0, 24), "choir", 52, 8),
    # -- Vintage Dreams: bells, keys, hits, effects -----------------------------------
    _f("fm_bells", "perc", "C3", "C8", _V, (0, 0), "fm_bell", 98, 6),
    _f("techno_bells", "perc", "C3", "C8", _V, (0, 89), "fm_bell", 98, 6),
    _f("glass_bells", "perc", "C3", "C8", _V, (0, 26), "fm_bell", 98, 6),
    _f("delicate_bells", "perc", "C3", "C8", _V, (0, 119), "fm_bell", 98, 6),
    _f("cosmic_vibes", "perc", "C3", "C7", _V, (0, 32), "vibraphone", 11, 4),
    _f("aluminium_plate", "perc", "C2", "C6", _V, (0, 40), "metal_pipe", 113, 2),
    _f("metallic_clink", "perc", "C2", "C7", _V, (0, 47), "clank", 113, 2),
    _f("fm_clang", "perc", "C2", "C6", _V, (0, 55), "clank", 113, 2),
    _f("house_organ", "keys", "C1", "C7", _V, (0, 84), "fm_organ", 17, 8),
    _f("cheap_organ", "keys", "C2", "C7", _V, (0, 5), "fm_organ", 17, 8),
    _f("polysynth", "synth", "C2", "C7", _V, (0, 108), "synth_brass", 62, 6),
    _f("polysynth_hit", "synth", "C2", "C6", _V, (0, 105), "rave_stab", 81, 6),
    _f("sawtooth_hit", "synth", "C2", "C6", _V, (0, 93), "rave_stab", 81, 6),
    _f("wailing_hit", "synth", "C2", "C6", _V, (0, 45), "rave_stab", 81, 4),
    _f("blips", "synth", "C3", "C7", _V, (0, 75), "synth_pluck", 87, 4),
    _f("zips", "synth", "C3", "C7", _V, (0, 95), "zap", 127, 2),
    _f("laser_pops", "synth", "C3", "C7", _V, (0, 115), "zap", 127, 2),
    _f("space_warp", "synth", "C2", "C6", _V, (0, 39), "siren", 125, 2),
    _f("wind_down", "synth", "C2", "C6", _V, (0, 118), "zap", 127, 1),
    _f("wind_blast", "synth", "C2", "C6", _V, (0, 114), "noise_wall", 122, 2),
    _f("thunder", "synth", "C1", "C5", _V, (0, 98), "noise_wall", 122, 2),
    _f("warehouse", "perc", "C2", "C6", _V, (0, 92), "clank", 113, 4,
       ("Pitched industrial percussion.",)),
    # -- raw chip waves ----------------------------------------------------------------
    _f("chip_saw", "chip", "C1", "C8", "chip8", (0, 2), "saw_lead", 81, 1),
    _f("chip_square", "chip", "C1", "C8", "chip8", (0, 3), "square_lead", 80, 1),
    _f("chip_sine", "chip", "C1", "C8", "chip8", (0, 1), "sine_lead", 79, 1),
]})

#: The drums of a kit, by the name a `beat` lane uses, as General MIDI keys.
KIT_DRUMS: dict[str, int] = {
    "kick": 36, "snare": 38, "rim": 37, "clap": 39, "hat": 42, "pedal": 44,
    "open": 46, "tom_lo": 45, "tom_mid": 47, "tom_hi": 50, "ride": 51, "bell": 53,
    "crash": 49, "splash": 55, "tamb": 54, "cow": 56, "shaker": 70,
}


def is_kit(instrument: str) -> bool:
    return instrument.startswith("kit")

#: What a voice is for. Lint uses this: a melody voice that never states a motif
#: is a finding, and a bass voice wandering above the harmony is another.
ROLES = ("melody", "counter", "harmony", "bass", "pad", "ornament", "percussion")


def get_instrument(name: str) -> Instrument:
    try:
        return INSTRUMENTS[name]
    except KeyError:
        near = difflib.get_close_matches(name.lower(), INSTRUMENTS, n=3, cutoff=0.6)
        hint = f"; did you mean {near}?" if near else f"; have {sorted(INSTRUMENTS)}"
        raise KeyError(f"unknown instrument {name!r}{hint}") from None


def suggest_register(inst: Instrument, role: str) -> tuple[int, int]:
    """A sensible octave band for a voice, given what it is there to do."""
    lo, hi = inst.clo, inst.chi
    span = hi - lo
    if role == "melody":
        return lo + span // 3, hi
    if role == "bass":
        return lo, lo + max(12, span // 3)
    if role in ("harmony", "pad"):
        return lo + span // 6, lo + 2 * span // 3
    return lo, hi


def families() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in INSTRUMENTS.values():
        out.setdefault(i.family, []).append(i.name)
    return out


def describe_instruments(family: str | None = None) -> list[dict]:
    return [i.to_json() for i in INSTRUMENTS.values()
            if family is None or i.family == family]
