from __future__ import annotations

from photon_link_lab.cpo import ScenarioConfig, benchmark_scenarios, evaluate_scenario


def test_cpo_default_scenarios_have_stable_schema() -> None:
    rows = benchmark_scenarios()
    assert [row["name"] for row in rows] == ["pluggable_retimed", "cpo_optical_io"]
    assert {"energy_pj_per_bit", "latency_ns", "retimer_total", "package_power_w"}.issubset(
        rows[0]
    )


def test_longer_copper_increases_retimer_need_and_latency() -> None:
    short = evaluate_scenario(ScenarioConfig(name="short", copper_trace_cm=4.0))
    long = evaluate_scenario(ScenarioConfig(name="long", copper_trace_cm=80.0))
    assert long["retimers_per_lane"] > short["retimers_per_lane"]
    assert long["latency_ns"] > short["latency_ns"]
    assert long["energy_pj_per_bit"] > short["energy_pj_per_bit"]
