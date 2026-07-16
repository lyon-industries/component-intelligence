# MAX3485ESA+

Analog Devices 3.3 V half-duplex RS-485 and RS-422 transceiver in SOIC-8 narrow.

## Candidate work

This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package.

- Identity verified: `true`
- Data cross-checked: `false`
- Native symbol verified: `false`
- Native footprint verified: `false`
- STEP model verified: `false`
- Physically tested: `false`

## Integration findings

- The receiver open-circuit fail-safe claim does not replace a defined idle bias for every cable topology, and surge/ESD protection is not established by the base MAX3485 record.

## Official sources

- [MAX3483-MAX3491 3.3V RS-485/RS-422 Transceivers](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX3483-MAX3491.pdf)

`component.json` is the canonical machine-readable record.
