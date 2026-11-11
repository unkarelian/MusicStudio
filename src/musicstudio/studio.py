"""The studio session: a project on disk plus the verbs agents call.

Two decisions here matter more than the rest of the file, and they are the same
two that make the sprite studio work. Every mutation autosaves, so work survives
across tool calls without anyone remembering to save it. And every mutation
hands back a fresh view plus a critique -- cropped to the bars that changed --
so the feedback loop closes by default rather than by discipline. An agent that
never thinks to look at what it just wrote still sees it.

Because every mutation autosaves, every mutation is also a checkpoint: the file
on disk before the save is pushed onto a per-piece undo stack under
``<project>/.history/``. Trying an idea is free when taking it back is one call,
and a studio for learning is a studio for trying ideas.
"""

from __future__ import annotations

import functools
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .doc import HarmonyEntry, OP_SPECS, Piece, Section, Voice
from .ensemble import ROLES, describe_instruments, families, get_instrument
from .lint import Finding, lint, report, summary
from .midi import save_midi
from .motif import TRANSFORMS, Motif, apply_transform
from .readback import chart, diff, motif_map, score, squint, stats, voice_view
from .render import Render, render
from .style import STYLES, get_style


@dataclass
class OpResult:
    """What comes back from a mutation: what changed, and how it now sounds."""

    ok: bool
    op_id: str | None
    view: str
    findings: list[Finding]
    message: str = ""
    #: What the render had to guess or drop (a guessed pronunciation, a
    #: syllable with no note). Not lint: nothing here is a judgement of the
    #: writing, only a statement that the piece is not sung as it is written.
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {"ok": self.ok, "op_id": self.op_id, "message": self.message,
                "view": self.view, "warnings": list(self.warnings),
                "lint": {"summary": summary(self.findings),
                         "findings": [f.to_json() for f in self.findings]}}

    def __str__(self) -> str:
        head = self.message or (f"op {self.op_id}" if self.op_id else "")
        parts = [head]
        if self.view:
            parts.append(self.view)
        if self.warnings:
            parts.append("\n".join(f"render warning: {w}" for w in self.warnings))
        parts.append(report(self.findings))
        return "\n\n".join(p for p in parts if p)


#: Undo depth per piece. Snapshots are whole documents, so this bounds disk use.
HISTORY_DEPTH = 100

#: A redo/undo entry meaning "the piece did not exist here" -- what lets a
#: delete be undone, and the undo of a delete be redone.
_TOMBSTONE = ""


def _mutation(fn):
    """Mark a verb that changes a piece.

    Several verbs change the cached piece in place before they validate (a
    section field is set, *then* checked). If that check fails, the cache holds
    a half-applied edit that was never saved, and the next successful call
    would save it. Evicting on failure makes the file on disk -- which is always
    the last good state, since every success autosaves -- the truth again.
    """
    @functools.wraps(fn)
    def wrapper(self, name, *args, **kwargs):
        try:
            return fn(self, name, *args, **kwargs)
        except Exception:
            self._cache.pop(name, None)
            raise
    return wrapper


