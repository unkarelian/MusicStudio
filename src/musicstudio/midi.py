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


def to_bytes(piece: Piece, rend: Render | None = None) -> bytes:
    r = rend if rend is not None else render(piece)
    chans = _channels(piece)

    meta: list[tuple[int, bytes]] = [(0, b"\xff\x03" + _len(piece.name.encode("utf-8")))]
    for sec, _, tick in piece.section_bounds():
        usec = int(60_000_000 / max(1, piece.tempo_of(sec)))
        meta.append((tick, b"\xff\x51\x03" + struct.pack(">I", usec)[1:]))
        num, den = parse_meter(sec.meter)
        power = max(0, den.bit_length() - 1)
        meta.append((tick, b"\xff\x58\x04" + bytes([num, power, 24, 8])))
        meta.append((tick, b"\xff\x06" + _len(sec.name.encode("utf-8"))))
    tracks = [_track(meta)]

    for v in piece.voices:
        notes = [n for n in r.notes if n.voice == v.name]
        ch = chans[v.name]
        ev: list[tuple[int, bytes]] = [
            (0, b"\xff\x03" + _len(f"{v.name} ({v.instrument})".encode("utf-8")))]
        if not v.inst.percussive:
            ev.append((0, bytes([0xC0 | ch, v.inst.program & 0x7F])))
        for n in notes:
            vel = max(1, min(127, n.velocity))
            pitch = max(0, min(127, n.pitch))
            ev.append((n.start, bytes([0x90 | ch, pitch, vel])))
            ev.append((max(n.start + 1, n.end), bytes([0x80 | ch, pitch, 0])))
        tracks.append(_track(ev))

    header = _chunk(b"MThd", struct.pack(">HHH", 1, len(tracks), TPQ))
    return header + b"".join(tracks)


def _len(b: bytes) -> bytes:
    return _vlq(len(b)) + b


def save_midi(piece: Piece, path: str | Path, rend: Render | None = None) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(to_bytes(piece, rend))
    return p
