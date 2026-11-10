"""MusicStudio - a music studio built for agents.

Pieces are op-logs over a harmonic scaffold, not note lists; pitch is scale
degrees, not MIDI numbers; motifs are named objects with a transformation
algebra, so a theme that comes back inverted is provably the same theme. Every
edit hands back a readable view plus a critique.

See ``studio.Studio`` for the session API, ``doc.OP_SPECS`` for the op
vocabulary, and ``motif.TRANSFORMS`` for the development vocabulary.
"""

from .audio import save_wav
from .doc import OP_SPECS, HarmonyEntry, Op, Piece, Section, Voice
from .ensemble import INSTRUMENTS, Instrument, get_instrument
from .lint import Finding, lint, report
from .midi import save_midi
from .motif import TRANSFORMS, Motif, Step, apply_transform, make_motif, similarity
from .readback import chart, motif_map, score, squint, stats, voice_view
from .render import Note, Render, render
from .studio import OpResult, Studio
from .style import STYLES, StyleProfile, get_style
from .theory import Chord, Key, parse_chord, pitch_name, ticks

__version__ = "0.3.0"
__all__ = [
    "Key", "Chord", "parse_chord", "pitch_name", "ticks",
    "Motif", "Step", "make_motif", "apply_transform", "similarity", "TRANSFORMS",
    "Piece", "Section", "Voice", "Op", "HarmonyEntry", "OP_SPECS",
    "Instrument", "INSTRUMENTS", "get_instrument",
    "render", "Render", "Note",
    "score", "chart", "motif_map", "squint", "voice_view", "stats",
    "lint", "report", "Finding",
    "Studio", "OpResult", "StyleProfile", "STYLES", "get_style",
    "save_midi", "save_wav",
]
