# ADS1115IDGSR

Texas Instruments 16-bit four-channel delta-sigma ADC with I2C interface in VSSOP-10.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- The programmable full-scale range does not permit analog inputs beyond the supply rails; confusing PGA range with absolute input limits can damage the ADC or corrupt readings.

## Official sources

- [ADS111x 16-Bit I2C-Compatible ADCs](https://www.ti.com/lit/ds/symlink/ads1115.pdf)

`component.json` is the canonical machine-readable record.
