from __future__ import annotations

import json
from pathlib import Path

from photon_link_lab.cli import main
from photon_link_lab.report import (
    DEFAULT_ARTIFACT_PATHS,
    REPORT_SCHEMA,
    build_project_report,
    render_markdown_report,
    write_project_report,
)


def test_build_project_report_summarizes_existing_artifacts(tmp_path: Path) -> None:
    manifest_path = _write_artifact_tree(tmp_path)

    report = build_project_report(
        manifest_path=manifest_path.relative_to(tmp_path),
        project_root=tmp_path,
    )

    assert report["schema"] == REPORT_SCHEMA
    assert report["health"] == {
        "status": "complete",
        "available_artifacts": len(DEFAULT_ARTIFACT_PATHS),
        "expected_artifacts": len(DEFAULT_ARTIFACT_PATHS),
        "scoreboard_rows": 5,
        "key_link_metrics": 7,
    }

    artifacts = {item["name"]: item for item in report["generated_benchmark_files"]}
    assert artifacts["tx_power_sweep"]["rows"] == 2
    assert artifacts["tx_power_sweep"]["columns"] == [
        "tx_laser_power_dbm",
        "ber",
        "q_factor_eye",
    ]
    assert artifacts["benchmark_v2_summary"]["top_level_keys"] == ["rows", "schema"]

    link_metrics = {item["label"]: item for item in report["key_link_metrics"]}
    assert link_metrics["Line rate"]["value"] == 112.0
    assert link_metrics["FEC margin"]["unit"] == "dB"

    highlights = {item["label"]: item for item in report["scoreboard_highlights"]}
    assert highlights["CPO energy improvement"]["value"] == 4.945
    assert highlights["Wafer yield"]["unit"] == "%"

    commands = [item["command"] for item in report["verification_commands"]]
    assert commands[0] == "python -m pytest"
    assert "python -m photon_link_lab.cli benchmark --out data/benchmarks" in commands[1]
    assert commands[-1].endswith(
        "--out artifacts/demo/recruiter_report.md "
        "--json-out artifacts/demo/recruiter_report.json"
    )


def test_render_markdown_report_contains_recruiter_sections(tmp_path: Path) -> None:
    manifest_path = _write_artifact_tree(tmp_path)
    report = build_project_report(
        manifest_path=manifest_path.relative_to(tmp_path),
        project_root=tmp_path,
    )

    markdown = render_markdown_report(report)

    assert markdown.startswith("# Photon Link Lab Repository Health Report\n")
    assert "## Generated Benchmark Files" in markdown
    assert "| Line rate | 112 | Gb/s | link_metrics.metrics.line_rate_gbps |" in markdown
    assert "| CPO energy improvement | 4.945 | pJ/bit |" in markdown
    assert "`python -m pytest`" in markdown


def test_write_project_report_and_cli_write_markdown_and_json(tmp_path: Path) -> None:
    manifest_path = _write_artifact_tree(tmp_path)
    direct_md = tmp_path / "direct.md"
    direct_json = tmp_path / "direct.json"

    direct_report = write_project_report(
        out=direct_md,
        json_out=direct_json,
        manifest_path=manifest_path.relative_to(tmp_path),
        project_root=tmp_path,
    )

    assert direct_md.exists()
    assert json.loads(direct_json.read_text()) == direct_report

    cli_md = tmp_path / "cli.md"
    cli_json = tmp_path / "cli.json"
    main(
        [
            "report",
            "--manifest",
            str(manifest_path),
            "--out",
            str(cli_md),
            "--json-out",
            str(cli_json),
        ]
    )

    assert cli_md.exists()
    cli_report = json.loads(cli_json.read_text())
    assert cli_report["schema"] == REPORT_SCHEMA
    assert cli_report["health"]["status"] == "complete"


def _write_artifact_tree(root: Path) -> Path:
    artifacts = dict(DEFAULT_ARTIFACT_PATHS)
    manifest_path = root / "data/benchmarks/manifest.json"
    _write_json(
        manifest_path,
        {
            "benchmark": "photon-link-lab.v1",
            "symbols": 512,
            "yield_samples": 8,
            "artifacts": artifacts,
        },
    )

    for name, relative_path in artifacts.items():
        path = root / relative_path
        if name == "plots":
            path.mkdir(parents=True, exist_ok=True)
        elif relative_path.endswith(".csv"):
            _write_csv(path)
        elif relative_path.endswith(".json"):
            _write_json(path, {})
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("artifact\n")

    _write_json(
        root / artifacts["link_metrics"],
        {
            "metrics": {
                "line_rate_gbps": 112.0,
                "ber": 0.1220703125,
                "ber_upper_95": 0.14158280668015458,
                "fec_margin_db": -28.499805216919082,
                "q_factor_eye": 0.9996480418593198,
            },
            "budget": {
                "rx_optical_power_dbm": -5.831276076630618,
                "static_margin_db": 10.296562490566735,
            },
        },
    )
    _write_json(
        root / artifacts["benchmark_v2_summary"],
        {
            "schema": "photon-link-lab.benchmark-v2.scoreboard.v1",
            "rows": [
                {
                    "section": "link_core",
                    "metric": "line_rate_gbps",
                    "value": 112.0,
                    "unit": "Gb/s",
                    "note": "",
                },
                {
                    "section": "link_core",
                    "metric": "fec_margin_db",
                    "value": -28.499805216919082,
                    "unit": "dB",
                    "note": "",
                },
                {
                    "section": "wafer_proxy",
                    "metric": "yield_percent",
                    "value": 82.71604938271605,
                    "unit": "%",
                    "note": "",
                },
                {
                    "section": "surrogate",
                    "metric": "mae_log10_ber",
                    "value": 0.3429767056015855,
                    "unit": "log10(BER)",
                    "note": "",
                },
                {
                    "section": "architecture_delta.pluggable_minus_cpo",
                    "metric": "energy_pj_per_bit",
                    "value": 4.945,
                    "unit": "pJ/bit",
                    "note": "",
                },
            ],
        },
    )
    return manifest_path


def _write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "tx_laser_power_dbm,ber,q_factor_eye\n"
        "-4.0,0.12890625,0.9948717844572252\n"
        "-3.0,0.126953125,0.996658611676315\n"
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
