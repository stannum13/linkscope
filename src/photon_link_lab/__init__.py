"""Silicon-photonic optical link simulation toolkit."""

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig
from photon_link_lab.link import LinkResult, simulate_link
from photon_link_lab.metrics import estimate_ber, link_budget
from photon_link_lab.sweeps import monte_carlo_yield, sweep_thermal_drift, sweep_tx_power
from photon_link_lab.variation import generate_wafer_grid, summarize_pass_fail

__all__ = [
    "estimate_ber",
    "generate_wafer_grid",
    "LinkConfig",
    "LinkResult",
    "link_budget",
    "ModulatorConfig",
    "monte_carlo_yield",
    "simulate_link",
    "summarize_pass_fail",
    "sweep_thermal_drift",
    "sweep_tx_power",
    "VariationConfig",
]

__version__ = "0.1.0"
