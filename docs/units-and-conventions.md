# Units and Conventions

## Symbol and Bit Mapping

- PAM order must be a power of two.
- Symbol indices are natural-order integers from `0` to `PAM_order - 1`.
- BER uses Gray-coded symbol bits.
- PAM4 index-to-bit mapping:

| Symbol index | Gray code | Bits |
| ---: | ---: | --- |
| 0 | 0 | `00` |
| 1 | 1 | `01` |
| 2 | 3 | `11` |
| 3 | 2 | `10` |

`ber_proxy` is retained only for historical compatibility as `SER / bits_per_symbol`. FEC comparisons should use bit-counted `ber_upper_95`.

## Optical and Electrical Units

| Quantity | Unit |
| --- | --- |
| Wavelength and resonance shift | nm |
| Laser power | dBm |
| Optical power | W internally, dBm in budgets |
| Photocurrent | A internally, uA in reports |
| TIA gain | ohm |
| TIA output | V internally, mV in budgets |
| Symbol rate | Gbaud |
| Line rate | Gbps |
| Heater power | mW |
| Noise current | A RMS |

## Confidence Bounds

- SER confidence bounds use symbol errors over symbol count.
- BER confidence bounds use Gray-coded bit errors over bit count.
- Wilson upper bounds are used for smoke-scale intervals.
- A zero-error smoke run still has a nonzero upper bound.

## Current Boundary

The retained local simulator is a behavioral approximation. The canonical E001 experiment must document the exact SAX circuit response units and OptiCommPy waveform/channel/DSP conventions before claiming an upstream-backed result.
