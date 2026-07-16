# Component quality and trust tiers

Version: `component-intelligence-v1`

The repository has two explicit trust tiers. Directory location and generated
catalog membership are authoritative; prose maturity labels are not.

## Complete package: `components/`

A component may appear in `components/` and `catalog.json` only when all of the
following pass:

- one exact manufacturer MPN and package are identified
- official sources have retrieval dates and exact locators
- normalized pins, electrical types, rating boundaries, and package facts have
  been independently cross-checked
- a native symbol is included, hashed, parsed, and checked against the pin map
- a native footprint is included, hashed, parsed, and checked against explicit
  pad geometry, numbering, origin, orientation, mask, paste, courtyard, and
  applicable keep-outs
- a STEP model is included, hashed, opened, and checked for origin, seating,
  orientation, and its declared mechanical envelope
- asset provenance, intended use, limitations, tool versions, and rights are
  explicit
- no active `fabrication-stop` finding remains
- schema, semantic, asset, catalog, and promotion validation pass

Complete means the agent receives the local data and CAD needed for schematic,
layout, and mechanical integration. It does not approve the consuming circuit,
PCB, enclosure, manufacturing process, or regulated product.

## Candidate: `candidates/`

A candidate can be merged with incomplete capabilities when it provides:

- exact manufacturer and MPN identity
- at least one authoritative source
- one useful normalized fact, asset, correction, or finding
- honest capability flags and explicit limitations
- compatible rights
- passing schema and candidate validation

Candidates are excluded from `catalog.json`. They appear only in
`candidate-catalog.json`, whose tier is explicitly `candidate`.

If a candidate satisfies the complete-package gate, validation fails until it
is promoted. If a complete package no longer passes, it must be fixed or moved
back to `candidates/`.

## Capability flags

| Flag | Meaning when `true` |
| --- | --- |
| `identity_verified` | An official source supports the exact device identity. |
| `data_cross_checked` | A second engineering comparison checked normalized data. |
| `symbol_verified` | The included native symbol matches the record and parses. |
| `footprint_verified` | The included native footprint matches the sourced land pattern. |
| `step_verified` | The included STEP model has checked placement and envelope scope. |
| `physically_tested` | Dated exact-MPN physical evidence is recorded. |

The first five flags are mandatory for the complete tier. Physical testing is
independent because a shared CAD package cannot replace application-specific
qualification.

## Findings

Findings compound field knowledge across designs. Each finding records a stable
local ID, type, severity, status, scope, date, mechanism, and supporting source
IDs when available.

- `fabrication-stop`: can invalidate board manufacture or assembly
- `design-risk`: requires an explicit downstream engineering decision
- `note`: changes how evidence or asset scope should be interpreted

Resolved findings remain when the failure and correction can prevent recurrence.

## Physical evidence

`physically_tested: false` requires no speculative fixture or coupon.

When true, evidence must name the exact MPN, date, bounded scope, pass/fail/mixed
result, and a reviewable artifact. Physical evidence never silently upgrades
symbol, footprint, or STEP verification.
