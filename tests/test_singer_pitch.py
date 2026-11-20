"""The pitch line every singer shares, and the grains a recorded one is cut into.

Both were made faster by doing less of the same arithmetic, so each is held
here against the plain version it replaced: the same samples, not nearly the
same.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")


def _whole_phrase_pitch(sung, singer, n, t0, rng, scoop, drift, total, vowels_only):
    """The pitch line worked out the long way: every slide and every vibrato
    over every sample of the phrase."""
    from musicstudio.vocal import SR, VOWELS
    t = np.arange(n) / SR + t0
    midi = np.full(n, sung[0].pitch, dtype=np.float64)
    for i, s in enumerate(sung):
        if i == 0:
            continue
        x = np.clip((t - (s.start - 0.012)) / (singer.glide / 4.0), -40.0, 40.0)
        midi += (s.pitch - sung[i - 1].pitch) / (1.0 + np.exp(-x))
    cents = -scoop * np.exp(-np.maximum(t - sung[0].start, 0.0) / 0.05) * (t >= sung[0].start - 0.05)
    for s in sung:
        if s.end - s.start < 0.36 or (vowels_only and s.nucleus not in VOWELS):
            continue
        rate = singer.vibrato_rate * rng.uniform(0.95, 1.05)
        rise = np.clip((t - s.start - 0.2) / 0.3, 0.0, 1.0) * (t < s.end)
        cents += singer.vibrato * rise * np.sin(2 * np.pi * rate * (t - s.start)
                                                + rng.uniform(0, 2 * np.pi))
    if drift:
        cents = cents + np.interp(t, np.linspace(t[0], t[-1], max(4, int(total * 3))),
                                  rng.normal(0.0, drift, max(4, int(total * 3))))
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0 + cents / 1200.0)


@pytest.mark.parametrize("instrument", ["singer", "singer_warm", "singer_low"])
@pytest.mark.parametrize("scoop, drift, vowels_only", [(55.0, 5.0, True), (45.0, 4.0, False),
                                                       (30.0, 0.0, False)])
def test_the_pitch_line_is_the_same_worked_out_only_where_it_moves(instrument, scoop, drift,
                                                                    vowels_only):
    from musicstudio.vocal import SINGERS, SR, Sung, _pitch_line
    singer = SINGERS[instrument]
    # Short notes whose slides overlap, long ones with vibrato, a leap of two
    # octaves, a note on a syllabic consonant, a rest inside the phrase, and
    # notes at the very start and end of what is rendered.
    shape = [(0.11, 60, "aa"), (0.09, 62, "iy"), (0.12, 64, "aa"), (0.9, 69, "ow"),
             (0.5, 45, "n"), (0.07, 69, "aa"), (0.07, 69, "aa"), (1.4, 57.25, "uw"),
             (0.4, 81, "ae"), (0.2, 80, "ih")]
    sung, at = [], 0.31
    for k, (length, pitch, nucleus) in enumerate(shape):
        sung.append(Sung(at, at + length, float(pitch), 80, (), nucleus, ()))
        at += length + (0.2 if k == 4 else 0.0)
    for t0, tail in ((0.0, 0.5), (0.3, 0.0)):
        total = sung[-1].end - t0 + tail
        n = int(total * SR)
        want = _whole_phrase_pitch(sung, singer, n, t0, np.random.default_rng(7), scoop, drift,
                                   total, vowels_only)
        got = _pitch_line(sung, singer, n, t0, np.random.default_rng(7), scoop=scoop,
                          drift=drift, total=total, vowels_only=vowels_only)
        assert got.tobytes() == want.tobytes()


def _plain_psola(u, src, f0):
    """`voicebank.psola` as it was first written: numpy asked for every value,
    and a window made for every grain."""
    from musicstudio.vocal import SR
    n = len(src)
    x = u.x
    pos = np.clip(src, 0, len(x) - 2)
    weight = u.voiced[pos.astype(np.int64)]
    out = np.zeros(n)
    have_marks = len(u.marks) >= 2
    noise_half = 160
    noise_win = np.hanning(2 * noise_half)
    t = 0.0
    while t < n:
        k = int(t)
        p = pos[k]
        if have_marks and weight[k] > 0.5:
            T_out = SR / max(60.0, float(f0[k]))
            j = int(np.searchsorted(u.marks, p))
            j = min(max(j, 0), len(u.marks) - 1)
            if j > 0 and abs(u.marks[j - 1] - p) < abs(u.marks[j] - p):
                j -= 1
            m = int(u.marks[j])
            T_src = float(u.period[min(m, len(x) - 1)])
            half = int(T_src)
            a, b = m - half, m + half
            if a >= 0 and b < len(x) and half > 8:
                grain = x[a:b] * np.hanning(2 * half) * min(1.6, T_out / T_src) ** 0.8
                o0 = k - half
                g0, g1 = max(0, -o0), min(2 * half, n - o0)
                if g1 > g0:
                    out[o0 + g0:o0 + g1] += grain[g0:g1]
            t += T_out
        else:
            m = int(p)
            a, b = m - noise_half, m + noise_half
            if a >= 0 and b < len(x):
                o0 = k - noise_half
                g0, g1 = max(0, -o0), min(2 * noise_half, n - o0)
                if g1 > g0:
                    out[o0 + g0:o0 + g1] += (x[a:b] * noise_win)[g0:g1]
            t += noise_half
    return out


def test_psola_lays_the_same_grains_as_the_plain_loop():
    from musicstudio import vocal
    from musicstudio.vocal import SINGERS, SR, Sung
    from musicstudio.voicebank import FRAME, Unit, psola, voicing
    # A "recording": the formant singer saying "sa", which has both kinds of
    # grain in it -- noise for the "s", pitch-marked cycles for the vowel.
    said, _ = vocal.render_phrase([Sung(0.2, 0.7, 62.0, 90, ("s",), "a", ())],
                                  SINGERS["singer_warm"], 3)
    x = np.concatenate([np.zeros(FRAME // 2), said, np.zeros(FRAME)])
    d = voicing(x, low=75.0, high=800.0)
    assert len(d["marks"]) > 20
    unit = Unit(x, d["marks"], d["voiced"], d["period"], 0, len(x))
    # Forwards at speed, slowed to a crawl, standing still, and off both ends.
    paths = [np.arange(len(x), dtype=np.float64),
             np.linspace(0, len(x) - 1, 3 * len(x)),
             np.full(SR // 4, float(d["marks"][len(d["marks"]) // 2])),
             np.linspace(-500.0, len(x) + 500.0, len(x) // 2)]
    for k, path in enumerate(paths):
        f0 = 180.0 * 2.0 ** (np.sin(np.arange(len(path)) / 3000.0 + k) / 2.0)
        got, want = psola(unit, path, f0), _plain_psola(unit, path, f0)
        assert np.abs(want).max() > 0.01
        assert got.tobytes() == want.tobytes()
