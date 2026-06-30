# Model Equations

This document keeps the equations used by the package close to the implementation.

## PAM Symbols

For PAM-M:

```text
levels = {-M+1, -M+3, ..., M-1} / (M-1)
bits_per_symbol = log2(M)
line_rate = symbol_rate * log2(M)
```

NRZ is represented as `pam_order=2`; PAM4 is represented as `pam_order=4`.

## First-Order Bandwidth Model

The driver and receiver use a first-order low-pass approximation:

```text
tau = 1 / (2 pi f_3dB)
alpha = dt / (tau + dt)
y[n] = y[n-1] + alpha * (x[n] - y[n-1])
```

## Ring Resonator

```text
linewidth_nm = lambda_res / Q
detuning = (lambda_laser - lambda_res) / linewidth_nm
depth = 1 - 10^(-ER_dB / 10)
T_ring = 10^(-IL_dB / 10) * [1 - depth / (1 + (2 detuning)^2)]
```

The effective resonance includes heater, voltage, thermal, and process terms:

```text
lambda_res,eff = lambda_res,0
               + eta_heater_nm_per_mw * P_heater
               + eta_voltage_nm_per_v * V
               + thermal_shift_nm
               + process_shift_nm
```

## MZI

```text
phi(V) = pi * V / Vpi + phi_bias
ER_floor = 10^(-ER_dB / 10)
T_mzi = 10^(-IL_dB / 10) * [ER_floor + (1 - ER_floor) * 0.5 * (1 + cos(phi))]
```

## Link Budget

```text
P_tx,W = 1e-3 * 10^(P_tx,dBm / 10)
P_rx,W = P_tx,W * T_mod * 10^(-(L_wg + L_fiber + L_connector) / 10)
I_pd = R_pd * P_rx,W
V_tia = G_tia * I_pd
```

## Detector Noise

```text
sigma_shot = sqrt(2 q I_avg B)
sigma_RIN = I_avg * sqrt(10^(RIN_dB_per_Hz / 10) * B)
sigma_total = sqrt(sigma_shot^2 + sigma_thermal^2 + sigma_RIN^2)
```

The baseline shot-noise model uses average photocurrent for speed and
determinism. A sample-dependent variant is a planned refinement.

## WDM Crosstalk And Dispersion

Channel wavelengths are spaced by converting frequency spacing to wavelength:

```text
delta_lambda ~= lambda_center^2 / c * delta_f
```

The WDM crosstalk matrix uses mux insertion loss on the diagonal and configured
adjacent/non-adjacent leakage terms off diagonal:

```text
P_out[i] = sum_j C[i,j] P_in[j]
```

First-order dispersion spread is reported in unit intervals:

```text
spread_ps = |D| * spectral_width_nm * fiber_length_km
dispersion_ui = spread_ps / UI_ps
```

## Equalizer

The feed-forward equalizer solves:

```text
c = argmin ||X c - s_train||_2
y[k] = sum_i c_i x[k+i]
```

## Eye Metrics And BER

```text
SER = N_symbol_errors / N_symbols
BER ~= SER / log2(PAM_order)
eye_opening_i = mu_{i+1} - mu_i
Q_i = eye_opening_i / (sigma_{i+1} + sigma_i)
Q_eye = min_i Q_i
```
