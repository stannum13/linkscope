from __future__ import annotations

from photon_link_lab.calibration import fit_ring_from_measurements
from photon_link_lab.config import ModulatorConfig
from photon_link_lab.datasets import generate_synthetic_ring_measurements


def test_calibration_recovers_synthetic_ring_parameters(tmp_path) -> None:
    mod = ModulatorConfig(
        insertion_loss_db=1.8,
        extinction_ratio_db=6.5,
        q_factor=8500.0,
        resonance_wavelength_nm=1310.05,
    )
    data_path = generate_synthetic_ring_measurements(
        tmp_path / "ring.csv",
        mod=mod,
        seed=42,
        n_wavelengths=81,
    )
    result = fit_ring_from_measurements(data_path, initial=mod)
    assert abs(result.insertion_loss_db - mod.insertion_loss_db) < 0.25
    assert abs(result.extinction_ratio_db - mod.extinction_ratio_db) < 0.75
    assert abs(result.q_factor - mod.q_factor) / mod.q_factor < 0.10
    assert abs(result.resonance_wavelength_nm - mod.resonance_wavelength_nm) < 0.02
    assert result.rmse_db < 0.15
