"""A voice bank: a recorded voice, complete on its own, that sings any lyric.

`vocal.py` makes a voice from a table of formants, and sounds like a table of
formants. A voice bank is a real one, built the way UTAU and its descendants
build theirs. A fixed list of 271 common one-syllable words is recorded once
(`data/voice_corpus.txt` -- chosen so that every join between a consonant and a
vowel that those words use is in it somewhere). Each recording is cut in two at
the middle of its vowel:

    "cat"  ->  k-ae  (the consonant, and the mouth opening into the vowel)
               ae-t  (the vowel closing into the consonant)

and those halves are the units. Any syllable of any lyric is then assembled
from them -- ``k ae t`` is those two; ``s t r ey n jh`` is an ``s`` and a ``t``
borrowed from other words, then ``r-ey``, then ``ey-n``, then a ``jh`` -- so
once the bank exists, nothing else is ever recorded. You arrange the notes and
the words; the voice is already there.

**The recording is what you hear.** Unvoiced sounds (``s``, ``t``, ``k``) are
played back exactly as recorded. Voiced sound is re-pitched by PSOLA: the
recording is cut at each closing of the vocal folds into two-period grains, and
the grains are laid down again at the spacing of the note being sung. The
shape of each grain -- the vowel, the speaker -- is untouched; only how often
they come changes. A held note dwells in the steady middle of the vowel,
moving back and forth through a few hundredths of a second of it so that no
single grain repeats into a buzz.

**The vowel lands on the beat.** Every unit knows where its vowel begins. The
consonants before that point are placed ahead of the note; what follows a
vowel closes its own note.

The recordings come from a text-to-speech voice through a paid service, under
the user's own account, so they live in ``~/.cache/musicstudio/voicebank`` and
never in a piece or a repository. A piece only *names* a bank. Where the bank
is missing -- in CI, on another machine -- the voice falls back to the
synthesized singer and says so.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import wave
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .lyrics import VOWELS
from .vocal import SR, Sung

CACHE_DIR = Path("~/.cache/musicstudio/voicebank")
ENDPOINT = "https://openrouter.ai/api/v1/audio/speech"
DEFAULT_MODEL = "elevenlabs/eleven-v4"
KEY_ENV = "OPENROUTER_API_KEY"
CORPUS = Path(__file__).parent / "data" / "voice_corpus.txt"

#: Output scale, set so a sung mezzo-forte vowel matches the synthesized singer.
LEVEL = 0.31
#: Consonants are sung a little hotter than they were spoken. In speech they
#: are 10-20 dB under the vowels, and a sung vowel is longer and louder still.
CONSONANT_LIFT = 1.5
#: The loudness every unit's vowel is brought to when the bank is loaded.
VOWEL_RMS = 0.1

#: Sounds the corpus does not contain as such, and what stands in for them.
#: Romaji's pure vowels map to their English neighbours; a flap is close to a
#: quick "d"; the moraic nasal is an "n".
ALIASES = {"a": "aa", "i": "iy", "u": "uw", "e": "eh", "o": "ow", "rr": "d", "N": "n"}
#: When a join was never recorded, the vowel most like the one wanted.
NEAR_VOWEL = {
    "aa": ("ah", "ao", "ae"), "ae": ("eh", "aa", "ah"), "ah": ("aa", "uh", "er"),
    "ao": ("aa", "ow", "ah"), "aw": ("aa", "ae", "ah"), "ay": ("aa", "ah", "ae"),
    "eh": ("ae", "ih", "ey"), "er": ("ah", "uh", "eh"), "ey": ("eh", "ih", "iy"),
    "ih": ("iy", "eh", "ey"), "iy": ("ih", "ey", "eh"), "ow": ("ao", "uh", "uw"),
    "oy": ("ao", "ow", "aa"), "uh": ("uw", "ah", "ow"), "uw": ("uh", "ow", "ah"),
}
VOICED_CONSONANTS = {"b", "d", "g", "jh", "v", "dh", "z", "zh", "m", "n", "ng", "l",
                     "r", "w", "y"}


def _folder(name: str) -> str:
    """A voice or model name as one folder name: nothing in it can climb out
    of the cache (``..``, ``/abs``) however the bank was spelled in a piece."""
    out = re.sub(r"[^a-z0-9._-]+", "_", str(name).lower()).strip(".")
    if not out:
        raise ValueError(f"{name!r} is not a voice bank name")
    return out


def bank_dir(voice: str, model: str = DEFAULT_MODEL) -> Path:
    return CACHE_DIR.expanduser() / _folder(model) / _folder(voice)


def _clean(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower())


def sample_path(word: str, voice: str, model: str = DEFAULT_MODEL) -> Path:
    return bank_dir(voice, model) / f"{_clean(word)}.wav"


def corpus() -> dict[str, tuple[str, str, str]]:
    """``word -> (onset, vowel, coda)`` for the recording list ('' for none)."""
    out: dict[str, tuple[str, str, str]] = {}
    for line in CORPUS.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        word, onset, vowel, coda = line.split()
        out[word] = ("" if onset == "-" else onset, vowel, "" if coda == "-" else coda)
    return out


def status(voice: str, model: str = DEFAULT_MODEL) -> dict:
    words = corpus()
    have = {w for w in words if sample_path(w, voice, model).is_file()}
    return {"voice": voice, "model": model, "words": len(words), "recorded": len(have),
            "missing": [w for w in words if w not in have],
            "vocabulary": len(vocabulary(voice, model)),
            "where": str(bank_dir(voice, model)),
            "complete": len(have) == len(words)}


#: A frequency-ordered list of common English words, used only to decide what
#: to record. Fetched when a vocabulary is built and kept in the cache; it is
#: not redistributed with the studio.
COMMON_URL = ("https://raw.githubusercontent.com/first20hours/google-10000-english/"
              "master/google-10000-english-no-swears.txt")
COMMON_SHA256 = "d6b3e04f1ac30be6525d41474166c0bff28486ecd8c48dcb0ab9c7c9cc05ed86"


def common_words(count: int) -> list[str]:
    """The ``count`` commonest English words that have a known pronunciation."""
    from .lyrics import dictionary
    from .soundfonts import _fetch, _write
    path = CACHE_DIR.expanduser() / "common-words.txt"
    if not path.is_file():
        _write(path, _fetch(COMMON_URL, COMMON_SHA256))
    known = dictionary()
    if not known:
        raise RuntimeError("choosing a vocabulary needs the pronouncing dictionary: "
                           "run `ms lyrics install` first")
    out = []
    for word in path.read_text().split():
        # One- and two-letter entries in a web corpus are mostly abbreviations.
        if word in known and re.fullmatch(r"[a-z]+", word) and (len(word) > 2 or word in _SHORT):
            out.append(word)
        if len(out) >= count:
            break
    return out


_SHORT = {"a", "i", "am", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is",
          "it", "me", "my", "no", "of", "oh", "on", "or", "so", "to", "up", "us", "we"}


def vocabulary(voice: str, model: str = DEFAULT_MODEL) -> set[str]:
    """Every word this bank has a recording of."""
    d = bank_dir(voice, model)
    return {f.stem for f in d.glob("*.wav")} if d.is_dir() else set()


def parse_bank(bank: str) -> tuple[str, str]:
    voice, _, model = bank.partition("@")
    return voice, model or DEFAULT_MODEL


# --------------------------------------------------------------------------
# recording
# --------------------------------------------------------------------------

def fetch(word: str, voice: str, *, model: str = DEFAULT_MODEL, force: bool = False) -> Path:
    """Have the voice say one word, and keep it. Needs ``$OPENROUTER_API_KEY``
    and ffmpeg (to decode what comes back)."""
    import time
    out = sample_path(word, voice, model)
    if out.is_file() and not force:
        return out
    key = os.environ.get(KEY_ENV)
    if not key:
        raise RuntimeError(f"recording a voice bank needs ${KEY_ENV} in the environment")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("recording a voice bank needs ffmpeg on PATH to decode it")
    text = _clean(word)
    if not text:
        raise ValueError(f"{word!r} has no letters to say")
    # A full stop, so the word is said as a statement and not left hanging.
    body = json.dumps({"model": model, "voice": voice, "input": f"{text}.",
                       "response_format": "mp3"}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "X-Title": "musicstudio"})
    audio = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio = resp.read()
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            if exc.code not in (429, 500, 502, 503, 524, 529) or attempt == 3:
                raise RuntimeError(f"the speech service refused {text!r} "
                                   f"({exc.code}): {detail}") from None
        except urllib.error.URLError as exc:
            if attempt == 3:
                raise RuntimeError(f"could not reach the speech service: {exc}") from None
        time.sleep(1.5 * (attempt + 1))
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        mp3 = Path(tmp) / "w.mp3"
        mp3.write_bytes(audio)
        wav = Path(tmp) / "w.wav"
        done = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3),
                               "-ac", "1", "-ar", str(SR), str(wav)],
                              capture_output=True, text=True)
        if done.returncode != 0 or not wav.is_file():
            raise RuntimeError(f"could not decode the recording of {text!r}: "
                               f"{done.stderr.strip()[:200]}")
        os.replace(wav, out)
    return out


def build(voice: str, *, model: str = DEFAULT_MODEL, workers: int = 6,
          words: int = 0, progress=None) -> dict:
    """Record the bank. Returns :func:`status` afterwards.

    Always the 271-word unit corpus, from which any syllable can be assembled.
    With ``words``, also that many of the commonest English words whole: a
    word that was recorded whole is sung from its own recording, with the joins
    inside it exactly as they were spoken, and that is much easier to
    understand than the same word assembled from halves of other words. Two
    thousand words cover most of any lyric and cost about a dollar.
    """
    have = vocabulary(voice, model)
    todo = [w for w in status(voice, model)["missing"]]
    if words:
        todo += [w for w in common_words(words) if w not in have and w not in set(todo)]
    done = 0

    def one(word: str) -> str:
        fetch(word, voice, model=model)
        return word

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for word in pool.map(one, todo):
            done += 1
            if progress:
                progress(done, len(todo), word)
    _banks.pop((voice, model), None)
    for key in [k for k in _words if k[:2] == (voice, model)]:
        _words.pop(key, None)
    return status(voice, model)


# --------------------------------------------------------------------------
# analysis: where the voice is, and where each cycle of it begins
# --------------------------------------------------------------------------

FRAME = 1024
STEP = 256


@dataclass
class Unit:
    """Half of a recorded word: a consonant opening into a vowel, or a vowel
    closing into a consonant. Times are sample positions in ``x``."""

    x: np.ndarray          # the whole word, normalized
    marks: np.ndarray      # glottal closures: where each voiced cycle starts
    voiced: np.ndarray     # per sample, 0..1
    period: np.ndarray     # per sample, the speaker's pitch period in samples
    start: int             # where this unit begins in x
    end: int               # and ends
    #: For an opening unit, where the vowel starts: what goes on the beat.
    vowel: int = 0
    #: A steady stretch of vowel to dwell in while a note is held.
    steady: tuple[int, int] = (0, 0)
    #: Where the vowel stops and whatever closes the word begins.
    v_end: int = 0
    #: Where the vowel's opening ends and holding begins (its steady middle).
    mid: int = 0


def _load(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
        x = raw.reshape(-1, w.getnchannels()).mean(axis=1) / 32768.0
        if w.getframerate() != SR:
            raise ValueError(f"{path} is {w.getframerate()} Hz; a bank is kept at {SR}")
    return x


def _smooth(x: np.ndarray, n: int) -> np.ndarray:
    k = np.hanning(n + 2)[1:-1]
    return np.convolve(x, k / k.sum(), mode="same")


def analyze_word(x: np.ndarray, onset: str, coda: str = "") -> dict:
    """Voicing, pitch, pitch marks and the vowel's landmarks for one word."""
    level = np.abs(x)
    loud = np.flatnonzero(level > max(0.008, level.max() * 0.025))
    if len(loud):
        x = x[max(0, loud[0] - 400):loud[-1] + 1800]
    x = np.concatenate([np.zeros(FRAME // 2), x, np.zeros(FRAME)])
    data = voicing(x)
    data.update(landmarks(data, 0, len(data["rms"]), onset, coda))
    return data


def voicing(x: np.ndarray, low: float = 110.0, high: float = 420.0) -> dict:
    """Where ``x`` is voiced, its pitch period and one mark per cycle, in
    ``x``'s own sample positions. ``x`` wants half a frame of silence before it
    and a frame after; ``low`` and ``high`` bound the speaker's pitch in Hz."""
    frames = np.lib.stride_tricks.sliding_window_view(x, FRAME)[::STEP]
    rms = np.sqrt((frames ** 2).mean(axis=1))
    spec = np.abs(np.fft.rfft(frames * np.hanning(FRAME), axis=1)) ** 2
    ac = np.fft.irfft(spec, FRAME, axis=1)
    ac /= ac[:, :1] + 1e-12
    lo, hi = int(SR / high), int(SR / low)
    lag = lo + np.argmax(ac[:, lo:hi], axis=1)
    strength = ac[np.arange(len(ac)), lag]
    voiced_f = (strength > 0.45) & (rms > max(0.004, rms.max() * 0.05))
    # One stray frame is not a change of mind.
    voiced_f = _smooth(voiced_f.astype(float), 3) > 0.5
    good = lag[voiced_f]
    typical = float(np.median(good)) if len(good) else SR / 200.0
    # Octave errors: a period half or double the speaker's usual one is a slip.
    lag = np.where((lag > typical * 1.6) | (lag < typical / 1.6), typical, lag).astype(float)
    centres = np.arange(len(rms)) * STEP + FRAME // 2
    idx = np.arange(len(x))
    period = np.interp(idx, centres, _smooth(lag, 5))
    voiced = np.interp(idx, centres, _smooth(voiced_f.astype(float), 3))

    # Pitch marks: one per cycle, each on the strongest peak near where the
    # last one says the next should be.
    marks: list[int] = []
    low = _smooth(x, 9)
    runs = np.flatnonzero(np.diff(np.concatenate([[0], (voiced > 0.5).astype(int), [0]])))
    for a, b in zip(runs[::2], runs[1::2]):
        if b - a < int(typical * 2):
            continue
        anchor = a + int(np.argmax(low[a:b]))
        here = [anchor]
        t = anchor
        while True:                                   # forward
            T = period[min(t, len(x) - 1)]
            w0, w1 = int(t + 0.7 * T), int(t + 1.3 * T)
            if w1 >= b:
                break
            t = w0 + int(np.argmax(low[w0:w1]))
            here.append(t)
        t = anchor
        while True:                                   # backward
            T = period[max(t, 0)]
            w0, w1 = int(t - 1.3 * T), int(t - 0.7 * T)
            if w0 <= a:
                break
            t = w0 + int(np.argmax(low[w0:w1]))
            here.insert(0, t)
        marks += here
    marks_a = np.array(sorted(set(marks)), dtype=np.int64)

    freqs = np.fft.rfftfreq(FRAME, 1.0 / SR)
    return {"x": x, "marks": marks_a, "voiced": voiced, "period": period,
            "rms": rms, "energy": _smooth(rms * voiced_f, 5),
            "bright": _smooth(spec[:, (freqs > 1000) & (freqs < 4000)].sum(axis=1), 3)}


def landmarks(d: dict, first: int, last: int, onset: str, coda: str) -> dict:
    """Where the vowel is inside frames ``[first, last)`` of an analysed word.

    Returns sample positions: ``vowel`` (what goes on the beat), ``mid`` (a
    steady moment to hold), ``v_end`` (where the vowel gives way to whatever
    closes the syllable), ``end`` (where the syllable stops sounding), and
    ``ref``, the vowel's loudness.
    """
    rms, energy, bright = d["rms"], d["energy"], d["bright"]
    pos = lambda k: int(k * STEP + FRAME // 2)
    seg = energy[first:last]
    if len(seg) == 0 or seg.max() <= 0:
        mid = pos((first + last) // 2)
        return {"vowel": mid, "mid": mid, "end": pos(last), "steady": (mid, mid + 1),
                "ref": 0.0, "v_end": mid, "start": pos(first)}
    peak = first + int(np.argmax(seg))
    top = energy[peak]
    a = peak
    while a > first and energy[a - 1] >= top * 0.18:
        a -= 1
    b = peak + 1
    while b < last and energy[b] >= top * 0.18:
        b += 1
    v0, v1 = pos(a), pos(b)
    # A voiced consonant (m, n, l, z ...) hums on either side of the vowel and
    # can be nearly as loud, so loudness does not find the join. Brightness
    # does: with the mouth closed or narrowed, almost everything above 1 kHz
    # goes. The vowel is the stretch where that band is open.
    open_ = bright >= bright[a:b].max() * 0.5
    centre = a + int(np.argmax(bright[a:b]))
    if onset in VOICED_CONSONANTS:
        k = centre
        while k > a and open_[k - 1]:
            k -= 1
        # A glide or a liquid never closes the mouth: fall back to loudness.
        if k == a:
            while k < peak and energy[k] < top * 0.6:
                k += 1
        vowel = pos(k)
    else:
        vowel = v0
    if coda in VOICED_CONSONANTS:
        k = centre
        while k < b - 1 and open_[k + 1]:
            k += 1
        if k >= b - 2:
            k = centre + int((b - centre) * 0.6)
        v1 = max(vowel + 2 * STEP, pos(k + 1))
    mid = int(vowel + (v1 - vowel) * 0.45)
    half = int(0.02 * SR)
    steady = (max(vowel, mid - half), min(v1, mid + half))
    # The syllable stops sounding where the level last was above a whisper.
    live = np.flatnonzero(rms[first:last] > rms[first:last].max() * 0.06)
    end = pos(first + int(live[-1]) + 2) if len(live) else pos(last)
    end = min(end, pos(last)) if last < len(rms) else min(end, len(d["x"]))
    lo = first * STEP + FRAME // 2 if first else 0
    ref = float(np.sqrt(np.mean(d["x"][v0:max(v0 + 1, pos(b))] ** 2)))
    return {"vowel": int(vowel), "mid": int(mid), "end": int(end), "steady": steady,
            "ref": ref, "v_end": int(v1), "start": int(lo)}


def split_word(d: dict, count: int) -> list[tuple[int, int]]:
    """Cut an analysed word into ``count`` syllables, as frame ranges.

    Syllables are hills of voiced energy. Inside the word's *core* -- the
    stretch where anything is really sounding, not the breath after it -- the
    ``count`` tallest hills are the vowels and each cut goes at the lowest
    point between two of them. When speech runs two vowels into one hill
    ("static" has no dip at its "t"), the core is divided evenly instead:
    wrong by a few hundredths of a second, never by a whole syllable.
    """
    n = len(d["rms"])
    if count <= 1:
        return [(0, n)]
    energy = d["rms"] * (0.25 + 0.75 * (d["energy"] > 0))
    smooth = _smooth(energy, 7)
    live = np.flatnonzero(smooth > smooth.max() * 0.1)
    if len(live) < count * 2:
        return [(i * n // count, (i + 1) * n // count) for i in range(count)]
    c0, c1 = int(live[0]), int(live[-1]) + 1
    floor = smooth.max() * 0.12
    peaks = [i for i in range(max(1, c0), min(n - 1, c1))
             if smooth[i] > smooth[i - 1] and smooth[i] >= smooth[i + 1] and smooth[i] > floor]
    peaks.sort(key=lambda i: -smooth[i])
    chosen: list[int] = []
    gap = max(5, (c1 - c0) // (count * 3))
    for p in peaks:
        if all(abs(p - c) >= gap for c in chosen):
            chosen.append(p)
        if len(chosen) == count:
            break
    if len(chosen) == count:
        chosen.sort()
        inner = [x + int(np.argmin(smooth[x:y])) for x, y in zip(chosen, chosen[1:])]
    else:
        inner = [c0 + (c1 - c0) * i // count for i in range(1, count)]
    cuts = [0] + inner + [n]
    return list(zip(cuts, cuts[1:]))


@dataclass
class Bank:
    cv: dict[tuple[str, str], Unit]
    vc: dict[tuple[str, str], Unit]

    def opening(self, onset: str, vowel: str) -> tuple[Unit | None, bool]:
        """The unit for consonant-into-vowel, and whether it is exact."""
        if (onset, vowel) in self.cv:
            return self.cv[(onset, vowel)], True
        for v in NEAR_VOWEL.get(vowel, ()):
            if (onset, v) in self.cv:
                return self.cv[(onset, v)], False
        hit = next((u for (o, _), u in self.cv.items() if o == onset), None)
        return hit, False

    def closing(self, vowel: str, coda: str) -> tuple[Unit | None, bool]:
        if (vowel, coda) in self.vc:
            return self.vc[(vowel, coda)], True
        for v in NEAR_VOWEL.get(vowel, ()):
            if (v, coda) in self.vc:
                return self.vc[(v, coda)], False
        hit = next((u for (_, c), u in self.vc.items() if c == coda), None)
        return hit, False

    def consonant(self, c: str, vowel: str) -> Unit | None:
        """Just a consonant, from the word that says it before this vowel."""
        return self.opening(c, vowel)[0]


_banks: dict[tuple[str, str], Bank | None] = {}


def load(voice: str, model: str = DEFAULT_MODEL) -> Bank | None:
    """The bank, analysed and ready, or ``None`` if it has not been recorded."""
    key = (voice, model)
    if key in _banks:
        return _banks[key]
    cv: dict[tuple[str, str], Unit] = {}
    vc: dict[tuple[str, str], Unit] = {}
    words = corpus()
    present = [w for w in words if sample_path(w, voice, model).is_file()]
    if len(present) < len(words) * 0.9:
        _banks[key] = None
        return None
    for word in present:
        onset, vowel, coda = words[word]
        a = analyze_word(_load(sample_path(word, voice, model)), onset, coda)
        if a["ref"] <= 0:
            continue
        x = a["x"] * (VOWEL_RMS / a["ref"])
        common = dict(x=x, marks=a["marks"], voiced=a["voiced"], period=a["period"],
                      steady=a["steady"], v_end=a["v_end"], mid=a["mid"])
        cv.setdefault((onset, vowel), Unit(start=0, end=a["mid"], vowel=a["vowel"], **common))
        vc.setdefault((vowel, coda), Unit(start=a["mid"], end=a["end"], vowel=a["mid"], **common))
    _banks[key] = Bank(cv, vc)
    return _banks[key]


_words: dict[tuple, list | None] = {}


def word_units(word: str, syllables: list[tuple[str, str]], voice: str,
               model: str = DEFAULT_MODEL) -> list[Unit] | None:
    """A recorded word as one unit per syllable, or ``None`` if not recorded.

    ``syllables`` gives, for each, the consonant just before its vowel and the
    one just after (``''`` for none): what `landmarks` needs to find where
    each vowel begins and ends.
    """
    key = (voice, model, _clean(word), tuple(syllables))
    if key in _words:
        return _words[key]
    path = sample_path(word, voice, model)
    if not path.is_file():
        _words[key] = None
        return None
    d = analyze_word(_load(path), syllables[0][0], syllables[-1][1])
    spans = split_word(d, len(syllables))
    out: list[Unit] = []
    for (first, last), (onset, coda) in zip(spans, syllables):
        lm = landmarks(d, first, last, onset, coda)
        if lm["ref"] <= 0:
            _words[key] = None
            return None
        # Every syllable is brought to the same loudness: in speech an
        # unstressed syllable nearly vanishes, sung it is a note like any other.
        gain = min(6.0, VOWEL_RMS / lm["ref"])
        end = lm["end"] if last >= len(d["rms"]) else int(last * STEP + FRAME // 2)
        out.append(Unit(x=d["x"] * gain, marks=d["marks"], voiced=d["voiced"],
                        period=d["period"], start=lm["start"], end=end, vowel=lm["vowel"],
                        steady=lm["steady"], v_end=lm["v_end"], mid=lm["mid"]))
    _words[key] = out
    return out


# --------------------------------------------------------------------------
# PSOLA: the recording, at another pitch and another length
# --------------------------------------------------------------------------

def psola(u: Unit, src: np.ndarray, f0: np.ndarray) -> np.ndarray:
    """Play ``u.x`` along the path ``src`` (a source position for every output
    sample) at pitch ``f0`` (Hz, per output sample).

    The output is built from short windowed grains of the recording. Where the
    source is voiced, a grain is two pitch periods long, taken at one of the
    source's own pitch marks, and they are laid down at the *output's* period:
    the pitch is the score's and the grain -- the vowel -- is the recording's.
    Where it is unvoiced, grains are a fixed few milliseconds, taken wherever
    the path is. Either way a grain is never resampled, so playing a consonant
    faster or slower changes how long it lasts and not what it sounds like.
    (Reading the recording straight along a fast path would shift an "s" up by
    as many times as it was sped up.)
    """
    n = len(src)
    if n == 0:
        return np.zeros(0)
    x = u.x
    pos = np.clip(src, 0, len(x) - 2)
    weight = u.voiced[pos.astype(np.int64)]
    out = np.zeros(n)
    have_marks = len(u.marks) >= 2
    noise_half = 160                                 # 7 ms grains for noise
    noise_win = np.hanning(2 * noise_half)
    t = 0.0
    while t < n:
        k = int(t)
        p = pos[k]
        if have_marks and weight[k] > 0.5:
            T_out = SR / max(60.0, float(f0[k]))
            j = int(np.searchsorted(u.marks, p))
            j = min(max(j, 0), len(u.marks) - 1)
            if j > 0 and abs(u.marks[j - 1] - p) < abs(u.marks[j] - p):
                j -= 1
            m = int(u.marks[j])
            T_src = float(u.period[min(m, len(x) - 1)])
            half = int(T_src)
            a, b = m - half, m + half
            if a >= 0 and b < len(x) and half > 8:
                # More grains per second at a higher pitch: scale so the level
                # stays where the recording had it.
                grain = x[a:b] * np.hanning(2 * half) * min(1.6, T_out / T_src) ** 0.8
                o0 = k - half
                g0, g1 = max(0, -o0), min(2 * half, n - o0)
                if g1 > g0:
                    out[o0 + g0:o0 + g1] += grain[g0:g1]
            t += T_out
        else:
            m = int(p)
            a, b = m - noise_half, m + noise_half
            if a >= 0 and b < len(x):
                o0 = k - noise_half
                g0, g1 = max(0, -o0), min(2 * noise_half, n - o0)
                if g1 > g0:
                    out[o0 + g0:o0 + g1] += (x[a:b] * noise_win)[g0:g1]
            t += noise_half                           # 50% overlap: the windows sum to one
    return out


def _ride(a: float, b: float, n: int) -> np.ndarray:
    """A path from ``a`` to ``b`` in ``n`` samples at constant speed."""
    return np.linspace(a, b, n, endpoint=False) if n > 0 else np.zeros(0)


def _stretch(a: float, b: float, n: int) -> np.ndarray:
    """A path through the whole of a recorded vowel, made to last ``n`` samples.

    The first and last sixtieth of a second go by at the speed they were
    spoken -- that is where the mouth is moving, into the vowel and out of it
    -- and the middle is slowed to fill the note. So a long note still opens
    and closes like the word, and a diphthong still glides, just late.
    """
    span = b - a
    if n <= 0:
        return np.zeros(0)
    if n <= span or span < 32:
        return np.linspace(a, b, n, endpoint=False)
    edge = int(min(0.06 * SR, span / 3.0))
    middle = n - 2 * edge
    return np.concatenate([np.arange(edge) + a,
                           np.linspace(a + edge, b - edge, middle, endpoint=False),
                           np.arange(edge) + (b - edge)])


def _dwell(steady: tuple[int, int], n: int, rng=None) -> np.ndarray:
    """A path that holds the vowel for ``n`` samples.

    It stays almost still, at the middle of the steady stretch, wandering a
    few milliseconds either way. Sweeping back and forth across the vowel was
    tried first and is audible as the syllable repeating ("na-na-na"): a spoken
    vowel is never steady for long, so holding one means choosing a moment of
    it. The wander is only there so that the same grain is not repeated
    exactly, which would turn the voice into a buzz.
    """
    a, b = steady
    if n <= 0:
        return np.zeros(0)
    mid = (a + b) / 2.0
    reach = min(0.006 * SR, (b - a) / 2.0)
    t = np.arange(n) / SR
    phase = rng.uniform(0, 2 * np.pi, 3) if rng is not None else np.zeros(3)
    wander = (np.sin(2 * np.pi * 2.3 * t + phase[0]) + np.sin(2 * np.pi * 3.7 * t + phase[1])
              + np.sin(2 * np.pi * 5.9 * t + phase[2])) / 3.0
    return mid + reach * wander


# --------------------------------------------------------------------------
# singing a phrase
# --------------------------------------------------------------------------

def _alias(ph: str) -> str:
    return ALIASES.get(ph, ph)


def render_phrase(sung: list[Sung], bank: Bank, singer, seed: int,
                  whole=None) -> tuple[np.ndarray, float]:
    """Sing one phrase from the bank. Returns ``(samples, start time)``.

    ``whole(word, syllables)`` returns a recorded word's units if there is one;
    a syllable with one is sung from it, and one without is assembled.
    """
    rng = np.random.default_rng(seed)
    lead = 0.45
    t0 = max(0.0, sung[0].start - lead)
    total = sung[-1].end - t0 + 0.5
    n = int(total * SR)
    out = np.zeros(n)

    # -- pitch: the score's ---------------------------------------------------
    t = np.arange(n) / SR + t0
    midi = np.full(n, sung[0].pitch, dtype=np.float64)
    for i, s in enumerate(sung):
        if i == 0:
            continue
        x = np.clip((t - (s.start - 0.012)) / (singer.glide / 4.0), -40.0, 40.0)
        midi += (s.pitch - sung[i - 1].pitch) / (1.0 + np.exp(-x))
    cents = -45.0 * np.exp(-np.maximum(t - sung[0].start, 0.0) / 0.05) * (t >= sung[0].start - 0.05)
    for s in sung:
        if s.end - s.start < 0.36:
            continue
        rate = singer.vibrato_rate * rng.uniform(0.95, 1.05)
        rise = np.clip((t - s.start - 0.2) / 0.3, 0.0, 1.0) * (t < s.end)
        cents += singer.vibrato * rise * np.sin(2 * np.pi * rate * (t - s.start)
                                                + rng.uniform(0, 2 * np.pi))
    drift = np.interp(t, np.linspace(t[0], t[-1], max(4, int(total * 3))),
                      rng.normal(0.0, 4.0, max(4, int(total * 3))))
    f0 = 440.0 * 2.0 ** ((midi - 69.0) / 12.0 + (cents + drift) / 1200.0)

    fade = int(0.012 * SR)

    def lay(u: Unit, path: np.ndarray, at: float, gain: float) -> None:
        """Put a stretch of a unit into the phrase, with soft edges."""
        k = int(round((at - t0) * SR))
        if k < 0:
            path = path[-k:]
            k = 0
        m = min(len(path), n - k)
        if m <= 8:
            return
        piece = psola(u, path[:m], f0[k:k + m]) * gain
        f = min(fade, m // 2)
        piece[:f] *= np.linspace(0.0, 1.0, f)
        piece[-f:] *= np.linspace(1.0, 0.0, f)
        out[k:k + m] += piece

    # Consonants are played at the speed they were spoken. A consonant squeezed
    # to fit is the first thing to stop being understood, so when there is not
    # room the *vowel* gives way, then the consonant is sped up by at most half,
    # and only then is some of it cut -- from the end furthest from the vowel.
    MAX_SPEED = 3.0

    def fit(natural: float, room: float) -> tuple[float, float]:
        """``(seconds it will take, seconds of source it covers)``."""
        if natural <= room:
            return natural, natural
        return room, min(natural, room * MAX_SPEED)

    def joined_next(i: int) -> bool:
        return i + 1 < len(sung) and sung[i + 1].start - sung[i].end < 0.04

    def _closing_of(u: Unit) -> list:
        """The end of a recorded syllable: whatever follows its vowel, up to
        where the next syllable (or silence) begins."""
        a = u.v_end
        b = min(u.end, u.v_end + int(0.30 * SR))      # room for "-lz", "-nts"
        return [(u, a, b)] if b - a > int(0.012 * SR) else []

    # Which notes belong to one recorded word, and that word's units.
    recorded: dict[int, Unit] = {}
    if whole is not None:
        i = 0
        while i < len(sung):
            name, _, where = sung[i].word.partition("#")
            idx, _, cnt = where.partition("/")
            if not name or sung[i].hold or int(idx or 0) != 0:
                i += 1
                continue
            cnt = int(cnt or 1)
            # The word's syllables, skipping any held notes sung inside it.
            members = [j for j in range(i, len(sung)) if not sung[j].hold][:cnt]
            members = [j for j in members if sung[j].word.startswith(name + "#")]
            if len(members) == cnt:
                shape = [(_alias(sung[j].onset[-1]) if sung[j].onset else "",
                          _alias(sung[j].coda[0]) if sung[j].coda else "") for j in members]
                units = whole(name, shape)
                if units is not None:
                    recorded.update(zip(members, units))
            i += 1

    plans = []
    last_open: Unit | None = None
    for i, s in enumerate(sung):
        vowel = _alias(s.nucleus)
        if vowel not in VOWELS or len(vowel) == 1:
            vowel = "ah"                       # a syllabic consonant: a neutral vowel under it
        onset = [_alias(c) for c in s.onset if c != "q"]
        coda = [_alias(c) for c in s.coda if c != "q"]
        nxt = sung[i + 1] if i + 1 < len(sung) else None
        holds_on = nxt is not None and nxt.hold and nxt.start - s.end < 0.05
        gain = (max(1, min(127, s.velocity)) / 127.0) ** 1.2
        seg = recorded.get(i)
        if s.hold and last_open is not None:
            # A melisma: the same vowel, from the same recording, at a new pitch.
            before, u_open = [], last_open
            after = [] if holds_on else _closing_of(last_open)
        elif seg is not None:
            u_open = seg
            a0 = max(seg.start, seg.vowel - int(0.22 * SR))
            # Skip the silence before the word (and most of a stop's closure):
            # only what can be heard needs a place before the beat.
            lead = np.abs(seg.x[a0:seg.vowel])
            if len(lead) > 400:
                heard = np.flatnonzero(_smooth(lead, 220) > max(0.004, lead.max() * 0.08))
                if len(heard):
                    a0 += max(0, int(heard[0]) - int(0.015 * SR))
            before = [(seg, a0, seg.vowel)] if seg.vowel > a0 else []
            after = [] if holds_on else _closing_of(seg)
        else:
            u_open, _ = bank.opening(onset[-1] if onset and not s.hold else "", vowel)
            if u_open is None:
                u_open, _ = bank.opening("", vowel)
            before = []                            # (unit, source start, source end)
            if u_open is not None and not s.hold:
                for c in onset[:-1]:
                    uc = bank.consonant(c, vowel)
                    if uc is not None:
                        before.append((uc, max(uc.start, uc.vowel - int(0.10 * SR)), uc.vowel))
                a0 = max(u_open.start, u_open.vowel - int(0.18 * SR))
                if u_open.vowel > a0:
                    before.append((u_open, a0, u_open.vowel))
            after = []
            if not holds_on:
                if coda:
                    uc, _ = bank.closing(vowel, coda[0])
                    if uc is not None:
                        after.append((uc, max(uc.start, uc.v_end - int(0.05 * SR)),
                                      min(uc.end, uc.v_end + int(0.18 * SR))))
                for c in coda[1:]:
                    uc = bank.consonant(c, vowel)
                    if uc is not None:
                        after.append((uc, max(uc.start, uc.vowel - int(0.09 * SR)), uc.vowel))
                if not coda and not joined_next(i):
                    # An open syllable before a rest: let the vowel finish the
                    # way it was spoken (the glide of "now", the fall of "day").
                    uc, exact = bank.closing(vowel, "")
                    if uc is not None and exact:
                        after.append((uc, max(uc.start, uc.v_end - int(0.12 * SR)),
                                      min(uc.end, uc.v_end + int(0.05 * SR))))
        last_open = u_open
        plans.append({"s": s, "open": u_open, "before": before, "after": after,
                      "gain": gain, "whole": seg is not None,
                      "held": s.hold and last_open is not None})

    for i, pl in enumerate(plans):
        s, u_open = pl["s"], pl["open"]
        if u_open is None:
            continue
        gain = pl["gain"]
        length = s.end - s.start
        nxt = plans[i + 1] if i + 1 < len(plans) else None
        joined = nxt is not None and nxt["s"].start - s.end < 0.04
        closing = sum((b - a) for _, a, b in pl["after"]) / SR
        next_on = sum((b - a) for _, a, b in nxt["before"]) / SR if joined else 0.0
        room = length * 0.62
        share = min(1.0, room / (closing + next_on)) if closing + next_on > 0 else 1.0
        pl["onset_share"] = pl.get("onset_share", 1.0)
        if nxt is not None:
            nxt["onset_share"] = share if joined else 1.0

        # -- before the beat ------------------------------------------------------
        on_share = pl["onset_share"] if i else 1.0
        pieces = []
        for u, a, b in pl["before"]:
            took, covers = fit((b - a) / SR, (b - a) / SR * on_share)
            pieces.append((u, b - covers * SR, b, took))        # keep the end by the vowel
        at = s.start - sum(p[3] for p in pieces)
        for u, a, b, took in pieces:
            lay(u, _ride(a, b, int(took * SR)), at, gain * CONSONANT_LIFT)
            at += took

        # -- on the beat: the vowel -------------------------------------------------
        v_len = max(0.03, length - (closing + next_on) * share)
        if pl["held"] or s.hold:
            lay(u_open, _dwell(u_open.steady, int((v_len + 0.018) * SR), rng), s.start - 0.006, gain)
        elif pl["whole"]:
            # A recorded word: its whole vowel, stretched to the note. If the
            # note is held on into a melisma, stop at the steady middle.
            stop = u_open.v_end if pl["after"] or not (nxt and nxt["held"]) else u_open.mid
            lay(u_open, _stretch(u_open.vowel, max(u_open.vowel + 64, stop),
                                 int((v_len + 0.012) * SR)), s.start, gain)
        else:
            opening = max(0.0, (u_open.mid - u_open.vowel) / SR)
            rise = min(opening, v_len * 0.7)
            m = int(rise * SR)
            lay(u_open, _ride(u_open.vowel, u_open.vowel + m, m), s.start, gain)
            hold = v_len - rise
            if hold > 0.012:
                # Overlapped a little at both ends so the joins crossfade.
                lay(u_open, _dwell(u_open.steady, int((hold + 0.024) * SR), rng),
                    s.start + rise - 0.012, gain)

        # -- what closes the note ---------------------------------------------------
        at = s.start + v_len
        for u, a, b in pl["after"]:
            took, covers = fit((b - a) / SR, (b - a) / SR * share)
            lay(u, _ride(a, a + covers * SR, int(took * SR)), at - 0.006,
                gain * CONSONANT_LIFT)                                 # keep the start
            at += took

    return out * (LEVEL * singer.level / VOWEL_RMS), t0


def voice_stems(piece, notes, to_sec, total: int, pans: dict[str, float], *,
                strict: bool = False) -> dict[str, tuple]:
    """``{voice: (left, right)}`` for every singer whose bank has been recorded.
    A bank that is missing is left to the formant singer with a warning, or
    raises under ``strict``."""
    import warnings
    from . import neural
    from . import utau
    from .vocal import SINGERS, phrases, plan
    # A UTAU voicebank is a recorded voice too, of another make (`utau.py`).
    out: dict[str, tuple] = utau.voice_stems(piece, notes, to_sec, total, pans, strict=strict)
    for v in piece.voices:
        if (v.muted or not v.bank or v.instrument not in SINGERS or neural.knows(v.bank)
                or utau.is_utau(v.bank)):
            continue
        mine = [n for n in notes if n.voice == v.name and not n.percussive]
        if not mine:
            continue
        voice_name, model = parse_bank(v.bank)
        bank = load(voice_name, model)
        if bank is None:
            if strict:
                raise RuntimeError(f"voice {v.name!r}: the bank {v.bank!r} has not "
                                   f"been recorded")
            warnings.warn(f"voice {v.name!r} falls back to the synthesized singer: the "
                          f"bank {v.bank!r} has not been recorded. Run "
                          f"`ms voicebank build {voice_name}`.", stacklevel=2)
            continue
        singer = SINGERS[v.instrument]
        mono = np.zeros(total)
        for group in phrases(plan(mine, to_sec)):
            seed = zlib.crc32(f"{v.name}|{group[0].start:.4f}|{group[0].pitch}".encode())
            sig, t0 = render_phrase(
                group, bank, singer, seed,
                whole=lambda w, shape: word_units(w, shape, voice_name, model))
            a = int(t0 * SR)
            k = min(len(sig), total - a)
            if k > 0:
                mono[a:a + k] += sig[:k]
        theta = (max(-1.0, min(1.0, pans.get(v.name, 0.0))) + 1.0) * math.pi / 4
        out[v.name] = (mono * math.cos(theta) * math.sqrt(2),
                       mono * math.sin(theta) * math.sqrt(2))
    return out


# --------------------------------------------------------------------------
# being listened to
# --------------------------------------------------------------------------

TRANSCRIBE_ENDPOINT = "https://openrouter.ai/api/v1/audio/transcriptions"
TRANSCRIBE_MODEL = "openai/whisper-large-v3"


def transcribe(path: Path, *, model: str = TRANSCRIBE_MODEL, language: str = "en") -> str:
    """What a speech recogniser hears in a rendered file.

    The nearest thing the studio has to an ear for words: if a recogniser can
    write down most of a sung line, a person can follow it. Needs
    ``$OPENROUTER_API_KEY`` and ffmpeg, and costs a little per call, so it is
    only ever run when asked for.
    """
    import base64
    key = os.environ.get(KEY_ENV)
    if not key:
        raise RuntimeError(f"transcribing needs ${KEY_ENV} in the environment")
    with tempfile.TemporaryDirectory() as tmp:
        small = Path(tmp) / "a.mp3"
        done = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path),
                               "-ac", "1", "-ar", "16000", "-b:a", "48k", str(small)],
                              capture_output=True, text=True)
        if done.returncode != 0:
            raise RuntimeError(f"could not prepare {path} for transcription: "
                               f"{done.stderr.strip()[:200]}")
        data = base64.b64encode(small.read_bytes()).decode()
    body = json.dumps({"model": model, "language": language,
                       "input_audio": {"data": data, "format": "mp3"}}).encode()
    req = urllib.request.Request(TRANSCRIBE_ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "X-Title": "musicstudio"})
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            return str(json.load(resp).get("text", "")).strip()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"transcription refused ({exc.code}): "
                           f"{exc.read().decode('utf-8', 'replace')[:300]}") from None


def transcribe_long(path: Path, *, chunk: float = 16.0, **kw) -> str:
    """`transcribe`, a stretch at a time.

    A recogniser handed a whole song tends to write down the first verse and
    stop -- it scored one render 30% that it scored 85% in pieces. So the file
    is cut at its quietest moments, about every ``chunk`` seconds, and each
    piece is heard on its own.
    """
    with wave.open(str(path), "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        return transcribe(path, **kw)
    x = np.frombuffer(raw, dtype="<i2").reshape(-1, channels)
    if len(x) <= chunk * 1.5 * rate:
        return transcribe(path, **kw)
    hop = int(0.05 * rate)
    level = np.array([np.abs(x[i:i + hop].astype(np.float64)).mean()
                      for i in range(0, len(x) - hop, hop)])
    cuts, at = [0], chunk
    while at < len(x) / rate - chunk / 2:
        lo, hi = int((at - chunk / 4) / 0.05), int((at + chunk / 4) / 0.05)
        k = lo + int(np.argmin(_smooth(level[lo:hi], 5)))
        cuts.append(k * hop)
        at = k * 0.05 + chunk
    cuts.append(len(x))
    heard = []
    with tempfile.TemporaryDirectory() as tmp:
        for a, b in zip(cuts, cuts[1:]):
            if np.abs(x[a:b]).max() < 300:              # silence: nothing to ask about
                continue
            part = Path(tmp) / "part.wav"
            with wave.open(str(part), "wb") as w:
                w.setnchannels(channels)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(x[a:b].tobytes())
            heard.append(transcribe(part, **kw))
    return " ".join(h for h in heard if h)


def words_heard(written: list[str], heard: str) -> tuple[float, list[str]]:
    """How much of a lyric survived: the share of written words the recogniser
    also wrote, in order, and the ones it missed. Order matters -- a word heard
    in the wrong line is not the word being understood."""
    import difflib
    want = [_clean(w) for w in written if _clean(w)]
    got = [_clean(w) for w in re.split(r"[^A-Za-z']+", heard) if _clean(w)]
    match = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    kept = [False] * len(want)
    for block in match.get_matching_blocks():
        for i in range(block.a, block.a + block.size):
            kept[i] = True
    missed = [w for w, k in zip(want, kept) if not k]
    return (sum(kept) / len(want) if want else 0.0), missed


def words_added(written: list[str], heard: str) -> list[str]:
    """What the recogniser wrote that the lyric does not say. ``words_heard``
    is recall, and recall alone is satisfied by a voice that sings every word
    among a lot of noise the recogniser also took for words; this is the other
    half of the score."""
    import difflib
    want = [_clean(w) for w in written if _clean(w)]
    got = [_clean(w) for w in re.split(r"[^A-Za-z']+", heard) if _clean(w)]
    match = difflib.SequenceMatcher(a=want, b=got, autojunk=False)
    kept = [False] * len(got)
    for block in match.get_matching_blocks():
        for i in range(block.b, block.b + block.size):
            kept[i] = True
    return [w for w, k in zip(got, kept) if not k]
