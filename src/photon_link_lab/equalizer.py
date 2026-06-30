"""Symbol-spaced equalization and PAM decisions."""

from __future__ import annotations

import math

import numpy as np

from photon_link_lab.symbols import pam_levels


def fit_ffe(samples: np.ndarray, target_symbols: np.ndarray, taps: int = 7) -> np.ndarray:
    taps = max(1, int(taps))
    x = np.asarray(samples, dtype=float)
    y = np.asarray(target_symbols, dtype=float)
    rows = []
    targets = []
    center = taps // 2
    for i in range(center, min(len(x) - (taps - center - 1), len(y))):
        rows.append(x[i - center : i - center + taps])
        targets.append(y[i])
    matrix = np.asarray(rows)
    if len(matrix) == 0:
        return np.ones(1)
    coeffs, *_ = np.linalg.lstsq(matrix, np.asarray(targets), rcond=None)
    return coeffs


def apply_ffe(samples: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    x = np.asarray(samples, dtype=float)
    c = np.asarray(coeffs, dtype=float)
    center = len(c) // 2
    padded = np.pad(x, (center, len(c) - center - 1), mode="edge")
    return np.convolve(padded, c[::-1], mode="valid")


def decide_pam(samples: np.ndarray, order: int) -> tuple[np.ndarray, np.ndarray]:
    levels = pam_levels(order)
    distances = np.abs(np.asarray(samples)[:, None] - levels[None, :])
    decisions = np.argmin(distances, axis=1)
    return decisions, levels[decisions]


def bits_per_symbol(order: int) -> int:
    return int(round(math.log2(order)))
