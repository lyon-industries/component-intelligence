# Contributing

Contributions should make a component safe for an engineering agent to use,
not only easier to find.

Read [`AGENTS.md`](AGENTS.md) and [`QUALITY.md`](QUALITY.md) before preparing a
component. New reference-only records are not merged. Keep incomplete work in a
branch, draft pull request, or issue until every admission gate passes.

## Choose a contribution

Good contributions include:

- qualifying one exact component end to end
- correcting a source-backed fact or native asset
- returning a failure observed in a real design or assembly
- refreshing an exact-MPN orderability, source revision, lifecycle, or errata
  decision
- improving a validator or test because a concrete component exposed a gap

Do not add speculative families, distributor-generated assets, scraped part
dumps, or schema abstractions without a qualified component that requires them.

## Required pull request dossier

Use `.github/pull_request_template.md` and provide:

1. Exact manufacturer, MPN, package, grade, and packing suffix.
2. The engineering use the record enables and the application boundary it does
   not approve.
3. Current official sources with revision, retrieval date, and exact locators.
4. Complete electrical semantics, bounded ratings, package, land pattern,
   orientation, assembly, and application constraints.
5. Cross-checked machine-usable symbol and footprint plus deterministic
   previews.
6. A checked 3D model or an explicit profile-approved not-applicable decision.
7. Automated parse, render, ERC, DRC, pin-to-pad, layer, mask, paste,
   courtyard, origin, rotation, and 3D checks as applicable.
8. A dated assembly coupon or production-equivalent assembly for the exact
   package.
9. A bounded functional test of the exact MPN, including fixture, conditions,
   instruments, measurements, limits, and result.
10. At least one relevant failure mode and a precise account of what remains
    untested.
11. Rights and provenance for every included file.

Unknown values stay unknown and block admission when they are load-bearing.
Inference can guide research but must be replaced by source or test evidence.

## Files and identity

Use one directory per exact MPN:

```text
components/<manufacturer-slug>/<path-encoded-mpn>/
```

Use the exact manufacturer spelling inside `component.json` and the component
ID. Percent-encode path-reserved characters only in the directory name. For
example, `/` becomes `%2F`; it must not create another directory level.

SVG previews are required review aids when the profile calls for them. They
must be derived from or cross-checked against the native asset and must not be
marked for manufacturing use.

## Sources and third-party rights

Use manufacturer documents, errata, package drawings, reference designs,
standards, and dated test evidence. Distributor pages may support a current
availability observation but cannot override manufacturer technical sources.

Do not add vendor PDFs, images, footprints, symbols, or STEP files unless their
redistribution terms are recorded and compatible. Prefer original normalized
records and original CAD built from citable facts. Preserve all required
third-party notices.

Contributions intentionally submitted for inclusion are licensed under
Apache-2.0 unless explicitly stated otherwise. By submitting, you confirm that
you have the right to contribute the work. The repository does not require a
separate contributor license agreement at this stage.

## Validate

Run from the repository root:

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Also run the native EDA and physical test procedure named in the component
dossier. Passing the general validator is not engineering approval.

## Review outcomes

A reviewer will assign one outcome:

- admit as `agent-ready`
- return for specific evidence or corrections
- keep as a draft pull request
- reject because identity, evidence, rights, or testability cannot be resolved

The frozen legacy list may shrink when an existing record is qualified or
removed. It must not be expanded to admit incomplete work.
