"""Recruiter-friendly repository health report generation."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "photon-link-lab.recruiter-report.v1"
DEFAULT_MANIFEST_PATH = Path("data/benchmarks/manifest.json")
DEFAULT_REPORT_MARKDOWN_PATH = Path("artifacts/demo/recruiter_report.md")
DEFAULT_REPORT_JSON_PATH = Path("artifacts/demo/recruiter_report.json")

DEFAULT_ARTIFACT_PATHS: tuple[tuple[str, str], ...] = (
    ("measured_data", "data/measured/fake_measured_ring_sweep.csv"),
    ("tx_power_sweep", "data/benchmarks/tx_power_sweep.csv"),
    ("thermal_drift_sweep", "data/benchmarks/thermal_drift_sweep.csv"),
    ("yield_monte_carlo", "data/benchmarks/yield_monte_carlo.csv"),
    ("wdm_sweep", "data/benchmarks/wdm_sweep.csv"),
    ("wafer_grid", "data/benchmarks/wafer_grid.csv"),
    ("wafer_summary", "artifacts/demo/wafer_summary.json"),
    ("cpo_scenarios", "data/benchmarks/cpo_scenarios.csv"),
    ("cpo_summary", "artifacts/demo/cpo_scenarios.json"),
    ("benchmark_v2_scoreboard", "data/benchmarks/benchmark_v2_scoreboard.csv"),
    ("benchmark_v2_summary", "artifacts/demo/benchmark_v2_scoreboard.json"),
    ("link_metrics", "artifacts/demo/link_metrics.json"),
    ("calibration", "artifacts/demo/calibration.json"),
    ("heater_tuning", "artifacts/demo/heater_tuning.json"),
    ("compact_model", "artifacts/demo/compact_model.json"),
    ("veriloga_style", "artifacts/demo/ring_behavioral.va"),
    ("surrogate", "artifacts/demo/surrogate.json"),
    ("scoreboard_plot", "plots/benchmark_v2_scoreboard.png"),
    ("plots", "plots"),
)

LINK_METRIC_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("Line rate", "metrics", "line_rate_gbps", "Gb/s"),
    ("Empirical BER", "metrics", "ber", "ratio"),
    ("BER upper 95%", "metrics", "ber_upper_95", "ratio"),
    ("FEC margin", "metrics", "fec_margin_db", "dB"),
    ("Eye Q", "metrics", "q_factor_eye", "ratio"),
    ("RX optical power", "budget", "rx_optical_power_dbm", "dBm"),
    ("Static link margin", "budget", "static_margin_db", "dB"),
)

SCOREBOARD_HIGHLIGHT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("Line rate", "link_core", "line_rate_gbps"),
    ("BER upper 95%", "link_core", "ber_upper_95"),
    ("FEC margin", "link_core", "fec_margin_db"),
    ("WDM worst BER", "wdm_worst_channel", "ber"),
    ("Wafer yield", "wafer_proxy", "yield_percent"),
    ("Surrogate BER MAE", "surrogate", "mae_log10_ber"),
    ("CPO energy improvement", "architecture_delta.pluggable_minus_cpo", "energy_pj_per_bit"),
    ("CPO package power improvement", "architecture_delta.pluggable_minus_cpo", "package_power_w"),
    ("CPO latency improvement", "architecture_delta.pluggable_minus_cpo", "latency_ns"),
)


def build_project_report(
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    project_root: str | Path = ".",
    report_out: str | Path = DEFAULT_REPORT_MARKDOWN_PATH,
    json_out: str | Path = DEFAULT_REPORT_JSON_PATH,
) -> dict[str, object]:
    """Build a deterministic JSON-ready report from existing artifacts."""

    root = Path(project_root)
    manifest_file = _resolve(root, manifest_path)
    manifest = _read_json(manifest_file)
    artifact_paths = _artifact_paths(manifest)
    artifact_summaries = [
        _summarize_artifact(name, path, root) for name, path in artifact_paths.items()
    ]
    available_artifacts = sum(1 for item in artifact_summaries if item["exists"])

    link_payload = _read_json(_resolve(root, artifact_paths.get("link_metrics", "")))
    scoreboard_rows = _read_scoreboard_rows(root, artifact_paths)
    key_link_metrics = _extract_link_metrics(link_payload)
    scoreboard_highlights = _extract_scoreboard_highlights(scoreboard_rows)

    return {
        "schema": REPORT_SCHEMA,
        "project": {
            "name": "photon-link-lab",
            "benchmark": str(manifest.get("benchmark", "unknown")),
            "manifest": _display_path(manifest_file, root),
            "symbols": manifest.get("symbols"),
            "yield_samples": manifest.get("yield_samples"),
        },
        "health": {
            "status": "complete" if available_artifacts == len(artifact_summaries) else "partial",
            "available_artifacts": available_artifacts,
            "expected_artifacts": len(artifact_summaries),
            "scoreboard_rows": len(scoreboard_rows),
            "key_link_metrics": len(key_link_metrics),
        },
        "generated_benchmark_files": artifact_summaries,
        "key_link_metrics": key_link_metrics,
        "scoreboard_highlights": scoreboard_highlights,
        "verification_commands": _verification_commands(
            root=root,
            manifest=manifest,
            manifest_path=manifest_file,
            artifact_paths=artifact_paths,
            report_out=report_out,
            json_out=json_out,
        ),
    }


def render_markdown_report(report: Mapping[str, object]) -> str:
    """Render a Markdown report from a report payload."""

    project = _mapping(report.get("project"))
    health = _mapping(report.get("health"))
    generated_files = _sequence(report.get("generated_benchmark_files"))
    key_metrics = _sequence(report.get("key_link_metrics"))
    highlights = _sequence(report.get("scoreboard_highlights"))
    commands = _sequence(report.get("verification_commands"))

    lines = [
        "# Photon Link Lab Repository Health Report",
        "",
        "A deterministic snapshot of generated benchmark artifacts and link-health signals.",
        "",
        "## Snapshot",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Benchmark | {_md(project.get('benchmark', 'unknown'))} |",
        f"| Manifest | `{_md(project.get('manifest', ''))}` |",
        f"| Artifact coverage | {_format_value(health.get('available_artifacts'))}/"
        f"{_format_value(health.get('expected_artifacts'))} |",
        f"| Scoreboard rows | {_format_value(health.get('scoreboard_rows'))} |",
        f"| Status | {_md(health.get('status', 'unknown'))} |",
        "",
        "## Generated Benchmark Files",
        "",
        "| Artifact | Path | Status | Summary |",
        "| --- | --- | --- | --- |",
    ]

    for item in generated_files:
        artifact = _mapping(item)
        lines.append(
            "| "
            f"{_md(artifact.get('name', ''))} | "
            f"`{_md(artifact.get('path', ''))}` | "
            f"{'present' if artifact.get('exists') else 'missing'} | "
            f"{_md(_artifact_summary_text(artifact))} |"
        )

    lines.extend(
        [
            "",
            "## Key Link Metrics",
            "",
            "| Metric | Value | Unit | Source |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for item in key_metrics:
        metric = _mapping(item)
        lines.append(
            "| "
            f"{_md(metric.get('label', ''))} | "
            f"{_format_value(metric.get('value'))} | "
            f"{_md(metric.get('unit', ''))} | "
            f"{_md(metric.get('source', ''))} |"
        )

    lines.extend(
        [
            "",
            "## Scoreboard Highlights",
            "",
            "| Highlight | Value | Unit | Scoreboard Row |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for item in highlights:
        highlight = _mapping(item)
        row_name = f"{highlight.get('section', '')}.{highlight.get('metric', '')}"
        lines.append(
            "| "
            f"{_md(highlight.get('label', ''))} | "
            f"{_format_value(highlight.get('value'))} | "
            f"{_md(highlight.get('unit', ''))} | "
            f"`{_md(row_name)}` |"
        )

    lines.extend(
        [
            "",
            "## Verification Commands",
            "",
            "| Purpose | Command |",
            "| --- | --- |",
        ]
    )
    for item in commands:
        command = _mapping(item)
        lines.append(
            "| "
            f"{_md(command.get('label', ''))} | "
            f"`{_md(command.get('command', ''))}` |"
        )

    return "\n".join(lines).rstrip() + "\n"


def write_project_report(
    out: str | Path = DEFAULT_REPORT_MARKDOWN_PATH,
    json_out: str | Path = DEFAULT_REPORT_JSON_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    project_root: str | Path = ".",
) -> dict[str, object]:
    """Write Markdown and JSON recruiter reports, returning the JSON payload."""

    report = build_project_report(
        manifest_path=manifest_path,
        project_root=project_root,
        report_out=out,
        json_out=json_out,
    )
    out_path = Path(out)
    json_path = Path(json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown_report(report))
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def _artifact_paths(manifest: Mapping[str, Any]) -> dict[str, str]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return dict(DEFAULT_ARTIFACT_PATHS)
    paths: dict[str, str] = {}
    for default_name, default_path in DEFAULT_ARTIFACT_PATHS:
        value = artifacts.get(default_name, default_path)
        if isinstance(value, str):
            paths[default_name] = value
    for name, value in artifacts.items():
        if isinstance(name, str) and isinstance(value, str) and name not in paths:
            paths[name] = value
    return paths


def _summarize_artifact(name: str, path: str, root: Path) -> dict[str, object]:
    artifact_path = _resolve(root, path)
    summary: dict[str, object] = {
        "name": name,
        "path": _display_path(artifact_path, root),
        "kind": _artifact_kind(artifact_path),
        "exists": artifact_path.exists(),
    }
    if not artifact_path.exists():
        return summary
    if artifact_path.is_dir():
        summary["file_count"] = sum(1 for child in artifact_path.iterdir() if child.is_file())
        return summary
    if artifact_path.suffix.lower() == ".csv":
        summary.update(_csv_summary(artifact_path))
    elif artifact_path.suffix.lower() == ".json":
        payload = _read_json(artifact_path)
        summary["top_level_keys"] = sorted(str(key) for key in payload)
    return summary


def _csv_summary(path: Path) -> dict[str, object]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = sum(1 for _ in reader)
        return {"rows": rows, "columns": list(reader.fieldnames or [])}


def _extract_link_metrics(payload: Mapping[str, Any]) -> list[dict[str, object]]:
    metrics = _mapping(payload.get("metrics"))
    budget = _mapping(payload.get("budget"))
    sections = {"metrics": metrics, "budget": budget}
    rows: list[dict[str, object]] = []
    for label, section, key, unit in LINK_METRIC_SPECS:
        source = sections[section]
        if key not in source:
            continue
        rows.append(
            {
                "label": label,
                "metric": key,
                "value": source[key],
                "unit": unit,
                "source": f"link_metrics.{section}.{key}",
            }
        )
    return rows


def _read_scoreboard_rows(root: Path, artifact_paths: Mapping[str, str]) -> list[dict[str, object]]:
    summary_path = artifact_paths.get("benchmark_v2_summary")
    if summary_path:
        payload = _read_json(_resolve(root, summary_path))
        rows = payload.get("rows")
        if isinstance(rows, list):
            return [_mapping(row) for row in rows if isinstance(row, Mapping)]

    csv_path = artifact_paths.get("benchmark_v2_scoreboard")
    if not csv_path:
        return []
    path = _resolve(root, csv_path)
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _extract_scoreboard_highlights(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    lookup = {
        (str(row.get("section", "")), str(row.get("metric", ""))): row
        for row in rows
    }
    highlights: list[dict[str, object]] = []
    for label, section, metric in SCOREBOARD_HIGHLIGHT_SPECS:
        row = lookup.get((section, metric))
        if row is None:
            continue
        highlights.append(
            {
                "label": label,
                "section": section,
                "metric": metric,
                "value": _coerce_number(row.get("value")),
                "unit": str(row.get("unit", "")),
            }
        )
    return highlights


def _verification_commands(
    root: Path,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    artifact_paths: Mapping[str, str],
    report_out: str | Path,
    json_out: str | Path,
) -> list[dict[str, str]]:
    benchmark_dir = _display_path(manifest_path.parent, root)
    artifacts_dir = _parent_display(artifact_paths.get("link_metrics"), root)
    measured_dir = _parent_display(artifact_paths.get("measured_data"), root)
    plots_dir = str(
        artifact_paths.get("plots")
        or _parent_display(artifact_paths.get("scoreboard_plot"), root)
    )
    symbols = manifest.get("symbols")
    yield_samples = manifest.get("yield_samples")

    benchmark_parts = [
        "python -m photon_link_lab.cli benchmark",
        f"--out {benchmark_dir}",
        f"--artifacts {artifacts_dir}",
        f"--plots {plots_dir}",
        f"--measured {measured_dir}",
    ]
    if isinstance(symbols, int | float):
        benchmark_parts.append(f"--symbols {_format_command_number(symbols)}")
    if isinstance(yield_samples, int | float):
        benchmark_parts.append(f"--yield-samples {_format_command_number(yield_samples)}")

    scoreboard_out = artifact_paths.get(
        "benchmark_v2_scoreboard",
        _default_artifact_path("benchmark_v2_scoreboard"),
    )
    scoreboard_summary = artifact_paths.get(
        "benchmark_v2_summary",
        _default_artifact_path("benchmark_v2_summary"),
    )
    scoreboard_plot = artifact_paths.get(
        "scoreboard_plot",
        _default_artifact_path("scoreboard_plot"),
    )
    scoreboard_command = (
        "python -m photon_link_lab.cli benchmark-v2 "
        f"--out {scoreboard_out} "
        f"--summary {scoreboard_summary} "
        f"--plot {scoreboard_plot}"
    )
    report_command = (
        "python -m photon_link_lab.cli report "
        f"--out {_display_path(_resolve(root, report_out), root)} "
        f"--json-out {_display_path(_resolve(root, json_out), root)}"
    )

    return [
        {"label": "Run the test suite", "command": "python -m pytest"},
        {"label": "Regenerate benchmark artifacts", "command": " ".join(benchmark_parts)},
        {"label": "Regenerate benchmark-v2 scoreboard", "command": scoreboard_command},
        {"label": "Regenerate this report", "command": report_command},
    ]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.is_dir():
        return {}
    return json.loads(path.read_text())


def _default_artifact_path(name: str) -> str:
    return dict(DEFAULT_ARTIFACT_PATHS)[name]


def _resolve(root: Path, path: str | Path) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return root / value


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parent_display(path: str | None, root: Path) -> str:
    if not path:
        return "."
    return _display_path(_resolve(root, path).parent, root)


def _artifact_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "file"


def _artifact_summary_text(artifact: Mapping[str, object]) -> str:
    if not artifact.get("exists"):
        return "not found"
    if "rows" in artifact:
        columns = artifact.get("columns", [])
        column_count = (
            len(columns)
            if isinstance(columns, Sequence) and not isinstance(columns, str)
            else 0
        )
        return f"{_format_value(artifact.get('rows'))} rows, {column_count} columns"
    if "top_level_keys" in artifact:
        keys = artifact.get("top_level_keys")
        if isinstance(keys, Sequence) and not isinstance(keys, str):
            return "keys: " + ", ".join(str(key) for key in keys)
    if "file_count" in artifact:
        return f"{_format_value(artifact.get('file_count'))} files"
    return str(artifact.get("kind", "file"))


def _format_value(value: object) -> str:
    if value is None:
        return ""
    number = _coerce_number(value)
    if isinstance(number, float):
        return f"{number:.6g}"
    return str(number)


def _format_command_number(value: float | int) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.6g}"


def _coerce_number(value: object) -> object:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, str) else []


def _md(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")
