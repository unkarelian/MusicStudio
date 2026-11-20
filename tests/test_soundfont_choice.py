"""Choosing a SoundFont by name: from a voice, from a piece, from a render."""

import asyncio
import json
import warnings

import pytest

from musicstudio import audio, soundfonts
from musicstudio.doc import Piece
from musicstudio.score import compile_score, decompile


def _bank(folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(b"RIFF\x04\x00\x00\x00sfbk")
    return path


def test_a_soundfont_is_asked_for_by_name_by_file_name_or_by_path(tmp_path, monkeypatch):
    monkeypatch.setattr(soundfonts, "INSTALL_DIR", tmp_path)
    fluid = _bank(tmp_path / soundfonts.EXTRA_DIR, soundfonts.BANKS["fluidr3"].filename)
    mine = _bank(tmp_path, "MyOrchestra.sf2")
    assert soundfonts.resolve("fluidr3") == fluid
    assert soundfonts.resolve("myorchestra") == mine
    assert soundfonts.resolve("MyOrchestra.sf2") == mine
    assert soundfonts.resolve(str(mine)) == mine
    assert soundfonts.resolve("hq") is None             # listed, not installed
    assert soundfonts.resolve("nothing") is None
    assert audio.find_soundfont("fluidr3") == fluid
    with pytest.raises(FileNotFoundError, match="ms soundfont install hq"):
        audio.find_soundfont("hq")
    with pytest.raises(FileNotFoundError, match="fluidr3"):   # the names it could be
        audio.find_soundfont("nothing")


def test_the_listing_says_what_is_installed_and_what_each_bank_plays(tmp_path, monkeypatch):
    monkeypatch.setattr(soundfonts, "INSTALL_DIR", tmp_path)
    _bank(tmp_path / soundfonts.EXTRA_DIR, soundfonts.BANKS["fluidr3"].filename)
    _bank(tmp_path, "MyOrchestra.sf2")
    banks = {b["name"]: b for b in soundfonts.listing()["banks"]}
    assert set(soundfonts.BANKS) <= set(banks)
    assert banks["fluidr3"]["installed"] and banks["fluidr3"]["kind"] == "general midi"
    assert not banks["hq"]["installed"] and banks["hq"]["path"] is None
    assert banks["MyOrchestra"]["installed"]
    # A bank for particular instruments names them; every bank says its terms.
    assert banks["muldjord"]["kind"] == "instruments" and banks["muldjord"]["instruments"]
    assert all(b["terms"] for b in banks.values())


def test_a_piece_names_its_soundfont_in_its_score_and_falls_back_without_it(
        tmp_path, monkeypatch):
    monkeypatch.setattr(soundfonts, "INSTALL_DIR", tmp_path)
    text = ('piece p key="C major" tempo=90 style=orchestral\n'
            'meta soundfont = "fluidr3"\n\n'
            'section a bars=2\n\n'
            'voice v piano role=melody engine=soundfont bank=opl3\n')
    piece = compile_score(text)
    assert piece.meta["soundfont"] == "fluidr3"
    assert piece.get_voice("v").bank == "opl3"
    again = compile_score(decompile(piece))
    assert again.to_json() == piece.to_json()
    with pytest.warns(UserWarning, match="fluidr3"):    # not installed: say so, go on
        assert audio.piece_soundfont(piece) is None
    with pytest.raises(RuntimeError, match="fluidr3"):
        audio.piece_soundfont(piece, strict=True)
    fluid = _bank(tmp_path / soundfonts.EXTRA_DIR, soundfonts.BANKS["fluidr3"].filename)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert audio.piece_soundfont(piece) == fluid
        assert audio.piece_soundfont(Piece("q", "C major")) is None
    # The piece's bank is the general one for its sampled voices; a voice's own wins.
    opl = _bank(tmp_path / soundfonts.EXTRA_DIR, soundfonts.BANKS["opl3"].filename)
    piece.voices.append(type(piece.voices[0])("w", "piano", engine="soundfont"))
    plan, _ = audio._sampler_plan(piece.voices, audio.piece_soundfont(piece), False)
    assert plan["v"][0] == opl and plan["w"][0] == fluid


def test_the_mcp_server_lists_soundfonts_and_has_the_listening_tools(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    from musicstudio import mcp_server
    monkeypatch.setattr(soundfonts, "INSTALL_DIR", tmp_path)
    _bank(tmp_path / soundfonts.EXTRA_DIR, soundfonts.BANKS["fluidr3"].filename)
    info = json.loads(mcp_server.ms_soundfonts())
    assert [b["name"] for b in info["banks"]] == ["fluidr3"]
    assert len(json.loads(mcp_server.ms_soundfonts(installed_only=False))["banks"]) \
        == len(soundfonts.BANKS)
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert {"ms_hear", "ms_match", "ms_at", "ms_tension", "ms_check_words",
            "ms_soundfonts", "ms_export_wav"} <= names


def test_a_render_through_the_mcp_server_says_what_fell_back(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    from musicstudio import mcp_server

    def render():
        warnings.warn("voice 'keys' asks for the SoundFont 'fluidr33'", stacklevel=2)
        warnings.warn("voice 'keys' asks for the SoundFont 'fluidr33'", stacklevel=2)
        return tmp_path / "out.wav"
    said = mcp_server._with_warnings(render).splitlines()
    assert said == [str(tmp_path / "out.wav"),
                    "render warning: voice 'keys' asks for the SoundFont 'fluidr33'"]
    assert mcp_server._with_warnings(lambda: "quiet") == "quiet"
