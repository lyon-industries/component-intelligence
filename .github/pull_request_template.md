## Exact component and change

- Manufacturer:
- Exact MPN:
- Candidate improvement, complete-package promotion, correction, or demotion:
- Engineering decision this helps:

## Evidence

- Official sources and exact locators:
- CAD checks, calculation, or physical-test evidence:
- Unknowns and limitations that remain:

## Trust tier

- [ ] Candidate work remains under `candidates/` and outside `catalog.json`.
- [ ] Promotion satisfies every complete-package gate in `QUALITY.md`.
- [ ] A compromised complete package was corrected or demoted in this change.

## Native assets

- Symbol format, hash, tool version, and checks:
- Footprint format, hash, tool version, and checks:
- STEP format, hash, tool version, envelope, and checks:

## Shared findings

- Failure or constraint returned to `integration.findings`:
- Confidential details intentionally excluded:

## Rights and validation

- [ ] I have the right to submit every included file under its declared terms.
- [ ] No confidential customer, employer, credential, or proprietary material is included.
- [ ] `python3 scripts/build_catalog.py` regenerated indexes, summaries, KiCad tables, and the component graph.
- [ ] Complete exact MPNs appear under the correct category; candidates remain outside the graph's device nodes.
- [ ] `python3 scripts/build_catalog.py --check` passes.
- [ ] `python3 scripts/validate.py` passes.
- [ ] `python3 -m unittest discover -s tests -v` passes.
