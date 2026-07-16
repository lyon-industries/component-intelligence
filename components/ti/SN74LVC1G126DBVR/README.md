# SN74LVC1G126DBVR

Texas Instruments single buffer with active-high output enable in SOT-23-5.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- Unused CMOS inputs must not float; define every input during reset and power sequencing. Output-enable polarity must be checked before substitution.

## Official sources

- [SN74LVC1G126 official data sheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g126.pdf)
- [SN74LVC1G126DBVR product and orderable identity](https://www.ti.com/product/SN74LVC1G126/part-details/SN74LVC1G126DBVR)

`component.json` is the canonical machine-readable record.
