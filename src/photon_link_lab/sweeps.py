"""Parameter sweeps for architecture exploration."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.link import simulate_link


def sweep_tx_power(
    powers_dbm: list[float] | np.ndarray,
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
) -> list[dict[str, float]]:
    cfg = cfg or LinkConfig()
    rows = []
    for power in powers_dbm:
        result = simulate_link(cfg.with_updates(tx_laser_power_dbm=float(power)), mod)
        rows.append(
            {
                "tx_laser_power_dbm": float(power),
                "ber": result.metrics["ber"],
                "ser": result.metrics["ser"],
                "q_factor_eye": result.metrics["q_factor_eye"],
                "rx_optical_power_dbm": result.budget["rx_optical_power_dbm"],
                "photocurrent_uA": result.budget["photocurrent_uA"],
            }
        )
    return rows


def sweep_thermal_drift(
    drifts_nm: list[float] | np.ndarray,
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
) -> list[dict[str, float]]:
    cfg = cfg or LinkConfig()
    rows = []
    for drift in drifts_nm:
        result = simulate_link(cfg, mod, thermal_shift_nm=float(drift))
        rows.append(
            {
                "thermal_shift_nm": float(drift),
                "ber": result.metrics["ber"],
                "ser": result.metrics["ser"],
                "q_factor_eye": result.metrics["q_factor_eye"],
                "rx_voltage_pp_mV": result.metrics["rx_voltage_pp_mV"],
            }
        )
    return rows


def monte_carlo_yield(
    n: int = 64,
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
    variation: VariationConfig | None = None,
    ber_limit: float = 1e-3,
) -> list[dict[str, float]]:
    cfg = cfg or LinkConfig(n_symbols=2048)
    variation = variation or VariationConfig()
    rows = []
    for i in range(n):
        run_cfg = cfg.with_updates(seed=cfg.seed + i)
        result = simulate_link(run_cfg, mod, variation=variation)
        rows.append(
            {
                "sample": float(i),
                "ber": result.metrics["ber"],
                "q_factor_eye": result.metrics["q_factor_eye"],
                "pass": float(result.metrics["ber"] <= ber_limit),
            }
        )
    return rows


def write_csv(path: str | Path, rows: list[dict[str, float]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty sweep")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
