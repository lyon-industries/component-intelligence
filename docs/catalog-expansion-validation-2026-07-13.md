# Catalog expansion validation — 13 July 2026

## Release scope

The catalog expanded from two to 20 exact component records. The 18 additions
cover power conversion, battery charging, wireless and wired interfaces, three
microcontroller families, environmental and current sensing, data conversion,
nonvolatile memory, ESD protection, logic, analog, timing, and discrete
semiconductors.

Every addition is `reference-only`, `not-tested`, and `extracted`. None claims
independent engineering review, assembly evidence, electrical qualification,
or production approval. The original two cross-checked records retain their
previous state.

## QA completed

- JSON Schema validation passed for all 20 records.
- The semantic validator passed catalog coverage, exact identity, path,
  package pin count, terminal-group, source-reference, asset, orderability,
  known-risk, and release-state checks.
- Reserved characters in four exact MPNs are percent-encoded in directory
  names. Exact manufacturer spelling remains unchanged in records and IDs.
- All 14 newly captured PDF files matched the SHA-256 and byte size stored in
  their records after generation.
- Live retrieval returned an official PDF for 15 of the 20 catalog sources.
  The remaining four new sources were independently readable in the browser
  review path but blocked direct command-line byte capture; records make no
  hash claim for them.
- Every added record has a package-specific pin map, at least three selected
  ratings, an official package or land-pattern locator, assembly boundaries,
  one concrete integration risk, and a local README.
- Current orderability is claimed only for the exact STM32C011F6P6TR,
  USBLC6-2SC6, and MAX3485ESA+ MPNs, which were confirmed in official product
  tables on 13 July 2026. Other new records leave current orderability unknown.

## Validator hardening

The validator now fails on unsorted or duplicate catalog entries, orphan
records, missing component READMEs, directory/identity mismatch, catalog state
drift, duplicate or invalid source references, impossible source-page
locators, false source-byte claims, unsupported orderability dates, missing
integration risks, and untested production approval.

Mutation checks deliberately introduced an orphan record, an identity/path
mismatch, an out-of-range source locator, and an unsupported orderability
claim in disposable copies. Each mutation caused validation to fail.

## Remaining risk

The records normalize official documents; they are not EDA library assets.
Native symbols, footprints, and STEP models remain absent. Before any record
can move beyond reference use, it needs a second engineering review of the
exact package, a native asset comparison, specimen inspection, assembly fit,
and application-specific electrical and thermal testing.
