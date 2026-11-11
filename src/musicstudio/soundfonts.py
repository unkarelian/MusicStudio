"""Fetching a SoundFont, for the sampled render.

A General MIDI bank is tens of megabytes of recordings, which is not something
to commit to a repository or ship in a wheel that most people install for the
built-in render. So the bank is downloaded once, on request, into the per-user
directory ``audio.find_soundfont`` already looks in -- after which
``ms wav <piece> --soundfont`` needs no path.

Two rules, because this is the one place the studio runs something off the
network. **Every download is pinned by SHA-256**, checked before a byte is
unpacked, and a bank given by URL must come with its own hash. And **the
licence travels with the bank**: these are MIT-licensed recordings whose
licence asks to be reproduced alongside copies, so it is written next to the
file rather than left on a server.

Pure standard library: ``urllib`` to fetch, ``tarfile`` to unpack.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

#: Under the install directory: banks for particular instruments (``Bank.extra``).
EXTRA_DIR = "musicstudio-extra"

#: Where banks are installed. Per-user, no privileges needed, and first in
#: ``audio.SOUNDFONT_DIRS``.
INSTALL_DIR = Path("~/.local/share/soundfonts")


@dataclass(frozen=True)
class Bank:
    name: str
    summary: str
    url: str
    sha256: str
    #: Megabytes fetched, for telling the user what they are about to download.
    size_mb: int
    #: File name it is installed under.
    filename: str
    #: For a Debian package: the member to take out of ``data.tar``.
    member: str | None = None
    #: The licence, as a member of the same package or as its own URL.
    license_member: str | None = None
    license_url: str | None = None
    license_sha256: str | None = None
    #: How the download is packed, when it is not the bank itself or a Debian
    #: package: ``"tar"`` (any compression ``tarfile`` reads), ``"zip"``, or
    #: ``"7z"``, which the standard library cannot read and so needs ``7z``
    #: (p7zip) or ``bsdtar`` on PATH.
    archive: str | None = None
    #: A bank for particular instruments rather than a General MIDI set. It is
    #: installed one directory down, where ``audio.find_soundfont`` does not
    #: look, so it can never be mistaken for the bank a whole piece is played
    #: through; an instrument asks for it by name (``Instrument.font``).
    extra: bool = False
    #: What the licence asks, in a sentence, for `ms soundfont banks`.
    terms: str = ""


#: The standard bank's hash was taken from the mirror itself (there is no
#: published one), so it pins the file against changing, not against the mirror.
#: MuseScore never published the HQ bank as a plain file -- it shipped through
#: the MuseScore 3 extension server, which no longer serves it. Debian
#: redistributes the same bank as a package, so that is where it comes from; the
#: hash is the one in Debian's own package index.
BANKS: dict[str, Bank] = {b.name: b for b in [
    Bank("hq",
         "MuseScore General HQ 0.2.1 -- the full bank, with separate solo and "
         "ensemble samples. MIT. The best-sounding option here.",
         "https://deb.debian.org/debian/pool/main/m/musescore-general-soundfont/"
         "musescore-general-soundfont_0.2.1-1_all.deb",
         "21ab87e4b15711817f84130a370bdb51003c90f3bf53e4015f3b410b9ed8c6a5",
         73, "MuseScore_General_HQ.sf3",
         member="usr/share/sounds/sf3/MuseScore_General_Full.sf3",
         license_member="usr/share/doc/musescore-general-soundfont/copyright"),
    Bank("standard",
         "MuseScore General 0.2 -- the scaled-down bank MuseScore ships by "
         "default. MIT. Half the download, lighter instruments.",
         "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/"
         "MuseScore_General.sf3",
         "5b85b6c2c61d10b2b91cddd41efcce7b25cd31c8271d511c73afafbef20b6fa3",
         38, "MuseScore_General.sf3",
         license_url="https://ftp.osuosl.org/pub/musescore/soundfont/"
                     "MuseScore_General/MuseScore_General_License.md",
         license_sha256="5ad8d737e13c7f01f5b9674872a82a92b4ba253603e8ed14b9db12293550b4b9"),
]}
DEFAULT_BANK = "hq"

_CC0 = "CC0: nothing asked."
_FP = "https://github.com/freepats/"
_FPZ = "https://freepats.zenvoid.org/"
_VD = "https://raw.githubusercontent.com/FluidSynth/fluidsynth/v2.6.2/sf2/"

#: Banks for particular things. Each was fetched, hashed, unpacked and its
#: licence read before it was listed here; `SOUNDFONTS.md` says where each
#: comes from and what it asks. Instruments in ``ensemble`` name these by key.
BANKS.update({b.name: b for b in [
    Bank("fluidr3",
         "FluidR3 GM -- a second General MIDI bank with another character "
         "(bigger drums, rougher guitars). Any voice can ask for it: "
         "bank=\"fluidr3\".",
         "https://snapshot.debian.org/file/9cf2ecd68b96de93f048708ea52728eca171f692",
         "6f531493ac4e4d9772fd96b2488ea1790af81c196135fbdd25997da0781fc60e",
         120, "FluidR3_GM.sf2", member="usr/share/sounds/sf2/FluidR3_GM.sf2",
         license_member="usr/share/doc/fluid-soundfont-gm/copyright", extra=True,
         terms="MIT (Frank Wen, Toby Smithe): keep the notice."),
    Bank("opl3",
         "OPL-3 FM 128M -- the two-operator FM chip of DOS games, as a whole "
         "General MIDI set. bank=\"opl3\" on any voice.",
         "https://snapshot.debian.org/file/53fc514eabe203d192d22111c6ec9ac608223b38",
         "d0534cc07a536e1cfa05b1d0c0befb8586840c8d0e163ef24c536ca1bb5c9aff",
         100, "OPL-3_FM_128M.sf2", member="usr/share/sounds/sf2/OPL-3_FM_128M.sf2",
         license_member="usr/share/doc/opl3-soundfont/copyright", extra=True,
         terms="CC-BY-SA 4.0 (Zandro Reveille): credit, and share alike."),
    Bank("vintage",
         "Vintage Dreams Waves 2.0 -- 128 analog and FM synth presets and "
         "eight drum machines (808, 909, CR-78) in a third of a megabyte.",
         _VD + "VintageDreamsWaves-v2.sf2",
         "52132b2b83994f0067d3a66b93b4f1b67d53ff8c0d3be90d39f23f92b4585cdd",
         1, "VintageDreamsWaves-v2.sf2", license_url=_VD + "COPYRIGHT.txt",
         license_sha256="766f8b6f5716dae672ab3cab74c3d6e3ad452beb49cfef81c82b79970c2601d6",
         extra=True,
         terms="Freeware (Ian Wilson): free to use and pass on unaltered, with "
               "its copyright notice. Do not convert or edit the file."),
    Bank("chip8",
         "Open8bitVChiptuner -- four raw chip waves: noise, sine, saw, square.",
         "https://github.com/trzyglow/Open8bitVChiptuner/releases/download/1.0/"
         "release-1.0.zip",
         "e3c00f67ed8c34e34019473142a239d033973fe896a685b47742726cd76f0f0d",
         1, "Open8bitVChiptuner.sf2", archive="zip", member="Open8bitVChiptuner.sf2",
         license_url="https://raw.githubusercontent.com/trzyglow/Open8bitVChiptuner/"
                     "0a71d41de11c75a187d1ddf3fcba0c1c1edfe5b6/LICENSE.md",
         license_sha256="5e35b27531a7d02fdca18fb9a95ee05c16cd309dbe96df1848eff95edac4977f",
         extra=True, terms="CC-BY-SA 4.0 (Timo Heidutzek): credit, and share alike."),
    Bank("guitar_dist",
         "FreePats electric guitar FSBS, distorted (bridge pickup, a real amp "
         "and rack). 127 MB to fetch, 390 MB on disk.",
         _FP + "electric-guitar-FSBS-dist2/releases/download/2022-09-11/"
               "EGuitarFSBS-dist2-SF2-20220911.7z",
         "0ed99135d955940c1200e09ca9e36e261dfebbe8767ae58da6f298fe29fdd146",
         127, "EGuitarFSBS-dist2.sf2", archive="7z",
         member="EGuitarFSBS-dist2 SF2-20220911/EGuitarFSBS-dist2 bridge 20220911.sf2",
         license_member="EGuitarFSBS-dist2 SF2-20220911/LICENSE.txt", extra=True,
         terms=_CC0),
    Bank("guitar_clean",
         "FreePats electric guitar FSBS, clean, bridge pickup (the small set).",
         _FP + "electric-guitar-FSBS-clean/releases/download/2026-08-07/"
               "EGuitarFSBS-clean-bridge-small-SF2-20260807.7z",
         "bcea7d4c92a1cc6a26e545a218b34e59037d4bab6cf0fce24396428e6934d69c",
         7, "EGuitarFSBS-clean-small.sf2", archive="7z",
         member="EGuitarFSBS-clean bridge small SF2-20260807/"
                "EGuitarFSBS-clean bridge small 20260807.sf2",
         license_member="EGuitarFSBS-clean bridge small SF2-20260807/LICENSE.txt",
         extra=True, terms=_CC0),
    Bank("guitar_nylon",
         "FreePats Spanish classical guitar -- one nylon-strung guitar, recorded "
         "note by note in 2008.",
         _FPZ + "Guitar/SpanishClassicalGuitar/SpanishClassicalGuitar-SF2-20190618.7z",
         "8c192f1fc640a553199a4a43a17ae12354a6a05e3d6aad79bd43b5d29314ff51",
         10, "SpanishClassicalGuitar.sf2", archive="7z",
         member="SpanishClassicalGuitar-SF2-20190618/SpanishClassicalGuitar-20190618.sf2",
         license_member="SpanishClassicalGuitar-SF2-20190618/cc0.txt", extra=True,
         terms=_CC0),
    Bank("bass_picked",
         "FreePats electric bass YR, played with a pick.",
         _FP + "electric-bass-YR/releases/download/2019-09-30/PickedBassYR-SF2-20190930.7z",
         "e6bff767c352cd27de2de8cfff326d0849a76bb38d876075eecd5ffd2dc5afd0",
         3, "PickedBassYR.sf2", archive="7z",
         member="PickedBassYR SF2-20190930/PickedBassYR 20190930.sf2",
         license_member="PickedBassYR SF2-20190930/LICENSE.txt", extra=True, terms=_CC0),
    Bank("bass_finger",
         "FreePats electric bass YR, fingered.",
         _FP + "electric-bass-YR/releases/download/2019-09-30/FingerBassYR-SF2-20190930.7z",
         "f5b5cfe04435a9e9037d1f97d515dc596535acf26637db9579d724cd757f179e",
         3, "FingerBassYR.sf2", archive="7z",
         member="FingerBassYR SF2-20190930/FingerBassYR 20190930.sf2",
         license_member="FingerBassYR SF2-20190930/LICENSE.txt", extra=True, terms=_CC0),
    Bank("muldjord",
         "MuldjordKit -- a recorded rock and metal drum kit: two kicks, four "
         "toms, a china. 55 MB to fetch, 220 MB on disk.",
         _FP + "muldjordkit/releases/download/2020-10-18/MuldjordKit-SF2-20201018.7z",
         "aef4c9e0a96f9a899a7838f65ff07565f6af247bbb4ff31e24dba3331a671a96",
         55, "MuldjordKit.sf2", archive="7z",
         member="MuldjordKit-SF2-20201018/MuldjordKit 20201018.sf2",
         license_member="MuldjordKit-SF2-20201018/LICENSE.txt", extra=True,
         terms="CC-BY 4.0: credit Lars Muldjord (FreePats version by "
               "roberto@zenvoid.org)."),
    Bank("synth_drums",
         "FreePats synthesizer percussion -- an analog-style drum machine, "
         "synthesized, not sampled from one.",
         _FPZ + "Percussion/SynthesizerPercussion/SynthesizerPercussion-SF2-20220718.7z",
         "6ff6580165061eac3113a9961e1e93860c9af87a82b523a49949f099d6f47ea3",
         1, "SynthesizerPercussion.sf2", archive="7z",
         member="SynthesizerPercussion-SF2-20220718/SynthesizerPercussion-20220718.sf2",
         license_member="SynthesizerPercussion-SF2-20220718/LICENSE", extra=True,
         terms=_CC0),
    Bank("lately_bass",
         "FreePats Lately Bass -- the FM bass of late-eighties dance records, "
         "recreated.",
         _FP + "lately-bass/releases/download/2024-04-09/LatelyBass-SF2-20240409.7z",
         "5af4595187632a98e802893de32456beb6f0f865c20258c3ec35ff890b7f995e",
         2, "LatelyBass.sf2", archive="7z",
         member="LatelyBass SF2-20240409/LatelyBass 20240409.sf2",
         license_member="LatelyBass SF2-20240409/LICENSE.txt", extra=True, terms=_CC0),
    Bank("fm_piano",
         "FreePats FM Piano 1 -- a sampled DX-style electric piano.",
         _FP + "fm-piano1/releases/download/2019-09-16/FM-Piano1-SF2-20190916.7z",
         "543774e268e00eaf13968c53d9a42eada7f13564e559d51534ed552507c971ad",
         14, "FM-Piano1.sf2", archive="7z",
         member="FM-Piano1 SF2-20190916/FM-Piano1 20190916.sf2",
         license_member="FM-Piano1 SF2-20190916/LICENSE.txt", extra=True, terms=_CC0),
    Bank("organ_rock",
         "FreePats rock organ -- a tonewheel organ through its rotary speaker.",
         _FPZ + "Organ/RockOrganEmulation/RockOrganEmulation-SF2-20190715.tar.xz",
         "5be252317cc511d0d92e94b07e2289540b57e4381ec34b26392e685f9b1d505d",
         13, "RockOrganEmulation.sf2", archive="tar",
         member="RockOrganEmulation-SF2-20190715/RockOrganEmulation-20190715.sf2",
         license_member="RockOrganEmulation-SF2-20190715/readme.txt", extra=True,
         terms=_CC0),
    Bank("organ_drawbar",
         "FreePats drawbar organ -- the same organ, plain.",
         _FPZ + "Organ/DrawbarOrganEmulation/DrawbarOrganEmulation-SF2-20190712.tar.xz",
         "9b41fa8418f6f1a14924381bc6ccbddbb665bbec2b5f46d4ab549e8d88a2e178",
         6, "DrawbarOrganEmulation.sf2", archive="tar",
         member="DrawbarOrganEmulation-SF2-20190712/DrawbarOrganEmulation-20190712.sf2",
         license_member="DrawbarOrganEmulation-SF2-20190712/readme.txt", extra=True,
         terms=_CC0),
    Bank("piano_ydp",
         "YDP Grand Piano -- a recorded concert grand, many velocity layers.",
         _FPZ + "Piano/YDP-GrandPiano/YDP-GrandPiano-SF2-20160804.tar.bz2",
         "d243dc3e182a60df2a16e92828c1821cf3eb5748b45e2e2bdcfa9cf7af056026",
         37, "YDP-GrandPiano.sf2", archive="tar",
         member="YDP-GrandPiano-SF2-20160804/YDP-GrandPiano-20160804.sf2",
         license_member="YDP-GrandPiano-SF2-20160804/YDP-GrandPiano-20160804.txt",
         extra=True,
         terms="CC-BY 3.0: credit Zenph Studios / the OLPC sample library and "
               "FreePats."),
]})


def _fetch(url: str, sha256: str, progress=None) -> bytes:
    """Download, and refuse the result unless it is exactly what was pinned."""
    req = urllib.request.Request(url, headers={"User-Agent": "musicstudio"})
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        while True:
            block = resp.read(1 << 18)
            if not block:
                break
            chunks.append(block)
            digest.update(block)
            got += len(block)
            if progress:
                progress(got, total)
    if digest.hexdigest() != sha256.lower():
        raise ValueError(
            f"checksum mismatch for {url}: expected {sha256}, got "
            f"{digest.hexdigest()}. Nothing was installed.")
    return b"".join(chunks)


def _fetch_file(url: str, sha256: str, folder: Path, progress=None) -> Path:
    """Download straight to a file in ``folder`` and return its path, for
    archives too large to hold in memory twice over. The same rule as
    ``_fetch``: a file that is not exactly what was pinned is deleted, and
    nothing is returned."""
    req = urllib.request.Request(url, headers={"User-Agent": "musicstudio"})
    digest = hashlib.sha256()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f".download-{os.getpid()}-{sha256[:12]}.part"
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as out:
            total = int(resp.headers.get("Content-Length") or 0)
            got = 0
            while True:
                block = resp.read(1 << 18)
                if not block:
                    break
                out.write(block)
                digest.update(block)
                got += len(block)
                if progress:
                    progress(got, total)
        if digest.hexdigest() != sha256.lower():
            raise ValueError(
                f"checksum mismatch for {url}: expected {sha256}, got "
                f"{digest.hexdigest()}. Nothing was installed.")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _deb_data(deb: bytes) -> tarfile.TarFile:
    """The ``data.tar`` inside a Debian package, which is an ``ar`` archive."""
    if deb[:8] != b"!<arch>\n":
        raise ValueError("not a Debian package (no ar header)")
    at = 8
    while at + 60 <= len(deb):
        header = deb[at:at + 60]
        name = header[:16].decode("ascii", "replace").strip().rstrip("/")
        size = int(header[48:58])
        at += 60
        if name.startswith("data.tar"):
            return tarfile.open(fileobj=io.BytesIO(deb[at:at + size]))
        at += size + (size & 1)
    raise ValueError("Debian package has no data.tar member")


def _member(tar: tarfile.TarFile, path: str) -> bytes:
    for name in (path, "./" + path):
        try:
            f = tar.extractfile(name)
        except KeyError:
            continue
        if f is not None:
            return f.read()
    raise ValueError(f"package does not contain {path}")


def _write(path: Path, data: bytes) -> None:
    """Atomically: a download interrupted half-way must not leave a truncated
    bank where the renderer will find it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.chmod(tmp, 0o644)        # mkstemp makes it private; a bank is not a secret
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _progress(got: int, total: int) -> None:
    if not sys.stderr.isatty():
        return
    mb = got / 1e6
    tail = f" / {total / 1e6:.0f} MB" if total else " MB"
    sys.stderr.write(f"\r  {mb:6.1f}{tail}")
    if total and got >= total:
        sys.stderr.write("\n")
    sys.stderr.flush()


