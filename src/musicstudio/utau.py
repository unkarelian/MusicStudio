"""UTAU voicebanks: a folder of somebody's recordings, sung by the studio.

A UTAU voicebank is a directory of short recordings and an ``oto.ini`` that
says, for each *alias* (``か``, ``a か``, ``- か``), which stretch of which file
it is and where its landmarks are. Thousands exist, each under its author's
own terms. The studio bundles none, downloads none and lists none: you point
it at one you have (``ms utau add teto ~/Downloads/teto.zip``) and a singer
voice asks for it with ``bank="utau:teto"``. Its ``readme.txt`` and
``character.txt`` are the author's terms; ``ms utau show`` says where they are.

What an ``oto.ini`` line means, all in milliseconds from the start of the file
(``name.wav=alias,offset,consonant,cutoff,preutterance,overlap``):

``offset``
    where the alias starts.
``preutterance``
    how far after ``offset`` the vowel begins. **That point goes on the
    beat**, so everything before it is sung ahead of the note, in the time of
    the note before -- the same rule as every other singer here.
``overlap``
    how much of its beginning is crossfaded with the sound before.
``consonant``
    the stretch after ``offset`` that is never stretched; what lies beyond it
    is vowel, and is what lasts as long as the note does.
``cutoff``
    where it ends: counted back from the end of the file when positive, and
    forward from ``offset`` when negative.

The studio decides the notes, the syllables and the pitch; the bank gives the
sound. A recording is re-pitched by ``voicebank.psola`` (grains taken at the
recording's own pitch marks, laid at the score's period) and nothing in it is
resampled.

Japanese banks are what this reads: aliases in kana or romaji, recorded as
separate syllables (CV: ``か``) or as chains (VCV: ``a か``, which carries the
join from the vowel before and is preferred where the bank has it), with
``prefix.map`` choosing a recording by pitch in a bank that has several. A
lyric in romaji maps onto that directly. English is *approximated* through the
same syllables -- the vowel nearest each English vowel, a cluster's extra
consonants taken from the front of a recorded syllable -- so it is sung with a
Japanese accent, which is what such a bank sounds like in any editor. Banks
recorded with English aliases (arpasing, VCCV) are not read yet.

``ust`` goes the other way: one voice written out as a ``.ust`` file, which
UTAU, OpenUtau and other singing editors open, for rendering the line with a
voice the studio cannot run.
"""

from __future__ import annotations

import json
import math
import re
import shutil
import wave
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path

try:
    import numpy as np
except ImportError:                       # the core has no dependencies
    np = None

UTAU_DIR = Path("~/.local/share/musicstudio/utau")
PREFIX = "utau:"

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")


def is_utau(bank: str | None) -> bool:
    return bool(bank) and bank.lower().startswith(PREFIX)


def bank_name(bank: str) -> str:
    return bank[len(PREFIX):].strip().lower()


# --------------------------------------------------------------------------
# where banks are
# --------------------------------------------------------------------------

def _root() -> Path:
    return UTAU_DIR.expanduser()


