from __future__ import annotations

import pytest

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.metrics import ber_confidence_metrics, estimate_ber, link_budget


def test_estimate_ber_from_symbol_errors() -> None:
    ber, ser = estimate_ber([0, 1, 2, 3], [2, 1, 2, 3], order=4)
    assert ser == pytest.approx(0.25)
    assert ber == pytest.approx(0.25)


def test_ber_proxy_is_separate_from_gray_bit_counted_ber() -> None:
    metrics = ber_confidence_metrics([0, 1, 2, 3], [2, 1, 2, 3], order=4)
    assert metrics["symbol_errors"] == 1.0
    assert metrics["bit_errors"] == 2.0
    assert metrics["ser"] == pytest.approx(0.25)
    assert metrics["ber_proxy"] == pytest.approx(0.125)
    assert metrics["ber"] == pytest.approx(0.25)


def test_ber_confidence_reports_zero_error_upper_bound() -> None:
    metrics = ber_confidence_metrics([0, 1, 2, 3] * 32, [0, 1, 2, 3] * 32, order=4)
    assert metrics["ber"] == 0.0
    assert metrics["symbol_errors"] == 0.0
    assert metrics["bit_errors"] == 0.0
    assert 0.0 < metrics["ber_upper_95"] < 0.02
    assert metrics["ber_observation_floor"] == pytest.approx(1.0 / (128 * 2))


def test_ber_confidence_upper_bound_increases_with_errors() -> None:
    clean = ber_confidence_metrics([0, 1, 2, 3] * 32, [0, 1, 2, 3] * 32, order=4)
    errored = ber_confidence_metrics([0, 1, 2, 3] * 32, [1, 1, 2, 3] * 32, order=4)
    assert errored["ber"] > clean["ber"]
    assert errored["ber_upper_95"] > clean["ber_upper_95"]
    assert errored["fec_margin_db"] < clean["fec_margin_db"]


def test_ber_confidence_custom_confidence_suffix_for_empty_input() -> None:
    metrics = ber_confidence_metrics([], [], order=4, confidence=0.9)
    assert "ber_upper_90" in metrics
    assert "fec_pass_upper_90" in metrics


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
