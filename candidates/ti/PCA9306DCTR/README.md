# PCA9306DCTR

Texas Instruments dual bidirectional I2C and SMBus voltage-level translator in SSOP-8.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- This pass-FET translator requires the correct VREF bias network and pull-ups on both sides; treating it as a push-pull logic translator can hold the bus at invalid levels.

## Official sources

- [PCA9306 Dual Bidirectional I2C Bus and SMBus Voltage-Level Translator](https://www.ti.com/lit/ds/symlink/pca9306.pdf)

`component.json` is the canonical machine-readable record.
