# Photon Link Lab Repository Health Report

A deterministic snapshot of generated benchmark artifacts and link-health signals.

## Snapshot

| Field | Value |
| --- | --- |
| Benchmark | photon-link-lab.v1 |
| Manifest | `data/benchmarks/manifest.json` |
| Artifact coverage | 19/19 |
| Scoreboard rows | 39 |
| Status | complete |

## Generated Benchmark Files

| Artifact | Path | Status | Summary |
| --- | --- | --- | --- |
| measured_data | `data/measured/fake_measured_ring_sweep.csv` | present | 644 rows, 4 columns |
| tx_power_sweep | `data/benchmarks/tx_power_sweep.csv` | present | 10 rows, 6 columns |
| thermal_drift_sweep | `data/benchmarks/thermal_drift_sweep.csv` | present | 13 rows, 5 columns |
| yield_monte_carlo | `data/benchmarks/yield_monte_carlo.csv` | present | 8 rows, 4 columns |
| wdm_sweep | `data/benchmarks/wdm_sweep.csv` | present | 4 rows, 9 columns |
| wafer_grid | `data/benchmarks/wafer_grid.csv` | present | 81 rows, 13 columns |
| wafer_summary | `artifacts/demo/wafer_summary.json` | present | keys: failed_die, mean_yield_score, median_yield_score, min_yield_score, passed_die, total_die, yield_fraction, yield_percent |
| cpo_scenarios | `data/benchmarks/cpo_scenarios.csv` | present | 2 rows, 15 columns |
| cpo_summary | `artifacts/demo/cpo_scenarios.json` | present | keys: scenarios |
| benchmark_v2_scoreboard | `data/benchmarks/benchmark_v2_scoreboard.csv` | present | 39 rows, 5 columns |
| benchmark_v2_summary | `artifacts/demo/benchmark_v2_scoreboard.json` | present | keys: rows, schema |
| link_metrics | `artifacts/demo/link_metrics.json` | present | keys: budget, metrics |
| calibration | `artifacts/demo/calibration.json` | present | keys: extinction_ratio_db, insertion_loss_db, n_points, q_factor, resonance_wavelength_nm, rmse_db |
| heater_tuning | `artifacts/demo/heater_tuning.json` | present | keys: ber, heater_mw, observations, score |
| compact_model | `artifacts/demo/compact_model.json` | present | keys: format, model, units |
| veriloga_style | `artifacts/demo/ring_behavioral.va` | present | va |
| surrogate | `artifacts/demo/surrogate.json` | present | keys: design_parameter_names, feature_names, format, metrics, model, target_names |
| scoreboard_plot | `plots/benchmark_v2_scoreboard.png` | present | png |
| plots | `plots` | present | 10 files |

## Key Link Metrics

| Metric | Value | Unit | Source |
| --- | ---: | --- | --- |
| Line rate | 112 | Gb/s | link_metrics.metrics.line_rate_gbps |
| Empirical BER | 0.12207 | ratio | link_metrics.metrics.ber |
| BER upper 95% | 0.141583 | ratio | link_metrics.metrics.ber_upper_95 |
| FEC margin | -28.4998 | dB | link_metrics.metrics.fec_margin_db |
| Eye Q | 0.999648 | ratio | link_metrics.metrics.q_factor_eye |
| RX optical power | -5.83128 | dBm | link_metrics.budget.rx_optical_power_dbm |
| Static link margin | 10.2966 | dB | link_metrics.budget.static_margin_db |

## Scoreboard Highlights

| Highlight | Value | Unit | Scoreboard Row |
| --- | ---: | --- | --- |
| Line rate | 112 | Gb/s | `link_core.line_rate_gbps` |
| BER upper 95% | 0.141583 | ratio | `link_core.ber_upper_95` |
| FEC margin | -28.4998 | dB | `link_core.fec_margin_db` |
| WDM worst BER | 0.143916 | ratio | `wdm_worst_channel.ber` |
| Wafer yield | 82.716 | % | `wafer_proxy.yield_percent` |
| Surrogate BER MAE | 0.342977 | log10(BER) | `surrogate.mae_log10_ber` |
| CPO energy improvement | 4.945 | pJ/bit | `architecture_delta.pluggable_minus_cpo.energy_pj_per_bit` |
| CPO package power improvement | 494.5 | W | `architecture_delta.pluggable_minus_cpo.package_power_w` |
| CPO latency improvement | 1.85 | ns | `architecture_delta.pluggable_minus_cpo.latency_ns` |

## Verification Commands

| Purpose | Command |
| --- | --- |
| Run the test suite | `python -m pytest` |
| Regenerate benchmark artifacts | `python -m photon_link_lab.cli benchmark --out data/benchmarks --artifacts artifacts/demo --plots plots --measured data/measured --symbols 512 --yield-samples 8` |
| Regenerate benchmark-v2 scoreboard | `python -m photon_link_lab.cli benchmark-v2 --out data/benchmarks/benchmark_v2_scoreboard.csv --summary artifacts/demo/benchmark_v2_scoreboard.json --plot plots/benchmark_v2_scoreboard.png` |
| Regenerate this report | `python -m photon_link_lab.cli report --out artifacts/demo/recruiter_report.md --json-out artifacts/demo/recruiter_report.json` |
