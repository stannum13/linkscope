"""Benchmark-v2 scoreboard assembly across link, WDM, yield, ML, and CPO."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from photon_link_lab.config import LinkConfig
from photon_link_lab.cpo import benchmark_scenarios
from photon_link_lab.link import LinkResult, simulate_link
from photon_link_lab.surrogate import train_test_surrogate
from photon_link_lab.variation import generate_wafer_grid, summarize_pass_fail
from photon_link_lab.wdm import simulate_wdm

SCOREBOARD_SCHEMA = "photon-link-lab.benchmark-v2.scoreboard.v1"
DEFAULT_FEC_THRESHOLD_BER = 2e-4

ScoreboardRow = dict[str, float | str]


def run_scoreboard_benchmark(
    symbols: int = 2048,
    yield_symbols: int = 768,
    surrogate_samples: int = 24,
    fec_threshold_ber: float = DEFAULT_FEC_THRESHOLD_BER,
) -> list[ScoreboardRow]:
    """Run a compact cross-domain benchmark and return scoreboard rows."""

    cfg = LinkConfig(n_symbols=symbols)
    yield_cfg = LinkConfig(n_symbols=yield_symbols)
    link_result = simulate_link(cfg)
    wdm_rows = simulate_wdm(cfg=yield_cfg)
    wafer_summary = summarize_pass_fail(generate_wafer_grid())
    cpo_rows = benchmark_scenarios()
    surrogate_result = train_test_surrogate(n_samples=surrogate_samples, n_symbols=yield_symbols)
    return build_scoreboard(
        link_result=link_result,
        wdm_rows=wdm_rows,
        wafer_summary=wafer_summary,
        cpo_rows=cpo_rows,
        surrogate_result=surrogate_result,
        fec_threshold_ber=fec_threshold_ber,
    )


def build_scoreboard(
    link_result: LinkResult,
    wdm_rows: Sequence[Mapping[str, float]],
    wafer_summary: Mapping[str, float | int],
    cpo_rows: Sequence[Mapping[str, float | str]],
    surrogate_result: Mapping[str, object],
    fec_threshold_ber: float = DEFAULT_FEC_THRESHOLD_BER,
) -> list[ScoreboardRow]:
    """Build normalized scoreboard rows from already-computed benchmark outputs."""

    rows: list[ScoreboardRow] = []
    metrics = link_result.metrics
    budget = link_result.budget
    ber_upper_95 = float(metrics.get("ber_upper_95", metrics["ber"]))
    _add(rows, "link_core", "line_rate_gbps", metrics["line_rate_gbps"], "Gb/s")
    _add(rows, "link_core", "empirical_ber", metrics["ber"], "ratio")
    _add(rows, "link_core", "ber_upper_95", ber_upper_95, "ratio")
    _add(rows, "link_core", "fec_threshold_ber", fec_threshold_ber, "ratio")
    _add(rows, "link_core", "fec_margin_db", _fec_margin_db(ber_upper_95, fec_threshold_ber), "dB")
    _add(rows, "link_core", "eye_q", metrics["q_factor_eye"], "ratio")
    _add(rows, "link_core", "rx_optical_power_dbm", budget["rx_optical_power_dbm"], "dBm")
    _add(rows, "link_core", "observed_symbol_errors", metrics.get("symbol_errors", 0.0), "count")

    if wdm_rows:
        worst = max(wdm_rows, key=lambda row: float(row["ber"]))
        max_penalty_db = max(float(row["crosstalk_penalty_db"]) for row in wdm_rows)
        max_skew_ui = max(float(row["dispersion_band_skew_ui"]) for row in wdm_rows)
        _add(rows, "wdm_worst_channel", "channel", worst["channel"], "index")
        _add(rows, "wdm_worst_channel", "ber", worst["ber"], "ratio")
        _add(rows, "wdm_worst_channel", "eye_q", worst["q_factor_eye"], "ratio")
        _add(rows, "wdm_worst_channel", "max_crosstalk_penalty_db", max_penalty_db, "dB")
        _add(rows, "wdm_worst_channel", "max_dispersion_band_skew_ui", max_skew_ui, "UI")

    for key, unit in (
        ("yield_percent", "%"),
        ("mean_yield_score", "ratio"),
        ("min_yield_score", "ratio"),
        ("total_die", "count"),
    ):
        _add(rows, "wafer_proxy", key, wafer_summary[key], unit)

    surrogate_metrics = surrogate_result["metrics"]
    if not isinstance(surrogate_metrics, Mapping):
        raise TypeError("surrogate_result['metrics'] must be a mapping")
    for key, unit in (
        ("n_samples", "count"),
        ("n_test", "count"),
        ("mae_log10_ber", "log10(BER)"),
        ("rmse_log10_ber", "log10(BER)"),
        ("mae_q_factor_eye", "Q"),
        ("rmse_q_factor_eye", "Q"),
    ):
        _add(rows, "surrogate", key, surrogate_metrics[key], unit)

    for row in cpo_rows:
        name = str(row["name"])
        section = f"architecture.{name}"
        for key, unit in (
            ("energy_pj_per_bit", "pJ/bit"),
            ("package_power_w", "W"),
            ("latency_ns", "ns"),
            ("retimer_total", "count"),
            ("lanes", "count"),
            ("link_margin_proxy_db", "dB"),
        ):
            _add(rows, section, key, row[key], unit)

    _add_cpo_delta_rows(rows, cpo_rows)
    return rows


def scoreboard_payload(rows: Sequence[ScoreboardRow]) -> dict[str, object]:
    """Return JSON-ready metadata plus normalized rows."""

    return {
        "schema": SCOREBOARD_SCHEMA,
        "rows": list(rows),
    }


def _add(
    rows: list[ScoreboardRow],
    section: str,
    metric: str,
    value: float | int | str,
    unit: str,
    note: str = "",
) -> None:
    rows.append(
        {
            "section": section,
            "metric": metric,
            "value": float(value),
            "unit": unit,
            "note": note,
        }
    )


def _add_cpo_delta_rows(
    rows: list[ScoreboardRow],
    cpo_rows: Sequence[Mapping[str, float | str]],
) -> None:
    by_name = {str(row["name"]): row for row in cpo_rows}
    if "pluggable_retimed" not in by_name or "cpo_optical_io" not in by_name:
        return
    pluggable = by_name["pluggable_retimed"]
    cpo = by_name["cpo_optical_io"]
    for key, unit in (
        ("energy_pj_per_bit", "pJ/bit"),
        ("package_power_w", "W"),
        ("latency_ns", "ns"),
        ("retimer_total", "count"),
    ):
        delta = float(pluggable[key]) - float(cpo[key])
        _add(rows, "architecture_delta.pluggable_minus_cpo", key, delta, unit)


def _fec_margin_db(ber_upper: float, fec_threshold_ber: float) -> float:
    if fec_threshold_ber <= 0.0:
        raise ValueError("fec_threshold_ber must be positive")
    return 10.0 * math.log10(fec_threshold_ber / max(float(ber_upper), 1e-30))
