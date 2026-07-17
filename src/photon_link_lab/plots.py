"""Plot helpers for the retained link and calibration paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from photon_link_lab.link import LinkResult


def save_eye_diagram(result: LinkResult, path: str | Path, samples_per_symbol: int) -> None:
    samples = np.asarray(result.rx_voltage_v)
    traces = []
    for start in range(0, len(samples) - samples_per_symbol, samples_per_symbol):
        traces.append(samples[start : start + samples_per_symbol])
        if len(traces) >= 256:
            break

    _prepare_path(path)
    plt.figure(figsize=(6, 4))
    for trace in traces:
        plt.plot(trace, color="#355c7d", alpha=0.08)
    plt.title("Received eye diagram")
    plt.xlabel("Sample within symbol")
    plt.ylabel("Voltage (V)")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_ber_sweep(rows: Sequence[Mapping[str, float]], path: str | Path) -> None:
    _line_plot(
        rows,
        path,
        x_key="tx_laser_power_dbm",
        y_key="ber",
        title="BER versus laser power",
        xlabel="Laser power (dBm)",
        ylabel="BER",
    )


def save_drift_sweep(rows: Sequence[Mapping[str, float]], path: str | Path) -> None:
    _line_plot(
        rows,
        path,
        x_key="thermal_shift_nm",
        y_key="ber",
        title="BER versus thermal drift",
        xlabel="Thermal shift (nm)",
        ylabel="BER",
    )


def save_yield_histogram(rows: Sequence[Mapping[str, float]], path: str | Path) -> None:
    _prepare_path(path)
    plt.figure(figsize=(6, 4))
    plt.hist([float(row["ber"]) for row in rows], bins=16, color="#7a9e7e", edgecolor="#2f3e36")
    plt.title("Process-variation BER distribution")
    plt.xlabel("BER")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def save_ring_fit(data: Mapping[str, np.ndarray], fitted_db: np.ndarray, path: str | Path) -> None:
    observed = data.get("synthetic_transmission_db", data.get("measured_transmission_db"))
    if observed is None:
        raise KeyError("expected synthetic_transmission_db or measured_transmission_db")

    _prepare_path(path)
    plt.figure(figsize=(6, 4))
    plt.scatter(data["wavelength_nm"], observed, s=8, alpha=0.35, label="synthetic samples")
    plt.plot(data["wavelength_nm"], fitted_db, color="#b45f4d", label="fit")
    plt.title("Ring calibration fit")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Transmission (dB)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _line_plot(
    rows: Sequence[Mapping[str, float]],
    path: str | Path,
    *,
    x_key: str,
    y_key: str,
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    _prepare_path(path)
    plt.figure(figsize=(6, 4))
    plt.plot([float(row[x_key]) for row in rows], [float(row[y_key]) for row in rows], marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _prepare_path(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
