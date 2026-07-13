# Component Intelligence

Evidence-bound component records for electrical, mechanical, assembly, and
manufacturing automation.

This repository uses an inspectable contract instead of an unqualified part
dump. Each record binds one exact manufacturer part number to official
source locators, electrical pins, package dimensions, CAD state, assembly
metadata, known integration failures, rights, and validation state.

## Current catalog

| Manufacturer | Exact MPN | Type | Evidence state | Physical state |
| --- | --- | --- | --- | --- |
| Alpha & Omega Semiconductor | AO3400A | 30 V N-channel MOSFET | Extracted | Not tested |
| Analog Devices | MAX3485ESA+ | 3.3 V RS-485 transceiver | Extracted | Not tested |
| Bosch Sensortec | BME280 | Humidity, pressure, and temperature sensor | Extracted | Not tested |
| Diodes Incorporated | AP63205WU-7 | 5 V synchronous buck converter | Cross-checked | Not tested |
| Espressif Systems | ESP32-C3-WROOM-02-N4 | Wi-Fi and Bluetooth LE MCU module | Extracted | Not tested |
| Littelfuse / C&K | PTS815SJM250SMTRLFS | SMT momentary switch | Cross-checked | Not tested |
| Microchip Technology | 24LC256-I/SN | 256-Kbit I2C EEPROM | Extracted | Not tested |
| Microchip Technology | ATtiny85-20SU | 8-bit AVR microcontroller | Extracted | Not tested |
| Microchip Technology | MCP73831T-2ACI/OT | Single-cell Li-ion charger | Extracted | Not tested |
| Nexperia | BAT54C,215 | Dual common-cathode Schottky diode | Extracted | Not tested |
| STMicroelectronics | STM32C011F6P6TR | 32-bit Arm Cortex-M0+ microcontroller | Extracted | Not tested |
| STMicroelectronics | USBLC6-2SC6 | Two-line USB ESD protection | Extracted | Not tested |
| Texas Instruments | ADS1115IDGSR | 16-bit I2C ADC | Extracted | Not tested |
| Texas Instruments | INA219AIDCNR | I2C current and power monitor | Extracted | Not tested |
| Texas Instruments | LM358DR | Dual operational amplifier | Extracted | Not tested |
| Texas Instruments | NE555DR | Bipolar precision timer | Extracted | Not tested |
| Texas Instruments | PCA9306DCTR | I2C voltage-level translator | Extracted | Not tested |
| Texas Instruments | SN74LVC1G17DBVR | Schmitt-trigger buffer | Extracted | Not tested |
| Texas Instruments | TLV75533PDBVR | 3.3 V low-dropout regulator | Extracted | Not tested |
| Texas Instruments | TPS62162DSGR | 3.3 V synchronous buck converter | Extracted | Not tested |

The catalog deliberately spans power conversion, charging, wireless and wired
interfaces, three microcontroller families, sensing, data conversion, memory,
protection, logic, analog, timing, switching, and electromechanical input.
These records are reference material, not production-approved library parts.
No component has been physically qualified here by incoming inspection,
assembly, or an electrical test.

## What belongs in a record

- exact manufacturer and orderable part identity
- official source URL, revision, retrieval state, hash when bytes can be
  captured, and exact page or figure locators
- pin meaning, ratings, internally common terminals, and conditions
- package dimensions and manufacturer land-pattern data
- symbol, footprint, preview, and STEP-model state
- mounting, packing, orientation, and assembly constraints
- validation state, known integration failures, and physical-test state
- explicit rights and redistribution boundaries

Vendor PDFs and vendor CAD are not mirrored by default. This repository stores
original normalized records and original previews, then links to the official
source. Third-party files should only be added when their license and
provenance are recorded.

## Evidence states

1. Captured: source identity and retrieval are recorded.
2. Extracted: a fact is bound to an exact source locator.
3. Cross-checked: the pin, package, or CAD interpretation has had an independent
   comparison.
4. Physically verified: a dated specimen or assembly test supports the claim.

The catalog stops at extracted or cross-checked evidence. Neither state is
physical proof.

## Validate

    python3 -m pip install -r requirements-dev.txt
    python3 scripts/validate.py

The validator applies the JSON Schema and additional semantic checks: catalog
identity, unique pins, terminal-group references, asset paths, source URLs,
and the rule that an untested part cannot be production-approved.

## Repository map

    catalog.json
    components/<manufacturer>/<path-encoded-mpn>/
      component.json
      README.md
      symbol.svg
      footprint.svg
    schema/component.schema.json
    scripts/validate.py
    docs/source-retrieval-log-2026-07-13.md
    docs/release-validation-log-2026-07-13.md

STEP files, native EDA symbols, and native footprints are expected future asset
roles. Their absence is explicit in the seed records rather than silently
filled with guessed geometry.

Directory names percent-encode path-reserved characters in exact MPNs; the
record and component ID retain the manufacturer spelling unchanged.

## License and source rights

Original repository content is MIT licensed. Manufacturer names and product
names identify the referenced parts and remain the property of their owners.
Linked vendor documents and CAD are not relicensed and are not included.
