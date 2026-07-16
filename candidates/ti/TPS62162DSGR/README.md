# TPS62162DSGR

Texas Instruments fixed 3.3 V synchronous buck converter in WSON-8 with exposed pad.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- The exposed pad must be soldered to AGND, while PGND and AGND current paths still require deliberate placement; a generic 8-pad footprint is unusable.

## Official sources

- [TPS6216x 3-V to 17-V 1-A Step-Down Converters](https://www.ti.com/lit/ds/symlink/tps62160.pdf)

`component.json` is the canonical machine-readable record.
