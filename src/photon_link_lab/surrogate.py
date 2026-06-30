"""Deterministic surrogate models for fast BER/Q prediction."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.link import simulate_link

SURROGATE_FORMAT = "photon-link-lab.surrogate.ber-q.v1"

DESIGN_PARAMETER_NAMES = (
    "tx_laser_power_dbm",
    "drive_vpp",
    "thermal_shift_nm",
    "heater_mw",
    "wavelength_nm",
    "driver_noise_vrms",
    "jitter_ui",
    "ring_q_factor",
    "insertion_loss_db",
)

FEATURE_NAMES = (
    "tx_laser_power_dbm",
    "drive_vpp",
    "driver_noise_vrms",
    "jitter_ui",
    "insertion_loss_db",
    "ring_q_factor_1e3",
    "effective_detuning_nm",
    "abs_effective_detuning_nm",
    "effective_detuning_nm_sq",
    "normalized_detuning",
    "abs_normalized_detuning",
    "normalized_detuning_sq",
)

TARGET_NAMES = ("log10_ber", "q_factor_eye")

DEFAULT_DESIGN_RANGES = {
    "tx_laser_power_dbm": (-2.0, 5.0),
    "drive_vpp": (0.45, 1.35),
    "thermal_shift_nm": (-0.25, 0.25),
    "heater_mw": (0.0, 4.0),
    "wavelength_nm": (1309.95, 1310.15),
    "driver_noise_vrms": (0.0, 0.06),
    "jitter_ui": (0.0, 0.03),
    "ring_q_factor": (6000.0, 12000.0),
    "insertion_loss_db": (1.0, 3.0),
}


@dataclass(frozen=True)
class SurrogateSampleSet:
    """Generated simulator samples and transformed surrogate targets."""

    design_parameters: np.ndarray
    features: np.ndarray
    targets: np.ndarray
    simulator_metrics: tuple[dict[str, float], ...]
    design_parameter_names: tuple[str, ...] = DESIGN_PARAMETER_NAMES
    feature_names: tuple[str, ...] = FEATURE_NAMES
    target_names: tuple[str, ...] = TARGET_NAMES

    def rows(self) -> list[dict[str, float]]:
        output = []
        for values, metrics in zip(self.design_parameters, self.simulator_metrics, strict=True):
            row = {
                name: float(value)
                for name, value in zip(self.design_parameter_names, values, strict=True)
            }
            row.update(metrics)
            output.append(row)
        return output


@dataclass(frozen=True)
class SurrogateModel:
    """Standardized ridge model for log10 clipped BER and eye-Q."""

    feature_names: tuple[str, ...]
    target_names: tuple[str, ...]
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    coefficients: np.ndarray
    ridge_alpha: float = 1e-6
    ber_clip_min: float = 1e-5
    ber_clip_max: float = 0.5
    resonance_wavelength_nm: float = 1310.05
    tuning_efficiency_nm_per_mw: float = 0.075

    def predict_features(self, features: np.ndarray) -> np.ndarray:
        return predict_surrogate(self, features)

    def predict_designs(
        self,
        design_parameters: Mapping[str, float]
        | Sequence[Mapping[str, float]]
        | Sequence[float]
        | np.ndarray,
    ) -> dict[str, np.ndarray]:
        design = _design_parameters_array(design_parameters)
        features = _features_from_design_array(
            design,
            self.resonance_wavelength_nm,
            self.tuning_efficiency_nm_per_mw,
        )
        targets = predict_surrogate(self, features)
        log10_ber = targets[:, 0]
        clipped_log10_ber = np.clip(
            log10_ber,
            np.log10(self.ber_clip_min),
            np.log10(self.ber_clip_max),
        )
        return {
            "log10_ber": log10_ber,
            "ber": np.power(10.0, clipped_log10_ber),
            "q_factor_eye": targets[:, 1],
        }

    def predict_one(
        self,
        design_parameters: Mapping[str, float] | Sequence[float],
    ) -> dict[str, float]:
        predictions = self.predict_designs(design_parameters)
        return {name: float(values[0]) for name, values in predictions.items()}

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "format": SURROGATE_FORMAT,
            "feature_names": list(self.feature_names),
            "target_names": list(self.target_names),
            "ridge_alpha": float(self.ridge_alpha),
            "ber_clip": {
                "min": float(self.ber_clip_min),
                "max": float(self.ber_clip_max),
            },
            "feature_mean": _float_list(self.feature_mean),
            "feature_scale": _float_list(self.feature_scale),
            "coefficients": _coefficients_payload(self),
            "feature_reference": {
                "resonance_wavelength_nm": float(self.resonance_wavelength_nm),
                "tuning_efficiency_nm_per_mw": float(self.tuning_efficiency_nm_per_mw),
            },
        }


def sample_design_parameters(
    n_samples: int = 64,
    seed: int = 101,
    design_ranges: Mapping[str, tuple[float, float]] | None = None,
) -> np.ndarray:
    """Generate deterministic Latin-hypercube-style design samples."""

    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    ranges = design_ranges or DEFAULT_DESIGN_RANGES
    missing = set(DESIGN_PARAMETER_NAMES).difference(ranges)
    if missing:
        raise ValueError(f"missing design ranges: {sorted(missing)}")

    rng = np.random.default_rng(seed)
    fractions = (np.arange(n_samples, dtype=float) + 0.5) / n_samples
    columns = []
    for name in DESIGN_PARAMETER_NAMES:
        lo, hi = ranges[name]
        if hi <= lo:
            raise ValueError(f"invalid design range for {name}: {(lo, hi)}")
        columns.append(float(lo) + (float(hi) - float(lo)) * rng.permutation(fractions))
    return np.column_stack(columns)


def design_parameters_to_features(
    design_parameters: Mapping[str, float]
    | Sequence[Mapping[str, float]]
    | Sequence[float]
    | np.ndarray,
    mod: ModulatorConfig | None = None,
) -> np.ndarray:
    """Expand raw design parameters into deterministic linear-model features."""

    reference_mod = mod or ModulatorConfig()
    return _features_from_design_array(
        _design_parameters_array(design_parameters),
        reference_mod.resonance_wavelength_nm,
        reference_mod.tuning_efficiency_nm_per_mw,
    )


def generate_surrogate_samples(
    n_samples: int = 64,
    n_symbols: int = 384,
    seed: int = 101,
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
    samples_per_symbol: int = 8,
    ber_clip_min: float = 1e-5,
    ber_clip_max: float = 0.5,
    design_ranges: Mapping[str, tuple[float, float]] | None = None,
) -> SurrogateSampleSet:
    """Run the simulator over generated design samples for surrogate training."""

    if not 0.0 < ber_clip_min < ber_clip_max:
        raise ValueError("BER clip bounds must satisfy 0 < min < max")
    base_cfg = cfg or LinkConfig()
    base_cfg = base_cfg.with_updates(n_symbols=n_symbols, samples_per_symbol=samples_per_symbol)
    base_mod = mod or ModulatorConfig()
    if base_mod.kind.lower() != "ring":
        raise ValueError("surrogate sample generation currently supports ring modulators")

    design = sample_design_parameters(n_samples, seed=seed, design_ranges=design_ranges)
    features = design_parameters_to_features(design, mod=base_mod)
    targets = np.zeros((n_samples, len(TARGET_NAMES)), dtype=float)
    simulator_metrics: list[dict[str, float]] = []

    for i, row in enumerate(design):
        params = _design_row_dict(row)
        run_cfg = base_cfg.with_updates(
            seed=int(seed * 10_000 + i),
            tx_laser_power_dbm=params["tx_laser_power_dbm"],
            drive_vpp=params["drive_vpp"],
            wavelength_nm=params["wavelength_nm"],
            driver_noise_vrms=params["driver_noise_vrms"],
            jitter_ui=params["jitter_ui"],
        )
        run_mod = ModulatorConfig(
            **{
                **base_mod.__dict__,
                "heater_mw": params["heater_mw"],
                "q_factor": params["ring_q_factor"],
                "insertion_loss_db": params["insertion_loss_db"],
            }
        )
        result = simulate_link(
            run_cfg,
            run_mod,
            thermal_shift_nm=params["thermal_shift_nm"],
        )
        clipped_ber = float(np.clip(result.metrics["ber"], ber_clip_min, ber_clip_max))
        log10_ber = float(np.log10(clipped_ber))
        q_factor_eye = float(result.metrics["q_factor_eye"])
        targets[i] = (log10_ber, q_factor_eye)
        simulator_metrics.append(
            {
                "sample": float(i),
                "ber": float(result.metrics["ber"]),
                "log10_ber": log10_ber,
                "q_factor_eye": q_factor_eye,
                "ser": float(result.metrics["ser"]),
            }
        )

    return SurrogateSampleSet(
        design_parameters=design,
        features=features,
        targets=targets,
        simulator_metrics=tuple(simulator_metrics),
    )


def generate_surrogate_dataset(
    n_samples: int = 48,
    n_symbols: int = 384,
    seed: int = 101,
) -> tuple[np.ndarray, np.ndarray]:
    """Return feature and target arrays for the generated simulator samples."""

    dataset = generate_surrogate_samples(n_samples=n_samples, n_symbols=n_symbols, seed=seed)
    return dataset.features, dataset.targets


def fit_ridge_surrogate(
    features: np.ndarray,
    targets: np.ndarray,
    alpha: float = 1e-6,
    mod: ModulatorConfig | None = None,
    ber_clip_min: float = 1e-5,
    ber_clip_max: float = 0.5,
) -> SurrogateModel:
    """Fit a standardized linear ridge model."""

    if alpha < 0.0:
        raise ValueError("alpha must be non-negative")
    x = _as_2d_float_array(features, len(FEATURE_NAMES), "features")
    y = _as_2d_float_array(targets, len(TARGET_NAMES), "targets")
    mean = np.mean(x, axis=0)
    scale = np.std(x, axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    x_scaled = (x - mean) / scale
    design = np.c_[np.ones(len(x_scaled)), x_scaled]
    penalty = alpha * np.eye(design.shape[1])
    penalty[0, 0] = 0.0
    coeffs = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    reference_mod = mod or ModulatorConfig()
    return SurrogateModel(
        feature_names=FEATURE_NAMES,
        target_names=TARGET_NAMES,
        feature_mean=mean,
        feature_scale=scale,
        coefficients=coeffs,
        ridge_alpha=float(alpha),
        ber_clip_min=float(ber_clip_min),
        ber_clip_max=float(ber_clip_max),
        resonance_wavelength_nm=float(reference_mod.resonance_wavelength_nm),
        tuning_efficiency_nm_per_mw=float(reference_mod.tuning_efficiency_nm_per_mw),
    )


def predict_surrogate(model: SurrogateModel, features: np.ndarray) -> np.ndarray:
    """Predict log10 clipped BER and eye-Q from expanded feature rows."""

    x = _as_2d_float_array(features, len(model.feature_names), "features")
    x_scaled = (x - model.feature_mean) / model.feature_scale
    design = np.c_[np.ones(len(x_scaled)), x_scaled]
    return design @ model.coefficients


def train_test_split_indices(
    n_samples: int,
    test_fraction: float = 0.25,
    seed: int = 101,
) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic train/test row indices."""

    if n_samples < 2:
        raise ValueError("at least two samples are required for a train/test split")
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1")
    rng = np.random.default_rng(seed)
    order = rng.permutation(n_samples)
    test_n = int(round(n_samples * test_fraction))
    test_n = min(max(1, test_n), n_samples - 1)
    return order[test_n:], order[:test_n]


