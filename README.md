# Photon Link Lab

A Python package for behavioral silicon-photonic optical link simulation, from
PAM4/NRZ symbols through modulator, channel, photodiode/TIA, equalization, eye
metrics, BER estimation, calibration, and heater tuning. It uses NumPy by
default and includes an optional JAX array-backend path for future
differentiable kernels.

The project is organized as a portfolio-ready engineering artifact: importable
package code, CLI, deterministic datasets, tests, plots, CI, notebooks, a static
dashboard, and technical documentation. Notebooks are walkthroughs only; the
simulator lives in `src/photon_link_lab`.

## Portfolio Entry Points

- [Recruiter brief](docs/recruiter_brief.md): role signal, review artifacts,
  commands, current capabilities, and limitations.
- [Technical write-up](docs/technical_writeup.md): model assumptions,
  validation strategy, calibration flow, WDM, wafer variation, CPO scenarios,
  and benchmark scoreboard scope.
- [Requirements traceability](docs/requirements_traceability.md): mapping from
  prompt requirements to package, CLI, data, plots, tests, CI, and docs.

## System Diagram

```mermaid
flowchart LR
  A[PAM4 / NRZ symbols] --> B[Electrical driver<br/>Vpp, bandwidth, noise]
  B --> C{Modulator}
  C --> D[Microring<br/>Q, detuning, heater]
  C --> E[MZI<br/>Vpi, bias, ER]
  D --> F[Waveguide / fiber / connector loss]
  E --> F
  F --> G[Photodiode + TIA<br/>responsivity, bandwidth]
  G --> H[Noise<br/>shot, thermal, RIN, jitter, quantization]
  H --> I[FFE equalizer]
  I --> J[Eye metrics / BER / link budget]
  K[Fake measured ring data] --> L[Calibration]
  L --> D
  M[Heater tuning search] --> D
```

## Quickstart

```bash
pip install -e ".[dev]"
pytest
python -m photon_link_lab.cli simulate --out artifacts/demo
python -m photon_link_lab.cli benchmark
python -m photon_link_lab.cli benchmark-v2
python -m photon_link_lab.cli dashboard --out artifacts/demo/dashboard.html
python -m photon_link_lab.cli report
```

Installed entry point:

```bash
photon-link simulate --pam-order 4 --modulator ring --out artifacts/demo
photon-link generate-data --out data/measured/fake_measured_ring_sweep.csv
photon-link calibrate --data data/measured/fake_measured_ring_sweep.csv
photon-link sweep --out data/benchmarks/tx_power_sweep.csv
photon-link drift --out data/benchmarks/thermal_drift_sweep.csv
photon-link yield --out data/benchmarks/yield_monte_carlo.csv
photon-link wdm --out data/benchmarks/wdm_sweep.csv
photon-link cpo --out data/benchmarks/cpo_scenarios.csv
photon-link benchmark-v2 --out data/benchmarks/benchmark_v2_scoreboard.csv
photon-link tune --thermal-shift-nm 0.12
photon-link report --out artifacts/demo/recruiter_report.md
photon-link benchmark
```

## Core Equations

Static link budget:

```text
P_tx,W = 1e-3 * 10^(P_tx,dBm / 10)
L_total,dB = L_mod,dB + L_waveguide,dB + L_fiber,dB + L_connector,dB
P_rx,W = P_tx,W * 10^(-L_total,dB / 10)
I_pd = R_pd * P_rx,W
V_tia = G_tia * I_pd
```

Microring through-port notch model:

```text
linewidth_nm = lambda_res / Q
detuning = (lambda_laser - lambda_res) / linewidth_nm
depth = 1 - 10^(-ER_dB / 10)
T_ring = 10^(-IL_dB / 10) * [1 - depth / (1 + (2 detuning)^2)]
```

MZI transfer:

```text
phi(V) = pi * V / Vpi + phi_bias
ER_floor = 10^(-ER_dB / 10)
T_mzi = 10^(-IL_dB / 10) * [ER_floor + (1 - ER_floor) * 0.5 * (1 + cos(phi))]
```

Detector noise:

```text
sigma_shot = sqrt(2 q I_avg B)
sigma_RIN = I_avg * sqrt(RIN_linear * B)
sigma_total = sqrt(sigma_shot^2 + sigma_thermal^2 + sigma_RIN^2)
```

Wafer yield proxy:

```text
score = 1 / (1 + resonance_penalty^2 + q_penalty^2
               + loss_penalty^2 + responsivity_penalty^2)
pass = score >= threshold
```

Empirical BER estimate:

```text
SER = symbol_errors / symbols
BER ~= SER / log2(PAM_order)
Q_eye = min_i (mu_{i+1} - mu_i) / (sigma_{i+1} + sigma_i)
```

BER confidence and FEC-margin proxy:

```text
p_hat = symbol_errors / symbols
SER_upper,95 = WilsonUpper(p_hat, symbols, 95%)
BER_upper,95 ~= SER_upper,95 / log2(PAM_order)
FEC_margin_dB = 10 log10(BER_FEC_threshold / BER_upper,95)
```

## Current Results

The canonical artifact bundle is regenerated with:

```bash
python -m photon_link_lab.cli benchmark
python -m photon_link_lab.cli dashboard --out artifacts/demo/dashboard.html
python -m photon_link_lab.cli report
```

Together these commands regenerate:

| Artifact | Path |
|---|---|
| Fake measured ring sweep | `data/measured/fake_measured_ring_sweep.csv` |
| TX power sweep | `data/benchmarks/tx_power_sweep.csv` |
| Thermal drift sweep | `data/benchmarks/thermal_drift_sweep.csv` |
| Monte Carlo yield | `data/benchmarks/yield_monte_carlo.csv` |
| WDM channel sweep | `data/benchmarks/wdm_sweep.csv` |
| Wafer process grid | `data/benchmarks/wafer_grid.csv` |
| CPO scenario benchmark | `data/benchmarks/cpo_scenarios.csv` |
| Benchmark v2 scoreboard | `data/benchmarks/benchmark_v2_scoreboard.csv` |
| Link metrics | `artifacts/demo/link_metrics.json` |
| Calibration result | `artifacts/demo/calibration.json` |
| Heater tuning result | `artifacts/demo/heater_tuning.json` |
| Surrogate report | `artifacts/demo/surrogate.json` |
| Benchmark v2 summary | `artifacts/demo/benchmark_v2_scoreboard.json` |
| Recruiter health report | `artifacts/demo/recruiter_report.md` |
| Dashboard | `artifacts/demo/dashboard.html` |

Current quick-demo metrics:

| Metric | Value |
|---|---:|
| PAM order | 4 |
| Symbol count | 512 |
| Empirical BER | 0.122 |
| 95% BER upper bound | 0.142 |
| FEC-margin proxy | -28.5 dB |
| Eye Q | 1.000 |
| RX optical power | -5.83 dBm |
| Photocurrent | 214 uA |
| Wafer proxy yield | 82.7% |
| CPO energy delta | 4.95 pJ/bit lower for CPO scenario |
| Calibration RMSE | 0.083 dB |
| Fitted Q | 8461 |

Representative plots:

![Eye diagram](plots/eye_diagram.png)

![BER versus power](plots/ber_vs_power.png)

![Calibration fit](plots/calibration_fit.png)

![Thermal drift](plots/thermal_drift.png)

![Yield histogram](plots/yield_histogram.png)

![WDM channel BER](plots/wdm_channel_ber.png)

![Wafer map](plots/wafer_map.png)

![Surrogate parity](plots/surrogate_parity.png)

![CPO scenarios](plots/cpo_scenarios.png)

![Benchmark v2 scoreboard](plots/benchmark_v2_scoreboard.png)

## Implemented Scope

Base optical interconnect:

- PAM2/NRZ and PAM4 symbols.
- Electrical driver bandwidth and driver voltage noise.
- Microring or MZI modulator.
- Waveguide, fiber, and connector loss.
- Photodiode/TIA bandwidth and detector noise.
- Shot noise, thermal noise, RIN, quantization, and jitter-like impairment.
- Feed-forward equalizer.
- Eye diagram, eye-Q metrics, empirical SER/BER, confidence-bounded BER,
  FEC-margin proxy, and link budget.