def folder_of(bank: Bank, dest: str | Path | None = None) -> Path:
    base = Path(dest or INSTALL_DIR).expanduser()
    return base / EXTRA_DIR if bank.extra else base


def path_of(name: str, dest: str | Path | None = None) -> Path | None:
    """Where a catalogued bank is installed, or ``None`` if it is not."""
    b = BANKS.get(name)
    if b is None:
        return None
    out = folder_of(b, dest) / b.filename
    return out if out.is_file() else None


def _unpack(raw: bytes, bank: Bank) -> tuple[bytes, bytes | None]:
    """The bank and its licence out of a tar or zip. Members are read by name
    into memory; nothing is extracted to disk, so a hostile path in the
    archive has nowhere to go."""
    if bank.archive == "zip":
        import zipfile
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            def read(path: str) -> bytes:
                try:
                    return z.read(path)
                except KeyError:
                    raise ValueError(f"archive does not contain {path}") from None
            return read(bank.member), (read(bank.license_member)
                                       if bank.license_member else None)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        return _member(tar, bank.member), (_member(tar, bank.license_member)
                                           if bank.license_member else None)


def _seven(archive: Path, member: str, out) -> None:
    """One member of a 7z archive, streamed to ``out``. The standard library
    cannot read the format, so this runs an extractor -- on a file that has
    already been checked against its pinned hash, and only ever to a pipe."""
    for exe, args in (("7z", ["e", "-so", "--"]), ("7za", ["e", "-so", "--"]),
                      ("7zr", ["e", "-so", "--"]), ("bsdtar", ["-xOf"])):
        path = shutil.which(exe)
        if path is None:
            continue
        done = subprocess.run([path, *args, str(archive), member], stdout=out,
                              stderr=subprocess.PIPE)
        if done.returncode != 0:
            raise ValueError(f"{exe} could not read {member!r}: "
                             f"{done.stderr.decode('utf-8', 'replace').strip()[:300]}")
        return
    raise RuntimeError("this bank is packed as 7z, which needs `7z` (p7zip) or "
                       "`bsdtar` on PATH to unpack")