def train_test_surrogate(
    n_samples: int = 48,
    n_symbols: int = 384,
    seed: int = 101,
    test_fraction: float = 0.25,
    split_seed: int | None = None,
    alpha: float = 1e-6,
) -> dict[str, object]:
    """Generate samples, split train/test, fit ridge, and evaluate holdout rows."""

    dataset = generate_surrogate_samples(n_samples=n_samples, n_symbols=n_symbols, seed=seed)
    train_idx, test_idx = train_test_split_indices(
        len(dataset.features),
        test_fraction=test_fraction,
        seed=seed if split_seed is None else split_seed,
    )
    model = fit_ridge_surrogate(
        dataset.features[train_idx],
        dataset.targets[train_idx],
        alpha=alpha,
    )
    train_predictions = predict_surrogate(model, dataset.features[train_idx])
    test_predictions = predict_surrogate(model, dataset.features[test_idx])
    train_metrics = _regression_metrics(dataset.targets[train_idx], train_predictions, TARGET_NAMES)
    test_metrics = _regression_metrics(dataset.targets[test_idx], test_predictions, TARGET_NAMES)
    metrics = {
        "n_samples": int(n_samples),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "train": train_metrics,
        "test": test_metrics,
        "mae_log10_ber": test_metrics["mae"]["log10_ber"],
        "mae_q_factor_eye": test_metrics["mae"]["q_factor_eye"],
        "rmse_log10_ber": test_metrics["rmse"]["log10_ber"],
        "rmse_q_factor_eye": test_metrics["rmse"]["q_factor_eye"],
    }
    return {
        "model": model,
        "dataset": dataset,
        "features": dataset.features,
        "targets": dataset.targets,
        "train_indices": train_idx,
        "test_indices": test_idx,
        "predictions": test_predictions,
        "metrics": metrics,
    }


