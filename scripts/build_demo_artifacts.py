"""Build the reproducible demo artifact bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

from photon_link_lab.cli import main  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Photon Link Lab demo artifacts")
    parser.add_argument("--quick", action="store_true", help="use smaller CI-friendly runs")
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    if args.quick:
        main(
            [
                "benchmark",
                "--symbols",
                "512",
                "--yield-samples",
                "8",
                "--yield-symbols",
                "128",
            ]
        )
    else:
        main(["benchmark"])
    main(["dashboard", "--out", "artifacts/demo/dashboard.html"])


if __name__ == "__main__":
    run()
