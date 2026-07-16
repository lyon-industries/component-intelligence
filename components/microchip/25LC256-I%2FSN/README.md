# 25LC256-I/SN

Microchip Technology 256-Kbit SPI serial EEPROM in SOIC-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- CS, WP, and HOLD require defined levels; poll write completion before starting the next operation.

## Official sources

- [25LC256 official data sheet](https://ww1.microchip.com/downloads/en/DeviceDoc/25AA256-25LC256-256K-SPI-Bus-Serial-EEPROM-20001822H.pdf)
- [25LC256-I/SN product and orderable identity](https://www.microchip.com/en-us/product/25lc256)

`component.json` is the canonical machine-readable record.