def surrogate_report_payload(result: Mapping[str, object]) -> dict[str, object]:
    """Return a stable JSON-ready report for a train/test surrogate run."""

    model = result["model"]
    if not isinstance(model, SurrogateModel):
        raise TypeError("result['model'] must be a SurrogateModel")
    metrics = result["metrics"]
    if not isinstance(metrics, Mapping):
        raise TypeError("result['metrics'] must be a mapping")
    return {
        "format": SURROGATE_FORMAT,
        "feature_names": list(model.feature_names),
        "target_names": list(model.target_names),
        "design_parameter_names": list(DESIGN_PARAMETER_NAMES),
        "metrics": dict(metrics),
        "model": model.to_json_dict(),
    }


def write_surrogate_report(path: str | Path, result: Mapping[str, object]) -> Path:
    """Write surrogate report metrics and model coefficients as JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(surrogate_report_payload(result), indent=2, sort_keys=True)
    output_path.write_text(payload + "\n")
    return output_path


def write_surrogate_metrics(path: str | Path, metrics: Mapping[str, Any]) -> Path:
    """Write a metrics-only JSON payload."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    return output_path


def _features_from_design_array(
    design: np.ndarray,
    resonance_wavelength_nm: float,
    tuning_efficiency_nm_per_mw: float,
) -> np.ndarray:
    wavelength_nm = design[:, DESIGN_PARAMETER_NAMES.index("wavelength_nm")]
    heater_mw = design[:, DESIGN_PARAMETER_NAMES.index("heater_mw")]
    thermal_shift_nm = design[:, DESIGN_PARAMETER_NAMES.index("thermal_shift_nm")]
    ring_q_factor = design[:, DESIGN_PARAMETER_NAMES.index("ring_q_factor")]
    resonance_nm = resonance_wavelength_nm + heater_mw * tuning_efficiency_nm_per_mw
    effective_detuning_nm = wavelength_nm - resonance_nm - thermal_shift_nm
    linewidth_nm = np.maximum(resonance_wavelength_nm / ring_q_factor, 1e-12)
    normalized_detuning = effective_detuning_nm / linewidth_nm

    return np.column_stack(
        [
            design[:, DESIGN_PARAMETER_NAMES.index("tx_laser_power_dbm")],
            design[:, DESIGN_PARAMETER_NAMES.index("drive_vpp")],
            design[:, DESIGN_PARAMETER_NAMES.index("driver_noise_vrms")],
            design[:, DESIGN_PARAMETER_NAMES.index("jitter_ui")],
            design[:, DESIGN_PARAMETER_NAMES.index("insertion_loss_db")],
            ring_q_factor / 1000.0,
            effective_detuning_nm,
            np.abs(effective_detuning_nm),
            effective_detuning_nm**2,
            normalized_detuning,
            np.abs(normalized_detuning),
            normalized_detuning**2,
        ]
    )


