"""Configuration objects for link, device, and variation models."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class ModulatorConfig:
    kind: str = "ring"
    insertion_loss_db: float = 1.8
    extinction_ratio_db: float = 6.5
    vpi_v: float = 1.2
    phase_bias_rad: float = 1.57079632679
    q_factor: float = 8500.0
    resonance_wavelength_nm: float = 1310.05
    fsr_nm: float = 8.0
    tuning_efficiency_nm_per_mw: float = 0.075
    voltage_tuning_nm_per_v: float = 0.055
    heater_max_mw: float = 18.0
    heater_mw: float = 0.0
    phase_noise_rad: float = 0.0


@dataclass(frozen=True)
class LinkConfig:
    pam_order: int = 4
    n_symbols: int = 4096
    samples_per_symbol: int = 16
    symbol_rate_gbaud: float = 56.0
    tx_laser_power_dbm: float = 2.0
    wavelength_nm: float = 1310.0
    drive_vpp: float = 0.9
    driver_bandwidth_ghz: float = 38.0
    driver_noise_vrms: float = 0.004
    waveguide_loss_db: float = 1.2
    fiber_loss_db: float = 0.8
    connector_loss_db: float = 0.6
    responsivity_a_per_w: float = 0.82
    tia_gain_ohm: float = 1200.0
    rx_bandwidth_ghz: float = 34.0
    thermal_noise_a_rms: float = 1.5e-6
    rin_db_per_hz: float = -150.0
    quantization_bits: int = 8
    jitter_ui: float = 0.008
    equalizer_taps: int = 7
    training_fraction: float = 0.25
    seed: int = 7
    prefer_jax: bool = True

    def with_updates(self, **kwargs) -> LinkConfig:
        return replace(self, **kwargs)


@dataclass(frozen=True)
class VariationConfig:
    wavelength_sigma_nm: float = 0.18
    q_sigma_fraction: float = 0.08
    loss_sigma_db: float = 0.35
    responsivity_sigma_fraction: float = 0.04
    die_to_die_offset_nm: float = 0.0
    wafer_gradient_nm: float = 0.0


@dataclass(frozen=True)
class CalibrationResult:
    insertion_loss_db: float
    extinction_ratio_db: float
    q_factor: float
    resonance_wavelength_nm: float
    rmse_db: float
    n_points: int
