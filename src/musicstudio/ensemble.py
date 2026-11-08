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
                "program": self.program, "notes": list(self.notes)}


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
    # -- tuned percussion -------------------------------------------------
    _i("glockenspiel", "perc", "F5", "C8", "C6", "C8", 9, polyphony=4, timbre="bell"),
    _i("vibraphone", "perc", "F3", "F6", "F3", "F6", 11, polyphony=4, timbre="bell"),
    _i("marimba", "perc", "C2", "C7", "C3", "C6", 12, polyphony=4, timbre="pluck"),
    _i("timpani", "perc", "D2", "A3", "F2", "F3", 47, polyphony=2, timbre="struck",
       notes=("Tuned to two or three pitches per cue; retuning takes bars, not beats.",)),
    # -- synth ------------------------------------------------------------
    _i("synth_pad", "synth", "C1", "C7", "C2", "C6", 89, polyphony=8, timbre="pad"),
    _i("synth_lead", "synth", "C2", "C7", "C4", "C6", 81, polyphony=1, timbre="saw"),
    _i("synth_bass", "synth", "C0", "C4", "C1", "C3", 38, polyphony=1, timbre="saw"),
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
    _i("taiko", "drums", "A1", "A1", "A1", "A1", 0, timbre="noise", percussive=True, drum_key=117),
    _i("tambourine", "drums", "F#2", "F#2", "F#2", "F#2", 0, timbre="noise", percussive=True, drum_key=54),
    _i("noise", "chip", "D1", "D1", "D1", "D1", 0, timbre="noise", percussive=True, drum_key=38),
]}

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
