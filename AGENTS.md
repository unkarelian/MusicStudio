# MusicStudio — notes for agents working on this repo

A music studio whose whole purpose is to make *you* good at writing music. If
you are writing a cue, use the tools; do not hand-write note lists.

## Invariants worth not breaking

- **Pieces are op-logs, not note lists.** Every edit must stay re-editable by op
  id. If you find yourself adding an API that bakes notes irreversibly, that is a
  design smell — the `phrase` op is the intended escape hatch.
- **Pitch is degrees end to end.** A raw MIDI number must never reach a
  generator; degrees become pitches only in `render._pitch_of`, against the key
  and chord in force *at that note's own onset*. This is what makes out-of-key
  notes unrepresentable and reharmonization free. Keep it that way.
- **Motif identity is derived, never retyped.** `derive_motif` and the
  `transform=` param both record lineage, and that lineage is what lets the
  motif map state that a theme returned rather than guess it. Any new way to
  produce a variation must carry `derived_from` and `lineage` with it, or the
  studio quietly loses the one thing it does that a note list cannot.
- **Lint favours precision over recall.** A false positive on correct writing
  costs more trust than a missed finding costs quality.
  `test_correct_four_part_writing_has_no_voice_leading_findings` exists purely to
  hold this line: a textbook I–IV–V–I, correctly voiced, must come back clean. If
  a new check fires on it, the check is wrong, not the chorale.
- **Studio options never shadow op params.** Op args arrive via `**params`, so
  studio-level options take a `view_` prefix (`view_bars`, not `bars` — `bars`
  belongs to the chords/bass/drone/groove ops). For the same reason the `double`
  op calls the part it follows `source`: `add_op(name, voice, ...)` already means
  the voice being written *to*, and one name cannot mean both. Both have
  regression tests.
- **Mutations return view + lint.** The feedback loop closes by default, not by
  the caller remembering. Preserve this in any new mutating verb.

- **Analysis never over-claims.** `analyze.py` exists to *refuse* findings as much
  as to produce them: the null-model test and `is_degenerate` are the load-bearing
  parts, not the n-gram search. Two tests hold this line —
  `test_unrelated_pieces_are_not_reported_as_sharing_a_theme` and
  `test_degenerate_shapes_are_refused`. If you loosen a threshold to make a
  desired result appear, you have broken the tool, because its whole value is
  that a positive result means something.
- **Imported audio is labelled as an estimate everywhere it surfaces.** The
  `confidence` figure and its warnings must survive into any view or report built
  on it. A plausible-looking transcription that means nothing is the failure mode
  that matters.

- **Every save is a checkpoint, and the file outranks the cache.** `Studio.save`
  pushes the previous file onto `.history/<piece>/undo` before writing, so add new
  mutating verbs through `save`/`_result`, never by writing the file directly, and
  wrap them in `@_mutation` so a verb that fails half-way evicts its half-applied
  edit instead of leaving it in the cache for the next save. `get()` reloads when
  the file's mtime or size changed, because the MCP server and a build script can
  hold the same piece at once.
- **Seeded means seeded.** Anything random in the render (`humanize`, and every
  instrument model in `synth.py`) derives its seed from stable data --
  `zlib.crc32`, never `hash()`, which Python salts per process.
  `test_humanize_is_reproducible_across_processes` and
  `test_every_instrument_has_a_voice_and_a_stable_one` hold this.
- **Decoration never moves the line.** An ornament is a mark on a step, realized
  in degree space at render time; the written note keeps its onset and its end,
  and graces borrow from the note *before*. The elaborating transforms
  (`embellish`, `dot`, `displace`, `thin`) keep total duration for the same
  reason `fill` does. Ornament notes carry `Note.ornament`, and voice-leading
  lint judges the line without them -- a trill is not a run of parallels.
- **`then` keeps one parent.** A theme joined from cells descends from its
  first cell (`derived_from`), and names the others in its lineage. That is what
  `Piece.heard_within` reads, so a cell that only ever sounds inside a longer
  theme is not reported as unused.

## Working on it

```bash
uv sync --all-extras
uv run pytest tests/ -q
uv run python examples/build_dusk.py     # the dogfood build; it must lint clean
uv run python examples/build_lanterns.py # the long build; it must lint clean too
```

