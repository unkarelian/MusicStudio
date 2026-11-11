"""Writing a render out as a standard MIDI file.

Hand-rolled rather than pulled from a library, for the same reason the geometry
in a pixel studio is hand-rolled: the format is small, exactly specified, and
the failure mode of getting it slightly wrong is a file that opens but sounds
wrong. Format 1, one track per voice, with the tempo and meter map on track 0
so a DAW picks up the form.
"""

from __future__ import annotations

import struct
from pathlib import Path

from .doc import Piece
from .render import Render, render
from .theory import TPQ, parse_meter


def _vlq(n: int) -> bytes:
    """Variable-length quantity: seven bits per byte, high bit set to continue."""
    if n < 0:
        raise ValueError(f"negative delta time {n}")
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def _chunk(tag: bytes, body: bytes) -> bytes:
    return tag + struct.pack(">I", len(body)) + body


def _track(events: list[tuple[int, bytes]]) -> bytes:
    """Sort by tick, delta-encode, terminate.

    Note-offs sort before note-ons at the same tick so that a repeated pitch
    retriggers instead of the off silencing the note that just started.
    """
    events.sort(key=lambda e: (e[0], 0 if e[1][:1] and (e[1][0] & 0xF0) == 0x80 else 1))
    body, last = bytearray(), 0
    for tick, data in events:
        body += _vlq(tick - last) + data
        last = tick
    body += _vlq(0) + b"\xff\x2f\x00"
    return _chunk(b"MTrk", bytes(body))


def _channels(piece: Piece) -> dict[str, int]:
    """Channel 9 is percussion; everyone else takes the next free channel."""
    out, nxt = {}, 0
    for v in piece.voices:
        if v.inst.percussive:
            out[v.name] = 9
            continue
        while nxt == 9:
            nxt += 1
        if nxt > 15:
            # More than fifteen melodic voices: wrap and share, which is better
            # than refusing to export.
            nxt = 0
        out[v.name] = nxt
        nxt += 1
    return out


def _sounding_ends(notes) -> list[int]:
    """Where each note's note-off goes, so that no pitch is ever on twice.

    MIDI has one note-off per pitch per channel. If a string is struck again
    while it is still ringing -- a pedalled arpeggio, or two notes nudged into
    each other by humanized timing -- the first note's off arrives during the
    second and silences it. So a note ends, at the latest, where the next note
    of the same pitch begins.
    """
    ends = [max(n.start + 1, n.end) for n in notes]
    last: dict[int, int] = {}
    for i in sorted(range(len(notes)), key=lambda i: notes[i].start):
        j = last.get(notes[i].pitch)
        if j is not None and ends[j] > notes[i].start:
            ends[j] = max(notes[j].start + 1, notes[i].start)
        last[notes[i].pitch] = i
    return ends


#: Channel volume that a trim of 0 dB is written as. Below the usual 100 so a
#: quiet instrument has room to be turned *up*.
TRIM_BASE = 72


def trim_to_volume(db: float) -> int:
    """A level trim in dB as a MIDI channel volume. The SoundFont volume curve
    is 40 log10(v/127), so 12 dB is a factor of two in the controller value."""
    return max(1, min(127, round(TRIM_BASE * 10 ** (db / 40.0))))


