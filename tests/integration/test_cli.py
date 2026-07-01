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


def test_cli_smoke_paths(tmp_path) -> None:
    run_cli("simulate", "--symbols", "128", "--out", str(tmp_path / "artifacts"))
    assert (tmp_path / "artifacts" / "link_metrics.json").exists()
    assert (tmp_path / "artifacts" / "eye_diagram.png").exists()

    measured = tmp_path / "measured.csv"
    run_cli("generate-data", "--out", str(measured))
    assert measured.exists()

    run_cli(
        "calibrate",
        "--data",
        str(measured),
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

    run_cli(
        "wdm",
        "--symbols",
        "64",
        "--out",
        str(tmp_path / "wdm.csv"),
        "--plot",
        str(tmp_path / "wdm.png"),
    )
    assert (tmp_path / "wdm.csv").exists()

    run_cli(
        "wafer",
        "--out",
        str(tmp_path / "wafer.csv"),
        "--summary",
        str(tmp_path / "wafer.json"),
        "--plot",
        str(tmp_path / "wafer.png"),
    )
    assert (tmp_path / "wafer.csv").exists()
    assert (tmp_path / "wafer.json").exists()

    run_cli(
        "cpo",
        "--out",
        str(tmp_path / "cpo.csv"),
        "--summary",
        str(tmp_path / "cpo.json"),
        "--plot",
        str(tmp_path / "cpo.png"),
    )
    assert (tmp_path / "cpo.csv").exists()
    assert (tmp_path / "cpo.json").exists()

    run_cli(
        "benchmark-v2",
        "--symbols",
        "64",
        "--yield-symbols",
        "64",
        "--surrogate-samples",
        "8",
        "--out",
        str(tmp_path / "scoreboard.csv"),
        "--summary",
        str(tmp_path / "scoreboard.json"),
        "--plot",
        str(tmp_path / "scoreboard.png"),
    )
    assert (tmp_path / "scoreboard.csv").exists()
    assert (tmp_path / "scoreboard.json").exists()
    assert (tmp_path / "scoreboard.png").exists()

    manifest = tmp_path / "report_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "benchmark": "photon-link-lab.v1",
                "artifacts": {
                    "link_metrics": str(tmp_path / "artifacts" / "link_metrics.json"),
                    "benchmark_v2_scoreboard": str(tmp_path / "scoreboard.csv"),
                    "benchmark_v2_summary": str(tmp_path / "scoreboard.json"),
                },
            }
        )
    )
    run_cli(
        "report",
        "--manifest",
        str(manifest),
        "--out",
        str(tmp_path / "recruiter_report.md"),
        "--json-out",
        str(tmp_path / "recruiter_report.json"),
    )
    assert (tmp_path / "recruiter_report.md").exists()
    assert (tmp_path / "recruiter_report.json").exists()


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
        "--measured",
        str(tmp_path / "measured"),
    )
    assert (tmp_path / "bench" / "manifest.json").exists()
    assert (tmp_path / "bench" / "tx_power_sweep.csv").exists()
    assert (tmp_path / "bench" / "wdm_sweep.csv").exists()
    assert (tmp_path / "bench" / "wafer_grid.csv").exists()
    assert (tmp_path / "bench" / "cpo_scenarios.csv").exists()
    assert (tmp_path / "bench" / "benchmark_v2_scoreboard.csv").exists()
    assert (tmp_path / "artifacts" / "link_metrics.json").exists()
    assert (tmp_path / "artifacts" / "benchmark_v2_scoreboard.json").exists()
    assert (tmp_path / "plots" / "eye_diagram.png").exists()
    assert (tmp_path / "plots" / "benchmark_v2_scoreboard.png").exists()