def _install_seven(b: Bank, out: Path, progress) -> None:
    """Fetch to disk, unpack to a file beside the destination, rename. These
    are the large banks: nothing is held in memory."""
    out.parent.mkdir(parents=True, exist_ok=True)
    archive = _fetch_file(b.url, b.sha256, out.parent, progress)
    part = out.with_name(out.name + f".{os.getpid()}.part")
    try:
        with open(part, "wb") as f:
            _seven(archive, b.member, f)
        with open(part, "rb") as f:
            head = f.read(12)
        if head[:4] != b"RIFF" or head[8:12] != b"sfbk":
            raise ValueError(f"{b.url} did not contain a SoundFont")
        if b.license_member:
            with tempfile.TemporaryFile() as lic:
                _seven(archive, b.license_member, lic)
                lic.seek(0)
                _write(out.with_suffix(".LICENSE.txt"), lic.read())
        os.chmod(part, 0o644)
        os.replace(part, out)
    finally:
        part.unlink(missing_ok=True)
        archive.unlink(missing_ok=True)


def installed(dest: str | Path | None = None) -> list[Path]:
    base = Path(dest or INSTALL_DIR).expanduser()
    if not base.is_dir():
        return []
    found = [f for f in base.iterdir() if f.suffix.lower() in (".sf2", ".sf3")]
    extra = base / EXTRA_DIR
    if extra.is_dir():
        found += [f for f in extra.iterdir() if f.suffix.lower() in (".sf2", ".sf3")]
    return sorted(found)


