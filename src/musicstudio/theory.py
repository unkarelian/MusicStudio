"""Pitch, key, harmony and time -- the vocabulary a piece is written in.

Nothing above this module ever names a MIDI note number. A melody is a run of
scale degrees, a chord is a roman numeral, and neither becomes a pitch until
the key it sits in says so. That is what makes "out of key" unrepresentable
rather than merely discouraged, and what turns a modulation into a one-line
change instead of a rewrite.

Time works the same way. Durations are fractions of a whole note and positions
are ``bar:beat``, both resolved against the meter in force. An agent never adds
up ticks, so the rhythm cannot slide out from under the barline.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from fractions import Fraction

#: Ticks per quarter note. 480 divides evenly by 3, so triplets stay integers.
TPQ = 480
WHOLE = TPQ * 4

# --------------------------------------------------------------------------
# time
# --------------------------------------------------------------------------

NAMED_DURATIONS = {"w": "1/1", "h": "1/2", "q": "1/4", "e": "1/8", "s": "1/16"}

_DUR_RE = re.compile(r"^(\d+)(?:/(\d+))?(\.*)(t?)$")


def dur_fraction(dur: str) -> Fraction:
    """Duration as a fraction of a whole note.

    ``'1/4'`` quarter, ``'1/8.'`` dotted eighth, ``'1/8t'`` triplet eighth,
    ``'1/4+1/8'`` tied. ``w h q e s`` are aliases for the plain values. Dots
    stack (``'1/4..'``), and a trailing ``t`` takes two thirds.
    """
    if isinstance(dur, Fraction):
        return dur
    if not isinstance(dur, str):
        raise ValueError(f"duration must be a string like '1/8' or '1/4.', got {dur!r}")
    total = Fraction(0)
    for term in dur.replace(" ", "").split("+"):
        term = NAMED_DURATIONS.get(term, term)
        m = _DUR_RE.match(term)
        if not m:
            raise ValueError(
                f"bad duration {term!r}; want a fraction of a whole note like "
                f"'1/4', '1/8.', '1/8t', or an alias {sorted(NAMED_DURATIONS)}")
        num, den, dots, trip = m.group(1), m.group(2), m.group(3), m.group(4)
        v = Fraction(int(num), int(den) if den else 1)
        # A dot adds half of what came before it, so n dots multiply by 2 - 2^-n.
        if dots:
            v *= Fraction(2) - Fraction(1, 2 ** len(dots))
        if trip:
            v *= Fraction(2, 3)
        total += v
    if total <= 0:
        raise ValueError(f"duration {dur!r} is not positive")
    return total


def ticks(dur: str | int) -> int:
    """Duration in ticks. Ints pass through as raw ticks; strings are parsed."""
    if isinstance(dur, int) and not isinstance(dur, bool):
        return dur
    f = dur_fraction(dur) * WHOLE
    if f.denominator != 1:
        raise ValueError(f"duration {dur!r} is not a whole number of ticks at TPQ={TPQ}")
    return int(f)


def parse_meter(meter: str) -> tuple[int, int]:
    """``'4/4'`` -> ``(4, 4)``: that many beats of that note value per bar."""
    m = re.match(r"^(\d+)\s*/\s*(\d+)$", str(meter).strip())
    if not m:
        raise ValueError(f"bad meter {meter!r}; want something like '4/4', '6/8', '5/4'")
    return int(m.group(1)), int(m.group(2))


def beat_ticks(meter: str) -> int:
    """Ticks in one beat of this meter -- the denominator's note value."""
    _, den = parse_meter(meter)
    return WHOLE // den


