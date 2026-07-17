"""Simple behavioral bandwidth and impairment filters."""

from __future__ import annotations

import math

import numpy as np


def first_order_lowpass(
    waveform: np.ndarray,
    bandwidth_hz: float,
    sample_rate_hz: float,
) -> np.ndarray:
    if bandwidth_hz <= 0:
        return np.asarray(waveform, dtype=float)
    dt = 1.0 / sample_rate_hz
    tau = 1.0 / (2.0 * math.pi * bandwidth_hz)
    alpha = dt / (tau + dt)
    out = np.empty_like(np.asarray(waveform, dtype=float))
    out[0] = waveform[0]
    for i in range(1, len(out)):
        out[i] = out[i - 1] + alpha * (waveform[i] - out[i - 1])
    return out


def quantize(waveform: np.ndarray, bits: int) -> np.ndarray:
    if bits <= 0:
        return np.asarray(waveform, dtype=float)
    arr = np.asarray(waveform, dtype=float)
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi <= lo:
        return arr.copy()
    levels = 2**bits - 1
    scaled = np.round((arr - lo) / (hi - lo) * levels) / levels
    return scaled * (hi - lo) + lo


def apply_jitter_like_noise(
    waveform: np.ndarray, samples_per_symbol: int, jitter_ui: float, rng: np.random.Generator
) -> np.ndarray:
    if jitter_ui <= 0:
        return np.asarray(waveform, dtype=float)
    arr = np.asarray(waveform, dtype=float)
    slope = np.gradient(arr)
    timing_sigma_samples = jitter_ui * samples_per_symbol
    return arr + slope * rng.normal(0.0, timing_sigma_samples, size=arr.shape)
