# LM358DR

Texas Instruments dual general-purpose operational amplifier in SOIC-8.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- The input common-mode range includes ground but not the positive rail, and the output is not rail-to-rail; a circuit can saturate while all pins remain within absolute maximum ratings.

## Official sources

- [Industry-Standard Dual Operational Amplifiers](https://www.ti.com/lit/ds/symlink/lm358.pdf)

`component.json` is the canonical machine-readable record.
