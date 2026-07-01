"""Metrics and link-budget calculations."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.devices import ring_transfer
from photon_link_lab.units import db_to_linear, linear_to_db, w_to_dbm


def estimate_ber(tx_indices: np.ndarray, rx_indices: np.ndarray, order: int) -> tuple[float, float]:
    n = min(len(tx_indices), len(rx_indices))
    if n == 0:
        return 0.0, 0.0
    symbol_errors = np.count_nonzero(np.asarray(tx_indices[:n]) != np.asarray(rx_indices[:n]))
    ser = symbol_errors / n
    ber = ser / max(1.0, math.log2(order))
    return float(ber), float(ser)


def ber_confidence_metrics(
    tx_indices: np.ndarray,
    rx_indices: np.ndarray,
    order: int,
    confidence: float = 0.95,
    fec_threshold_ber: float = 2e-4,
) -> dict[str, float]:
    """Return empirical BER/SER plus a Wilson upper confidence bound.

    The simulator makes hard symbol decisions, so BER is estimated from symbol
    errors divided by bits/symbol. The upper bound is computed on SER and then
    mapped to BER by the same convention. It is intentionally conservative for
    short smoke-test runs where zero observed errors do not imply zero BER.
    """

    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if fec_threshold_ber <= 0.0:
        raise ValueError("fec_threshold_ber must be positive")

    n = min(len(tx_indices), len(rx_indices))
    bits_per_symbol = max(1.0, math.log2(order))
    suffix = int(round(confidence * 100))
    if n == 0:
        return {
            "symbol_count": 0.0,
            "symbol_errors": 0.0,
            "bits_per_symbol": bits_per_symbol,
            "ser": 0.0,
            "ber": 0.0,
            f"ser_upper_{suffix}": 1.0,
            f"ber_upper_{suffix}": 1.0 / bits_per_symbol,
            "ber_observation_floor": float("inf"),
            "fec_threshold_ber": fec_threshold_ber,
            "fec_margin_db": float("-inf"),
            f"fec_pass_upper_{suffix}": 0.0,
        }

    tx = np.asarray(tx_indices[:n])
    rx = np.asarray(rx_indices[:n])
    symbol_errors = int(np.count_nonzero(tx != rx))
    ser = symbol_errors / n
    ber = ser / bits_per_symbol
    ser_upper = _wilson_upper_bound(symbol_errors, n, confidence)
    ber_upper = ser_upper / bits_per_symbol
    fec_margin_db = 10.0 * math.log10(fec_threshold_ber / max(ber_upper, 1e-30))
    return {
        "symbol_count": float(n),
        "symbol_errors": float(symbol_errors),
        "bits_per_symbol": bits_per_symbol,
        "ser": float(ser),
        "ber": float(ber),
        f"ser_upper_{suffix}": float(ser_upper),
        f"ber_upper_{suffix}": float(ber_upper),
        "ber_observation_floor": float(1.0 / (n * bits_per_symbol)),
        "fec_threshold_ber": float(fec_threshold_ber),
        "fec_margin_db": float(fec_margin_db),
        f"fec_pass_upper_{suffix}": float(ber_upper <= fec_threshold_ber),
    }


def _wilson_upper_bound(errors: int, trials: int, confidence: float) -> float:
    if trials <= 0:
        return 1.0
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    p_hat = errors / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (p_hat + z2 / (2.0 * trials)) / denominator
    radius = z * math.sqrt(
        (p_hat * (1.0 - p_hat) / trials) + (z2 / (4.0 * trials * trials))
    ) / denominator
    return min(1.0, max(0.0, center + radius))


def eye_metrics(samples: np.ndarray, tx_indices: np.ndarray, order: int) -> dict[str, float]:
    x = np.asarray(samples, dtype=float)
    idx = np.asarray(tx_indices)
    means = []
    sigmas = []
    for level in range(order):
        bucket = x[idx[: len(x)] == level]
        if len(bucket) == 0:
            means.append(float("nan"))
            sigmas.append(float("nan"))
        else:
            means.append(float(np.mean(bucket)))
            sigmas.append(float(np.std(bucket) + 1e-15))
    openings = []
    q_values = []
    for i in range(order - 1):
        opening = means[i + 1] - means[i]
        sigma_sum = sigmas[i + 1] + sigmas[i]
        openings.append(opening)
        q_values.append(opening / max(sigma_sum, 1e-15))
    return {
        "min_eye_opening": float(np.nanmin(openings)),
        "mean_eye_opening": float(np.nanmean(openings)),
        "q_factor_eye": float(np.nanmin(q_values)),
    }


def link_budget(cfg: LinkConfig, mod: ModulatorConfig) -> dict[str, float]:
    tx_w = 1e-3 * db_to_linear(cfg.tx_laser_power_dbm)
    if mod.kind.lower() == "ring":
        mod_tx = tx_w * float(ring_transfer(cfg.wavelength_nm, mod))
    else:
        mod_tx = tx_w * db_to_linear(-mod.insertion_loss_db) * 0.5
    passive_loss_db = cfg.waveguide_loss_db + cfg.fiber_loss_db + cfg.connector_loss_db
    rx_w = mod_tx * db_to_linear(-passive_loss_db)
    current_a = rx_w * cfg.responsivity_a_per_w
    return {
        "laser_power_dbm": cfg.tx_laser_power_dbm,
        "modulator_output_dbm": w_to_dbm(mod_tx),
        "passive_loss_db": passive_loss_db,
        "rx_optical_power_dbm": w_to_dbm(rx_w),
        "photocurrent_uA": current_a * 1e6,
        "tia_output_mV": current_a * cfg.tia_gain_ohm * 1e3,
        "static_margin_db": linear_to_db(max(current_a / 20e-6, 1e-12)),
    }
