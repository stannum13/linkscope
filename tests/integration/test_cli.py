from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.setdefault("MPLBACKEND", "Agg")
    return subprocess.run(
        [sys.executable, "-m", "photon_link_lab.cli", *args],
        cwd=cwd or ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_cli_core_paths(tmp_path) -> None:
    run_cli("simulate", "--symbols", "128", "--out", str(tmp_path / "artifacts"))
    assert (tmp_path / "artifacts" / "link_metrics.json").exists()
    assert (tmp_path / "artifacts" / "eye_diagram.png").exists()

    synthetic = tmp_path / "synthetic.csv"
    run_cli("generate-data", "--out", str(synthetic))
    assert synthetic.exists()
    assert "synthetic_transmission_db" in synthetic.read_text().splitlines()[0]

    run_cli(
        "calibrate",
        "--data",
        str(synthetic),
        "--out",
        str(tmp_path / "calibration.json"),
        "--plot",
        str(tmp_path / "calibration.png"),
    )
    calibration = json.loads((tmp_path / "calibration.json").read_text())
    assert calibration["rmse_db"] < 0.2

    run_cli(
        "sweep",
        "--symbols",
        "128",
        "--points",
        "3",
        "--out",
        str(tmp_path / "power.csv"),
        "--plot",
        str(tmp_path / "power.png"),
    )
    assert (tmp_path / "power.csv").exists()

    run_cli(
        "drift",
        "--symbols",
        "128",
        "--points",
        "3",
        "--out",
        str(tmp_path / "drift.csv"),
        "--plot",
        str(tmp_path / "drift.png"),
    )
    assert (tmp_path / "drift.csv").exists()

    run_cli(
        "yield",
        "--samples",
        "2",
        "--symbols",
        "64",
        "--out",
        str(tmp_path / "yield.csv"),
        "--plot",
        str(tmp_path / "yield.png"),
    )
    assert (tmp_path / "yield.csv").exists()


def test_cli_benchmark_smoke(tmp_path) -> None:
    run_cli(
        "benchmark",
        "--symbols",
        "128",
        "--yield-samples",
        "2",
        "--yield-symbols",
        "64",
        "--out",
        str(tmp_path / "bench"),
        "--artifacts",
        str(tmp_path / "artifacts"),
        "--plots",
        str(tmp_path / "plots"),
        "--synthetic",
        str(tmp_path / "synthetic"),
    )
    assert (tmp_path / "bench" / "manifest.json").exists()
    assert (tmp_path / "bench" / "tx_power_sweep.csv").exists()
    assert (tmp_path / "bench" / "thermal_drift_sweep.csv").exists()
    assert (tmp_path / "bench" / "yield_monte_carlo.csv").exists()
    assert (tmp_path / "artifacts" / "link_metrics.json").exists()
    assert (tmp_path / "artifacts" / "calibration.json").exists()
    assert (tmp_path / "artifacts" / "heater_tuning.json").exists()
    assert (tmp_path / "plots" / "eye_diagram.png").exists()
    assert (tmp_path / "plots" / "thermal_drift.png").exists()
