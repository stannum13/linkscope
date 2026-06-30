from __future__ import annotations

import numpy as np

from photon_link_lab.config import LinkConfig, WDMConfig
from photon_link_lab.wdm import channel_wavelengths_nm, crosstalk_matrix, simulate_wdm


def test_channel_wavelengths_are_centered() -> None:
    config = WDMConfig(n_channels=4, center_wavelength_nm=1310.0)
    wavelengths = channel_wavelengths_nm(config)
    assert len(wavelengths) == 4
    assert float(np.mean(wavelengths)) == config.center_wavelength_nm
    assert np.all(np.diff(wavelengths) > 0)


def test_crosstalk_matrix_tracks_adjacent_setting() -> None:
    quiet = crosstalk_matrix(WDMConfig(adjacent_crosstalk_db=-35.0))
    loud = crosstalk_matrix(WDMConfig(adjacent_crosstalk_db=-20.0))
    assert quiet.shape == (4, 4)
    assert loud[0, 1] > quiet[0, 1]
    assert np.all(np.diag(quiet) > quiet[0, 1])


def test_single_channel_wdm_has_no_crosstalk() -> None:
    rows = simulate_wdm(
        cfg=LinkConfig(n_symbols=128),
        wdm=WDMConfig(n_channels=1),
    )
    assert len(rows) == 1
    assert rows[0]["crosstalk_power_ratio"] == 0.0
    assert rows[0]["dispersion_ui"] == 0.0
