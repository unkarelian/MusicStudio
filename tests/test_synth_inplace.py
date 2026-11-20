"""synth.py's in-place arithmetic against the plain expressions it stands for.

The per-sample code there works in place to spare the allocator, on the promise
that it is the same operations in the same order. This holds it to that: each
helper must give, bit for bit, what the expression it replaced gives.
"""

import pytest

np = pytest.importorskip("numpy")

from musicstudio import synth


def _same(got, plain):
    assert got.dtype == plain.dtype and got.tobytes() == plain.tobytes()


def test_in_place_helpers_give_the_plain_expressions_bit_for_bit():
    rng = np.random.default_rng(7)
    n = 5000
    t = np.arange(n) / synth.SR
    cents = 30.0 * rng.standard_normal(n)

    _same(synth._decay(t, 0.4), np.exp(-t / 0.4))

    cycles = np.cumsum(261.6 * 2.0 ** (cents / 1200.0)) / synth.SR + 0.37
    _same(synth._cycles(cents.copy(), 261.6, 0.37), cycles)

    pos = (cycles - np.floor(cycles)) * synth.TABLE
    i = pos.astype(np.int64)
    frac = pos - i
    tab = synth._table(1.0 / np.arange(1.0, 40.0))
    _same(synth._osc(tab, cycles), tab[i] + (tab[i + 1] - tab[i]) * frac)

    # The synth's stack is float32 and is read past both ends of its rows.
    stack = synth._synth_stack("saw", 1.2, 4, 261.6)
    row = np.linspace(-2.0, len(stack) + 2.0, n)
    r = np.clip(row, 0.0, len(stack) - 1.001)
    j = r.astype(np.int64)
    lo = stack[j, i] + (stack[j, i + 1] - stack[j, i]) * frac
    hi = stack[j + 1, i] + (stack[j + 1, i + 1] - stack[j + 1, i]) * frac
    _same(synth._stack_osc(stack, cycles, row), lo + (hi - lo) * (r - j))
    _same(row, np.linspace(-2.0, len(stack) + 2.0, n))      # and leaves its inputs alone
