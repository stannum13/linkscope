"""Co-packaged optics architecture scenario benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    aggregate_bandwidth_tbps: float = 100.0
    lane_rate_gbps: float = 200.0
    copper_trace_cm: float = 30.0
    fiber_reach_m: float = 100.0
    wdm_channels: int = 8
    pluggable_optics: bool = True
    electrical_loss_db_per_cm: float = 0.18
    retimer_loss_budget_db: float = 8.0
    retimer_power_w: float = 1.2
    retimer_latency_ns: float = 4.0
    serdes_energy_pj_per_bit: float = 4.0
    optical_engine_energy_pj_per_bit: float = 3.2
    laser_wall_energy_pj_per_bit: float = 1.0
    heater_power_mw_per_wdm_channel: float = 12.0
    cooling_overhead_fraction: float = 0.15


def default_scenarios() -> list[ScenarioConfig]:
    return [
        ScenarioConfig(
            name="pluggable_retimed",
            copper_trace_cm=42.0,
            pluggable_optics=True,
            serdes_energy_pj_per_bit=5.5,
            optical_engine_energy_pj_per_bit=4.5,
            laser_wall_energy_pj_per_bit=1.4,
        ),
        ScenarioConfig(
            name="cpo_optical_io",
            copper_trace_cm=5.0,
            pluggable_optics=False,
            serdes_energy_pj_per_bit=3.2,
            optical_engine_energy_pj_per_bit=3.0,
            laser_wall_energy_pj_per_bit=0.9,
        ),
    ]


def evaluate_scenario(config: ScenarioConfig) -> dict[str, float | str]:
    lanes = ceil(config.aggregate_bandwidth_tbps * 1000.0 / config.lane_rate_gbps)
    electrical_loss_db = config.copper_trace_cm * config.electrical_loss_db_per_cm
    retimers_per_lane = max(0, ceil(electrical_loss_db / config.retimer_loss_budget_db) - 1)
    retimer_total = lanes * retimers_per_lane
    retimer_power_w = retimer_total * config.retimer_power_w
    heater_power_w = lanes * config.heater_power_mw_per_wdm_channel * 1e-3 / max(
        config.wdm_channels,
        1,
    )
    base_energy_pj_bit = (
        config.serdes_energy_pj_per_bit
        + config.optical_engine_energy_pj_per_bit
        + config.laser_wall_energy_pj_per_bit
    )
    retimer_energy_pj_bit = retimer_power_w / config.aggregate_bandwidth_tbps
    heater_energy_pj_bit = heater_power_w / config.aggregate_bandwidth_tbps
    subtotal_energy = base_energy_pj_bit + retimer_energy_pj_bit + heater_energy_pj_bit
    energy_pj_bit = subtotal_energy * (1.0 + config.cooling_overhead_fraction)
    package_power_w = energy_pj_bit * config.aggregate_bandwidth_tbps
    latency_ns = (
        2.0
        + 0.05 * config.copper_trace_cm
        + retimers_per_lane * config.retimer_latency_ns
        + 0.0049 * config.fiber_reach_m
    )
    link_margin_proxy_db = max(0.0, config.retimer_loss_budget_db - electrical_loss_db)
    return {
        "name": config.name,
        "aggregate_bandwidth_tbps": config.aggregate_bandwidth_tbps,
        "lane_rate_gbps": config.lane_rate_gbps,
        "lanes": float(lanes),
        "wdm_channels": float(config.wdm_channels),
        "copper_trace_cm": config.copper_trace_cm,
        "electrical_loss_db": electrical_loss_db,
        "retimers_per_lane": float(retimers_per_lane),
        "retimer_total": float(retimer_total),
        "energy_pj_per_bit": energy_pj_bit,
        "package_power_w": package_power_w,
        "latency_ns": latency_ns,
        "heater_power_w": heater_power_w,
        "link_margin_proxy_db": link_margin_proxy_db,
        "pluggable_optics": float(config.pluggable_optics),
    }


def benchmark_scenarios(
    configs: list[ScenarioConfig] | None = None,
) -> list[dict[str, float | str]]:
    return [evaluate_scenario(config) for config in (configs or default_scenarios())]
