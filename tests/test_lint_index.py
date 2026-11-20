"""The shared index lint builds once must not change what any check says.

Each check takes the index as an optional last argument; called on its own it
builds one. Both ways, and the whole pass, must agree.
"""

import importlib
from pathlib import Path

import pytest

from musicstudio import Studio
from musicstudio.render import render
from musicstudio.score import _strip_comment
from musicstudio.style import get_style

# `musicstudio.lint` the attribute is the function; this is the module.
lint = importlib.import_module("musicstudio.lint")
GALLERY = Path(__file__).resolve().parent.parent / "gallery"


@pytest.mark.parametrize("name", ["dusk", "lanterns"])
def test_each_check_says_the_same_alone_and_inside_the_pass(name):
    piece = Studio(GALLERY).get(name)
    rend = render(piece)
    style = get_style(piece.style)
    shared = lint._Index(piece, rend)
    alone: list[str] = []
    for check in lint.CHECKS:
        mine = [str(f) for f in check(piece, rend, style)]
        assert mine == [str(f) for f in check(piece, rend, style, shared)], check.__name__
        alone += mine
    assert sorted(alone) == sorted(str(f) for f in lint.lint(piece, rend))


def test_the_index_agrees_with_the_scans_it_replaces():
    piece = Studio(GALLERY).get("dusk")
    rend = render(piece)
    ix = lint._Index(piece, rend)
    for v in piece.voices:
        assert ix.voice(v.name) == rend.by_voice(v.name)
    for s, by in zip(ix.moments, ix.moment_voices):
        for v in piece.voices:
            assert by.get(v.name, []) == s.voice(v.name)


@pytest.mark.parametrize("raw, kept", [
    ("  play motif=hero at=1   ", "  play motif=hero at=1"),
    ("  play motif=hero at=1  # a comment", "  play motif=hero at=1"),
    ("  phrase steps=\"#4 5\" at=1", "  phrase steps=\"#4 5\" at=1"),
    ("  phrase steps=\"0 # 1\" at=1 # gone", "  phrase steps=\"0 # 1\" at=1"),
    ("  play motif=hero at=1   -- a note # kept  ", "  play motif=hero at=1   -- a note # kept"),
    ("# only a comment", ""),
])
def test_a_comment_is_stripped_and_a_sharp_is_not(raw, kept):
    assert _strip_comment(raw) == kept
