"""Plot generation for simulation artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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


def save_surrogate_parity(
    targets: np.ndarray,
    predictions: np.ndarray,
    path: str | Path,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.8), dpi=150)
    labels = ["log10(BER)", "Eye Q"]
    for i, ax in enumerate(axes):
        true = np.asarray(targets)[:, i]
        pred = np.asarray(predictions)[:, i]
        lo = float(min(np.min(true), np.min(pred)))
        hi = float(max(np.max(true), np.max(pred)))
        ax.scatter(true, pred, s=18, color="#2458a6", alpha=0.75)
        ax.plot([lo, hi], [lo, hi], color="#b42318", linewidth=1.0)
        ax.set_xlabel(f"Simulator {labels[i]}")
        ax.set_ylabel(f"Surrogate {labels[i]}")
        ax.grid(True, alpha=0.25)
    fig.suptitle("Surrogate held-out parity")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_wafer_map(
    matrix: np.ndarray,
    path: str | Path,
    title: str = "Wafer yield score",
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.4, 4.8), dpi=150)
    image = ax.imshow(matrix, cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xlabel("Die column")
    ax.set_ylabel("Die row")
    ax.set_title(title)
    fig.colorbar(image, ax=ax, label="Yield score")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_cpo_benchmark(rows: list[dict[str, float | str]], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = [str(row["name"]) for row in rows]
    energy = np.asarray([float(row["energy_pj_per_bit"]) for row in rows])
    latency = np.asarray([float(row["latency_ns"]) for row in rows])
    x = np.arange(len(rows))
    fig, ax1 = plt.subplots(figsize=(7.0, 4.2), dpi=150)
    width = 0.36
    ax1.bar(x - width / 2, energy, width=width, color="#2458a6", label="pJ/bit")
    ax1.set_ylabel("Energy (pJ/bit)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=12, ha="right")
    ax1.grid(True, axis="y", alpha=0.25)
    ax2 = ax1.twinx()
    ax2.bar(x + width / 2, latency, width=width, color="#b42318", label="latency")
    ax2.set_ylabel("Latency (ns)")
    ax1.set_title("CPO architecture scenario benchmark")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def save_scoreboard_summary(
    rows: Sequence[Mapping[str, float | str]],
    path: str | Path,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2), dpi=150)

    empirical = _scoreboard_value(rows, "link_core", "empirical_ber")
    upper = _scoreboard_value(rows, "link_core", "ber_upper_95")
    fec = _scoreboard_value(rows, "link_core", "fec_threshold_ber")
    margin = _scoreboard_value(rows, "link_core", "fec_margin_db")
    ber_values = np.asarray([max(empirical, 1e-12), max(upper, 1e-12), max(fec, 1e-12)])
    axes[0].bar(["BER", "95% upper", "FEC"], ber_values, color=["#475467", "#b42318", "#067647"])
    axes[0].set_yscale("log")
    axes[0].set_ylabel("BER")
    axes[0].set_title(f"BER confidence: {margin:.1f} dB FEC margin")
    axes[0].grid(True, axis="y", which="both", alpha=0.25)

    scenario_sections = [
        section
        for section in _scoreboard_sections(rows)
        if section.startswith("architecture.") and not section.startswith("architecture_delta.")
    ]
    names = [section.split(".", 1)[1] for section in scenario_sections]
    if names:
        energy = np.asarray(
            [_scoreboard_value(rows, section, "energy_pj_per_bit") for section in scenario_sections]
        )
        latency = np.asarray(
            [_scoreboard_value(rows, section, "latency_ns") for section in scenario_sections]
        )
        x = np.arange(len(names))
        width = 0.36
        axes[1].bar(x - width / 2, energy, width=width, color="#2458a6", label="pJ/bit")
        axes[1].set_ylabel("Energy (pJ/bit)")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels([name.replace("_", "\n") for name in names])
        axes[1].grid(True, axis="y", alpha=0.25)
        ax2 = axes[1].twinx()
        ax2.bar(x + width / 2, latency, width=width, color="#b42318", label="latency")
        ax2.set_ylabel("Latency (ns)")
        axes[1].set_title("Architecture scenarios")
    else:
        axes[1].axis("off")
        axes[1].text(0.5, 0.5, "No architecture rows", ha="center", va="center")

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def _scoreboard_value(
    rows: Sequence[Mapping[str, float | str]],
    section: str,
    metric: str,
) -> float:
    for row in rows:
        if row["section"] == section and row["metric"] == metric:
            return float(row["value"])
    raise KeyError(f"scoreboard metric not found: {section}.{metric}")


def _scoreboard_sections(rows: Sequence[Mapping[str, float | str]]) -> list[str]:
    sections: list[str] = []
    for row in rows:
        section = str(row["section"])
        if section not in sections:
            sections.append(section)
    return sections
