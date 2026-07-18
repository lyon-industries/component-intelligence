# Component quality and trust tiers

Version: `component-intelligence-v1`

The repository has two explicit trust tiers. Directory location and generated
catalog membership are authoritative; prose maturity labels are not.

## What the automated gate establishes

The automated gate—`scripts/build_catalog.py --check`, `scripts/validate.py`,
and the unit tests—currently checks:

- schema shape, exact source references, retrieval chronology, and captured-file
  hashes
- positive dimensions, unique pin numbers, source-bound pins and ratings, and
  valid finding states
- deterministic KiCad symbol and footprint replay from `component.json`
- symbol pin number, name, and electrical-type agreement
- footprint pad count, number, position, size, copper, paste, and mask agreement
- duplicate pads, pin-to-pad equality, pin-one indication where required,
  silkscreen-to-pad clearance, fab fields, and 0.05 mm-grid courtyard geometry
- STEP parse, solid presence, seating at z=0, height, and declared nominal body
  and land-pattern envelope
- asset hashes, declared paths, generated summaries, catalogs, complete-tier
  KiCad library tables, and the 16:9 component graph
- candidate isolation and the absence of active fabrication-stop findings in
  the complete tier

Tests deliberately corrupt symbol pins, pad lists, silkscreen, hashes, STEP
seating, and generated outputs to prove the relevant failures are detected.

## What a recorded review establishes

Each record's `verification.checks` names the comparison that was actually
performed and its date. `data_cross_checked: true` means a second explicit
engineering comparison was recorded—for example a second official source,
package drawing, product page, or independently repeated land-pattern
arithmetic. It does not mean an accredited laboratory or unrelated organization
certified the part.

## Complete package: `components/`

A component may appear in `components/` and `catalog.json` only when:

- one exact manufacturer MPN and package are identified
- official sources have retrieval dates and exact locators
- the required verification checks and capability flags are present
- a native symbol is included, hashed, replayed, and checked against the pin map
- a native footprint is included, hashed, replayed, and checked against explicit
  pad geometry and the repository's manufacturing-safety rules
- a nominal STEP model is included, hashed, reopened, and checked for seating
  and its declared envelope
- asset provenance, intended use, limitations, tool versions, and rights are
  explicit
- no active `fabrication-stop` finding remains
- schema, semantic, asset, catalog, and promotion validation pass

Complete means the repository contains a mutually consistent local data and CAD
package. It does not approve the consuming circuit, PCB, enclosure,
manufacturing process, regulated product, or supply decision.

## Candidate: `candidates/`

A candidate can be merged with incomplete capabilities when it provides:

- exact manufacturer and MPN identity
- at least one authoritative source
- one useful normalized fact, correction, finding, or compatible asset
- honest capability flags and explicit limitations
- compatible rights and passing candidate validation

Candidates are excluded from `catalog.json` and the generated KiCad library
tables. If a candidate satisfies the complete gate, validation fails until it
is promoted. If a complete package no longer passes, it must be fixed or moved
back to `candidates/`.

## Capability flags

| Flag | Meaning when `true` |
| --- | --- |
| `identity_verified` | A recorded official-source check supports the exact device identity. |
| `data_cross_checked` | A recorded second comparison checked the normalized data. |
| `symbol_verified` | The included native symbol deterministically matches the record and repository checks. |
| `footprint_verified` | The included native footprint deterministically matches the source-bound land pattern and repository checks. |
| `step_verified` | The included nominal STEP model reopens with the checked placement and envelope. |
| `physically_tested` | Dated, exact-MPN physical evidence is recorded. |

The first five flags are mandatory for the complete tier. Physical testing is
independent because a shared CAD package cannot replace application-specific
qualification.

## KiCad convention audit

The 2026-07-18 launch audit used the upstream KiCad library checker at commit
`f733308c80768a7d42d0f92284f61abf7e6f3ec0` against every complete package.
All 46 symbols passed when the generated footprint libraries were resolved.
All 46 footprints passed except KLC rule F9.3: this repository intentionally
uses `${COMPONENT_INTELLIGENCE_ROOT}` for self-contained STEP paths instead of
KiCad's official `${KICAD10_3DMODEL_DIR}` tree.

This is an explicit portability tradeoff, not a blanket KLC-compliance claim.
The repository validator requires the custom path to resolve to the exact
hashed local STEP file. A read-only KiCad 10.0.4 CLI smoke test also opened and
exported all 46 symbols and all 46 footprints successfully. See
[`docs/KICAD.md`](docs/KICAD.md) and `scripts/audit_kicad_native.py`.

## Findings

Findings compound field knowledge across designs. Each finding records a stable
local ID, type, severity, status, scope, date, mechanism, and supporting source
IDs when available.

- `fabrication-stop`: can invalidate board manufacture or assembly
- `design-risk`: requires an explicit downstream engineering decision
- `note`: changes how evidence or asset scope should be interpreted

Resolved findings remain when the failure and correction can prevent
recurrence.

## Physical evidence

`physically_tested: false` requires no speculative fixture or coupon. When true,
evidence must name the exact MPN, date, bounded scope, result, and a reviewable
artifact. Physical evidence never silently upgrades symbol, footprint, or STEP
verification.
