"""Style profiles: the rules a piece is held to.

A profile is not a filter applied at the end, and it is not a mood word. It is
a set of *checkable properties* the critique pass enforces, so that "write it
like an orchestral cue" becomes something a machine can be wrong about.

Form presets do for structure what canvas presets do for a sprite: a cue that
starts as ``intro / build / climax / resolve`` has a shape before it has a note
in it, which is the opposite of how agents usually write music and most of the
reason theirs meanders.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StyleProfile:
    name: str
    summary: str
    #: Hard cap on simultaneous voices; ``None`` for unlimited.
    max_voices: int | None = None
    #: Instrument families this style admits; ``None`` for any.
    families: tuple[str, ...] | None = None
    #: Check parallel perfect intervals, voice crossing and spacing.
    voice_leading: bool = True
    #: Apply the low-interval limit -- close intervals in the bass turn to mud.
    low_interval_limit: bool = True
    #: Warn when a line sits outside the instrument's characteristic register.
    check_tessitura: bool = True
    #: Bars the same chord may last before it counts as stasis.
    max_static_bars: int = 4
    #: Expected share of melodic notes that come from a named motif.
    min_motif_coverage: float = 0.35
    #: Widest simultaneous span one player's hand may cover, in semitones.
    max_hand_span: int | None = None
    #: Simultaneous notes above which the texture is judged overloaded.
    max_sonority: int = 12
    require_cadence: bool = True
    #: Velocity spread across sections below which the piece reads as flat.
    min_dynamic_range: int = 12
    tempo_range: tuple[int, int] = (40, 208)
    form_presets: dict[str, tuple[tuple[str, int], ...]] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def form(self, key: str) -> tuple[tuple[str, int], ...]:
        if key not in self.form_presets:
            raise KeyError(f"style {self.name!r} has no form preset {key!r}; "
                           f"have {sorted(self.form_presets)}")
        return self.form_presets[key]

    def to_json(self) -> dict:
        return {"name": self.name, "summary": self.summary,
                "max_voices": self.max_voices,
                "families": list(self.families) if self.families else None,
                "voice_leading": self.voice_leading,
                "low_interval_limit": self.low_interval_limit,
                "max_static_bars": self.max_static_bars,
                "min_motif_coverage": self.min_motif_coverage,
                "max_hand_span": self.max_hand_span,
                "require_cadence": self.require_cadence,
                "tempo_range": list(self.tempo_range),
                "forms": {k: [list(p) for p in v] for k, v in self.form_presets.items()},
                "notes": list(self.notes)}


COMMON_FORMS = {
    "ternary": (("A", 8), ("B", 8), ("A2", 8)),
    "binary": (("A", 8), ("B", 8)),
    "arch": (("A", 8), ("B", 8), ("C", 8), ("B2", 8), ("A2", 8)),
    "cue": (("intro", 4), ("build", 8), ("climax", 8), ("resolve", 4)),
    "loop": (("intro", 4), ("A", 8), ("B", 8)),
    "miniature": (("A", 4), ("B", 4), ("A2", 4)),
}

ORCHESTRAL = StyleProfile(
    name="orchestral",
    summary=(
        "Scoring for a real ensemble. Ranges and tessitura are enforced, voice "
        "leading is checked between every pair of parts, and the low-interval "
        "limit applies -- the constraints that make an arrangement sound like "
        "players rather than like a piano roll assigned to instruments."
    ),
    families=("strings", "winds", "brass", "perc", "keys", "plucked", "voice"),
    voice_leading=True,
    low_interval_limit=True,
    check_tessitura=True,
    max_static_bars=4,
    min_motif_coverage=0.35,
    max_sonority=14,
    require_cadence=True,
    form_presets=COMMON_FORMS,
    notes=(
        "Give every voice a reason to exist. A part that only doubles another at "
        "the unison is a part you have not written yet.",
        "Keep close intervals above C3. Thirds in the bass are mud at any dynamic.",
        "Leave the melody an octave of clear space; the commonest scoring error is "
        "burying the tune under its own accompaniment.",
        "Brass is loud. Writing it at the same dynamic as the strings means it wins.",
        "State a theme plainly before you develop it. Development of material the "
        "listener has not heard is just noise with a lineage.",
    ),
)

CHAMBER = StyleProfile(
    name="chamber",
    summary=(
        "Few players, every line exposed. Same rules as orchestral but with a "
        "hard voice cap, because there is nowhere for a weak inner part to hide."
    ),
    max_voices=6,
    families=("strings", "winds", "keys", "plucked"),
    max_static_bars=4,
    min_motif_coverage=0.45,
    max_sonority=8,
    form_presets=COMMON_FORMS,
    notes=(
        "Four independent lines beat eight dependent ones.",
        "Rests are structural here. A line that never stops stops being heard.",
    ),
)

AMBIENT = StyleProfile(
    name="ambient",
    summary=(
        "Slow harmony, sustained texture, space as the primary material. "
        "Harmonic stasis is the idiom rather than a defect, so that check relaxes "
        "-- but register and mud still matter, arguably more."
    ),
    voice_leading=False,
    low_interval_limit=True,
    max_static_bars=32,
    min_motif_coverage=0.15,
    max_sonority=10,
    require_cadence=False,
    min_dynamic_range=6,
    tempo_range=(40, 90),
    form_presets={**COMMON_FORMS,
                  "drift": (("bed", 16), ("swell", 16), ("bed2", 16))},
    notes=(
        "One idea per minute is a reasonable rate. Two is busy.",
        "A drone plus one moving line is a complete texture.",
        "Dynamics carry the form when harmony will not.",
    ),
)

PIANO = StyleProfile(
    name="piano",
    summary=(
        "Two hands, ten fingers. The span limit is the real constraint and the "
        "one most often violated by music written without a body in mind."
    ),
    max_voices=3,
    families=("keys",),
    voice_leading=True,
    low_interval_limit=True,
    max_hand_span=14,
    max_sonority=10,
    min_motif_coverage=0.4,
    form_presets=COMMON_FORMS,
    notes=(
        "Keep each hand inside a tenth unless the chord is rolled.",
        "Below E2 the piano blurs; leave the bottom octave for single notes.",
        "The left hand is an accompaniment, not a second melody -- unless it is, "
        "in which case thin out the right.",
    ),
)

CHIPTUNE = StyleProfile(
    name="chiptune",
    summary=(
        "Four monophonic channels: two pulse, one triangle, one noise. Harmony "
        "has to be implied by arpeggios because there are not enough voices to "
        "state it, which is the constraint that gives the idiom its sound."
    ),
    max_voices=4,
    families=("chip",),
    voice_leading=False,
    low_interval_limit=False,
    check_tessitura=False,
    max_static_bars=8,
    min_motif_coverage=0.5,
    max_sonority=4,
    require_cadence=False,
    tempo_range=(80, 200),
    form_presets={**COMMON_FORMS,
                  "loop": (("intro", 4), ("A", 8), ("B", 8), ("A2", 8))},
    notes=(
        "Every channel is monophonic. A chord is an arpeggio played fast.",
        "The triangle is the bass and has no volume control; write it as a line.",
        "Use the noise channel for rhythm, not for texture.",
        "Melody carries everything. If the tune is weak nothing else will cover it.",
    ),
)

FREEFORM = StyleProfile(
    name="freeform",
    summary="No house rules. Only unambiguous defects are reported.",
    voice_leading=False,
    low_interval_limit=False,
    check_tessitura=False,
    max_static_bars=64,
    min_motif_coverage=0.0,
    require_cadence=False,
    min_dynamic_range=0,
    form_presets=COMMON_FORMS,
)

STYLES: dict[str, StyleProfile] = {
    s.name: s for s in (ORCHESTRAL, CHAMBER, AMBIENT, PIANO, CHIPTUNE, FREEFORM)
}


def get_style(name: str) -> StyleProfile:
    try:
        return STYLES[name]
    except KeyError:
        raise KeyError(f"unknown style {name!r}; have {sorted(STYLES)}") from None
