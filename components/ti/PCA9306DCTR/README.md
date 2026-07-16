# PCA9306DCTR

Texas Instruments dual bidirectional I2C and SMBus voltage-level translator in SSOP-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- This pass-FET translator requires the correct VREF bias network and pull-ups on both sides; treating it as a push-pull logic translator can hold the bus at invalid levels.

## Official sources

- [PCA9306 Dual Bidirectional I2C Bus and SMBus Voltage-Level Translator](https://www.ti.com/lit/ds/symlink/pca9306.pdf)
- [PCA9306DCTR product and package status](https://www.ti.com/product/PCA9306/part-details/PCA9306DCTR)

`component.json` is the canonical machine-readable record.
