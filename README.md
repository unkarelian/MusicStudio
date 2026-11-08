# MusicStudio

A music studio built for agents. Instrumental score writing — OST rather than
songs — where themes are objects you develop, not notes you retype.

## Why agents are bad at music

Not for lack of taste. Five specific mechanical reasons:

1. **They write blind.** A note stream is emitted token by token and never heard,
   never seen, never checked against anything.
2. **The abstraction is wrong.** MIDI note 67 at tick 1920 is the assembly
   language of music. Nobody thinks that; they think "the theme, a third higher,
   on the downbeat of bar 5".
3. **Time drifts.** One note the wrong length and everything after it slides,
   and nothing catches it.
4. **Nothing enforces harmony.** Lines wander off the chord, the bass note isn't
   in it, voices collide, and the register is wherever the tokens landed.
5. **Motifs don't survive.** An agent "brings the theme back" by re-emitting
   notes it half-remembers. The whole point of a leitmotif is *exact identity
   under transformation*, and approximate recall destroys precisely that.

MusicStudio removes all five as *possibilities* rather than coaching against them.

## How it works

**A piece is an op-log over a scaffold, not a note list.** A form, a harmonic
scaffold, and voices holding ordered, named operations:

```python
add_motif("hero", "0 2 4:1/4 3 2:1/2")
add_op("horn", "play",   id="statement", motif="hero", at="5")
add_op("horn", "play",   id="return",    motif="hero", at="33",
       transform=["invert", "augment:2"])
add_op("cello", "bass",  id="ground",    at="1", bars=48, pattern="root")
```

Ops are addressable, so revision is surgical — `update_op("return", transpose=2)`
moves one statement of a theme and leaves the rest of the score alone.

**Every change is a checkpoint.** Mutations autosave, and the state before each
save goes onto a per-piece undo stack (`<project>/.history/`, 100 deep). Trying
the bold version of an idea is free when taking it back is `ms undo dusk` —
which also answers with a diff of exactly which notes came back. Deleting a
piece is undoable too.

**Pitch is scale degrees, never MIDI numbers.** `"0 2 4:1/4 3 2:1/2"` is a
shape, not a set of notes; it becomes pitches only when a key and a chord say
so. Out-of-key notes are unrepresentable rather than discouraged, modulation is
a one-line change, and the classical development operations become exact integer
arithmetic instead of approximations:

```
transpose   deg + n            inversion   2*axis - deg
retrograde  reverse the steps  augment     durations * factor
```

**Harmony is roman numerals, and chords stack thirds in the scale.** So `ii` is
minor in a major key without being told, `V7` gets a minor seventh, and `vii%7`
comes out half-diminished — the spellings agents reliably get wrong from memory.

**Motifs are named objects with recorded lineage.** This is the whole point.
Because `hero.invert.augment` is derived rather than retyped, the studio can
*state* — not guess — that the theme returning in the last act is the same
theme, and show you where every statement of it lands:

```
  motif            form                   appearances (bar: voice)
  hero             as written             5:horn 13:horn
  hero             invert:0               33:cello
  hero             fragment:0,3+sequence  21:violin 23:violin 25:violin
```

**The studio knows what instruments can do.** A voice is an instrument with a
range, a register where it actually sounds like itself, and a polyphony limit.
Ask a horn for a low E and it is an error; write a melody without naming an
octave and it lands where a horn sounds heroic rather than where the tokens fell.

## The views

Every mutation returns one. `score` is a pitch-by-time grid, one glyph per
voice, every column labelled by bar — which is what makes counterpoint *visible*:

```
    bar 1       2       3       4
        |       |       |       |
     A4|  Ll                    Pppppppp
     F4| L   Lll                Pppppppp
     D4|Lppppppp        Pppppppp
     D2|OoOoOoOo        OoOoOoOo
  chord|i       VI      iv      V7
```

`squint` is the arc — one column per bar, four lines, the whole piece:

```
  density  ..::-=+*##%@%#*+=-::..
  register __..--~~^^^~~--..__
  dynamic  ...:::---===+++***##
  voices   1122334455554433221
           intro   build   climax  resolve
```