def install(bank: str = DEFAULT_BANK, *, dest: str | Path | None = None,
            url: str | None = None, sha256: str | None = None,
            force: bool = False, quiet: bool = False) -> Path:
    """Download a bank into the per-user SoundFont directory and return its path.

    ``bank`` is a key of :data:`BANKS`. To install anything else, pass ``url``
    and its ``sha256`` -- a hash is required, because a file fetched from an
    arbitrary address and handed to a sampler should be the file you meant.
    """
    base = Path(dest or INSTALL_DIR).expanduser()
    show = None if quiet else _progress
    if url:
        if not sha256:
            raise ValueError("a custom --url needs --sha256, so the download can "
                             "be verified before it is installed")
        name = Path(url.split("?")[0]).name
        if Path(name).suffix.lower() not in (".sf2", ".sf3"):
            raise ValueError(f"{name!r} is not a .sf2 or .sf3 file")
        out = base / name
        if out.is_file() and not force:
            return out
        data = _fetch(url, sha256, show)
        # The same check a listed bank gets: the hash says it is the file that
        # was asked for, not that the file is a SoundFont.
        if data[:4] != b"RIFF" or data[8:12] != b"sfbk":
            raise ValueError(f"{url} is not a SoundFont (no RIFF/sfbk header)")
        _write(out, data)
        return out
    if bank not in BANKS:
        raise KeyError(f"unknown bank {bank!r}; have {sorted(BANKS)}")
    b = BANKS[bank]
    out = folder_of(b, base) / b.filename
    if out.is_file() and not force:
        return out
    if b.archive == "7z":
        _install_seven(b, out, show)
        return out
    raw = _fetch(b.url, b.sha256, show)
    license_text = None
    if b.archive:
        data, license_text = _unpack(raw, b)
    elif b.member:
        tar = _deb_data(raw)
        data = _member(tar, b.member)
        if b.license_member:
            license_text = _member(tar, b.license_member)
            if b.license_member.endswith(".gz"):
                license_text = gzip.decompress(license_text)
    else:
        data = raw
    if b.license_url and b.license_sha256:
        license_text = _fetch(b.license_url, b.license_sha256)
    if data[:4] != b"RIFF" or data[8:12] != b"sfbk":
        raise ValueError(f"{b.url} did not contain a SoundFont")
    if license_text:
        _write(out.with_suffix(".LICENSE.txt"), license_text)
    _write(out, data)
    return out
