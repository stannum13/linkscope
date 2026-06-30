"""Plot generation for simulation artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from photon_link_lab.link import LinkResult


def save_eye_diagram(
    result: LinkResult,
    path: str | Path,
    samples_per_symbol: int,
    traces: int = 240,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    waveform = result.rx_voltage_v
    span = 2 * samples_per_symbol
    fig, ax = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    max_start = min(len(waveform) - span, traces * samples_per_symbol)
    for start in range(0, max_start, samples_per_symbol):
        ax.plot(
            np.arange(span) / samples_per_symbol,
            waveform[start : start + span] * 1e3,
            color="#2458a6",
            alpha=0.08,
        )
    ax.set_xlabel("Unit intervals")
    ax.set_ylabel("TIA output (mV)")
    ax.set_title("PAM eye diagram")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_ber_sweep(rows: list[dict[str, float]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.asarray([row["tx_laser_power_dbm"] for row in rows])
    ber = np.asarray([max(row["ber"], 1e-6) for row in rows])
    q = np.asarray([row["q_factor_eye"] for row in rows])
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    ax1.semilogy(x, ber, marker="o", color="#b42318", label="BER")
    ax1.set_xlabel("TX laser power (dBm)")
    ax1.set_ylabel("BER")
    ax1.grid(True, which="both", alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(x, q, marker="s", color="#067647", label="Eye Q")
    ax2.set_ylabel("Eye Q")
    ax1.set_title("Power sweep")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_ring_fit(data: dict[str, np.ndarray], fitted_db: np.ndarray, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    heaters = np.unique(data["heater_mw"])
    for heater in heaters:
        mask = data["heater_mw"] == heater
        ax.scatter(
            data["wavelength_nm"][mask],
            data["measured_transmission_db"][mask],
            s=8,
            alpha=0.45,
            label=f"{heater:g} mW measured",
        )
        ax.plot(data["wavelength_nm"][mask], fitted_db[mask], linewidth=1.2)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Transmission (dB)")
    ax.set_title("Ring calibration fit")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=7, ncols=2)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_drift_sweep(rows: list[dict[str, float]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.asarray([row["thermal_shift_nm"] for row in rows])
    q = np.asarray([row["q_factor_eye"] for row in rows])
    ber = np.asarray([max(row["ber"], 1e-6) for row in rows])
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    ax1.plot(x, q, marker="o", color="#2458a6")
    ax1.set_xlabel("Thermal resonance shift (nm)")
    ax1.set_ylabel("Eye Q")
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.semilogy(x, ber, marker="s", color="#b42318")
    ax2.set_ylabel("BER")
    ax1.set_title("Thermal drift penalty")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_yield_histogram(rows: list[dict[str, float]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    q = np.asarray([row["q_factor_eye"] for row in rows])
    passed = np.asarray([row["pass"] for row in rows], dtype=bool)
    yield_percent = 100.0 * float(np.mean(passed)) if len(passed) else 0.0
    fig, ax = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    ax.hist(q, bins=min(16, max(4, len(q) // 4)), color="#475467", edgecolor="white")
    ax.axvline(np.median(q), color="#067647", linewidth=1.8, label="median")
    ax.set_xlabel("Eye Q")
    ax.set_ylabel("Monte Carlo samples")
    ax.set_title(f"Process-variation yield: {yield_percent:.1f}% pass")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_wdm_sweep(rows: list[dict[str, float]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    channels = np.asarray([row["channel"] for row in rows])
    ber = np.asarray([max(row["ber"], 1e-6) for row in rows])
    q = np.asarray([row["q_factor_eye"] for row in rows])
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    ax1.semilogy(channels, ber, marker="o", color="#b42318")
    ax1.set_xlabel("WDM channel")
    ax1.set_ylabel("BER")
    ax1.set_xticks(channels)
    ax1.grid(True, which="both", alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(channels, q, marker="s", color="#2458a6")
    ax2.set_ylabel("Eye Q")
    ax1.set_title("WDM channel metrics")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