If those lines are flat, the piece is flat, and no amount of good writing inside
the bars will fix it. `chart` shows the form and harmony; `motif_map` answers
whether the themes are developing or just repeating.

## The critique pass

`lint` reports bar positions, because "the voice leading is bad somewhere" is not
actionable:

- `range_violation` / `polyphony_exceeded` — notes the player does not have,
  chords on a monophonic instrument
- `out_of_tessitura` — a line written where the instrument sounds weak
- `low_interval_limit` — close intervals in the bass, which turn to mud
- `parallel_fifths` / `parallel_octaves` / `voice_crossing` — two parts that
  stopped being two parts
- `chord_clash` — a long dissonance that grinds and never resolves
- `harmonic_stasis` / `cadence_missing` / `redundant_accidental`
- `flat_dynamics` — four minutes at one level
- `motif_starvation` / `motif_never_developed` / `verbatim_repeat` — the failures
  of *form*, which are the ones agents actually make
- `never_rests` — players breathe, and a line that never stops stops being heard
- `melody_buried` — a pad or chord part sitting just above the tune, within an
  octave of it, for most of the time they share: the commonest scoring error,
  and one a line-against-line crossing check cannot see
- `untracked_quote` — a `phrase` that retypes a motif (or its inversion or
  retrograde) by hand, so the motif map cannot see the theme came back; the
  hint names the `play` op that would track it

Checks are tuned for **precision over recall**. A false positive on correct
writing costs more trust than a missed finding costs quality, so parallels are
only reported between genuinely independent monophonic lines, a clash must be
long *and* dissonant *and* unresolved, a leap has to exceed an octave, and a
"moment" shorter than a 32nd note — the overlap humanized timing makes where
one note's release meets the next attack — is not counted as a chord. A
textbook-correct four-part progression must lint clean — there is a test
asserting exactly that.

Game music that repeats can be marked as a loop (`--loop` on `new`, or
`ms piece dusk --loop`), and the cadence check stops asking it to end on the
tonic.

## Listening to music it did not write

The studio also reads existing music, so it can be pointed at a piece and asked
what it is made of. Imported material becomes an ordinary piece — every view,
the critique pass and every export work on it unchanged.

**MIDI is exact.** Every pitch and onset is stated in the file, so analysis of an
imported MIDI is as trustworthy as analysis of something the studio wrote.

**Audio is an estimate, and says so.** Pulling a melody out of a finished mix is
the MIREX melody-extraction problem — research-grade and genuinely hard. What
comes back is a monophonic guess produced by harmonic-summation salience and a
Viterbi track, carrying a `confidence` score that falls on the two known failure
modes: long stretches of one pitch (the tracker has locked onto a pad or bass)
and alternating intervals (it is flip-flopping between two partials).

```bash
uv run ms -p gallery import theme song.mid          # exact
uv run ms -p gallery import theme song.ogg          # estimated, with warnings
uv run ms -p gallery findmotifs theme
uv run ms -p gallery compare theme_a theme_b theme_c
uv run ms -p gallery adopt theme main --index 0     # make a find into a real motif
```

### Discovery refuses to guess

The hard part of finding themes is not finding repeated patterns — it is
declining to report the ones that mean nothing. Any long melody contains
thousands of repeated interval sequences by chance, and a scale passage hands you
`[2,2,2,2]` in every piece ever written. So:

- every candidate is tested against a **null model** — the same intervals,
  shuffled, many times over — and dropped if it appears about as often by chance;
- **degenerate shapes are refused outright**: all repeated notes, pure
  alternation, unbroken scale runs. These carry no thematic information, and not
  coincidentally they are also precisely what a failing pitch tracker emits;
- a cross-piece claim must clear significance **in every piece it is claimed to
  appear in**, and the report states the weakest transcription's confidence.

This is the critique pass's principle applied to analysis. A tool that tells you
two pieces share a leitmotif when they do not is worse than one that says it
cannot tell — and there is a test asserting that three unrelated random melodies
produce no shared theme.

