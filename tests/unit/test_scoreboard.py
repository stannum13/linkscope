from __future__ import annotations

import math

from photon_link_lab.scoreboard import (
    SCOREBOARD_SCHEMA,
    run_scoreboard_benchmark,
    scoreboard_payload,
)


def test_run_scoreboard_benchmark_returns_normalized_rows() -> None:
    rows = run_scoreboard_benchmark(symbols=64, yield_symbols=64, surrogate_samples=8)
    assert rows
    assert {str(row["section"]) for row in rows}.issuperset(
        {
            "link_core",
            "wdm_worst_channel",
            "wafer_proxy",
            "surrogate",
            "architecture.pluggable_retimed",
            "architecture.cpo_optical_io",
            "architecture_delta.pluggable_minus_cpo",
        }
    )
    lookup = {
        (str(row["section"]), str(row["metric"])): float(row["value"])
        for row in rows
    }
    assert math.isfinite(lookup[("link_core", "ber_upper_95")])
    assert math.isfinite(lookup[("link_core", "fec_margin_db")])
    assert lookup[("architecture_delta.pluggable_minus_cpo", "energy_pj_per_bit")] > 0.0


def test_scoreboard_payload_has_schema() -> None:
    rows = [{"section": "link_core", "metric": "ber", "value": 0.0, "unit": "ratio", "note": ""}]
    payload = scoreboard_payload(rows)
    assert payload["schema"] == SCOREBOARD_SCHEMA
    assert payload["rows"] == rows
