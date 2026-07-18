# Contributing

Contribute the smallest evidence-backed improvement that makes the next design
safer or faster. Partial candidate work and well-supported corrections are
welcome. Incomplete work must never enter the complete catalog.

Start with [`QUALITY.md`](QUALITY.md) and the target `component.json`.
`AGENTS.md` contains repository instructions for automated contributors; human
contributors do not need agent tooling.

For a wrong pin, land pattern, source locator, model envelope, or assembly
result, the fastest route is the
[component error form](https://github.com/lyon-industries/component-intelligence/issues/new?template=component-error.yml).
For a new part, use the
[exact-MPN request form](https://github.com/lyon-industries/component-intelligence/issues/new?template=component-request.yml).

## Evidence first

Every contribution should identify:

- one exact, orderable manufacturer MPN and package suffix
- current official sources with page, table, figure, or section locators
- the design decision or failure the change informs
- EDA/CAD version and fabrication or assembly context when relevant
- rights for any redistributed asset

Prefer manufacturer datasheets, package drawings, errata, application notes,
reference designs, standards, and actual test artifacts. Distributor pages may
support dated availability but do not override manufacturer technical data.

Do not submit family-level guesses, scraped distributor dumps, decorative
previews as engineering evidence, speculative test projects, confidential work,
or third-party CAD without compatible redistribution rights.

## Candidate contributions

Add or improve a directory under:

```text
candidates/<manufacturer-slug>/<path-encoded-mpn>/
```

Useful candidate contributions include source-backed identity and pin data, a
corrected rating or package fact, one compatible native asset, a reproducible
comparison, a field finding, or dated exact-MPN physical evidence. Unknowns and
missing capabilities must remain explicit.

## Complete-package promotion

Promote a candidate only after completing the full gate in `QUALITY.md`, moving
the directory to `components/`, regenerating outputs including the component
graph, and running validation.

A promotion pull request must identify:

- exact MPN, package, intended use, official sources, and locators
- symbol-pin and footprint-pad comparisons
- footprint origin, orientation, layers, mask, paste, courtyard, and applicable
  process assumptions
- STEP seating, orientation, nominal envelope, and limitations
- asset hashes, tool versions, provenance, and rights
- resolved and remaining findings

Existing filenames are not evidence. The assets must be mutually consistent
with the canonical record.

## Demotion and returned findings

If a complete package develops an unresolved fabrication-stop finding or loses
source, asset, hash, or verification integrity, fix it immediately or move the
whole directory to `candidates/`. Never leave a misleading entry in
`catalog.json` while work continues elsewhere.

Add returned results to `integration.findings` with type, severity, status,
scope, date, concise mechanism, and supporting sources. Share only evidence you
have permission to publish.

## Local validation

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/build_catalog.py
python scripts/build_catalog.py --check
python scripts/validate.py
python -m unittest discover -s tests -v
```

Inspect generated `catalog.json`, `candidate-catalog.json`, `CATALOG.md`, KiCad
library tables, component summaries, and
`assets/component-catalog-graph.svg` before submission. Every complete exact
MPN must appear once under its canonical category; candidate devices must stay
outside the graph.
