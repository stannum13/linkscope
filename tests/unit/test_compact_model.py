from __future__ import annotations

import json

import pytest

from photon_link_lab.compact_model import (
    COMPACT_MODEL_FORMAT,
    LEGACY_COMPACT_FORMAT,
    compact_model_to_verilog_a,
    export_compact_model,
    export_verilog_a_model,
    load_compact_model,
)
from photon_link_lab.config import LinkConfig, ModulatorConfig


def test_compact_model_round_trip(tmp_path) -> None:
    cfg = LinkConfig(
        pam_order=2,
        n_symbols=123,
        tx_laser_power_dbm=1.5,
        responsivity_a_per_w=0.7,
    )
    mod = ModulatorConfig(kind="ring", q_factor=9000.0, heater_mw=3.0)
    path = export_compact_model(tmp_path / "compact.json", cfg, mod)
    assert path.read_text().count(COMPACT_MODEL_FORMAT) == 1

    loaded_cfg, loaded_mod = load_compact_model(path)
    assert loaded_cfg.pam_order == 2
    assert loaded_cfg.n_symbols == 123
    assert loaded_cfg.tx_laser_power_dbm == pytest.approx(1.5)
    assert loaded_cfg.responsivity_a_per_w == pytest.approx(0.7)
    assert loaded_mod.q_factor == pytest.approx(9000.0)
    assert loaded_mod.heater_mw == pytest.approx(3.0)


def test_load_compact_model_supports_v1_compact_link_subset(tmp_path) -> None:
    path = tmp_path / "legacy_compact.json"
    path.write_text(
        json.dumps(
            {
                "format": LEGACY_COMPACT_FORMAT,
                "model": {
                    "modulator": {"kind": "mzi", "vpi_v": 1.4},
                    "link": {
                        "symbol_rate_gbaud": 64.0,
                        "responsivity_a_per_w": 0.72,
                        "rx_bandwidth_ghz": 31.0,
                        "driver_bandwidth_ghz": 29.0,
                        "losses_db": {
                            "waveguide": 1.1,
                            "fiber": 0.7,
                            "connector": 0.5,
                        },
                    },
                },
            }
        )
    )

    loaded_cfg, loaded_mod = load_compact_model(path)
    assert loaded_cfg.symbol_rate_gbaud == pytest.approx(64.0)
    assert loaded_cfg.responsivity_a_per_w == pytest.approx(0.72)
    assert loaded_cfg.waveguide_loss_db == pytest.approx(1.1)
    assert loaded_cfg.pam_order == LinkConfig().pam_order
    assert loaded_mod.kind == "mzi"
    assert loaded_mod.vpi_v == pytest.approx(1.4)


def test_ring_verilog_a_export_contains_key_parameters_and_units(tmp_path) -> None:
    cfg = LinkConfig(symbol_rate_gbaud=64.0, responsivity_a_per_w=0.9)
    mod = ModulatorConfig(
        q_factor=9100.0,
        resonance_wavelength_nm=1311.2,
        tuning_efficiency_nm_per_mw=0.081,
        voltage_tuning_nm_per_v=0.052,
    )
    path = export_verilog_a_model(tmp_path / "ring_behavioral.va", cfg, mod)
    text = path.read_text()
    assert "LinkScope behavioral compact model" in text
    assert "modulator_kind: ring" in text
    assert "symbol_rate_gbaud = 64; // Gbaud" in text
    assert "responsivity_a_per_w = 0.9; // A/W" in text
    assert "resonance_wavelength_nm = 1311.2; // nm" in text
    assert "q_factor = 9100; // unitless" in text
    assert "tuning_efficiency_nm_per_mw = 0.081; // nm/mW" in text
    assert "voltage_tuning_nm_per_v = 0.052; // nm/V" in text
    assert "Ring equation" in text


def test_mzi_verilog_a_text_contains_key_parameters_and_units() -> None:
    mod = ModulatorConfig(kind="mzi", vpi_v=1.35, phase_bias_rad=0.25)
    text = compact_model_to_verilog_a(LinkConfig(), mod)
    assert "modulator_kind: mzi" in text
    assert "vpi_v = 1.35; // V" in text
    assert "phase_bias_rad = 0.25; // rad" in text
    assert "phase_noise_rad = 0; // rad" in text
    assert "MZI equation" in text
