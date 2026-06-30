# Photon Link Lab Execution Plan

This plan is keyed directly to the project prompt and the four-agent debate in
`docs/agent_debate.md`.

## Definition Of Done

A reviewer should be able to run:

```bash
pip install -e ".[dev]"
pytest
ruff check .
photon-link benchmark --out data/benchmarks
photon-link simulate --out artifacts/demo
photon-link dashboard --out artifacts/demo/dashboard.html
```

Then the repo should visibly contain:

- README with system diagram, equations, commands, and results.
- Clean package code under `src/photon_link_lab`.
- Unit, integration, CLI, regression, and artifact tests.
- CLI and generated static dashboard.
- Benchmark data and synthetic measured data.
- Plots for eye diagram, BER sweep, calibration fit, drift, and yield.
- CI that validates install, lint, tests, CLI smoke, and artifact generation.
- Technical write-up with assumptions, limitations, and validation.

## Phase 0: Make The Core Demo Runnable

Goal: unblock every downstream artifact.

Tasks:

1. Fix `devices.ring_transfer()` so it handles scalar and array-shaped
   resonance/linewidth values.
2. Add smoke tests for default ring simulation and MZI simulation.
3. Add CLI smoke tests for `simulate`, `generate-data`, `calibrate`, `sweep`,
   `drift`, `tune`, and `dashboard`.
4. Confirm `photon-link simulate --out <tmp>` writes metrics, eye plot, and
   compact model.

Acceptance:

- `simulate_link(LinkConfig(n_symbols=512), ModulatorConfig(kind="ring"))`
  returns finite metrics.
- `simulate_link(... kind="mzi")` returns finite metrics.
- CLI smoke tests pass from a temporary output directory.

## Phase 1: Package, Tests, And CI Baseline

Goal: make the repo behave like a maintainable software project.

Tasks:

1. Harden public API in `src/photon_link_lab/__init__.py`.
2. Add tests:
   - `tests/unit/test_units.py`
   - `tests/unit/test_symbols.py`
   - `tests/unit/test_devices.py`
   - `tests/unit/test_metrics.py`
   - `tests/integration/test_simulate_link.py`
   - `tests/integration/test_cli_smoke.py`
3. Add `.github/workflows/ci.yml`.
4. Add optional `Makefile` targets: `test`, `lint`, `demo`, `bench`.

Acceptance:

- `pip install -e ".[dev]"` works.
- `pytest` passes.
- `ruff check .` passes.
- CI installs the package and runs CLI smoke from the installed entry point.

## Phase 2: Reviewer-Facing Documentation

Goal: make the project understandable in three minutes.

Tasks:

1. Add `README.md` with:
   - one-line description;
   - signal-chain system diagram;
   - quickstart;
   - equations for link budget, ring transfer, MZI transfer, noise, eye/BER;
   - baseline result table;
   - linked plots and datasets;
   - limitations and scope labels.
2. Add `docs/technical_writeup.md`.
3. Add `docs/model_equations.md`.
4. Keep `docs/requirements_traceability.md` current as features land.

Acceptance:

- README links every headline claim to a command, file, test, plot, dataset, or
  write-up section.
- Technical write-up explains behavioral approximations and does not overclaim
  signoff fidelity.

## Phase 3: Deterministic Demo And Benchmark Artifacts

Goal: make all visible results reproducible by command.

Tasks:

1. Add `photon-link budget`.
2. Add `photon-link yield`.
3. Add `photon-link benchmark` to generate canonical artifacts.
4. Add `scripts/build_demo_artifacts.py` or `experiments/make_all_results.py`.
5. Generate:
   - `data/measured/fake_measured_ring_sweep.csv`;
   - `data/benchmarks/tx_power_sweep.csv`;
   - `data/benchmarks/thermal_drift_sweep.csv`;
   - `data/benchmarks/yield_monte_carlo.csv`;
   - `artifacts/demo/link_metrics.json`;
   - `artifacts/demo/calibration.json`;
   - `artifacts/demo/heater_tuning.json`;
   - `artifacts/demo/compact_model.json`;
   - `artifacts/demo/dashboard.html`;
   - `plots/eye_diagram.png`;
   - `plots/ber_vs_power.png`;
   - `plots/calibration_fit.png`;
   - `plots/thermal_drift.png`;
   - `plots/yield_histogram.png`.

Acceptance:

