# Component Intelligence

Evidence-bound component records for electrical, mechanical, assembly, and
manufacturing automation.

This repository starts with a small, inspectable contract instead of a large
part dump. Each record binds one exact manufacturer part number to official
source locators, electrical pins, package dimensions, CAD state, assembly
metadata, known integration failures, rights, and validation state.

## Current seed

| Manufacturer | Exact MPN | Type | Evidence state | Physical state |
| --- | --- | --- | --- | --- |
| Diodes Incorporated | AP63205WU-7 | 5 V synchronous buck converter | Cross-checked | Not tested |
| Littelfuse / C&K | PTS815SJM250SMTRLFS | SMT momentary switch | Cross-checked | Not tested |

The records are reference material, not production-approved library parts.
Neither device has been qualified here by incoming inspection, assembly, or a
physical electrical test.

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

The seed stops at cross-checked. It must not be presented as physical proof.

## Validate

    python3 -m pip install -r requirements-dev.txt
    python3 scripts/validate.py

The validator applies the JSON Schema and additional semantic checks: catalog
identity, unique pins, terminal-group references, asset paths, source URLs,
and the rule that an untested part cannot be production-approved.

## Repository map

    catalog.json
    components/<manufacturer>/<mpn>/
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

## License and source rights

Original repository content is MIT licensed. Manufacturer names and product
names identify the referenced parts and remain the property of their owners.
Linked vendor documents and CAD are not relicensed and are not included.
