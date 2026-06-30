"""Synthetic measurement datasets."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from photon_link_lab.config import ModulatorConfig
from photon_link_lab.devices import ring_transfer
from photon_link_lab.units import linear_to_db


def generate_fake_ring_measurements(
    path: str | Path,
    mod: ModulatorConfig | None = None,
    seed: int = 13,
    n_wavelengths: int = 161,
    heater_points_mw: tuple[float, ...] = (0.0, 4.0, 8.0, 12.0),
) -> Path:
    mod = mod or ModulatorConfig()
    rng = np.random.default_rng(seed)
    wavelengths = np.linspace(1309.55, 1310.55, n_wavelengths)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "wavelength_nm",
                "heater_mw",
                "measured_transmission_db",
                "true_transmission_db",
            ],
        )
        writer.writeheader()
        for heater in heater_points_mw:
            resonance = mod.resonance_wavelength_nm + heater * mod.tuning_efficiency_nm_per_mw
            for wavelength in wavelengths:
                true_db = linear_to_db(
                    float(ring_transfer(wavelength, mod, resonance_nm=resonance))
                )
                measured_db = true_db + rng.normal(0.0, 0.08)
                writer.writerow(
                    {
                        "wavelength_nm": f"{wavelength:.6f}",
                        "heater_mw": f"{heater:.3f}",
                        "measured_transmission_db": f"{measured_db:.6f}",
                        "true_transmission_db": f"{true_db:.6f}",
                    }
                )
    return path


def read_measurements(path: str | Path) -> dict[str, np.ndarray]:
    columns: dict[str, list[float]] = {}
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for key, value in row.items():
                columns.setdefault(key, []).append(float(value))
    return {key: np.asarray(value, dtype=float) for key, value in columns.items()}
