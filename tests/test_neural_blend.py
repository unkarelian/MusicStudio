"""Blending voices that share one model into a singer of its own."""
import struct

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("yaml")

from musicstudio import neural  # noqa: E402


def _bank(root, name, voices, model=b"one model", hidden=4):
    d = root / name
    (d / "dsvariance").mkdir(parents=True)
    for sub, key in (("", "acoustic"), ("dsvariance", "variance")):
        f = d / sub
        (f / "m.onnx").write_bytes(model + key.encode())
        (f / "phonemes.txt").write_text("SP\naa\n")
        extra = "linguistic: m.onnx\n" if sub else ""
        (f / "dsconfig.yaml").write_text(
            f"phonemes: phonemes.txt\n{key}: m.onnx\n{extra}hidden_size: {hidden}\n"
            "speakers:\n" + "".join(f"- {v}\n" for v in voices))
        for v, x in voices.items():
            (f / f"{v}.emb").write_bytes(struct.pack(f"<{hidden}f", *([x] * hidden)))
    (d / "portrait.png").write_bytes(b"png")
    return d


@pytest.fixture
def singers(tmp_path, monkeypatch):
    monkeypatch.setattr(neural, "SINGER_DIR", tmp_path)
    _bank(tmp_path, "one", {"soft": 1.0, "firm": 3.0})
    _bank(tmp_path, "two", {"plain": 5.0})
    _bank(tmp_path, "other", {"plain": 5.0}, model=b"another model")
    return tmp_path


def test_mix_syntax():
    assert neural.parse_mix("a*0.6+b*0.4") == [("a", 0.6), ("b", 0.4)]
    assert neural.parse_mix("a+b") == [("a", 1.0), ("b", 1.0)]
    assert neural.parse_mix("") == []
    with pytest.raises(ValueError):
        neural.parse_mix("a*-1")
    assert neural.parse_recipe("one:soft*1+firm*1+two:plain*2") == [
        ("one", "soft", 0.25), ("one", "firm", 0.25), ("two", "plain", 0.5)]


def test_a_colour_can_be_a_blend_of_a_banks_own(singers):
    m = neural._Model(singers / "one")
    assert np.allclose(m.embed("soft*3+firm", 2), 1.5)
    assert np.allclose(m.embed("firm", 2), 3.0)
    assert np.allclose(m.embed("", 2), 1.0)
    assert np.allclose(m.embed("nobody", 2), 1.0)


def test_blend_across_banks_that_share_a_model(singers):
    dest = neural.blend("mine", "one:soft*0.5+two:plain*0.5", gender=0.4)
    for sub in ("", "dsvariance"):
        m = neural._Model(dest / sub)
        assert m.speakers == ["mine"]
        assert np.allclose(m.embed("", 1), 3.0)
    assert not list(dest.rglob("soft.emb")) and not (dest / "portrait.png").exists()
    made = neural.blend_info("mine")
    assert made["gender"] == 0.4 and made["models_from"] == "one"
    assert [r["bank"] for r in made["recipe"]] == ["one", "two"]
    # The sources are untouched.
    assert neural._Model(singers / "one").speakers == ["soft", "firm"]
    with pytest.raises(FileExistsError):
        neural.blend("mine", "one:soft")
    neural.blend("mine", "one:firm", force=True)
    assert np.allclose(neural._Model(dest).embed("", 1), 3.0)


def test_blend_refuses_what_cannot_be_blended(singers):
    with pytest.raises(ValueError, match="not voices of one model"):
        neural.blend("x", "one:soft+other:plain")
    with pytest.raises(ValueError, match="no voice"):
        neural.blend("x", "one:nobody")
    with pytest.raises(FileNotFoundError):
        neural.blend("x", "one:soft+absent:plain")
    with pytest.raises(ValueError, match="listed"):
        neural.blend("qixuan", "one:soft")
    neural.blend("mine", "one:soft+two:plain")
    with pytest.raises(ValueError, match="itself a blend"):
        neural.blend("again", "mine")
    assert not (singers / "x").exists()
