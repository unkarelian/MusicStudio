"""A neural singer: a DiffSinger voicebank, sung from the score.

`vocal.py` is a model of a voice and `voicebank.py` re-pitches recorded speech.
This is the third engine and the only one that was trained on *singing*: a
DiffSinger voicebank in the layout OpenUtau uses, run through ONNX Runtime. A
bank is five small models, and a phrase goes through them in order:

    duration   how long each consonant takes at this tempo
    pitch      the curve a singer would draw through the written notes
    variance   breathiness and voicing, frame by frame
    acoustic   phonemes + durations + pitch  ->  a mel spectrogram (diffusion)
    vocoder    mel spectrogram + pitch       ->  sound

**No voicebank ships with the studio and none is fetched by a render.** Each
one is somebody's voice under that person's terms. `CATALOGUE` lists the ones
whose terms were read and what they ask; `install` downloads one only when
called with ``accept=True``, pinned by SHA-256 like every other download here
(`soundfonts._fetch`), and `add` registers a bank you obtained yourself. A
voice whose bank is not installed, or a machine without ``onnxruntime``, falls
back to the synthesized singer with a warning -- CI has neither.

What the studio decides and what the bank decides: the studio gives the notes,
where each syllable's vowel starts (exactly on its note, as in `vocal.py`) and
which phonemes are sung; the bank decides consonant lengths, the pitch curve
between and within the notes, and the timbre. So the melody is the score's and
the *singing* of it is the bank's.

Seeded means seeded: the diffusion noise is drawn inside the models, so every
run is preceded by ``onnxruntime.set_seed`` with a seed derived from the voice
and the phrase through ``crc32``. A rendered phrase is also kept on disk
(`CACHE_DIR`), keyed by everything that went into it, because diffusion on a
CPU takes seconds per phrase and `hear` renders every voice more than once.

The conventions for feeding these models (eight frames of silence either side,
boundaries rounded cumulatively, a word beginning at its vowel with the
consonants before it belonging to the word before) are OpenUtau's
(MIT, (c) StAkira and contributors: OpenUtau.Core/DiffSinger), which the banks
are exported for; erz0r/warble (MIT) was the reference for reading them.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import threading
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

try:
    import numpy as np
except ImportError:                                   # pragma: no cover
    np = None

SR = 44100
#: Installed banks, one folder each, and the vocoders they share.
SINGER_DIR = Path("~/.local/share/musicstudio/singers")
CACHE_DIR = Path("~/.cache/musicstudio/neural")

#: Diffusion steps. More is slower and, past about twenty, not audibly better.
STEPS = 20
PITCH_STEPS = 10
#: How far (semitones) a note's middle may sit from the written pitch before
#: `_land` corrects it, and how much of the rest it takes out. A singer a few
#: cents off is a singer; one a semitone flat is on another note.
PITCH_SLACK = 0.12
PITCH_PULL = 1.0
#: Bump when this module would sing the same phrase differently, so that
#: phrases cached by an older version are not mistaken for current ones.
ENGINE = 6
HEAD = TAIL = 8                 # frames of silence the models expect around a phrase
LEAD_MS = 500.0                 # what the duration model is told came before the phrase
#: How loud a neural voice is at full velocity: the level of its sung vowels
#: (RMS), set where the synthesized singers sit. Banks come out anywhere within
#: 12 dB of each other, so each is measured once (`trim`) and brought here.
LEVEL = 0.235
#: A gap inside a phrase shorter than this is sung through; longer is a rest.
REST = 0.06
#: The longest breath (seconds) taken before a phrase, where the line before
#: left room for one, sung with the bank's own breath phoneme (``AP``). A
#: singer who never breathes is the first thing a listener calls a machine.
#: 0 turns breaths off.
BREATH = 0.3


# --------------------------------------------------------------------------
# what can be installed, and what it asks of you
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Entry:
    """A voicebank the studio knows where to get. It is not part of the studio."""

    name: str
    title: str
    voice: str
    languages: tuple[str, ...]
    by: str
    homepage: str
    terms: str
    #: A plain summary of the terms, for the moment of installing. The linked
    #: document is the authority, not this.
    asks: tuple[str, ...]
    url: str = ""
    sha256: str = ""
    megabytes: int = 0
    vocoder: str = ""
    #: The folder inside the archive that holds ``dsconfig.yaml``.
    inner: str = ""


@dataclass(frozen=True)
class Vocoder:
    name: str
    url: str
    sha256: str
    licence: str
    homepage: str


VOCODERS = {
    "pc_nsf_hifigan_44.1k_hop512_128bin_2025.02": Vocoder(
        "pc_nsf_hifigan_44.1k_hop512_128bin_2025.02",
        "https://github.com/openvpi/vocoders/releases/download/"
        "pc-nsf-hifigan-44.1k-hop512-128bin-2025.02/"
        "pc_nsf_hifigan_44.1k_hop512_128bin_2025.02.oudep",
        "ba7d43142d41f6900c8264b5662ca7125a50feb8760bb8b9615c61a8f5e6902e",
        "CC BY-NC-SA 4.0 for the model weights (by the OpenVPI Team): credit "
        "OpenVPI and keep the licence if you pass the weights on, and do not "
        "sell them; songs made with it are not restricted by this licence",
        "https://openvpi.github.io/vocoders/"),
}

CATALOGUE = {
    "qixuan": Entry(
        name="qixuan",
        title="Qixuan (绮萱) v2.7.0",
        voice="a bright, young female voice",
        languages=("zh", "en", "ja"),
        by="voice: 颜绮萱; model: YQ之神 and the DiffSinger community",
        homepage="https://github.com/yqzhishen/qixuan-diffsinger",
        terms="https://github.com/yqzhishen/qixuan-diffsinger/blob/main/"
              "terms_of_use/Terms_of_Use.zh-CN.md",
        asks=(
            "Music made with it may be shared and sold.",
            "When you publish, say that the vocal is AI-synthesized and credit "
            "the voicebank as \"绮萱\" (Qixuan) and the engine as \"DiffSinger\"; "
            "do not credit the voice under any other name.",
            "Not for violent, sexual, abusive or otherwise unlawful content, nor "
            "for political or religious propaganda.",
            "Do not use what it sings to train or sample another voice model.",
            "Do not modify, convert, fine-tune or distil the model files.",
            "You may pass the voicebank on only whole, unmodified, free of "
            "charge, and with its terms.",
            "The terms are in Chinese and the Chinese text is the one that "
            "counts; this is a summary, not a translation.",
        ),
        url="https://github.com/yqzhishen/qixuan-diffsinger/releases/download/"
            "v2.7.0/Qixuan_v2.7.0_DiffSinger_OpenUtau.zip",
        sha256="fe8ee7c95883d327a2b7facbbe832a7a53e1344918dc791ca83fc23b08034110",
        megabytes=401,
        vocoder="pc_nsf_hifigan_44.1k_hop512_128bin_2025.02",
        inner="Qixuan_v2.7.0_DiffSinger_OpenUtau"),
    "shisakune": Entry(
        name="shisakune",
        title="Shisakune Demo (试作音Demo) v4.5.1",
        voice="three voice colours: smooth, solid, symphonic",
        languages=("zh", "en", "ja"),
        by="voice: UG (SnowbootP, tuskinekinase); training: Hisaka",
        homepage="https://github.com/tuskinekinase/shisakunedemo_ds",
        terms="https://github.com/tuskinekinase/shisakunedemo_ds/blob/main/LICENSE",
        asks=(
            "The voicebank is under CC BY-NC-SA 4.0: credit it by name, do not "
            "use it commercially, and share anything adapted from it under the "
            "same licence.",
            "Its repository gives no separate terms for songs made with it, so "
            "treat those as non-commercial too unless its authors tell you "
            "otherwise.",
        ),
        url="https://github.com/tuskinekinase/shisakunedemo_ds/releases/download/"
            "v4.5.1/Shisakune-Demo_CN.EN.JP_v4.5.1.zip",
        sha256="09e963976f733d70cf9cfac83fa937540c56bb353754995a5abd7076d9631987",
        megabytes=502),
    "alemon": Entry(
        name="alemon",
        title="Alemon (柠檬君) v3.5",
        voice="two voice colours: normal, falsetto",
        languages=("zh", "en", "ja"),
        by="tuskinekinase; training: Hisaka",
        homepage="https://github.com/tuskinekinase/alemon_ds",
        terms="https://github.com/tuskinekinase/alemon_ds/blob/main/LICENSE",
        asks=(
            "The voicebank is under CC BY-NC-SA 4.0: credit it by name, do not "
            "use it commercially, and share anything adapted from it under the "
            "same licence.",
            "Its repository gives no separate terms for songs made with it, so "
            "treat those as non-commercial too unless its authors tell you "
            "otherwise.",
        ),
        url="https://github.com/tuskinekinase/alemon_ds/releases/download/"
            "v3.5/Alemon_CN.EN.JP_v3.5.zip",
        sha256="47acc0112c236b51a230de71f0a6cf2c167d346b1eeed2853cd68a7a64958e19",
        megabytes=502),
}


def singer_dir(name: str) -> Path:
    return SINGER_DIR.expanduser() / _clean(name)


def _clean(name: str) -> str:
    out = "".join(c for c in name.lower() if c.isalnum() or c in "-_.")
    if not out or out.startswith((".", "_")):
        raise ValueError(f"not a usable singer name: {name!r}")
    return out


def parse_bank(bank: str) -> tuple[str, str]:
    """``"qixuan"`` or ``"name:speaker"`` for a bank with several voices."""
    name, _, speaker = bank.partition(":")
    return name.strip(), speaker.strip()


def parse_mix(speaker: str) -> list[tuple[str, float]]:
    """``"a*0.6+b*0.4"`` as ``[("a", 0.6), ("b", 0.4)]``: a voice blended from
    several of a bank's own. The weights are relative (they are scaled to sum
    to one) and a voice named without one counts as 1, so ``"a+b"`` is half of
    each. A plain name is a blend of one."""
    out: list[tuple[str, float]] = []
    for term in speaker.split("+"):
        name, star, weight = term.partition("*")
        name = name.strip()
        if not name:
            continue
        try:
            w = float(weight) if star else 1.0
        except ValueError:
            raise ValueError(f"not a blend weight: {weight.strip()!r} in {speaker!r}") from None
        if w < 0:
            raise ValueError(f"a blend weight cannot be negative: {term.strip()!r}")
        out.append((name, w))
    return out


def installed() -> list[str]:
    root = SINGER_DIR.expanduser()
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir()
                  if d.is_dir() and (d / "dsconfig.yaml").is_file())


def is_installed(name: str) -> bool:
    try:
        return (singer_dir(name) / "dsconfig.yaml").is_file()
    except ValueError:
        return False


def knows(bank: str) -> bool:
    """Whether a voice's ``bank`` names a neural singer (installed or listed)."""
    name = parse_bank(bank)[0].lower()
    return name in CATALOGUE or is_installed(name)


