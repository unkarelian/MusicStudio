# Neural singers

A `singer` voice can be sung by a **DiffSinger voicebank**: a set of models
trained on recordings of one person singing. The studio writes the notes and
the syllables; the voicebank decides how they are sung.

**No voicebank is part of MusicStudio, and none is downloaded unless you ask.**
Each one is somebody's voice, published under that person's terms. This page
lists the ones this engine has been run with, where each comes from, and what
its terms ask of you. The summaries are ours and are not legal advice: the
linked terms are the authority, and they can change.

```bash
uv sync --extra neural                      # numpy, onnxruntime, pyyaml
uv run ms singer list                       # what is listed, what is installed
uv run ms singer show qixuan                # its terms, in short, and the link
uv run ms singer install qixuan --accept-terms
```

```python
add_voice("vox", "singer", role="melody", bank="qixuan")
add_op("vox", "lyrics", text="I will wait for you by the riv-er in the morn-ing")
```

Voicebanks are kept in `~/.local/share/musicstudio/singers`, never in a piece
or a repository. Every listed download is pinned by SHA-256 and checked before
it is unpacked. A voice whose bank is not installed is sung by the built-in
synthesized singer instead, with a warning, so a piece still renders anywhere.

## Listed voicebanks

`ms singer install <name> --accept-terms` fetches these from their authors'
own release pages.

| name | voice | sings | terms in short | size |
|---|---|---|---|---|
| `qixuan` | [Qixuan (绮萱) v2.7.0](https://github.com/yqzhishen/qixuan-diffsinger): a bright, young female voice. Voice: 颜绮萱; model: YQ之神 and the DiffSinger community | zh, en, ja | Its own [terms of use](https://github.com/yqzhishen/qixuan-diffsinger/blob/main/terms_of_use/Terms_of_Use.zh-CN.md) (Chinese; the Chinese text prevails). Songs may be shared and sold. Credit "绮萱" and "DiffSinger" and state that the vocal is AI-synthesized. No violent, sexual, abusive or unlawful content; no political or religious propaganda. Do not train or sample another voice model from its output. Do not modify or convert the model files. Pass it on only whole, unmodified and free. | 401 MB |
| `shisakune` | [Shisakune Demo (试作音Demo) v4.5.1](https://github.com/tuskinekinase/shisakunedemo_ds): three voice colours (`shisakune:smooth`, `:solid`, `:symphonic`). Voice: UG; training: Hisaka | zh, en, ja | [CC BY-NC-SA 4.0](https://github.com/tuskinekinase/shisakunedemo_ds/blob/main/LICENSE): credit it, non-commercial only, share adaptations alike. The repository gives no separate terms for songs, so treat those as non-commercial unless its authors say otherwise. | 502 MB |
| `alemon` | [Alemon (柠檬君) v3.5](https://github.com/tuskinekinase/alemon_ds): two voice colours (`alemon:normal`, `:falsetto`). By tuskinekinase; training: Hisaka | zh, en, ja | [CC BY-NC-SA 4.0](https://github.com/tuskinekinase/alemon_ds/blob/main/LICENSE), as above. | 502 MB |

All three need the **DiffSinger community vocoder** (PC-NSF-HiFiGAN 2025.02, by
the OpenVPI Team), which turns the model's spectrogram into sound. Its weights
are under [CC BY-NC-SA 4.0](https://openvpi.github.io/vocoders/); read that page
for how its authors apply the licence. `ms singer install` fetches it alongside
a voicebank that does not bundle one.

## Other voicebanks

Any DiffSinger voicebank in OpenUtau's layout (a folder with `dsconfig.yaml`)
can be registered after you download it yourself:

```bash
uv run ms singer add <name> <the zip or the folder>
```

These have English and published terms, but have **not** been run with this
engine, and their terms are yours to read:

- [Nishiren Gard](https://github.com/Gardanana/Nishiren-AI-Diffsinger) (contralto;
  English and Japanese). [Terms](https://github.com/Gardanana/Nishiren-AI-Diffsinger/blob/main/terms-of-service.md):
  name the voicebank when publishing; commercial use needs the author's approval;
  and it may not be used "with unethically AI generated lyrics, music, art, or
  videos". If an agent wrote the song, ask the author before using it.
- [Lem the Shapeshifter DS](https://wik-wav.neocities.org/lem-utau-voicebank)
  (three male voice colours; English, Japanese, Polish). Terms on its page.
- [OpenUtau's singer index](https://openutau.github.io/svs-index/) lists more,
  tagged `diffsinger`.

Not every voicebank will run: this engine feeds the inputs the common exports
declare (phonemes, durations, pitch, breathiness, voicing, tension, energy,
gender, velocity, a voice colour). One that needs something else is reported
by name and the voice falls back to the synthesized singer.

## When you publish

Credit the voicebank the way its terms ask. For Qixuan that is a line such as:

> Vocal: 绮萱 (Qixuan), DiffSinger voicebank. AI-synthesized singing voice.

## How it is driven

A phrase goes through the bank's models in order: **duration** (how long each
consonant takes at this tempo), **pitch** (the curve a singer would draw through
the written notes), **variance** (breathiness, voicing), **acoustic** (a mel
spectrogram, by diffusion) and the **vocoder**. The studio fixes where each
vowel starts (exactly on its note) and which phonemes are sung, from the same
`lyrics` op every other singer uses; English words are looked up in the
pronouncing dictionary (`ms lyrics install`).

Renders are reproducible: the noise the diffusion starts from is seeded from the
voice and the phrase, and each model is loaded freshly seeded for every phrase.
Rendered phrases are cached in `~/.cache/musicstudio/neural`, so only a phrase
you changed is sung again.

`ms singer check <piece>` renders the singer alone and has a speech recogniser
write down what it hears, scored against the lyric (paid; needs
`OPENROUTER_API_KEY`).

The input conventions these models expect are OpenUtau's
([MIT](https://github.com/stakira/OpenUtau)); [warble](https://github.com/erz0r/warble)
(MIT) was the reference for reading them.
