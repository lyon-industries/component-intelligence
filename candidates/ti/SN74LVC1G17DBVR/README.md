# SN74LVC1G17DBVR

Texas Instruments single noninverting Schmitt-trigger buffer in SOT-23-5.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- Unused CMOS inputs must not float; the Schmitt input tolerates slow edges but does not create a defined logic level without a bias path.

## Official sources

- [SN74LVC1G17 Single Schmitt-Trigger Buffer](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf)

`component.json` is the canonical machine-readable record.
