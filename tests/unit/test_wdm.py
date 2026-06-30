from __future__ import annotations

import numpy as np
import pytest

from photon_link_lab.config import LinkConfig, ModulatorConfig, WDMConfig
from photon_link_lab.link import simulate_link
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
    cfg = LinkConfig(n_symbols=128)
    wdm = WDMConfig(n_channels=1, mux_loss_db=1.2)
    rows = simulate_wdm(
        cfg=cfg,
        wdm=wdm,
    )
    equivalent = simulate_link(
        cfg.with_updates(connector_loss_db=cfg.connector_loss_db + wdm.mux_loss_db),
        ModulatorConfig(),
    )
    assert len(rows) == 1
    assert rows[0]["crosstalk_power_ratio"] == 0.0
    assert rows[0]["crosstalk_penalty_factor"] == 1.0
    assert rows[0]["dispersion_band_skew_ui"] == 0.0
    assert rows[0]["ber"] == pytest.approx(equivalent.metrics["ber"])
    assert rows[0]["q_factor_eye"] == pytest.approx(equivalent.metrics["q_factor_eye"])
    assert rows[0]["rx_optical_power_dbm"] == pytest.approx(
        equivalent.budget["rx_optical_power_dbm"]
    )


def test_crosstalk_penalty_coefficient_controls_metric_penalty() -> None:
    cfg = LinkConfig(n_symbols=128)
    off = simulate_wdm(
        cfg=cfg,
        wdm=WDMConfig(crosstalk_penalty_coefficient=0.0, adjacent_crosstalk_db=-20.0),
    )
    on = simulate_wdm(
        cfg=cfg,
        wdm=WDMConfig(crosstalk_penalty_coefficient=10.0, adjacent_crosstalk_db=-20.0),
    )
    assert on[1]["crosstalk_penalty_factor"] > off[1]["crosstalk_penalty_factor"]
    assert on[1]["q_factor_eye"] < off[1]["q_factor_eye"]
