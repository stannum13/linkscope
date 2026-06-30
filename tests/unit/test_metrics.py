from __future__ import annotations

import pytest

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.metrics import estimate_ber, link_budget


def test_estimate_ber_from_symbol_errors() -> None:
    ber, ser = estimate_ber([0, 1, 2, 3], [0, 1, 1, 3], order=4)
    assert ser == pytest.approx(0.25)
    assert ber == pytest.approx(0.125)


def test_link_budget_has_expected_fields_and_power_trend() -> None:
    low = link_budget(LinkConfig(tx_laser_power_dbm=0.0), ModulatorConfig())
    high = link_budget(LinkConfig(tx_laser_power_dbm=3.0), ModulatorConfig())
    required = {
        "laser_power_dbm",
        "modulator_output_dbm",
        "passive_loss_db",
        "rx_optical_power_dbm",
        "photocurrent_uA",
        "tia_output_mV",
        "static_margin_db",
    }
    assert required.issubset(low)
    assert high["rx_optical_power_dbm"] > low["rx_optical_power_dbm"]
    assert high["photocurrent_uA"] > low["photocurrent_uA"]
