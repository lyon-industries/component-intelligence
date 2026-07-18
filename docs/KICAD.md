# KiCad integration and audit

Component Intelligence distributes KiCad 10 symbol libraries, footprint
libraries, and repository-local nominal STEP models. The canonical engineering
record remains `component.json`; native filenames are an integration detail.

## Add the complete catalog to a project

1. Clone this repository at a pinned commit.
2. In KiCad 10, open **Preferences → Configure Paths**.
3. Add `COMPONENT_INTELLIGENCE_ROOT` and set it to the absolute repository path.
4. For a new project without project-specific library tables, copy
   `kicad/sym-lib-table` and `kicad/fp-lib-table` into the project directory.
5. For an existing project, open the Symbol and Footprint Library managers and
   merge the desired entries. Do not overwrite existing project tables.

KiCad supports project-specific library tables and path-variable substitution;
see the official [Schematic Editor library documentation](https://docs.kicad.org/master/en/eeschema/eeschema.html#managing-symbol-libraries).

The generated tables contain only `components/` records that satisfy the local
complete-package gate. Candidate records are not exposed.

## Native names and exact MPNs

KiCad library nicknames cannot safely contain every character used in an exact
MPN. The generator therefore uses a deterministic native name, for example:

```text
Exact MPN:        24LC256-I/SN
Repository path: components/microchip/24LC256-I%2FSN/
KiCad nickname:  24LC256-I_SN
```

The exact MPN remains in `component.json` and the symbol Value field. Consumers
must use the canonical record for purchasing and identity checks.

## 2026-07-18 KLC audit

The launch audit ran KiCad's upstream `kicad-library-utils` checker at commit
`f733308c80768a7d42d0f92284f61abf7e6f3ec0` across all 46 complete packages.

| Asset | Result |
| --- | --- |
| Symbols | 46/46 passed with their generated footprint libraries resolved |
| Footprints | 46/46 passed every checked rule except F9.3 |
| KiCad 10.0.4 native export | 46/46 symbols and 46/46 footprints opened and exported to SVG |
| F9.3 | Expected deviation for the repository-local STEP path described below |

The upstream convention expects official-library 3D paths beginning with
`${KICAD10_3DMODEL_DIR}` and a matching official footprint-library directory.
This repository instead uses:

```text
${COMPONENT_INTELLIGENCE_ROOT}/components/<maker>/<encoded-mpn>/<native-name>.3dshapes/<native-name>.step
```

That choice keeps each exact-MPN record and its hashed STEP file portable at a
pinned repository commit. `scripts/validate.py` requires the footprint path to
resolve to the exact declared local asset. This is a documented KLC F9.3
deviation, not a claim of full KLC compliance.

The native smoke test ran `kicad-cli` 10.0.4 directly from the official
read-only macOS disk image. It supplied `COMPONENT_INTELLIGENCE_ROOT`, opened
each complete symbol and footprint library, and exported each asset to SVG.
`scripts/audit_kicad_native.py` reproduces that test on any host with KiCad 10.
Checks also include deterministic replay, structural parsing, CadQuery/Open
CASCADE STEP reopen and measurement, and the upstream KLC checker. Opening the
project-specific library tables and placing the assets in the consuming design
remain downstream acceptance steps.

```sh
python3 scripts/audit_kicad_native.py --kicad-cli /path/to/kicad-cli
```

## Before fabrication

- confirm the exact orderable MPN and package suffix against a current official
  source
- compare symbol pin numbers, names, electrical types, and hidden power pins to
  the intended circuit
- inspect pad numbering, pin-one orientation, body outline, courtyard, and
  assembly drawing at high zoom
- adapt solder paste, solder mask, thermal relief, via, finish, and stencil
  details to the PCB fabricator and assembler
- run ERC and DRC using the project's real rules, stackup, and net classes
- inspect the STEP model in the enclosure and remember it is a nominal envelope
- qualify the assembled exact MPN under the application's electrical, thermal,
  mechanical, environmental, regulatory, and lifecycle constraints

A complete repository package is a better starting point, not the final design
authority.
