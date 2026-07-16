# 24LC256-I/SN

Microchip Technology 256-Kbit I2C serial EEPROM in SOIC-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- Writes are page-bounded and require write-cycle completion polling; crossing a 64-byte page without software handling overwrites earlier bytes in that page.

## Official sources

- [24AA256/24LC256/24FC256 256-Kbit I2C Serial EEPROM](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/24AA256-24LC256-24FC256-256K-I2C-Serial-EEPROM-DS20001203.pdf)
- [24LC256 product status and family package availability](https://www.microchip.com/en-us/product/24LC256)

`component.json` is the canonical machine-readable record.