## Styles

A profile is a set of *checkable properties*, not a vibe. `orchestral` is the
baseline: enforced ranges and tessitura, voice leading between every pair of
parts, the low-interval limit. Also ships `chamber`, `ambient` (harmonic stasis
is the idiom, so that check relaxes), `piano` (two hands, tenth span limit),
`chiptune` (four monophonic channels — chords have to be arpeggios) and
`freeform`. Each carries form presets, which do for structure what canvas
presets do for a sprite: `--form cue` gives you `intro / build / climax /
resolve` before a note exists.

## Use it

```bash
uv sync --all-extras

uv run ms styles                      # the rules and form presets
uv run ms ops                         # the op vocabulary
uv run ms transforms                  # the development vocabulary
uv run ms instruments --family brass  # ranges and idiom

uv run ms -p gallery new dusk --key "d minor" --tempo 76 --form cue
uv run ms -p gallery harmony dusk 1=i 3=VI 5=iv 7=V7
uv run ms -p gallery voice dusk horn horn --role melody
uv run ms -p gallery motif dusk hero "0 2 4:1/4 3 2:1/2"
uv run ms -p gallery op dusk horn play --id h1 motif=hero at=5
uv run ms -p gallery show dusk --bars 5-8
uv run ms -p gallery squint dusk
uv run ms -p gallery motifs dusk
uv run ms -p gallery lint dusk        # exits non-zero on errors
uv run ms -p gallery wav dusk         # and actually listen to it

uv run ms -p gallery undo dusk        # take back the last change (diff + lint)
uv run ms -p gallery redo dusk
uv run ms -p gallery piece dusk --key "e minor" --tempo 84   # transpose / retime
uv run ms -p gallery toggle dusk h1 off                      # A/B an op
```

Also: `setsection`, `setvoice` (incl. `pan=`), `rmsection`, `rmvoice`,
`rmmotif`, `reorder`, `delete`, `history`. `ms --help` lists everything.

As an MCP server:

```bash
uv run ms-mcp /path/to/project
```

or in `.mcp.json`:

```json
{"mcpServers": {"musicstudio": {"command": "uv",
  "args": ["run", "--directory", "/path/to/MusicStudio", "ms-mcp", "/path/to/project"]}}}
```

## Listening

`wav` renders a stereo 16-bit file. The synthesis is deliberately simple, but
three things are there because they are what let an ear pick the parts apart —
which is the whole reason to listen:

- **voices are seated** like an orchestra (violins left, low strings right,
  bass pulled to the centre), or wherever a voice's own `pan` puts them;
- **oscillators are band-limited per note**, so a high line does not fold back
  into inharmonic hiss, and bells are additive rather than a wavetable that
  cannot hold their inharmonic partials;
- **there is a room** sized to the style — long for ambient, short for chamber,
  nearly dry for chiptune — plus a little delayed vibrato on sustained timbres.

The room and vibrato need numpy (the `analysis` extra); without it the render
is dry but otherwise the same. `--dry` and `--mono` turn them off.

## Dependencies

The core has none. MIDI is read and written to spec and audio is synthesized with
the standard library, for the same reason the geometry in a pixel studio is
hand-rolled: the formats are small, exactly specified, and the failure mode of
getting them slightly wrong is a file that opens but is subtly wrong.

Audio *import* is the exception — spectral analysis over minutes of samples is
not something to do in pure Python — so it lives behind an extra, which also
makes WAV rendering several times faster and adds the reverb:

```bash
uv sync --extra analysis    # numpy; audio import also needs ffmpeg on PATH
```

MIDI import, motif discovery and cross-piece comparison need neither.

## Development

```bash
uv sync --all-extras
uv run pytest tests/ -q
uv run python examples/build_dusk.py     # the dogfood build; it must lint clean
```

`CLAUDE.md` (mirrored as `AGENTS.md`) lists the invariants the design rests on;
read it before changing `render.py`, `lint.py` or `analyze.py`.

## License

MIT — see [LICENSE](LICENSE).