def _registry() -> dict[str, str]:
    try:
        d = json.loads((_root() / "banks.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, str)}


def _check(name: str) -> str:
    name = name.strip().lower()
    if not _NAME_RE.match(name) or name == "banks":
        raise ValueError(f"{name!r} is not a bank name: lower-case letters, digits, "
                         f"'-' and '_' (it is what a voice writes after 'utau:')")
    return name


def find(name: str) -> Path | None:
    """The directory of the bank called ``name``, if there is one."""
    name = name.strip().lower()
    if not _NAME_RE.match(name):
        return None
    there = _registry().get(name)
    for p in ([Path(there)] if there else []) + [_root() / name]:
        if p.is_dir():
            return p
    return None


def banks() -> list[str]:
    root = _root()
    inside = [p.name for p in root.iterdir() if p.is_dir()] if root.is_dir() else []
    return sorted({n for n in list(_registry()) + inside if find(n) is not None})


def _unzip(archive: Path, dest: Path) -> None:
    """Unpack a voicebank, with its file names read as Japanese.

    A zip made on Japanese Windows stores names in Shift-JIS without saying
    so, and a plain unpack turns every kana file name into noise that no
    longer matches ``oto.ini``.
    """
    limit = 4 * 1024 ** 3
    total = 0
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = info.filename
            if not info.flag_bits & 0x800:
                try:
                    name = name.encode("cp437").decode("cp932")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
            parts = [p for p in name.replace("\\", "/").split("/") if p not in ("", ".")]
            if not parts or ".." in parts or info.is_dir():
                continue
            total += info.file_size
            if total > limit:
                raise ValueError(f"{archive.name} unpacks to more than 4 GB")
            out = dest.joinpath(*parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)


def add(name: str, path: str | Path, *, force: bool = False) -> dict:
    """Make a voicebank you have known to the studio as ``utau:<name>``.

    A directory is used where it is (nothing is copied); a ``.zip`` is unpacked
    into the studio's own folder. Nothing is fetched: the bank and its terms
    are yours to have got.
    """
    name = _check(name)
    src = Path(path).expanduser()
    root = _root()
    if find(name) is not None and not force:
        raise ValueError(f"there is already a bank called {name!r}; --force replaces it")
    reg = _registry()
    if src.is_dir():
        if not any(src.rglob("oto.ini")):
            raise ValueError(f"{src} has no oto.ini anywhere in it: not a UTAU voicebank")
        reg[name] = str(src.resolve())
    elif src.is_file() and zipfile.is_zipfile(src):
        dest = root / name
        part = root / f".{name}.part"
        shutil.rmtree(part, ignore_errors=True)
        part.mkdir(parents=True)
        try:
            _unzip(src, part)
            if not any(part.rglob("oto.ini")):
                raise ValueError(f"{src.name} has no oto.ini in it: not a UTAU voicebank")
            shutil.rmtree(dest, ignore_errors=True)
            part.rename(dest)
        finally:
            shutil.rmtree(part, ignore_errors=True)
        reg.pop(name, None)
    else:
        raise ValueError(f"{src} is neither a voicebank folder nor a .zip of one")
    root.mkdir(parents=True, exist_ok=True)
    (root / "banks.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False))
    _banks.pop(name, None)
    return describe(name)


def remove(name: str) -> None:
    """Forget a bank. One the studio unpacked is deleted; a folder of yours
    that was only pointed at is left alone."""
    name = _check(name)
    reg = _registry()
    reg.pop(name, None)
    root = _root()
    if (root / name).is_dir():
        shutil.rmtree(root / name)
    if root.is_dir():
        (root / "banks.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False))
    _banks.pop(name, None)


# --------------------------------------------------------------------------
# reading a bank
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    """One alias: a stretch of one file. Times are seconds from ``offset``."""

    alias: str
    path: Path
    offset: float
    consonant: float
    cutoff: float           # as written: ms, positive from the end of the file
    pre: float
    overlap: float


@dataclass
class UtauBank:
    name: str
    root: Path
    entries: dict[str, Entry]
    #: ``midi pitch -> (prefix, suffix)`` from prefix.map.
    by_pitch: dict[int, tuple[str, str]]
    missing: int = 0        # oto lines whose recording is not there
    info: dict | None = None

    def suffixes(self, pitch: float) -> list[tuple[str, str]]:
        got = self.by_pitch.get(int(round(pitch)))
        return ([got] if got and got != ("", "") else []) + [("", "")]


def _text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp932", errors="replace")


_TONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def _tone(name: str) -> int | None:
    m = re.match(r"^([A-G])(#?)(-?\d)$", name.strip())
    if not m:
        return None
    return _TONES[m.group(1)] + (1 if m.group(2) else 0) + 12 * (int(m.group(3)) + 1)


def _num(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return 0.0


def read_oto(path: Path) -> tuple[list[Entry], int]:
    """The entries of one ``oto.ini`` and how many lines name a missing file."""
    out: list[Entry] = []
    missing = 0
    here = path.parent
    for line in _text(path).splitlines():
        file, eq, rest = line.partition("=")
        if not eq or not file.strip():
            continue
        f = [x.strip() for x in rest.split(",")] + [""] * 6
        wav = here / file.strip()
        if not wav.is_file():
            missing += 1
            continue
        out.append(Entry(f[0] or wav.stem, wav, _num(f[1]) / 1000.0, _num(f[2]) / 1000.0,
                         _num(f[3]), _num(f[4]) / 1000.0, _num(f[5]) / 1000.0))
    return out, missing


_banks: dict[str, tuple[tuple, UtauBank]] = {}


def load(name: str) -> UtauBank | None:
    root = find(name)
    if root is None:
        return None
    otos = sorted(root.rglob("oto.ini"))
    stamp = tuple((str(p), p.stat().st_mtime_ns) for p in otos)
    hit = _banks.get(name)
    if hit is not None and hit[0] == stamp:
        return hit[1]
    entries: dict[str, Entry] = {}
    missing = 0
    for oto in otos:
        got, lost = read_oto(oto)
        missing += lost
        for e in got:
            entries.setdefault(e.alias, e)
    by_pitch: dict[int, tuple[str, str]] = {}
    for pm in sorted(root.rglob("prefix.map"))[:1]:
        for line in _text(pm).splitlines():
            f = line.split("\t")
            tone = _tone(f[0]) if f else None
            if tone is not None:
                by_pitch[tone] = (f[1] if len(f) > 1 else "", f[2].strip() if len(f) > 2 else "")
    info = {}
    for ch in sorted(root.rglob("character.txt"))[:1]:
        for line in _text(ch).splitlines():
            k, eq, v = line.partition("=")
            if eq:
                info[k.strip().lower()] = v.strip()
    bank = UtauBank(name, root, entries, by_pitch, missing, info)
    _banks[name] = (stamp, bank)
    return bank


def describe(name: str) -> dict:
    """What a bank is, for ``ms utau show``."""
    bank = load(name)
    if bank is None:
        raise KeyError(f"no UTAU bank called {name!r}; have {banks()}. "
                       f"`ms utau add {name} <folder or .zip>` adds one you have.")
    chained = sum(1 for a in bank.entries if _CHAIN_RE.match(a))
    kana = sum(1 for a in bank.entries if re.search(r"[ぁ-ゖァ-ヺ]", a))
    # Whatever the author wrote to be read: the terms are in there.
    terms = sorted(str(p) for p in bank.root.rglob("*.txt")
                   if len(p.relative_to(bank.root).parts) <= 2
                   and p.name.lower() not in ("install.txt", "character.txt"))
    can = sum(1 for k in _BASIC if _lookup(bank, k, "-", 60.0) is not None)
    return {"name": name, "path": str(bank.root), "author": (bank.info or {}).get("author", ""),
            "voice": (bank.info or {}).get("name", ""), "aliases": len(bank.entries),
            "chained": chained, "kana": kana, "pitches": len(set(bank.by_pitch.values())),
            "missing_files": bank.missing, "terms": terms,
            "syllables": can, "of": len(_BASIC)}


# --------------------------------------------------------------------------
# syllables to aliases
# --------------------------------------------------------------------------

_V = "aiueo"
#: consonant -> the five kana of its row (a i u e o).
_ROWS = {
    "": "あ い う え お", "k": "か き く け こ", "g": "が ぎ ぐ げ ご",
    "s": "さ すぃ す せ そ", "sh": "しゃ し しゅ しぇ しょ", "z": "ざ ずぃ ず ぜ ぞ",
    "jh": "じゃ じ じゅ じぇ じょ", "t": "た てぃ とぅ て と", "ch": "ちゃ ち ちゅ ちぇ ちょ",
    "ts": "つぁ つぃ つ つぇ つぉ", "d": "だ でぃ どぅ で ど", "n": "な に ぬ ね の",
    "hh": "は ひ ふ へ ほ", "f": "ふぁ ふぃ ふ ふぇ ふぉ", "b": "ば び ぶ べ ぼ",
    "p": "ぱ ぴ ぷ ぺ ぽ", "m": "ま み む め も", "y": "や い ゆ いぇ よ",
    "rr": "ら り る れ ろ", "w": "わ うぃ う うぇ を", "v": "ヴぁ ヴぃ ヴ ヴぇ ヴぉ",
    "ky": "きゃ き きゅ きぇ きょ", "gy": "ぎゃ ぎ ぎゅ ぎぇ ぎょ", "ny": "にゃ に にゅ にぇ にょ",
    "hy": "ひゃ ひ ひゅ ひぇ ひょ", "by": "びゃ び びゅ びぇ びょ", "py": "ぴゃ ぴ ぴゅ ぴぇ ぴょ",
    "my": "みゃ み みゅ みぇ みょ", "ry": "りゃ り りゅ りぇ りょ",
}
_KANA = {(c, v): row.split()[i] for c, row in _ROWS.items() for i, v in enumerate(_V)}
#: What to sing when the bank lacks a syllable: the nearest one most banks have.
_NEAR = {"すぃ": "し", "ずぃ": "じ", "てぃ": "ち", "とぅ": "つ", "でぃ": "じ", "どぅ": "ず",
         "しぇ": "せ", "じぇ": "ぜ", "ちぇ": "て", "つぁ": "さ", "つぃ": "ち", "つぇ": "せ",
         "つぉ": "そ", "ふぁ": "は", "ふぃ": "ひ", "ふぇ": "へ", "ふぉ": "ほ", "いぇ": "え",
         "うぃ": "い", "うぇ": "え", "を": "お", "ヴぁ": "ば", "ヴぃ": "び", "ヴ": "ぶ",
         "ヴぇ": "べ", "ヴぉ": "ぼ", "きぇ": "け", "ぎぇ": "げ", "にぇ": "ね", "ひぇ": "へ",
         "びぇ": "べ", "ぴぇ": "ぺ", "みぇ": "め", "りぇ": "れ"}
_ROMAJI_C = {"hh": "h", "jh": "j", "rr": "r"}
_ROMAJI_ALT = {"shi": "si", "chi": "ti", "tsu": "tu", "fu": "hu", "ji": "zi", "wo": "o",
               "sha": "sya", "shu": "syu", "sho": "syo", "cha": "tya", "chu": "tyu",
               "cho": "tyo", "ja": "zya", "ju": "zyu", "jo": "zyo"}
_BASIC = [(c, v) for c in ("", "k", "s", "t", "n", "hh", "m", "y", "rr", "w", "g", "z",
                           "d", "b", "p") for v in _V
          if (c, v) not in (("y", "i"), ("y", "e"), ("w", "i"), ("w", "u"), ("w", "e"),
                            ("s", "i"), ("t", "i"), ("t", "u"), ("z", "i"), ("d", "i"),
                            ("d", "u"))] + [("sh", "i"), ("ch", "i"), ("ts", "u"),
                                            ("jh", "i"), ("f", "u"), ("N", "")]
_CHAIN_RE = re.compile(r"^[aiueonN] \S")

#: English consonants a Japanese bank does not have, as the nearest it does.
_CONSONANT = {"l": "rr", "r": "rr", "th": "s", "dh": "z", "zh": "jh", "ng": "n", "N": "n"}
#: English vowels as (the vowel that is held, the one it closes on).
_VOWEL = {"a": ("a", ""), "i": ("i", ""), "u": ("u", ""), "e": ("e", ""), "o": ("o", ""),
          "aa": ("a", ""), "ae": ("a", ""), "ah": ("a", ""), "er": ("a", ""),
          "ao": ("o", ""), "ow": ("o", ""), "eh": ("e", ""), "ih": ("i", ""),
          "iy": ("i", ""), "uh": ("u", ""), "uw": ("u", ""), "ey": ("e", "i"),
          "ay": ("a", "i"), "aw": ("a", "u"), "oy": ("o", "i")}
#: The vowel a lone consonant is borrowed from: the one that colours it least.
_REST_VOWEL = {"t": "o", "d": "o", "ch": "i", "jh": "i", "sh": "i", "y": "u"}


def _romaji(key: tuple[str, str]) -> list[str]:
    c, v = key
    if c == "N":
        return ["n", "nn"]
    if c == "w" and v == "o":
        return ["wo", "o"]
    r = _ROMAJI_C.get(c, c) + v
    return [r] + ([_ROMAJI_ALT[r]] if r in _ROMAJI_ALT else [])


def _forms(key: tuple[str, str]) -> list[str]:
    """Every way a bank might write this syllable, best first."""
    if key[0] == "N":
        return ["ん", "ン"] + _romaji(key)
    kana = _KANA.get(key)
    if kana is None:
        return []
    out = [kana] + _romaji(key)
    if kana in _NEAR:
        out.append(_NEAR[kana])
    return out


def _lookup(bank: UtauBank, key: tuple[str, str], before: str, pitch: float,
            *, chained: bool = True) -> Entry | None:
    """The recording for syllable ``key`` after the sound ``before`` (a vowel
    letter, ``n``, or ``-`` for silence or a consonant)."""
    for form in _forms(key):
        tries = []
        if before != "-" and chained:
            tries.append(f"{before} {form}")
        if before == "-":
            tries.append(f"- {form}")
        tries.append(form)
        if before != "-":
            tries.append(f"- {form}")
        for pre, suf in bank.suffixes(pitch):
            for t in tries:
                e = bank.entries.get(f"{pre}{t}{suf}")
                if e is not None:
                    return e
    return None


@dataclass
class _Event:
    """One stretch of one recording, placed in the phrase."""

    entry: Entry
    on: float               # when its vowel (its preutterance point) sounds
    limit: float            # the latest it may still be sounding
    gain: float
    #: Only the part before the vowel: a consonant on its own.
    bare: bool = False
    lead: float = 0.0       # filled in by the layout: seconds before ``on``
    ovl: float = 0.0


def _syllable_keys(s) -> tuple[list[str], tuple[str, str] | None, list, list[str]]:
    """``(extra opening consonants, the syllable, what it closes on, closing
    consonants)`` for one sung note."""
    onset = [_CONSONANT.get(c, c) for c in s.onset if c != "q"]
    raw = [c for c in s.coda if c != "q"]
    # A syllable that closes on "n" closes on the syllabic nasal, which a
    # Japanese bank has as a sound of its own.
    nasal = 0
    while nasal < len(raw) and raw[nasal] in ("N", "n", "ng"):
        nasal += 1
    coda = [_CONSONANT.get(c, c) for c in raw[nasal:]]
    if s.nucleus in ("N", "n", "m", "ng"):
        return onset, ("N", ""), [], coda
    if s.nucleus == "l":
        vowel, close = "u", ""
    else:
        vowel, close = _VOWEL.get(s.nucleus, ("a", ""))
    tails: list[tuple[str, str]] = ([("", close)] if close else []) + [("N", "")] * min(nasal, 1)
    c = ""
    if onset:
        c = onset.pop()
        if c == "y" and onset and onset[-1] + "y" in _ROWS:
            c = onset.pop() + "y"
    if (c, vowel) not in _KANA:
        c = ""
    return onset, (c, vowel), tails, coda


def _sound_of(key: tuple[str, str]) -> str:
    return "n" if key[0] == "N" else key[1]


# --------------------------------------------------------------------------
# recordings
# --------------------------------------------------------------------------

def _read_wav(path: Path) -> "np.ndarray":
    from .vocal import SR
    with wave.open(str(path), "rb") as w:
        width, ch, rate = w.getsampwidth(), w.getnchannels(), w.getframerate()
        raw = w.readframes(w.getnframes())
    if width == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        x = ((b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)) << 8 >> 8) / 8388608.0
    elif width == 4:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    elif width == 1:
        x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        raise ValueError(f"{path.name}: {8 * width}-bit audio is not read")
    x = x[:len(x) // ch * ch].reshape(-1, ch).mean(axis=1)
    if rate != SR and len(x) > 1:
        # Band-limited: the spectrum is cut (or padded) and transformed back.
        n = int(round(len(x) * SR / rate))
        spec = np.fft.rfft(x)
        m = n // 2 + 1
        spec = spec[:m] if m <= len(spec) else np.concatenate([spec, np.zeros(m - len(spec))])
        x = np.fft.irfft(spec, n) * (n / len(x))
    return x


_units: dict[tuple, tuple] = {}


def _unit(e: Entry):
    """``(Unit, start, pre, fixed, end, level)``: the entry's recording ready
    for PSOLA, and its landmarks as sample positions in it."""
    from .vocal import SR
    from .voicebank import FRAME, Unit, voicing
    key = (str(e.path), e.path.stat().st_mtime_ns, e.offset, e.cutoff)
    hit = _units.get(key)
    if hit is not None:
        return hit
    x = _read_wav(e.path)
    a = int(e.offset * SR)
    b = len(x) - int(e.cutoff / 1000.0 * SR) if e.cutoff >= 0 else a + int(-e.cutoff / 1000.0 * SR)
    a = max(0, min(a, len(x) - 1))
    b = max(a + 1, min(b, len(x)))
    pad = FRAME // 2
    seg = np.concatenate([np.zeros(pad), x[a:b], np.zeros(FRAME)])
    d = voicing(seg, low=75.0, high=800.0)
    start, end = pad, pad + (b - a)
    pre = min(end - 1, start + int(max(0.0, e.pre) * SR))
    fixed = min(end - 1, max(pre, start + int(max(0.0, e.consonant) * SR)))
    body = seg[fixed:end] if end - fixed > 256 else seg[pre:end]
    level = float(np.sqrt((body ** 2).mean())) if len(body) else 0.0
    got = (Unit(seg, d["marks"], d["voiced"], d["period"], start, end), start, pre, fixed,
           end, max(level, 1e-4))
    if len(_units) > 4000:
        _units.clear()
    _units[key] = got
    return got


# --------------------------------------------------------------------------
# singing a phrase
# --------------------------------------------------------------------------

def render_phrase(sung, bank: UtauBank, singer, seed: int,
                  lost: set | None = None) -> "tuple[np.ndarray, float]":
    """Sing one phrase from the bank. Returns ``(samples, start time)``.
    Syllables the bank has no recording for are added to ``lost``."""
    from .vocal import SR
    from .voicebank import LEVEL, VOWEL_RMS, _stretch, psola
    rng = np.random.default_rng(seed)
    t0 = max(0.0, sung[0].start - 0.6)
    total = sung[-1].end - t0 + 0.5
    n = int(total * SR)
    out = np.zeros(n)

    # -- pitch: the score's, as every singer here has it -------------------------
    t = np.arange(n) / SR + t0
    midi = np.full(n, float(sung[0].pitch))
    for i, s in enumerate(sung[1:], 1):
        x = np.clip((t - (s.start - 0.012)) / (singer.glide / 4.0), -40.0, 40.0)
        midi += (s.pitch - sung[i - 1].pitch) / (1.0 + np.exp(-x))
    cents = -30.0 * np.exp(-np.maximum(t - sung[0].start, 0.0) / 0.05) * (t >= sung[0].start - 0.05)
    for s in sung:
        if s.end - s.start < 0.36:
            continue
        rate = singer.vibrato_rate * rng.uniform(0.95, 1.05)
        rise = np.clip((t - s.start - 0.2) / 0.3, 0.0, 1.0) * (t < s.end)
        cents += singer.vibrato * rise * np.sin(2 * np.pi * rate * (t - s.start)
                                                + rng.uniform(0, 2 * np.pi))
    f0 = 440.0 * 2.0 ** ((midi - 69.0) / 12.0 + cents / 1200.0)

    # -- which recordings, and when ------------------------------------------------
    # A held note (a melisma) is the syllable before it going on: one recording
    # across both, with the pitch moving under it.
    spans: list[list] = []
    for s in sung:
        if s.hold and spans and s.start - spans[-1][1] < 0.05:
            spans[-1][1] = s.end
        else:
            spans.append([s, s.end])

    events: list[_Event] = []
    before = "-"
    for j, (s, end) in enumerate(spans):
        if j and s.start - spans[j - 1][1] > 0.12:
            before = "-"
        gain = (max(1, min(127, s.velocity)) / 127.0) ** 1.2
        extra, key, tails, coda = _syllable_keys(s)
        if s.hold:
            # A phrase that begins on a held note: the vowel, from nothing.
            extra, key, tails, coda = [], ("", "a"), [], []
        length = end - s.start

        def bare(c: str, pitch: float) -> Entry | None:
            for v in (_REST_VOWEL.get(c, "u"), "u", "a"):
                if (c, v) in _KANA:
                    e = _lookup(bank, (c, v), "-", pitch, chained=False)
                    if e is not None and not _CHAIN_RE.match(e.alias) and e.pre > 0.012:
                        return e
            return None

        openers = [e for e in (bare(c, s.pitch) for c in extra) if e is not None]
        main = _lookup(bank, key, "-" if openers else before, s.pitch)
        if main is None and key[0] not in ("", "N"):
            main = _lookup(bank, ("", key[1]), before, s.pitch)     # at least the vowel
            if lost is not None:
                lost.add(_KANA.get(key, "".join(key)))
        if main is None:
            if lost is not None:
                lost.add("ん" if key[0] == "N" else _KANA.get(key, "".join(key)))
            before = "-"
            continue
        closers = [e for e in (bare(c, s.pitch) for c in coda) if e is not None]
        # What closes the note takes its time from the end of the note.
        slots = [min(0.13, length * 0.3)] * len(tails) + \
                [min(c.pre, 0.12) for c in closers]
        if sum(slots) > length * 0.5:
            slots = [x * length * 0.5 / sum(slots) for x in slots]
        for e in openers:
            events.append(_Event(e, s.start, s.start, gain, bare=True))
        events.append(_Event(main, s.start, end + 0.05, gain))
        at = end - sum(slots)
        prev = _sound_of(key)
        for k, tk in enumerate(tails):
            e = _lookup(bank, tk, prev, s.pitch)
            if e is not None:
                # A chained recording begins in the vowel before; a separate
                # one begins at its own beginning. Either way it arrives at
                # the start of its slot.
                events.append(_Event(e, at + max(0.0, e.pre - e.overlap), end + 0.05, gain))
                prev = _sound_of(tk)
            at += slots[k]
        for k, e in enumerate(closers):
            events.append(_Event(e, at + slots[len(tails) + k], end + 0.08, gain, bare=True))
            at += slots[len(tails) + k]
            prev = "-"
        before = prev

    # -- layout: each sound gives way as the next begins ------------------------------
    # Lead-ins are sung ahead of the beat at the speed they were recorded; when
    # there is no room the lead-in is hurried, never the beat moved.
    written = [ev.on for ev in events]
    starts: list[float] = []
    for i in range(len(events) - 1, -1, -1):
        ev = events[i]
        if ev.bare and i + 1 < len(events) and starts[0] <= ev.on + 1e-6:
            ev.on = starts[0]              # a lone consonant ends where the next sound begins
        earlier = [events[j].on for j in range(i) if written[j] < written[i] - 1e-3]
        room = max(0.012, (ev.on - earlier[-1]) * 0.6) if earlier else ev.on - t0
        lead = max(0.0, min(ev.entry.pre, room))
        ev.lead = lead
        scale = lead / ev.entry.pre if ev.entry.pre > 1e-6 else 1.0
        ev.ovl = max(0.004, min(ev.entry.overlap * scale, lead if lead > 0.004 else 0.004))
        starts.insert(0, ev.on - lead)
    # Sounds are sung one after another: none begins before the one before it.
    for i in range(1, len(events)):
        if starts[i] < starts[i - 1] + 0.008:
            starts[i] = starts[i - 1] + 0.008
            events[i].lead = max(0.0, events[i].on - starts[i])

    for i, ev in enumerate(events):
        unit, start, pre, fixed, end, level = _unit(ev.entry)
        begin = starts[i]
        if i + 1 < len(events) and starts[i + 1] <= ev.limit:
            stop = starts[i + 1] + events[i + 1].ovl
            fade = events[i + 1].ovl
        else:
            stop, fade = ev.limit, 0.05
        lead_n = int(round(ev.lead * SR))
        path = [np.linspace(start, pre, lead_n, endpoint=False)] if lead_n > 0 else []
        if not ev.bare:
            room = int(round((stop - ev.on) * SR))
            hard = min(fixed - pre, max(0, room))
            if hard > 0:
                path.append(np.arange(hard, dtype=np.float64) + pre)
            room -= hard
            if room > 0:
                a, b = (fixed, end) if end - fixed > 64 else (max(start, end - 64), end)
                if room <= b - a:
                    path.append(np.arange(room, dtype=np.float64) + a)
                else:
                    path.append(_stretch(a, b, room))
        elif not path:
            continue
        if not path:
            continue
        p = np.concatenate(path)
        k = int(round((begin - t0) * SR))
        if k < 0:
            p, k = p[-k:], 0
        m = min(len(p), n - k)
        if m <= 16:
            continue
        sig = psola(unit, p[:m], f0[k:k + m]) * (ev.gain * VOWEL_RMS / level)
        fi = max(8, min(int(ev.ovl * SR), m // 2))
        fo = max(8, min(int(fade * SR), m // 2))
        sig[:fi] *= np.linspace(0.0, 1.0, fi)
        sig[-fo:] *= np.linspace(1.0, 0.0, fo)
        out[k:k + m] += sig

    return out * (LEVEL * singer.level / VOWEL_RMS), t0


def voice_stems(piece, notes, to_sec, total: int, pans: dict[str, float], *,
                strict: bool = False) -> dict[str, tuple]:
    """``{voice: (left, right)}`` for every singer whose ``bank`` is
    ``utau:<name>`` and whose bank is here. A bank that is not is left to the
    formant singer with a warning, or raises under ``strict``."""
    import warnings
    from .vocal import SINGERS, SR, phrases, plan
    out: dict[str, tuple] = {}
    for v in piece.voices:
        if v.muted or not is_utau(v.bank) or v.instrument not in SINGERS:
            continue
        mine = [n for n in notes if n.voice == v.name and not n.percussive]
        if not mine:
            continue
        name = bank_name(v.bank)
        bank = load(name)
        if bank is None or not bank.entries:
            why = (f"there is no UTAU bank called {name!r}" if bank is None
                   else f"the UTAU bank {name!r} has no recordings that could be read")
            if strict:
                raise RuntimeError(f"voice {v.name!r}: {why}")
            warnings.warn(f"voice {v.name!r} falls back to the synthesized singer: {why}. "
                          f"`ms utau add {name} <folder or .zip>` adds one you have.",
                          stacklevel=2)
            continue
        singer = SINGERS[v.instrument]
        mono = np.zeros(total)
        lost: set[str] = set()
        for group in phrases(plan(mine, to_sec)):
            seed = zlib.crc32(f"{v.name}|{group[0].start:.4f}|{group[0].pitch}".encode())
            sig, t0 = render_phrase(group, bank, singer, seed, lost)
            a = int(t0 * SR)
            k = min(len(sig), total - a)
            if k > 0:
                mono[a:a + k] += sig[:k]
        if lost:
            warnings.warn(f"voice {v.name!r}: the UTAU bank {name!r} has no recording for "
                          f"{' '.join(sorted(lost))}; the nearest it has was sung instead",
                          stacklevel=2)
        theta = (max(-1.0, min(1.0, pans.get(v.name, 0.0))) + 1.0) * math.pi / 4
        out[v.name] = (mono * math.cos(theta) * math.sqrt(2),
                       mono * math.sin(theta) * math.sqrt(2))
    return out


# --------------------------------------------------------------------------
# writing a line out for another editor
# --------------------------------------------------------------------------

def kana_of(sung: str) -> list[str]:
    """One sung syllable (a note's ``sung`` text) as the kana an editor would
    be given: the syllable, then anything it closes on."""
    from .lyrics import Syllable
    syl = Syllable.from_json(sung) if sung else Syllable((), "aa", (), "")
    if syl.hold:
        return ["-"]
    extra, key, tails, coda = _syllable_keys(syl)
    main = "ん" if key[0] == "N" else _KANA.get(key, "あ")
    return [main] + ["ん" if k[0] == "N" else _KANA[k] for k in tails]


def ust(piece, notes, voice: str) -> str:
    """One voice as the text of a ``.ust`` file (UTAU's score format).

    Ticks are the studio's own (480 to the quarter note), so the rhythm is
    exact. A syllable that closes on ``n`` or on a second vowel is written as
    two notes, the second taking the last part of the first; a held note
    repeats its vowel, which is how a melisma is written for a voicebank.
    The gap an articulation leaves between two notes (up to a sixteenth) is
    given to the first, so a line is not written as a string of tiny rests.
    Pitches are equal-tempered: a fraction of a semitone on a note is dropped.
    """
    mine = sorted((n for n in notes if n.voice == voice and not n.percussive),
                  key=lambda n: (n.start, n.pitch))
    if not mine:
        raise ValueError(f"voice {voice!r} plays nothing to write out")
    tempo = dict(piece.tempo_map())
    marks = sorted(tempo)
    lines = ["[#VERSION]", "UST Version1.2", "[#SETTING]",
             f"Tempo={float(tempo[marks[0]]):.2f}", "Tracks=1",
             f"ProjectName={piece.name}", "Mode2=True"]
    out: list[tuple[int, int, str, int]] = []           # start, length, lyric, pitch
    cursor = 0
    vowel = "あ"
    for n in mine:
        if n.start < cursor:
            continue                                      # a singer has one mouth
        if out and 0 < n.start - cursor <= 120:
            # The space a player leaves between notes is not a rest: in a
            # voicebank editor a rest is a breath and a new attack.
            a, length, lyric, pitch = out[-1]
            out[-1] = (a, length + n.start - cursor, lyric, pitch)
        elif n.start > cursor:
            out.append((cursor, n.start - cursor, "R", 60))
        parts = kana_of(n.sung)
        if parts == ["-"]:
            parts = [vowel]
        dur = n.dur
        tail = min(dur // 3, 120) if len(parts) > 1 else 0
        tail -= tail % 5
        out.append((n.start, dur - tail * (len(parts) - 1), parts[0], n.pitch))
        at = n.start + dur - tail * (len(parts) - 1)
        for p in parts[1:]:
            if tail > 0:
                out.append((at, tail, p, n.pitch))
                at += tail
        last = parts[-1] if tail > 0 or len(parts) == 1 else parts[0]
        vowel = last if last == "ん" else _KANA[("", _vowel_of(last))]
        cursor = n.start + dur
    said = None
    for i, (start, length, lyric, pitch) in enumerate(out):
        lines += [f"[#{i:04d}]", f"Length={length}", f"Lyric={lyric}", f"NoteNum={pitch}"]
        now = tempo[max((m for m in marks if m <= start), default=marks[0])]
        if said is not None and abs(now - said) > 1e-6:
            lines.append(f"Tempo={float(now):.2f}")
        said = now
        lines += ["PreUtterance=", "Intensity=100", "Modulation=0"]
    lines.append("[#TRACKEND]")
    return "\r\n".join(lines) + "\r\n"


def _vowel_of(kana: str) -> str:
    for (c, v), k in _KANA.items():
        if k == kana:
            return v
    return "a"
