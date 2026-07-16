# LM358DR

Texas Instruments dual general-purpose operational amplifier in SOIC-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- The input common-mode range includes ground but not the positive rail, and the output is not rail-to-rail; a circuit can saturate while all pins remain within absolute maximum ratings.

## Official sources

- [Industry-Standard Dual Operational Amplifiers](https://www.ti.com/lit/ds/symlink/lm358.pdf)
- [LM358DR product and package status](https://www.ti.com/product/LM358/part-details/LM358DR)

`component.json` is the canonical machine-readable record.
