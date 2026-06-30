"""Export compact behavioral model coefficients."""

from __future__ import annotations

import json
from pathlib import Path

from photon_link_lab.config import LinkConfig, ModulatorConfig


def export_compact_model(path: str | Path, cfg: LinkConfig, mod: ModulatorConfig) -> Path:
    payload = {
        "format": "photon-link-lab.compact.v1",
        "model": {
            "modulator": mod.__dict__,
            "link": {
                "symbol_rate_gbaud": cfg.symbol_rate_gbaud,
                "responsivity_a_per_w": cfg.responsivity_a_per_w,
                "rx_bandwidth_ghz": cfg.rx_bandwidth_ghz,
                "driver_bandwidth_ghz": cfg.driver_bandwidth_ghz,
                "losses_db": {
                    "waveguide": cfg.waveguide_loss_db,
                    "fiber": cfg.fiber_loss_db,
                    "connector": cfg.connector_loss_db,
                },
            },
        },
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path