To judge a musical change, render and actually listen — the ASCII views tell you
whether the writing is correct, not whether the music works:

```bash
uv run ms -p gallery wav dusk -o /tmp/check.wav
uv run ms -p gallery wav dusk -o /tmp/check.wav --soundfont   # sampled, if installed
```

If you cannot listen, measure. `ms hear <piece>` renders each voice alone and
reports who is loudest, whether the tune clears its accompaniment, and which
notes did not sound; `ms tension <piece>` shows whether the piece leans
anywhere. `hear` found a piano model bug (strings of one note starting out of
phase) and a SoundFont whose horn buried the violins, neither of which any
score view could have shown. Run it with `--soundfont` too: the two renders
can disagree, and the one the listener hears is the one that matters.

`squint` is the fastest way to see whether a change helped: if density, register
and dynamics are flat across the bars, the piece is flat regardless of what the
score view shows.

## Where things live

`theory.py` holds the parts most easily got subtly wrong. `parse_chord` stacks
thirds *in the scale* and treats case and suffixes as corrections on top — that
ordering is what makes `ii` minor and `vii%7` half-diminished without being told,
and inverting it breaks every diatonic quality at once. Duration parsing is
fractions of a whole note, with TPQ=480 chosen so triplets and dotted values stay
whole ticks.

`motif.py` holds the transformation algebra. The operations are exact integer
arithmetic on purpose; `fill` in particular must preserve total duration, or
smoothing a line silently moves everything after it. There is a test for it.

`render.py` resolves degrees against the harmony at each onset and picks the
octave that centres a line in the instrument's tessitura. Read the module
docstring before changing either — both are load-bearing.

`audio.py` has two synthesis paths, pure stdlib and numpy, that must render the
same *arrangement*: same length, same seating, same note onsets and loudness
contour (`_envelope_np` is checked sample-for-sample against `_envelope`, and
`test_instrument_models_change_the_sound_and_not_the_music` holds the rest).
Reverb, the limiter and the instrument models are numpy-only extras on top,
never a different arrangement of the notes.

`synth.py` holds the instrument models -- what a note sounds like once it is
decided that it sounds. Read its docstring first: each mechanism (moving
spectrum, fixed formants, onset noise, slurs, inharmonic partials) is there
because its absence is audible, and the formant numbers are measured resonance
regions, not taste. Two rules: a model may not move, lengthen or re-seat a note,
and every random number is seeded from `(voice, onset, pitch)` through `crc32`.
`LEVEL` is calibrated so models on and off sit at the same loudness; if you
change a model's `level`, re-check the balance of a full piece, not one note.

Drums are notes like everything else: a kit voice's pitch is the General MIDI
key of the drum, `beat` writes lanes and `chop` re-orders slices of whatever the
voice already plays. Keep `chop` symbolic -- it must stay an edit of the op-log,
not a bounce to audio. `filter`, `drive`, `compress`, `crush` and `gain` are
`render.AUDIO_ONLY`: they return the notes untouched and are applied by
`audio._apply_fx` to that voice's own bus, so they exist in the built-in render
and not in MIDI. `compress` and `drive` are level-matched on purpose (same
power, same peak): adding one must not remix the piece, and `gain` is the fader.
A voice with `engine="soundfont"` is rendered by `audio.sampled_stems` (one
FluidSynth run per voice, pitch groups laid end to end and resampled) and then
joins its bus like any other; it must fall back to the model, with a warning,
when FluidSynth or a bank is missing, because CI has neither. One drum
channel means one kit per piece in MIDI; the first kit voice chooses it.

`lyrics.py` turns text into one `Syllable` (onset, nucleus, coda) per note and
`vocal.py` sings them. Lyrics live *on the notes* (`Note.lyric`, `Note.sung`),
put there by the `lyrics` modifier op, so they follow a note through `double`,
`chop` and every other op. A singer is rendered a phrase at a time, not a note
at a time, by `audio.prerendered` -- consonants borrow time from the note
before and formants glide across the boundary, which a per-note model cannot
do. Three things in `vocal.py` are load-bearing: the vowel starts exactly on
the note (`test_consonants_come_before_the_beat...`), the formant table is
measured values and not taste, and the root-and-tilt on the tract response is
what gives the voice any energy above 2 kHz. Tests that use English words must
point `lyrics.DICT_DIR` at a temp directory, or they depend on whether the
dictionary happens to be installed.

