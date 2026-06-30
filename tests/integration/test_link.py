from __future__ import annotations

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.link import simulate_link
from photon_link_lab.sweeps import monte_carlo_yield, sweep_thermal_drift, sweep_tx_power


def test_simulate_link_ring_and_mzi_are_finite() -> None:
    for kind in ["ring", "mzi"]:
        result = simulate_link(LinkConfig(n_symbols=256), ModulatorConfig(kind=kind))
        assert len(result.sampled_v) == 256
        assert len(result.equalized_symbols) == 256
        assert np.isfinite(result.metrics["ber"])
        assert np.isfinite(result.metrics["q_factor_eye"])
        assert np.isfinite(result.budget["rx_optical_power_dbm"])


def test_simulate_link_supports_nrz() -> None:
    result = simulate_link(LinkConfig(n_symbols=256, pam_order=2), ModulatorConfig())
    assert result.metrics["line_rate_gbps"] == 56.0
    assert set(result.rx_indices).issubset({0, 1})


def test_sweeps_have_stable_schema() -> None:
    power = sweep_tx_power([-2.0, 0.0], cfg=LinkConfig(n_symbols=128))
    drift = sweep_thermal_drift([-0.05, 0.0, 0.05], cfg=LinkConfig(n_symbols=128))
    yield_rows = monte_carlo_yield(
        n=3,
        cfg=LinkConfig(n_symbols=128),
        variation=VariationConfig(wavelength_sigma_nm=0.01),
    )
    assert set(power[0]) == {
        "tx_laser_power_dbm",
        "ber",
        "ser",
        "q_factor_eye",
        "rx_optical_power_dbm",
        "photocurrent_uA",
    }
    assert "thermal_shift_nm" in drift[0]
    assert set(yield_rows[0]) == {"sample", "ber", "q_factor_eye", "pass"}
