"""Lyrics: from words to the sounds a singer makes, one syllable per note.

A singing voice needs to know, for every note, three things a lyric sheet does
not say: which consonants come *before* the note (they are sung ahead of the
beat, so the vowel lands on it), which vowel is held for the note's length, and
which consonants close it. This module turns text into exactly that.

Three ways in, tried in this order for each syllable:

**Phonemes, in brackets.** ``[s t r ey n jh]`` is taken literally. The escape
hatch, and the way to fix a word the other two get wrong.

**Romaji.** ``ka ze ga fu i te`` -- Japanese syllables are already phonetic, so
this needs no dictionary and cannot be mispronounced. ``n`` alone is the
syllabic nasal, a doubled consonant (``kitte``) is a held stop.

**English words**, through the CMU Pronouncing Dictionary when it is installed
(``ms lyrics install``; 3.6 MB, downloaded once, pinned by hash) and through a
small set of spelling rules when it is not. The rules are a fallback and sound
like one: English spelling does not determine English pronunciation, which is
why the dictionary exists. A word is split across notes with hyphens,
``lan-terns``, and its sounds are divided at the syllable boundaries.

``-`` holds the previous syllable's vowel across another note (a melisma) and
``_`` leaves a note to be sung on a plain "ah".

The phoneme set is ARPAbet's, lower-case, plus the five pure Japanese vowels
``a i u e o``, the moraic nasal ``N``, the flap ``rr`` and a glottal stop ``q``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

VOWELS = {"a", "i", "u", "e", "o",
          "aa", "ae", "ah", "ao", "eh", "er", "ih", "iy", "uh", "uw",
          "ay", "aw", "oy", "ey", "ow"}
#: Diphthongs are two targets: the first is held, the second arrives at the end.
DIPHTHONGS = {"ay": ("aa", "ih"), "aw": ("aa", "uh"), "oy": ("ao", "ih"),
              "ey": ("eh", "ih"), "ow": ("ao", "uh")}
#: Sounds that can carry a note by themselves when a syllable has no vowel.
SYLLABIC = {"N", "n", "m", "ng", "l"}
CONSONANTS = {"p", "b", "t", "d", "k", "g", "ch", "jh", "ts", "f", "v", "th", "dh",
              "s", "z", "sh", "zh", "hh", "m", "n", "ng", "N", "l", "r", "rr", "w",
              "y", "q"}
PHONEMES = VOWELS | CONSONANTS

#: Where a pronouncing dictionary is looked for. Per-user, like the SoundFonts.
DICT_DIR = Path("~/.local/share/musicstudio")
DICT_NAME = "cmudict.dict"
DICT_URL = ("https://raw.githubusercontent.com/cmusphinx/cmudict/"
            "74790861f652b15e4ac49015a90074ad62a27690/cmudict.dict")
DICT_SHA256 = "81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22"
LICENSE_URL = ("https://raw.githubusercontent.com/cmusphinx/cmudict/"
               "74790861f652b15e4ac49015a90074ad62a27690/LICENSE")
LICENSE_SHA256 = "bd4ce8e44170a5f9f481310ca85c51de3c4f851a65e679b40e603b143bd3542a"


@dataclass(frozen=True)
class Syllable:
    """What is sung on one note."""

    onset: tuple[str, ...] = ()
    #: The sound that is held: a vowel, or a syllabic consonant.
    nucleus: str = "aa"
    coda: tuple[str, ...] = ()
    text: str = ""
    #: A melisma: no new syllable, the previous vowel carries on at a new pitch.
    hold: bool = False
    #: The whole word this syllable belongs to, and which syllable of it this
    #: is -- what a voice bank needs to find the recording. Empty for sounds
    #: given in brackets, which no recording was asked for.
    word: str = ""
    index: int = 0
    count: int = 1

    def phonemes(self) -> str:
        return " ".join(self.onset + (self.nucleus,) + self.coda)

    def to_json(self) -> str:
        return "-" if self.hold else self.phonemes()

    @classmethod
    def from_json(cls, s: str, text: str = "") -> Syllable:
        if s == "-":
            return cls(hold=True, text="-")
        return _from_phonemes(s.split(), text or s)


def _from_phonemes(phones: list[str], text: str) -> Syllable:
    bad = [p for p in phones if p not in PHONEMES]
    if bad:
        raise ValueError(f"unknown phoneme(s) {bad} in {text!r}; the set is "
                         f"{sorted(PHONEMES)}")
    at = next((i for i, p in enumerate(phones) if p in VOWELS), None)
    if at is None:
        at = next((i for i, p in enumerate(phones) if p in SYLLABIC), None)
    if at is None:
        raise ValueError(f"{text!r} has nothing to hold a note on: a syllable needs "
                         f"a vowel (or a syllabic n, m, ng or l)")
    return Syllable(tuple(phones[:at]), phones[at], tuple(phones[at + 1:]), text)


# --------------------------------------------------------------------------
# romaji
# --------------------------------------------------------------------------

_ROMAJI_ONSETS = {
    "": (), "k": ("k",), "g": ("g",), "s": ("s",), "z": ("z",), "t": ("t",),
    "d": ("d",), "n": ("n",), "h": ("hh",), "b": ("b",), "p": ("p",), "m": ("m",),
    "y": ("y",), "r": ("rr",), "w": ("w",), "f": ("f",), "j": ("jh",), "v": ("v",),
    "sh": ("sh",), "ch": ("ch",), "ts": ("ts",),
    "ky": ("k", "y"), "gy": ("g", "y"), "ny": ("n", "y"), "hy": ("hh", "y"),
    "by": ("b", "y"), "py": ("p", "y"), "my": ("m", "y"), "ry": ("rr", "y"),
}
_ROMAJI_RE = re.compile(
    r"^(?P<gem>([kstpgdbzfhjm])(?=\2)|t(?=ch|ts))?"
    r"(?P<on>ky|gy|ny|hy|by|py|my|ry|sh|ch|ts|[kgsztdnhbpmyrwfjv])?"
    r"(?P<v>[aiueo])(?P<long>[aiueo])?(?P<n>n)?$")


def romaji(token: str) -> Syllable | None:
    """A Japanese syllable, or ``None`` if the token is not one."""
    t = token.lower()
    if t in ("n", "nn"):
        return Syllable((), "N", (), token)
    m = _ROMAJI_RE.match(t)
    if not m:
        return None
    onset = m.group("on") or ""
    gem = m.group("gem")
    # A doubled consonant ("kitte", "matcha") is a stop held before the syllable.
    if m.group("long") and m.group("long") != m.group("v"):
        return None                       # "kai" is two syllables, not a long vowel
    on = (("q",) if gem else ()) + _ROMAJI_ONSETS[onset]
    return Syllable(on, m.group("v"), ("N",) if m.group("n") else (), token)


# --------------------------------------------------------------------------
# English
# --------------------------------------------------------------------------

_dictionary: dict[str, list[str]] | None = None
#: ``word -> [pronunciation, ...]`` for the words the dictionary gives more
#: than one of *with a different stressed vowel* ("lives": l ih v z, l ay v z).
_alternates: dict[str, list[str]] = {}
_dictionary_from: tuple | None = None


#: Stressed-vowel pairs that are an accent, not another word ("water" with
#: the vowel of "caught" or of "cot"). An alternative that differs only by one
#: of these is not worth a warning.
_SAME_TO_A_SINGER = {frozenset(p) for p in (("ao", "aa"), ("aa", "ah"), ("ih", "iy"),
                                            ("uh", "uw"), ("ih", "ah"), ("eh", "ae"),
                                            ("eh", "ih"), ("eh", "ey"), ("ao", "uh"),
                                            ("ao", "ow"), ("ae", "aa"), ("ah", "uh"))}


def dictionary_path() -> Path:
    return DICT_DIR.expanduser() / DICT_NAME


def dictionary() -> dict[str, list[str]]:
    """The pronouncing dictionary, if installed: ``word -> ARPAbet, lower-case,
    stress removed``. Empty when it is not there."""
    global _dictionary, _dictionary_from, _alternates
    path = dictionary_path()
    try:
        st = path.stat()
        stamp = (path, st.st_mtime_ns, st.st_size)
    except OSError:
        stamp = (path, 0, 0)
    # Stamped by the file, not only its path: a dictionary installed by another
    # process (or after this one looked) must be seen.
    if _dictionary is not None and _dictionary_from == stamp:
        return _dictionary
    out: dict[str, list[str]] = {}
    stressed: dict[str, str] = {}
    others: dict[str, list[str]] = {}

    def strong(phones: list[str]) -> str:
        return next((ph[:-1].lower() for ph in phones if ph.endswith("1")), "")

    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line or line.startswith(";;;"):
                continue
            word, *phones = line.split("#")[0].split()
            plain = [re.sub(r"\d", "", ph).lower() for ph in phones]
            if "(" in word:
                # An alternative. The first pronunciation is the one sung, but
                # one that puts a *different vowel under the stress* is another
                # word to the ear ("lives" the verb and "lives" the noun), and
                # the writer has to be told there is a choice.
                base = word.split("(")[0].lower()
                first = out.get(base)
                # ...and only that vowel: "us" against "U.S." is not a choice
                # anyone is making, and neither is the Italian "fine".
                differs = (first is not None and len(first) == len(plain)
                           and sum(a != b for a, b in zip(first, plain)) == 1)
                if (differs and strong(phones) and stressed.get(base)
                        and strong(phones) != stressed[base]
                        and frozenset((strong(phones), stressed[base])) not in _SAME_TO_A_SINGER):
                    others.setdefault(base, [" ".join(out[base])]).append(" ".join(plain))
                continue
            out[word.lower()] = plain
            stressed[word.lower()] = strong(phones)
    _alternates = {w: ways for w, v in others.items()
                   if len(ways := list(dict.fromkeys(v))) > 1}
    _dictionary, _dictionary_from = out, stamp
    return out


def install_dictionary(*, force: bool = False, quiet: bool = False) -> Path:
    """Download the CMU Pronouncing Dictionary, pinned by hash, licence beside it."""
    from .soundfonts import _fetch, _progress, _write
    global _dictionary
    path = dictionary_path()
    if path.is_file() and not force:
        return path
    data = _fetch(DICT_URL, DICT_SHA256, None if quiet else _progress)
    _write(path.with_name("cmudict.LICENSE.txt"), _fetch(LICENSE_URL, LICENSE_SHA256))
    _write(path, data)
    _dictionary = None
    return path


#: Spelling rules, longest first: the fallback when there is no dictionary or
#: the word is not in it. Deliberately small. It gets common, regular words
#: roughly right and everything else roughly wrong, and says so in a warning.
_SPELLING = [
    ("tion", ["sh", "ah", "n"]), ("sion", ["zh", "ah", "n"]), ("ture", ["ch", "er"]),
    ("ough", ["ow"]), ("augh", ["ao"]), ("eigh", ["ey"]), ("igh", ["ay"]),
    ("tch", ["ch"]), ("dge", ["jh"]), ("sch", ["s", "k"]),
    ("ch", ["ch"]), ("sh", ["sh"]), ("th", ["th"]), ("ph", ["f"]), ("wh", ["w"]),
    ("ck", ["k"]), ("ng", ["ng"]), ("qu", ["k", "w"]), ("gh", []), ("kn", ["n"]),
    ("wr", ["r"]), ("ee", ["iy"]), ("ea", ["iy"]), ("oo", ["uw"]), ("ou", ["aw"]),
    ("ow", ["ow"]), ("oi", ["oy"]), ("oy", ["oy"]), ("ai", ["ey"]), ("ay", ["ey"]),
    ("au", ["ao"]), ("aw", ["ao"]), ("ie", ["iy"]), ("ei", ["ey"]), ("oa", ["ow"]),
    ("ue", ["uw"]), ("ar", ["aa", "r"]), ("er", ["er"]), ("ir", ["er"]),
    ("ur", ["er"]), ("or", ["ao", "r"]),
    ("a", ["ae"]), ("e", ["eh"]), ("i", ["ih"]), ("o", ["aa"]), ("u", ["ah"]),
    ("y", ["iy"]), ("b", ["b"]), ("c", ["k"]), ("d", ["d"]), ("f", ["f"]),
    ("g", ["g"]), ("h", ["hh"]), ("j", ["jh"]), ("k", ["k"]), ("l", ["l"]),
    ("m", ["m"]), ("n", ["n"]), ("p", ["p"]), ("q", ["k"]), ("r", ["r"]),
    ("s", ["s"]), ("t", ["t"]), ("v", ["v"]), ("w", ["w"]), ("x", ["k", "s"]),
    ("z", ["z"]),
]
_LONG = {"a": "ey", "e": "iy", "i": "ay", "o": "ow", "u": "uw"}


def spell_out(word: str) -> list[str]:
    """Letter-to-sound rules. A guess, used only when the dictionary cannot help."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return []
    # A final silent e lengthens the vowel before the consonant: "fire", "home".
    magic = len(w) >= 3 and w[-1] == "e" and w[-2] not in "aeiou" and w[-3] in "aeiou"
    if magic:
        w = w[:-1]
    out: list[str] = []
    i = 0
    while i < len(w):
        if magic and i == len(w) - 2 and w[i] in _LONG:
            out.append(_LONG[w[i]])
            i += 1
            continue
        if w[i] == "y" and i == 0:
            out.append("y")
            i += 1
            continue
        if w[i] == "c" and i + 1 < len(w) and w[i + 1] in "eiy":
            out.append("s")
            i += 1
            continue
        for letters, phones in _SPELLING:
            if w.startswith(letters, i):
                # A doubled consonant is said once.
                if not (len(letters) == 1 and out and phones and phones[-1] == out[-1]
                        and letters not in "aeiou" and i > 0 and w[i - 1] == letters):
                    out += phones
                i += len(letters)
                break
        else:
            i += 1
    return out


