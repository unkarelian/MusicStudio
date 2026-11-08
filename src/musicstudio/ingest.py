"""Reading existing music in, so the studio can be pointed at what already exists.

Two doors, and the difference between them matters more than anything else in
this module:

**MIDI is exact.** Every pitch, onset and duration is stated in the file, so an
imported MIDI piece can be analyzed with the same confidence as one the studio
wrote itself.

**Audio is an estimate.** Pulling a melody out of a finished mix is the MIREX
melody-extraction problem: research-grade, and hard. What comes back here is a
monophonic guess at the most prominent line, produced by harmonic-summation
salience and a Viterbi track. On sparse, clearly-led material it is usable. On
dense multi-layered arrangements it will merge voices, chase accompaniment, and
invent repeated notes -- so every transcription carries a ``confidence`` figure
and the analysis layer refuses to draw conclusions the evidence cannot support.
Treat audio import as a lead to follow, never as ground truth.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .theory import TPQ, Key

# --------------------------------------------------------------------------
# events -- the common currency of anything imported
# --------------------------------------------------------------------------

@dataclass
class Event:
    """One imported note, in absolute ticks and MIDI pitch."""
    pitch: int
    start: int
    dur: int
    velocity: int = 80
    track: str = ""

    def to_json(self) -> list:
        return [self.pitch, self.start, self.dur, self.velocity]


@dataclass
class Ingested:
    name: str
    events: list[Event]
    tempo: int = 120
    meter: str = "4/4"
    key: Key | None = None
    #: 0..1. How much the note data can be trusted -- 1.0 for MIDI, lower and
    #: heuristic for audio. Analysis gates its conclusions on this.
    confidence: float = 1.0
    source: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def duration(self) -> int:
        return max((e.start + e.dur for e in self.events), default=0)

    def summary(self) -> str:
        bars = self.duration / (TPQ * 4) if self.duration else 0
        return (f"{self.name}: {len(self.events)} events, ~{bars:.0f} bars, "
                f"q≈{self.tempo}, key≈{self.key.name if self.key else '?'}, "
                f"confidence {self.confidence:.2f} ({self.source})")


# --------------------------------------------------------------------------
# MIDI in -- exact
# --------------------------------------------------------------------------

def _read_vlq(data: bytes, i: int) -> tuple[int, int]:
    n = 0
    while True:
        b = data[i]
        i += 1
        n = (n << 7) | (b & 0x7F)
        if not b & 0x80:
            return n, i


def read_midi(path: str | Path, *, name: str | None = None) -> Ingested:
    """Parse a standard MIDI file into events. Formats 0 and 1, running status."""
    data = Path(path).read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"{path} is not a MIDI file (no MThd header)")
    _, ntrks, division = struct.unpack(">HHH", data[8:14])
    if division & 0x8000:
        raise ValueError("SMPTE time division is not supported; re-export with "
                         "ticks-per-quarter timing")
    events: list[Event] = []
    tempo, meter = 120, "4/4"
    seen_tempo = seen_meter = False
    pos = 14
    for _ in range(ntrks):
        if data[pos:pos + 4] != b"MTrk":
            break
        length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body, pos = data[pos + 8:pos + 8 + length], pos + 8 + length
        events += _read_track(body, division, out_tempo := [])
        for kind, val in out_tempo:
            # First marking wins: a cue that ritards at the end is not a slow cue.
            if kind == "tempo" and not seen_tempo:
                tempo, seen_tempo = val, True
            elif kind == "meter" and not seen_meter:
                meter, seen_meter = val, True
    events.sort(key=lambda e: (e.start, e.pitch))
    ing = Ingested(name or Path(path).stem, events, tempo, meter,
                   source=f"midi:{Path(path).name}", confidence=1.0)
    ing.key = estimate_key(events)
    return ing


def _read_track(body: bytes, division: int, meta_out: list) -> list[Event]:
    scale = TPQ / division            # normalize onto the studio's own resolution
    i, tick, status = 0, 0, 0
    open_notes: dict[tuple[int, int], tuple[int, int]] = {}
    out: list[Event] = []
    name = ""
    while i < len(body):
        delta, i = _read_vlq(body, i)
        tick += delta
        if i >= len(body):
            break
        b = body[i]
        if b & 0x80:
            status, i = b, i + 1
        cmd, chan = status & 0xF0, status & 0x0F
        if b == 0xFF:
            meta = body[i]
            i += 1
            n, i = _read_vlq(body, i)
            payload, i = body[i:i + n], i + n
            if meta == 0x51 and n == 3:
                usec = int.from_bytes(payload, "big")
                meta_out.append(("tempo", max(1, round(60_000_000 / usec))))
            elif meta == 0x58 and n >= 2:
                meta_out.append(("meter", f"{payload[0]}/{1 << payload[1]}"))
            elif meta == 0x03:
                name = payload.decode("utf-8", "replace")
            continue
        if status in (0xF0, 0xF7):
            n, i = _read_vlq(body, i)
            i += n
            continue
        if cmd in (0x80, 0x90):
            pitch, vel, i = body[i], body[i + 1], i + 2
            key = (chan, pitch)
            if cmd == 0x90 and vel > 0:
                open_notes[key] = (int(tick * scale), vel)
            elif key in open_notes:
                start, v = open_notes.pop(key)
                dur = max(1, int(tick * scale) - start)
                out.append(Event(pitch, start, dur, v, name))
        elif cmd in (0xA0, 0xB0, 0xE0):
            i += 2
        elif cmd in (0xC0, 0xD0):
            i += 1
        else:
            i += 1
    return out


# --------------------------------------------------------------------------
# audio in -- an estimate, and labelled as one
# --------------------------------------------------------------------------

SR, FFT, HOP = 22050, 4096, 256
LOW_PITCH, HIGH_PITCH = 48, 96          # C3..C7, the melodic register


def _require(module: str):
    try:
        return __import__(module)
    except ImportError:
        raise ImportError(
            f"audio import needs {module}. Install the analysis extra: "
            f"`uv sync --extra analysis`. MIDI import needs no extras and is exact."
        ) from None


def decode_audio(path: str | Path, sr: int = SR):
    """Decode anything ffmpeg reads into mono float samples."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("audio import needs ffmpeg on PATH")
    np = _require("numpy")
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
         "-f", "s16le", "-"], capture_output=True)
    if proc.returncode != 0:
        raise ValueError(f"ffmpeg could not decode {path}: "
                         f"{proc.stderr.decode('utf-8', 'replace')[:200]}")
    return np.frombuffer(proc.stdout, dtype="<i2").astype(np.float32) / 32768.0


