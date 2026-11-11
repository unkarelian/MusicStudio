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
  the caller remembering. Preserve this in any new mutating verb that changes
  what sounds. (The motif verbs and `set_master` return what they changed
  instead: a motif nobody plays yet has no bars to show.) `OpResult.warnings`
  carries what the render had to guess or drop -- a guessed pronunciation, a
  syllable with no note -- because that is not lint and must still be seen.

- **Analysis never over-claims.** `analyze.py` exists to *refuse* findings as much
  as to produce them: the null-model test and `is_degenerate` are the load-bearing
  parts, not the n-gram search. Two tests hold this line —
  `test_unrelated_pieces_are_not_reported_as_sharing_a_theme` and
  `test_degenerate_shapes_are_refused`. If you loosen a threshold to make a
  desired result appear, you have broken the tool, because its whole value is
  that a positive result means something. The null model tests the *whole
  search*, not the one shape it found: two long melodies nearly always share
  some five-note shape, so `_shared_by_chance` and `_repeats_by_chance` ask how
  often shuffled pieces yield anything as long (per-shape testing reported a
  shared theme in 18 of 20 unrelated pairs). The pairwise many-seed assertions
  in that test are the ones that catch it; a p-value is never reported as zero.
- **Imported audio is labelled as an estimate everywhere it surfaces.** The
  `confidence` figure and its warnings must survive into any view or report built
  on it. A plausible-looking transcription that means nothing is the failure mode
  that matters.

- **Every save is a checkpoint, and the file outranks the cache.** `Studio.save`
  pushes the previous file onto `.history/<piece>/undo` before writing, so add new
  mutating verbs through `save`/`_result`, never by writing the file directly.
  `_result` renders and lints *before* it saves, so an op that validates but
  cannot be rendered never reaches the file
  (`test_an_edit_that_cannot_be_rendered_never_reaches_the_file`), and `save`
  writes beside the piece and renames over it. Also
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

- **A score file is the op-log as text, and nothing else.** `score.py` compiles
  one file into one piece; `decompile` writes any piece out, and
  `test_every_piece_in_the_gallery_is_the_same_piece_as_text` holds that the
  round trip is exact. So the language has no vocabulary of its own: an op line
  is the op's kind and its own parameter names. Add sugar only where it stays
  that way (positions by section, named lanes, `for`/`on` blocks all expand to
  plain ops with ids) -- a construct the JSON cannot hold would be a second
  place music is stored. `Studio.build` renders and lints before it saves, like
  every other mutation, and saves through `save`, so a build is a checkpoint.
  `#` followed by a space is a comment; `#4` is a sharp.
- **A diagnostic names the line.** `hear`, `match` and `at` exist because a
  listener says "the bell at 1:30 is far too loud" and the score is written in
  bars and ops: each reports a measurement *with* the voice, the op ids and
  (when the piece has a score file) the line that makes it. A new diagnostic
  that says only "the top is harsh" is half built.

## Working on it

```bash
uv sync --all-extras
uv run pytest tests/ -q
uv run python examples/build_dusk.py     # the dogfood build; it must lint clean
uv run python examples/build_lanterns.py # the long build; it must lint clean too
```

Write and revise a piece as a score file, not as a stream of calls or a build
script: `gallery/scores/iron_tide.ms` is the worked example, the docstring of
`score.py` is the notation, and `ms source <piece> -w` writes any existing
piece out as one.