_ONSET_CLUSTERS = {
    ("p", "l"), ("p", "r"), ("b", "l"), ("b", "r"), ("t", "r"), ("d", "r"), ("k", "l"),
    ("k", "r"), ("g", "l"), ("g", "r"), ("f", "l"), ("f", "r"), ("th", "r"), ("sh", "r"),
    ("s", "p"), ("s", "t"), ("s", "k"), ("s", "m"), ("s", "n"), ("s", "l"), ("s", "w"),
    ("t", "w"), ("d", "w"), ("k", "w"), ("g", "w"), ("hh", "y"), ("k", "y"), ("f", "y"),
    ("m", "y"), ("b", "y"), ("p", "y"), ("v", "y"), ("n", "y"),
    ("s", "p", "l"), ("s", "p", "r"), ("s", "t", "r"), ("s", "k", "r"), ("s", "k", "w"),
}


def split_syllables(phones: list[str]) -> list[list[str]]:
    """Divide a word's phonemes at syllable boundaries.

    Each vowel is a syllable. Consonants between two vowels go to the *later*
    one as far as English allows a syllable to begin that way (``str`` yes,
    ``nt`` no), and the rest close the earlier one.
    """
    nuclei = [i for i, p in enumerate(phones) if p in VOWELS]
    if not nuclei:
        return [phones] if phones else []
    out: list[list[str]] = []
    start = 0
    for a, b in zip(nuclei, nuclei[1:]):
        between = phones[a + 1:b]
        keep = len(between)
        for k in range(len(between) + 1):
            tail = tuple(between[k:])
            if len(tail) <= 1 and (not tail or tail[0] != "ng") or tail in _ONSET_CLUSTERS:
                keep = k
                break
        out.append(phones[start:a + 1 + keep])
        start = a + 1 + keep
    out.append(phones[start:])
    return out


