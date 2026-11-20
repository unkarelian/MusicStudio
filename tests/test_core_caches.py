"""The core model remembers a few answers a render asks for at every note.
Pieces are edited in place, so each of those must notice an edit."""

import pytest

from musicstudio.doc import Piece, Section
from musicstudio.theory import bar_ticks, parse_meter


def _slow_section_of_tick(piece, tick):
    for sec, _, start in piece.section_bounds():
        if start <= tick < start + sec.length:
            return sec
    return piece.sections[-1]


def _agrees_everywhere(piece):
    for tick in range(-960, piece.total_ticks + 1921, 120):
        assert piece.section_of_tick(tick) is _slow_section_of_tick(piece, tick), tick


def test_section_of_tick_sees_a_form_edited_in_place():
    p = Piece("t", "C major")
    p.sections = [Section("a", 2), Section("b", 3, "3/4"), Section("c", 1, "6/8")]
    _agrees_everywhere(p)
    assert p.section_of_tick(2 * 1920).name == "b"

    p.sections[0].bars = 4                      # a section grows
    assert p.section_of_tick(2 * 1920).name == "a"
    _agrees_everywhere(p)

    p.sections[1].meter = "5/4"                 # a meter changes
    _agrees_everywhere(p)

    p.sections.insert(1, Section("new", 1))     # the list itself changes
    assert p.section_of_tick(4 * 1920).name == "new"
    _agrees_everywhere(p)

    p.sections[1] = Section("swapped", 1)       # same shape, another section
    assert p.section_of_tick(4 * 1920).name == "swapped"

    del p.sections[1:]
    _agrees_everywhere(p)
    assert p.section_of_tick(10 ** 9).name == "a"


def test_section_of_tick_with_a_section_of_no_length_or_no_sections():
    p = Piece("t", "C major")
    assert p.section_of_tick(0).name == ""      # the stand-in, as before
    p.sections = [Section("a", 1), Section("b", 1), Section("c", 1)]
    p.sections[1].bars = 0                      # not a valid form, but not a crash
    _agrees_everywhere(p)
    assert p.section_of_tick(1920).name == "c"


def test_a_bad_meter_is_refused_every_time_and_a_good_one_reads_the_same():
    for _ in range(2):
        with pytest.raises(ValueError, match="bad meter 'four'"):
            parse_meter("four")
        with pytest.raises(ValueError, match="bad meter 44"):
            parse_meter(44)
        assert parse_meter(" 6 / 8 ") == (6, 8)
        assert parse_meter("6/8") == (6, 8)
        assert bar_ticks("6/8") == 1440
