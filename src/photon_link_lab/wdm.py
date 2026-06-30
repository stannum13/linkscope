"""Wavelength-division multiplexing behavioral helpers."""

from __future__ import annotations

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, WDMConfig
from photon_link_lab.link import simulate_link
from photon_link_lab.units import db_to_linear, linear_to_db


def channel_wavelengths_nm(config: WDMConfig) -> np.ndarray:
    """Return channel wavelengths centered around `center_wavelength_nm`."""

    c_m_per_s = 299_792_458.0
    center_m = config.center_wavelength_nm * 1e-9
    spacing_m = (center_m**2 / c_m_per_s) * config.channel_spacing_ghz * 1e9
    spacing_nm = spacing_m * 1e9
    offsets = np.arange(config.n_channels) - (config.n_channels - 1) / 2.0
    return config.center_wavelength_nm + offsets * spacing_nm


def crosstalk_matrix(config: WDMConfig) -> np.ndarray:
    """Return a linear-power crosstalk matrix with mux insertion loss."""

    if config.n_channels < 1:
        raise ValueError("WDM n_channels must be at least 1")
    matrix = np.zeros((config.n_channels, config.n_channels), dtype=float)
    diag = db_to_linear(-config.mux_loss_db)
    adjacent = db_to_linear(config.adjacent_crosstalk_db)
    nonadjacent = db_to_linear(config.nonadjacent_crosstalk_db)
    for i in range(config.n_channels):
        for j in range(config.n_channels):
            if i == j:
                matrix[i, j] = diag
            elif abs(i - j) == 1:
                matrix[i, j] = adjacent
            else:
                matrix[i, j] = nonadjacent
    return matrix


def dispersion_band_skew_ui(config: WDMConfig, symbol_rate_gbaud: float) -> float:
    """First-order WDM lane-to-lane skew estimate in unit intervals."""

    wavelengths = channel_wavelengths_nm(config)
    spectral_width_nm = (
        float(np.max(wavelengths) - np.min(wavelengths)) if len(wavelengths) else 0.0
    )
    spread_ps = (
        abs(config.dispersion_ps_per_nm_km)
        * spectral_width_nm
        * max(config.fiber_length_km, 0.0)
    )
    ui_ps = 1e3 / symbol_rate_gbaud
    return float(spread_ps / ui_ps) if ui_ps > 0 else 0.0


def simulate_wdm(
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
    wdm: WDMConfig | None = None,
) -> list[dict[str, float]]:
    """Simulate per-channel link metrics and attach WDM impairment summaries."""

    cfg = cfg or LinkConfig(n_symbols=1024)
    mod = mod or ModulatorConfig()
    wdm = wdm or WDMConfig()
    wavelengths = channel_wavelengths_nm(wdm)
    matrix = crosstalk_matrix(wdm)
    band_skew_ui = dispersion_band_skew_ui(wdm, cfg.symbol_rate_gbaud)
    rows = []
    nominal_detuning_nm = mod.resonance_wavelength_nm - cfg.wavelength_nm
    for channel, wavelength in enumerate(wavelengths):
        channel_cfg = cfg.with_updates(
            wavelength_nm=float(wavelength),
            seed=cfg.seed + channel,
            connector_loss_db=cfg.connector_loss_db + wdm.mux_loss_db,
        )
        channel_mod = ModulatorConfig(
            **{
                **mod.__dict__,
                "resonance_wavelength_nm": float(wavelength + nominal_detuning_nm),
            }
        )
        result = simulate_link(channel_cfg, channel_mod)
        desired = matrix[channel, channel]
        leakage = float(np.sum(matrix[channel]) - desired)
        crosstalk_ratio = leakage / max(desired, 1e-15)
        penalty = 1.0 + wdm.crosstalk_penalty_coefficient * crosstalk_ratio
        rows.append(
            {
                "channel": float(channel),
                "wavelength_nm": float(wavelength),
                "rx_optical_power_dbm": result.budget["rx_optical_power_dbm"],
                "ber": min(0.5, result.metrics["ber"] * penalty),
                "q_factor_eye": result.metrics["q_factor_eye"] / penalty,
                "crosstalk_power_ratio": crosstalk_ratio,
                "crosstalk_penalty_factor": penalty,
                "crosstalk_penalty_db": linear_to_db(penalty),
                "dispersion_band_skew_ui": band_skew_ui,
            }
        )
    return rows
