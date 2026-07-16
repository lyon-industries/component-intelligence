# 24LC256-I/SN

Microchip Technology 256-Kbit I2C serial EEPROM in SOIC-8.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- Writes are page-bounded and require write-cycle completion polling; crossing a 64-byte page without software handling overwrites earlier bytes in that page.

## Official sources

- [24AA256/24LC256/24FC256 256-Kbit I2C Serial EEPROM](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/24AA256-24LC256-24FC256-256K-I2C-Serial-EEPROM-DS20001203.pdf)

`component.json` is the canonical machine-readable record.
