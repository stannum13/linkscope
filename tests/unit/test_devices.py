from __future__ import annotations

import numpy as np
import pytest

from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.devices import (
    channel_loss,
    mzi_transfer,
    ring_derived_metrics,
    ring_transfer,
)
from photon_link_lab.units import db_to_linear


def test_ring_transfer_accepts_array_resonance() -> None:
    mod = ModulatorConfig()
    resonance = np.linspace(1309.9, 1310.1, 32)
    transmission = ring_transfer(1310.0, mod, resonance_nm=resonance)
    assert transmission.shape == resonance.shape
    assert np.all(np.isfinite(transmission))
    assert np.all(transmission > 0.0)


def test_ring_minimum_occurs_near_resonance() -> None:
    mod = ModulatorConfig(resonance_wavelength_nm=1310.0, q_factor=10_000)
    wavelengths = np.linspace(1309.7, 1310.3, 601)
    transmission = ring_transfer(wavelengths, mod)
    min_wavelength = wavelengths[np.argmin(transmission)]
    assert min_wavelength == pytest.approx(mod.resonance_wavelength_nm, abs=0.002)


def test_ring_derived_metrics_are_physical() -> None:
    metrics = ring_derived_metrics(ModulatorConfig(q_factor=10_000, fsr_nm=8.0))
    assert metrics["linewidth_nm"] > 0
    assert metrics["linewidth_ghz"] > 0
    assert metrics["finesse"] == pytest.approx(8.0 / metrics["linewidth_nm"])


def test_mzi_transfer_bounds() -> None:
    mod = ModulatorConfig(kind="mzi", insertion_loss_db=2.0, extinction_ratio_db=8.0)
    voltage = np.linspace(-1.0, 1.0, 100)
    transmission = mzi_transfer(voltage, mod)
    upper = db_to_linear(-mod.insertion_loss_db)
    lower = upper * db_to_linear(-mod.extinction_ratio_db)
    assert np.max(transmission) <= upper + 1e-12
    assert np.min(transmission) >= lower - 1e-12


def test_channel_loss_applies_db_sum() -> None:
    cfg = LinkConfig(waveguide_loss_db=1.0, fiber_loss_db=2.0, connector_loss_db=3.0)
    out = channel_loss(np.array([1.0]), cfg)
    assert out[0] == pytest.approx(db_to_linear(-6.0))
