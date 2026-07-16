# ADS1115IDGSR

Texas Instruments 16-bit four-channel delta-sigma ADC with I2C interface in VSSOP-10.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- The programmable full-scale range does not permit analog inputs beyond the supply rails; confusing PGA range with absolute input limits can damage the ADC or corrupt readings.

## Official sources

- [ADS111x 16-Bit I2C-Compatible ADCs](https://www.ti.com/lit/ds/symlink/ads1115.pdf)
- [ADS1115IDGSR product and package status](https://www.ti.com/product/ADS1115/part-details/ADS1115IDGSR)

`component.json` is the canonical machine-readable record.
