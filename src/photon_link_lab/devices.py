"""Behavioral photonic and electrical device models."""

from __future__ import annotations

import math

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.filters import first_order_lowpass
from photon_link_lab.units import db_to_linear, dbm_to_w

E_CHARGE = 1.602176634e-19


def ring_transfer(
    wavelength_nm: np.ndarray | float,
    mod: ModulatorConfig,
    resonance_nm: np.ndarray | float | None = None,
) -> np.ndarray:
    """Lorentzian microring notch transfer in linear power units."""

    wl = np.asarray(wavelength_nm, dtype=float)
    resonance = np.asarray(
        mod.resonance_wavelength_nm if resonance_nm is None else resonance_nm,
        dtype=float,
    )
    linewidth_nm = np.maximum(resonance / mod.q_factor, 1e-12)
    depth = 1.0 - db_to_linear(-mod.extinction_ratio_db)
    detuning = (wl - resonance) / linewidth_nm
    through = 1.0 - depth / (1.0 + (2.0 * detuning) ** 2)
    return db_to_linear(-mod.insertion_loss_db) * np.clip(through, 1e-6, 1.0)


def ring_derived_metrics(mod: ModulatorConfig) -> dict[str, float]:
    """Return derived microring quantities used by docs, CLI output, and tests."""

    linewidth_nm = mod.resonance_wavelength_nm / mod.q_factor
    c_m_per_s = 299_792_458.0
    wavelength_m = mod.resonance_wavelength_nm * 1e-9
    linewidth_m = linewidth_nm * 1e-9
    linewidth_ghz = c_m_per_s * linewidth_m / (wavelength_m**2) / 1e9
    return {
        "linewidth_nm": float(linewidth_nm),
        "linewidth_ghz": float(linewidth_ghz),
        "fsr_nm": float(mod.fsr_nm),
        "finesse": float(mod.fsr_nm / linewidth_nm),
    }


def mzi_transfer(voltage_v: np.ndarray, mod: ModulatorConfig) -> np.ndarray:
    phase = math.pi * np.asarray(voltage_v, dtype=float) / mod.vpi_v + mod.phase_bias_rad
    through = 0.5 * (1.0 + np.cos(phase))
    er_floor = db_to_linear(-mod.extinction_ratio_db)
    through = er_floor + (1.0 - er_floor) * through
    return db_to_linear(-mod.insertion_loss_db) * np.clip(through, 1e-6, 1.0)


def driver(symbol_waveform: np.ndarray, cfg: LinkConfig, rng: np.random.Generator) -> np.ndarray:
    sample_rate_hz = cfg.symbol_rate_gbaud * 1e9 * cfg.samples_per_symbol
    voltage = 0.5 * cfg.drive_vpp * np.asarray(symbol_waveform, dtype=float)
    voltage = first_order_lowpass(voltage, cfg.driver_bandwidth_ghz * 1e9, sample_rate_hz)
    if cfg.driver_noise_vrms > 0:
        voltage = voltage + rng.normal(0.0, cfg.driver_noise_vrms, size=voltage.shape)
    return voltage


def apply_variation(
    mod: ModulatorConfig,
    link: LinkConfig,
    variation: VariationConfig | None,
    rng: np.random.Generator,
) -> tuple[ModulatorConfig, LinkConfig]:
    if variation is None:
        return mod, link
    resonance_shift = (
        rng.normal(0.0, variation.wavelength_sigma_nm)
        + variation.die_to_die_offset_nm
        + variation.wafer_gradient_nm
    )
    q_factor = mod.q_factor * max(0.25, 1.0 + rng.normal(0.0, variation.q_sigma_fraction))
    insertion_loss_db = max(0.0, mod.insertion_loss_db + rng.normal(0.0, variation.loss_sigma_db))
    responsivity = link.responsivity_a_per_w * max(
        0.1, 1.0 + rng.normal(0.0, variation.responsivity_sigma_fraction)
    )
    return (
        ModulatorConfig(
            **{
                **mod.__dict__,
                "resonance_wavelength_nm": mod.resonance_wavelength_nm + resonance_shift,
                "q_factor": q_factor,
                "insertion_loss_db": insertion_loss_db,
            }
        ),
        link.with_updates(responsivity_a_per_w=responsivity),
    )


def modulate(
    voltage_v: np.ndarray,
    cfg: LinkConfig,
    mod: ModulatorConfig,
    thermal_shift_nm: float = 0.0,
) -> np.ndarray:
    laser_power_w = dbm_to_w(cfg.tx_laser_power_dbm)
    if mod.kind.lower() == "mzi":
        transmission = mzi_transfer(voltage_v, mod)
    elif mod.kind.lower() == "ring":
        heater_shift_nm = (
            np.clip(mod.heater_mw, 0.0, mod.heater_max_mw)
            * mod.tuning_efficiency_nm_per_mw
        )
        voltage_shift_nm = np.asarray(voltage_v) * mod.voltage_tuning_nm_per_v
        resonance_nm = (
            mod.resonance_wavelength_nm
            + heater_shift_nm
            + thermal_shift_nm
            + voltage_shift_nm
        )
        transmission = ring_transfer(cfg.wavelength_nm, mod, resonance_nm=resonance_nm)
    else:
        raise ValueError(f"unsupported modulator kind: {mod.kind}")
    return laser_power_w * transmission


def channel_loss(optical_power_w: np.ndarray, cfg: LinkConfig) -> np.ndarray:
    total_loss_db = cfg.waveguide_loss_db + cfg.fiber_loss_db + cfg.connector_loss_db
    return np.asarray(optical_power_w, dtype=float) * db_to_linear(-total_loss_db)


def photodiode_tia(
    optical_power_w: np.ndarray,
    cfg: LinkConfig,
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, float]]:
    current_a = cfg.responsivity_a_per_w * np.asarray(optical_power_w, dtype=float)
    sample_rate_hz = cfg.symbol_rate_gbaud * 1e9 * cfg.samples_per_symbol
    noise_var = cfg.thermal_noise_a_rms**2
    bandwidth_hz = cfg.rx_bandwidth_ghz * 1e9
    mean_current = np.mean(np.maximum(current_a, 0))
    shot_sigma = float(
        np.sqrt(np.maximum(2.0 * E_CHARGE * mean_current * bandwidth_hz, 0))
    )
    rin_linear = 10.0 ** (cfg.rin_db_per_hz / 10.0)
    rin_sigma = float(mean_current * np.sqrt(max(rin_linear * bandwidth_hz, 0.0)))
    noise_var += shot_sigma**2 + rin_sigma**2
    noisy_current = current_a + rng.normal(0.0, math.sqrt(noise_var), size=current_a.shape)
    voltage = noisy_current * cfg.tia_gain_ohm
    voltage = first_order_lowpass(voltage, cfg.rx_bandwidth_ghz * 1e9, sample_rate_hz)
    return voltage, {
        "mean_current_a": float(np.mean(current_a)),
        "shot_noise_a_rms": shot_sigma,
        "rin_noise_a_rms": rin_sigma,
        "total_noise_a_rms": math.sqrt(noise_var),
    }
