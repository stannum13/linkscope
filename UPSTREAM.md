# Upstream Substrates

LinkScope is intended to bridge a behavioral silicon-photonic circuit model into a communications-link simulation stack.

| Component | Pin |
| --- | --- |
| SAX repository | `https://github.com/flaport/sax` |
| SAX commit inspected | `910ea69480d479cbbe4e1f23225888ed76d98166` |
| SAX package | `sax==0.18.2` |
| OptiCommPy repository | `https://github.com/edsonportosilva/OptiCommPy` |
| OptiCommPy commit inspected | `a9ed07a188099b4f62acf07399a68a33d0e48a21` |
| OptiCommPy package | `opticommpy==0.10.0` |

Current repository status:

- The retained local code is a NumPy behavioral link scaffold with ring/MZI modulation, detector/TIA noise, FFE equalization, process variation, calibration fitting, and corrected Gray-coded BER accounting.
- SAX and OptiCommPy are not vendored.
- The E001 smoke path validates local BER accounting and retained link/drift artifact generation only.
- A future canonical E001 run should replace local duplicate primitives with SAX circuit response and OptiCommPy waveform/channel/DSP metrics before claiming a substrate-backed result.