def bar_ticks(meter: str) -> int:
    num, den = parse_meter(meter)
    return num * (WHOLE // den)


_POS_RE = re.compile(r"^(\d+)(?::(\d+(?:\.\d+)?|\d+/\d+))?$")


def parse_position(pos: str | int) -> tuple[int, Fraction]:
    """``'5:2.5'`` -> bar 5, beat 2.5. Both are 1-indexed, as musicians count.

    A bare ``'5'`` or ``5`` means bar 5 beat 1, which is what "at bar 5" means
    every time anyone says it.
    """
    if isinstance(pos, int) and not isinstance(pos, bool):
        return pos, Fraction(1)
    m = _POS_RE.match(str(pos).strip())
    if not m:
        raise ValueError(f"bad position {pos!r}; want 'bar' or 'bar:beat', e.g. '5' or '5:2.5'")
    bar = int(m.group(1))
    raw = m.group(2)
    beat = Fraction(raw) if raw and "/" in raw else Fraction(str(raw or 1))
    if bar < 1:
        raise ValueError(f"bar numbers start at 1, got {bar}")
    if beat < 1:
        raise ValueError(f"beat numbers start at 1, got {beat}")
    return bar, beat


def format_position(bar: int, beat: Fraction) -> str:
    b = float(beat)
    return f"{bar}:{int(b)}" if b.is_integer() else f"{bar}:{b:g}"


# --------------------------------------------------------------------------
# pitch
# --------------------------------------------------------------------------

_LETTER_PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

_PITCH_RE = re.compile(r"^([a-gA-G])([b#]*)(-?\d+)?$")

#: Tonics conventionally spelled with sharps, by circle of fifths. Every key not
#: listed takes flats -- so Bb minor rather than A# minor (5 flats beats 7 sharps)
#: but G# minor rather than Ab minor, which is how the repertoire actually spells
#: them. Purely cosmetic: the pitch classes are identical either way.
SHARP_TONICS_MAJOR = frozenset({0, 2, 4, 6, 7, 9, 11})
SHARP_TONICS_MINOR = frozenset({1, 4, 6, 8, 11})


def spell_tonic(pc: int, minorish: bool) -> str:
    table = SHARP_TONICS_MINOR if minorish else SHARP_TONICS_MAJOR
    return (SHARP_NAMES if pc % 12 in table else FLAT_NAMES)[pc % 12]


def parse_pitch(name: str | int) -> int:
    """``'C4'`` -> 60, ``'Bb2'`` -> 46. Octaveless names default to octave 4."""
    if isinstance(name, int) and not isinstance(name, bool):
        return name
    m = _PITCH_RE.match(str(name).strip())
    if not m:
        raise ValueError(f"bad pitch {name!r}; want a note name like 'C4', 'Bb2', 'F#5'")
    letter, acc, octv = m.group(1).lower(), m.group(2), m.group(3)
    pc = _LETTER_PC[letter] + acc.count("#") - acc.count("b")
    return 12 * ((int(octv) if octv is not None else 4) + 1) + pc


def pitch_name(pitch: int, *, flats: bool = False) -> str:
    names = FLAT_NAMES if flats else SHARP_NAMES
    return f"{names[pitch % 12]}{pitch // 12 - 1}"


def interval_name(semitones: int) -> str:
    base = ["P1", "m2", "M2", "m3", "M3", "P4", "TT", "P5", "m6", "M6", "m7", "M7"]
    n = abs(semitones)
    label = base[n % 12] + ("" if n < 12 else f"+{n // 12}oct")
    return label


# --------------------------------------------------------------------------
# scales and keys
# --------------------------------------------------------------------------

SCALES: dict[str, tuple[int, ...]] = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    "melodic_minor": (0, 2, 3, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
    "pentatonic_minor": (0, 3, 5, 7, 10),
    "blues": (0, 3, 5, 6, 7, 10),
    "whole_tone": (0, 2, 4, 6, 8, 10),
    "octatonic": (0, 2, 3, 5, 6, 8, 9, 11),
    "chromatic": tuple(range(12)),
}

SCALE_ALIASES = {
    "ionian": "major", "aeolian": "minor", "natural_minor": "minor",
    "maj": "major", "min": "minor", "m": "minor", "nat_minor": "minor",
    "harm_minor": "harmonic_minor", "mel_minor": "melodic_minor",
    "pent_major": "pentatonic_major", "pent_minor": "pentatonic_minor",
    "penta_major": "pentatonic_major", "penta_minor": "pentatonic_minor",
}


def scale_steps(scale: str) -> tuple[int, ...]:
    key = SCALE_ALIASES.get(scale.lower(), scale.lower())
    try:
        return SCALES[key]
    except KeyError:
        raise KeyError(f"unknown scale {scale!r}; have {sorted(SCALES)}") from None


@dataclass(frozen=True, slots=True)
class Key:
    """A tonic pitch class plus a scale. Degrees only mean something through one."""

    tonic: int
    scale: str = "major"

    @classmethod
    def parse(cls, text: str | Key) -> Key:
        """``'d minor'``, ``'Bb lydian'``, ``'F#'``, ``'a harmonic_minor'``."""
        if isinstance(text, Key):
            return text
        parts = str(text).replace("-", "_").split()
        if not parts:
            raise ValueError("empty key")
        # 'Cm' and 'F#m' are the common shorthand, so the tonic is taken greedily
        # and whatever is glued to it counts as the first word of the scale name.
        m = re.match(r"^([a-gA-G])([b#]*)(.*)$", parts[0])
        if not m:
            raise ValueError(f"bad key {text!r}; want e.g. 'd minor', 'Bb lydian', 'Cm'")
        letter, acc, glued = m.group(1).lower(), m.group(2), m.group(3)
        tonic = (_LETTER_PC[letter] + acc.count("#") - acc.count("b")) % 12
        scale = "_".join(([glued] if glued else []) + parts[1:]).lower() or "major"
        scale_steps(scale)  # validate now, so a typo fails at the key, not mid-render
        return cls(tonic, SCALE_ALIASES.get(scale, scale))

    @property
    def steps(self) -> tuple[int, ...]:
        return scale_steps(self.scale)

    @property
    def size(self) -> int:
        return len(self.steps)

    @property
    def minorish(self) -> bool:
        """Whether the scale's third is minor -- decides chord case and spelling."""
        return 3 in self.steps and 4 not in self.steps

    @property
    def name(self) -> str:
        return f"{spell_tonic(self.tonic, self.minorish)} {self.scale}"

    def step_semitones(self, index: int) -> int:
        """Semitones above the tonic for a diatonic index, unwrapped past the octave."""
        n = self.size
        octv, i = divmod(index, n)
        return self.steps[i] + 12 * octv

    def pitch(self, degree: int, alt: int = 0, octave: int = 4) -> int:
        """Degree 0 is the tonic. Degree 7 (in a 7-note scale) is the octave above."""
        return 12 * (octave + 1) + self.tonic + self.step_semitones(degree) + alt

    def degree_of(self, pitch: int) -> tuple[int, int, int]:
        """Inverse of :meth:`pitch`: ``(degree, alt, octave)``.

        Used for labelling a rendered note back into the language it was written
        in. Chromatic notes come back as the degree below plus ``alt=+1``, which
        is how a musician would name them.
        """
        rel = pitch - self.tonic - 12
        octv, within = divmod(rel, 12)
        steps = self.steps
        best = max(i for i in range(self.size) if steps[i] <= within)
        return best, within - steps[best], octv

    def transposed(self, semitones: int) -> Key:
        return Key((self.tonic + semitones) % 12, self.scale)


# --------------------------------------------------------------------------
# chords
# --------------------------------------------------------------------------

ROMAN_INDEX = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
_ROMAN_RE = re.compile(r"^([b#]*)(iii|ii|iv|vii|vi|v|i|III|II|IV|VII|VI|V|I)(.*)$")

#: Suffix -> what it does to the stacked-thirds default.
QUALITY_SUFFIXES = ("maj9", "maj7", "sus4", "sus2", "add9", "b13", "#11", "b9", "#9", "13", "11",
                    "9", "7", "6", "o7", "%", "o", "+", "5")

#: Altered tensions: semitones above the root. Each implies the seventh, as
#: ``9`` does -- ``V7b9`` and ``Vb9`` are the same chord.
ALTERED_TENSIONS = {"b9": 13, "#9": 15, "#11": 18, "b13": 20}


@dataclass(frozen=True, slots=True)
class Chord:
    """A roman numeral resolved against a key.

    ``intervals`` are semitones above the chord root, and ``root_offset`` is
    semitones above the tonic. Everything downstream asks for pitches in a
    register rather than reading these directly.
    """

    numeral: str
    root_offset: int
    intervals: tuple[int, ...]
    inversion: int = 0

    @property
    def size(self) -> int:
        return len(self.intervals)

    def pitch_classes(self, key: Key) -> tuple[int, ...]:
        return tuple(sorted({(key.tonic + self.root_offset + i) % 12 for i in self.intervals}))

    def root_pitch(self, key: Key, octave: int = 3) -> int:
        return 12 * (octave + 1) + key.tonic + self.root_offset

    def tone(self, key: Key, index: int, octave: int = 4) -> int:
        """Chord tone by index: 0 root, 1 third, 2 fifth, 3 seventh, wrapping up.

        This is what ``anchor='chord'`` motifs are realized through, so one
        arpeggio figure works over any progression without being rewritten.
        """
        n = self.size
        octv, i = divmod(index, n)
        return self.root_pitch(key, octave) + self.intervals[i] + 12 * octv

    def bass_pitch(self, key: Key, octave: int = 2) -> int:
        """The sounding bass note, honouring the inversion."""
        root = self.root_pitch(key, octave)
        if not self.inversion:
            return root
        p = root + self.intervals[self.inversion % self.size]
        return p - 12 if p - root >= 12 else p

    def voiced(self, key: Key, low: int, high: int) -> list[int]:
        """Every chord tone inside a register, low to high."""
        pcs = self.pitch_classes(key)
        return [p for p in range(low, high + 1) if p % 12 in pcs]

    def quality_name(self) -> str:
        iv = self.intervals
        third = iv[1] - iv[0] if len(iv) > 1 else None
        fifth = iv[2] - iv[0] if len(iv) > 2 else None
        if third == 3 and fifth == 6:
            return "diminished"
        if third == 4 and fifth == 8:
            return "augmented"
        if third == 5:
            return "sus4"
        if third == 2:
            return "sus2"
        if third == 3:
            return "minor"
        if third == 4:
            return "major"
        return "other"


def parse_chord(numeral: str, key: Key) -> Chord:
    """Resolve a roman numeral against a key. Memoized: both arguments are
    immutable, and a render asks the same question at every note."""
    return _parse_chord(str(numeral), key)


@functools.lru_cache(maxsize=4096)
def _parse_chord(numeral: str, key: Key) -> Chord:
    """Resolve a roman numeral against a key.

    Chords are built by stacking thirds *in the scale*, so ``ii`` comes out
    minor in a major key and ``V7`` gets a minor seventh without anyone saying
    so. Case and suffixes only apply corrections on top of that -- which is the
    one place agents reliably go wrong when spelling chords by hand.

    Understood: ``I ii V7 vii%7 bVII #ivo IVmaj7 Vsus4 i6 IVmaj9 V7b9 V7#9 IVmaj7#11 V7b13``,
    secondary chords
    as ``V/V``, and inversions as a trailing ``_1`` / ``_2`` (first, second).
    """
    text = str(numeral).strip()
    if not text:
        raise ValueError("empty chord")

    # Secondary function: V/V is 'the V of the key a fifth up'. Resolve the
    # right side first, make its root the temporary tonic, parse the left there.
    if "/" in text:
        left, right = text.split("/", 1)
        of = parse_chord(right, key)
        local = Key((key.tonic + of.root_offset) % 12,
                    "major" if of.quality_name() != "minor" else "minor")
        inner = parse_chord(left, local)
        return Chord(text, (of.root_offset + inner.root_offset) % 12,
                     inner.intervals, inner.inversion)

    inversion = 0
    if "_" in text:
        text, _, inv = text.partition("_")
        inversion = int(inv)

    m = _ROMAN_RE.match(text)
    if not m:
        raise ValueError(
            f"bad chord {numeral!r}; want a roman numeral like 'I', 'ii', 'V7', "
            f"'bVII', 'vii%7', 'V/V', optionally inverted as 'V_1'")
    accs, roman, suffix = m.group(1), m.group(2), m.group(3)
    if key.size != 7:
        raise ValueError(
            f"roman numerals need a 7-note scale, but the key is {key.name!r}. "
            f"Write the harmony in a diatonic key and give the melody its own "
            f"scale on the motif instead.")

    degree = ROMAN_INDEX[roman.lower()]
    chromatic = accs.count("#") - accs.count("b")
    root_offset = key.step_semitones(degree) + chromatic
    minor_numeral = roman.islower()

    if chromatic:
        # An altered root is off the scale, so there are no scale thirds to
        # stack. Fall back to the plain triad the numeral's case asks for.
        intervals = [0, 3 if minor_numeral else 4, 7]
    else:
        intervals = [key.step_semitones(degree + 2 * k) - key.step_semitones(degree)
                     for k in range(3)]
        # Case is a correction, not the source of truth.
        if minor_numeral and intervals[1] == 4:
            intervals[1] = 3
        elif not minor_numeral and intervals[1] == 3:
            intervals[1] = 4

    seventh = (10 if chromatic else
               key.step_semitones(degree + 6) - key.step_semitones(degree))

    tokens = _split_suffix(suffix, numeral)
    add_seventh = False
    for tok in tokens:
        if tok == "o":
            intervals[1:3] = [3, 6]
        elif tok == "o7":
            intervals[1:3] = [3, 6]
            seventh = 9
            add_seventh = True
        elif tok == "%":
            intervals[1:3] = [3, 6]
            seventh = 10
        elif tok == "+":
            intervals[1:3] = [4, 8]
        elif tok == "sus4":
            intervals[1] = 5
        elif tok == "sus2":
            intervals[1] = 2
        elif tok == "5":
            intervals = [intervals[0], intervals[2]]
    if add_seventh:
        intervals.append(seventh)
    for tok in tokens:
        if tok == "7":
            intervals.append(seventh)
        elif tok == "maj7":
            intervals.append(11)
        elif tok == "maj9":
            intervals += [11, 14]
        elif tok == "6":
            intervals.append(9)
        elif tok == "9":
            if seventh not in intervals and 11 not in intervals:
                intervals.append(seventh)
            intervals.append(14)
        elif tok == "add9":
            intervals.append(14)
        elif tok in ALTERED_TENSIONS:
            if seventh not in intervals and 11 not in intervals:
                intervals.append(seventh)
            intervals.append(ALTERED_TENSIONS[tok])
        elif tok == "11":
            if seventh not in intervals and 11 not in intervals:
                intervals.append(seventh)
            intervals += [14, 17]
        elif tok == "13":
            if seventh not in intervals and 11 not in intervals:
                intervals.append(seventh)
            intervals += [14, 21]

    return Chord(numeral, root_offset, tuple(dict.fromkeys(intervals)), inversion)


def _split_suffix(suffix: str, whole: str) -> list[str]:
    """Chop a suffix into known tokens, longest first so 'maj7' beats '7'."""
    out, i = [], 0
    while i < len(suffix):
        for tok in QUALITY_SUFFIXES:
            if suffix.startswith(tok, i):
                out.append(tok)
                i += len(tok)
                break
        else:
            raise ValueError(
                f"chord {whole!r}: don't understand {suffix[i:]!r}; "
                f"known suffixes are {list(QUALITY_SUFFIXES)}")
    return out


def chord_symbol(chord: Chord, key: Key) -> str:
    """A concert-pitch name for a numeral, for readbacks: ``bVII`` -> ``Bb``."""
    root = (key.tonic + chord.root_offset) % 12
    name = spell_tonic(root, key.minorish)
    q = chord.quality_name()
    tail = {"minor": "m", "diminished": "dim", "augmented": "aug",
            "sus4": "sus4", "sus2": "sus2", "major": "", "other": ""}[q]
    iv = chord.intervals
    if len(iv) > 3:
        seventh = iv[3] - iv[0]
        if q == "diminished":
            # o7 stacks another minor third; %7 keeps a minor seventh. Calling
            # both "dim7" loses the distinction that decides how they resolve.
            tail = "dim7" if seventh == 9 else "m7b5" if seventh == 10 else tail + "7"
        else:
            tail += ("maj7" if seventh == 11 else "7" if seventh == 10
                     else "6" if seventh == 9 else "")
    return name + tail


DYNAMICS = {"ppp": 20, "pp": 33, "p": 48, "mp": 62, "mf": 76, "f": 92, "ff": 108, "fff": 120}


def dynamic_velocity(name: str) -> int:
    try:
        return DYNAMICS[str(name).lower()]
    except KeyError:
        raise KeyError(f"unknown dynamic {name!r}; have {list(DYNAMICS)}") from None


def velocity_dynamic(vel: int) -> str:
    return min(DYNAMICS, key=lambda k: abs(DYNAMICS[k] - vel))


def ticks_to_dur(t: int) -> str:
    """Ticks back into the notation they were written in, for readbacks.

    Recognizes plain, dotted and triplet values before falling back to a raw
    fraction, so a round trip through the studio hands back ``'1/8.'`` rather
    than ``'3/16'``.
    """
    f = Fraction(t, WHOLE)
    n, d = f.numerator, f.denominator
    # Triplets first: a triplet of 1/b is 2/(3b), so recover b and check it is a
    # real note value. Otherwise an eighth triplet reads back as '1/12', which is
    # arithmetically the same and musically unreadable.
    if d % 3 == 0:
        b = Fraction(2, 3) / f
        if b.denominator == 1 and b > 0 and not (int(b) & (int(b) - 1)):
            return f"1/{int(b)}t"
    if n == 1:
        return f"1/{d}" if d != 1 else "1/1"
    if n == 3 and d % 2 == 0:
        return f"1/{d // 2}."      # 3/8 is a dotted quarter
    if n == 7 and d % 4 == 0:
        return f"1/{d // 4}.."
    return f"{n}/{d}"


def spell_pitch(pitch: int, key: Key) -> str:
    """A note name spelled the way the key would spell it: Bb in D minor, not A#."""
    names = FLAT_NAMES if (key.minorish or key.tonic in (5, 10, 3, 8, 1)) else SHARP_NAMES
    return f"{names[pitch % 12]}{pitch // 12 - 1}"
