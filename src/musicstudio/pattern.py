"""A small notation for rhythm: write the *shape* of a bar, not its grid.

A lane string such as ``x...x...x...x...`` says where sixteen sixteenths go
and nothing about why. Most of what a drummer plays is better said as a rule:
"three hits spread over eight", "this bar, then that one, in turn", "a roll on
the last beat", "a ghost note, sometimes". This module is that vocabulary. The
idea of writing rhythm as nested, cycling subdivisions comes from the
live-coding pattern languages (TidalCycles and its ports); the grammar and the
implementation here are the studio's own, and deliberately a subset.

One pattern fills one *cycle* (a bar, unless the op says otherwise)::

    x . x .          four equal steps: a hit, a rest, a hit, a rest
    x [x x] . x      a step can itself be divided
    x*4              four hits inside one step            (a roll)
    x!3 o            the step three times, then a ghost   (x x x o)
    x@3 x            the first step lasts three times as long as the second
    x(3,8)           three hits spread as evenly as eight steps allow
    x(3,8,2)         the same, started two steps later
    <x o> x          a different choice each cycle: x x, then o x, then x x ...
    x? o?0.25        a hit half the time; a ghost a quarter of the time
    a | b            whole cycles in turn: the same as <[a] [b]>

``.``, ``~`` and ``-`` are rests. Anything else is a *symbol*, and it is the
caller that says what symbols mean: for a kit, ``x`` is a stroke, ``X`` an
accent and ``o`` a ghost note.

Everything is exact (``Fraction``): a pattern is a function from a cycle number
to ``(start, length, symbol)`` within ``[0, 1)``, and the caller turns those
into ticks. Chance is seeded by the caller, so a render is still a render.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

RESTS = (".", "~", "-")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_SYMBOL = re.compile(r"[^\s\[\]<>()*!@?|,]+")


@dataclass
class Node:
    """One element of a sequence: a symbol, or a group of elements."""

    kind: str                       # 'sym', 'seq' (divide) or 'alt' (one per cycle)
    symbol: str = ""
    children: list["Node"] = field(default_factory=list)
    weight: Fraction = Fraction(1)
    fast: int = 1                   # ``*n``
    euclid: tuple[int, int, int] | None = None
    chance: float | None = None     # ``?``


@dataclass(frozen=True)
class Event:
    start: Fraction                 # within the cycle, 0 <= start < 1
    length: Fraction
    symbol: str
    #: Where in the pattern this came from, for seeding: stable across edits
    #: elsewhere in the piece, different for every hit of the pattern.
    path: tuple


class PatternError(ValueError):
    pass


def parse(text: str) -> Node:
    """Read a pattern. Raises ``PatternError`` with the place it went wrong."""
    src = str(text)
    pos = 0

    def fail(why: str):
        raise PatternError(f"bad pattern {src!r} at character {pos + 1}: {why}")

    def space():
        nonlocal pos
        while pos < len(src) and src[pos].isspace():
            pos += 1

    def number(what: str) -> str:
        nonlocal pos
        m = _NUMBER.match(src, pos)
        if not m:
            fail(f"expected a number for {what}")
        pos = m.end()
        return m.group(0)

    def whole(what: str, least: int = 1) -> int:
        raw = number(what)
        if "." in raw or int(raw) < least:
            fail(f"{what} must be a whole number of at least {least}")
        return int(raw)

    def sequence(closers: str) -> list[Node]:
        nonlocal pos
        out: list[Node] = []
        while True:
            space()
            if pos >= len(src) or src[pos] in closers:
                return out
            out.extend(element())

    def element() -> list[Node]:
        nonlocal pos
        ch = src[pos]
        if ch == "[":
            pos += 1
            node = Node("seq", children=bars("]"))
            if pos >= len(src):
                fail("a '[' is never closed")
            pos += 1
        elif ch == "<":
            pos += 1
            node = Node("alt", children=sequence(">"))
            if pos >= len(src):
                fail("a '<' is never closed")
            if not node.children:
                fail("'<>' needs something to choose from")
            pos += 1
        else:
            m = _SYMBOL.match(src, pos)
            if not m:
                fail(f"unexpected {ch!r}")
            pos = m.end()
            node = Node("sym", symbol=m.group(0))
        copies = 1
        while pos < len(src) and src[pos] in "*!@(?":
            mark = src[pos]
            pos += 1
            if mark == "*":
                node.fast *= whole("'*'")
            elif mark == "!":
                copies *= whole("'!'")
            elif mark == "@":
                node.weight *= Fraction(number("'@'"))
                if node.weight <= 0:
                    fail("'@' needs a length above zero")
            elif mark == "(":
                space()
                hits = whole("the number of hits", 0)
                space()
                if pos >= len(src) or src[pos] != ",":
                    fail("write a spread as (hits,steps), e.g. x(3,8)")
                pos += 1
                space()
                steps = whole("the number of steps")
                space()
                turn = 0
                if pos < len(src) and src[pos] == ",":
                    pos += 1
                    space()
                    turn = whole("the rotation", 0)
                    space()
                if pos >= len(src) or src[pos] != ")":
                    fail("a '(' is never closed")
                pos += 1
                if hits > steps:
                    fail(f"{hits} hits do not fit in {steps} steps")
                node.euclid = (hits, steps, turn % steps)
            else:
                m = _NUMBER.match(src, pos)
                node.chance = float(m.group(0)) if m else 0.5
                if m:
                    pos = m.end()
                if not 0.0 <= node.chance <= 1.0:
                    fail("a chance is between 0 and 1")
        return [node] * copies

    def bars(closers: str) -> list[Node]:
        """A sequence, or several whole ones in turn if it has ``|`` in it."""
        nonlocal pos
        parts = [sequence(closers + "|")]
        while pos < len(src) and src[pos] == "|":
            pos += 1
            parts.append(sequence(closers + "|"))
        parts = [p for p in parts if p]
        if len(parts) <= 1:
            return parts[0] if parts else []
        return [Node("alt", children=[Node("seq", children=p) for p in parts])]

    top = bars("")
    if pos < len(src):
        fail(f"unexpected {src[pos]!r}")
    if not top:
        raise PatternError(f"the pattern {src!r} is empty")
    return Node("seq", children=top)


def spread(hits: int, steps: int, turn: int = 0) -> list[bool]:
    """``hits`` as evenly as ``steps`` allow -- the Euclidean rhythms, which
    are most of the world's common timelines: (3,8) is the tresillo, (5,8)
    the cinquillo, (2,5) and (3,7) the usual odd-metre claves."""
    if hits <= 0:
        return [False] * steps
    # Bjorklund's algorithm: pair off hits and rests, then pair off what is
    # left, until at most one odd group remains. It gives the patterns in the
    # form musicians know them (x.xx.xx. for five in eight, not a rotation).
    a = [[True] for _ in range(hits)]
    b = [[False] for _ in range(steps - hits)]
    while len(b) > 1:
        m = min(len(a), len(b))
        a, b = [a[i] + b[i] for i in range(m)], (a[m:] or b[m:])
    base = [x for group in a + b for x in group]
    return base[-turn:] + base[:-turn] if turn else base


def events(node: Node, cycle: int = 0) -> list[Event]:
    """What the pattern plays in one cycle, in order, rests left out. Chance
    is *not* applied here: an event that might not sound carries its odds in
    ``chances(node)`` -- see ``play``."""
    return [e for e, _ in _walk(node, cycle, Fraction(0), Fraction(1), ())]


def play(node: Node, cycle: int, lucky) -> list[Event]:
    """The cycle's events with chance applied. ``lucky(event, odds)`` decides
    whether a ``?`` event sounds; the caller seeds it."""
    return [e for e, odds in _walk(node, cycle, Fraction(0), Fraction(1), ())
            if odds is None or lucky(e, odds)]


def _walk(node: Node, cycle: int, start: Fraction, length: Fraction, path: tuple):
    if node.fast > 1:
        part = length / node.fast
        once = Node(node.kind, node.symbol, node.children, node.weight, 1, node.euclid,
                    node.chance)
        for i in range(node.fast):
            # Each repeat is its own turn of anything that alternates inside.
            yield from _walk(once, cycle * node.fast + i, start + i * part, part, path + (i,))
        return
    if node.euclid is not None:
        hits, steps, turn = node.euclid
        part = length / steps
        once = Node(node.kind, node.symbol, node.children, node.weight, 1, None, node.chance)
        for i, on in enumerate(spread(hits, steps, turn)):
            if on:
                yield from _walk(once, cycle, start + i * part, part, path + ("e", i))
        return
    if node.kind == "sym":
        if node.symbol not in RESTS:
            yield Event(start, length, node.symbol, path), node.chance
        return
    if node.kind == "alt":
        pick = cycle % len(node.children)
        child = node.children[pick]
        for ev, odds in _walk(child, cycle // len(node.children), start, length,
                              path + ("a", pick)):
            yield ev, (odds if node.chance is None else
                       node.chance if odds is None else odds * node.chance)
        return
    total = sum((c.weight for c in node.children), Fraction(0))
    at = start
    for i, child in enumerate(node.children):
        part = length * child.weight / total
        for ev, odds in _walk(child, cycle, at, part, path + (i,)):
            yield ev, (odds if node.chance is None else
                       node.chance if odds is None else odds * node.chance)
        at += part


def describe(text: str, cycles: int = 1, steps: int = 16) -> str:
    """The pattern drawn on a grid, a line per cycle: what you would have had
    to type. Hits that fall between grid lines are shown on the nearest one,
    and a hit that only sometimes sounds is shown as ``?``."""
    node = parse(text)
    rows = []
    for c in range(cycles):
        row = ["."] * steps
        for ev, odds in _walk(node, c, Fraction(0), Fraction(1), ()):
            i = min(steps - 1, int(ev.start * steps + Fraction(1, 2)))
            row[i] = "?" if odds is not None else ev.symbol[:1]
        rows.append("".join(row))
    return "\n".join(rows)
