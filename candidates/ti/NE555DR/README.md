# NE555DR

Texas Instruments single bipolar precision timer in SOIC-8.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- RESET must be held at a defined high level when unused, and large charge/discharge currents can disturb the supply and timing threshold without close decoupling.

## Official sources

- [xx555 Precision Timers](https://www.ti.com/lit/ds/symlink/ne555.pdf)

`component.json` is the canonical machine-readable record.