`voicebank.py` is a recorded voice that sings any lyric: whole-word recordings
where it has them, halves of the 271-word unit corpus (`data/voice_corpus.txt`)
where it does not, re-pitched by PSOLA. Things learned the hard way, each with
a test or a measurement behind it: sing a recorded word *whole* (assembling
everything from units scored 37% with a speech recogniser, whole words 85%);
stretch the whole vowel (`_stretch`), never freeze its middle or sweep back and
forth across it ("na-na-na"); never resample a consonant to shorten it
(`psola` lays unvoiced sound in fixed grains --
`test_a_consonant_played_faster_keeps_its_tone`); find the vowel/consonant
join by *brightness*, because nasals are as loud as vowels; level every
syllable to the note. The recordings live in the user's cache and never in a
piece or the repo (they come from a paid service under the user's account).
Recording and transcribing cost money, need `OPENROUTER_API_KEY`, and happen
only on an explicit command, never inside a render. A voice whose bank is
missing falls back whole to `vocal.py` with a warning, because CI has no bank.
`Studio.check_words` is the only objective test of intelligibility the studio
has; change the engine against it, not against a spectrogram.

`neural.py` sings through a DiffSinger voicebank (ONNX: duration, pitch,
variance, acoustic, vocoder) and is the only engine trained on singing. Rules,
each learned or decided on purpose: **no voicebank is bundled, committed or
fetched by a render** -- each is a person's voice under that person's terms, so
`install` refuses without `accept=True`, every download is pinned by SHA-256
through `soundfonts._fetch`, and `SINGERS.md` carries the link and a summary of
the terms for every entry in `CATALOGUE`. Do not add an entry whose terms you
have not read, and say in `asks` what they require (credit, non-commercial,
content limits). The studio keeps deciding the notes, the phonemes and where
each vowel starts (`group_phrase`: a syllable's opening consonants close the
group *before* it, which is what puts the vowel on the beat); the bank decides
the rest. Seeding: ONNX Runtime seeds a graph's random nodes when the session
is built and never again, so `Singer._session` builds a fresh one per run --
caching sessions makes a phrase depend on what was rendered before it, and
`test_an_installed_neural_singer_sings_the_score_the_same_way_twice` (which
runs only where a bank is installed) catches exactly that. Rendered phrases are
cached on disk; bump `ENGINE` when the same phrase would come out differently.
Levels differ by 12 dB between banks, so `trim` measures each once against
`LEVEL`. A missing bank, vocoder or `onnxruntime` falls back whole to
`vocal.py` with a warning, because CI has none of them. The `--soundfont`
whole-piece render does not sing at all (a singer becomes a General MIDI
patch): judge a sung piece through the built-in render.

`tension.py` and `listen.py` are the two views built for an agent that cannot
listen. `tension` is a *model* (chord function, key distance, key profiles,
interval expectation) and `listen` is a *measurement* of rendered stems; each
says which it is in its first line, and both describe rather than judge --
neither is a lint finding, and neither should become one without the precision
tests lint has. `listen.calibrate` is what keeps a SoundFont render balanced
like the built-in one: per instrument, a level trim and a velocity exponent,
measured against the models and cached per bank. If you change a model's level
in `synth.py` the cache key changes with `LEVEL`, but not with a single
instrument's `level` -- pass `refresh=True` once.

`soundfonts.py` is the only place the studio fetches anything. Every download is
pinned by SHA-256 and verified before it is unpacked, a custom URL must bring
its own hash, and the bank's licence is written beside it. Do not add a bank
without a hash, and do not commit one: they are tens of megabytes of recordings.

`ingest.py` holds the MIDI parser (running status and all) and the audio melody
tracker. Read `_confidence` before touching the tracker: it encodes the two ways
the tracker fails, and those checks are why a bad transcription announces itself
instead of quietly producing nonsense.

`lint.py` holds `LOW_INTERVAL_LIMITS`, keyed by *interval* rather than by
register: a major second is fine at Eb3 and mud a fifth lower, while a perfect
fifth is fine nearly to the bottom of the piano. It got this backwards once and
reported every octave in the bass as mud.
