# Four-Agent Planning Debate

This document records the orthogonal planning review requested for
`photon-link-lab`. Four agents evaluated the same prompt from different lenses:
photonic physics, software architecture, calibration/ML experiments, and
portfolio/reviewer signal.

## Shared Conclusion

The repository should be built as an engineering simulator, not as a notebook
demo. Notebooks may explain results, but the source of truth must be:

- an installable Python package under `src/photon_link_lab`;
- deterministic CLI commands and scripts that generate data, plots, and reports;
- tests that validate physics trends and artifact generation;
- CI that installs the package, runs tests, and exercises the CLI;
- README and write-up equations that match the code paths.

The current package skeleton already points in the right direction:

- `symbols.py`: PAM/NRZ symbol generation and sampling.
- `devices.py`: driver, ring/MZI modulation, channel loss, photodiode/TIA.
- `link.py`: end-to-end simulation orchestration.
- `metrics.py`: BER/SER, eye metrics, link budget.
- `sweeps.py`: power, drift, and yield-style sweeps.
- `datasets.py`: fake measured ring sweep generation.
- `calibration.py`: ring parameter fitting.
- `ml.py`: heater tuning search.
- `compact_model.py`: compact model export.
- `cli.py`: simulation, calibration, sweep, tuning, and dashboard commands.

The first implementation gate is that the default ring simulation must run
reliably. One agent found a concrete issue: `ring_transfer()` currently uses a
scalar `max()` for linewidth while `modulate()` can pass waveform-shaped
resonance values. Phase 0 must fix that and add a regression test.

## Agent 1: Optical And System Modeling Lens

Primary position: formalize the behavioral physics and validation matrix before
expanding scope.

Recommended signal chain:

```text
PAM4 / NRZ symbols
  -> electrical driver
  -> microring or MZI modulator
  -> waveguide / fiber / connector loss
  -> optional WDM mux + crosstalk + dispersion
  -> photodiode
  -> TIA / receiver bandwidth
  -> shot noise / thermal noise / RIN / jitter / quantization
  -> equalizer
  -> eye diagram / BER / link budget / sweeps / calibration / ML tuning
```

Key equations that must appear in README/write-up:

```text
P_tx,W = 1e-3 * 10^(P_tx,dBm / 10)
L_total,dB = L_mod,dB + L_wg,dB + L_fiber,dB + L_connector,dB
P_rx,dBm = P_tx,dBm - L_total,dB
I_pd = R_pd * P_rx,W
V_tia = G_tia * I_pd
```

```text
linewidth_nm = lambda_res / Q
detuning = (lambda_laser - lambda_res) / linewidth_nm
T_ring(lambda) = IL_linear * [1 - depth / (1 + (2 detuning)^2)]
depth = 1 - 10^(-ER_dB / 10)
```

```text
phi(V) = pi * V / Vpi + phi_bias
T_mzi(V) = IL_linear * [ER_floor + (1 - ER_floor) * 0.5 * (1 + cos(phi))]
ER_floor = 10^(-ER_dB / 10)
```

```text
sigma_shot = sqrt(2 q I_avg B)
sigma_rin = I_avg * sqrt(RIN_linear * B)
sigma_total = sqrt(sigma_shot^2 + sigma_thermal^2 + sigma_rin^2)
```

```text
SER = N_symbol_errors / N_symbols
BER ~= SER / log2(M)
Q_i = (mu_{i+1} - mu_i) / (sigma_{i+1} + sigma_i)
```

Physics recommendation:

- Implement and document Levels 1-4 first: static budget, ring/Q/detuning,
  thermal drift/heater limits, and noise/jitter/quantization.
- Treat Level 5 WDM, Level 6 wafer variation, Level 7 compact models, and
  Level 8 real data calibration as staged expansions unless each has tests and
  artifacts.
- Report empirical BER honestly. For short simulations, use bounded language
  such as `< 1/Nbits` or an eye-Q proxy rather than claiming signoff BER.

## Agent 2: Software Architecture And CI Lens

Primary position: keep the package clean, make the CLI the reproducibility
surface, and validate with CI.

Required architecture:

- `config.py`: immutable dataclasses and schema defaults.
- `symbols.py`: PAM/NRZ generation and sampling.
- `devices.py`: driver, ring/MZI, channel, photodiode/TIA, variability.
- `filters.py`: bandwidth, jitter-like impairment, quantization.
- `equalizer.py`: FFE fitting/application and PAM decisions.
- `metrics.py`: BER/SER, eye metrics, link budget.
- `link.py`: orchestration only.
- `sweeps.py`: architecture exploration and yield studies.
- `datasets.py`: synthetic measurement generation/readers.
- `calibration.py`: physical parameter fitting.
- `ml.py`: heater tuning first, later surrogate/BO/UQ.
- `compact_model.py`: exportable behavioral model.
- `plots.py`: artifact rendering.
- `cli.py`: stable user-facing commands.

