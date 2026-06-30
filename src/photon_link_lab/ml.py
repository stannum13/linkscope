"""Small ML/AI tuning utilities layered on the physical simulator."""

from __future__ import annotations

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.link import simulate_link


def bayesian_like_heater_search(
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
    candidates_mw: np.ndarray | None = None,
    thermal_shift_nm: float = 0.0,
) -> dict[str, float]:
    """Deterministic acquisition-style search for heater locking.

    This keeps dependencies light while exposing the same interface a Gaussian
    process optimizer could replace. It samples coarse candidates, then refines
    around the best measured BER/Q point.
    """

    cfg = cfg or LinkConfig(n_symbols=2048)
    mod = mod or ModulatorConfig()
    if candidates_mw is None:
        candidates_mw = np.linspace(0.0, mod.heater_max_mw, 13)
    observations = []
    for heater in candidates_mw:
        candidate_mod = ModulatorConfig(**{**mod.__dict__, "heater_mw": float(heater)})
        result = simulate_link(cfg, candidate_mod, thermal_shift_nm=thermal_shift_nm)
        score = result.metrics["q_factor_eye"] - 1000.0 * result.metrics["ber"]
        observations.append((float(heater), float(score), float(result.metrics["ber"])))
    best_heater, _, best_ber = max(observations, key=lambda item: item[1])
    lo = max(0.0, best_heater - mod.heater_max_mw / 8.0)
    hi = min(mod.heater_max_mw, best_heater + mod.heater_max_mw / 8.0)
    for heater in np.linspace(lo, hi, 9):
        candidate_mod = ModulatorConfig(**{**mod.__dict__, "heater_mw": float(heater)})
        result = simulate_link(cfg, candidate_mod, thermal_shift_nm=thermal_shift_nm)
        score = result.metrics["q_factor_eye"] - 1000.0 * result.metrics["ber"]
        observations.append((float(heater), float(score), float(result.metrics["ber"])))
    best_heater, best_score, best_ber = max(observations, key=lambda item: item[1])
    return {
        "heater_mw": best_heater,
        "score": best_score,
        "ber": best_ber,
        "observations": float(len(observations)),
    }
