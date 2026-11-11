"""The score language: a piece as one text file.

A piece is an op-log, and an op-log is text. Driving it one call at a time --
`add_op`, look, `update_op`, look -- is right for a single change and wrong for
writing: a piece of two hundred ops is two hundred round trips, and a revision
is a hunt for the call that made the thing being revised. So the whole log can
be written down, read, searched and edited as a file, and compiled in one step:

    piece dusk key="A minor" tempo=84 style=orchestral

    section A bars=8 dynamic=p
    section B bars=8 dynamic=f

    harmony
      1: i i VI VII | i iv V7 i          # one chord a bar, from bar 1
                                         # (a comment is `# ` with a space: #4 is a sharp)
      @B: [VI VII]*3 V7 i                # from a section; groups repeat
      @B.7:3: V7                         # a change inside a bar

    motif hero = 0 2 4:1/4 3 2:1/2       -- the tune
    motif hero_wide < hero : augment:2 > transpose:2

    lanes ROCK
      kick:  x.....x.x.......
      snare: ....x.......x...

    voice violin violin role=melody octave=5
      theme_a: play motif=hero at=@A dynamic=mf      -- stated plainly
      theme_b: play motif=hero_wide at=@B.3
      shape amount=0.5                               # an id is made if none is given

    voice drums kit role=percussion
      beat at=@B bars=8 lanes=$ROCK crash=x

    on violin viola                      # the same ops on several voices
      {v}_soft: dynamics in=@A start=p end=mp

    for k in 0..3                        # a block repeated; {…} is arithmetic
      voice bell{k} celesta role=ornament
        phrase at={1 + 4*k} steps="7:1/1"

It is the same model and nothing else: every line is one section, chord, motif,
voice or op, with the op's own parameters under their own names (`ms ops`), so
the language has no vocabulary of its own to learn or to drift. What it adds is
only what makes a file pleasant: positions by section (``@B.3:2`` is beat 2 of
B's third bar, ``@B.end`` the bar after it, ``in=@B`` or ``in=@B.3-6`` a span),
named lane sets, constants (``set NAME = value``, used as ``$NAME``), and
``for``/``on`` blocks. ``compile_score`` builds the piece in memory and
nothing is written unless all of it parses, validates and renders.

Motif identity is kept the way the studio keeps it: ``<`` derives, through the
same transforms, and the lineage is recorded by them. (``recorded`` exists so a
piece written before the language can be written out as text when a transform
did not store its arguments; it restates the lineage the file already had.)
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .doc import HarmonyEntry, OP_SPECS, Piece, Section, Voice
from .ensemble import KIT_DRUMS
from .motif import Motif, apply_transform, make_motif


class _Quoted(str):
    """A value that was written in quotes: text, never a reference."""


class ScoreError(ValueError):
    """A problem in a score file, with the line it is on."""

    def __init__(self, message: str, line: int | None = None, text: str = ""):
        self.line = line
        where = f"line {line}: " if line else ""
        shown = f"\n    {text.strip()}" if text.strip() else ""
        super().__init__(f"{where}{message}{shown}")


@dataclass
class _Line:
    no: int
    indent: int
    text: str
    body: list["_Line"] = field(default_factory=list)


# --------------------------------------------------------------------------
# lines, blocks, loops
# --------------------------------------------------------------------------

def _strip_comment(raw: str) -> str:
    out, quote = [], False
    for i, ch in enumerate(raw):
        if ch == '"' and (i == 0 or raw[i - 1] != "\\"):
            quote = not quote
        # A note runs to the end of the line, `#` and all: it is the writer's
        # sentence, and a piece written out must read back the same.
        if not quote and raw.startswith(" -- ", i):
            return raw.rstrip()
        # `# ` starts a comment; `#4` is a sharpened degree.
        if ch == "#" and not quote and (i == 0 or raw[i - 1].isspace()) and \
                (i + 1 == len(raw) or raw[i + 1].isspace()):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _tree(text: str) -> list[_Line]:
    """Lines nested by indentation."""
    root: list[_Line] = []
    stack: list[_Line] = []
    for no, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[:len(raw) - len(raw.lstrip())]:
            raise ScoreError("indent with spaces, not tabs", no, raw)
        line = _strip_comment(raw)
        if not line.strip():
            continue
        node = _Line(no, len(line) - len(line.lstrip()), line.strip())
        while stack and stack[-1].indent >= node.indent:
            stack.pop()
        (stack[-1].body if stack else root).append(node)
        stack.append(node)
    return root


_ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.USub,
            ast.IfExp, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.List, ast.Tuple, ast.Subscript, ast.BoolOp, ast.And, ast.Or)


def _evaluate(expr: str, env: dict, line: _Line) -> Any:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError:
        raise ScoreError(f"cannot read {{{expr}}}", line.no, line.text) from None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ScoreError(f"{{{expr}}} may only do arithmetic on loop variables",
                             line.no, line.text)
        if isinstance(node, ast.Name) and node.id not in env:
            raise ScoreError(f"{{{expr}}}: no loop variable {node.id!r} here "
                             f"(have {sorted(env) or 'none'})", line.no, line.text)
    value = eval(compile(tree, "<score>", "eval"), {"__builtins__": {}}, dict(env))
    if isinstance(value, float) and value == int(value):
        value = int(value)
    return value


def _fill(text: str, env: dict, line: _Line) -> str:
    if "{" not in text or not env:
        return text
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == '"':                              # quoted text is left as written
            j = i + 1
            while j < len(text) and not (text[j] == '"' and text[j - 1] != "\\"):
                j += 1
            j = min(len(text), j + 1)
            out.append(text[i:j])
            i = j
        elif ch == "{":
            j = text.find("}", i)
            inner = text[i + 1:j] if j > 0 else ""
            if j > 0 and re.fullmatch(r"[\w\s+\-*/%()<>=!,.\[\]]+", inner) and \
                    any(re.search(rf"\b{re.escape(k)}\b", inner) for k in env):
                out.append(str(_evaluate(inner, env, line)))
                i = j + 1
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _expand(nodes: list[_Line], env: dict) -> list[_Line]:
    """Unroll ``for`` blocks and substitute ``{…}``."""
    out: list[_Line] = []
    for node in nodes:
        m = re.fullmatch(r"for\s+(\w+)\s+in\s+(.+?):?", node.text)
        if m:
            name, spec = m.group(1), _fill(m.group(2), env, node).strip()
            r = re.fullmatch(r"(-?\d+)\s*\.\.\s*(-?\d+)", spec)
            values: list = (list(range(int(r.group(1)), int(r.group(2)) + 1)) if r
                            else [_scalar(tok) for tok in spec.split()])
            if not node.body:
                raise ScoreError("a `for` needs an indented block under it", node.no,
                                 node.text)
            for value in values:
                for child in _expand(node.body, {**env, name: value}):
                    out.append(child)
            continue
        out.append(_Line(node.no, node.indent, _fill(node.text, env, node),
                         _expand(node.body, env)))
    return out


# --------------------------------------------------------------------------
# values
# --------------------------------------------------------------------------

def _scalar(tok: str) -> Any:
    low = tok.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "none"):
        return None
    if re.fullmatch(r"[+-]?\d+", tok):
        return int(tok)
    if re.fullmatch(r"[+-]?(\d+\.\d*|\.\d+)", tok):
        return float(tok)
    return tok


def _split_note(text: str) -> tuple[str, str]:
    quote = False
    for i in range(len(text) - 1):
        if text[i] == '"' and (i == 0 or text[i - 1] != "\\"):
            quote = not quote
        if not quote and text.startswith(" -- ", i):
            return text[:i].rstrip(), text[i + 4:].strip()
    return text, ""


def _pairs(text: str, line: _Line) -> tuple[list[str], dict[str, Any]]:
    """``word word key=value key="two words" key=[1, 2]`` -> bare words, pairs."""
    words: list[str] = []
    pairs: dict[str, Any] = {}
    i, n = 0, len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        m = re.match(r"([A-Za-z_][\w.]*)=", text[i:])
        if not m:
            j = i
            while j < n and not text[j].isspace():
                j += 1
            words.append(text[i:j])
            i = j
            continue
        key = m.group(1)
        i += m.end()
        if i < n and text[i] == '"':
            j = i + 1
            while j < n and not (text[j] == '"' and text[j - 1] != "\\"):
                j += 1
            if j >= n:
                raise ScoreError(f"unclosed quote in {key}=", line.no, line.text)
            value: Any = _Quoted(text[i + 1:j].replace('\\"', '"'))
            i = j + 1
        elif i < n and text[i] in "[{":
            close = {"[": "]", "{": "}"}
            depth, j, quote = 0, i, False
            while j < n:
                if text[j] == '"' and text[j - 1] != "\\":
                    quote = not quote
                elif not quote and text[j] in "[{":
                    depth += 1
                elif not quote and text[j] in "]}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= n:
                raise ScoreError(f"unclosed {text[i]} … {close[text[i]]} in {key}=",
                                 line.no, line.text)
            raw = text[i:j + 1]
            try:
                value = json.loads(raw)
            except ValueError:
                if raw[0] != "[":
                    raise ScoreError(f"{key}= is not valid JSON", line.no,
                                     line.text) from None
                value = [_scalar(t.strip().strip('"')) for t in raw[1:-1].split(",")
                         if t.strip()]
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace():
                j += 1
            value = _scalar(text[i:j])
            i = j
        if key in pairs:
            raise ScoreError(f"{key}= is given twice", line.no, line.text)
        pairs[key] = value
    return words, pairs


# --------------------------------------------------------------------------
# the compiler
# --------------------------------------------------------------------------

class _Compiler:
    def __init__(self) -> None:
        self.piece: Piece | None = None
        self.consts: dict[str, Any] = {}
        self.lanes: dict[str, dict[str, str]] = {}
        self.pending_ops: list[tuple[str, _Line]] = []
        self.harmony: list[_Line] = []
        self.master: dict = {}
        self.auto: dict[str, int] = {}

    # -- positions ---------------------------------------------------------

    def _start(self, section: str, line: _Line) -> tuple[int, int]:
        bar = 1
        for sec in self.piece.sections:
            if sec.name == section:
                return bar, sec.bars
            bar += sec.bars
        raise ScoreError(f"no section {section!r} (have "
                         f"{[s.name for s in self.piece.sections]}); sections must be "
                         f"declared before they are used", line.no, line.text)

    def position(self, value: Any, line: _Line) -> Any:
        if not isinstance(value, str) or not value.startswith("@"):
            return value
        m = re.fullmatch(r"@([A-Za-z_]\w*)(?:\.(end|\d+))?(?::([\d.]+))?", value)
        if not m:
            raise ScoreError(f"cannot read the position {value!r}: write @section, "
                             f"@section.3, @section.3:2.5 or @section.end", line.no,
                             line.text)
        first, bars = self._start(m.group(1), line)
        which = m.group(2)
        if which == "end":
            bar = first + bars
        else:
            n = int(which) if which else 1
            if not 1 <= n <= bars:
                raise ScoreError(f"{value}: section {m.group(1)!r} has {bars} bars",
                                 line.no, line.text)
            bar = first + n - 1
        return f"{bar}:{m.group(3)}" if m.group(3) else str(bar)

    def span(self, value: Any, line: _Line) -> tuple[str, str]:
        m = re.fullmatch(r"@([A-Za-z_]\w*)(?:\.(\d+)-(\d+))?", str(value))
        if not m:
            raise ScoreError(f"in={value}: write in=@section or in=@section.3-6", line.no,
                             line.text)
        first, bars = self._start(m.group(1), line)
        a = int(m.group(2)) if m.group(2) else 1
        z = int(m.group(3)) if m.group(3) else bars
        if not 1 <= a <= z <= bars:
            raise ScoreError(f"in={value}: section {m.group(1)!r} has {bars} bars",
                             line.no, line.text)
        return str(first + a - 1), str(first + z)

    def resolve(self, value: Any, line: _Line) -> Any:
        # Only a bare word is a reference. "@A" in quotes is a lyric that
        # happens to start with an at-sign, and JSON is taken as written.
        if isinstance(value, _Quoted):
            return str(value)
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str) and value.startswith("$"):
            name = value[1:]
            if name in self.lanes:
                return dict(self.lanes[name])
            if name in self.consts:
                return self.consts[name]
            raise ScoreError(f"nothing is named {value} (set and lanes: "
                             f"{sorted(self.consts) + sorted(self.lanes)})", line.no,
                             line.text)
        return self.position(value, line)

    # -- statements --------------------------------------------------------

    def run(self, nodes: list[_Line]) -> Piece:
        for node in nodes:
            head = node.text.split(None, 1)[0].rstrip(":")
            handler = getattr(self, f"_do_{head}", None)
            if handler is None:
                raise ScoreError(
                    f"a top-level line starts with one of: piece, master, stop, meta, "
                    f"section, harmony, motif, lanes, set, voice, on, for -- not "
                    f"{head!r}", node.no, node.text)
            if head != "piece" and self.piece is None:
                raise ScoreError("the first line names the piece: "
                                 "piece NAME key=\"C major\" tempo=90 style=…", node.no,
                                 node.text)
            handler(node)
        if self.piece is None:
            raise ScoreError("the file is empty: it needs at least a `piece` line")
        self._finish()
        return self.piece

    def _do_piece(self, node: _Line) -> None:
        if self.piece is not None:
            raise ScoreError("one piece to a file", node.no, node.text)
        text, _ = _split_note(node.text)
        words, kv = _pairs(text.split(None, 1)[1] if " " in text else "", node)
        if len(words) != 1 and not (len(words) == 2 and words[1] == "loop"):
            raise ScoreError("piece NAME key=\"C major\" tempo=90 style=orchestral",
                             node.no, node.text)
        from .style import get_style
        style = str(kv.pop("style", "orchestral"))
        tempo = int(kv.pop("tempo", 90))
        try:
            st = get_style(style)
        except KeyError as exc:
            raise ScoreError(str(exc).strip('"'), node.no, node.text) from None
        if not st.tempo_range[0] <= tempo <= st.tempo_range[1]:
            raise ScoreError(f"tempo {tempo} is outside style {style!r}'s range "
                             f"{st.tempo_range}", node.no, node.text)
        self.piece = Piece(words[0], str(kv.pop("key", "C major")), tempo=tempo,
                           meter=str(kv.pop("meter", "4/4")), style=style,
                           loop=bool(kv.pop("loop", len(words) == 2)))
        if kv:
            raise ScoreError(f"piece does not take {sorted(kv)}", node.no, node.text)

    def _do_master(self, node: _Line) -> None:
        text, _ = _split_note(node.text)
        words, kv = _pairs(text.split(None, 1)[1] if " " in text else "", node)
        if words:
            raise ScoreError(f"stray word {words[0]!r} on a master line", node.no, node.text)
        for key, value in kv.items():
            if key.startswith("room."):
                self.master.setdefault("room", {})[key[5:]] = float(value)
            elif key in ("push", "clip", "level"):
                self.master[key] = float(value)
            else:
                raise ScoreError(f"master takes push, clip, level, room.decay and "
                                 f"room.wet -- not {key}", node.no, node.text)

    def _do_stop(self, node: _Line) -> None:
        text, _ = _split_note(node.text)
        _, kv = _pairs(text.split(None, 1)[1] if " " in text else "", node)
        if "in" in kv:
            kv["from"], kv["until"] = self.span(kv.pop("in"), node)
        if "from" not in kv or "until" not in kv:
            raise ScoreError("stop from=… until=… [keep=[voice, …]]", node.no, node.text)
        self.master.setdefault("stops", []).append(
            {"from": str(self.position(kv["from"], node)),
             "until": str(self.position(kv["until"], node)),
             "keep": list(kv.get("keep") or [])})

    def _do_meta(self, node: _Line) -> None:
        m = re.fullmatch(r"meta\s+(\w+)\s*=\s*(.+)", node.text)
        if not m:
            raise ScoreError("meta KEY = <json>", node.no, node.text)
        try:
            self.piece.meta[m.group(1)] = json.loads(m.group(2))
        except ValueError:
            raise ScoreError("the value of a meta line is JSON", node.no,
                             node.text) from None

    def _do_set(self, node: _Line) -> None:
        m = re.fullmatch(r"set\s+(\w+)\s*=\s*(.+)", node.text)
        if not m:
            raise ScoreError("set NAME = value", node.no, node.text)
        _, kv = _pairs(f"v={m.group(2).strip()}", node)
        self.consts[m.group(1)] = kv["v"]

    def _do_section(self, node: _Line) -> None:
        text, note = _split_note(node.text)
        words, kv = _pairs(text.split(None, 1)[1] if " " in text else "", node)
        if len(words) != 1:
            raise ScoreError("section NAME bars=8 dynamic=mf", node.no, node.text)
        if any(s.name == words[0] for s in self.piece.sections):
            raise ScoreError(f"section {words[0]!r} is declared twice", node.no, node.text)
        known = {"bars", "meter", "tempo", "key", "dynamic", "tempo_end"}
        if set(kv) - known:
            raise ScoreError(f"section takes {sorted(known)} -- not "
                             f"{sorted(set(kv) - known)}", node.no, node.text)
        self.piece.sections.append(Section(
            words[0], int(kv.get("bars", 8)), str(kv.get("meter") or self.piece.meter),
            kv.get("tempo"), kv.get("key"), str(kv.get("dynamic", "mf")), note,
            kv.get("tempo_end")))

    def _do_harmony(self, node: _Line) -> None:
        if not node.body:
            raise ScoreError("harmony needs indented lines under it: `1: i iv V i`",
                             node.no, node.text)
        self.harmony += node.body

    def _harmony(self) -> None:
        entries: list[HarmonyEntry] = []
        for line in self.harmony:
            text, note = _split_note(line.text)
            m = re.match(r"(@[\w.]+(?::[\d.]+)?|\d+(?::[\d.]+)?)\s*:\s*(.+)", text)
            if not m:
                raise ScoreError("a harmony line is `BAR: chord chord …` (one chord a "
                                 "bar) or `BAR:BEAT: chord`", line.no, line.text)
            at = str(self.position(m.group(1), line))
            chords = self._chords(m.group(2), line)
            if ":" in at:
                if len(chords) != 1:
                    raise ScoreError("a line that starts inside a bar holds one chord",
                                     line.no, line.text)
                entries.append(HarmonyEntry(at, chords[0][0], chords[0][1], note))
                continue
            bar = int(at)
            for chord, dur in chords:
                entries.append(HarmonyEntry(str(bar), chord, dur, note))
                bar += 1
        entries.sort(key=lambda e: self.piece.tick_of(e.at))
        self.piece.harmony = entries
        for e in entries:
            try:
                self.piece.chord_at(self.piece.tick_of(e.at))
            except (ValueError, KeyError) as exc:
                raise ScoreError(f"harmony at {e.at}: {exc}") from None

    def _chords(self, text: str, line: _Line) -> list[tuple[str, str | None]]:
        text = text.replace("|", " ")
        while True:
            m = re.search(r"\[([^\[\]]*)\]\s*\*\s*(\d+)", text)
            if not m:
                break
            text = text[:m.start()] + " ".join([m.group(1)] * int(m.group(2))) + text[m.end():]
        out: list[tuple[str, str | None]] = []
        for tok in text.split():
            m = re.fullmatch(r"(.+?)\*(\d+)", tok)
            reps = int(m.group(2)) if m else 1
            chord = m.group(1) if m else tok
            dur = None
            if "~" in chord:
                chord, dur = chord.split("~", 1)
            if not chord or "[" in chord or "]" in chord:
                raise ScoreError(f"cannot read the chord {tok!r}", line.no, line.text)
            out += [(chord, dur)] * reps
        return out

    def _do_motif(self, node: _Line) -> None:
        text, note = _split_note(node.text)
        m = re.fullmatch(r"motif\s+(\w+)\s*<\s*(\w+)\s+recorded\s+\"([^\"]*)\"\s*=\s*(.+)",
                         text)
        if m:                                      # written out by `decompile`
            name, parent, lineage, rest = m.groups()
            steps, kv = self._motif_source(rest, node)
            made = make_motif(name, steps, **kv)
            self._put_motif(Motif(name, made.steps, made.anchor, made.scale, made.unit,
                                  note, parent,
                                  tuple(t for t in lineage.split(" + ") if t)), node)
            return
        m = re.fullmatch(r"motif\s+(\w+)\s*<\s*(\w+)\s*:\s*(.+)", text)
        if m:
            name, parent, chain = m.groups()
            try:
                made = self.piece.get_motif(parent)
                for t in (c.strip() for c in chain.split(" > ")):
                    made = apply_transform(made, t, resolve=self.piece.get_motif)
            except (KeyError, ValueError, TypeError) as exc:
                raise ScoreError(str(exc).strip('"'), node.no, node.text) from None
            self._put_motif(Motif(name, made.steps, made.anchor, made.scale, made.unit,
                                  note or made.note, made.derived_from or parent,
                                  made.lineage), node)
            return
        m = re.fullmatch(r"motif\s+(\w+)\s*=\s*(.+)", text)
        if not m:
            raise ScoreError("motif NAME = 0 2 4:1/4 …   or   "
                             "motif NAME < PARENT : transform > transform", node.no,
                             node.text)
        steps, kv = self._motif_source(m.group(2), node)
        try:
            made = make_motif(m.group(1), steps, note=note, **kv)
        except (ValueError, KeyError) as exc:
            raise ScoreError(str(exc).strip('"'), node.no, node.text) from None
        self._put_motif(made, node)

    def _motif_source(self, rest: str, node: _Line) -> tuple[str, dict]:
        kv: dict = {}
        while True:
            m = re.search(r"\s+(anchor|unit|scale)=(\"[^\"]*\"|\S+)\s*$", rest)
            if not m:
                break
            kv[m.group(1)] = m.group(2).strip('"')
            rest = rest[:m.start()]
        return rest.strip(), kv

    def _put_motif(self, motif: Motif, node: _Line) -> None:
        if motif.name in self.piece.motifs:
            raise ScoreError(f"motif {motif.name!r} is defined twice", node.no, node.text)
        self.piece.motifs[motif.name] = motif

    def _do_lanes(self, node: _Line) -> None:
        words = node.text.split()
        if len(words) != 2 or not node.body:
            raise ScoreError("lanes NAME, then indented `drum: pattern` lines", node.no,
                             node.text)
        lanes: dict[str, str] = {}
        for line in node.body:
            drum, sep, pattern = line.text.partition(":")
            if not sep or drum.strip() not in KIT_DRUMS:
                raise ScoreError(f"a lane is `drum: pattern`; drums are "
                                 f"{sorted(KIT_DRUMS)}", line.no, line.text)
            lanes[drum.strip()] = pattern.strip().strip('"')
        self.lanes[words[1]] = lanes

    def _do_voice(self, node: _Line) -> None:
        text, _ = _split_note(node.text)
        words, kv = _pairs(text.split(None, 1)[1] if " " in text else "", node)
        if len(words) != 2:
            raise ScoreError("voice NAME INSTRUMENT role=melody [octave= pan= engine= "
                             "bank= dynamic= muted=]", node.no, node.text)
        name, instrument = words
        if any(v.name == name for v in self.piece.voices):
            raise ScoreError(f"voice {name!r} is declared twice; to add ops to it from "
                             f"elsewhere in the file use `on {name}`", node.no, node.text)
        from .ensemble import ROLES, get_instrument
        try:
            get_instrument(instrument)
        except KeyError as exc:
            raise ScoreError(str(exc).strip('"'), node.no, node.text) from None
        known = {"role", "octave", "dynamic", "muted", "pan", "engine", "bank"}
        if set(kv) - known:
            raise ScoreError(f"voice takes {sorted(known)} -- not "
                             f"{sorted(set(kv) - known)}", node.no, node.text)
        role = str(kv.get("role", "melody"))
        if role not in ROLES:
            raise ScoreError(f"role is one of {list(ROLES)}", node.no, node.text)
        self.piece.voices.append(Voice(
            name, instrument, role, kv.get("octave"), kv.get("dynamic"),
            bool(kv.get("muted", False)),
            pan=None if kv.get("pan") is None else float(kv["pan"]),
            engine=kv.get("engine"), bank=kv.get("bank")))
        self.pending_ops += [(name, line) for line in node.body]

    def _do_on(self, node: _Line) -> None:
        voices = node.text.split()[1:]
        voices = [v.rstrip(":").rstrip(",") for v in voices if v.rstrip(":").rstrip(",")]
        if not voices or not node.body:
            raise ScoreError("on VOICE [VOICE …], then indented op lines", node.no,
                             node.text)
        for line in node.body:
            for voice in voices:
                filled = _Line(line.no, line.indent, _fill(line.text, {"v": voice}, line),
                               line.body)
                self.pending_ops.append((voice, filled))

    def _do_for(self, node: _Line) -> None:          # pragma: no cover - expanded earlier
        raise ScoreError("a `for` needs `for NAME in a b c` or `for NAME in 0..3`",
                         node.no, node.text)

    # -- ops ---------------------------------------------------------------

    def _op(self, voice: str, line: _Line) -> None:
        if line.body:
            child = line.body[0]
            raise ScoreError("this line is indented under an op, and an op has nothing "
                             "under it: bring it back to the op's own indent", child.no,
                             child.text)
        text, note = _split_note(line.text)
        op_id = None
        m = re.match(r"([\w.\-]+):\s+(.*)", text)
        if m:
            op_id, text = m.group(1), m.group(2)
        words, kv = _pairs(text, line)
        if not words or words[0] not in OP_SPECS:
            raise ScoreError(f"an op line is `[id:] KIND key=value …`; kinds are "
                             f"{sorted(OP_SPECS)}", line.no, line.text)
        kind = words[0]
        enabled = True
        for flag in words[1:]:
            if flag == "off":
                enabled = False
            else:
                raise ScoreError(f"stray word {flag!r}: every parameter is key=value "
                                 f"(quote values with spaces)", line.no, line.text)
        spec = OP_SPECS[kind]
        allowed = set(spec.required) | set(spec.optional)
        if "in" in kv and "in" not in allowed:
            kv["from"], kv["until"] = self.span(kv.pop("in"), line)
        params = {k: self.resolve(v, line) for k, v in kv.items()}
        if "lanes" in allowed:                       # drum=pattern folds into lanes
            extra = {k: params.pop(k) for k in list(params) if k in KIT_DRUMS}
            if extra or "lanes" in params:
                lanes = dict(params.get("lanes") or {})
                lanes.update({k: str(v) for k, v in extra.items()})
                params["lanes"] = lanes
        unknown = set(params) - allowed
        if unknown:
            raise ScoreError(f"{kind} does not take {sorted(unknown)}; it takes "
                             f"{sorted(allowed)}", line.no, line.text)
        if op_id is None:
            where = str(params.get("at") or params.get("from") or "")
            base = f"{voice}_{kind}" + (f"_{where.replace(':', '.')}" if where else "")
            n = self.auto.get(base, 0)
            self.auto[base] = n + 1
            op_id = base if n == 0 else f"{base}_{n + 1}"
        try:
            op = self.piece.add_op(voice, kind, id=op_id, note=note, **params)
        except (ValueError, KeyError, TypeError) as exc:
            raise ScoreError(str(exc).strip('"'), line.no, line.text) from None
        op.enabled = enabled

    def _finish(self) -> None:
        if not self.piece.sections:
            raise ScoreError("a piece needs at least one `section`")
        self._harmony()
        for voice, line in self.pending_ops:
            if voice not in {v.name for v in self.piece.voices}:
                raise ScoreError(f"no voice {voice!r}", line.no, line.text)
            self._op(voice, line)
        if self.master:
            for stop in self.master.get("stops", []):
                for name in stop["keep"]:
                    self.piece.get_voice(name)
            self.piece.meta["master"] = self.master


def compile_score(text: str) -> Piece:
    """A score file's text -> a piece, in memory. Raises ``ScoreError`` with a
    line number for anything it cannot read; validates every op as it goes."""
    return _Compiler().run(_expand(_tree(text), {}))


# --------------------------------------------------------------------------
# writing a piece out
# --------------------------------------------------------------------------

def _value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        plain = re.fullmatch(r"[^\s\"\[\]{}=$@#]+", v) and _scalar(v) == v
        return v if plain else '"' + v.replace('"', '\\"') + '"'
    return json.dumps(v, ensure_ascii=False, separators=(", ", ": "))


def _kv(pairs: dict) -> str:
    return " ".join(f"{k}={_value(v)}" for k, v in pairs.items() if v is not None)


def decompile(piece: Piece) -> str:
    """A piece as score text. ``compile_score(decompile(p))`` is ``p``."""
    out: list[str] = []
    head = {"key": piece.key.name, "tempo": piece.tempo, "style": piece.style}
    if piece.meter != "4/4":
        head["meter"] = piece.meter
    if piece.loop:
        head["loop"] = True
    out.append(f"piece {piece.name} {_kv(head)}")
    master = dict(piece.meta.get("master") or {})
    flat = {k: master[k] for k in ("push", "clip", "level") if k in master}
    flat.update({f"room.{k}": v for k, v in (master.get("room") or {}).items()})
    if flat:
        out.append(f"master {_kv(flat)}")
    for stop in master.get("stops", []):
        out.append(f"stop {_kv({'from': str(stop['from']), 'until': str(stop['until']), 'keep': stop.get('keep') or None})}")
    for key, value in piece.meta.items():
        if key != "master":
            out.append(f"meta {key} = {json.dumps(value, ensure_ascii=False)}")
    out.append("")
    for sec in piece.sections:
        fields = {"bars": sec.bars, "dynamic": sec.dynamic,
                  "meter": sec.meter if sec.meter != piece.meter else None,
                  "tempo": sec.tempo, "key": sec.key, "tempo_end": sec.tempo_end}
        out.append(f"section {sec.name} {_kv(fields)}"
                   + (f"   -- {sec.note}" if sec.note else ""))
    if piece.harmony:
        out += ["", "harmony"]
        run: list[str] = []
        start = None
        expect = None

        def flush() -> None:
            nonlocal run, start
            if run:
                out.append(f"  {start}: {' '.join(run)}")
            run, start = [], None

        for e in piece.harmony:
            chord = e.chord + (f"~{e.dur}" if e.dur else "")
            whole = ":" not in str(e.at)
            if whole and not e.note and expect == int(e.at) and run:
                run.append(chord)
                expect += 1
                continue
            flush()
            if whole and not e.note:
                start, run, expect = str(e.at), [chord], int(e.at) + 1
            else:
                out.append(f"  {e.at}: {chord}" + (f"   -- {e.note}" if e.note else ""))
                expect = None
        flush()
    if piece.motifs:
        out.append("")
    for m in piece.motifs.values():
        tail = "".join(f" {k}={_value(v)}" for k, v in
                       (("anchor", m.anchor if m.anchor != "scale" else None),
                        ("unit", m.unit if m.unit != "1/8" else None),
                        ("scale", m.scale)) if v)
        note = f"   -- {m.note}" if m.note else ""
        if not m.derived_from:
            out.append(f"motif {m.name} = {m.source()}{tail}{note}")
            continue
        line = None
        try:                                         # re-derive it, if that is possible
            made = piece.get_motif(m.derived_from)
            for t in m.lineage:
                made = apply_transform(made, t, resolve=piece.get_motif)
            if made.steps == m.steps and made.lineage == tuple(m.lineage):
                line = f"motif {m.name} < {m.derived_from} : {' > '.join(m.lineage)}"
        except Exception:
            line = None
        if line is None:
            line = (f'motif {m.name} < {m.derived_from} recorded '
                    f'"{" + ".join(m.lineage)}" = {m.source()}{tail}')
        out.append(line + note)
    for v in piece.voices:
        fields = {"role": v.role, "octave": v.octave, "dynamic": v.dynamic,
                  "muted": True if v.muted else None, "pan": v.pan, "engine": v.engine,
                  "bank": v.bank}
        out += ["", f"voice {v.name} {v.instrument} {_kv(fields)}"]
        for op in v.ops:
            params = {k: val for k, val in op.params.items() if val is not None}
            line = f"  {op.id}: {op.kind} {_kv(params)}".rstrip()
            if not op.enabled:
                line += " off"
            out.append(line + (f"   -- {op.note}" if op.note else ""))
    return "\n".join(out) + "\n"
