"""Metrics and link-budget calculations."""

from __future__ import annotations

import math

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
