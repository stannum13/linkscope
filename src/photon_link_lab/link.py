"""End-to-end optical link simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.devices import apply_variation, channel_loss, driver, modulate, photodiode_tia
from photon_link_lab.equalizer import apply_ffe, decide_pam, fit_ffe
from photon_link_lab.filters import apply_jitter_like_noise, quantize
from photon_link_lab.metrics import estimate_ber, eye_metrics, link_budget
from photon_link_lab.symbols import generate_symbols, sample_at_symbols, upsample


@dataclass
class LinkResult:
    tx_indices: np.ndarray
    tx_symbols: np.ndarray
    driver_voltage_v: np.ndarray
    optical_power_w: np.ndarray
    rx_voltage_v: np.ndarray
    sampled_v: np.ndarray
    equalized_symbols: np.ndarray
    rx_indices: np.ndarray
    metrics: dict[str, float]
    budget: dict[str, float]
    equalizer_coeffs: np.ndarray


def simulate_link(
    cfg: LinkConfig | None = None,
    mod: ModulatorConfig | None = None,
    variation: VariationConfig | None = None,
    thermal_shift_nm: float = 0.0,
) -> LinkResult:
    cfg = cfg or LinkConfig()
    mod = mod or ModulatorConfig()
    rng = np.random.default_rng(cfg.seed)
    mod, cfg = apply_variation(mod, cfg, variation, rng)

    tx_indices, tx_symbols = generate_symbols(cfg.n_symbols, cfg.pam_order, cfg.seed)
    symbol_waveform = upsample(tx_symbols, cfg.samples_per_symbol)
    voltage = driver(symbol_waveform, cfg, rng)
    optical = modulate(voltage, cfg, mod, thermal_shift_nm=thermal_shift_nm)
    optical = channel_loss(optical, cfg)
    rx_voltage, noise_metrics = photodiode_tia(optical, cfg, rng)
    rx_voltage = apply_jitter_like_noise(rx_voltage, cfg.samples_per_symbol, cfg.jitter_ui, rng)
    rx_voltage = quantize(rx_voltage, cfg.quantization_bits)

    sampled = sample_at_symbols(rx_voltage, cfg.samples_per_symbol)[: cfg.n_symbols]
    train_n = max(cfg.equalizer_taps * 3, int(len(sampled) * cfg.training_fraction))
    coeffs = fit_ffe(sampled[:train_n], tx_symbols[:train_n], cfg.equalizer_taps)
    equalized = apply_ffe(sampled, coeffs)
    rx_indices, _ = decide_pam(equalized, cfg.pam_order)
    ber, ser = estimate_ber(tx_indices, rx_indices, cfg.pam_order)
    eye = eye_metrics(equalized, tx_indices[: len(equalized)], cfg.pam_order)
    metrics = {
        "ber": ber,
        "ser": ser,
        "symbol_rate_gbaud": cfg.symbol_rate_gbaud,
        "line_rate_gbps": cfg.symbol_rate_gbaud * np.log2(cfg.pam_order),
        "rx_voltage_pp_mV": float((np.max(rx_voltage) - np.min(rx_voltage)) * 1e3),
        "equalizer_taps": float(cfg.equalizer_taps),
        **eye,
        **noise_metrics,
    }
    return LinkResult(
        tx_indices=tx_indices,
        tx_symbols=tx_symbols,
        driver_voltage_v=voltage,
        optical_power_w=optical,
        rx_voltage_v=rx_voltage,
        sampled_v=sampled,
        equalized_symbols=equalized,
        rx_indices=rx_indices,
        metrics=metrics,
        budget=link_budget(cfg, mod),
        equalizer_coeffs=coeffs,
    )
