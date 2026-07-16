# SN74LVC1G17DBVR

Texas Instruments single noninverting Schmitt-trigger buffer in SOT-23-5.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- Unused CMOS inputs must not float; the Schmitt input tolerates slow edges but does not create a defined logic level without a bias path.

## Official sources

- [SN74LVC1G17 Single Schmitt-Trigger Buffer](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf)
- [SN74LVC1G17DBVR product and package status](https://www.ti.com/product/SN74LVC1G17/part-details/SN74LVC1G17DBVR)

`component.json` is the canonical machine-readable record.
