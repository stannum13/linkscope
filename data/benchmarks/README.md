# Benchmark Data

The CSV/JSON files in this directory are deterministic benchmark artifacts.

Regenerate:

```bash
python -m photon_link_lab.cli benchmark
```

Expected files:

- `tx_power_sweep.csv`
- `thermal_drift_sweep.csv`
- `yield_monte_carlo.csv`
- `wdm_sweep.csv`
- `wafer_grid.csv`
- `cpo_scenarios.csv`
- `benchmark_v2_scoreboard.csv`
- `manifest.json`

These files are small enough to review and version. Larger sweeps should be
generated outside CI and summarized in the technical write-up.

`benchmark_v2_scoreboard.csv` uses a normalized schema:

```text
section,metric,value,unit,note
```

It joins core link confidence metrics, WDM worst-channel behavior, wafer yield
proxy, surrogate error, and CPO/pluggable architecture metrics.
