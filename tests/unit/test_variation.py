from __future__ import annotations

import numpy as np

from photon_link_lab.config import VariationConfig
from photon_link_lab.variation import (
    PASS_FAIL_SUMMARY_FIELDS,
    WaferGridConfig,
    generate_wafer_grid,
    summarize_pass_fail,
    wafer_field_matrix,
)


def test_wafer_grid_is_reproducible_for_fixed_seed() -> None:
    grid = WaferGridConfig(rows=7, cols=7, seed=123)

    first = generate_wafer_grid(grid=grid)
    second = generate_wafer_grid(grid=grid)

    assert first == second
    assert set(summarize_pass_fail(first)) == set(PASS_FAIL_SUMMARY_FIELDS)
    assert {
        "die_index",
        "row",
        "col",
        "x_mm",
        "y_mm",
        "radius_norm",
        "resonance_wavelength_nm",
        "resonance_shift_nm",
        "q_factor",
        "insertion_loss_db",
        "responsivity_a_per_w",
        "yield_score",
        "pass",
    }.issubset(first[0])


def test_zero_variation_collapses_process_fields() -> None:
    rows = generate_wafer_grid(
        grid=WaferGridConfig(rows=5, cols=5, seed=99),
        variation=VariationConfig(
            wavelength_sigma_nm=0.0,
            q_sigma_fraction=0.0,
            loss_sigma_db=0.0,
            responsivity_sigma_fraction=0.0,
            die_to_die_offset_nm=0.0,
            wafer_gradient_nm=0.0,
        ),
    )
    summary = summarize_pass_fail(rows)

    for field in (
        "resonance_wavelength_nm",
        "q_factor",
        "insertion_loss_db",
        "responsivity_a_per_w",
        "yield_score",
        "pass",
    ):
        assert len({row[field] for row in rows}) == 1
    assert summary["yield_fraction"] == 1.0
    assert summary["mean_yield_score"] == 1.0


def test_larger_variation_worsens_yield_proxy() -> None:
    grid = WaferGridConfig(rows=15, cols=15, seed=21)
    mild = generate_wafer_grid(
        grid=grid,
        variation=VariationConfig(
            wavelength_sigma_nm=0.02,
            q_sigma_fraction=0.005,
            loss_sigma_db=0.02,
            responsivity_sigma_fraction=0.002,
        ),
    )
    severe = generate_wafer_grid(
        grid=grid,
        variation=VariationConfig(
            wavelength_sigma_nm=0.45,
            q_sigma_fraction=0.20,
            loss_sigma_db=0.85,
            responsivity_sigma_fraction=0.12,
            wafer_gradient_nm=0.25,
        ),
    )
    mild_summary = summarize_pass_fail(mild)
    severe_summary = summarize_pass_fail(severe)

    assert severe_summary["mean_yield_score"] < mild_summary["mean_yield_score"]
    assert severe_summary["yield_fraction"] <= mild_summary["yield_fraction"]


def test_wafer_field_matrix_keeps_off_wafer_sites_as_nan() -> None:
    grid = WaferGridConfig(rows=5, cols=5, seed=3)
    rows = generate_wafer_grid(grid=grid)
    matrix = wafer_field_matrix(rows, "yield_score")

    assert matrix.shape == (grid.rows, grid.cols)
    assert np.isnan(matrix[0, 0])
    for row in rows:
        assert matrix[int(row["row"]), int(row["col"])] == row["yield_score"]