def _key(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower())


def english(word: str, said: dict | None = None) -> tuple[list[list[str]], bool]:
    """A word as syllables of phonemes, and whether its pronunciation is known
    (from ``said``, the pronunciations a lyric carries with it, or else from
    the dictionary) rather than guessed from spelling."""
    key = _key(word)
    known = str(said[key]).split() if said and said.get(key) else dictionary().get(key)
    phones = known if known is not None else spell_out(key)
    return split_syllables(list(phones)), known is not None


# --------------------------------------------------------------------------
# the whole lyric
# --------------------------------------------------------------------------

_BRACKET_RE = re.compile(r"\[([^\]]*)\]")


def _words(text: str, lang: str) -> tuple[str, list[str]]:
    """The resolved language and the plain English words of a lyric."""
    words = _BRACKET_RE.sub(" ", text.replace("|", " ")).split()
    parts = [p for w in words if w not in ("-", "_")
             for p in re.sub(r"[^A-Za-z'\-]", "", w).split("-") if p]
    if lang == "auto":
        lang = "ja" if parts and all(romaji(p) is not None for p in parts) else "en"
    if lang != "en":
        return lang, []
    return lang, [k for w in words if w not in ("-", "_")
                  for k in [_key(re.sub(r"[^A-Za-z'\-]", "", w).replace("-", ""))] if k]