def available() -> bool:
    """Whether this machine can run a neural singer at all."""
    if np is None:
        return False
    try:
        import onnxruntime  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


#: The most an archive may unpack to. The largest listed bank is about half a
#: gigabyte; a zip that declares far more than that is not a voicebank.
UNPACK_LIMIT = 8 << 30


def _unpack(archive: Path | bytes, dest: Path, inner: str = "",
            needs: tuple[str, ...] = ("dsconfig.yaml", "vocoder.yaml")) -> None:
    """Extract a zip into ``dest``, refusing any member that would land outside
    it. What is already at ``dest`` is replaced only once the new folder is
    whole and has one of the files in ``needs``: a bad archive must not cost
    the user the working install it was meant to replace."""
    import io
    z = zipfile.ZipFile(io.BytesIO(archive) if isinstance(archive, bytes) else archive)
    if sum(info.file_size for info in z.infolist()) > UNPACK_LIMIT:
        raise ValueError(f"archive unpacks to more than {UNPACK_LIMIT >> 30} GB; refusing")
    tmp = dest.with_name(dest.name + ".part")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    root = tmp.resolve()
    for info in z.infolist():
        target = (tmp / info.filename).resolve()
        if root != target and root not in target.parents:
            shutil.rmtree(tmp)
            raise ValueError(f"archive member escapes its folder: {info.filename!r}")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    source = tmp / inner if inner else tmp
    if not inner and not (source / "dsconfig.yaml").is_file() \
            and not (source / "vocoder.yaml").is_file():
        # One wrapping folder is usual.
        inside = [d for d in tmp.iterdir() if d.is_dir()]
        if len(inside) == 1:
            source = inside[0]
    if not any((source / n).is_file() for n in needs):
        shutil.rmtree(tmp)
        raise ValueError(f"not a DiffSinger voicebank: the archive has no "
                         f"{' or '.join(needs)}")
    if dest.exists():
        shutil.rmtree(dest)
    source.rename(dest)
    if tmp.exists():
        shutil.rmtree(tmp)


def _download(url: str, sha256: str, dest: Path, inner: str, needs: tuple[str, ...],
              progress=None) -> None:
    """Fetch a pinned archive to disk (never into memory: these are hundreds
    of megabytes) and unpack it."""
    from . import soundfonts
    archive = soundfonts._fetch_file(url, sha256, dest.parent, progress)
    try:
        _unpack(archive, dest, inner, needs)
    finally:
        Path(archive).unlink(missing_ok=True)


def install_vocoder(name: str, *, progress=None, force: bool = False) -> Path:
    dest = SINGER_DIR.expanduser() / "vocoders" / name
    if (dest / "vocoder.yaml").is_file() and not force:
        return dest
    if name not in VOCODERS:
        raise ValueError(f"no known download for the vocoder {name!r}; put its folder "
                         f"(with vocoder.yaml) at {dest}")
    v = VOCODERS[name]
    dest.parent.mkdir(parents=True, exist_ok=True)
    _download(v.url, v.sha256, dest, "", ("vocoder.yaml",), progress)
    (dest / "SOURCE.txt").write_text(
        f"{v.name}\nfrom {v.url}\nsha256 {v.sha256}\nlicence: {v.licence}\n{v.homepage}\n")
    return dest


def install(name: str, *, accept: bool = False, progress=None, force: bool = False) -> Path:
    """Download a listed voicebank and the vocoder it needs.

    Nothing is fetched unless ``accept`` is true: the voicebank is someone's
    voice, and using it means agreeing to their terms (`CATALOGUE[name].asks`
    summarizes them and ``.terms`` links the real ones).
    """
    key = _clean(name)
    if key not in CATALOGUE:
        raise ValueError(f"no voicebank called {name!r} is listed "
                         f"(listed: {', '.join(sorted(CATALOGUE))}). To use one you "
                         f"downloaded yourself: ms singer add <name> <zip or folder>")
    e = CATALOGUE[key]
    if not accept:
        raise PermissionError(
            f"{e.title} is not part of MusicStudio and has its own terms of use:\n  "
            + "\n  ".join(f"- {a}" for a in e.asks)
            + f"\n  full terms: {e.terms}"
            # The vocoder comes with it and is a second work under a second
            # licence; accepting must be accepting both.
            + (f"\nIt also needs the vocoder {e.vocoder}, which is downloaded with "
               f"it: {VOCODERS[e.vocoder].licence} ({VOCODERS[e.vocoder].homepage})."
               if e.vocoder in VOCODERS else "")
            + "\nInstall it with --accept-terms once you agree.")
    dest = singer_dir(key)
    if is_installed(key) and not force:
        if e.vocoder:
            install_vocoder(e.vocoder, progress=progress)
        return dest
    if not e.url:
        raise ValueError(f"{e.title} has no direct download; get it from {e.homepage} "
                         f"and run: ms singer add {key} <zip or folder>")
    dest.parent.mkdir(parents=True, exist_ok=True)
    _download(e.url, e.sha256, dest, e.inner, ("dsconfig.yaml",), progress)
    (dest / "SOURCE.txt").write_text(
        f"{e.title}\nfrom {e.url}\nsha256 {e.sha256}\n{e.by}\n"
        f"terms of use: {e.terms}\n\nIn short (the linked terms are the authority):\n"
        + "".join(f"- {a}\n" for a in e.asks))
    if e.vocoder:
        install_vocoder(e.vocoder, progress=progress)
    _singers.pop(key, None)
    return dest


