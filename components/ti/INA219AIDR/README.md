# INA219AIDR

Texas Instruments 26 V 12-bit bidirectional current and power monitor with I2C interface in SOIC-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- Measurement accuracy depends on the external shunt, Kelvin routing, calibration register, thermal drift, and bypass placement; the IC package alone does not establish system accuracy.
- The bus register can scale to 32 V, but the applied common-mode voltage must not exceed the device's 26 V input limit.

## Official sources

- [INA219 Zerø-Drift Bidirectional Current/Power Monitor](https://www.ti.com/lit/ds/symlink/ina219.pdf)
- [INA219AIDR current exact-part status](https://www.ti.com/product/INA219/part-details/INA219AIDR)

`component.json` is the canonical machine-readable record.