CLI contract:

```bash
photon-link simulate --out artifacts
photon-link generate-data --out data/measured/fake_measured_ring_sweep.csv
photon-link calibrate --data data/measured/fake_measured_ring_sweep.csv
photon-link sweep --out data/benchmarks/tx_power_sweep.csv
photon-link drift --out data/benchmarks/thermal_drift_sweep.csv
photon-link tune --thermal-shift-nm 0.12
photon-link dashboard --out artifacts/dashboard.html
```

Commands to add:

```bash
photon-link budget --out artifacts/link_budget.json
photon-link yield --samples 128 --out data/benchmarks/yield_monte_carlo.csv
photon-link benchmark --out data/benchmarks
photon-link report --out artifacts/report.json
```

CI must include:

- lint: `ruff check .`;
- tests: unit, integration, regression;
- package install/build;
- CLI smoke from installed package;
- artifact smoke asserting JSON/CSV/PNG/HTML files exist and parse.

## Agent 3: Calibration, Data, And ML Lens

Primary position: datasets and experiments should be reproducible artifacts,
not notebook-only outputs.

Dataset contract:

- `data/measured/fake_measured_ring_sweep.csv`: wavelength, heater, measured
  transmission, true transmission, measurement sigma, device id.
- `data/synthetic/link_grid.csv`: PAM order, power, bandwidths, loss, drift,
  heater, BER, SER, eye Q, eye opening.
- `data/synthetic/wafer_population.csv`: wafer x/y, die id, resonance offset,
  Q, loss, responsivity, pass/fail.
- `data/benchmarks/tx_power_sweep.csv`: canonical BER/Q/power curve.
- `data/benchmarks/thermal_drift_sweep.csv`: drift degradation and heater
  recovery.
- `data/benchmarks/calibration_recovery.json`: true parameters, fitted
  parameters, confidence/tolerance metrics.

Experiment scripts:

- `experiments/run_baseline_link.py`
- `experiments/run_parameter_sweeps.py`
- `experiments/run_variability_yield.py`
- `experiments/run_calibration.py`
- `experiments/run_heater_locking.py`
- `experiments/train_surrogate.py`
- `experiments/run_uq.py`
- `experiments/run_active_learning.py`
- `experiments/make_all_results.py`

ML ladder recommendation:

- Level 1 regression calibration is mandatory.
- Level 2 heater tuning must be measured against random/grid baselines or
  clearly named coarse-to-fine search if not true Bayesian optimization.
- Level 3 surrogate is useful only with train/test split, parity plot, and
  held-out error.
- Levels 4-8 should be deferred unless each has a dataset, metric, and plot.

## Agent 4: Portfolio And Traceability Lens

Primary position: a reviewer should understand the repo in under three minutes.

Reviewer path:

1. Open `README.md`: see one-line description, system diagram, equations,
   quickstart, results table, plots, and traceability link.
2. Run `pip install -e ".[dev]"`.
3. Run `pytest`.
4. Run `photon-link benchmark`.
5. Inspect `artifacts/demo/dashboard.html`, `plots/*.png`, and
   `data/benchmarks/*.csv`.
6. Read `docs/technical_writeup.md` for assumptions and limitations.

Portfolio priorities:

- Fix core runnable demo first.
- Add README, technical write-up, and traceability.
- Generate deterministic demo and benchmark artifacts.
- Keep notebooks thin and downstream of package APIs.
- Avoid overclaiming real silicon validation until real or cited published data
  is included.

## Consensus Priorities

1. Phase 0: make the end-to-end simulator runnable and tested.
2. Phase 1: create the visible engineering surface: README, docs, tests, CI,
   deterministic artifacts.
3. Phase 2: complete base optical link modeling: NRZ/PAM4, link budget, eye,
   BER, sweeps, variability, thermal drift, detector noise, fake measured data,
   calibration.
4. Phase 3: present physics Levels 1-4 as implemented; mark Levels 5-8 as
   scoped extensions until implemented with tests and plots.
5. Phase 4: present ML Levels 1-2 honestly; add surrogate/UQ/active learning
   only when backed by artifacts.

## Explicit Risks

- Current default ring path has an array/scalar linewidth bug and needs a test.
- The project says Python/JAX, but most current kernels are NumPy-first. Either
  claim optional JAX hooks or refactor differentiable kernels behind `backend.xp`.
- BER estimates from short sequences can be noisy. Use fixed seeds, confidence
  language, and eye-Q proxy estimates.
- Calibration on fake data validates the pipeline, not physical truth.
- Notebooks can weaken the artifact signal if they contain core logic.
- "Bayesian-like" heater search must not be presented as full Bayesian
  optimization unless implemented.