def pronounce(text: str, lang: str = "auto", keep: dict | None = None) -> dict[str, str]:
    """``word -> phonemes`` for every English word of a lyric the dictionary
    knows. A lyrics op stores this beside its text, so the piece is sung the
    same on a machine with another dictionary, or none: how a word is said is
    decided when the line is written, not each time it is rendered. ``keep`` is
    what the op already stored or the writer chose, and it stands: a word in
    it is not looked up again."""
    known = dictionary()
    out: dict[str, str] = {}
    for key in _words(text, lang)[1]:
        if keep and keep.get(key):
            out[key] = str(keep[key])
        elif key in known:
            out[key] = " ".join(known[key])
    return out


def parse(text: str, lang: str = "auto",
          said: dict | None = None) -> tuple[list[Syllable], list[str]]:
    """Lyrics as one syllable per note, plus warnings about anything guessed.

    ``said`` is the op's stored pronunciations (see ``pronounce``); a word in
    it is read from there and the dictionary is not consulted.

    ``lang`` is ``'ja'`` (romaji), ``'en'`` or ``'auto'``, which reads the lyric
    as romaji if every word in it is a Japanese syllable and as English
    otherwise -- so ``to`` is "toh" in a Japanese line and "too" in an English one.
    """
    if lang not in ("auto", "ja", "en"):
        raise ValueError(f"lang must be 'auto', 'ja' or 'en', got {lang!r}")
    # Bracketed phonemes may contain spaces; protect them before splitting.
    literal: list[str] = []

    def stash(m: re.Match) -> str:
        literal.append(m.group(1))
        return f"\x00{len(literal) - 1}\x00"

    words = _BRACKET_RE.sub(stash, text.replace("|", " ")).split()
    plain = [w for w in words if "\x00" not in w and w not in ("-", "_")]
    parts = [p for w in plain for p in re.sub(r"[^A-Za-z'\-]", "", w).split("-") if p]
    if lang == "auto":
        lang = "ja" if parts and all(romaji(p) is not None for p in parts) else "en"

    out: list[Syllable] = []
    warnings: list[str] = []
    guessed: list[str] = []
    for word in words:
        if word == "-":
            out.append(Syllable(hold=True, text="-"))
            continue
        if word == "_":
            out.append(Syllable((), "aa", (), "_", word="ah"))
            continue
        if "\x00" in word:
            out.append(_from_phonemes(literal[int(word.strip("\x00"))].split(), word))
            continue
        clean = re.sub(r"[^A-Za-z'\-]", "", word)
        if not clean.strip("-'"):
            continue
        pieces = [p for p in clean.split("-") if p]
        if lang == "ja":
            for piece in pieces:
                syl = romaji(piece)
                if syl is None:
                    raise ValueError(
                        f"{piece!r} is not a romaji syllable. Write one syllable per "
                        f"note ('ka ze', 'kyo u', 'n'), put the sounds in brackets "
                        f"('[k ae t]'), or pass lang='en'")
                out.append(Syllable(syl.onset, syl.nucleus, syl.coda, syl.text,
                                    word=piece.lower()))
            continue
        syls, known = english("".join(pieces), said)
        if not known:
            guessed.append("".join(pieces))
        if len(pieces) > 1 and len(pieces) != len(syls):
            raise ValueError(
                f"{word!r} is written as {len(pieces)} syllables but is pronounced "
                f"as {len(syls)} ({' / '.join(' '.join(s) for s in syls)}); "
                f"hyphenate it to match, or give the sounds in brackets")
        if len(pieces) == 1 and len(syls) > 1:
            raise ValueError(
                f"{word!r} has {len(syls)} syllables "
                f"({' / '.join(' '.join(s) for s in syls)}) and one note: hyphenate "
                f"it ('{_suggest(pieces[0], len(syls))}'), one syllable per note, or "
                f"use '-' after it to hold a note")
        whole = re.sub(r"[^a-z']", "", "".join(pieces).lower())
        for i, (piece, phones) in enumerate(zip(pieces, syls)):
            syl = _from_phonemes(phones, piece)
            out.append(Syllable(syl.onset, syl.nucleus, syl.coda, piece,
                                word=whole, index=i, count=len(syls)))
    if said is None and lang == "en":
        # Asked only when the lyric carries no pronunciations yet, which is
        # when it is being written or checked: once the op has `said`, the
        # choice has been made and a render has nothing to ask.
        dictionary()
        twice = {k: _alternates[k] for k in dict.fromkeys(_words(text, "en")[1])
                 if k in _alternates}
        for word, ways in twice.items():
            warnings.append(
                f"{word!r} can be said {len(ways)} ways ("
                + " / ".join(ways) + f"); the first is sung. For another, pass "
                f"said={{'{word}': '{ways[1]}'}} on the lyrics op.")
    if guessed:
        where = ("the pronouncing dictionary is not installed (`ms lyrics install`), "
                 "and the lyric carries no pronunciation for them"
                 if not dictionary() else "not in the pronouncing dictionary")
        warnings.append(f"pronunciation guessed from spelling for {sorted(set(guessed))}: "
                        f"{where}. Put the sounds in brackets to be sure.")
    return out, warnings


def _suggest(word: str, n: int) -> str:
    """A hyphenation hint: split after each vowel group, as a starting point."""
    parts = re.findall(r"[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$)?", word.lower()) or [word]
    while len(parts) > n:
        parts[-2:] = [parts[-2] + parts[-1]]
    return "-".join(parts)
