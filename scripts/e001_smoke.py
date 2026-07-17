from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

def main() -> int:
    from photon_link_lab.config import LinkConfig
    from photon_link_lab.link import simulate_link
    from photon_link_lab.sweeps import sweep_thermal_drift

    config_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else REPO_ROOT / "experiments/e001/configs/smoke.json"
    )
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    config = json.loads(config_path.read_text())
    if config.get("mode") == "canonical" and not config.get("enabled", True):
        reason = config.get("blocked_reason", "no reason recorded")
        print(f"Canonical E001 is disabled: {reason}", file=sys.stderr)
        return 2

    result_dir = REPO_ROOT / "results/e001"
    result_dir.mkdir(parents=True, exist_ok=True)

    cfg = LinkConfig(n_symbols=int(config["symbols"]), seed=int(config["seed"]))
    nominal = simulate_link(cfg)
    drift_rows = sweep_thermal_drift(config["drift_nm"], cfg=cfg)
    worst_drift = max(drift_rows, key=lambda row: float(row["ber"]))

    summary = {
        "experiment_id": config["experiment_id"],
        "mode": config["mode"],
        "status": "local_smoke_passed",
        "canonical_quality_result": False,
        "symbols": cfg.n_symbols,
        "ber": nominal.metrics["ber"],
        "ber_proxy": nominal.metrics["ber_proxy"],
        "ser": nominal.metrics["ser"],
        "bit_errors": nominal.metrics["bit_errors"],
        "symbol_errors": nominal.metrics["symbol_errors"],
        "ber_upper_95": nominal.metrics["ber_upper_95"],
        "ser_upper_95": nominal.metrics["ser_upper_95"],
        "worst_smoke_drift_nm": worst_drift["thermal_shift_nm"],
        "worst_smoke_drift_ber": worst_drift["ber"],
        "notes": [
            "Smoke output validates local corrected BER accounting and drift "
            "sweep generation only.",
            "It is not a SAX/OptiCommPy canonical joint-adaptation result.",
        ],
    }

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "upstream": config["upstream"],
        "artifacts": {
            "summary_json": "results/e001/summary.json",
            "summary_csv": "results/e001/summary.csv",
            "figure_svg": "results/e001/figure.svg",
        },
        "drift_rows": drift_rows,
    }

    (result_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (result_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    with (result_dir / "summary.csv").open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "experiment_id",
                "mode",
                "status",
                "canonical_quality_result",
                "symbols",
                "ber",
                "ber_proxy",
                "ser",
                "bit_errors",
                "symbol_errors",
                "ber_upper_95",
                "ser_upper_95",
                "worst_smoke_drift_nm",
                "worst_smoke_drift_ber",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow({field: summary[field] for field in writer.fieldnames})

    figure_lines = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="220" '
            'viewBox="0 0 760 220" role="img" aria-labelledby="title desc">'
        ),
        '  <title id="title">E001 smoke status</title>',
        (
            '  <desc id="desc">Local smoke passed; canonical SAX and OptiCommPy '
            "evaluation has not run.</desc>"
        ),
        '  <rect width="760" height="220" fill="#fffaf3"/>',
        (
            '  <rect x="32" y="32" width="696" height="156" fill="#edf2f0" '
            'stroke="#aebdb8"/>'
        ),
        (
            '  <text x="56" y="78" font-family="monospace" font-size="20" '
            'fill="#1f2b28">E001 smoke: local_smoke_passed</text>'
        ),
        (
            '  <text x="56" y="118" font-family="monospace" font-size="15" '
            f'fill="#40514d">BER: {summary["ber"]:.6f}  '
            f'SER: {summary["ser"]:.6f}</text>'
        ),
        (
            '  <text x="56" y="148" font-family="monospace" font-size="15" '
            'fill="#7f4a3e">Canonical SAX/OptiCommPy result: not run</text>'
        ),
        "</svg>",
    ]
    figure = "\n".join(figure_lines) + "\n"
    (result_dir / "figure.svg").write_text(figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