def _design_parameters_array(
    design_parameters: Mapping[str, float]
    | Sequence[Mapping[str, float]]
    | Sequence[float]
    | np.ndarray,
) -> np.ndarray:
    if isinstance(design_parameters, Mapping):
        return np.asarray(
            [[float(design_parameters[name]) for name in DESIGN_PARAMETER_NAMES]],
            dtype=float,
        )
    if _is_sequence_of_mappings(design_parameters):
        return np.asarray(
            [
                [float(row[name]) for name in DESIGN_PARAMETER_NAMES]
                for row in design_parameters  # type: ignore[union-attr]
            ],
            dtype=float,
        )
    return _as_2d_float_array(design_parameters, len(DESIGN_PARAMETER_NAMES), "design_parameters")


def _is_sequence_of_mappings(value: object) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, str | bytes | np.ndarray)
        and len(value) > 0
        and isinstance(value[0], Mapping)
    )


def _design_row_dict(row: np.ndarray) -> dict[str, float]:
    return {
        name: float(value)
        for name, value in zip(DESIGN_PARAMETER_NAMES, row, strict=True)
    }


def _as_2d_float_array(values: object, n_columns: int, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.ndim != 2 or array.shape[1] != n_columns:
        raise ValueError(f"{name} must have shape (n, {n_columns})")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values")
    return array


def _regression_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    target_names: tuple[str, ...],
) -> dict[str, dict[str, float]]:
    error = np.asarray(predicted, dtype=float) - np.asarray(actual, dtype=float)
    abs_error = np.abs(error)
    return {
        "mae": {
            target: float(value)
            for target, value in zip(target_names, np.mean(abs_error, axis=0), strict=True)
        },
        "rmse": {
            target: float(value)
            for target, value in zip(
                target_names,
                np.sqrt(np.mean(error**2, axis=0)),
                strict=True,
            )
        },
        "max_abs_error": {
            target: float(value)
            for target, value in zip(target_names, np.max(abs_error, axis=0), strict=True)
        },
    }


def _coefficients_payload(model: SurrogateModel) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    for target, values in zip(model.target_names, model.coefficients.T, strict=True):
        rows[target] = {
            "intercept": float(values[0]),
            **{
                feature: float(value)
                for feature, value in zip(model.feature_names, values[1:], strict=True)
            },
        }
    return rows


def _float_list(values: np.ndarray) -> list[float]:
    return [float(value) for value in np.asarray(values, dtype=float)]
