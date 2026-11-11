"""Command line interface. ``ms --help`` for the verb list."""

from __future__ import annotations

import argparse
import json
import shutil
import sys

from .lint import report
from .studio import Studio


def _val(raw: str):
    """Parse a ``key=value`` value as JSON, falling back to a bare string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _kwargs(pairs: list[str]) -> dict:
    out = {}
    for p in pairs:
        if "=" not in p:
            raise SystemExit(f"expected key=value, got {p!r}")
        k, v = p.split("=", 1)
        out[k] = _val(v)
    return out


def _bars(s: str | None):
    if not s:
        return None
    parts = s.replace(" ", "").split("-")
    return (int(parts[0]), int(parts[-1]))


def _singer(s, a) -> int:
    """`ms singer ...`: the neural singers and what their terms ask."""
    from . import soundfonts

    def show(i: dict) -> None:
        state = "installed" if i["installed"] else "not installed"
        print(f"{i['name']:<12} {i.get('title', '(added by you)')}  [{state}]")
        if i.get("voice"):
            print(f"  voice      {i['voice']}")
        if i.get("languages"):
            print(f"  languages  {' '.join(i['languages'])}")
        if i.get("speakers"):
            print(f"  colours    {' '.join(i['speakers'])}   (bank=\"{i['name']}:<colour>\")")
        if i.get("by"):
            print(f"  by         {i['by']}")
        if i.get("homepage"):
            print(f"  from       {i['homepage']}")
        if i.get("terms"):
            print(f"  terms      {i['terms']}")
        if i["installed"] and i.get("vocoder_installed") is False:
            print(f"  missing    the vocoder {i.get('vocoder')!r}")
        if i.get("problem"):
            print(f"  problem    {i['problem']}")

    if a.action == "list":
        info = s.singers()
        if not info["runtime"]:
            print("neural singers need: uv sync --extra neural   (numpy, onnxruntime, pyyaml)")
        for i in info["singers"]:
            show(i)
        print(f"kept in {info['where']}. None is part of MusicStudio: SINGERS.md says "
              f"what each one's terms ask.")
        return 0
    if not a.name:
        print("which singer? see: ms singer list", file=sys.stderr)
        return 2
    if a.action == "add" and not a.source:
        print("ms singer add <name> <zip or folder>", file=sys.stderr)
        return 2
    try:
        i = s.singer(a.name, install=a.action == "install", accept_terms=a.accept_terms,
                     source=a.source if a.action == "add" else None, force=a.force,
                     progress=soundfonts._progress if a.action == "install" else None)
    except PermissionError as exc:
        print(exc, file=sys.stderr)
        return 1
    show(i)
    for line in i.get("asks", []):
        print(f"  - {line}")
    if i["installed"]:
        print(f"  use it     add_voice(..., \"singer\", bank=\"{i['name']}\")")
    elif i.get("listed"):
        print(f"  get it     ms singer install {i['name']} --accept-terms"
              f"   ({i.get('megabytes', '?')} MB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ms", description="MusicStudio - a music studio for agents")
    ap.add_argument("--project", "-p", default=".", help="project directory (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("styles", help="list style profiles, their rules and form presets")
    sub.add_parser("ops", help="list the op vocabulary")
    sub.add_parser("transforms", help="list the motif development vocabulary")
    p = sub.add_parser("instruments", help="list instruments, ranges and roles")
    p.add_argument("--family")
    sub.add_parser("ls", help="list pieces in the project")

    p = sub.add_parser("new", help="create a piece")
    p.add_argument("name")
    p.add_argument("--key", default="C major")
    p.add_argument("--tempo", type=int, default=90)
    p.add_argument("--meter", default="4/4")
    p.add_argument("--style", default="orchestral")
    p.add_argument("--form", help="form preset from the style (e.g. cue, ternary, loop)")
    p.add_argument("--loop", action="store_true",
                   help="the piece repeats (game BGM), so it need not end on the tonic")
    p.add_argument("--overwrite", action="store_true")

    p = sub.add_parser("piece", help="change a piece's key, tempo, style or loop flag")
    p.add_argument("name")
    p.add_argument("--key"); p.add_argument("--tempo", type=int); p.add_argument("--style")
    p.add_argument("--loop", action=argparse.BooleanOptionalAction, default=None)

    p = sub.add_parser("delete", help="delete a piece (undoable)")
    p.add_argument("name")

    for verb, helptext in [("undo", "take back the last change to a piece"),
                           ("redo", "re-apply a change that was undone"),
                           ("history", "how many changes can be undone / redone")]:
        q = sub.add_parser(verb, help=helptext)
        q.add_argument("name")

    p = sub.add_parser("section", help="add a section")
    p.add_argument("name"); p.add_argument("section")
    p.add_argument("--bars", type=int, default=8)
    p.add_argument("--meter"); p.add_argument("--tempo", type=int)
    p.add_argument("--key"); p.add_argument("--dynamic", default="mf")
    p.add_argument("--note", default="")

    p = sub.add_parser("setsection", help="change a section's fields")
    p.add_argument("name"); p.add_argument("section")
    p.add_argument("fields", nargs="+", metavar="KEY=VALUE",
                   help="bars, meter, tempo, tempo_end, key, dynamic, note")

    p = sub.add_parser("rmsection", help="remove a section")
    p.add_argument("name"); p.add_argument("section")

    p = sub.add_parser("harmony", help="set the chord scaffold, as bar=numeral pairs")
    p.add_argument("name")
    p.add_argument("chords", nargs="+", metavar="BAR=NUMERAL")
    p.add_argument("--add", action="store_true", help="append instead of replacing")

    p = sub.add_parser("voice", help="add a voice")
    p.add_argument("name"); p.add_argument("voice"); p.add_argument("instrument")
    p.add_argument("--role", default="melody")
    p.add_argument("--octave", type=int); p.add_argument("--dynamic")
    p.add_argument("--pan", type=float, help="-1 (left) .. 1 (right); default seats by instrument")

    p = sub.add_parser("setvoice", help="change a voice's instrument, role, octave, "
                                        "dynamic, muted or pan")
    p.add_argument("name"); p.add_argument("voice")
    p.add_argument("fields", nargs="+", metavar="KEY=VALUE")

    p = sub.add_parser("rmvoice", help="remove a voice and its ops")
    p.add_argument("name"); p.add_argument("voice")

    p = sub.add_parser("motif", help="define a motif in degree notation")
    p.add_argument("name"); p.add_argument("motif"); p.add_argument("source")
    p.add_argument("--anchor", default="scale", choices=["scale", "chord"])
    p.add_argument("--unit", default="1/8"); p.add_argument("--scale")
    p.add_argument("--note", default="")

    p = sub.add_parser("derive", help="make a named variation of a motif")
    p.add_argument("name"); p.add_argument("motif"); p.add_argument("source_motif")
    p.add_argument("transforms", nargs="+", metavar="TRANSFORM",
                   help="e.g. invert retrograde augment:2 fragment:0,3")
    p.add_argument("--note", default="")

    p = sub.add_parser("rmmotif", help="remove a motif nothing plays")
    p.add_argument("name"); p.add_argument("motif")

    p = sub.add_parser("op", help="add an op to a voice")
    p.add_argument("name"); p.add_argument("voice"); p.add_argument("kind")
    p.add_argument("params", nargs="*", metavar="KEY=VALUE")
    p.add_argument("--id"); p.add_argument("--index", type=int)
    p.add_argument("--note", default="")

    p = sub.add_parser("update", help="change an op's params")
    p.add_argument("name"); p.add_argument("op_id")
    p.add_argument("params", nargs="+", metavar="KEY=VALUE")

    p = sub.add_parser("move", help="shift an op in time")
    p.add_argument("name"); p.add_argument("op_id")
    p.add_argument("--bars", type=int, default=0)
    p.add_argument("--beats", type=float, default=0)

    p = sub.add_parser("rm", help="remove an op")
    p.add_argument("name"); p.add_argument("op_id")

    p = sub.add_parser("toggle", help="enable or disable an op without deleting it")
    p.add_argument("name"); p.add_argument("op_id")
    p.add_argument("state", choices=["on", "off"])

    p = sub.add_parser("reorder", help="move an op to a new index in its voice's log")
    p.add_argument("name"); p.add_argument("op_id"); p.add_argument("index", type=int)
    p.add_argument("--voice", help="move it onto another voice")

    p = sub.add_parser("list", help="list a piece's ops")
    p.add_argument("name"); p.add_argument("--voice")

    p = sub.add_parser("show", help="the score: a pitch-by-time grid")
    p.add_argument("name")
    p.add_argument("--bars", "-b", help="e.g. 1-8")
    p.add_argument("--res", default="1/8")
    p.add_argument("--degrees", action="store_true", help="show scale degrees not voices")
    p.add_argument("--voices", nargs="*")
    p.add_argument("--upto", help="render only up to this op id")

    for verb, helptext in [("chart", "the form and harmony at a glance"),
                           ("motifs", "where every theme appears, and in what shape"),
                           ("squint", "the arc: density, register and dynamics per bar"),
                           ("stats", "counts, ranges and motif coverage"),
                           ("lint", "the critique pass")]:
        q = sub.add_parser(verb, help=helptext)
        q.add_argument("name")

    p = sub.add_parser("import", help="import a MIDI (exact) or audio (estimated) file")
    p.add_argument("name"); p.add_argument("path")
    p.add_argument("--kind", default="auto", choices=["auto", "midi", "audio"])
    p.add_argument("--instrument", default="piano")
    p.add_argument("--tempo", type=int)
    p.add_argument("--overwrite", action="store_true")

    p = sub.add_parser("findmotifs", help="discover repeated shapes, significance-tested")
    p.add_argument("name")
    p.add_argument("--min-notes", type=int, default=4)
    p.add_argument("--max-notes", type=int, default=10)
    p.add_argument("--p-max", type=float, default=0.05)

    p = sub.add_parser("compare", help="find melodic shapes shared across pieces")
    p.add_argument("names", nargs="+")
    p.add_argument("--require", type=int, help="how many pieces must share it")
    p.add_argument("--p-max", type=float, default=0.02)

    p = sub.add_parser("adopt", help="turn a discovered pattern into a named motif")
    p.add_argument("name"); p.add_argument("motif")
    p.add_argument("--index", type=int, default=0)

    p = sub.add_parser("part", help="one voice as an event list")
    p.add_argument("name"); p.add_argument("voice"); p.add_argument("--bars", "-b")

    p = sub.add_parser("lyrics", help="show how a line will be sung, or install "
                                      "the pronouncing dictionary")
    p.add_argument("text", nargs="*", help="a lyric line, or 'install'")
    p.add_argument("--lang", default="auto", choices=("auto", "ja", "en"))

    p = sub.add_parser("pattern", help="draw a rhythm pattern (the notation `beat` "
                                       "takes with cycle=1) on a grid")
    p.add_argument("text", nargs="+", help="e.g. 'x(3,8)' or '<x o> [x x]*2 . x?'")
    p.add_argument("--cycles", "-n", type=int, default=4)
    p.add_argument("--steps", type=int, default=16)

    p = sub.add_parser("singer", help="neural singers (DiffSinger voicebanks): list "
                                      "them, read one's terms, install or add one")
    p.add_argument("action", choices=("list", "show", "install", "add", "check"),
                   help="install: download a listed voicebank (needs --accept-terms). "
                        "add: register one you downloaded yourself. check: render a "
                        "piece's singer alone and have a speech recogniser write "
                        "down what it hears (paid, needs OPENROUTER_API_KEY)")
    p.add_argument("name", nargs="?", help="a singer, or a piece for check")
    p.add_argument("source", nargs="?", help="with add: the zip or folder")
    p.add_argument("--accept-terms", action="store_true",
                   help="you have read the voicebank's terms of use and agree to them")
    p.add_argument("--force", action="store_true", help="replace what is installed")

    p = sub.add_parser("voicebank", help="a recorded singing voice: show it, record "
                                         "it (once), or check what a piece's singer says")
    p.add_argument("action", choices=("show", "build", "check"),
                   help="build: record the bank (paid, needs OPENROUTER_API_KEY). "
                        "check: render a piece's singer alone and have a speech "
                        "recogniser write down what it hears (also paid)")
    p.add_argument("name", help="a voice for show/build ('sarah'), a piece for check")
    p.add_argument("--model", help="the speech model to record from")
    p.add_argument("--words", type=int, default=0,
                   help="with build: also record this many of the commonest English "
                        "words whole (2000 is about a dollar)")

    p = sub.add_parser("master", help="how hard the finished mix is hit")
    p.add_argument("name")
    p.add_argument("--push", type=float, help="dB into the limiter")
    p.add_argument("--clip", type=float, help="dB past full scale, tops cut off")
    p.add_argument("--level", type=float, help="dB (negative): turn the file down")

    p = sub.add_parser("tension", help="per bar: distance from home, surprise, and "
                                       "whether the climax was prepared")
    p.add_argument("name")
    p = sub.add_parser("hear", help="measure the rendered audio: who is loudest, is "
                                    "the tune clear, did every note sound")
    p.add_argument("name")
    p.add_argument("--soundfont", "-s", nargs="?", const="auto", metavar="SF2",
                   help="measure the sampled render instead of the built-in models")

    p = sub.add_parser("midi", help="export a .mid")
    p.add_argument("name"); p.add_argument("--out", "-o")
    p = sub.add_parser("wav", help="export a .wav")
    p.add_argument("name"); p.add_argument("--out", "-o")
    p.add_argument("--mono", action="store_true", help="one channel, no stereo seating")
    p.add_argument("--dry", action="store_true", help="no reverb")
    p.add_argument("--plain", action="store_true",
                   help="fixed oscillators instead of the instrument models")
    p.add_argument("--soundfont", "-s", nargs="?", const="auto", metavar="SF2",
                   help="render sampled instruments through FluidSynth; with no "
                        "path, uses $MUSICSTUDIO_SOUNDFONT or one found on the system")

    p = sub.add_parser("soundfont", help="show or download the SoundFont used by "
                                         "`wav --soundfont`")
    p.add_argument("action", nargs="?", choices=("show", "install", "banks"),
                   default="show")
    p.add_argument("bank", nargs="?", default=None,
                   help="which bank to install: hq (default) or standard")
    p.add_argument("--url", help="install some other .sf2/.sf3 instead")
    p.add_argument("--sha256", help="required with --url")
    p.add_argument("--force", action="store_true", help="download again")

    args = ap.parse_args(argv)
    s = Studio(args.project)

    try:
        return _dispatch(s, args)
    except (KeyError, ValueError, IndexError, TypeError, RuntimeError, ImportError,
            OSError) as exc:
        msg = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        print(f"error: {msg}", file=sys.stderr)
        return 2


def _dispatch(s: Studio, a) -> int:
    c = a.cmd
    if c == "styles":
        for st in s.describe_styles():
            print(f"{st['name']}: {st['summary']}")
            print(f"  forms: {', '.join(st['forms'])}")
            for n in st["notes"]:
                print(f"  - {n}")
            print()
        return 0
    if c == "ops":
        for op in s.describe_ops():
            print(f"{op['kind']:<12} [{op['kind_of']}] {op['doc']}")
            print(f"{'':<12} required: {op['required']}  optional: {sorted(op['optional'])}")
        return 0
    if c == "transforms":
        for k, v in s.describe_transforms().items():
            print(f"{k:<12} {v}")
        notation = s.describe_notation()
        print("\nornaments, written on a note as '4:1/4@tr':")
        for k, v in notation["ornaments"].items():
            print(f"{'@' + k:<12} {v}")
        print("articulations: " + " ".join("@" + a for a in notation["articulations"]))
        return 0
    if c == "instruments":
        d = s.describe_instruments(a.family)
        for i in d["instruments"]:
            print(f"{i['name']:<18} {i['family']:<9} {i['range'][0]:>4}-{i['range'][1]:<4} "
                  f"comfort {i['comfort'][0]:>4}-{i['comfort'][1]:<4} poly={i['polyphony']}")
        print(f"\nroles: {', '.join(d['roles'])}")
        return 0
    if c == "ls":
        for row in s.list_pieces():
            print(json.dumps(row))
        return 0
    if c == "new":
        p = s.create(a.name, key=a.key, tempo=a.tempo, meter=a.meter, style=a.style,
                     form=a.form, overwrite=a.overwrite, loop=a.loop)
        print(f"created {p.name}: {p.key.name}, q={p.tempo}, {p.meter}, style={p.style}"
              + (", loop" if p.loop else ""))
        print(f"sections: {[(x.name, x.bars) for x in p.sections] or 'none yet'}")
        print(f"file: {s.path_for(p.name)}")
        return 0
    if c == "piece":
        print(s.update_piece(a.name, key=a.key, tempo=a.tempo, style=a.style, loop=a.loop))
        return 0
    if c == "delete":
        s.delete(a.name)
        print(f"deleted {a.name} (undo brings it back)")
        return 0
    if c == "undo":
        print(s.undo(a.name))
        return 0
    if c == "redo":
        print(s.redo(a.name))
        return 0
    if c == "history":
        print(json.dumps(s.history(a.name)))
        return 0
    if c == "setsection":
        print(s.update_section(a.name, a.section, **_kwargs(a.fields)))
        return 0
    if c == "rmsection":
        print(s.remove_section(a.name, a.section))
        return 0
    if c == "setvoice":
        print(s.set_voice(a.name, a.voice, **_kwargs(a.fields)))
        return 0
    if c == "rmvoice":
        print(s.remove_voice(a.name, a.voice))
        return 0
    if c == "rmmotif":
        print(json.dumps(s.remove_motif(a.name, a.motif)))
        return 0
    if c == "toggle":
        print(s.set_op_enabled(a.name, a.op_id, a.state == "on"))
        return 0
    if c == "reorder":
        print(s.reorder_op(a.name, a.op_id, a.index, a.voice))
        return 0
    if c == "section":
        print(s.add_section(a.name, a.section, bars=a.bars, meter=a.meter, tempo=a.tempo,
                            key=a.key, dynamic=a.dynamic, note=a.note))
        return 0
    if c == "harmony":
        entries = []
        for pair in a.chords:
            if "=" not in pair:
                raise ValueError(f"expected BAR=NUMERAL, got {pair!r}")
            at, numeral = pair.split("=", 1)
            entries.append([at, numeral])
        print(s.set_harmony(a.name, entries, replace=not a.add))
        return 0
    if c == "voice":
        print(s.add_voice(a.name, a.voice, a.instrument, role=a.role, octave=a.octave,
                          dynamic=a.dynamic, pan=a.pan))
        return 0
    if c == "motif":
        print(json.dumps(s.add_motif(a.name, a.motif, a.source, anchor=a.anchor,
                                     unit=a.unit, scale=a.scale, note=a.note), indent=2))
        return 0
    if c == "derive":
        print(json.dumps(s.derive_motif(a.name, a.motif, a.source_motif, a.transforms,
                                        note=a.note), indent=2))
        return 0
    if c == "op":
        print(s.add_op(a.name, a.voice, a.kind, id=a.id, index=a.index, note=a.note,
                       **_kwargs(a.params)))
        return 0
    if c == "update":
        print(s.update_op(a.name, a.op_id, **_kwargs(a.params)))
        return 0
    if c == "move":
        print(s.move_op(a.name, a.op_id, a.bars, a.beats))
        return 0
    if c == "rm":
        print(s.remove_op(a.name, a.op_id))
        return 0
    if c == "list":
        for row in s.list_ops(a.name, a.voice):
            print(json.dumps(row))
        return 0
    if c == "show":
        print(s.score(a.name, bars=_bars(a.bars), res=a.res,
                      glyphs="degree" if a.degrees else "voice",
                      voices=a.voices or None, upto=a.upto))
        return 0
    if c == "import":
        r = s.import_music(a.name, a.path, kind=a.kind, instrument=a.instrument,
                           tempo=a.tempo, overwrite=a.overwrite)
        print(r["summary"])
        print(f"trust: {r['trust']}")
        for w in r["warnings"]:
            print(f"  ! {w}")
        return 0
    if c == "findmotifs":
        print(s.find_motifs(a.name, min_notes=a.min_notes, max_notes=a.max_notes,
                            p_max=a.p_max)["report"])
        return 0
    if c == "compare":
        print(s.compare(a.names, require=a.require, p_max=a.p_max)["report"])
        return 0
    if c == "adopt":
        print(json.dumps(s.adopt_pattern(a.name, a.motif, a.index), indent=2))
        return 0
    if c == "chart":
        print(s.chart(a.name))
        return 0
    if c == "motifs":
        print(s.motifs(a.name))
        return 0
    if c == "squint":
        print(s.squint(a.name))
        return 0
    if c == "stats":
        print(json.dumps(s.stats(a.name), indent=2))
        return 0
    if c == "part":
        print(s.voice(a.name, a.voice, bars=_bars(a.bars)))
        return 0
    if c == "lint":
        findings = s.lint(a.name)
        print(report(findings))
        return 1 if any(f.severity == "error" for f in findings) else 0
    if c == "lyrics":
        from . import lyrics
        if a.text == ["install"]:
            print(lyrics.install_dictionary())
            return 0
        syllables, warnings = lyrics.parse(" ".join(a.text), a.lang)
        for syl in syllables:
            print(f"  {syl.text:<12} {syl.to_json()}")
        for w in warnings:
            print(f"warning: {w}")
        print(f"{len(syllables)} syllables: one note each")
        return 0
    if c == "pattern":
        from . import pattern
        print(pattern.describe(" ".join(a.text), a.cycles, a.steps))
        return 0
    if c == "singer" and a.action != "check":
        return _singer(s, a)
    if c in ("voicebank", "singer") and a.action == "check":
        r = s.check_words(a.name)
        print(f"{r['voice']}: a recogniser understood {r['understood']:.0%} of "
              f"{r['words']} words")
        print(f"  heard:  {r['heard']}")
        if r["missed"]:
            print(f"  missed: {' '.join(r['missed'])}")
        if r.get("extra"):
            print(f"  heard but not written ({len(r['extra'])}): {' '.join(r['extra'])}")
        return 0
    if c == "voicebank":
        def tick(done, total, word):
            print(f"\r  {done}/{total} {word:<12}", end="", file=sys.stderr, flush=True)
        info = s.voicebank(a.name, build=a.action == "build", model=a.model,
                           words=a.words, progress=tick if a.action == "build" else None)
        if a.action == "build":
            print(file=sys.stderr)
        print(f"{info['voice']} ({info['model']}): {info['recorded']} of "
              f"{info['words']} unit words recorded, {info['vocabulary']} words in all"
              + ("" if info["complete"] else f"; missing {' '.join(info['missing'][:12])}"
                 + (" ..." if len(info["missing"]) > 12 else "")))
        print(f"  kept in {info['where']}")
        return 0
    if c == "master":
        print(s.set_master(a.name, push=a.push, clip=a.clip, level=a.level))
        return 0
    if c == "tension":
        print(s.tension(a.name))
        return 0
    if c == "hear":
        print(s.hear(a.name, source="soundfont" if a.soundfont else "models",
                     soundfont=a.soundfont))
        return 0
    if c == "midi":
        print(s.export_midi(a.name, a.out))
        return 0
    if c == "soundfont":
        from . import audio, soundfonts
        if a.action == "banks":
            for b in soundfonts.BANKS.values():
                mark = " (default)" if b.name == soundfonts.DEFAULT_BANK else ""
                print(f"{b.name:<9} {b.size_mb:>3} MB  {b.summary}{mark}")
            return 0
        if a.action == "install":
            bank = a.bank or soundfonts.DEFAULT_BANK
            if not a.url and bank in soundfonts.BANKS:
                b = soundfonts.BANKS[bank]
                print(f"fetching {b.filename} ({b.size_mb} MB) from "
                      f"{b.url.split('/')[2]}", file=sys.stderr)
            path = soundfonts.install(bank, url=a.url, sha256=a.sha256, force=a.force)
            print(path)
            return 0
        try:
            print(f"in use:    {audio.find_soundfont()}")
        except FileNotFoundError as exc:
            print(f"in use:    none -- {exc}")
        for f in soundfonts.installed():
            print(f"installed: {f}")
        print(f"fluidsynth: {shutil.which('fluidsynth') or 'not found on PATH'}")
        return 0
    if c == "wav":
        print(s.export_wav(a.name, a.out, stereo=not a.mono,
                           reverb=False if a.dry else None,
                           models=False if a.plain else None,
                           soundfont=a.soundfont))
        return 0
    raise ValueError(f"unhandled command {c!r}")  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
