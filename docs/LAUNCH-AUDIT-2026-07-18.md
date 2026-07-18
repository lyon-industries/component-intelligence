# Launch-readiness audit — 2026-07-18

## Decision

**Would an electrical engineer use this?** Yes—as a source-traceable component
preflight dataset and a reviewable native-CAD starting point. No—as an
unreviewed drop-in production library.

The useful distinction is evidence compression. A package keeps exact identity,
official-source locators, normalized pin and pad data, native assets, limitations,
and integration findings together. It can remove repetitive transcription and
source hunting. It cannot transfer responsibility for circuit, footprint,
process, supply, or physical qualification to the repository.

## Audit baseline

The pre-sprint state contained 40 complete packages, 6 candidates, 50 findings,
and no physical-test evidence. The catalog was concentrated in TI parts and
SOT-23/SOT-23-5/SOIC-8 packages. It had no exact-MPN passives, inductors, or
LEDs, and no human KiCad onboarding.

The first upstream KiCad-library audit found at least one convention failure in
every footprint and every generator-produced symbol. The important failures
were not cosmetic: nine Nexperia footprints had silkscreen intersecting pad
clearance, reserved MPN characters leaked into native names, and the generated
files used an obsolete syntax contract. README language also implied a broader
and more independently qualified library than the evidence supported.

## Implemented corrections

- moved the generator to KiCad 10 syntax with deterministic KiCad-safe native
  names while preserving exact MPN identity in records and symbol values
- added conventional two-terminal passive symbols, a switch symbol, functional
  pin grouping, power/ground placement, current fab fields, pin-one markers,
  clipped silkscreen, and 0.05 mm-grid courtyards
- made validation replay the native files and compare exact pin names,
  electrical types, duplicate-safe pads, layers, silk clearance, model paths,
  STEP seating, and envelope measurements
- added four manufacturer-specific Würth parts: 10 kΩ 0603 resistor, 100 nF
  0603 MLCC, 10 µH power inductor, and red 0603 LED
- added TI INA219AIDR and SN74HC595DR packages from current official data sheets,
  package drawings, and exact-part pages
- corrected the INA219AIDCNR candidate by removing a false DCN land-pattern
  locator; the captured data sheet only contains the D-package geometry, so the
  candidate now carries a fabrication-stop source gap
- added generated KiCad project tables, a human catalog, native KiCad 10 audit
  tooling, issue forms, security reporting, and a practical KiCad acceptance
  checklist
- rewrote README and quality claims around the actual local gate and added a
  provenance-labeled repository/social preview

## Verification result

- repository validation: 46 complete, 6 candidates, 59 findings, 0 physically
  tested
- Python tests: 23 passed
- upstream KLC symbol checker: 46/46 passed with footprint resolution
- upstream KLC footprint checker: only the documented F9.3 path deviation
  remains across the 46 self-contained STEP links
- native KiCad 10.0.4 CLI: 46/46 symbols and 46/46 footprints opened and
  exported successfully

The KLC run used upstream `kicad-library-utils` commit
`f733308c80768a7d42d0f92284f61abf7e6f3ec0`. See [`KICAD.md`](KICAD.md) for
the exact F9.3 tradeoff.

## Remaining limits

- no package has dated physical assembly or measurement evidence
- most IC and multi-terminal discrete symbols are compact functional blocks,
  not a replacement for every organization's preferred conventional or
  multi-unit schematic style
- STEP models are source-dimensioned nominal envelopes rather than redistributed
  manufacturer models
- catalog breadth is still thin in connectors, crystals/oscillators, relays,
  optoelectronics beyond one LED, RF modules, and larger power packages
- project-specific paste, mask, thermal, stackup, fab, and assembly rules remain
  downstream decisions

These are claim and roadmap limits, not reasons to weaken the complete/candidate
boundary.

## Channel red team

Use EE communities as a quality bar, not as an entitlement to promote. Current
[`r/PrintedCircuitBoard` rules](https://www.reddit.com/r/PrintedCircuitBoard/comments/zj6ac8/please_read_before_posting_especially_if_using_a/)
exclude AI topics/content, promotion, and self-promotion, with only occasional
moderator-approved exceptions. A promotional launch post there should not be
made without explicit moderator approval.

Recent footprint discussions in that community repeatedly favor building from
manufacturer data and checking every third-party asset. The launch message
should therefore lead with exact sources, deterministic checks, known limits,
and correction flow—not with “trusted,” “production-ready,” or “never draw a
footprint again.”

## Launch claim

Use:

> Source-linked exact-MPN records with native KiCad symbols, footprints, and
> nominal STEP models for engineering agents.

Do not claim independent certification, production qualification, full KLC
compliance, physical testing, or universal library coverage.
