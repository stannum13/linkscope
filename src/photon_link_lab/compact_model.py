"""Export and import compact behavioral model coefficients."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path

from photon_link_lab.config import LinkConfig, ModulatorConfig

COMPACT_FORMAT = "photon-link-lab.compact.v1"
COMPACT_MODEL_FORMAT = COMPACT_FORMAT


def export_compact_model(path: str | Path, cfg: LinkConfig, mod: ModulatorConfig) -> Path:
    payload = {
        "format": COMPACT_FORMAT,
        "units": {
            "wavelength": "nm",
            "power": "dBm or mW where named",
            "bandwidth": "GHz",
            "responsivity": "A/W",
        },
        "model": {
            "modulator": asdict(mod),
            "link_config": asdict(cfg),
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


def load_compact_model(path: str | Path) -> tuple[LinkConfig, ModulatorConfig]:
    payload = json.loads(Path(path).read_text())
    if payload.get("format") != COMPACT_FORMAT:
        raise ValueError(f"unsupported compact model format: {payload.get('format')}")
    model = payload["model"]
    mod = ModulatorConfig(**_dataclass_kwargs(ModulatorConfig, model["modulator"]))
    link_payload = model.get("link_config")
    if link_payload is None:
        link = LinkConfig(
            symbol_rate_gbaud=model["link"]["symbol_rate_gbaud"],
            responsivity_a_per_w=model["link"]["responsivity_a_per_w"],
            rx_bandwidth_ghz=model["link"]["rx_bandwidth_ghz"],
            driver_bandwidth_ghz=model["link"]["driver_bandwidth_ghz"],
            waveguide_loss_db=model["link"]["losses_db"]["waveguide"],
            fiber_loss_db=model["link"]["losses_db"]["fiber"],
            connector_loss_db=model["link"]["losses_db"]["connector"],
        )
    else:
        link = LinkConfig(**_dataclass_kwargs(LinkConfig, link_payload))
    return link, mod


def compact_model_to_verilog_a(
    cfg: LinkConfig,
    mod: ModulatorConfig,
    module_name: str | None = None,
) -> str:
    """Return readable Verilog-A-style behavioral text.

    The output is intentionally not foundry-ready Verilog-A. It is a portable
    compact-model artifact that records equations, units, and valid assumptions.
    """

    kind = mod.kind.lower()
    if kind not in {"ring", "mzi"}:
        raise ValueError(f"unsupported modulator kind for text export: {mod.kind}")

    module = module_name or f"photon_link_lab_{kind}_behavioral"
    lines = [
        "// Photon Link Lab behavioral compact model",
        "// Verilog-A-style parameter export; not foundry-ready Verilog-A.",
        f"// format: {COMPACT_FORMAT}",
        "// Units are shown on each parameter declaration.",
        f"// modulator_kind: {kind}",
        f"module {module}(optical_in, optical_out, drive);",
        "  inout optical_in, optical_out, drive;",
        "  // Ports are placeholders for downstream Verilog-A discipline binding.",
        "",
    ]
    lines.extend(_common_parameter_lines(cfg, mod))
    if kind == "ring":
        lines.extend(_ring_parameter_lines(mod))
        lines.extend(_ring_equation_lines())
    else:
        lines.extend(_mzi_parameter_lines(mod))
        lines.extend(_mzi_equation_lines())
    lines.append("endmodule")
    return "\n".join(lines)


def export_veriloga_style(
    path: str | Path,
    cfg: LinkConfig,
    mod: ModulatorConfig,
    module_name: str | None = None,
) -> Path:
    """Write readable Verilog-A-style behavioral text."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compact_model_to_verilog_a(cfg, mod, module_name=module_name) + "\n")
    return path


def export_verilog_a_model(
    path: str | Path,
    cfg: LinkConfig,
    mod: ModulatorConfig,
    module_name: str | None = None,
) -> Path:
    """Write readable Verilog-A-style behavioral text."""

    return export_veriloga_style(path, cfg, mod, module_name=module_name)


def _dataclass_kwargs(dataclass_type: type, values: dict) -> dict:
    field_names = {field.name for field in fields(dataclass_type)}
    return {key: value for key, value in values.items() if key in field_names}


def _format_value(value: float | int) -> str:
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _parameter_line(name: str, value: float | int, unit: str, note: str) -> str:
    return f"  parameter real {name} = {_format_value(value)}; // {unit} - {note}"


