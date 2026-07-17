"""Command line interface for LinkScope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from photon_link_lab.calibration import fit_ring_from_measurements, write_calibration
from photon_link_lab.compact_model import export_compact_model, export_veriloga_style
from photon_link_lab.config import LinkConfig, ModulatorConfig
from photon_link_lab.datasets import generate_synthetic_ring_measurements, read_measurements
from photon_link_lab.devices import ring_derived_metrics, ring_transfer
from photon_link_lab.link import simulate_link
from photon_link_lab.metrics import link_budget
from photon_link_lab.ml import bayesian_like_heater_search
from photon_link_lab.plots import (
    save_ber_sweep,
    save_drift_sweep,
    save_eye_diagram,
    save_ring_fit,
    save_yield_histogram,
)
from photon_link_lab.sweeps import monte_carlo_yield, sweep_thermal_drift, sweep_tx_power, write_csv
from photon_link_lab.units import linear_to_db


def _write_json(path: str | Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def simulate_cmd(args: argparse.Namespace) -> None:
    cfg = LinkConfig(
        pam_order=args.pam_order,
        n_symbols=args.symbols,
        tx_laser_power_dbm=args.power_dbm,
        seed=args.seed,
    )
    mod = ModulatorConfig(kind=args.modulator, heater_mw=args.heater_mw)
    result = simulate_link(cfg, mod, thermal_shift_nm=args.thermal_shift_nm)
    out = Path(args.out)
    _write_json(
        out / "link_metrics.json",
        {
            "config": {
                "pam_order": cfg.pam_order,
                "n_symbols": cfg.n_symbols,
                "symbol_rate_gbaud": cfg.symbol_rate_gbaud,
                "modulator": mod.kind,
            },
            "metrics": result.metrics,
            "budget": result.budget,
            "ring": ring_derived_metrics(mod) if mod.kind == "ring" else {},
        },
    )
    save_eye_diagram(result, out / "eye_diagram.png", cfg.samples_per_symbol)
    export_compact_model(out / "compact_model.json", cfg, mod)
    export_veriloga_style(out / "ring_behavioral.va", cfg, mod)
    print(json.dumps({"metrics": result.metrics, "budget": result.budget}, indent=2))


def generate_data_cmd(args: argparse.Namespace) -> None:
    path = generate_synthetic_ring_measurements(args.out)
    print(path)


def calibrate_cmd(args: argparse.Namespace) -> None:
    result = fit_ring_from_measurements(args.data)
    write_calibration(args.out, result)
    data = read_measurements(args.data)
    mod = ModulatorConfig(
        insertion_loss_db=result.insertion_loss_db,
        extinction_ratio_db=result.extinction_ratio_db,
        q_factor=result.q_factor,
        resonance_wavelength_nm=result.resonance_wavelength_nm,
    )
    fitted = []
    for wl, heater in zip(data["wavelength_nm"], data["heater_mw"], strict=False):
        resonance = mod.resonance_wavelength_nm + heater * mod.tuning_efficiency_nm_per_mw
        fitted.append(linear_to_db(float(ring_transfer(wl, mod, resonance_nm=resonance))))
    save_ring_fit(data, np.asarray(fitted), Path(args.plot))
    print(json.dumps(result.__dict__, indent=2))


def sweep_cmd(args: argparse.Namespace) -> None:
    cfg = LinkConfig(n_symbols=args.symbols)
    rows = sweep_tx_power(np.linspace(args.min_dbm, args.max_dbm, args.points), cfg=cfg)
    write_csv(args.out, rows)
    save_ber_sweep(rows, args.plot)
    print(json.dumps({"rows": len(rows), "csv": args.out, "plot": args.plot}, indent=2))


def drift_cmd(args: argparse.Namespace) -> None:
    cfg = LinkConfig(n_symbols=args.symbols)
    rows = sweep_thermal_drift(np.linspace(args.min_nm, args.max_nm, args.points), cfg=cfg)
    write_csv(args.out, rows)
    if args.plot:
        save_drift_sweep(rows, args.plot)
    print(json.dumps({"rows": len(rows), "csv": args.out, "plot": args.plot}, indent=2))


def yield_cmd(args: argparse.Namespace) -> None:
    cfg = LinkConfig(n_symbols=args.symbols)
    rows = monte_carlo_yield(n=args.samples, cfg=cfg, ber_limit=args.ber_limit)
    write_csv(args.out, rows)
    if args.plot:
        save_yield_histogram(rows, args.plot)
    yield_percent = 100.0 * sum(row["pass"] for row in rows) / len(rows)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "yield_percent": yield_percent,
                "csv": args.out,
                "plot": args.plot,
            },
            indent=2,
        )
    )


def tune_cmd(args: argparse.Namespace) -> None:
    result = bayesian_like_heater_search(thermal_shift_nm=args.thermal_shift_nm)
    _write_json(args.out, result)
    print(json.dumps(result, indent=2))


def budget_cmd(args: argparse.Namespace) -> None:
    cfg = LinkConfig(tx_laser_power_dbm=args.power_dbm)
    mod = ModulatorConfig(kind=args.modulator, heater_mw=args.heater_mw)
    payload = {
        "budget": link_budget(cfg, mod),
        "ring": ring_derived_metrics(mod) if mod.kind == "ring" else {},
    }
    _write_json(args.out, payload)
    print(json.dumps(payload, indent=2))


def benchmark_cmd(args: argparse.Namespace) -> None:
    root = Path(args.out)
    artifacts = Path(args.artifacts)
    plots = Path(args.plots)
    synthetic = Path(args.synthetic)
    cfg = LinkConfig(n_symbols=args.symbols)

    synthetic_path = generate_synthetic_ring_measurements(synthetic / "synthetic_ring_sweep.csv")
    link_result = simulate_link(cfg)
    _write_json(
        artifacts / "link_metrics.json",
        {"metrics": link_result.metrics, "budget": link_result.budget},
    )
    save_eye_diagram(link_result, plots / "eye_diagram.png", cfg.samples_per_symbol)
    export_compact_model(artifacts / "compact_model.json", cfg, ModulatorConfig())
    export_veriloga_style(artifacts / "ring_behavioral.va", cfg, ModulatorConfig())

    power_rows = sweep_tx_power(np.linspace(-4.0, 5.0, 10), cfg=cfg)
    write_csv(root / "tx_power_sweep.csv", power_rows)
    save_ber_sweep(power_rows, plots / "ber_vs_power.png")

    drift_rows = sweep_thermal_drift(np.linspace(-0.2, 0.2, 13), cfg=cfg)
    write_csv(root / "thermal_drift_sweep.csv", drift_rows)
    save_drift_sweep(drift_rows, plots / "thermal_drift.png")

    yield_rows = monte_carlo_yield(
        n=args.yield_samples,
        cfg=LinkConfig(n_symbols=args.yield_symbols),
    )
    write_csv(root / "yield_monte_carlo.csv", yield_rows)
    save_yield_histogram(yield_rows, plots / "yield_histogram.png")

    calibration = fit_ring_from_measurements(synthetic_path)
    write_calibration(artifacts / "calibration.json", calibration)
    data = read_measurements(synthetic_path)
    fit_mod = ModulatorConfig(
        insertion_loss_db=calibration.insertion_loss_db,
        extinction_ratio_db=calibration.extinction_ratio_db,
        q_factor=calibration.q_factor,
        resonance_wavelength_nm=calibration.resonance_wavelength_nm,
    )
    fitted = []
    for wl, heater in zip(data["wavelength_nm"], data["heater_mw"], strict=False):
        resonance = fit_mod.resonance_wavelength_nm + heater * fit_mod.tuning_efficiency_nm_per_mw
        fitted.append(linear_to_db(float(ring_transfer(wl, fit_mod, resonance_nm=resonance))))
    save_ring_fit(data, np.asarray(fitted), plots / "calibration_fit.png")

    tuning = bayesian_like_heater_search(
        cfg=LinkConfig(n_symbols=args.yield_symbols),
        thermal_shift_nm=0.12,
    )
    _write_json(artifacts / "heater_tuning.json", tuning)
    manifest = {
        "benchmark": "linkscope.core.v1",
        "symbols": args.symbols,
        "yield_samples": args.yield_samples,
        "artifacts": {
            "synthetic_calibration_data": str(synthetic_path),
            "tx_power_sweep": str(root / "tx_power_sweep.csv"),
            "thermal_drift_sweep": str(root / "thermal_drift_sweep.csv"),
            "yield_monte_carlo": str(root / "yield_monte_carlo.csv"),
            "link_metrics": str(artifacts / "link_metrics.json"),
            "calibration": str(artifacts / "calibration.json"),
            "heater_tuning": str(artifacts / "heater_tuning.json"),
            "compact_model": str(artifacts / "compact_model.json"),
            "veriloga_style": str(artifacts / "ring_behavioral.va"),
            "plots": str(plots),
        },
    }
    _write_json(root / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Silicon-photonic optical link simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    simulate = sub.add_parser("simulate", help="run an end-to-end link simulation")
    simulate.add_argument("--out", default="artifacts")
    simulate.add_argument("--symbols", type=int, default=4096)
    simulate.add_argument("--pam-order", type=int, choices=[2, 4], default=4)
    simulate.add_argument("--power-dbm", type=float, default=2.0)
    simulate.add_argument("--modulator", choices=["ring", "mzi"], default="ring")
    simulate.add_argument("--heater-mw", type=float, default=0.0)
    simulate.add_argument("--thermal-shift-nm", type=float, default=0.0)
    simulate.add_argument("--seed", type=int, default=7)
    simulate.set_defaults(func=simulate_cmd)

    generate = sub.add_parser("generate-data", help="generate synthetic ring calibration data")
    generate.add_argument("--out", default="data/synthetic/synthetic_ring_sweep.csv")
    generate.set_defaults(func=generate_data_cmd)

    calibrate = sub.add_parser("calibrate", help="fit ring model parameters from calibration data")
    calibrate.add_argument("--data", default="data/synthetic/synthetic_ring_sweep.csv")
    calibrate.add_argument("--out", default="artifacts/calibration.json")
    calibrate.add_argument("--plot", default="plots/calibration_fit.png")
    calibrate.set_defaults(func=calibrate_cmd)

    sweep = sub.add_parser("sweep", help="sweep TX laser power")
    sweep.add_argument("--out", default="data/benchmarks/tx_power_sweep.csv")
    sweep.add_argument("--plot", default="plots/ber_vs_power.png")
    sweep.add_argument("--symbols", type=int, default=2048)
    sweep.add_argument("--min-dbm", type=float, default=-4.0)
    sweep.add_argument("--max-dbm", type=float, default=5.0)
    sweep.add_argument("--points", type=int, default=10)
    sweep.set_defaults(func=sweep_cmd)

    drift = sub.add_parser("drift", help="sweep thermal resonance drift")
    drift.add_argument("--out", default="data/benchmarks/thermal_drift_sweep.csv")
    drift.add_argument("--plot", default="plots/thermal_drift.png")
    drift.add_argument("--symbols", type=int, default=2048)
    drift.add_argument("--min-nm", type=float, default=-0.2)
    drift.add_argument("--max-nm", type=float, default=0.2)
    drift.add_argument("--points", type=int, default=13)
    drift.set_defaults(func=drift_cmd)

    tune = sub.add_parser("tune", help="search heater setting for a drifted ring")
    tune.add_argument("--thermal-shift-nm", type=float, default=0.12)
    tune.add_argument("--out", default="artifacts/heater_tuning.json")
    tune.set_defaults(func=tune_cmd)

    budget = sub.add_parser("budget", help="compute static link budget")
    budget.add_argument("--power-dbm", type=float, default=2.0)
    budget.add_argument("--modulator", choices=["ring", "mzi"], default="ring")
    budget.add_argument("--heater-mw", type=float, default=0.0)
    budget.add_argument("--out", default="artifacts/link_budget.json")
    budget.set_defaults(func=budget_cmd)

    yield_parser = sub.add_parser("yield", help="run a small process-variation sweep")
    yield_parser.add_argument("--samples", type=int, default=64)
    yield_parser.add_argument("--symbols", type=int, default=512)
    yield_parser.add_argument("--ber-limit", type=float, default=1e-3)
    yield_parser.add_argument("--out", default="data/benchmarks/yield_monte_carlo.csv")
    yield_parser.add_argument("--plot", default="plots/yield_histogram.png")
    yield_parser.set_defaults(func=yield_cmd)

    benchmark = sub.add_parser("benchmark", help="regenerate retained core artifacts")
    benchmark.add_argument("--out", default="data/benchmarks")
    benchmark.add_argument("--artifacts", default="artifacts/core")
    benchmark.add_argument("--plots", default="plots")
    benchmark.add_argument("--synthetic", default="data/synthetic")
    benchmark.add_argument("--symbols", type=int, default=2048)
    benchmark.add_argument("--yield-samples", type=int, default=16)
    benchmark.add_argument("--yield-symbols", type=int, default=512)
    benchmark.set_defaults(func=benchmark_cmd)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
