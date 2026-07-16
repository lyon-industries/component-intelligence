# AP63205WU-7

Diodes Incorporated fixed-output synchronous buck converter in TSOT26.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- A generated custom footprint used about 1.9 mm lead pitch where this package requires 0.95 mm pitch; ordinary PCB clearance checks did not detect the package mismatch.
- A completed route passed native geometry checks while placing the input capacitor and switching paths too far from the converter for the datasheet layout intent.

## Official sources

- [AP63200/AP63201/AP63203/AP63205](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf)

`component.json` is the canonical machine-readable record.
