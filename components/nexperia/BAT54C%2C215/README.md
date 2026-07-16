# BAT54C,215

Nexperia dual common-cathode Schottky barrier diode in SOT-23.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- The two diodes share pin 3 as a common cathode; using a generic dual-diode symbol with the opposite common-node polarity reverses the intended clamp behavior.

## Official sources

- [BAT54C Schottky Barrier Diode](https://assets.nexperia.com/documents/data-sheet/BAT54C.pdf)
- [BAT54C,215 product and orderable identity](https://www.nexperia.com/chemical-content/BAT54C.html)

`component.json` is the canonical machine-readable record.
