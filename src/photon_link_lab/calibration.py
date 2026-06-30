"""Calibration routines for fitting physical model parameters."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from photon_link_lab.config import CalibrationResult, ModulatorConfig
from photon_link_lab.datasets import read_measurements
from photon_link_lab.devices import ring_transfer
from photon_link_lab.units import linear_to_db


def fit_ring_from_measurements(
    path: str | Path,
    initial: ModulatorConfig | None = None,
) -> CalibrationResult:
    data = read_measurements(path)
    initial = initial or ModulatorConfig()
    wavelength = data["wavelength_nm"]
    heater = data["heater_mw"]
    measured_db = data["measured_transmission_db"]

    def residual(params: np.ndarray) -> np.ndarray:
        insertion_loss_db, extinction_ratio_db, q_factor, resonance_nm = params
        mod = ModulatorConfig(
            **{
                **initial.__dict__,
                "insertion_loss_db": float(insertion_loss_db),
                "extinction_ratio_db": float(extinction_ratio_db),
                "q_factor": float(q_factor),
                "resonance_wavelength_nm": float(resonance_nm),
            }
        )
        predicted = []
        for wl, h in zip(wavelength, heater, strict=False):
            resonance = mod.resonance_wavelength_nm + h * mod.tuning_efficiency_nm_per_mw
            predicted.append(linear_to_db(float(ring_transfer(wl, mod, resonance_nm=resonance))))
        return np.asarray(predicted) - measured_db

    x0 = np.asarray(
        [
            initial.insertion_loss_db,
            initial.extinction_ratio_db,
            initial.q_factor,
            initial.resonance_wavelength_nm,
        ],
        dtype=float,
    )
    fit = least_squares(
        residual,
        x0,
        bounds=([0.05, 1.0, 1000.0, 1308.0], [8.0, 20.0, 40000.0, 1312.0]),
        loss="soft_l1",
    )
    rmse = float(np.sqrt(np.mean(residual(fit.x) ** 2)))
    return CalibrationResult(
        insertion_loss_db=float(fit.x[0]),
        extinction_ratio_db=float(fit.x[1]),
        q_factor=float(fit.x[2]),
        resonance_wavelength_nm=float(fit.x[3]),
        rmse_db=rmse,
        n_points=len(measured_db),
    )


def write_calibration(path: str | Path, result: CalibrationResult) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(result.__dict__, indent=2) + "\n")
