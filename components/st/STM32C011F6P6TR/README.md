# STM32C011F6P6TR

STMicroelectronics 32-bit Arm Cortex-M0+ microcontroller with 32 KB flash in TSSOP20.

## Complete package

This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model.

- Identity verified: `true`
- Data cross-checked: `true`
- Native symbol verified: `true`
- Native footprint verified: `true`
- STEP model verified: `true`
- Physically tested: `false`

## Integration findings

- PA14 is also BOOT0 and the serial-wire clock; loading it incorrectly can block the intended boot or debug path.

## Official sources

- [STM32C011x4/x6 Datasheet](https://www.st.com/resource/en/datasheet/stm32c011f4.pdf)
- [STM32C011F6P6TR product and package status](https://www.st.com/en/microcontrollers-microprocessors/stm32c011f6.html)

`component.json` is the canonical machine-readable record.
