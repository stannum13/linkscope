# Technical Write-Up

## Summary

Photon Link Lab is a behavioral simulator for silicon-photonic optical
interconnects. It models a complete PAM2/PAM4 link from generated symbols
through electrical driver, microring or MZI modulation, optical loss,
photodetection, receiver noise, equalization, and BER/eye metrics. The package
also includes synthetic measured data generation, least-squares calibration, and
a heater tuning search for drift compensation. A first-order WDM helper models
channel wavelength spacing, mux loss, crosstalk, and dispersion UI penalty.
The benchmark-v2 scoreboard joins link BER confidence/FEC margin, WDM
worst-channel behavior, wafer proxy yield, surrogate error, and CPO
architecture metrics into one normalized CSV/JSON artifact.

The goal is architecture exploration and validation workflow prototyping. It is
not a replacement for electromagnetic simulation, SPICE, Verilog-A signoff, or
silicon lab measurement.

For a shorter portfolio entry point, see the [recruiter brief](recruiter_brief.md).

## Signal Chain

The implemented chain is:

```text
PAM4/NRZ symbols
  -> driver bandwidth/noise
  -> microring or MZI modulator
  -> waveguide/fiber/connector loss
  -> photodiode/TIA bandwidth
  -> shot, thermal, RIN, quantization, jitter-like impairments
  -> feed-forward equalizer
  -> eye metrics, SER/BER, confidence-bounded BER, and link budget
```

The orchestrating entry point is `simulate_link()` in `src/photon_link_lab/link.py`.
Each major block is implemented in a separate module so physics models, sweeps,
calibration, and plotting can be tested independently.

## Calibration Flow

The calibration pipeline generates a fake measured ring sweep over wavelength
and heater power. The fitter recovers insertion loss, extinction ratio, Q, and
resonance wavelength using nonlinear least squares. The generated plot overlays
measured and fitted curves, and tests assert recovery tolerances on synthetic
truth.

This validates the data plumbing and fitting workflow. It does not claim
agreement with real silicon until a real or published dataset is added with
source metadata and citation.

## ML And Tuning

The current tuning routine is a deterministic coarse-to-fine search over heater
power. It uses a simulator-derived score based on eye Q and BER penalty. This is
useful as a control baseline and can be replaced by true Bayesian optimization.

`src/photon_link_lab/surrogate.py` adds a deterministic ridge-regression BER/Q
baseline. It generates seeded simulator samples over link power, drive, noise,
jitter, ring Q/loss, heater, wavelength, and thermal shift; splits them into
train/test sets; fits log10 clipped BER and eye-Q targets; and emits a stable
JSON report containing feature names, target names, split counts, train/test
MAE/RMSE/max-error metrics, and fitted coefficients.

The roadmap stages neural surrogate modeling, uncertainty quantification,
active learning, differentiable JAX optimization, controller design, and anomaly
detection only when each feature has a dataset, metric, baseline, and generated
artifact.

## Wafer Process Variation

`src/photon_link_lab/variation.py` adds a deterministic wafer-grid generator for
process and yield visualization. A `WaferGridConfig` defines the clipped wafer
die grid, random seed, and proxy pass/fail tolerances. `VariationConfig`
controls die-local resonance, Q, loss, and responsivity spreads, plus
die-to-die resonance offset and a linear wafer resonance gradient.

Each active die row contains physical coordinates and process fields:
resonance wavelength, resonance shift, Q factor, insertion loss, responsivity,
yield score, and pass/fail flag. The pass/fail proxy is a normalized distance
from nominal device/link fields:

```text
score = 1 / (1 + resonance_penalty^2 + q_penalty^2
               + loss_penalty^2 + responsivity_penalty^2)
pass = score >= threshold
```

The summary schema is intentionally stable for future CLI or plotting wiring:
`total_die`, `passed_die`, `failed_die`, `yield_fraction`, `yield_percent`,
`mean_yield_score`, `median_yield_score`, and `min_yield_score`. This proxy is
for deterministic screening and wafer-map visualization; it is not a substitute
for a full end-to-end BER Monte Carlo over every die.

## CPO Scenario Benchmark

`src/photon_link_lab/cpo.py` adds an assumption-driven architecture benchmark
for retimed pluggable optics versus co-packaged optical I/O. It translates
aggregate bandwidth and lane-rate assumptions into lane count, electrical-loss
proxy, retimer count, energy per bit, package power, latency, heater power, and
link-margin proxy. This connects the component simulator to package-level
optical-I/O questions: power per bit, trace length, retimer/DSP burden, thermal
load, and serviceability. It does not reproduce or claim vendor system
performance.

## Benchmark V2 Scoreboard

`src/photon_link_lab/scoreboard.py` assembles a cross-domain scoreboard from
already-generated benchmark outputs. Rows use the stable schema `section`,
`metric`, `value`, `unit`, and `note`, so the CSV can be diffed in code review
and the JSON can be consumed by dashboards. The scoreboard currently includes:

- core link line rate, empirical BER, 95 percent BER upper bound, FEC-margin
  proxy, eye Q, RX power, and observed symbol errors;
- WDM worst-channel BER/Q plus maximum crosstalk penalty and dispersion skew;
- wafer proxy yield and yield-score statistics;
- surrogate train/test sample counts and held-out MAE/RMSE;
- pluggable-versus-CPO energy, power, latency, retimer, and lane metrics plus
  delta rows.

The FEC field is a margin proxy against a configurable pre-FEC BER threshold.
It does not model an actual FEC code or post-FEC BER.

## Validation Strategy

The test suite checks:

- unit conversion round trips;
- PAM2/PAM4 levels and deterministic symbol generation;
- ring transfer bounds and resonance behavior;
- MZI transfer bounds;
- channel loss and link-budget trends;
- empirical BER, Wilson upper confidence bound, and FEC-margin trend;
- finite end-to-end ring/MZI simulation results;
- WDM wavelength spacing and crosstalk matrix behavior;
- CPO scenario determinism and copper-length retimer/latency trends;
- benchmark-v2 scoreboard schema and CLI artifact generation;
- wafer-grid reproducibility, zero-variation collapse, and worsening yield proxy
  under larger process spreads;
- synthetic calibration recovery;
- deterministic surrogate prediction finiteness, JSON report shape, and
  held-out error sanity;
- CLI smoke paths and benchmark artifact generation.

Benchmark outputs are deterministic for fixed seeds and are generated by the
CLI rather than by notebooks.

## Limitations

- Ring and MZI models are compact behavioral approximations.
- Shot noise uses average current in the baseline implementation.
- Jitter is approximated as slope times timing noise rather than explicit
  waveform resampling.
- Empirical BER and Wilson confidence bounds from short random sequences should
  be interpreted as smoke metrics, not low-BER signoff estimates.
- JAX is not yet used for the full stochastic simulator; planned JAX work should
  focus on smooth differentiable kernels and optimization proxies.
