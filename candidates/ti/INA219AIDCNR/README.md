# INA219AIDCNR

Texas Instruments bidirectional current and power monitor with I2C interface in SOT-23-8.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- Current and power register accuracy depends on the external shunt value, Kelvin routing, calibration register, and thermal drift; the IC alone does not establish measurement accuracy.
- The captured INA219 data sheet includes only the D0008A SOIC package drawing and land pattern on pages 33-35; no source-bound DCN body dimensions or land pattern are recorded, so this exact MPN remains excluded from the default catalog.

## Official sources

- [INA219 Zerø-Drift Bidirectional Current/Power Monitor](https://www.ti.com/lit/ds/symlink/ina219.pdf)
- [INA219AIDCNR current exact-part status](https://www.ti.com/product/INA219/part-details/INA219AIDCNR)

`component.json` is the canonical machine-readable record.