def _common_parameter_lines(cfg: LinkConfig, mod: ModulatorConfig) -> list[str]:
    return [
        _parameter_line(
            "insertion_loss_db",
            mod.insertion_loss_db,
            "dB",
            "modulator insertion loss",
        ),
        _parameter_line(
            "extinction_ratio_db",
            mod.extinction_ratio_db,
            "dB",
            "modulator extinction ratio",
        ),
        _parameter_line(
            "symbol_rate_gbaud",
            cfg.symbol_rate_gbaud,
            "Gbaud",
            "link symbol rate",
        ),
        _parameter_line(
            "wavelength_nm",
            cfg.wavelength_nm,
            "nm",
            "laser wavelength",
        ),
        _parameter_line(
            "driver_bandwidth_ghz",
            cfg.driver_bandwidth_ghz,
            "GHz",
            "electrical driver 3 dB bandwidth",
        ),
        _parameter_line(
            "rx_bandwidth_ghz",
            cfg.rx_bandwidth_ghz,
            "GHz",
            "receiver 3 dB bandwidth",
        ),
        _parameter_line(
            "responsivity_a_per_w",
            cfg.responsivity_a_per_w,
            "A/W",
            "photodiode responsivity",
        ),
        _parameter_line("waveguide_loss_db", cfg.waveguide_loss_db, "dB", "waveguide loss"),
        _parameter_line("fiber_loss_db", cfg.fiber_loss_db, "dB", "fiber loss"),
        _parameter_line("connector_loss_db", cfg.connector_loss_db, "dB", "connector loss"),
        "",
    ]


def _ring_parameter_lines(mod: ModulatorConfig) -> list[str]:
    return [
        _parameter_line("q_factor", mod.q_factor, "unitless", "loaded quality factor"),
        _parameter_line(
            "resonance_wavelength_nm",
            mod.resonance_wavelength_nm,
            "nm",
            "cold resonance wavelength",
        ),
        _parameter_line("fsr_nm", mod.fsr_nm, "nm", "free spectral range"),
        _parameter_line(
            "tuning_efficiency_nm_per_mw",
            mod.tuning_efficiency_nm_per_mw,
            "nm/mW",
            "heater tuning coefficient",
        ),
        _parameter_line(
            "voltage_tuning_nm_per_v",
            mod.voltage_tuning_nm_per_v,
            "nm/V",
            "voltage tuning coefficient",
        ),
        _parameter_line("heater_max_mw", mod.heater_max_mw, "mW", "heater limit"),
        _parameter_line("heater_mw", mod.heater_mw, "mW", "heater operating point"),
        "",
    ]


def _mzi_parameter_lines(mod: ModulatorConfig) -> list[str]:
    return [
        _parameter_line("vpi_v", mod.vpi_v, "V", "pi phase-shift voltage"),
        _parameter_line("phase_bias_rad", mod.phase_bias_rad, "rad", "phase bias"),
        _parameter_line("phase_noise_rad", mod.phase_noise_rad, "rad", "phase noise rms"),
        "",
    ]


def _ring_equation_lines() -> list[str]:
    return [
        "  analog begin",
        "    // Ring equation:",
        "    // linewidth_nm = resonance_wavelength_nm / q_factor;",
        "    // depth = 1.0 - pow(10.0, -extinction_ratio_db / 10.0);",
        "    // resonance_eff_nm = resonance_wavelength_nm",
        "    //                  + heater_mw * tuning_efficiency_nm_per_mw",
        "    //                  + V(drive) * voltage_tuning_nm_per_v;",
        "    // detuning = (wavelength_nm - resonance_eff_nm) / linewidth_nm;",
        "    // T = pow(10.0, -insertion_loss_db / 10.0)",
        "    //     * (1.0 - depth / (1.0 + pow(2.0 * detuning, 2.0)));",
        "  end",
    ]


def _mzi_equation_lines() -> list[str]:
    return [
        "  analog begin",
        "    // MZI equation:",
        "    // phi_rad = 3.141592653589793 * V(drive) / vpi_v + phase_bias_rad;",
        "    // er_floor = pow(10.0, -extinction_ratio_db / 10.0);",
        "    // T = pow(10.0, -insertion_loss_db / 10.0)",
        "    //     * (er_floor + (1.0 - er_floor) * 0.5 * (1.0 + cos(phi_rad)));",
        "  end",
    ]