- One command regenerates all README-referenced data and plots with fixed seeds.
- CSV and JSON schemas are tested.
- CI runs a reduced artifact build.

## Phase 4: Base Optical Link Modeling

Goal: complete the prompt's base simulated optical interconnect.

Tasks:

1. Expose NRZ/PAM4 through config and CLI.
2. Expand link budget into a per-stage table.
3. Add ring derived metrics: linewidth, FSR, finesse, detuning.
4. Add thermal coefficient and actuator-limit handling.
5. Add detector noise breakdown to metrics output.
6. Add eye metrics per PAM eye and BER floor/confidence reporting.
7. Add parameter sweeps for TX power, drift, bandwidth, detuning, ER,
   responsivity, and noise.

Acceptance:

- PAM2 and PAM4 simulations pass tests.
- Static link budget matches hand-calculated golden cases.
- Ring minimum occurs near configured resonance.
- Thermal drift worsens margin and heater correction improves it within range.
- Increasing detector noise worsens or preserves Q/BER in the expected direction.

## Phase 5: Calibration And ML Levels 1-2

Goal: deliver credible calibration and tuning without overclaiming.

Tasks:

1. Formalize fake measured data schema with measurement sigma and device id.
2. Test synthetic calibration recovery:
   - insertion loss within about 0.25 dB;
   - extinction ratio within about 0.75 dB;
   - Q within about 10 percent;
   - resonance within about 0.02 nm;
   - RMSE below about 0.15 dB for the fake dataset.
3. Add calibration residual report.
4. Rename current `bayesian_like_heater_search` if it remains coarse-to-fine,
   or implement actual Gaussian-process/TPE-style BO.
5. Compare heater tuning against untuned and grid/random baselines.

Acceptance:

- Calibration has numerical recovery tests.
- Tuning improves a drifted link objective with fewer evaluations than dense
  sweep, or is explicitly documented as coarse-to-fine search.

## Phase 6: Variation And Yield

Goal: demonstrate process-variation and architecture-evaluation signal.

Tasks:

1. Expand `VariationConfig` toward hierarchical wafer/die/device variation.
2. Generate Monte Carlo yield benchmark.
3. Add yield histogram and optional wafer map.
4. Add tests for deterministic seeds, zero-variation collapse, and yield
   degradation under larger variation.

Acceptance:

- `data/benchmarks/yield_monte_carlo.csv` has stable schema.
- Yield result is reproducible by seed.
- README reports pass rate and assumptions.

## Phase 7: Physics Levels 5-8 Extensions

Goal: extend beyond the base artifact only with tests and visible results.

Level 5 WDM:

- Baseline complete: `WDMConfig`, crosstalk matrix, channel spacing,
  first-order dispersion penalty, WDM CLI, CSV, plot, and tests.
- Next refinement: couple crosstalk into waveform-level optical power instead
  of applying a channel metric penalty.

Level 6 process variation:

- Add wafer-gradient and die-to-die models.
- Generate wafer map.

Level 7 compact models:

- Version compact JSON schema.
- Add loader and round-trip tests.
- Optionally export Verilog-A-style text.

Level 8 real/published data:

- Add adapter with source metadata.
- Include citation and license notes before claiming real-data calibration.

## Phase 8: ML Levels 3-8 Extensions

Goal: add AI depth only when backed by datasets, baselines, and metrics.

Level 3 surrogate:

- Train on generated sweeps.
- Report train/test split, MAE/RMSE, parity plot, worst-case error.

Level 4 UQ:

- Bootstrap or ensemble yield intervals.
- Report 5/50/95 percentiles.

Level 5 active learning:

- Select wavelength/heater/power points to reduce uncertainty.
- Compare against random selection.

Level 6 JAX differentiable optimization:

- Move smooth kernels behind a backend abstraction.
- Optimize heater, power, wavelength, or bias against a differentiable margin.

Level 7 RL/MPC:

- Start with MPC/PID baseline before RL.
- Maintain link margin under simulated drift.

Level 8 anomaly detection:

- Inject manufacturing/test anomalies.
- Report precision and recall.

## Scope Rules

- Implemented claims need code, tests, and artifacts.
- Prototype claims need commands and result files but can have lighter tests.
- Future-work claims must not appear as completed README capabilities.
- Notebooks are consumers, never the source of core logic.
- Synthetic data validates the workflow, not real-silicon accuracy.
- The whole stochastic simulator does not need to be JAX-native initially;
  prioritize JAX for smooth differentiable kernels.
