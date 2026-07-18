<p align="center">
  <img src="https://raw.githubusercontent.com/lyon-industries/.github/main/profile/lyon-industries-banner.svg" alt="Lyon Industries" width="100%">
</p>

# Component Intelligence

Component Intelligence is an open collection of complete electronic-component
packages for engineering agents. A component in the default catalog includes
the exact-MPN data, native symbol, native footprint, and STEP model needed for
schematic capture, PCB layout, and mechanical rendering without another source
hunt.

Incomplete but useful work lives in a separate candidate catalog. It can be
improved collaboratively without weakening the complete-package promise.

## Remote agent workflow

Consumers do not need to clone this repository or run Python.
There is intentionally no repository-specific query client or required runtime:
the versioned JSON files and declared asset paths are the public interface.

1. Fetch `catalog.json` from GitHub at a pinned commit.
2. Select an exact MPN from that complete-package index.
3. Fetch the listed `component.json` path at the same commit.
4. Fetch the symbol, footprint, and STEP paths declared in that record.
5. Read integration findings and re-run the native checks required by the
   consuming toolchain.

```text
https://raw.githubusercontent.com/lyon-industries/component-intelligence/<commit>/catalog.json
https://raw.githubusercontent.com/lyon-industries/component-intelligence/<commit>/<record-path>
https://raw.githubusercontent.com/lyon-industries/component-intelligence/<commit>/<asset-path>
```

The catalog entry supplies `<record-path>`. Asset paths in `component.json` are
relative to that record's directory. Pin the commit so every fetched file comes
from the same accepted dataset state.

Treat catalog paths as repository paths, not pre-encoded URLs. URL-encode each
path segment before inserting it into a raw GitHub or Contents API URL. A
literal `%2F` in a repository path represents an encoded MPN character and must
appear as `%252F` in the request URL. Do not decode the catalog path first.

The GitHub Contents API is also suitable when an agent wants to enumerate or
download the complete directory:

```text
https://api.github.com/repos/lyon-industries/component-intelligence/contents/<component-directory>?ref=<commit>
```

## Complete packages

`catalog.json` contains only directories under `components/`. Every listed
package has:

- exact manufacturer and MPN identity
- source-backed pins, ratings, package, and integration findings
- independently cross-checked normalized data
- verified native symbol
- verified native footprint with explicit pad geometry
- verified STEP model with stated mechanical scope
- hashes, tool versions, provenance, and rights information
- no active fabrication-stop finding

Physical testing remains an independent evidence flag. A complete CAD package
does not claim that every downstream circuit or product has been qualified.

## Candidate work

`candidate-catalog.json` indexes directories under `candidates/`. These records
are intentionally excluded from ordinary component discovery and must not be
consumed as complete CAD packages.

A candidate may contain a source-backed pin map, a useful failure report, one
native asset, or another bounded improvement. This keeps contribution work
approachable while preserving the default catalog's trust boundary.

Candidate records use the same schema and expose the same capability flags, so
an agent can identify exactly which symbol, footprint, STEP, cross-check, or
evidence task remains.

## Repository layout

```text
catalog.json                 # complete packages only
candidate-catalog.json       # collaborative incomplete work
components/<maker>/<mpn>/    # complete package trust tier
candidates/<maker>/<mpn>/    # incomplete collaborative tier
schema/component.schema.json
scripts/build_catalog.py     # maintainer generation tool
scripts/generate_native_assets.py # maintainer CAD serialization tool
scripts/validate.py          # maintainer trust-boundary validator
```

Each complete component directory normally contains:

```text
component.json
README.md
<exact-mpn>.kicad_sym
<exact-mpn>.kicad_mod
<exact-mpn>.step
```

Actual subdirectory names may follow native tool conventions; the canonical
paths are always declared in `component.json`. Directory names percent-encode
reserved MPN characters while record identities preserve exact spelling.

## Return field findings

When a consuming agent discovers a wrong pin, import error, footprint problem,
mechanical mismatch, assembly failure, moved source, or application constraint,
return the smallest shareable correction to this repository.

Real findings belong in `integration.findings` even if the reporter cannot
complete every missing CAD asset. A serious finding against a complete package
must either be corrected immediately or demote the component to `candidates/`
in the same change.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`QUALITY.md`](QUALITY.md).

## Maintainer validation

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/build_catalog.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

## License and source rights

Original repository content is Apache-2.0. Manufacturer names and product names
identify referenced parts. Linked manufacturer documents are not redistributed
or relicensed by default. Every included CAD asset records its provenance,
limitations, and source basis.
