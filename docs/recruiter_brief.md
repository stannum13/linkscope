# Recruiter Brief

Photon Link Lab is a compact hardware/software simulation project for
silicon-photonic optical interconnects. It is built as an engineering artifact,
not a notebook demo: package code, CLI, tests, CI, deterministic benchmark data,
plots, generated JSON reports, a static dashboard, and technical documentation.

## Role Signal

- Optical interconnect modeling: PAM2/PAM4 symbols, driver, ring or MZI
  modulator, optical loss, photodiode/TIA, receiver noise, equalization, eye
  metrics, BER smoke metrics, and link budget.
- Silicon validation and photonics test workflow: generated ring sweep data,
  least-squares calibration, fitted parameter JSON, calibration plot, and
  synthetic recovery tests.
- AI infrastructure and CPO architecture reasoning: WDM sweep, wafer variation
  proxy, CPO versus pluggable scenario benchmark, and cross-domain scoreboard.
- Production-style software practice: importable Python package, console entry
  point, deterministic seeds, unit/integration tests, CI, reproducible artifacts,
  and concise technical docs.

## Review Artifacts

| Area | Artifact |
|---|---|
| Source package | `src/photon_link_lab/` |
| Tests | `tests/unit/`, `tests/integration/` |
| CLI | `photon-link` entry point in `pyproject.toml` |
| CI | `.github/workflows/ci.yml` |
| Technical narrative | `docs/technical_writeup.md` |
| Equations | `docs/model_equations.md` |
| Benchmark data | `data/benchmarks/*.csv`, `data/benchmarks/manifest.json` |
| Generated reports | `artifacts/demo/*.json`, `artifacts/demo/dashboard.html` |
| Recruiter health report | `artifacts/demo/recruiter_report.md` |
| Plots | `plots/*.png` |

## Commands

```bash
pip install -e ".[dev]"
pytest
python -m photon_link_lab.cli benchmark
python -m photon_link_lab.cli dashboard --out artifacts/demo/dashboard.html
python -m photon_link_lab.cli report
```

Useful focused commands:

```bash
photon-link simulate --pam-order 4 --modulator ring --out artifacts/demo
photon-link calibrate --data data/measured/fake_measured_ring_sweep.csv
photon-link wdm --out data/benchmarks/wdm_sweep.csv
photon-link wafer --out data/benchmarks/wafer_grid.csv
photon-link cpo --out data/benchmarks/cpo_scenarios.csv
photon-link benchmark-v2 --out data/benchmarks/benchmark_v2_scoreboard.csv
photon-link report --out artifacts/demo/recruiter_report.md
```

## Current Capabilities

- End-to-end seeded optical-link simulation with ring and MZI modulator paths.
- Static link budget, BER/eye metrics, Wilson BER upper bound, and FEC-margin
  proxy for short deterministic runs.
- Power, thermal drift, WDM, yield, wafer-map, surrogate, and CPO scenario
  benchmark artifacts.
- Synthetic ring measurement generation and parameter fitting for insertion
  loss, extinction ratio, Q, and resonance wavelength.
- Coarse-to-fine heater tuning baseline and deterministic ridge surrogate for
  BER/Q prediction from generated simulator samples.
- Compact JSON export/import and Verilog-A-style behavioral text export.

## What It Does Not Claim

- No real-silicon or published measurement dataset is included yet.
- BER numbers are smoke metrics from short sequences, not low-BER signoff.
- The CPO benchmark is assumption-driven and does not claim vendor performance.
- The models are behavioral approximations, not EM, TCAD, SPICE, or Verilog-A
  signoff replacements.
- JAX is an optional backend path; the current stochastic simulator is not a
  full differentiable JAX implementation.
