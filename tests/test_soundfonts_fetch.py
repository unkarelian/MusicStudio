"""The two ways the studio downloads: into memory and straight to a file. Both
must refuse what was not pinned, and the file must not outlive a refusal."""
import hashlib

import pytest

from musicstudio import soundfonts


def test_both_fetches_keep_only_what_was_pinned(tmp_path):
    src = tmp_path / "bank.bin"
    data = bytes(range(256)) * 3000                     # several read blocks
    src.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    seen = []

    assert soundfonts._fetch(src.as_uri(), digest.upper(), lambda got, total: seen.append(got)) == data
    assert seen and seen[-1] == len(data) and seen == sorted(seen)
    with pytest.raises(ValueError, match="checksum mismatch.*Nothing was installed"):
        soundfonts._fetch(src.as_uri(), "0" * 64)

    folder = tmp_path / "into" / "here"
    path = soundfonts._fetch_file(src.as_uri(), digest, folder)
    assert path.parent == folder and path.read_bytes() == data
    path.unlink()
    with pytest.raises(ValueError, match="checksum mismatch.*Nothing was installed"):
        soundfonts._fetch_file(src.as_uri(), "0" * 64, folder)
    assert not list(folder.iterdir())                   # the refused download is deleted
    with pytest.raises(OSError):
        soundfonts._fetch_file((tmp_path / "absent.bin").as_uri(), digest, folder)
    assert not list(folder.iterdir())
