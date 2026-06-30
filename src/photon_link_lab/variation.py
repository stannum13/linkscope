"""Wafer-level process variation and yield-proxy helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np

from photon_link_lab.config import LinkConfig, ModulatorConfig, VariationConfig

WaferDie: TypeAlias = dict[str, float | int]

PASS_FAIL_SUMMARY_FIELDS = (
    "total_die",
    "passed_die",
    "failed_die",
    "yield_fraction",
    "yield_percent",
    "mean_yield_score",
    "median_yield_score",
    "min_yield_score",
)


@dataclass(frozen=True)
class WaferGridConfig:
    """Configuration for deterministic die placement and yield proxy thresholds."""

    rows: int = 11
    cols: int = 11
    wafer_radius_mm: float = 100.0
    edge_exclusion_mm: float = 3.0
    seed: int = 7
    pass_score_threshold: float = 0.5
    resonance_tolerance_nm: float = 0.30
    q_drop_tolerance_fraction: float = 0.25
    loss_tolerance_db: float = 0.75
    responsivity_drop_tolerance_fraction: float = 0.15


def generate_wafer_grid(
    grid: WaferGridConfig | None = None,
    mod: ModulatorConfig | None = None,
    link: LinkConfig | None = None,
    variation: VariationConfig | None = None,
) -> list[WaferDie]:
    """Generate deterministic wafer die rows with process fields and pass/fail flags.

    The model is intentionally lightweight: it samples die-local variation with a
    fixed NumPy generator, adds a linear wafer resonance gradient, and applies
    mild radial degradation to Q, loss, and responsivity. The resulting rows are
    directly usable by plotting code because every active die includes row/col
    indices plus physical x/y coordinates.
    """

    grid = grid or WaferGridConfig()
    mod = mod or ModulatorConfig()
    link = link or LinkConfig()
    variation = variation or VariationConfig()
    _validate_grid(grid)

    coords = _die_coordinates(grid)
    if not coords:
        return []

    row_idx = np.asarray([coord[0] for coord in coords], dtype=int)
    col_idx = np.asarray([coord[1] for coord in coords], dtype=int)
    x_mm = np.asarray([coord[2] for coord in coords], dtype=float)
    y_mm = np.asarray([coord[3] for coord in coords], dtype=float)
    usable_radius = grid.wafer_radius_mm - grid.edge_exclusion_mm
    radius_norm = np.sqrt(x_mm**2 + y_mm**2) / usable_radius
    x_norm = x_mm / usable_radius

    rng = np.random.default_rng(grid.seed)
    resonance_shift_nm = (
        variation.die_to_die_offset_nm
        + variation.wafer_gradient_nm * x_norm
        + rng.normal(0.0, variation.wavelength_sigma_nm, size=len(coords))
    )
    q_fraction = (
        rng.normal(0.0, variation.q_sigma_fraction, size=len(coords))
        - 0.5 * variation.q_sigma_fraction * radius_norm**2
    )
    loss_delta_db = (
        rng.normal(0.0, variation.loss_sigma_db, size=len(coords))
        + 0.75 * variation.loss_sigma_db * radius_norm**2
    )
    responsivity_fraction = (
        rng.normal(0.0, variation.responsivity_sigma_fraction, size=len(coords))
        - 0.5 * variation.responsivity_sigma_fraction * radius_norm**2
    )

    resonance_nm = mod.resonance_wavelength_nm + resonance_shift_nm
    q_factor = mod.q_factor * np.maximum(0.25, 1.0 + q_fraction)
    insertion_loss_db = np.maximum(0.0, mod.insertion_loss_db + loss_delta_db)
    responsivity_a_per_w = link.responsivity_a_per_w * np.maximum(
        0.1, 1.0 + responsivity_fraction
    )
    yield_score = _yield_scores(
        grid=grid,
        mod=mod,
        link=link,
        resonance_nm=resonance_nm,
        q_factor=q_factor,
        insertion_loss_db=insertion_loss_db,
        responsivity_a_per_w=responsivity_a_per_w,
    )
    passed = yield_score >= grid.pass_score_threshold

    rows: list[WaferDie] = []
    for index in range(len(coords)):
        rows.append(
            {
                "die_index": index,
                "row": int(row_idx[index]),
                "col": int(col_idx[index]),
                "x_mm": float(x_mm[index]),
                "y_mm": float(y_mm[index]),
                "radius_norm": float(radius_norm[index]),
                "resonance_wavelength_nm": float(resonance_nm[index]),
                "resonance_shift_nm": float(resonance_shift_nm[index]),
                "q_factor": float(q_factor[index]),
                "insertion_loss_db": float(insertion_loss_db[index]),
                "responsivity_a_per_w": float(responsivity_a_per_w[index]),
                "yield_score": float(yield_score[index]),
                "pass": int(passed[index]),
            }
        )
    return rows


def summarize_pass_fail(rows: list[WaferDie]) -> dict[str, float | int]:
    """Return a stable pass/fail summary schema for wafer-map rows."""

    total = len(rows)
    if total == 0:
        return {
            "total_die": 0,
            "passed_die": 0,
            "failed_die": 0,
            "yield_fraction": 0.0,
            "yield_percent": 0.0,
            "mean_yield_score": 0.0,
            "median_yield_score": 0.0,
            "min_yield_score": 0.0,
        }

    passed = np.asarray([row["pass"] for row in rows], dtype=bool)
    scores = np.asarray([row["yield_score"] for row in rows], dtype=float)
    passed_count = int(np.count_nonzero(passed))
    yield_fraction = passed_count / total
    return {
        "total_die": total,
        "passed_die": passed_count,
        "failed_die": total - passed_count,
        "yield_fraction": float(yield_fraction),
        "yield_percent": float(100.0 * yield_fraction),
        "mean_yield_score": float(np.mean(scores)),
        "median_yield_score": float(np.median(scores)),
        "min_yield_score": float(np.min(scores)),
    }


def wafer_field_matrix(
    rows: list[WaferDie],
    field: str,
    fill_value: float = np.nan,
) -> np.ndarray:
    """Convert a wafer row field into a row/column matrix for heat-map plotting."""

    if not rows:
        return np.empty((0, 0), dtype=float)
    if field not in rows[0]:
        raise KeyError(f"unknown wafer field: {field}")
    n_rows = int(max(row["row"] for row in rows)) + 1
    n_cols = int(max(row["col"] for row in rows)) + 1
    matrix = np.full((n_rows, n_cols), fill_value, dtype=float)
    for row in rows:
        matrix[int(row["row"]), int(row["col"])] = float(row[field])
    return matrix


def _die_coordinates(grid: WaferGridConfig) -> list[tuple[int, int, float, float]]:
    usable_radius = grid.wafer_radius_mm - grid.edge_exclusion_mm
    xs = _centered_axis(grid.cols, usable_radius)
    ys = _centered_axis(grid.rows, usable_radius)
    coords: list[tuple[int, int, float, float]] = []
    for row_index, y_mm in enumerate(ys):
        for col_index, x_mm in enumerate(xs):
            if x_mm**2 + y_mm**2 <= usable_radius**2 + 1e-12:
                coords.append((row_index, col_index, float(x_mm), float(y_mm)))
    return coords


def _centered_axis(count: int, radius_mm: float) -> np.ndarray:
    if count == 1:
        return np.asarray([0.0])
    return np.linspace(-radius_mm, radius_mm, count)


def _yield_scores(
    grid: WaferGridConfig,
    mod: ModulatorConfig,
    link: LinkConfig,
    resonance_nm: np.ndarray,
    q_factor: np.ndarray,
    insertion_loss_db: np.ndarray,
    responsivity_a_per_w: np.ndarray,
) -> np.ndarray:
    resonance_penalty = np.abs(resonance_nm - mod.resonance_wavelength_nm) / (
        grid.resonance_tolerance_nm
    )
    q_penalty = np.maximum(0.0, 1.0 - q_factor / mod.q_factor) / (
        grid.q_drop_tolerance_fraction
    )
    loss_penalty = np.maximum(0.0, insertion_loss_db - mod.insertion_loss_db) / (
        grid.loss_tolerance_db
    )
    responsivity_penalty = np.maximum(
        0.0, 1.0 - responsivity_a_per_w / link.responsivity_a_per_w
    ) / (grid.responsivity_drop_tolerance_fraction)
    combined = (
        resonance_penalty**2
        + q_penalty**2
        + loss_penalty**2
        + responsivity_penalty**2
    )
    return 1.0 / (1.0 + combined)


def _validate_grid(grid: WaferGridConfig) -> None:
    if grid.rows <= 0 or grid.cols <= 0:
        raise ValueError("wafer grid rows and cols must be positive")
    if grid.wafer_radius_mm <= 0:
        raise ValueError("wafer_radius_mm must be positive")
    if not 0.0 <= grid.edge_exclusion_mm < grid.wafer_radius_mm:
        raise ValueError("edge_exclusion_mm must be non-negative and smaller than wafer radius")
    if not 0.0 <= grid.pass_score_threshold <= 1.0:
        raise ValueError("pass_score_threshold must be between 0 and 1")
    if grid.resonance_tolerance_nm <= 0:
        raise ValueError("resonance_tolerance_nm must be positive")
    if grid.q_drop_tolerance_fraction <= 0:
        raise ValueError("q_drop_tolerance_fraction must be positive")
    if grid.loss_tolerance_db <= 0:
        raise ValueError("loss_tolerance_db must be positive")
    if grid.responsivity_drop_tolerance_fraction <= 0:
        raise ValueError("responsivity_drop_tolerance_fraction must be positive")