def add(name: str, source: str | Path, *, force: bool = False) -> Path:
    """Register a DiffSinger voicebank you obtained yourself (a zip or a folder
    in OpenUtau's layout). Its terms are yours to read and keep to."""
    key = _clean(name)
    src = Path(source).expanduser()
    dest = singer_dir(key)
    if dest.exists() and not force:
        raise FileExistsError(f"a singer called {key!r} is already installed at {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        root = src
        if not (root / "dsconfig.yaml").is_file():
            inside = [d for d in src.iterdir() if (d / "dsconfig.yaml").is_file()]
            if len(inside) != 1:
                raise ValueError(f"{src} is not a DiffSinger voicebank: no dsconfig.yaml")
            root = inside[0]
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(root, dest)
    elif src.is_file():
        _unpack(src, dest, needs=("dsconfig.yaml",))
    else:
        raise FileNotFoundError(str(src))
    if not (dest / "dsconfig.yaml").is_file():
        shutil.rmtree(dest)
        raise ValueError(f"{src} is not a DiffSinger voicebank: no dsconfig.yaml")
    _singers.pop(key, None)
    return dest


BLEND_FILE = "blend.yaml"


def _same_file(a: Path, b: Path) -> bool:
    if a.stat().st_size != b.stat().st_size:
        return False
    ha, hb = hashlib.sha256(), hashlib.sha256()
    for h, p in ((ha, a), (hb, b)):
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    return ha.digest() == hb.digest()


def parse_recipe(recipe: str) -> list[tuple[str, str, float]]:
    """``"shisakune:smooth*0.5+alemon:normal*0.5"`` as ``[(bank, voice,
    weight), ...]``, the weights scaled to sum to one. A term without a bank
    belongs to the bank named before it; one without a voice is that bank's
    first."""
    out, bank = [], ""
    for term, w in parse_mix(recipe):
        b, colon, voice = term.partition(":")
        if colon:
            bank = _clean(b)
        elif not bank:
            bank, voice = _clean(b), ""
        else:
            voice = b
        out.append((bank, voice.strip(), w))
    total = sum(w for _, _, w in out)
    if not out or total <= 0:
        raise ValueError(f"nothing to blend in {recipe!r}")
    return [(b, v, w / total) for b, v, w in out]


def blend(name: str, recipe: str, *, gender: float = 0.0, force: bool = False) -> Path:
    """Make a new singer by blending voices that live in one model.

    A DiffSinger model that was trained on several voices tells them apart by
    an embedding, a point in a space the model learned; a point between two of
    them is a voice that is neither. Banks released separately sometimes share
    one model (their acoustic files are byte for byte the same), and then
    their voices can be blended with each other as well. ``recipe`` names the
    voices and their shares (:func:`parse_recipe`); ``gender`` (-1..1) is a
    formant shift the new singer always sings with, which moves it further
    from its sources than the blend alone does.

    The result is a bank of its own under ``name``: the first source's models
    (linked, not copied, where the disk allows), one blended embedding, and a
    ``blend.yaml`` that records the recipe and whose voices it came from. It
    is an adaptation of every bank in the recipe and their terms all apply to
    it; a bank whose terms forbid modification must not be blended.
    """
    import yaml
    key = _clean(name)
    if key in CATALOGUE:
        raise ValueError(f"{key!r} is a listed voicebank; give the blend another name")
    parts = parse_recipe(recipe)
    dest = singer_dir(key)
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} exists (use force to replace it)")
    banks = list(dict.fromkeys(b for b, _, _ in parts))
    for b in banks:
        if not is_installed(b):
            raise FileNotFoundError(f"the singer {b!r} is not installed")
        if (singer_dir(b) / BLEND_FILE).is_file():
            raise ValueError(f"{b!r} is itself a blend; blend from its sources instead")
    roots = {b: singer_dir(b) for b in banks}
    models = {b: _Model(roots[b]) for b in banks}
    base = banks[0]
    subs = [""] + [d for d in ("dsvariance", "dspitch", "dsdur")
                   if (roots[base] / d / "dsconfig.yaml").is_file()
                   and _Model(roots[base] / d).speakers]
    # The voices must be points in one space: the same model, to the byte.
    for sub in subs:
        mine = _Model(roots[base] / sub) if sub else models[base]
        keys = [k for k in ("acoustic", "variance", "pitch", "dur", "linguistic") if mine.path(k)]
        for b in banks[1:]:
            folder = roots[b] / sub
            other = _Model(folder) if (folder / "dsconfig.yaml").is_file() else None
            for k in keys:
                if other is None or other.path(k) is None \
                        or not _same_file(mine.path(k), other.path(k)):
                    raise ValueError(
                        f"{base!r} and {b!r} are not voices of one model (their "
                        f"{sub or 'acoustic'} models differ), so they cannot be blended")
    vectors: dict[str, "np.ndarray"] = {}
    for sub in subs:
        total = None
        for b, voice, w in parts:
            m = _Model(roots[b] / sub) if sub else models[b]
            pick = m._find(voice) if voice else (m.speakers[0] if m.speakers else None)
            if pick is None:
                raise ValueError(f"the singer {b!r} has no voice {voice!r}; it has "
                                 f"{', '.join(models[b].speakers) or 'only one'}")
            v = m._one(pick) * np.float32(w)
            total = v if total is None else total + v
        vectors[sub] = total.astype("<f4")

    tmp = dest.with_name(dest.name + ".part")
    if tmp.exists():
        shutil.rmtree(tmp)
    for src in sorted(roots[base].rglob("*")):
        rel = src.relative_to(roots[base])
        if src.is_dir():
            (tmp / rel).mkdir(parents=True, exist_ok=True)
            continue
        # Not the source's embeddings, nor its name and portrait: this is not it.
        if src.suffix.lower() in (".emb", ".bmp", ".png", ".jpg", ".jpeg") or src.name in (
                "dsconfig.yaml", "SOURCE.txt", "character.txt", "character.yaml"):
            continue
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, tmp / rel)
        except OSError:
            shutil.copy2(src, tmp / rel)
    for sub in ("", "dsvariance", "dspitch", "dsdur"):
        cfg_path = roots[base] / sub / "dsconfig.yaml"
        if not cfg_path.is_file():
            continue
        cfg = _yaml(cfg_path)
        if sub in vectors:
            cfg["speakers"] = [key]
            (tmp / sub / f"{key}.emb").write_bytes(vectors[sub].tobytes())
        (tmp / sub / "dsconfig.yaml").write_text(
            yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    sources = []
    for b in banks:
        e = CATALOGUE.get(b)
        sources.append({"name": b, "title": e.title if e else b, "by": e.by if e else "",
                        "homepage": e.homepage if e else "", "terms": e.terms if e else "",
                        "asks": list(e.asks) if e else []})
    (tmp / BLEND_FILE).write_text(yaml.safe_dump({
        "name": key,
        "recipe": [{"bank": b, "voice": v, "share": round(w, 4)} for b, v, w in parts],
        "gender": max(-1.0, min(1.0, float(gender))),
        "models_from": base,
        "sources": sources,
    }, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (tmp / "character.txt").write_text(f"name={key}\n", encoding="utf-8")
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)
    _singers.pop(key, None)
    return dest


def blend_info(name: str) -> dict | None:
    """The recipe of a blended singer, or None for a bank that is not one."""
    path = singer_dir(_clean(parse_bank(name)[0])) / BLEND_FILE
    return _yaml(path) if path.is_file() else None


def describe(name: str) -> dict:
    """What is known about a singer: listed terms, whether it is installed, and
    whether everything it needs to make sound is here."""
    key = _clean(parse_bank(name)[0])
    e = CATALOGUE.get(key)
    info: dict = {"name": key, "installed": is_installed(key), "where": str(singer_dir(key)),
                  "listed": e is not None, "runtime": available()}
    if e:
        info.update(title=e.title, voice=e.voice, languages=list(e.languages), by=e.by,
                    homepage=e.homepage, terms=e.terms, asks=list(e.asks),
                    megabytes=e.megabytes, vocoder=e.vocoder)
    made = blend_info(key) if info["installed"] and available() else None
    if made:
        src = made.get("sources") or []
        shares = ", ".join(f"{round(100 * float(r['share']))}% {r['bank']}"
                           + (f":{r['voice']}" if r.get("voice") else "")
                           for r in made.get("recipe") or [])
        asks = [f"It is an adaptation of {' and '.join(x['title'] for x in src)}, "
                f"and the terms of each apply to it."]
        for x in src:
            asks += [a for a in x.get("asks") or [] if a not in asks]
        info.update(title=f"{key} (a blended voice)",
                    voice=f"blended: {shares}; formant shift {float(made.get('gender', 0)):+.2f}",
                    by="; ".join(f"{x['title']}: {x['by']}" for x in src if x.get("by")),
                    homepage=" ".join(x["homepage"] for x in src if x.get("homepage")),
                    terms=" ".join(x["terms"] for x in src if x.get("terms")),
                    asks=asks, blend=made)
    if info["installed"] and available():
        try:
            s = load(key)
            info.update(languages=sorted(s.acoustic.languages) or info.get("languages", []),
                        speakers=s.acoustic.speakers, vocoder=s.vocoder_name,
                        vocoder_installed=s.vocoder_path is not None,
                        models=[r for r in ("dur", "pitch", "variance") if getattr(s, r)])
        except Exception as exc:                      # a broken bank is reported, not raised
            info["problem"] = str(exc)
    return info


# --------------------------------------------------------------------------
# a bank on disk
# --------------------------------------------------------------------------

def _yaml(path: Path) -> dict:
    import yaml
    with open(path, encoding="utf-8-sig") as f:
        return yaml.safe_load(f) or {}


class _Model:
    """One model folder of a bank: its config, its own phoneme numbering (every
    sub-model has one, and they differ) and its language ids."""

    def __init__(self, folder: Path):
        self.dir = folder
        self.cfg = _yaml(folder / "dsconfig.yaml")
        ph = folder / str(self.cfg.get("phonemes", "phonemes.txt"))
        if ph.suffix == ".json":
            self.tokens = {str(k): int(v) for k, v in
                           json.loads(ph.read_text(encoding="utf-8-sig")).items()}
        else:
            self.tokens = {line: i for i, line in
                           enumerate(ph.read_text(encoding="utf-8-sig").splitlines())}
        self.languages: dict[str, int] = {}
        if self.cfg.get("languages"):
            lp = folder / str(self.cfg["languages"])
            if lp.is_file():
                self.languages = {str(k): int(v) for k, v in
                                  json.loads(lp.read_text(encoding="utf-8-sig")).items()}
        self.speakers = [str(s) for s in (self.cfg.get("speakers") or [])]
        self._embeds: dict[str, "np.ndarray"] = {}

    @property
    def frame_ms(self) -> float:
        return 1000.0 * float(self.cfg.get("hop_size", 512)) / float(self.cfg.get("sample_rate", SR))

    def path(self, key: str) -> Path | None:
        val = self.cfg.get(key)
        p = self.dir / str(val) if val else None
        return p if p is not None and p.is_file() else None

    def lang_id(self, symbol: str) -> int:
        return self.languages.get(symbol.partition("/")[0], 0) if "/" in symbol else 0

    def _one(self, pick: str) -> "np.ndarray":
        if pick not in self._embeds:
            hidden = int(self.cfg.get("hidden_size", 256))
            raw = np.frombuffer((self.dir / (pick + ".emb")).read_bytes(), dtype="<f4")
            if len(raw) < hidden:
                raise ValueError(f"speaker embedding {pick}.emb is too short for this model")
            self._embeds[pick] = raw[:hidden].astype(np.float32)
        return self._embeds[pick]

    def _find(self, speaker: str) -> str | None:
        for s in self.speakers:
            if s == speaker or s.replace("\\", "/").split("/")[-1] == speaker:
                return s
        return None

    def embed(self, speaker: str, frames: int) -> "np.ndarray":
        """``[1, frames, hidden]`` for one of the bank's voices, or for a blend
        of them (``"a*0.6+b*0.4"``; see :func:`parse_mix`). A voice this model
        does not have is left out of the blend; if none is left, the bank's
        first voice sings."""
        parts = [(self._find(n), w) for n, w in parse_mix(speaker)]
        parts = [(n, w) for n, w in parts if n is not None]
        total = sum(w for _, w in parts)
        if not parts or total <= 0:
            vec = self._one(self.speakers[0])
        else:
            vec = sum(self._one(n) * np.float32(w / total) for n, w in parts)
        return np.broadcast_to(vec, (1, frames, len(vec))).copy()


#: The studio's phonemes that are not a bank's own, as what to sing instead.
#: Tried in order; the first whose every part the bank has is used.
FALLBACKS = {
    "a": (("ja/a",), ("aa",)), "i": (("ja/i",), ("iy",)), "u": (("ja/u",), ("uw",)),
    "e": (("ja/e",), ("eh",)), "o": (("ja/o",), ("ow",)),
    "N": (("ja/N",), ("n",)), "ts": (("ja/ts",), ("t", "s")),
    "rr": (("ja/r",), ("dx",), ("r",)), "q": ((),),
    "ax": (("ah",),), "dx": (("d",),), "zh": (("jh",),), "er": (("ah", "r"),),
}


class Singer:
    """An installed bank, with its models loaded on first use."""

    def __init__(self, name: str):
        self.name = name
        root = singer_dir(name)
        if not (root / "dsconfig.yaml").is_file():
            raise FileNotFoundError(f"no singer {name!r} at {root}")
        self.acoustic = _Model(root)
        self.dur = self._sub(root / "dsdur", "dur")
        self.pitch = self._sub(root / "dspitch", "pitch")
        self.variance = self._sub(root / "dsvariance", "variance")
        #: A blended singer's own formant shift; a `tone` op's adds to it.
        made = _yaml(root / BLEND_FILE) if (root / BLEND_FILE).is_file() else {}
        self.gender = float(made.get("gender", 0.0) or 0.0)
        self.vocoder_name = str(self.acoustic.cfg.get("vocoder", ""))
        self.vocoder_cfg: dict = {}
        self.vocoder_path = self._find_vocoder(root)
        self._inputs: dict[Path, set[str]] = {}
        self._dicts: dict[str, dict[str, list[str]]] = {}
        self.stamp = f"{name}|{_fingerprint(root)}|{self.vocoder_name}|" + (
            _fingerprint(self.vocoder_path.parent) if self.vocoder_path else "")

    @staticmethod
    def _sub(folder: Path, key: str) -> _Model | None:
        if not (folder / "dsconfig.yaml").is_file():
            return None
        m = _Model(folder)
        return m if m.path(key) and m.path("linguistic") else None

    def _find_vocoder(self, root: Path) -> Path | None:
        for folder in (root / "dsvocoder", SINGER_DIR.expanduser() / "vocoders" / self.vocoder_name):
            cfg = folder / "vocoder.yaml"
            if cfg.is_file():
                self.vocoder_cfg = _yaml(cfg)
                model = folder / str(self.vocoder_cfg.get("model", "model.onnx"))
                if model.is_file():
                    return model
        return None

    # -- running a model ----------------------------------------------------
    def _session(self, path: Path, seed: int):
        """A model, freshly loaded and seeded.

        ONNX Runtime seeds a graph's random nodes when the session is built
        and never again, so a session kept between phrases would draw each
        phrase's noise from wherever the last one left off: the same phrase
        would come out differently depending on what was rendered before it.
        Loading takes a few tenths of a second and buys a render that depends
        only on its own inputs.
        """
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.log_severity_level = 3
        # The seed is process-wide and read when the session is built, so the
        # two steps must not interleave with another thread's.
        with _seeding:
            ort.set_seed(int(seed) & 0x7FFFFFFF)
            return ort.InferenceSession(str(path), sess_options=opts,
                                        providers=["CPUExecutionProvider"])

    def run(self, path: Path, feeds: dict, seed: int) -> dict:
        """Run one model, feeding exactly the inputs its graph declares."""
        sess = self._session(path, seed)
        kinds = {"tensor(float)": np.float32, "tensor(int64)": np.int64,
                 "tensor(bool)": np.bool_, "tensor(int32)": np.int32,
                 "tensor(double)": np.float64}
        ready = {}
        for meta in sess.get_inputs():
            if meta.name not in feeds:
                raise RuntimeError(f"{self.name}: the model {path.name} needs an input "
                                   f"{meta.name!r} that this engine does not provide")
            arr = np.asarray(feeds[meta.name])
            want = kinds.get(meta.type)
            if want is not None and arr.dtype != want:
                arr = arr.astype(want)
            if arr.ndim != len(meta.shape) and arr.size == 1:
                arr = arr.reshape(() if not meta.shape else (1,) * len(meta.shape))
            ready[meta.name] = arr
        names = [o.name for o in sess.get_outputs()]
        return dict(zip(names, sess.run(names, ready)))

    def inputs(self, path: Path) -> set[str]:
        if path not in self._inputs:
            self._inputs[path] = {i.name for i in self._session(path, 0).get_inputs()}
        return self._inputs[path]

    # -- phonemes -----------------------------------------------------------
    def pronounce(self, word: str, lang: str = "en") -> list[str] | None:
        """How the bank's own dictionary says a word, in its symbols.

        The bank was trained on these spellings, and they know things a plain
        pronouncing dictionary does not mark: which vowels are reduced
        (``en/ax`` in "the") and which t's and d's are flapped (``en/dx`` in
        "puddles"). The dictionaries run to a million lines, so each is read
        once with a line scanner and kept as JSON in the cache.
        """
        if lang not in self._dicts:
            self._dicts[lang] = self._read_dict(lang)
        return self._dicts[lang].get(word.lower())

    def _read_dict(self, lang: str) -> dict[str, list[str]]:
        root = self.acoustic.dir
        for cand in (root / "dsdur" / f"dsdict-{lang}.yaml", root / f"dsdict-{lang}.yaml"):
            if cand.is_file():
                break
        else:
            return {}
        st = cand.stat()
        kept = CACHE_DIR.expanduser() / "dict-{}.json".format(hashlib.sha256(
            f"{cand}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:24])
        if kept.is_file():
            try:
                return json.loads(kept.read_text(encoding="utf-8"))
            except ValueError:
                pass
        out: dict[str, list[str]] = {}
        word, phones = None, None
        with open(cand, encoding="utf-8-sig") as f:
            for line in f:
                if line.startswith("- grapheme:"):
                    word = line[11:].strip().strip("'\"").lower()
                    phones = None
                elif word is not None and line.startswith("  phonemes:"):
                    inline = line[11:].strip()
                    if inline.startswith("["):
                        phones = [x.strip().strip("'\"") for x in inline[1:-1].split(",") if x.strip()]
                        out.setdefault(word, phones)       # the first spelling of a word wins
                        word = None
                    else:
                        phones = []
                        fresh = word not in out
                        if fresh:
                            out[word] = phones
                        else:
                            phones = None
                elif phones is not None and line.startswith("  - "):
                    phones.append(line[4:].strip().strip("'\""))
                elif not line.startswith(" "):
                    word, phones = None, None
        try:
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_text(json.dumps(out), encoding="utf-8")
        except OSError:
            pass
        return out

    def symbols(self, phoneme: str, lang: str = "en") -> list[str]:
        """One of the studio's phonemes as this bank's symbols."""
        table = self.acoustic.tokens

        def find(p: str) -> str | None:
            if "/" in p:
                return p if p in table else None
            for cand in (f"{lang}/{p}", p, f"en/{p}", f"ja/{p}"):
                if cand in table:
                    return cand
            return None

        hit = find(phoneme)
        if hit and phoneme not in ("a", "i", "u", "e", "o", "N"):
            return [hit]
        for option in FALLBACKS.get(phoneme, ()):
            found = [find(p) for p in option]
            if all(found):
                return [f for f in found if f]
        return [hit] if hit else []


_singers: dict[str, tuple[str, Singer]] = {}
_seeding = threading.Lock()
_trims: dict[tuple[str, str], float] = {}


def trim(singer: "Singer", speaker: str = "") -> float:
    """The gain that brings this bank (and voice colour) to `LEVEL`.

    Measured on one fixed phrase in the middle of the staff, so it is the same
    for every piece and every process; the phrase is cached like any other.
    """
    key = (singer.stamp, speaker)
    if key not in _trims:
        from .vocal import Sung
        notes = [Sung(0.5 * i, 0.5 * i + 0.5, p, 127, ("l",), "aa", ())
                 for i, p in enumerate((60.0, 64.0, 67.0, 64.0))]
        sig, _ = render_phrase(notes, singer, 0, speaker=speaker)
        loud = sig[np.abs(sig) > np.abs(sig).max() * 0.1]
        rms = float(np.sqrt(np.mean(loud ** 2))) if len(loud) else 0.0
        _trims[key] = LEVEL / rms if rms > 1e-6 else 1.0
    return _trims[key]


def _fingerprint(folder: Path) -> str:
    """Every file under a folder, by path, size and modification time. A
    rendered phrase depends on all of a bank -- the duration, pitch and
    variance models, the dictionaries, the speaker embeddings, the vocoder --
    so the cache must change when any of them does, not only the acoustic
    model. Stats only: hashing half a gigabyte per render would cost more
    than the cache saves."""
    h = hashlib.sha256()
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.name != "SOURCE.txt":
            st = p.stat()
            h.update(f"{p.relative_to(folder).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()[:16]


def load(name: str) -> Singer:
    key = _clean(name)
    # Reloaded when the files change: another process may have reinstalled the
    # bank, and a singer kept from before would go on reading the old one.
    mark = _fingerprint(singer_dir(key))
    hit = _singers.get(key)
    if hit is None or hit[0] != mark:
        hit = _singers[key] = (mark, Singer(key))
    return hit[1]


# --------------------------------------------------------------------------
# one phrase
# --------------------------------------------------------------------------

@dataclass
class Phone:
    symbol: str
    vowel: bool = False
    #: Seconds; filled in by `time_phones`.
    start: float = 0.0
    end: float = 0.0
    pitch: float = 60.0


@dataclass
class Group:
    """What the models call a word: everything from one vowel's start up to the
    next one's, so a syllable's opening consonants sit at the end of the group
    *before* it. That is what puts the vowel, not the consonant, on the beat."""

    start: float
    pitch: float
    phones: list[Phone] = field(default_factory=list)


def _frames(durations_ms: list[float], frame_ms: float) -> list[int]:
    """Lengths in whole frames whose running total never drifts from the times."""
    out, acc, prev = [], 0.0, 0
    for d in durations_ms:
        acc += max(0.0, d)
        at = int(round(acc / frame_ms + 0.5))
        out.append(at - prev)
        prev = at
    return out


#: A bank's spelling may differ from the studio's in these ways and still be
#: the same word sung to the same notes: a vowel for a vowel (a reduced one,
#: usually), and a flap for the t or d it is.
_BANK_VOWELS = {"aa", "ae", "ah", "ao", "aw", "ax", "ay", "eh", "er", "ey", "ih", "iy",
                "ow", "oy", "uh", "uw"}
_SAME = {"dx": {"t", "d"}, "_r": {"r"}}


def _spell(sung, singer, lang: str) -> list[tuple[list[str], list[str], list[str]]]:
    """Every note's ``(onset, nucleus, coda)`` in the bank's symbols.

    Starts from the studio's phonemes. Where a note belongs to a word the
    bank's dictionary knows, and that spelling lines up with the written
    syllables sound for sound, the bank's spelling is used instead.
    """
    from .lyrics import VOWELS
    out = [([x for c in s.onset for x in singer.symbols(c, lang)],
            [] if s.hold and i else singer.symbols(s.nucleus, lang) or singer.symbols("ah", lang),
            [x for c in s.coda for x in singer.symbols(c, lang)])
           for i, s in enumerate(sung)]
    lookup = getattr(singer, "pronounce", None)
    if lookup is None:
        return out
    i = 0
    while i < len(sung):
        name, _, where = sung[i].word.partition("#")
        index, _, count = where.partition("/")
        if not name or sung[i].hold or int(index or 0) != 0:
            i += 1
            continue
        # The word's notes: its syllables, and any melisma sung inside them.
        j, seen = i, 0
        while j < len(sung) and (sung[j].hold or seen < int(count or 1)):
            if not sung[j].hold:
                if not sung[j].word.startswith(name + "#"):
                    break
                seen += 1
            j += 1
        theirs = lookup(name, lang) if seen == int(count or 1) else None
        slots = [(k, part, n) for k in range(i, j)
                 for part, phones in ((0, sung[k].onset), (1, () if sung[k].hold else (sung[k].nucleus,)),
                                      (2, sung[k].coda))
                 for n in range(len(phones))]
        ours = [(sung[k].onset, (sung[k].nucleus,), sung[k].coda)[part][n] for k, part, n in slots]
        if theirs and len(theirs) == len(ours) and all(
                t in singer.acoustic.tokens and (
                    t.split("/")[-1] == o
                    or (o in VOWELS and part == 1 and t.split("/")[-1] in _BANK_VOWELS)
                    or o in _SAME.get(t.split("/")[-1], ()))
                for t, o, (_, part, _n) in zip(theirs, ours, slots)):
            fresh: dict[tuple[int, int], list[str]] = {}
            for t, (k, part, _n) in zip(theirs, slots):
                fresh.setdefault((k, part), []).append(t)
            for (k, part), symbols in fresh.items():
                out[k][part][:] = symbols
        i = max(j, i + 1)
    return out


def group_phrase(sung, singer: Singer, lang: str = "en") -> tuple[list[Group], float]:
    """The phrase as groups, and the time it ends. ``groups[0]`` is the silence
    before the first note, holding that note's opening consonants."""
    first = sung[0]
    groups = [Group(first.start - LEAD_MS / 1000.0, float(first.pitch), [Phone("SP")])]
    spelled = _spell(sung, singer, lang)
    for i, (s, (onset, nucleus, coda)) in enumerate(zip(sung, spelled)):
        if i and s.start - sung[i - 1].end >= REST:
            groups.append(Group(sung[i - 1].end, float(sung[i - 1].pitch), [Phone("SP")]))
        if s.hold and i and groups[-1].phones[-1].symbol != "SP":
            # A melisma is a new note, not a new group: the vowel carries on.
            pass
        else:
            groups[-1].phones += [Phone(x) for x in onset]
            if not nucleus:
                nucleus = singer.symbols(s.nucleus, lang) or singer.symbols("ah", lang)
            if not nucleus:
                raise ValueError(f"the singer {singer.name!r} has no phoneme for "
                                 f"{s.nucleus!r} and nothing to stand in for it")
            groups.append(Group(s.start, float(s.pitch),
                                [Phone(nucleus[0], vowel=True)]
                                + [Phone(x) for x in nucleus[1:]]))
        groups[-1].phones += [Phone(x) for x in coda]
    return groups, sung[-1].end


def time_phones(groups: list[Group], end: float, singer: Singer, seed: int) -> list[Phone]:
    """Give every phoneme its place in time.

    The duration model says how long each one wants to be; each group is then
    scaled to fill exactly the time from its own start to the next group's, so
    vowels begin where the score says. The consonants that open the phrase keep
    their predicted length and finish on the first note.
    """
    starts = [g.start for g in groups] + [end]
    flat = [p for g in groups for p in g.phones]
    counts = [len(g.phones) for g in groups]
    dur = singer.dur
    if dur is not None:
        fm = dur.frame_ms
        tokens = np.array([[dur.tokens.get(p.symbol, dur.tokens.get("SP", 0)) for p in flat]])
        word_div = np.array([counts])
        word_dur = np.array([[max(1, int(b * 1000 / fm) - int(a * 1000 / fm))
                              for a, b in zip(starts, starts[1:])]])
        feeds = {"tokens": tokens, "word_div": word_div, "word_dur": word_dur,
                 "languages": np.array([[dur.lang_id(p.symbol) for p in flat]])}
        lin = singer.run(dur.path("linguistic"), feeds, seed)
        feeds = dict(lin)
        feeds.update(ph_midi=np.array([[int(round(g.pitch)) for g in groups for _ in g.phones]]),
                     word_div=word_div, word_dur=word_dur)
        if dur.speakers:
            feeds["spk_embed"] = dur.embed("", len(flat))
        want = singer.inputs(dur.path("dur"))
        out = singer.run(dur.path("dur"), {k: v for k, v in feeds.items() if k in want}, seed)
        lengths = [max(0.0, float(x)) * fm / 1000.0 for x in next(iter(out.values())).reshape(-1)]
    else:
        # No duration model: a consonant is 70 ms, a vowel takes what is left.
        lengths = []
        for g, a, b in zip(groups, starts, starts[1:]):
            cons = sum(1 for p in g.phones if not p.vowel and p.symbol != "SP")
            c = min(0.07, 0.4 * (b - a) / max(1, cons))
            lengths += [c if (not p.vowel and p.symbol != "SP") else
                        max(0.02, (b - a) - c * cons) for p in g.phones]
    k = 0
    for gi, g in enumerate(groups):
        mine = lengths[k:k + len(g.phones)]
        k += len(g.phones)
        span_end = starts[gi + 1]
        if gi == 0:
            # Silence, then the opening consonants at their own length.
            at = span_end - sum(mine[1:])
            g.phones[0].start, g.phones[0].end = at, at          # the head rest is implicit
            for p, d in zip(g.phones[1:], mine[1:]):
                p.start, p.end = at, at + d
                at += d
            continue
        total = sum(mine) or 1.0
        ratio = (span_end - g.start) / total
        at = g.start
        for p, d in zip(g.phones, mine):
            p.start, p.end = at, at + d * ratio
            at = p.end
    out = [p for g in groups for p in g.phones][1:]      # drop the leading silence
    for g in groups:
        for p in g.phones:
            p.pitch = g.pitch
    return [p for p in out if p.end - p.start > 1e-6 or p.symbol != "SP"]


def _segments(phones: list[Phone], frame_ms: float) -> tuple[list[str], list[int], float]:
    """Symbols and frame counts for a model: silence, the phones, silence.
    Returns them with the time (seconds) of frame 0."""
    symbols = ["SP"] + [p.symbol for p in phones] + ["SP"]
    ms = [HEAD * frame_ms] + [(p.end - p.start) * 1000.0 for p in phones] + [TAIL * frame_ms]
    return symbols, _frames(ms, frame_ms), phones[0].start - HEAD * frame_ms / 1000.0


def _sampling(model: _Model, names: set[str], steps: int, depth: float | None) -> dict:
    feeds: dict = {}
    if model.cfg.get("use_continuous_acceleration") or "steps" in names:
        feeds["steps"] = np.int64(steps)
        if "depth" in names:
            feeds["depth"] = np.float32(1.0 if depth is None else depth)
    else:
        speedup = max(1, 1000 // max(1, steps))
        while 1000 % speedup and speedup > 1:
            speedup -= 1
        feeds["speedup"] = np.int64(speedup)
        if "depth" in names:
            d = int(round((1.0 if depth is None else depth) * 1000))
            feeds["depth"] = np.int64(d // speedup * speedup)
    return feeds


def _pitch_curve(singer: Singer, sung, phones, seed: int, expression: float
                 ) -> tuple["np.ndarray", float, float]:
    """The sung pitch in semitones, per frame: ``(curve, frame_ms, start)``."""
    m = singer.pitch
    fm = (m or singer.acoustic).frame_ms
    symbols, ph_dur, start = _segments(phones, fm)
    T = int(sum(ph_dur))
    t = start + np.arange(T) * fm / 1000.0
    if m is None:
        # No pitch model: the notes, with a short curve from each to the next.
        curve = np.full(T, float(sung[0].pitch))
        for a, b in zip(sung, sung[1:]):
            lo, hi = b.start - 0.055, b.start + 0.035
            curve[t >= hi] = b.pitch
            mid = (t >= lo) & (t < hi)
            x = (t[mid] - lo) / (hi - lo)
            curve[mid] = a.pitch + (b.pitch - a.pitch) * (0.5 - 0.5 * np.cos(np.pi * x))
        return curve, fm, start
    feeds = {"tokens": np.array([[m.tokens.get(s, m.tokens.get("SP", 0)) for s in symbols]]),
             "languages": np.array([[m.lang_id(s) for s in symbols]]),
             "ph_dur": np.array([ph_dur])}
    lin_names = singer.inputs(m.path("linguistic"))
    if "word_div" in lin_names:
        vowels = [i + 1 for i, p in enumerate(phones) if p.vowel] or [len(symbols) - 2]
        div = [vowels[0]] + [b - a for a, b in zip(vowels, vowels[1:])] + [len(symbols) - vowels[-1]]
        dur, at = [], 0
        for n in div:
            dur.append(int(sum(ph_dur[at:at + n])))
            at += n
        feeds.update(word_div=np.array([div]), word_dur=np.array([dur]))
    lin = singer.run(m.path("linguistic"), {k: v for k, v in feeds.items() if k in lin_names}, seed)
    # The notes as the model wants them: rests before, between and after.
    ms, midi, rest = [(sung[0].start - start) * 1000.0], [float(sung[0].pitch)], [True]
    prev = sung[0].start
    for s in sung:
        if s.start - prev > 1e-4:
            ms.append((s.start - prev) * 1000.0)
            midi.append(float(s.pitch))
            rest.append(True)
        ms.append((s.end - s.start) * 1000.0)
        midi.append(float(s.pitch))
        rest.append(False)
        prev = s.end
    ms.append(TAIL * fm)
    midi.append(float(sung[-1].pitch))
    rest.append(True)
    # A rest takes the pitch of the nearer note, so the curve has nowhere to fall to.
    for i, r in enumerate(rest):
        if r:
            left = next((midi[j] for j in range(i - 1, -1, -1) if not rest[j]), None)
            right = next((midi[j] for j in range(i + 1, len(rest)) if not rest[j]), None)
            midi[i] = right if left is None else left
    note_dur = _frames(ms, fm)
    note_dur[-1] += T - sum(note_dur)
    if note_dur[-1] < 0:
        short, note_dur[-1] = -note_dur[-1], 0
        for i in range(len(note_dur) - 2, -1, -1):
            take = min(note_dur[i], short)
            note_dur[i] -= take
            short -= take
    names = singer.inputs(m.path("pitch"))
    feeds = {"encoder_out": lin["encoder_out"], "ph_dur": np.array([ph_dur]),
             "note_midi": np.array([midi], np.float32), "note_dur": np.array([note_dur]),
             "note_rest": np.array([rest]), "pitch": np.full((1, T), 60.0, np.float32),
             "retake": np.ones((1, T), bool),
             "expr": np.full((1, T), max(0.0, min(1.0, expression)), np.float32)}
    feeds.update(_sampling(m, names, PITCH_STEPS, None))
    if m.speakers:
        feeds["spk_embed"] = m.embed("", T)
    out = singer.run(m.path("pitch"), {k: v for k, v in feeds.items() if k in names}, seed)
    curve = next(iter(out.values())).reshape(-1)[:T].astype(np.float64)
    return _land(curve, t, sung), fm, start


def _land(curve: "np.ndarray", t: "np.ndarray", sung) -> "np.ndarray":
    """Bring each note the model sang off-pitch back to the written note.

    The pitch model sings a fast note the way a singer under-rehearsed would:
    it glides toward it and is gone before it arrives, a semitone or more flat
    on a sixteenth that leaps up. The note is the studio's to decide, so each
    note's middle is measured and the part of its error beyond `PITCH_SLACK`
    is taken out -- as one offset per note, blended into its neighbours', which
    moves the note and leaves the model's vibrato, scoops and slides as they
    were. A note sung within the slack is not touched at all.
    """
    if PITCH_PULL <= 0 or not len(curve):
        return curve
    at, off = [], []
    for s in sung:
        d = s.end - s.start
        core = (t >= s.start + 0.3 * d) & (t < s.end - 0.1 * d)
        if not core.any():
            core = (t >= s.start) & (t < s.end)
        if not core.any():
            continue
        err = float(np.median(curve[core])) - float(s.pitch)
        fix = -math.copysign(max(0.0, abs(err) - PITCH_SLACK), err) * PITCH_PULL
        # Held across the note's middle, so the whole note moves together and
        # only the joins between notes are blended.
        at += [s.start + 0.3 * d, s.end - 0.1 * d]
        off += [fix, fix]
    if not at or not any(off):
        return curve
    return curve + np.interp(t, at, off)


def _variances(singer: Singer, phones, midi, start, fm_ac, seed: int, speaker: str) -> dict:
    """Breathiness, voicing and whatever else the acoustic model wants told."""
    m = singer.variance
    if m is None:
        return {}
    fm = m.frame_ms
    symbols, ph_dur, v_start = _segments(phones, fm)
    T = int(sum(ph_dur))
    t = v_start + np.arange(T) * fm / 1000.0
    pitch = np.interp(t, start + np.arange(len(midi)) * fm_ac / 1000.0, midi).astype(np.float32)
    feeds = {"tokens": np.array([[m.tokens.get(s, m.tokens.get("SP", 0)) for s in symbols]]),
             "languages": np.array([[m.lang_id(s) for s in symbols]]),
             "ph_dur": np.array([ph_dur])}
    lin_names = singer.inputs(m.path("linguistic"))
    if "word_div" in lin_names:
        vowels = [i + 1 for i, p in enumerate(phones) if p.vowel] or [len(symbols) - 2]
        div = [vowels[0]] + [b - a for a, b in zip(vowels, vowels[1:])] + [len(symbols) - vowels[-1]]
        dur, at = [], 0
        for n in div:
            dur.append(int(sum(ph_dur[at:at + n])))
            at += n
        feeds.update(word_div=np.array([div]), word_dur=np.array([dur]))
    lin = singer.run(m.path("linguistic"), {k: v for k, v in feeds.items() if k in lin_names}, seed)
    names = singer.inputs(m.path("variance"))
    kinds = [v for v in ("energy", "breathiness", "voicing", "tension") if v in names]
    feeds = {"encoder_out": lin["encoder_out"], "ph_dur": np.array([ph_dur]),
             "pitch": pitch[None, :], "retake": np.ones((1, T, len(kinds)), bool)}
    for v in kinds:
        feeds[v] = np.zeros((1, T), np.float32)
    feeds.update(_sampling(m, names, STEPS, None))
    if m.speakers:
        feeds["spk_embed"] = m.embed(speaker, T)
    out = singer.run(m.path("variance"), {k: v for k, v in feeds.items() if k in names}, seed)
    n = len(midi)
    res = {}
    for v in kinds:
        arr = out.get(f"{v}_pred")
        if arr is not None:
            arr = arr.reshape(-1)
            res[v] = np.interp(np.arange(n) * fm_ac, np.arange(len(arr)) * fm, arr).astype(np.float32)
    return res


def render_phrase(sung, singer: Singer, seed: int, *, speaker: str = "", lang: str = "en",
                  expression: float = 1.0, steps: int = STEPS,
                  breath: float = 0.0, tone: dict | None = None) -> tuple["np.ndarray", float]:
    """Sing one phrase. Returns ``(samples at 44.1 kHz, start time in seconds)``.
    ``breath`` is how long an intake to sing before the first sound (seconds;
    0 for none, and none if the bank has no breath phoneme)."""
    if singer.vocoder_path is None:
        raise FileNotFoundError(
            f"the singer {singer.name!r} needs the vocoder {singer.vocoder_name!r}, "
            f"which is not installed")
    key = hashlib.sha256(json.dumps(
        [ENGINE, singer.stamp, speaker, lang, expression, steps, seed, LEAD_MS, REST,
         round(float(breath), 3), sorted((tone or {}).items()),
         [(round(s.start - sung[0].start, 5), round(s.end - sung[0].start, 5),
           round(float(s.pitch), 4), list(s.onset), s.nucleus, list(s.coda), bool(s.hold),
           s.word) for s in sung]]).encode()).hexdigest()[:40]
    cached = CACHE_DIR.expanduser() / f"{key}.npz"
    if cached.is_file():
        try:
            with np.load(cached) as z:
                return z["x"].astype(np.float64), sung[0].start + float(z["lead"])
        except Exception:                                 # a damaged entry is re-rendered
            pass

    tone = tone or {}
    groups, end = group_phrase(sung, singer, lang)
    phones = time_phones(groups, end, singer, seed)
    ac = singer.acoustic
    fm = ac.frame_ms
    if breath > 0.05 and "AP" in ac.tokens and phones:
        # The breath ends where the first consonant begins: it borrows from the
        # silence before the phrase and moves nothing that is written.
        air = Phone("AP")
        air.start, air.end = phones[0].start - breath, phones[0].start
        air.pitch = phones[0].pitch
        phones = [air] + phones
    symbols, durations, start = _segments(phones, fm)
    T = int(sum(durations))
    t = start + np.arange(T) * fm / 1000.0

    p_curve, p_fm, p_start = _pitch_curve(singer, sung, phones, seed, expression)
    midi = np.interp(t, p_start + np.arange(len(p_curve)) * p_fm / 1000.0, p_curve)
    f0 = (440.0 * 2.0 ** ((midi - 69.0) / 12.0)).astype(np.float32)

    path = ac.path("acoustic")
    names = singer.inputs(path)
    cfg = ac.cfg
    depth = None
    if cfg.get("use_variable_depth", cfg.get("use_shallow_diffusion")):
        md = float(cfg.get("max_depth") or 0)
        md = md if cfg.get("use_continuous_acceleration") else md / 1000.0
        depth = min(1.0, md) if md > 0 else 1.0
    feeds = {"tokens": np.array([[ac.tokens.get(s, ac.tokens.get("SP", 0)) for s in symbols]]),
             "languages": np.array([[ac.lang_id(s) for s in symbols]]),
             "durations": np.array([durations]), "f0": f0[None, :],
             "gender": np.full((1, T), max(-1.0, min(1.0, singer.gender
                                                     + float(tone.get("gender", 0.0)))),
                               np.float32),
             "velocity": np.full((1, T), max(0.5, min(2.0, float(tone.get("crisp", 1.0)))),
                                 np.float32)}
    feeds.update(_sampling(ac, names, steps, depth))
    if ac.speakers:
        feeds["spk_embed"] = ac.embed(speaker, T)
    wanted = [v for v in ("energy", "breathiness", "voicing", "tension") if v in names]
    if wanted:
        pred = _variances(singer, phones, midi, start, fm, seed, speaker)
        for v in wanted:
            if v not in pred:
                raise RuntimeError(f"the singer {singer.name!r} needs a {v} curve and has "
                                   f"no variance model that predicts one")
            lo, hi = (-10.0, 10.0) if v == "tension" else (-96.0, 0.0)
            # The bank predicts these curves; a `tone` op leans on them.
            lean = float(tone.get({"breathiness": "breath", "voicing": "firm"}.get(v, ""), 0.0))
            feeds[v] = np.clip(pred[v] + lean, lo, hi)[None, :]
    mel = next(iter(singer.run(path, {k: v for k, v in feeds.items() if k in names},
                               seed).values())).astype(np.float32)
    # An acoustic model that writes log10 mels into a vocoder that reads ln.
    if str(cfg.get("mel_base", "10")) != str(singer.vocoder_cfg.get("mel_base", "10")):
        mel = mel * np.float32(math.log(10) if str(cfg.get("mel_base", "10")) == "10"
                               else 1 / math.log(10))
    wav = next(iter(singer.run(singer.vocoder_path, {"mel": mel, "f0": f0[None, :]},
                               seed).values())).reshape(-1).astype(np.float64)
    rate = int(singer.vocoder_cfg.get("sample_rate", SR))
    if rate != SR:
        wav = np.interp(np.arange(int(len(wav) * SR / rate)) * rate / SR, np.arange(len(wav)), wav)
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        # Unique per process: two renders of one phrase must not share a file.
        tmp = cached.with_name(f"{cached.stem}.{os.getpid()}.part.npz")
        np.savez_compressed(tmp, x=wav.astype(np.float32), lead=np.float64(start - sung[0].start))
        tmp.replace(cached)
    except OSError:                                       # a cache is a convenience
        pass
    return wav, start


# --------------------------------------------------------------------------
# joining the mix
# --------------------------------------------------------------------------

def voice_stems(piece, notes, to_sec, total: int, pans: dict[str, float], *,
                strict: bool = False) -> dict[str, tuple]:
    """``{voice: (left, right)}`` for every singer whose ``bank`` is a neural
    singer that can be run here. The others are left to the engines below."""
    import warnings
    from .vocal import SINGERS, phrases, plan
    out: dict[str, tuple] = {}
    for v in piece.voices:
        if v.muted or not v.bank or v.instrument not in SINGERS or not knows(v.bank):
            continue
        mine = [n for n in notes if n.voice == v.name and not n.percussive]
        if not mine:
            continue
        name, speaker = parse_bank(v.bank)
        name = name.lower()
        if strict and not (is_installed(name) and available()):
            raise RuntimeError(f"voice {v.name!r}: the neural singer {name!r} "
                               f"cannot be run here (not installed, or the "
                               f"`neural` extra is missing)")
        if not is_installed(name):
            warnings.warn(f"voice {v.name!r} falls back to the synthesized singer: the "
                          f"neural singer {name!r} is not installed. See SINGERS.md, "
                          f"or run `ms singer show {name}`.", stacklevel=2)
            continue
        if not available():
            warnings.warn(f"voice {v.name!r} falls back to the synthesized singer: "
                          f"neural singers need `uv sync --extra neural` "
                          f"(numpy, onnxruntime, pyyaml).", stacklevel=2)
            continue
        try:
            singer = load(name)
            if singer.vocoder_path is None:
                raise FileNotFoundError(f"its vocoder {singer.vocoder_name!r} is not installed")
            mono = np.zeros(total)
            level = trim(singer, speaker)
            before = None
            tone = {}
            for op in v.ops:
                if op.kind == "tone" and op.enabled:
                    tone = {k: float(op.params[k]) for k in ("breath", "firm", "crisp", "gender")
                            if op.params.get(k) is not None}
            for group in phrases(plan(mine, to_sec)):
                seed = zlib.crc32(f"{v.name}|{group[0].start:.4f}|{group[0].pitch}".encode())
                # Room to breathe: all of it before the first line, and after
                # that only what the last line left, less its own release.
                room = BREATH if before is None else 0.6 * (group[0].start - before)
                before = group[-1].end
                sig, t0 = render_phrase(group, singer, seed, speaker=speaker,
                                        breath=min(BREATH, room) if room >= 0.15 else 0.0,
                                        tone=tone)
                # Loudness follows the written dynamics, a note at a time.
                gain = np.ones(len(sig))
                for s in group:
                    a = max(0, int((s.start - t0 - 0.03) * SR))
                    gain[a:] = (max(1, min(127, s.velocity)) / 127.0) ** 1.2
                k = max(1, int(0.03 * SR))
                gain = np.convolve(np.pad(gain, (k, k), mode="edge"),
                                   np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
                sig = sig * gain * level
                a = int(round(t0 * SR))
                if a < 0:
                    sig, a = sig[-a:], 0
                n = min(len(sig), total - a)
                if n > 0:
                    mono[a:a + n] += sig[:n]
        except Exception as exc:
            if strict:
                raise
            warnings.warn(f"voice {v.name!r} falls back to the synthesized singer: "
                          f"the neural singer {name!r} could not be run ({exc}).",
                          stacklevel=2)
            continue
        theta = (max(-1.0, min(1.0, pans.get(v.name, 0.0))) + 1.0) * math.pi / 4
        out[v.name] = (mono * math.cos(theta) * math.sqrt(2),
                       mono * math.sin(theta) * math.sqrt(2))
    return out
