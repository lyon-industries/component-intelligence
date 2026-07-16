# Agent-ready component standard

Version: `agentic-ee-v1`
Effective: 16 July 2026

This profile defines the minimum evidence required before a component may be
merged as a usable input to agentic electrical engineering. It qualifies the
record and its bundled assets. It does not approve any downstream product or
application.

## State model

| Release state | Meaning | Permitted use |
| --- | --- | --- |
| `reference-only` | Source normalization is incomplete or unqualified. | Research and manual cross-checking only. |
| `candidate` | Qualification work is active but at least one hard gate is open. | Draft pull request or maintainer workspace only. |
| `agent-ready` | Every gate in this profile passed for the exact MPN and bundled assets. | Bounded agentic selection, schematic placement, and PCB placement with application review. |
| `production-approved` | Historical state retained for schema compatibility. Production approval belongs to a specific product and must not be assigned by the shared catalog. | Do not use for new or revised records. |

`physically-verified` is an evidence state, not a release decision. A physically
tested part can still be blocked by a bad footprint, stale identity, missing
rights, or an open integration failure.

## Hard gates

Every gate must pass. A warning paragraph does not compensate for missing
evidence.

### 1. Exact identity and supply

- Exact manufacturer, MPN, package, grade, and packing suffix are recorded.
- The exact MPN is confirmed orderable from a current manufacturer source or
  authoritative manufacturer product table.
- The orderability decision is dated and no older than 365 days at review.
- Lifecycle, NRND, EOL, PCN, errata, counterfeit, and supply constraints are
  recorded when applicable.
- Manufacturer and distributor identities are not conflated.

### 2. Source authority and provenance

- At least one official primary source identifies the exact device or exact
  orderable option.
- Pin map, recommended operation, absolute maximum ratings, package drawing,
  land pattern, orientation, and application constraints have exact locators.
- Reviewed source bytes are hashed when capture is possible. A blocked capture
  is recorded honestly and independently reviewed.
- Conflicting source revisions are resolved or block promotion.
- Redistribution rights are explicit for every included non-original asset.

### 3. Electrical semantics

- Every physical terminal has one unambiguous number, name, function, source,
  locator, and electrical type.
- Internally common terminals, exposed pads, no-connects, multifunction pins,
  boot straps, default states, and forbidden connections are explicit.
- Ratings identify whether they are absolute maximum, recommended operating,
  characterized, or application-dependent.
- The dossier covers the constraints an agent needs to avoid a plausible but
  invalid circuit: required support parts, decoupling, pull states, sequencing,
  thermal limits, derating, protection, and relevant firmware or programming
  conditions.

### 4. Package and native CAD

- Package identity and dimensions match the exact MPN.
- Pad coordinates, sizes, shapes, numbering, origin, rotation, and view
  convention are explicit.
- The land pattern covers copper, mask, paste, courtyard, assembly outline,
  pin-1, keep-outs, exposed-pad treatment, vias, and thermal strategy as
  applicable.
- A machine-usable native symbol and footprint are included, rights-cleared,
  hashed, rendered, and cross-checked against the normalized record.
- Symbol pin types pass ERC and match the intended function.
- Footprint pad numbers match the electrical terminals mechanically.
- A checked 3D model is included when body envelope, actuator travel, antenna,
  optical path, connector mating, or enclosure clearance is material. A
  not-applicable decision must explain why omission is safe.
- SVG previews are derived inspection artifacts and never the CAD authority.

### 5. Assembly and manufacturing

- Process, packing, moisture sensitivity, storage, paste, reflow or soldering,
  cleaning, coating, polarity, tape orientation, and inspection constraints are
  recorded where applicable.
- Assembly rotation and pin-1 convention are documented.
- The exact footprint has passed a dated fabrication and assembly coupon or a
  documented production-equivalent assembly.
- Inspection evidence shows pin numbering, seating, solderability, clearance,
  and any package-specific concern.

### 6. Functional qualification

- The exact MPN has a bounded, dated functional test.
- The test states fixture revision, supply, load, environment, duration,
  instruments, measured outputs, acceptance limits, and result.
- The test exercises the failure most likely to invalidate agent use for the
  component class. Examples include continuity topology, regulator load and
  transient behavior, sensor communication and plausibility, MCU programming
  and boot, RF keep-out performance, or protection-device parasitics.
- The record states what the test did not prove.

### 7. Independent review and automated checks

- Identity, pin map, package, and land pattern have a second engineering
  comparison independent of the first extraction pass.
- JSON Schema and semantic validation pass.
- Native assets parse and render in the declared tool version.
- ERC, DRC, pin-to-pad, layer, mask, paste, courtyard, origin, rotation, and 3D
  checks pass as applicable.
- No validation check remains `open`.
- No known issue remains `open`. A documented limitation may remain only when
  it is bounded and does not invalidate the accepted use.

### 8. Agent handoff and rights

- The README states exact identity, accepted use, critical constraints, test
  status, known limitations, and source links in plain language.
- A consuming agent can tell which facts are source-derived, calculated,
  rendered, assembled, measured, or still unknown.
- Original repository content is Apache-2.0. Included third-party assets retain
  their own notices and must be compatible with redistribution.
- No confidential customer, employer, or proprietary workspace material is
  included.

## Machine-enforced minimum

`scripts/validate.py` enforces the parts of this profile that the current schema
can represent. An `agent-ready` record must have:

- current exact-MPN orderability
- `cross-checked` or `physically-verified` evidence
- `assembly-tested` physical state
- cross-checked land pattern with explicit pads
- cross-checked, machine-usable symbol and footprint paths
- a cross-checked machine-usable STEP path or an explicit not-applicable
  decision with a reviewable reason
- documented assembly orientation
- electrical types on every pin and rating boundaries on every rating
- no open check or issue
- no unresolved source-rights review

Human review still owns source interpretation, test adequacy, application
coverage, and rights decisions. CI is a floor, not the approval authority.

## Promotion record

The pull request must name:

- exact MPN and intended agent use
- source revisions and retrieval dates
- native asset formats and tool versions
- automated checks run
- physical specimen, fixture, board revision, and test date
- observed failures and corrections
- remaining application limits
- reviewer and promotion decision

If a component cannot meet the profile, keep the work in a branch or draft pull
request, file the missing evidence as an issue, or reject the contribution. Do
not merge it as reference inventory.