def to_bytes(piece: Piece, rend: Render | None = None, *,
             velocity_curve: float | dict[str, float] = 1.0,
             trims: dict[str, float] | None = None,
             time_scale: float = 1.0) -> bytes:
    """The piece as a format-1 MIDI file.

    ``time_scale`` stretches the whole file in time without touching a note: 1.26
    makes it 26% slower. It exists so a sampled drum part can be rendered slow
    and then played back fast, which pitches it up the way a sped-up break is.

    ``trims`` is ``{voice: dB}``, written as channel volume. It is how a
    sampler whose violin is quieter than its horn is brought back to the
    balance the piece was written with; without it no volume is written at all.

    ``velocity_curve`` is an exponent on normalized velocity. 1.0 writes the
    velocities as rendered, which is what a file meant for a DAW should carry.
    Below 1 lifts the quiet notes: samplers map velocity to loudness far more
    steeply than the built-in render does, and without it a ``p`` accompaniment
    under an ``mf`` tune all but disappears. A dict gives each voice its own,
    since a bank's piano and its strings do not respond alike.
    """
    r = rend if rend is not None else render(piece)
    chans = _channels(piece)
    from .audio import pan_positions
    pans = pan_positions(piece)

    meta: list[tuple[int, bytes]] = [(0, b"\xff\x03" + _len(piece.name.encode("utf-8")))]
    for tick, bpm in piece.tempo_map():
        usec = int(60_000_000 / max(1.0, bpm))
        meta.append((tick, b"\xff\x51\x03" + struct.pack(">I", usec)[1:]))
    for sec, _, tick in piece.section_bounds():
        num, den = parse_meter(sec.meter)
        power = max(0, den.bit_length() - 1)
        meta.append((tick, b"\xff\x58\x04" + bytes([num, power, 24, 8])))
        meta.append((tick, b"\xff\x06" + _len(sec.name.encode("utf-8"))))
    tracks = [_track(meta)]
    kit_sent = False

    for v in piece.voices:
        notes = [n for n in r.notes if n.voice == v.name]
        ch = chans[v.name]
        ev: list[tuple[int, bytes]] = [
            (0, b"\xff\x03" + _len(f"{v.name} ({v.instrument})".encode("utf-8")))]
        if v.inst.percussive and v.instrument.startswith("kit") and not kit_sent:
            # One drum channel, so one kit per piece: the first kit voice picks.
            ev.append((0, bytes([0xC0 | ch, v.inst.program & 0x7F])))
            kit_sent = True
        if not v.inst.percussive:
            ev.append((0, bytes([0xC0 | ch, v.inst.program & 0x7F])))
            # The seating plan travels with the file, so a sampler or a DAW puts
            # the players where the built-in render does. Not for the drum
            # channel: it is shared, and kits carry their own panning.
            pan = max(0, min(127, int(round(64 + 63 * pans.get(v.name, 0.0)))))
            ev.append((0, bytes([0xB0 | ch, 10, pan])))
            ev.append((0, bytes([0xB0 | ch, 91, 30 if v.role == "bass" else 52])))
        if trims is not None:
            ev.append((0, bytes([0xB0 | ch, 7, trim_to_volume(trims.get(v.name, 0.0))])))
        curve = (velocity_curve.get(v.name, 1.0) if isinstance(velocity_curve, dict)
                 else velocity_curve)
        for n, end in zip(notes, _sounding_ends(notes)):
            vel = max(1, min(127, n.velocity))
            if curve != 1.0:
                vel = max(1, min(127, round(127 * (vel / 127) ** curve)))
            pitch = max(0, min(127, n.pitch))
            if n.lyric and n.lyric != "-":
                # A lyric meta event, so a notation program shows the words.
                ev.append((n.start, b"\xff\x05" + _len(n.lyric.encode("utf-8"))))
            ev.append((n.start, bytes([0x90 | ch, pitch, vel])))
            ev.append((end, bytes([0x80 | ch, pitch, 0])))
        tracks.append(_track(ev))

    # Fewer ticks per quarter in the header makes every tick last longer.
    division = max(24, min(32767, round(TPQ / time_scale)))
    header = _chunk(b"MThd", struct.pack(">HHH", 1, len(tracks), division))
    return header + b"".join(tracks)


def _len(b: bytes) -> bytes:
    return _vlq(len(b)) + b


def save_midi(piece: Piece, path: str | Path, rend: Render | None = None, *,
              velocity_curve: float | dict[str, float] = 1.0,
              trims: dict[str, float] | None = None,
              time_scale: float = 1.0) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(to_bytes(piece, rend, velocity_curve=velocity_curve, trims=trims,
                           time_scale=time_scale))
    return p
