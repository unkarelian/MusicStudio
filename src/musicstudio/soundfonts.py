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
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

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


def installed(dest: str | Path | None = None) -> list[Path]:
    base = Path(dest or INSTALL_DIR).expanduser()
    if not base.is_dir():
        return []
    return sorted(f for f in base.iterdir() if f.suffix.lower() in (".sf2", ".sf3"))


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
    out = base / b.filename
    if out.is_file() and not force:
        return out
    raw = _fetch(b.url, b.sha256, show)
    license_text = None
    if b.member:
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
