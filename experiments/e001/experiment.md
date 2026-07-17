# E001: Joint Calibration and Equalization Under Drift

## Status

Preregistered with local smoke coverage. The canonical SAX + OptiCommPy experiment has not run yet, so this repository does not claim that joint optical/DSP adaptation improves BER.

## Question

Does joint ring-bias calibration and digital FFE adaptation maintain lower BER after thermal drift than optical recalibration alone or FFE adaptation alone under a matched training and measurement budget?

## Hypothesis

Joint adaptation should reduce bit-counted BER and SER across drift and process-variation regimes while consuming the same declared training-symbol and detector-measurement budget as the strongest single-domain baseline.

## Baselines

- Fixed nominal ring bias and fixed equalizer.
- Optical recalibration only.
- FFE adaptation only.
- Oracle resonance/channel knowledge as a diagnostic upper bound.

## Treatment

Alternate or jointly optimize bounded heater/bias updates and FFE coefficients from observed training symbols without access to hidden process offsets.

## Controls

- No thermal shift.
- No process variation.
- Perfect nominal model.
- Matched measurement and training-symbol budgets.
- Ring-model perturbation to test model mismatch.

## Metrics

- Actual BER from Gray-coded PAM bit errors.
- SER from symbol errors.
- Separate BER and SER Wilson confidence bounds.
- Eye opening or EVM/GMI where supported by the chosen communications substrate.
- Training symbols and detector measurements consumed.
- Recovery time and heater/actuation cost.
- Worst-seed and worst-channel behavior.

## Promotion Rule

Promote joint adaptation only if corrected BER improves across multiple drift and variation regimes under matched budgets. If DSP-only wins, publish that result and explain the optical-control cost.

## Current Smoke Boundary

The checked-in smoke command validates corrected BER accounting and regenerates a small retained link/drift artifact set:

```bash
scripts/reproduce_e001.sh experiments/e001/configs/smoke.json
```

The canonical config is disabled until SAX and OptiCommPy are wired into the same artifact chain and the task budget is declared.
