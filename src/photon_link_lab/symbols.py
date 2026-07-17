"""Symbol generation and sampling helpers."""

from __future__ import annotations

import numpy as np


def bits_per_symbol(order: int) -> int:
    if order < 2 or order & (order - 1):
        raise ValueError("PAM order must be a power of two and at least 2")
    return int(np.log2(order))


def gray_code(index: int) -> int:
    if index < 0:
        raise ValueError("symbol index must be non-negative")
    return index ^ (index >> 1)


def symbol_indices_to_gray_bits(indices: np.ndarray, order: int) -> np.ndarray:
    bit_count = bits_per_symbol(order)
    values = np.asarray(indices, dtype=int)
    if np.any(values < 0) or np.any(values >= order):
        raise ValueError("symbol indices must be within the PAM order")
    gray = values ^ (values >> 1)
    shifts = np.arange(bit_count - 1, -1, -1, dtype=int)
    return ((gray[:, None] >> shifts) & 1).astype(int)


def pam_levels(order: int) -> np.ndarray:
    bits_per_symbol(order)
    levels = np.arange(order, dtype=float) * 2.0 - (order - 1)
    return levels / np.max(np.abs(levels))


def generate_symbols(
    n_symbols: int,
    order: int = 4,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, order, size=n_symbols)
    return indices, pam_levels(order)[indices]


def upsample(symbol_values: np.ndarray, samples_per_symbol: int) -> np.ndarray:
    return np.repeat(np.asarray(symbol_values, dtype=float), samples_per_symbol)


def sample_at_symbols(
    waveform: np.ndarray,
    samples_per_symbol: int,
    offset: int | None = None,
) -> np.ndarray:
    if offset is None:
        offset = samples_per_symbol // 2
    return np.asarray(waveform)[offset::samples_per_symbol]
