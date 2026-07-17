# Limitations

## Evidence Status

- E001 has a local smoke artifact only. It is not a SAX + OptiCommPy canonical joint-adaptation result.
- The checked-in smoke validates corrected Gray-coded BER accounting and retained link/drift artifact generation.
- No improvement claim is made for joint optical calibration plus DSP adaptation.

## Model Limits

- The ring model is a behavioral Lorentzian approximation.
- Detector noise combines simple shot, thermal, RIN, quantization, and jitter-like terms; it is not validated against a measured receiver.
- The synthetic ring calibration fixture is generated from the same model family that calibration fits. It checks plumbing and recovery behavior, not real-silicon validity.

## Metric Limits

- BER is counted from Gray-coded PAM hard-decision bit errors.
- SER and BER confidence bounds are computed separately.
- FEC comparisons use the BER bound, not the historical `ber_proxy` field.
- Short smoke runs have wide confidence intervals and should not be used as system-level performance evidence.

## Scope Limits

- Broad exploratory branches for architecture comparisons, search helpers, extra channel modes, generated summaries, and broad modeling helpers were removed from the public main path.
- The package name remains `photon_link_lab` for compatibility; the public research surface is LinkScope.
- SAX and OptiCommPy are pinned as intended substrates but are not yet integrated into the smoke run.

## External Validity

A future positive result applies only to the declared PAM order, drift grid, process-variation distribution, noise regime, model mismatch controls, training budget, and upstream substrate versions used in the canonical configuration.
