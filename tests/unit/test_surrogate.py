from __future__ import annotations

import json

import numpy as np

from photon_link_lab.surrogate import (
    DESIGN_PARAMETER_NAMES,
    FEATURE_NAMES,
    SURROGATE_FORMAT,
    generate_surrogate_dataset,
    predict_surrogate,
    surrogate_report_payload,
    train_test_surrogate,
    write_surrogate_report,
)


def test_generate_surrogate_dataset_shape_and_finiteness() -> None:
    features, targets = generate_surrogate_dataset(n_samples=6, n_symbols=64, seed=3)
    assert features.shape == (6, len(FEATURE_NAMES))
    assert targets.shape == (6, 2)
    assert np.all(np.isfinite(features))
    assert np.all(np.isfinite(targets))


def test_train_test_surrogate_predicts_finite_targets() -> None:
    result = train_test_surrogate(n_samples=40, n_symbols=128, seed=5, test_fraction=0.25)
    model = result["model"]
    predictions = predict_surrogate(model, result["features"])
    one = model.predict_one(
        {
            "tx_laser_power_dbm": 2.0,
            "drive_vpp": 0.9,
            "thermal_shift_nm": 0.0,
            "heater_mw": 0.0,
            "wavelength_nm": 1310.0,
            "driver_noise_vrms": 0.004,
            "jitter_ui": 0.008,
            "ring_q_factor": 8500.0,
            "insertion_loss_db": 1.8,
        }
    )

    assert predictions.shape == (40, 2)
    assert np.all(np.isfinite(predictions))
    assert set(one) == {"log10_ber", "ber", "q_factor_eye"}
    assert np.isfinite(one["ber"])
    assert np.isfinite(one["q_factor_eye"])
    assert 0.0 < one["ber"] <= 0.5
    assert result["metrics"]["n_train"] == 30
    assert result["metrics"]["n_test"] == 10


def test_surrogate_report_payload_is_json_ready(tmp_path) -> None:
    result = train_test_surrogate(n_samples=40, n_symbols=128, seed=7, test_fraction=0.25)
    payload = surrogate_report_payload(result)
    path = write_surrogate_report(tmp_path / "surrogate_report.json", result)
    loaded = json.loads(path.read_text())

    assert payload["format"] == SURROGATE_FORMAT
    assert loaded["format"] == SURROGATE_FORMAT
    assert payload["feature_names"] == list(FEATURE_NAMES)
    assert payload["design_parameter_names"] == list(DESIGN_PARAMETER_NAMES)
    assert payload["target_names"] == ["log10_ber", "q_factor_eye"]
    assert set(payload["metrics"]["train"]) == {"mae", "rmse", "max_abs_error"}
    assert set(payload["metrics"]["test"]) == {"mae", "rmse", "max_abs_error"}
    assert set(payload["metrics"]["test"]["mae"]) == {"log10_ber", "q_factor_eye"}
    assert set(payload["model"]["coefficients"]) == {"log10_ber", "q_factor_eye"}


def test_surrogate_held_out_error_sanity() -> None:
    result = train_test_surrogate(
        n_samples=64,
        n_symbols=256,
        seed=11,
        split_seed=22,
        test_fraction=0.25,
    )
    test_metrics = result["metrics"]["test"]

    assert result["metrics"]["n_train"] == 48
    assert result["metrics"]["n_test"] == 16
    assert test_metrics["mae"]["log10_ber"] < 0.35
    assert test_metrics["mae"]["q_factor_eye"] < 0.35
