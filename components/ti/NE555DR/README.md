# NE555DR

Texas Instruments single bipolar precision timer in SOIC-8.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- RESET must be held at a defined high level when unused, and large charge/discharge currents can disturb the supply and timing threshold without close decoupling.

## Official sources

- [xx555 Precision Timers](https://www.ti.com/lit/ds/symlink/ne555.pdf)
- [NE555DR product and package status](https://www.ti.com/product/NE555/part-details/NE555DR)

`component.json` is the canonical machine-readable record.
