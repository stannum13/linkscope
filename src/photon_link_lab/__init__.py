"""Silicon-photonic optical link simulation toolkit."""

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.link import LinkResult, simulate_link
from photon_link_lab.metrics import estimate_ber, link_budget
from photon_link_lab.sweeps import monte_carlo_yield, sweep_thermal_drift, sweep_tx_power

__all__ = [
    "estimate_ber",
    "LinkConfig",
    "LinkResult",
    "link_budget",
    "ModulatorConfig",
    "monte_carlo_yield",
    "VariationConfig",
    "simulate_link",
    "sweep_thermal_drift",
    "sweep_tx_power",
]

__version__ = "0.1.0"