class Studio:
    """A project directory of pieces."""

    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self.pieces_dir = self.root / "pieces"
        self.renders_dir = self.root / "renders"
        self.history_dir = self.root / ".history"
        #: name -> ((mtime, size) of the file when loaded or saved, piece)
        self._cache: dict[str, tuple[tuple[int, int], Piece]] = {}

    # -- project -----------------------------------------------------------

    def path_for(self, name: str) -> Path:
        # A piece name becomes a file name here and a directory name under
        # .history; one with a separator in it would write outside the project.
        if (not isinstance(name, str) or not name or name in (".", "..")
                or any(c in name for c in '/\\\0') or name != name.strip()):
            raise ValueError(f"{name!r} is not a piece name: a name is a file name, "
                             f"so it cannot be empty or contain a path separator")
        return self.pieces_dir / f"{name}.ms.json"

    def list_pieces(self) -> list[dict]:
        out = []
        for p in sorted(self.pieces_dir.glob("*.ms.json")):
            try:
                d = json.loads(p.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                out.append({"name": p.stem.removesuffix(".ms"), "error": str(exc)})
                continue
            out.append({"name": d["name"], "key": d.get("key"), "tempo": d.get("tempo"),
                        "style": d.get("style"),
                        "bars": sum(s.get("bars", 0) for s in d.get("sections", [])),
                        "sections": len(d.get("sections", [])),
                        "voices": len(d.get("voices", [])),
                        "motifs": len(d.get("motifs", []))})
        return out

    def get(self, name: str) -> Piece:
        p = self.path_for(name)
        if not p.exists():
            self._cache.pop(name, None)
            known = [x.get("name") for x in self.list_pieces()]
            raise KeyError(f"no piece {name!r} in {self.pieces_dir}; have {known}")
        st = p.stat()
        mtime = (st.st_mtime_ns, st.st_size)
        hit = self._cache.get(name)
        # A file changed underneath us (a build script, a hand edit, a second
        # session) wins over the cache; otherwise the next autosave would
        # silently overwrite it with stale state.
        if hit is not None and hit[0] == mtime:
            return hit[1]
        piece = Piece.load(p)
        self._cache[name] = (mtime, piece)
        return piece

    def save(self, piece: Piece, *, record: bool = True) -> Path:
        """Write the piece, checkpointing what was on disk before it."""
        path = self.path_for(piece.name)
        text = piece.dumps()
        if record and path.exists():
            old = path.read_text()
            if old != text:
                self._push(piece.name, "undo", old)
                self._clear(piece.name, "redo")
        path.parent.mkdir(parents=True, exist_ok=True)
        # Written beside the piece and renamed over it: a crash mid-write
        # leaves the old file whole instead of a truncated one.
        part = path.with_name(f".{path.name}.{os.getpid()}.part")
        try:
            part.write_text(text)
            os.replace(part, path)
        finally:
            part.unlink(missing_ok=True)
        st = path.stat()
        self._cache[piece.name] = ((st.st_mtime_ns, st.st_size), piece)
        return path

    # -- history -----------------------------------------------------------

    def _stack(self, name: str, which: str) -> Path:
        return self.history_dir / name / which

    def _entries(self, name: str, which: str) -> list[Path]:
        d = self._stack(name, which)
        return sorted(d.glob("*.json")) if d.exists() else []

    def _push(self, name: str, which: str, text: str) -> None:
        d = self._stack(name, which)
        d.mkdir(parents=True, exist_ok=True)
        have = self._entries(name, which)
        nxt = int(have[-1].stem) + 1 if have else 1
        (d / f"{nxt:06d}.json").write_text(text)
        for old in have[: max(0, len(have) + 1 - HISTORY_DEPTH)]:
            old.unlink(missing_ok=True)

    def _pop(self, name: str, which: str) -> str | None:
        have = self._entries(name, which)
        if not have:
            return None
        text = have[-1].read_text()
        have[-1].unlink()
        return text

    def _clear(self, name: str, which: str) -> None:
        for f in self._entries(name, which):
            f.unlink(missing_ok=True)

    def history(self, name: str) -> dict:
        """How many steps can be undone and redone."""
        return {"undo": len(self._entries(name, "undo")),
                "redo": len(self._entries(name, "redo"))}

    def undo(self, name: str) -> OpResult:
        """Put the piece back the way it was before the last change."""
        return self._travel(name, "undo", "redo")

    def redo(self, name: str) -> OpResult:
        """Re-apply a change that was undone."""
        return self._travel(name, "redo", "undo")

    def _travel(self, name: str, src: str, dst: str) -> OpResult:
        snap = self._pop(name, src)
        if snap is None:
            raise ValueError(f"nothing to {src} for {name!r}")
        path = self.path_for(name)
        before = Piece.load(path) if path.exists() else None
        self._push(name, dst, path.read_text() if path.exists() else _TOMBSTONE)
        if snap == _TOMBSTONE:
            path.unlink(missing_ok=True)
            self._cache.pop(name, None)
            return OpResult(True, None, "", [], f"{src}: {name!r} no longer exists "
                                                f"({self._left(name)})")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(snap)
        self._cache.pop(name, None)
        piece = self.get(name)
        after = render(piece)
        view = diff(render(before), after, piece) if before is not None else chart(piece, after)
        return OpResult(True, None, view, lint(piece, after),
                        f"{src}: {name!r} restored ({self._left(name)})")

    def _left(self, name: str) -> str:
        h = self.history(name)
        return f"{h['undo']} undo, {h['redo']} redo left"

    def create(self, name: str, *, key: str = "C major", tempo: int = 90,
               meter: str = "4/4", style: str = "orchestral", form: str | None = None,
               sections: list | None = None, overwrite: bool = False,
               loop: bool = False) -> Piece:
        """Start a piece. Give a form preset so it has a shape before it has notes."""
        if self.path_for(name).exists() and not overwrite:
            raise FileExistsError(f"piece {name!r} already exists; pass overwrite=True")
        st = get_style(style)
        if not (st.tempo_range[0] <= tempo <= st.tempo_range[1]):
            raise ValueError(f"tempo {tempo} is outside style {style!r}'s range "
                             f"{st.tempo_range}")
        piece = Piece(name, key, tempo=tempo, meter=meter, style=style, loop=loop)
        spec = st.form(form) if form else (sections or [])
        for entry in spec:
            sec_name, bars = (entry if isinstance(entry, (list, tuple))
                              else (entry, 8))
            # No per-section tempo: they inherit the piece, so retiming works.
            piece.sections.append(Section(str(sec_name), int(bars), meter))
        self.save(piece)
        return piece

    def delete(self, name: str) -> None:
        """Remove a piece. Undoable: the last state goes onto its undo stack."""
        path = self.path_for(name)
        if not path.exists():
            raise KeyError(f"no piece {name!r} to delete")
        self._push(name, "undo", path.read_text())
        self._clear(name, "redo")
        path.unlink()
        self._cache.pop(name, None)

    @_mutation
    def update_piece(self, name: str, *, key: str | None = None, tempo: int | None = None,
                     style: str | None = None, loop: bool | None = None) -> OpResult:
        """Change the piece-level key, tempo, style or loop flag.

        Changing the key re-renders everything in the new key -- degrees make a
        transposition a one-field edit -- but every chord is re-checked first,
        because a numeral that parsed in a major key may not mean the same thing
        (or anything) in another scale.
        """
        p = self.get(name)
        changed = []
        if style is not None:
            st = get_style(style)
            p.style = st.name
            changed.append("style")
        if tempo is not None:
            lo, hi = get_style(p.style).tempo_range
            if not lo <= int(tempo) <= hi:
                raise ValueError(f"tempo {tempo} is outside style {p.style!r}'s range "
                                 f"({lo}, {hi})")
            p.tempo = int(tempo)
            changed.append("tempo")
        if key is not None:
            from .theory import Key, parse_chord
            p.key = Key.parse(key)
            for h in p.harmony:
                parse_chord(h.chord, p.key_at(p.tick_of(h.at)))
            changed.append("key")
        if loop is not None:
            p.loop = bool(loop)
            changed.append("loop")
        if not changed:
            raise ValueError("nothing to change; give key=, tempo=, style= or loop=")
        res = self._result(p, None, f"updated {name!r}: {', '.join(changed)} -> "
                                    f"{p.key.name}, q={p.tempo}, style={p.style}"
                                    + (", loop" if p.loop else ""), quiet=True)
        res.view = chart(p)
        return res

    @staticmethod
    def singers() -> dict:
        """The neural singers: which are installed, which are listed and what
        each one's terms ask. None ships with the studio."""
        from . import neural
        names = sorted(set(neural.CATALOGUE) | set(neural.installed()))
        return {"runtime": neural.available(), "where": str(neural.SINGER_DIR.expanduser()),
                "singers": [neural.describe(n) for n in names]}

    @staticmethod
    def singer(name: str, *, install: bool = False, accept_terms: bool = False,
               source: str | None = None, force: bool = False, progress=None) -> dict:
        """One neural singer. ``install`` downloads a listed one, and only with
        ``accept_terms``: a voicebank is someone's voice under their terms.
        ``source`` registers a voicebank you downloaded yourself instead."""
        from . import neural
        if source:
            neural.add(name, source, force=force)
        elif install:
            neural.install(name, accept=accept_terms, progress=progress, force=force)
        return neural.describe(name)

    @staticmethod
    def voicebank(voice: str, *, build: bool = False, model: str | None = None,
                  words: int = 0, progress=None) -> dict:
        """The state of a voice bank, and optionally record what is missing.

        A bank is 271 short recordings made once; after that any lyric can be
        sung from it. Recording costs money (a few cents in all) and needs
        ``$OPENROUTER_API_KEY``; it is never done implicitly by a render.
        """
        from . import voicebank as vb
        model = model or vb.DEFAULT_MODEL
        if build:
            return vb.build(voice, model=model, words=words, progress=progress)
        return vb.status(voice, model)

    def check_words(self, name: str, voice: str | None = None) -> dict:
        """Render a singer alone and ask a speech recogniser what it said.

        Returns the transcript, the share of the sung words it got, the words
        it missed, and the words it heard that the lyric does not say. Costs a little per call and needs
        ``$OPENROUTER_API_KEY``; never run implicitly.
        """
        import copy
        import tempfile
        from . import voicebank as vb
        from .audio import save_wav
        p = self.get(name)
        singers = [v for v in p.voices
                   if any(op.kind == "lyrics" for op in v.ops) and (voice in (None, v.name))]
        if not singers:
            raise ValueError(f"{name!r} has no voice with lyrics"
                             + (f" called {voice!r}" if voice else ""))
        target = singers[0]
        # The reference is what the render actually sings, read off the notes:
        # a syllable with no note, a chopped line or a replaced lyric must not
        # be counted as "written" when nobody could have heard it.
        r = render(p)
        first = {n.start: n.word.split("#")[0] for n in r.by_voice(target.name)
                 if n.word and n.word.split("#")[1].startswith("0/")}
        written = [first[t] for t in sorted(first)]
        if not written:
            raise ValueError(f"voice {target.name!r} sings no words (only held "
                             f"vowels or bracketed sounds), so there is nothing "
                             f"to check")
        solo = copy.deepcopy(p)
        for v in solo.voices:
            v.muted = v.name != target.name
        with tempfile.TemporaryDirectory() as tmp:
            heard = vb.transcribe_long(save_wav(solo, Path(tmp) / "solo.wav"))
        share, missed = vb.words_heard(written, heard)
        extra = vb.words_added(written, heard)
        return {"voice": target.name, "heard": heard, "understood": round(share, 2),
                "words": len(written), "missed": missed,
                # Words it heard that were never written: a high share with a
                # long list here is a garbled voice, not a clear one.
                "extra": extra}

    @_mutation
    def set_master(self, name: str, *, push: float | None = None,
                   clip: float | None = None, level: float | None = None,
                   stops: list | None = None, room: dict | None = None) -> dict:
        """How hard the finished mix is hit. ``push`` is dB into the limiter
        (3.5 by default, 9 for electronic); ``clip`` instead drives it that many
        dB past full scale and cuts the tops off, which is a sound, not a fault,
        in the styles that want it. ``level`` (dB, negative) turns the finished
        file down without changing its sound. Pass 0 to clear any of them.

        ``stops`` are the piece's hard stops: a list of ``{"from": "12:3",
        "until": "13", "keep": ["vox"]}``. Across each the whole band is cut
        to silence -- ringing notes and the room's tail too -- and the voices
        in ``keep`` carry on, dry. Pass ``[]`` to clear them.

        ``room`` replaces the style's reverb for this piece: ``{"decay":
        seconds, "wet": 0..1}``, either or both. ``{}`` goes back to the
        style's."""
        p = self.get(name)
        master = dict(p.meta.get("master") or {})
        if room is not None:
            mine = {}
            if room.get("decay") is not None:
                mine["decay"] = max(0.05, min(8.0, float(room["decay"])))
            if room.get("wet") is not None:
                mine["wet"] = max(0.0, min(1.0, float(room["wet"])))
            if mine:
                master["room"] = mine
            else:
                master.pop("room", None)
        if stops is not None:
            clean = []
            for st in stops:
                lo, hi = p.tick_of(st["from"]), p.tick_of(st["until"])
                if hi <= lo:
                    raise ValueError(f"a stop must end after it starts: {st}")
                keep = list(st.get("keep") or [])
                for voice in keep:
                    p.get_voice(voice)
                clean.append({"from": str(st["from"]), "until": str(st["until"]),
                              "keep": keep})
            if clean:
                master["stops"] = clean
            else:
                master.pop("stops", None)
        for key, val in (("push", push), ("clip", clip), ("level", level)):
            if val is None:
                continue
            if val:
                master[key] = float(val)
            else:
                master.pop(key, None)
        if master:
            p.meta["master"] = master
        else:
            p.meta.pop("master", None)
        self.save(p)
        return {"master": master}

    # -- views -------------------------------------------------------------

    def render(self, name: str, *, upto: str | None = None) -> Render:
        return render(self.get(name), upto=upto)

    def score(self, name: str, *, bars=None, res: str = "1/8", glyphs: str = "voice",
              legend: bool = True, voices=None, upto: str | None = None) -> str:
        p = self.get(name)
        return score(p, render(p, upto=upto), bars=bars, res=res, glyphs=glyphs,
                     legend=legend, voices=voices)

    def chart(self, name: str) -> str:
        p = self.get(name)
        return chart(p)

    def motifs(self, name: str) -> str:
        p = self.get(name)
        return motif_map(p)

    def squint(self, name: str) -> str:
        p = self.get(name)
        return squint(p)

    def voice(self, name: str, voice: str, *, bars=None) -> str:
        p = self.get(name)
        return voice_view(p, voice, bars=bars)

    def tension(self, name: str) -> str:
        """Per bar: distance from home, dissonance, surprise, and a reading."""
        from .tension import view
        return view(self.get(name))

    def hear(self, name: str, *, source: str = "models",
             soundfont: str | None = None) -> str:
        """Measurements of the rendered audio, voice by voice and bar by bar.

        ``source='soundfont'`` measures the sampled render instead of the
        built-in models -- the two can disagree, and it is the one the listener
        will hear that matters.
        """
        from .listen import view
        return view(self.get(name), source=source, soundfont=soundfont)

    def stats(self, name: str) -> dict:
        p = self.get(name)
        return stats(p)

    def lint(self, name: str) -> list[Finding]:
        return lint(self.get(name))

    # -- export ------------------------------------------------------------

    def export_midi(self, name: str, path: str | None = None) -> Path:
        p = self.get(name)
        return save_midi(p, Path(path) if path else self.renders_dir / f"{name}.mid")

    def export_wav(self, name: str, path: str | None = None, *, stereo: bool = True,
                   reverb: bool | None = None, models: bool | None = None,
                   soundfont: str | None = None) -> Path:
        """Render to WAV.

        ``reverb=None`` and ``models=None`` add the style's room and the
        instrument models if numpy is there. ``soundfont`` renders through
        FluidSynth with sampled instruments instead: a path to an .sf2/.sf3, or
        ``'auto'`` to use ``$MUSICSTUDIO_SOUNDFONT`` or one found on the system.
        """
        from .audio import save_wav, save_wav_soundfont
        p = self.get(name)
        out = Path(path) if path else self.renders_dir / f"{name}.wav"
        if soundfont:
            return save_wav_soundfont(p, out, soundfont)
        return save_wav(p, out, stereo=stereo, reverb=reverb, models=models)

    # -- result plumbing ---------------------------------------------------

    def _focus(self, piece: Piece, op_id: str | None) -> tuple[int, int] | None:
        """The bars a change touched, so the returned view is about that change."""
        if op_id is None:
            return None
        try:
            _, op = piece.find_op(op_id)
        except KeyError:
            return None
        pos = op.params.get("at") or op.params.get("from")
        if pos is None:
            return None
        from .theory import parse_position
        bar = parse_position(pos)[0]
        end = op.params.get("until")
        last = parse_position(end)[0] if end else bar + 3
        return max(1, bar), min(piece.total_bars, max(bar, last))

    def _result(self, piece: Piece, op_id, message, *, bars=None, quiet=False) -> OpResult:
        # Render and lint *before* saving: an edit that cannot be rendered must
        # not reach the file, or the file stops being the last good state and
        # `_mutation` evicting the cache would reload the broken piece.
        r = render(piece)
        view = ""
        if not quiet:
            focus = bars if bars is not None else self._focus(piece, op_id)
            view = score(piece, r, bars=focus, legend=False)
        findings = lint(piece, r)
        self.save(piece)
        return OpResult(True, op_id, view, findings, message, list(r.warnings))

    # -- form --------------------------------------------------------------

    @_mutation
    def add_section(self, name: str, section: str, *, bars: int = 8,
                    meter: str | None = None, tempo: int | None = None,
                    key: str | None = None, dynamic: str = "mf", note: str = "",
                    index: int | None = None,
                    tempo_end: int | None = None) -> OpResult:
        p = self.get(name)
        if any(s.name == section for s in p.sections):
            raise ValueError(f"section {section!r} already exists")
        # tempo stays None unless given: a section that states the piece's tempo
        # would be left behind at the old marking when the piece is retimed.
        sec = Section(section, bars, meter or p.meter, tempo, key, dynamic, note,
                      tempo_end)
        p.sections.insert(len(p.sections) if index is None else index, sec)
        return self._result(p, None, f"added section {section!r}: {bars} bars of "
                                     f"{sec.meter} at q={p.tempo_of(sec)}",
                            bars=p.section_bars(section))

    @_mutation
    def update_section(self, name: str, section: str, **fields) -> OpResult:
        p = self.get(name)
        sec = p.get_section(section)
        for k, v in fields.items():
            if v is None:
                continue
            if not hasattr(sec, k):
                raise ValueError(f"section has no field {k!r}; have bars, meter, "
                                 f"tempo, tempo_end, key, dynamic, note")
            setattr(sec, k, v)
        sec.__post_init__()
        return self._result(p, None, f"updated section {section!r}: {sorted(fields)}",
                            bars=p.section_bars(section))

    @_mutation
    def remove_section(self, name: str, section: str) -> OpResult:
        p = self.get(name)
        p.sections.remove(p.get_section(section))
        return self._result(p, None, f"removed section {section!r}", quiet=True)

    @_mutation
    def set_harmony(self, name: str, entries: list, *, replace: bool = True) -> OpResult:
        """Lay down the chord scaffold: ``[['1','i'], ['3','iv'], ['5','V7']]``."""
        p = self.get(name)
        made = []
        for e in entries:
            if isinstance(e, dict):
                made.append(HarmonyEntry(str(e["at"]), e["chord"], e.get("dur"),
                                         e.get("note", "")))
            else:
                at, chord, *rest = e
                made.append(HarmonyEntry(str(at), chord, rest[0] if rest else None))
        for h in made:                       # fail before mutating anything
            from .theory import parse_chord
            parse_chord(h.chord, p.key_at(p.tick_of(h.at)))
        p.harmony = made if replace else p.harmony + made
        return self._result(p, None, f"{'set' if replace else 'added'} {len(made)} "
                                     f"chord(s)", bars=(1, min(8, p.total_bars)))

    @_mutation
    def add_voice(self, name: str, voice: str, instrument: str, *, role: str = "melody",
                  octave: int | None = None, dynamic: str | None = None,
                  pan: float | None = None, engine: str | None = None,
                  bank: str | None = None) -> OpResult:
        p = self.get(name)
        if any(v.name == voice for v in p.voices):
            raise ValueError(f"voice {voice!r} already exists")
        inst = get_instrument(instrument)
        p.voices.append(Voice(voice, instrument, role, octave, dynamic, pan=pan,
                              engine=engine, bank=bank))
        msg = (f"added voice {voice!r}: {instrument} ({inst.family}), role={role}, "
               f"range {inst.low}-{inst.high}")
        if inst.notes:
            msg += "\n  " + "\n  ".join(inst.notes)
        return self._result(p, None, msg, quiet=True)

    @_mutation
    def remove_voice(self, name: str, voice: str) -> OpResult:
        p = self.get(name)
        v = p.get_voice(voice)
        followers = [f"{o.name}:{op.id}" for o in p.voices for op in o.ops
                     if op.kind == "double" and op.params.get("source") == voice]
        if followers:
            raise ValueError(f"voice {voice!r} is doubled by {followers}; remove those "
                             f"ops first")
        p.voices.remove(v)
        return self._result(p, None, f"removed voice {voice!r}", quiet=True)

    @_mutation
    def set_voice(self, name: str, voice: str, **fields) -> OpResult:
        p = self.get(name)
        v = p.get_voice(voice)
        for k, val in fields.items():
            if val is None:
                continue
            if k not in ("instrument", "role", "octave", "dynamic", "muted", "pan",
                         "engine", "bank"):
                raise ValueError(f"cannot set {k!r} on a voice; can set instrument, "
                                 f"role, octave, dynamic, muted, pan, engine, bank")
            setattr(v, k, val)
        v.__post_init__()
        return self._result(p, None, f"updated voice {voice!r}: {sorted(fields)}",
                            quiet=True)

    # -- motifs ------------------------------------------------------------

    @_mutation
    def add_motif(self, name: str, motif: str, source: str, *, anchor: str = "scale",
                  scale: str | None = None, unit: str = "1/8",
                  note: str = "") -> dict:
        p = self.get(name)
        m = p.add_motif(motif, source, anchor=anchor, scale=scale, unit=unit, note=note)
        self.save(p)
        return {"motif": m.to_json(),
                "reads_as": f"{m.source()}  ({len(m.steps)} steps, "
                            f"{m.duration / 480:g} beats, contour {m.contour() or '-'})"}

    @_mutation
    def derive_motif(self, name: str, motif: str, source_motif: str,
                     transforms: list, *, note: str = "") -> dict:
        """Make a named variation. The lineage is kept, so the map still knows it."""
        p = self.get(name)
        if motif in p.motifs:
            raise ValueError(f"motif {motif!r} already exists")
        m = p.get_motif(source_motif)
        for t in transforms:
            m = (apply_transform(m, t, resolve=p.get_motif) if isinstance(t, str)
                 else apply_transform(m, resolve=p.get_motif, **t))
        m = Motif(motif, m.steps, m.anchor, m.scale, m.unit, note or m.note,
                  m.derived_from or source_motif, m.lineage)
        p.motifs[motif] = m
        self.save(p)
        return {"motif": m.to_json(),
                "reads_as": f"{m.source()}  (from {m.derived_from} via "
                            f"{' + '.join(m.lineage)})"}

    @_mutation
    def remove_motif(self, name: str, motif: str) -> dict:
        p = self.get(name)
        users = [op.id for _, op in p.all_ops()
                 if op.kind == "play" and op.params.get("motif") == motif]
        if users:
            raise ValueError(f"motif {motif!r} is played by ops {users}; remove those first")
        p.motifs.pop(motif, None)
        self.save(p)
        return {"removed": motif}

    def list_motifs(self, name: str) -> list[dict]:
        return [m.to_json() for m in self.get(name).motifs.values()]

    # -- ops ---------------------------------------------------------------

    @_mutation
    def add_op(self, name: str, voice: str, kind: str, *, id: str | None = None,
               index: int | None = None, note: str = "", view_bars=None,
               **params) -> OpResult:
        """Add an op. ``**params`` are the op's own arguments -- see describe_ops.

        The view crop is ``view_bars``, not ``bars``, deliberately: ``bars`` is
        itself a parameter of the chords, bass, drone and groove ops, and a plain
        ``bars`` here would silently swallow it -- the op would still run, just
        over the wrong length of music. For the same reason the ``double`` op
        names the part it follows ``source`` rather than ``voice``: ``voice``
        here is the voice being written to, and one name cannot mean both.
        """
        p = self.get(name)
        op = p.add_op(voice, kind, id=id, index=index, note=note, **params)
        return self._result(p, op.id, f"added {kind} op {op.id!r} to voice {voice!r}",
                            bars=view_bars)

    @_mutation
    def update_op(self, name: str, op_id: str, **params) -> OpResult:
        p = self.get(name)
        op = p.update_op(op_id, **params)
        return self._result(p, op.id, f"updated {op.id!r}: {sorted(params)}")

    @_mutation
    def move_op(self, name: str, op_id: str, bars: int = 0, beats: float = 0) -> OpResult:
        p = self.get(name)
        before = render(p)
        op = p.move_op(op_id, bars, beats)
        res = self._result(p, op.id, f"moved {op.id!r} by {bars:+d} bar(s) "
                                     f"{beats:+g} beat(s)", quiet=True)
        res.view = diff(before, render(p), p)
        return res

    @_mutation
    def remove_op(self, name: str, op_id: str) -> OpResult:
        p = self.get(name)
        op = p.remove_op(op_id)
        return self._result(p, None, f"removed {op.id!r} ({op.kind})", quiet=True)

    @_mutation
    def reorder_op(self, name: str, op_id: str, index: int,
                   voice: str | None = None) -> OpResult:
        p = self.get(name)
        op = p.reorder_op(op_id, index, voice)
        return self._result(p, op.id, f"moved {op.id!r} to index {index}"
                                      + (f" on voice {voice!r}" if voice else ""))

    @_mutation
    def set_op_enabled(self, name: str, op_id: str, enabled: bool) -> OpResult:
        p = self.get(name)
        _, op = p.find_op(op_id)
        op.enabled = enabled
        return self._result(p, op.id, f"{'enabled' if enabled else 'disabled'} {op.id!r}")

    def list_ops(self, name: str, voice: str | None = None) -> list[dict]:
        p = self.get(name)
        return [{"voice": v.name, "index": i, "id": op.id, "kind": op.kind,
                 "enabled": op.enabled, "note": op.note,
                 "params": {k: val for k, val in op.params.items() if val is not None}}
                for v in p.voices if voice is None or v.name == voice
                for i, op in enumerate(v.ops)]

    # -- import and analysis -----------------------------------------------

    def import_music(self, name: str, path: str, *, kind: str = "auto",
                     voice: str = "imported", instrument: str = "piano",
                     tempo: int | None = None, overwrite: bool = False) -> dict:
        """Bring an existing piece in, as MIDI (exact) or audio (an estimate).

        The result is an ordinary piece: every view, the critique pass and every
        export work on it unchanged. Audio imports carry a confidence figure and
        the warnings behind it, because a transcription that reads plausibly and
        means nothing is the failure mode that matters here.
        """
        from .ingest import read_midi, transcribe_audio
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"no such file: {path}")
        if kind == "auto":
            kind = "midi" if src.suffix.lower() in (".mid", ".midi") else "audio"
        ing = (read_midi(src, name=name) if kind == "midi"
               else transcribe_audio(src, name=name, tempo=tempo))

        bar = 4 * 480
        bars = max(1, -(-ing.duration // bar))
        piece = self.create(name, key=ing.key.name if ing.key else "C major",
                            tempo=ing.tempo, meter=ing.meter, style="freeform",
                            sections=[("imported", bars)], overwrite=overwrite)
        piece.meta["import"] = {"source": ing.source, "confidence": ing.confidence,
                                "warnings": ing.notes}
        piece.voices.append(Voice(voice, instrument, "melody"))
        piece.add_op(voice, "events", id="source", events=[e.to_json() for e in ing.events],
                     note=f"imported from {src.name}")
        self.save(piece)
        return {"summary": ing.summary(), "confidence": ing.confidence,
                "warnings": ing.notes, "events": len(ing.events),
                "key": ing.key.name if ing.key else None, "tempo": ing.tempo,
                "bars": bars,
                "trust": ("exact -- every pitch and onset is stated in the file"
                          if kind == "midi" else
                          "estimated -- treat as a lead, not as ground truth")}

    def _events_of(self, name: str) -> list:
        from .ingest import Event
        r = render(self.get(name))
        return [Event(n.pitch, n.start, n.dur, n.velocity, n.voice) for n in r.notes]

    def find_motifs(self, name: str, **kw) -> dict:
        """Discover repeated melodic shapes in a piece, significance-tested."""
        from .analyze import find_motifs, report_patterns
        pats = find_motifs(self._events_of(name), source=name, **kw)
        conf = self.get(name).meta.get("import", {}).get("confidence")
        # The caveat rides in the report itself: the MCP tool and the CLI print
        # only the report, and an estimate must say so wherever it surfaces.
        caveat = ("" if conf is None or conf >= 0.85 else
                  f"\n\nNOTE: {name!r} is an estimated transcription, only "
                  f"{conf:.2f} confident. Shapes found in it may be the tracker's, "
                  f"not the music's; confirm against MIDI before believing them.")
        return {"patterns": [p.to_json() for p in pats],
                "report": report_patterns(pats, header=f"repeated shapes in {name!r}")
                          + caveat,
                "source_confidence": conf}

    def compare(self, names: list[str], **kw) -> dict:
        """Melodic shapes shared across pieces -- the leitmotif question."""
        from .analyze import report_patterns, shared_motifs
        sources = {n: self._events_of(n) for n in names}
        pats = shared_motifs(sources, **kw)
        confs = {n: self.get(n).meta.get("import", {}).get("confidence", 1.0)
                 for n in names}
        weakest = min(confs.values(), default=1.0)
        caveat = ("" if weakest >= 0.85 else
                  f"\n\nNOTE: the weakest source is only {weakest:.2f} confident. "
                  f"Shared-theme claims from estimated transcriptions are not "
                  f"reliable; confirm against MIDI before believing them.")
        return {"patterns": [p.to_json() for p in pats],
                "confidences": confs,
                "report": report_patterns(
                    pats, header=f"shapes shared by {', '.join(names)}") + caveat}

    @_mutation
    def adopt_pattern(self, name: str, motif: str, index: int = 0,
                      unit: str = "1/8") -> dict:
        """Turn a discovered pattern into a real motif you can play and develop."""
        from .analyze import find_motifs
        pats = find_motifs(self._events_of(name), source=name)
        if not pats:
            raise ValueError(f"no significant patterns found in {name!r}")
        if not 0 <= index < len(pats):
            raise IndexError(f"pattern {index} out of range; {len(pats)} were found")
        piece = self.get(name)
        m = pats[index].as_motif(motif, unit)
        if motif in piece.motifs:
            raise ValueError(f"motif {motif!r} already exists")
        piece.motifs[motif] = m
        self.save(piece)
        return {"motif": m.to_json(), "from_pattern": pats[index].to_json()}

    # -- discovery ---------------------------------------------------------

    @staticmethod
    def describe_ops() -> list[dict]:
        return [{"kind": k, "doc": s.doc, "required": list(s.required),
                 "optional": s.optional,
                 "kind_of": "modifier" if s.modifier else "generator"}
                for k, s in OP_SPECS.items()]

    @staticmethod
    def describe_styles() -> list[dict]:
        return [s.to_json() for s in STYLES.values()]

    @staticmethod
    def describe_transforms() -> dict:
        return TRANSFORMS

    @staticmethod
    def describe_notation() -> dict:
        """The marks a note can carry: ``4:1/4@tr``, ``2@gr+1@st``."""
        from .motif import ARTICULATION_MARKS, ORNAMENTS
        return {"ornaments": dict(ORNAMENTS),
                "articulations": sorted(k for k in ARTICULATION_MARKS if len(k) <= 4)}

    @staticmethod
    def describe_instruments(family: str | None = None) -> dict:
        return {"families": families(), "instruments": describe_instruments(family),
                "roles": list(ROLES)}
