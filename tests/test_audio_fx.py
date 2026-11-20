"""The per-voice effects: what a span covers, and what a transform's length may cost."""
import importlib

import pytest

np = pytest.importorskip("numpy")
audio = importlib.import_module("musicstudio.audio")
SR = audio.SR


def _smooth(n: int) -> bool:
    for q in (2, 3, 5):
        while n % q == 0:
            n //= q
    return n == 1


def test_a_transform_length_is_the_next_one_with_small_factors():
    for n in list(range(1, 2500)) + [11537262, 8904673]:
        size = audio._fft_size(n)
        assert size >= n and _smooth(size)
        if n < 2500:
            assert not any(_smooth(m) for m in range(n, size))


@pytest.mark.parametrize("span", [300, 2048, 2048 + 512 * 40 + 500, 2048 + 512 * 7])
def test_a_filter_reaches_the_last_sample_of_its_span(span):
    """Framed bare, the last few hundred samples of a span came through dry."""
    rng = np.random.default_rng(5)
    dry = rng.standard_normal(span + 4000)
    left, right = dry.copy(), dry.copy()
    lo, hi = 2000, 2000 + span
    audio._apply_fx(left, right, [("filter", {"start": 200, "end": 200}, lo, hi)])
    assert np.array_equal(left[:lo], dry[:lo]) and np.array_equal(left[hi:], dry[hi:])
    assert np.array_equal(left, right)
    tail = slice(hi - min(256, span // 2), hi)
    # A 200 Hz lowpass leaves a small part of white noise, everywhere in the span.
    assert np.sqrt((left[tail] ** 2).mean()) < 0.3 * np.sqrt((dry[tail] ** 2).mean())
    head = slice(lo, lo + min(256, span // 2))
    assert np.sqrt((left[head] ** 2).mean()) < 0.3 * np.sqrt((dry[head] ** 2).mean())
    assert not np.any(left[lo:hi] == dry[lo:hi])


def test_a_filter_wide_open_changes_nothing_it_can_hear():
    """The frames add back to what went in: no ripple at the hop, no edge gain."""
    t = np.arange(SR) / SR
    dry = 0.5 * np.sin(2 * np.pi * 220 * t)
    left, right = dry.copy(), dry.copy()
    audio._apply_fx(left, right, [("filter", {"start": 20000, "end": 20000}, 0, SR)])
    assert np.abs(left - dry)[64:-64].max() < 1e-3


def test_an_eq_does_not_carry_the_end_of_a_span_round_to_its_start():
    """A burst at the very end of the buffer rings on into nothing, and not
    into the silence at the start of it."""
    n = SR + 12347                      # a length with a large prime in it
    rng = np.random.default_rng(2)
    left = np.zeros(n)
    left[-2000:] = rng.standard_normal(2000)
    right = left.copy()
    audio._apply_fx(left, right, [("eq", {"freq": 3000, "gain": 6, "width": 2}, 0, n)])
    assert np.abs(left[:SR // 2]).max() < 1e-6


def test_an_eq_in_the_middle_is_the_plain_transform():
    n = SR + 12347
    rng = np.random.default_rng(4)
    dry = np.zeros(n)
    dry[SR // 4:SR // 2] = rng.standard_normal(SR // 4)
    left, right = dry.copy(), dry.copy()
    audio._apply_fx(left, right, [("eq", {"freq": 220, "gain": -4, "width": 1.5}, 0, n)])
    f = np.fft.rfftfreq(n, 1.0 / SR)
    curve = 10 ** (-4 / 20.0 * np.exp(-0.5 * (np.log2(np.maximum(f, 1e-6) / 220)
                                              / (1.5 / 2.355)) ** 2))
    want = np.fft.irfft(np.fft.rfft(dry) * curve, n)
    assert np.abs(left - want).max() < 1e-9


def test_a_duck_keyed_from_the_last_sample_does_not_fall_off_the_buffer():
    left, right = np.ones(1000), np.ones(1000)
    audio._apply_fx(left, right, [("duck", {"_hits": [1100, 999, 500], "depth": 8.0}, 0, 1000)])
    assert left.min() < 1.0 and np.all(np.isfinite(left))