def _salience(x, harmonics: int = 8, decay: float = 0.8):
    """Harmonic summation: a pitch is salient when its partials are all present.

    This is what separates a real fundamental from one of its own overtones --
    the overtone's own harmonic series is not there to support it.
    """
    np = _require("numpy")
    win = np.hanning(FFT).astype(np.float32)
    frames = 1 + (len(x) - FFT) // HOP
    if frames < 2:
        raise ValueError("audio is too short to analyze")
    idx = np.arange(FFT)[None, :] + HOP * np.arange(frames)[:, None]
    mag = np.abs(np.fft.rfft(x[idx] * win, axis=1)).astype(np.float32)
    pitches = np.arange(LOW_PITCH, HIGH_PITCH + 1)
    f0 = 440.0 * 2 ** ((pitches - 69) / 12.0)
    sal = np.zeros((frames, len(pitches)), dtype=np.float32)
    for h in range(1, harmonics + 1):
        b = np.clip(np.round(f0 * h / (SR / FFT)).astype(int), 1, mag.shape[1] - 2)
        sal += (decay ** (h - 1)) * np.maximum.reduce([mag[:, b - 1], mag[:, b], mag[:, b + 1]])
    return sal, mag


def _viterbi(sal, jump: float = 0.25):
    """Best pitch path: reward salience, penalise leaping.

    Without the continuity term a frame-wise argmax flips between competing
    partials and manufactures trills that are not in the music.
    """
    np = _require("numpy")
    n, k = sal.shape
    em = np.log(sal + 1e-6)
    em -= em.max(1, keepdims=True)
    d = np.abs(np.arange(k)[:, None] - np.arange(k)[None, :])
    trans = -jump * np.minimum(d, 14).astype(np.float32)
    dp = em[0].copy()
    back = np.zeros((n, k), dtype=np.int16)
    for t in range(1, n):
        tot = dp[:, None] + trans
        back[t] = tot.argmax(0)
        dp = tot.max(0) + em[t]
    path = np.zeros(n, dtype=int)
    path[-1] = int(dp.argmax())
    for t in range(n - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path + LOW_PITCH


def _onsets(mag):
    """Spectral flux peaks. Note boundaries come from onsets, not from wobble."""
    np = _require("numpy")
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    flux = flux / (flux.max() + 1e-9)
    w = 15
    pad = np.pad(flux, w, mode="edge")
    local = np.stack([pad[i:i + len(flux)] for i in range(2 * w + 1)]).mean(0)
    peaks, last = [], -99
    for i in range(1, len(flux) - 1):
        if flux[i] > flux[i - 1] and flux[i] >= flux[i + 1] and flux[i] > local[i] * 1.35:
            if i - last >= 4:
                peaks.append(i)
                last = i
    return peaks


def transcribe_audio(path: str | Path, *, name: str | None = None,
                     tempo: int | None = None) -> Ingested:
    """Estimate the leading melodic line of a mixed recording.

    The ``confidence`` on the result is not decoration. It falls when the track
    settles into long stretches of one pitch (the tracker has locked onto a pad
    or a bass rather than a melody) and when consecutive intervals alternate
    (the signature of flip-flopping between two partials). Both are the failure
    modes that make a transcription look like music and mean nothing.
    """
    np = _require("numpy")
    x = decode_audio(path)
    sal, mag = _salience(x)
    pitch = _viterbi(sal)
    energy = sal.max(1)
    ons = _onsets(mag)
    fps = SR / HOP
    floor = float(np.median(energy)) * 0.5

    events: list[Event] = []
    bounds = list(ons) + [len(pitch)]
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 4:
            continue
        seg, e = pitch[a:b], energy[a:b]
        if float(e.mean()) <= floor:
            continue
        vals, counts = np.unique(seg, return_counts=True)
        if counts.max() / len(seg) < 0.5:
            continue                     # the tracker never settled: no note here
        events.append(Event(int(vals[counts.argmax()]),
                            int(a / fps * TPQ * (tempo or 120) / 60),
                            max(1, int((b - a) / fps * TPQ * (tempo or 120) / 60)),
                            80, "melody"))

    est_tempo = tempo or estimate_tempo_from_onsets(ons, fps) or 120
    if tempo is None and est_tempo != 120:      # re-time onto the estimated tempo
        for ev in events:
            ev.start = int(ev.start * est_tempo / 120)
            ev.dur = max(1, int(ev.dur * est_tempo / 120))

    conf, warnings = _confidence(events, len(x) / SR)
    ing = Ingested(name or Path(path).stem, events, est_tempo, "4/4",
                   confidence=conf, source=f"audio:{Path(path).name}", notes=warnings)
    ing.key = estimate_key(events)
    return ing


def _confidence(events: list[Event], seconds: float) -> tuple[float, list[str]]:
    """Score the transcription against its own known failure modes."""
    warnings: list[str] = []
    if len(events) < 8:
        return 0.05, ["almost nothing was extracted; the melody is not separable here"]
    ivs = [b.pitch - a.pitch for a, b in zip(events, events[1:])]
    repeats = sum(1 for i in ivs if i == 0) / len(ivs)
    alternation = (sum(1 for a, b in zip(ivs, ivs[1:]) if a == -b and a != 0)
                   / max(1, len(ivs) - 1))
    rate = len(events) / max(1.0, seconds)
    score = 1.0
    if repeats > 0.35:
        score -= (repeats - 0.35) * 1.6
        warnings.append(
            f"{repeats:.0%} of intervals are repeated notes -- the tracker has "
            f"probably locked onto a sustained pad or bass rather than the melody")
    if alternation > 0.18:
        score -= (alternation - 0.18) * 1.8
        warnings.append(
            f"{alternation:.0%} of interval pairs alternate up-down-up -- the "
            f"signature of flip-flopping between two partials, not a real trill")
    if rate < 1.0:
        score -= 0.25
        warnings.append(f"only {rate:.1f} notes/second recovered; likely under-segmented")
    if rate > 12:
        score -= 0.2
        warnings.append(f"{rate:.1f} notes/second is implausibly dense; likely noise")
    return max(0.02, min(1.0, score)), warnings


def estimate_tempo_from_onsets(onsets: list[int], fps: float) -> int | None:
    """Most common inter-onset interval, folded into a musical tempo range."""
    if len(onsets) < 8:
        return None
    gaps = [(b - a) / fps for a, b in zip(onsets, onsets[1:]) if b > a]
    if not gaps:
        return None
    gaps.sort()
    beat = gaps[len(gaps) // 2]
    if beat <= 0:
        return None
    bpm = 60.0 / beat
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return int(round(bpm))


# --------------------------------------------------------------------------
# estimation
# --------------------------------------------------------------------------

#: Krumhansl-Kessler key profiles: how strongly each scale degree is weighted in
#: music that is genuinely in a key. Correlating a piece's pitch-class durations
#: against these, rotated to all twelve tonics, is the standard key finder.
KK_MAJOR = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
KK_MINOR = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


def estimate_key(events: list[Event]) -> Key | None:
    if not events:
        return None
    weight = [0.0] * 12
    for e in events:
        weight[e.pitch % 12] += e.dur
    total = sum(weight) or 1.0
    weight = [w / total for w in weight]

    def corr(profile, shift):
        rot = [profile[(i - shift) % 12] for i in range(12)]
        mp, mw = sum(rot) / 12, sum(weight) / 12
        num = sum((a - mp) * (b - mw) for a, b in zip(rot, weight))
        den = (sum((a - mp) ** 2 for a in rot) * sum((b - mw) ** 2 for b in weight)) ** 0.5
        return num / den if den else 0.0

    best, best_score = None, -2.0
    for shift in range(12):
        for profile, scale in ((KK_MAJOR, "major"), (KK_MINOR, "minor")):
            s = corr(profile, shift)
            if s > best_score:
                best, best_score = Key(shift, scale), s
    return best


def pitch_class_profile(events: list[Event]) -> dict[str, float]:
    from .theory import SHARP_NAMES
    weight = [0.0] * 12
    for e in events:
        weight[e.pitch % 12] += e.dur
    total = sum(weight) or 1.0
    return {SHARP_NAMES[i]: round(w / total, 4) for i, w in enumerate(weight)}
