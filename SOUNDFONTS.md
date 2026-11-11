# SoundFonts

MusicStudio renders with its own instrument models and needs no samples. A voice
marked `engine="soundfont"` is played from a SoundFont instead, inside the same
render. None of these banks is part of MusicStudio, none is in this repository,
and none is fetched by a render: each is downloaded once, on request, by
`ms soundfont install <name>`, checked against a pinned SHA-256 before it is
unpacked, and its licence is written beside it. They belong to the people who
made them; this page says who that is and what each asks.

`ms soundfont banks` lists them with sizes. Instruments that live in a
particular bank name it (`ms instruments` shows a `font`); without the bank the
instrument is played by its model, with a warning.

## General MIDI sets

| name | what | by | terms |
|---|---|---|---|
| `hq` | MuseScore General HQ 0.2.1. The default: every General MIDI instrument. | S. Christian Collins and others, for MuseScore | MIT |
| `standard` | MuseScore General 0.2, the smaller build. | the same | MIT |
| `fluidr3` | FluidR3 GM. A second complete set with another character; any voice can ask for it with `bank="fluidr3"`. | Frank Wen, Toby Smithe | MIT: keep the notice |
| `opl3` | OPL-3 FM 128M: the FM chip of DOS games as a General MIDI set (`bank="opl3"`). | Zandro Reveille | CC-BY-SA 4.0: credit, share alike |

`fluidr3` and `opl3` are fetched from snapshot.debian.org, which keeps every
version of a Debian package at a permanent address.

## Synthesizers and drum machines

| name | what | by | terms |
|---|---|---|---|
| `vintage` | Vintage Dreams Waves 2.0: 128 analog and FM synth presets and eight drum machines (808, 909, CR-78), built from plain waveforms. | Ian Wilson | Freeware: free to use and to pass on **unaltered, with its copyright notice**. It may not be edited or converted. It is installed as the original `.sf2` with the notice beside it. |
| `chip8` | Open8bitVChiptuner: four raw chip waves. | Timo Heidutzek | CC-BY-SA 4.0: credit, share alike |
| `synth_drums` | FreePats synthesizer percussion: an analog-style drum machine, synthesized with free software rather than sampled from hardware. | roberto@zenvoid.org, FreePats | CC0 |
| `lately_bass` | FreePats Lately Bass: a recreation of a well-known FM bass patch. | FreePats | CC0 |
| `fm_piano` | FreePats FM Piano 1: a sampled FM electric piano. | FreePats | CC0 |

## A rock band

| name | what | by | terms |
|---|---|---|---|
| `guitar_dist` | Electric guitar FSBS, distorted, bridge pickup. 127 MB to fetch, 390 MB installed. | FreePats | CC0 |
| `guitar_clean` | Electric guitar FSBS, clean, bridge pickup (the small set). | FreePats | CC0 |
| `bass_picked` | Electric bass YR, picked. | FreePats | CC0 |
| `bass_finger` | Electric bass YR, fingered. | FreePats | CC0 |
| `muldjord` | MuldjordKit: a recorded rock and metal drum kit. 55 MB to fetch, 220 MB installed. | Lars Muldjord; FreePats version by roberto@zenvoid.org | CC-BY 4.0: **credit Lars Muldjord** |
| `organ_rock` | Rock organ: a tonewheel organ through a rotary speaker. | FreePats | CC0 |
| `organ_drawbar` | Drawbar organ. | FreePats | CC0 |
| `piano_ydp` | YDP Grand Piano. | Zenph Studios / the OLPC sample library; FreePats | CC-BY 3.0: **credit them** |

The FreePats banks come from <https://freepats.zenvoid.org> and its GitHub
releases. Most are packed as 7z, so installing them needs `7z` (p7zip) or
`bsdtar` on PATH.

## If you publish music made with them

CC0 and MIT banks ask nothing of the music. For `muldjord`, `piano_ydp`, `opl3`
and `chip8`, credit the people named above. Considered and left out: GeneralUser
GS (its author asks that his download files not be linked to directly, and
cannot vouch for every sample's origin), TimGM6mb (GPL with no exception for
the sounds), and every rip of a commercial instrument's ROM.
