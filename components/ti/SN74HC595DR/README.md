# SN74HC595DR

Texas Instruments 8-bit serial-in parallel-out shift register with 3-state output register in SOIC-16.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- Unused CMOS inputs must not float; undefined SRCLR, SRCLK, RCLK, SER, or OE states can cause excess current, spurious clocks, or unintended outputs.
- The ±35 mA output-current figure is an absolute stress limit, not a guaranteed drive point; logic-level, package-current, switching, and thermal limits govern the usable load.

## Official sources

- [SNx4HC595 8-Bit Shift Registers With 3-State Output Registers](https://www.ti.com/lit/ds/symlink/sn74hc595.pdf)
- [D0016A SOIC package outline and example board layout](https://www.ti.com/lit/pdf/mpds432)
- [SN74HC595DR current exact-part status](https://www.ti.com/product/SN74HC595/part-details/SN74HC595DR)

`component.json` is the canonical machine-readable record.
