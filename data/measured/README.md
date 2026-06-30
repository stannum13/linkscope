# Measured Data Fixtures

`fake_measured_ring_sweep.csv` is generated synthetic measurement data for the
ring calibration workflow.

Regenerate:

```bash
python -m photon_link_lab.cli generate-data --out data/measured/fake_measured_ring_sweep.csv
```

Schema:

- `wavelength_nm`
- `heater_mw`
- `measured_transmission_db`
- `true_transmission_db`

The dataset validates the calibration pipeline. It is not real silicon data.
