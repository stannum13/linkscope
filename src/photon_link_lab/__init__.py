"""Silicon-photonic optical link simulation toolkit."""

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig, WDMConfig
from photon_link_lab.cpo import ScenarioConfig, benchmark_scenarios
from photon_link_lab.link import LinkResult, simulate_link
from photon_link_lab.metrics import estimate_ber, link_budget
from photon_link_lab.surrogate import train_test_surrogate
from photon_link_lab.sweeps import monte_carlo_yield, sweep_thermal_drift, sweep_tx_power
from photon_link_lab.variation import generate_wafer_grid, summarize_pass_fail
from photon_link_lab.wdm import simulate_wdm

__all__ = [
    "estimate_ber",
    "generate_wafer_grid",
    "LinkConfig",
    "LinkResult",
    "link_budget",
    "benchmark_scenarios",
    "ModulatorConfig",
    "monte_carlo_yield",
    "ScenarioConfig",
    "VariationConfig",
    "WDMConfig",
    "simulate_link",
    "simulate_wdm",
    "summarize_pass_fail",
    "sweep_thermal_drift",
    "sweep_tx_power",
    "train_test_surrogate",
]

__version__ = "0.1.0"
