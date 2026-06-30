from __future__ import annotations

import numpy as np
import pytest

from photon_link_lab.symbols import generate_symbols, pam_levels, sample_at_symbols, upsample


def test_pam_levels_support_nrz_and_pam4() -> None:
    assert np.allclose(pam_levels(2), [-1.0, 1.0])
    assert np.allclose(pam_levels(4), [-1.0, -1.0 / 3.0, 1.0 / 3.0, 1.0])


def test_pam_levels_reject_non_power_of_two() -> None:
    with pytest.raises(ValueError):
        pam_levels(3)


def test_symbol_generation_is_deterministic() -> None:
    first_idx, first_symbols = generate_symbols(16, order=4, seed=11)
    second_idx, second_symbols = generate_symbols(16, order=4, seed=11)
    assert np.array_equal(first_idx, second_idx)
    assert np.array_equal(first_symbols, second_symbols)


def test_upsample_and_sample_round_trip() -> None:
    symbols = np.array([-1.0, 0.0, 1.0])
    waveform = upsample(symbols, 4)
    assert np.array_equal(sample_at_symbols(waveform, 4), symbols)