- Parameter sweeps, thermal drift sweeps, and Monte Carlo device variability.
- Deterministic wafer-grid process variation with resonance, Q, loss,
  responsivity, yield score, and pass/fail fields for wafer-map visualization.
- WDM channel wavelength spacing, crosstalk matrix, and first-order dispersion
  penalty reporting.
- Fake measured ring data and least-squares ring calibration.
- Coarse-to-fine heater tuning search for resonance locking.
- Deterministic ridge surrogate for log10 clipped BER and eye-Q prediction from
  generated simulator samples.
- Compact JSON export/import plus Verilog-A-style behavioral text export for
  ring and MZI model parameters.
- Assumption-driven CPO/pluggable architecture scenarios for energy per bit,
  retimer count, package power, and latency.
- Benchmark v2 scoreboard joining link BER/FEC margin, WDM worst-channel
  behavior, wafer proxy yield, surrogate error, and CPO architecture metrics.

Physics ladder status:

| Level | Status |
|---|---|
| 1 static link budget | Implemented |
| 2 ring transfer, detuning, Q, FSR, linewidth | Implemented |
| 3 thermal drift, heater tuning, actuator limits | Implemented baseline |
| 4 shot, thermal, RIN, quantization, jitter | Implemented baseline |
| 5 WDM, crosstalk, dispersion | Baseline implemented |
| 6 process/wafer statistics | Monte Carlo baseline and deterministic wafer grid implemented |
| 7 compact models | JSON export/import and Verilog-A-style text export implemented |
| 8 real/published data calibration | Synthetic calibration implemented; real/published adapter planned |

ML ladder status:

| Level | Status |
|---|---|
| 1 regression fit of physical parameters | Implemented |
| 2 heater tuning / resonance locking | Coarse-to-fine implemented; true BO planned |
| 3 BER/Q surrogate | Deterministic ridge baseline implemented; neural model planned |
| 4 uncertainty quantification | Planned |
| 5 active learning | Planned |
| 6 differentiable JAX optimization | Planned for smooth kernels |
| 7 RL/MPC drift controller | Planned |
| 8 anomaly detection | Planned |

## Repository Layout

```text
src/photon_link_lab/        package code
tests/                      unit and integration tests
docs/                       technical write-up, equations, traceability, debate
data/measured/              generated fake measurement data
data/benchmarks/            deterministic benchmark CSV/JSON files
plots/                      generated figures
artifacts/demo/             generated JSON reports and dashboard
notebooks/                  thin walkthrough notebooks
scripts/                    reproducibility helpers
.github/workflows/ci.yml    CI
```

## Wafer Variation API

`photon_link_lab.variation.generate_wafer_grid()` returns one row per active die
inside the wafer radius. Row fields are `die_index`, `row`, `col`, `x_mm`,
`y_mm`, `radius_norm`, `resonance_wavelength_nm`, `resonance_shift_nm`,
`q_factor`, `insertion_loss_db`, `responsivity_a_per_w`, `yield_score`, and
`pass`.

`summarize_pass_fail()` returns a stable summary schema: `total_die`,
`passed_die`, `failed_die`, `yield_fraction`, `yield_percent`,
`mean_yield_score`, `median_yield_score`, and `min_yield_score`.

## CPO Scenario Benchmark

`photon_link_lab.cpo` compares explicit architecture assumptions for retimed
pluggable optics and co-packaged optical I/O. It reports lane count,
electrical-loss proxy, retimer count, energy per bit, package power, latency,
heater power, and link-margin proxy. These are scenario calculations for
architecture reasoning, not vendor performance claims.

## Limitations

This is a behavioral simulator, not an electromagnetic, TCAD, SPICE, or
Verilog-A signoff tool. BER values and Wilson upper bounds from short random
sequences are smoke metrics; low-BER claims should use longer runs,
Gray-code-aware bit counting, bathtub extrapolation, or measured data.
The fake measured data validates the calibration workflow, not real-silicon
accuracy. JAX support is currently scoped as an optional backend direction for
smooth differentiable kernels rather than a full stochastic JAX rewrite.
The CPO scenario layer uses stated assumptions and should not be read as a
claim of production CPO power, latency, or bandwidth.
