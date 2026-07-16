# Contributing

Contribute the smallest evidence-backed improvement that makes the next design
safer or faster. Partial candidate work is welcome. Incomplete work must never
enter the complete catalog.

Read [`AGENTS.md`](AGENTS.md), [`QUALITY.md`](QUALITY.md), and the target
`component.json` before editing.

## Candidate contributions

Add or improve a directory under:

```text
candidates/<manufacturer-slug>/<path-encoded-mpn>/
```

Useful candidate contributions include:

- source-backed exact-MPN identity and pin data
- a corrected locator, rating, or package fact
- one native symbol, footprint, or STEP model
- an independent comparison of existing data or CAD
- a real layout, electrical, assembly, firmware, thermal, supply, or mechanical
  finding
- dated exact-MPN physical evidence

A contributor does not need to finish all three CAD assets before a useful
candidate improvement can merge. Unknowns and missing assets must remain
explicit.

Do not submit family-level guesses, scraped distributor dumps, decorative
previews, speculative test projects, or third-party CAD without compatible
redistribution rights.

## Complete-package promotion

Promote a candidate by completing the full gate in `QUALITY.md`, moving its
directory from `candidates/` to `components/`, regenerating both catalogs, and
running all validation.

The pull request must identify:

- exact MPN and intended agent use
- official sources and locators
- symbol, footprint, and STEP formats, hashes, tool versions, and provenance
- pin-to-symbol and pin-to-pad checks
- footprint origin, orientation, layers, mask, paste, courtyard, and keep-outs
- STEP origin, seating, orientation, envelope, and limitations
- resolved and remaining findings
- rights for every included asset

Do not promote a directory merely because all filenames exist. The assets must
be mutually consistent and verified against the normalized record.

## Demotion

If a complete package develops an unresolved fabrication-stop finding or loses
source, asset, hash, or verification integrity, fix it immediately or move the
whole directory to `candidates/`. Never leave a misleading entry in
`catalog.json` while work continues elsewhere.

## Returning a finding

Add the result to `integration.findings` with its type, severity, status, scope,
date, concise mechanism, and supporting sources. Share only evidence you have
permission to publish. Never upload confidential customer, employer, credential,
or proprietary project material.

## Sources and rights

Prefer manufacturer datasheets, package drawings, errata, application notes,
reference designs, standards, and actual test results. Distributor pages may
support dated availability but do not override manufacturer technical data.

Do not redistribute vendor PDFs, images, symbols, footprints, or STEP files
unless their terms are recorded and compatible. Original contributions are
submitted under Apache-2.0 unless explicitly stated otherwise.

## Validate

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Inspect the generated `catalog.json` and `candidate-catalog.json` changes before
submission. The default catalog must change only through a complete-package
promotion, correction, or demotion.
