# Component Intelligence agent charter

This file is the operating contract for agents and people working in this
repository. Read it before using a record, changing the schema, or preparing a
contribution.

## What this repository is

Component Intelligence is a shared, evidence-bound component qualification
resource for agentic electrical engineering. It exists so an engineering agent
can identify an exact manufacturer part number, understand the limits that
matter, place qualified CAD assets, and trace every load-bearing decision back
to a source or test.

It is not a distributor search mirror, a collection of attractive SVGs, an
unreviewed EDA library, or a claim that one component is suitable for every
application. A smaller catalog that an agent can use safely is more valuable
than a large catalog of plausible records.

The core promise is:

> An accepted component is specific enough to order, complete enough to place,
> tested enough to trust as an engineering input, and explicit enough for an
> agent to know where its authority ends.

The repository is maintained by Lyon Industries as open engineering
infrastructure. Contributions are encouraged because component knowledge gets
better when field use, observed failures, and corrected assets return to the
shared catalog.

## Current status

Do not infer readiness from the presence of a directory in `components/`.
Inspect `validation.release_state` in `component.json` and apply
[`QUALITY.md`](QUALITY.md).

Records that predate the agent-ready admission rule are named in
`quality/legacy-records.json`. They are remediation inventory. They may support
research and cross-checking, but they are not approved for autonomous
schematic or PCB placement. No new record may be added to that exception set.

## Authority order

When instructions conflict, use this order:

1. The exact manufacturer source and dated test evidence for the exact MPN.
2. `schema/component.schema.json` and `scripts/validate.py`.
3. `QUALITY.md`.
4. This file.
5. The component `README.md` and other repository documentation.
6. Distributor pages, third-party libraries, search results, and model memory.

A distributor listing can establish availability at a point in time. It does
not override the manufacturer pin table, package drawing, operating limits, or
revision history.

## Non-negotiable admission rule

Do not merge a new component unless it is `agent-ready` under the current
profile. Schema validity is necessary and insufficient.

An agent-ready record requires, at minimum:

- one exact, orderable MPN with a dated orderability check
- official sources with exact page, table, figure, section, or drawing locators
- independent cross-checking of identity, pin map, package, and land pattern
- electrical pin types and rating-boundary semantics suitable for ERC and
  design reasoning
- a machine-usable native symbol and footprint, both cross-checked against the
  normalized record and rendered for human inspection
- explicit pad geometry, coordinate convention, orientation, paste, mask,
  courtyard, keep-out, and assembly constraints where applicable
- a rights-cleared, checked 3D model when mechanical envelope or placement is
  material; otherwise an explicit not-applicable decision
- no open validation check or open fabrication-stop issue
- a dated physical assembly test of the exact package and at least one bounded
  functional test of the exact MPN
- known failure modes, application limits, and a clear statement of what was
  not tested

The detailed gate and the meaning of each state are in `QUALITY.md`.

Do not lower the gate to make an existing record pass. Improve the evidence and
assets, or leave the record blocked.

## Using a component

Before an agent uses a record in a design:

1. Match the exact MPN, package suffix, temperature grade, packing suffix, and
   lifecycle or orderability state. Family-level similarity is not identity.
2. Confirm `validation.release_state` is `agent-ready`.
3. Check `reviewed_on`, source revision, and `orderable_checked_on` for age.
4. Read every `known_issue`, open limitation, layout constraint, and test
   boundary.
5. Verify the intended operating point against recommended conditions,
   absolute maximum ratings, thermal limits, external components, derating,
   and relevant standards.
6. Re-run the native EDA checks in the target toolchain. Import and conversion
   can change pin types, layers, origins, rotations, mask, paste, or 3D seating.
7. Keep the application-specific design review. Repository readiness does not
   approve a medical, safety, automotive, aviation, defense, mains, battery, RF,
   or other regulated design.

If any check fails, stop autonomous placement and report the record as blocked.
Never silently repair a component only inside the consuming PCB workspace.

## Field feedback mandate

If an agent consumes this repository and learns something that would make the
next design safer or faster, send that knowledge back.

Examples include:

- a needed exact MPN is missing
- a pin name, pin type, alternate function, common-terminal group, or no-connect
  rule is incomplete
- a footprint imports with the wrong origin, rotation, layer, mask, paste, or
  courtyard
- an assembly house, inspection image, or continuity test exposes a package
  interpretation error
- a typical application fails outside a stated operating condition
- a source moved, changed revision, or became obsolete
- a supply, lifecycle, moisture, thermal, RF, firmware, or programming
  constraint changes the design decision

The preferred return path is a pull request containing the corrected record,
source locators, assets, tests, and a concise failure account. If the evidence
is incomplete or the workspace is confidential, open an issue or draft pull
request containing only information that can be shared. Name the missing fact
and the test needed to close it. Do not upload customer designs, employer data,
credentials, proprietary source files, or screenshots without permission.

An agent that discovers a missing component in a PCB workspace should, when
authorized:

1. Capture the exact MPN and the engineering reason it was selected.
2. Retrieve current primary sources from the manufacturer.
3. Normalize facts with exact locators and preserve unknowns.
4. Create or correct the native assets and deterministic previews.
5. Run the digital and physical qualification work required by the profile.
6. Add the integration failure or decision that made the record useful.
7. Run repository validation.
8. Open a pull request using `.github/pull_request_template.md`.

Inference is welcome as a research aid. It is never evidence. Label a
hypothesis, then replace it with a source, calculation, measurement, or test
before admission.

## Component dossier requirements

Each component directory represents one exact MPN and must contain:

- `component.json`: canonical normalized evidence and validation state
- `README.md`: short human dossier with exact identity, use boundary, critical
  constraints, test status, and official source links
- native symbol and footprint files in their declared formats
- deterministic symbol and footprint previews for review
- a checked 3D model or an explicit profile-approved not-applicable decision
- test evidence referenced by the record without exposing confidential data

SVG files are review artifacts. They must be generated from, or checked against,
the machine-usable asset. An SVG cannot be the sole symbol or footprint and must
never be marked for manufacturing use.

Do not mirror manufacturer PDFs, distributor CAD, images, or STEP files unless
their redistribution terms have been verified and recorded. Prefer official
links plus hashes of reviewed bytes. Original normalized facts, original CAD,
tests, and previews belong in the repository under its license.

## Source and research behavior

- Use primary manufacturer documents, package drawings, errata, application
  notes, reference designs, standards, and test results.
- Use current sources for orderability, lifecycle, revisions, packaging, and
  regulatory claims. Record absolute dates.
- Keep absolute maximum ratings distinct from recommended operation and typical
  characteristics.
- Treat package drawings and land-pattern recommendations as separate facts.
- Preserve top-view versus bottom-view, pin-1, tape, reel, and assembly rotation
  conventions explicitly.
- Record internally common terminals and exposed-pad electrical connections.
- Do not infer package geometry from a family name or a third-party library.
- Record source access failures instead of inventing hashes or silently
  replacing the source.
- When two official sources disagree, stop promotion, cite both, and open a
  blocking issue.

Online research is expected for time-sensitive facts. Save the durable result
in the record; a browser session or an agent's memory is not repository
evidence.

## CAD and test behavior

- The normalized record owns identity, evidence, and acceptance state.
- The native EDA file owns tool-specific geometry and semantics.
- A preview owns no manufacturing authority.
- Render native symbols and footprints in CI or a reproducible local toolchain.
- Compare pin and pad sets mechanically. Visual similarity is insufficient.
- Run syntax, ERC, DRC, layer, courtyard, mask, paste, origin, rotation, and 3D
  envelope checks appropriate to the format.
- Use a representative fixture or coupon for physical qualification. Record the
  exact MPN, board revision, date, method, instruments, result, and artifact
  location.
- A powered test must state supply, load, environment, duration, measured
  outputs, and acceptance limits. “Works” is not a test result.
- Preserve failed and superseded states when they explain a safety or
  fabrication decision.

## Contribution boundaries

- One component per focused pull request unless several records share one
  inseparable package or schema correction.
- Do not combine schema changes with catalog expansion unless the component
  proves why the schema change is needed.
- Do not add dependencies, hosted services, analytics, databases, or an MCP
  server without an accepted architecture decision.
- Do not change license terms, source-rights policy, readiness criteria, or the
  legacy exception set as incidental work.
- Do not add agent, model, or vendor credit to branches, commits, files, pull
  requests, or generated assets. Preserve human and organization authorship.
- Respect unrelated working-tree changes. Do not reset or overwrite them.

Contributions intentionally submitted for inclusion are accepted under
Apache-2.0 unless explicitly stated otherwise. Contributors must have the right
to submit every file and must retain required third-party notices.

## Validation commands

Run from the repository root:

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Also run the native EDA render and test commands named by the component dossier.
The general validator cannot substitute for tool-specific or physical tests.

## Versioning and interfaces

Consumers should pin a Git commit. Component IDs are stable exact-MPN
identifiers. `schema_version` versions the data contract; it is not a marketing
release number. Breaking schema changes require migration of every record and a
major schema-version change. Additive optional fields use a minor change.

Do not add repository release machinery until qualified components and real
consumers create a release need. Do not add an MCP server while direct GitHub,
raw-file, clone, and ordinary JSON tooling satisfy discovery.

## Definition of done

A component contribution is done only when:

- the exact engineering decision and use boundary are clear
- every load-bearing fact is sourced or tested
- native assets and previews agree with the normalized record
- digital validation and physical qualification pass
- application, assembly, lifecycle, supply, cost, and rights constraints are
  explicit
- open failures block promotion rather than becoming prose disclaimers
- repository validation passes
- the pull request gives the next agent enough evidence to reproduce the
  decision

The final reviewer assigns one outcome: admit, return for evidence, keep in a
draft pull request, or reject. There is no “mostly ready” merge state.
