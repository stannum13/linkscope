# Baseline Audit

Date: 2026-07-17
Default-branch starting point: `d51109e`

## Baseline Commands

| Command | Result |
| --- | --- |
| `python3 -m pytest -q` | Pass, 69 tests |
| `python3 -m compileall -q src tests` | Pass |
| `python3 -m ruff check .` | Failed; global Python environment did not have Ruff installed |

`uv run --with ruff ruff check .` was available later and passed after the cleanup.

## Code Map Before Cleanup

Canonical paths retained:

- `src/photon_link_lab/link.py`: end-to-end behavioral link simulation.
- `src/photon_link_lab/metrics.py`: link metrics, BER/SER, confidence bounds, and link budget.
- `src/photon_link_lab/symbols.py`: PAM levels and Gray-coded bit mapping.
- `src/photon_link_lab/calibration.py`: ring parameter fit from calibration sweep data.
- `src/photon_link_lab/devices.py`: ring/MZI, driver, channel loss, photodiode/TIA models.
- `src/photon_link_lab/equalizer.py`: FFE fitting and hard PAM decisions.
- `src/photon_link_lab/sweeps.py`: TX power, thermal drift, and process-variation sweeps.

Removed from the public main path:

- Broad exploratory branches for architecture comparisons, search helpers, extra channel modes, generated summaries, and workflow snapshots.
- Generated artifact bundles, plots, notebooks, and process-oriented docs.
- Synthetic calibration data previously labeled as measured.

## Claim Inventory

Supported after cleanup:

- BER is counted from explicit Gray-coded PAM bit errors.
- SER and BER confidence bounds are separate.
- Retained CLI commands regenerate small link, calibration, drift, and process-variation smoke artifacts.
- E001 smoke artifacts are generated from a checked-in command.

Not claimed:

- SAX or OptiCommPy integration result.
- Joint optical/DSP adaptation improvement.
- Real-silicon calibration validity.
- Production architecture, extra channel modes, search-helper, modeling-helper, or optimization results.
