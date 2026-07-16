# Component Intelligence agent charter

Component Intelligence is a compounding exact-MPN dataset for agentic electrical
engineering. Its default catalog is a one-stop source of complete local data and
CAD for schematic capture, PCB layout, and mechanical rendering.

It is maintained by Lyon Industries as open engineering infrastructure.

## Trust boundary

- `components/` and `catalog.json` contain complete packages only.
- `candidates/` and `candidate-catalog.json` contain incomplete collaborative
  work that must not be consumed as complete CAD.

Never weaken this distinction to increase catalog count. A one-component
complete catalog is more credible than twenty records that send consuming agents
elsewhere for missing assets.

## Authority order

1. Exact manufacturer source or dated exact-MPN test evidence.
2. `component.json` and its referenced native assets.
3. `schema/component.schema.json` and `scripts/validate.py`.
4. `QUALITY.md` and `CONTRIBUTING.md`.
5. Generated README files, distributor pages, external libraries, and model
   memory.

When sources conflict, record the conflict and keep or move the component in
`candidates/` until resolved.

## Remote consumption

Assume consumers fetch files directly from GitHub. They should retrieve
`catalog.json`, a selected record, and all declared assets from one pinned Git
commit. Do not require a clone, Python environment, local database, MCP server,
or repository-specific consumer tool.

The default catalog must provide enough paths and identity data for this flow.
Maintainer scripts may generate and validate repository artifacts but are not
part of the consumer contract.

## Complete package requirements

Before moving a directory into `components/`:

- verify exact MPN, package, and official sources
- independently cross-check normalized pin, rating, package, and assembly data
- include and verify a native symbol
- include and verify a native footprint with explicit pad geometry
- include and verify a STEP model with stated envelope scope
- record hashes, tool versions, provenance, intended use, limitations, and
  rights for every asset
- check symbol pins, footprint pads, layers, origin, orientation, and STEP
  placement against the normalized record
- resolve every fabrication-stop finding
- regenerate catalogs and pass all validation

Native assets own engineering authority. SVG and PNG previews may assist review
but are never substitutes for the symbol, footprint, or STEP file.

## Candidate contributions

Agents may add truthful partial progress under `candidates/`: a source-backed
record, one asset, a correction, a cross-check, or a real field finding. Keep
missing capabilities false and limitations explicit.

When a consuming project learns something reusable:

1. Identify the exact MPN and affected fact or asset.
2. Add the smallest shareable correction or finding.
3. Cite the source, calculation, CAD inspection, or test evidence.
4. Preserve failed and corrected states when they explain the mechanism.
5. Demote an affected complete package if the new finding invalidates its gate.
6. Regenerate catalogs and run repository validation.
7. Open a focused pull request without confidential project material.

Do not require a contributor to complete 3D modeling before sharing a valid
candidate correction. Do not expose that candidate through the complete catalog.

## Data and CAD rules

- Preserve exact MPN spelling inside records and IDs.
- Percent-encode reserved characters only in directory names.
- Use official sources and exact locators for load-bearing facts.
- Keep absolute maximum, recommended operating, characteristic, and
  application-dependent ratings distinct.
- Record internally common terminals, exposed pads, no-connects, boot straps,
  and multifunction pins explicitly.
- Do not infer package geometry from a family name or unrelated suffix.
- Symbols must agree with sourced pin numbers and electrical types.
- Footprints must agree with the sourced land pattern, not merely pass DRC.
- STEP files must state whether they support nominal envelope clearance or more
  detailed mechanical decisions.
- Keep unknown values unknown.

## Physical testing

Physical evidence is valuable but independent from complete CAD admission. Set
`physically_tested` true only with dated exact-MPN evidence and a bounded result.
Do not commit unbuilt coupons or placeholder test projects.

## Repository boundaries

- Prefer one component or one generic contract correction per pull request.
- Do not add hosted services, analytics, databases, or an MCP server while
  direct GitHub files satisfy consumption.
- Do not add agent or model attribution to repository history or assets.
- Preserve unrelated working-tree changes and configured human authorship.
- Do not publish confidential customer or employer information.

## Validation

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/build_catalog.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Validation must fail when an incomplete record enters `components/` or when a
complete candidate remains unpromoted.