```bash
uv run ms -p gallery build gallery/scores/iron_tide.ms --wav   # says what changed since the last build
uv run ms -p gallery at iron_tide 1:28        # what sounds then, which op, which line
uv run ms -p gallery match iron_tide ref.mp3  # against a reference recording
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

Three things `hear` reports were each first noticed by a person or by a
listening model and not by the studio, which is why they are there: a voice
that is not the tune and is louder than everything else together (an ornament
at `ff`, heard as "a church bell hit over and over"), one pitch at one loudness
many times in a row (on a sampled instrument, one recording that many times),
and a silence in the middle of the music. `match` is how a piece is worked
toward a reference: band by band and section by section against the recording,
each difference with the voice that holds that band there and the ops that set
its level and tone. It found in one run what five rounds of asking a model did
not say plainly (a third of the reference's low end; a last section that never
fades). Given the reference separated into stems (`--stems DIR`: `drums.*`,
`bass.*` and the rest, from any source-separation model -- the studio runs
none) it also compares the balance between them and the drum pattern, which a
mix cannot give: `iron_tide` matched its reference's spectrum with a kit 11 dB
too quiet. A separator was checked against the studio's own true stems before
being believed (within about 1 dB for drums and bass). With stems it also says what each
stem *sounds* like against the reference's (how much of its own energy is
above 4 kHz, at 2-4 kHz, under 100 Hz), which is what turns "the mix is dull"
into "the voice is": `press_start` balanced like its reference and had a
fortieth of its vocal top. When the two recordings are not the same form the
piece is not laid over the reference; both are cut into equal parts, and then
only a difference that holds in most parts, in one direction, is reported --
part 3 of one song is a verse and of the other a chorus. A stem's power is its hits, their
length, their number and the separator's leakage all at once, so the drums also
get the level of the hits themselves against the bass's and the share of the
time they are sounding; a separated stem has its DC taken out before anything
is measured (an empty one is often a constant offset, which as power is a loud
instrument that is not there); and the drum grid is scaled to the track's own
loudest section, so hats that have gone show as nothing rather than as a
pattern turned back up. Each of those was a wrong reading first, caught by a
second reviewer re-measuring the same files: when a diagnostic leads to a
change in a piece, have its reading checked that way. One thing was built for
`match` and taken out again: reading how often the harmony changes, bar by bar,
out of a recording. Checked against a transcription of a real track it was
right 62% of the time, with or without stems, so it is not there -- see the
docstring -- and anything like it needs that kind of ground truth before it
ships. A listening model (see `examples/build_press_start.py` for how one was
used) is for checking that these tools are measuring the right things -- its
tempo and mix claims were often wrong, and its adjectives changed from run to
run -- not a step in writing a piece.

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
never a different arrangement of the notes. The stdlib path has no per-voice
processing and no singers; when a piece uses either it says so in a warning
(`_lost_without_numpy`), because an ignored `gain` is a different mix.
`synthesize(strict=True)` turns every fallback -- no numpy, a missing bank, no
FluidSynth -- into an error, and `engines={}` is filled with who actually
rendered each whole-voice stem. A test of an engine must use both: the formant
singer passes every audio assertion written for the neural one.

`synth.py` also holds the two synthesizers, `Synth` (oscillators, one resonant
filter with its own envelope, an LFO, unison) and `FM` (two operators and an
index envelope), and the digital instruments are settings of them. The filter
is never run over the signal: a filtered wave is a set of harmonics scaled by
the filter's response, which depends only on harmonic-over-cutoff, so there is
a stack of tables per wave and a moving filter is a walk through the stack
(`_synth_stack`). That is what keeps a note stateless, band-limited and the
same whatever was rendered before it; do not replace it with a recursive
filter. A pulse is two saws, which is what makes pulse-width modulation exact.
FM's index is capped by what the sample rate can hold at that pitch. An
instrument that lives in a SoundFont names a `like`, the model that plays it
where the bank is not installed (`_adopt`).

`synth.py` holds the instrument models -- what a note sounds like once it is
decided that it sounds. Read its docstring first: each mechanism (moving
spectrum, fixed formants, onset noise, slurs, inharmonic partials) is there
because its absence is audible, and the formant numbers are measured resonance
regions, not taste. Two rules: a model may not move, lengthen or re-seat a note,
and every random number is seeded from `(voice, onset, pitch)` through `crc32`.
The wavetable caches are keyed by the frequency a table is built from, not
only the written pitch, or a re-tuned note inherits another note's table and
the render depends on its own history
(`test_a_retuned_note_sounds_the_same_whatever_was_rendered_before_it`).
`LEVEL` is calibrated so models on and off sit at the same loudness; if you
change a model's `level`, re-check the balance of a full piece, not one note.

Drums are notes like everything else: a kit voice's pitch is the General MIDI
key of the drum, `beat` writes lanes and `chop` re-orders slices of whatever the
voice already plays. Keep `chop` symbolic -- it must stay an edit of the op-log,
not a bounce to audio. It has a sampler's meaning on purpose: a slice keeps the
sound it had where it was cut and is *not* re-harmonized where it lands, so a
moved note's `form` says "chopped" (the motif map must not call it the theme as
written), and on a pitched voice a whole-semitone `^n` moves the note's `pitch`
so lint, tension and MIDI see what sounds; only the fraction stays in `tune`. `filter`, `eq`, `drive`, `compress`, `crush` and `gain` are
`render.AUDIO_ONLY`: they return the notes untouched and are applied by
`audio._apply_fx` to that voice's own bus, so they exist in the built-in render
and not in MIDI. `compress` is level-matched on purpose (same power): adding one must not remix
the piece. `drive` is matched at the *peak*, which on a sustained voice is the
same thing and on a peaky one (a singer, a kit) is several dB louder -- follow
it with `gain`, the fader, and check with `ms hear`. `duck` keys from another
voice's notes (even a muted one), `cut` silences a bus, and the piece's `stops`
(`set_master`) cut every bus but the kept ones *and* the room's tail; `ms hear`
does not call a note under a stop a note that failed to sound. `tone` is read
by the neural singer and ignored by `_apply_fx`.
A voice with `engine="soundfont"` is rendered by `audio.sampled_stems` (one
FluidSynth run per voice, pitch groups laid end to end and resampled) and then
joins its bus like any other; it must fall back to the model, with a warning,
when FluidSynth or a bank is missing, because CI has neither. One drum
channel means one kit per piece in MIDI; the first kit voice chooses it.

`pattern.py` is a notation for rhythm that says the *shape* of a bar instead of
its grid (`x(3,8)`, `<x o>`, `x*4`, `x?`), used by `beat` when it is given
`cycle=`. The idea is the live-coding pattern languages'; the grammar and code
are the studio's own -- learn from other tools, never copy from them. It is
exact (`Fraction`s within one cycle; the caller makes ticks), a pattern is a
pure function of the cycle number, and chance is decided by the caller from a
`crc32` seed, so "sometimes" is the same every render
(`test_beat_takes_patterns_and_chance_is_the_same_every_render`, which also
holds that a bar written as a grid and as a pattern is the same notes). Keep it
a way of *writing* ops: a pattern lives in the op's params and stays editable;
it must not become a second place where music is stored.

`lyrics.py` turns text into one `Syllable` (onset, nucleus, coda) per note and
`vocal.py` sings them. Lyrics live *on the notes* (`Note.lyric`, `Note.sung`),
put there by the `lyrics` modifier op, so they follow a note through `double`,
`chop` and every other op. A lyrics op also carries `said`, the pronunciation
of each dictionary word, resolved when the text is written or changed
(`Piece._said`) and never at render: looked up per render, a saved piece sang
differently, or failed, on a machine with another dictionary or none. Editing
`said` is how one word is pronounced differently. A singer is rendered a phrase at a time, not a note
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
has; change the engine against it, not against a spectrogram. Its reference is
the words on the rendered notes, not the op text, and it reports `extra` (words
heard that were never written) beside the share understood, which is recall
only: every word sung amid noise scores 100%.

`utau.py` sings from a UTAU voicebank the user already has (`bank="utau:<name>"`,
made known by `ms utau add`): `oto.ini` says where each alias is in which
recording, and the engine lays those end to end through `voicebank.psola`.
**It fetches nothing and has no catalogue**, on purpose: every bank has its own
author's terms, in text files inside it, and `ms utau show` points at them
instead of summarising thousands of licences it has not read. Keep it that way
-- a test bank is recorded from the formant singer (`tests/test_utau.py`),
never downloaded. What is load-bearing: the preutterance point goes on the
beat (the lead-in is hurried when there is no room; the beat never moves);
`cutoff` is from the end of the file when positive and from the offset when
negative; `overlap` can be negative; `oto.ini` is Shift-JIS more often than
not, and so are the file names inside a `.zip`, which is why `add` unpacks the
archive itself. A held note is the same recording carried on, not a new one.
English goes through the Japanese syllables (`_syllable_keys`) and is an
approximation that says so; a bank recorded in English pieces
(`UtauBank.english`, X-SAMPA names) is sung by `_english_events` instead: a
cluster, a consonant-vowel piece on the beat, and a piece that closes the
vowel into the next consonant. Two things there were wrong first and measured
by `ms hear`: a consonant piece has no level of its own (levelled alone, every
final "s" was as loud as a vowel and the voice came out 16 dB hot -- it takes
its syllable's, `_Event.like`), and at speed the consonants between two beats
ate the note (they may take 55% of it, `KEEP`; past that they are hurried,
then cut from the end furthest from the vowel). It was checked once against a real bank with a
speech recogniser (19 of 20 syllables of a romaji line); change it against
that kind of check, not against a spectrogram. `ust` writes a voice out for
another editor; it is an export, like MIDI, and nothing reads one back in.

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
cached on disk; bump `ENGINE` when the same phrase would come out differently
(the key also holds `_fingerprint` of every file in the bank and its vocoder,
so replacing any model or dictionary invalidates it). An archive is streamed to
disk, size-bounded, and checked for `dsconfig.yaml` *before* it replaces an
existing install. Before a phrase the singer takes a breath
(the bank's own `AP` phoneme, up to `BREATH` seconds) where the line before
left room; it borrows from the silence and moves no written note.
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

One piece can draw on several SoundFonts. `Instrument.font` names a bank in
`soundfonts.BANKS` and `preset` its `(bank, program)` there; a voice's own
`bank=` asks for a whole other General MIDI set (`fluidr3`, `opl3`). Banks for
particular instruments (`Bank.extra`) are installed one directory down, where
`find_soundfont` does not look, so a kit of synth drums can never be mistaken
for the bank a whole piece is played through
(`test_a_bank_for_particular_instruments_is_never_the_general_bank`). Each is
level-matched against its own model (`listen.calibrate(font=)`), not centred
like a General MIDI set. A kit that a bank keeps as an ordinary preset with its
own layout carries a `keymap`, read out of the bank's zone table -- never
guessed from how the drums sound. `SOUNDFONTS.md` lists every bank with its
author and terms, and a test fails if one is missing from it. Left out on
purpose: GeneralUser GS (its author asks not to be linked to directly) and
anything ripped from a commercial instrument.

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
