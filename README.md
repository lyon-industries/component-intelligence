# Component Intelligence

Evidence-bound, qualified component records for agentic electrical engineering.

Component Intelligence is intended to let an engineering agent move from an
exact manufacturer part number to traceable electrical facts, native CAD,
assembly constraints, known failure modes, and bounded test evidence. The
catalog favors a small number of components that can be used correctly over a
large inventory that merely looks complete.

## Admission status

The repository is being hardened to the `agentic-ee-v1` standard. The 20
existing records are source-backed remediation inventory; none is currently
approved for autonomous schematic or PCB placement.

Do not infer readiness from a component directory or an SVG. Read
`validation.release_state` in the exact `component.json`:

- `reference-only`: research and manual cross-checking only
- `candidate`: active qualification work; not admitted
- `agent-ready`: passed the current repository profile

The complete admission contract is [`QUALITY.md`](QUALITY.md).

## What an accepted record provides

- exact manufacturer and orderable MPN identity
- current official sources with exact locators and hashes when bytes can be
  captured
- complete pin semantics and bounded ratings
- package, land-pattern, orientation, assembly, and keep-out constraints
- cross-checked machine-usable symbol, footprint, and applicable 3D assets
- deterministic previews for human review
- automated EDA checks and dated physical assembly evidence
- a bounded functional test of the exact MPN
- known integration failures, remaining limits, and rights provenance

SVG symbol and footprint files are inspection previews. They are not native EDA
assets and never carry manufacturing authority.

## Current inventory

| Manufacturer | Exact MPN | Function | State |
| --- | --- | --- | --- |
| Alpha & Omega Semiconductor | AO3400A | 30 V N-channel MOSFET | Reference only |
| Analog Devices | MAX3485ESA+ | 3.3 V RS-485 transceiver | Reference only |
| Bosch Sensortec | BME280 | Humidity, pressure, and temperature sensor | Reference only |
| Diodes Incorporated | AP63205WU-7 | 5 V synchronous buck converter | Reference only |
| Espressif Systems | ESP32-C3-WROOM-02-N4 | Wi-Fi and Bluetooth LE MCU module | Reference only |
| Littelfuse / C&K | PTS815SJM250SMTRLFS | SMT momentary switch | Reference only |
| Microchip Technology | 24LC256-I/SN | 256-Kbit I2C EEPROM | Reference only |
| Microchip Technology | ATtiny85-20SU | 8-bit AVR microcontroller | Reference only |
| Microchip Technology | MCP73831T-2ACI/OT | Single-cell Li-ion charger | Reference only |
| Nexperia | BAT54C,215 | Dual common-cathode Schottky diode | Reference only |
| STMicroelectronics | STM32C011F6P6TR | Arm Cortex-M0+ microcontroller | Reference only |
| STMicroelectronics | USBLC6-2SC6 | Two-line USB ESD protection | Reference only |
| Texas Instruments | ADS1115IDGSR | 16-bit I2C ADC | Reference only |
| Texas Instruments | INA219AIDCNR | I2C current and power monitor | Reference only |
| Texas Instruments | LM358DR | Dual operational amplifier | Reference only |
| Texas Instruments | NE555DR | Bipolar precision timer | Reference only |
| Texas Instruments | PCA9306DCTR | I2C voltage-level translator | Reference only |
| Texas Instruments | SN74LVC1G17DBVR | Schmitt-trigger buffer | Reference only |
| Texas Instruments | TLV75533PDBVR | 3.3 V low-dropout regulator | Reference only |
| Texas Instruments | TPS62162DSGR | 3.3 V synchronous buck converter | Reference only |

These records preserve useful source normalization and known failures while
they are qualified. They are frozen in `quality/legacy-records.json`; that list
may shrink and cannot grow. New components must pass the agent-ready profile
before merge.

## Using the catalog

Agents can clone the repository, fetch raw files, or use ordinary GitHub tools.
Consumers should pin a Git commit and filter by exact MPN and release state.

```sh
jq -r '.components[] | select(.release_state == "agent-ready") | [.manufacturer, .mpn, .path] | @tsv' catalog.json
jq '.validation.release_state' components/<manufacturer>/<encoded-mpn>/component.json
```

Directory names percent-encode path-reserved characters such as `/`, `+`, and
`,`; record IDs and MPN values retain the manufacturer's exact spelling.

The current decision is to keep Git and JSON as the access interface. An MCP
server and independent product versioning are deferred until real consumers
demonstrate a need.

## Return field evidence

If an agent uses the catalog and discovers a missing component, corrected pin,
bad footprint, assembly issue, moved source, supply constraint, or failed
operating assumption, contribute the result back. The preferred return is a
focused pull request containing the exact MPN, source locators, corrected native
assets, test evidence, and the failure that prompted the change.

Incomplete or confidential findings belong in an issue or draft pull request
with only shareable evidence. Never upload customer or employer material
without permission. Read [`AGENTS.md`](AGENTS.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md) before beginning.

## Validate

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

The validator checks schema, catalog identity, sources, paths, pins, pads,
assets, hashes, rights, frozen legacy debt, and machine-representable admission
rules. Native EDA and physical tests remain additional requirements.

## Repository map

```text
AGENTS.md
catalog.json
components/<manufacturer>/<path-encoded-mpn>/
QUALITY.md
quality/legacy-records.json
schema/component.schema.json
scripts/validate.py
tests/test_validate.py
```

## License and source rights

Original repository content is licensed under Apache-2.0. The `NOTICE` file
preserves Lyon Industries attribution. Manufacturer names and product names are
used only to identify the referenced parts and remain the property of their
owners. Linked vendor documents and CAD are not relicensed or redistributed by
default.
