#!/usr/bin/env python3
"""Generate indexes, KiCad tables, summaries, and the component catalog graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.generate_component_graph import render_component_graph
    from scripts.generate_native_assets import native_asset_name
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from generate_component_graph import render_component_graph
    from generate_native_assets import native_asset_name


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/lyon-industries/component-intelligence"
CATALOGS = {
    "components": ("catalog.json", "complete"),
    "candidates": ("candidate-catalog.json", "candidate"),
}


def kicad_quote(value: object) -> str:
    """Escape a value for a quoted KiCad S-expression string."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def markdown_cell(value: object) -> str:
    """Keep generated Markdown table cells on one row."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_path(path: Path) -> str:
    """Link to repository paths whose directory names contain literal percent signs."""
    return path.as_posix().replace("%", "%25")


def load_records(root: Path = ROOT, area: str | None = None) -> list[tuple[str, Path, dict[str, object]]]:
    areas = (area,) if area else tuple(CATALOGS)
    records = []
    for current_area in areas:
        for path in sorted((root / current_area).glob("*/*/component.json")):
            records.append((current_area, path, json.loads(path.read_text(encoding="utf-8"))))
    return records


def catalog_entry(root: Path, path: Path, record: dict[str, object]) -> dict[str, object]:
    verification = record["verification"]
    return {
        "id": record["id"],
        "manufacturer_slug": record["identity"]["manufacturer_slug"],
        "manufacturer": record["identity"]["manufacturer"],
        "mpn": record["identity"]["mpn"],
        "category": record["classification"]["category"],
        "function": record["classification"]["function"],
        "keywords": record["classification"]["keywords"],
        "package": record["package"]["name"],
        "path": str(path.relative_to(root)),
        "orderable": record["identity"]["orderable"],
        "orderable_checked_on": record["identity"]["orderable_checked_on"],
        "reviewed_on": verification["reviewed_on"],
        "rating_keys": sorted(rating["key"] for rating in record["electrical"]["ratings"]),
        "capabilities": {
            "identity_verified": verification["identity_verified"],
            "data_cross_checked": verification["data_cross_checked"],
            "symbol_verified": verification["symbol_verified"],
            "footprint_verified": verification["footprint_verified"],
            "step_verified": verification["step_verified"],
            "physically_tested": verification["physically_tested"],
        },
        "active_findings": sum(finding["status"] == "active" for finding in record["integration"]["findings"]),
    }


def build_catalog(root: Path = ROOT, area: str = "components") -> dict[str, object]:
    filename, tier = CATALOGS[area]
    entries = [catalog_entry(root, path, record) for _, path, record in load_records(root, area)]
    entries.sort(key=lambda item: (item["manufacturer_slug"], item["mpn"]))
    return {
        "schema_version": "1.0.0",
        "tier": tier,
        "repository": REPOSITORY,
        "generated_from": f"{area}/*/*/component.json",
        "components": entries,
    }


def native_library_records(root: Path = ROOT) -> list[tuple[str, Path, dict[str, object]]]:
    """Return complete records after enforcing the shared KiCad nickname contract."""
    libraries: list[tuple[str, Path, dict[str, object]]] = []
    nicknames: dict[str, tuple[str, str]] = {}
    for _, record_path, record in load_records(root, "components"):
        mpn = record["identity"]["mpn"]
        nickname = native_asset_name(mpn)
        if not nickname:
            raise ValueError(f"{record['id']}: exact MPN does not produce a KiCad-safe nickname")
        verification = record["verification"]
        complete_gate = (
            "identity_verified",
            "data_cross_checked",
            "symbol_verified",
            "footprint_verified",
            "step_verified",
        )
        if not all(verification[field] for field in complete_gate):
            # Repository validation reports the misplaced or incomplete record.
            # It must not become available through project-local library tables.
            continue
        symbol_value = record["cad"]["symbol"]["path"]
        footprint_value = record["cad"]["footprint"]["path"]
        if not isinstance(symbol_value, str) or not isinstance(footprint_value, str):
            continue
        symbol_path = Path(symbol_value)
        footprint_path = Path(footprint_value)
        expected_symbol = Path(f"{nickname}.kicad_sym")
        expected_footprint = Path(f"{nickname}.pretty") / f"{nickname}.kicad_mod"
        if symbol_path != expected_symbol or footprint_path != expected_footprint:
            raise ValueError(
                f"{record['id']}: native asset paths must use KiCad nickname {nickname!r}"
            )
        nickname_key = nickname.casefold()
        if nickname_key in nicknames:
            previous_nickname, previous_id = nicknames[nickname_key]
            raise ValueError(
                f"KiCad nickname {nickname!r} conflicts with {previous_nickname!r}; "
                f"used by {previous_id} and {record['id']}"
            )
        nicknames[nickname_key] = (nickname, record["id"])
        libraries.append((nickname, record_path, record))
    libraries.sort(key=lambda item: (item[0].casefold(), item[0]))
    return libraries


def render_kicad_library_table(root: Path, kind: str) -> str:
    """Render a project-local KiCad symbol or footprint library table."""
    if kind not in {"symbol", "footprint"}:
        raise ValueError(f"unknown KiCad library table kind: {kind}")
    table_name = "sym_lib_table" if kind == "symbol" else "fp_lib_table"
    lines = [f"({table_name}", "  (version 7)"]
    for nickname, record_path, record in native_library_records(root):
        cad_path = Path(record["cad"][kind]["path"])
        component_path = record_path.parent.relative_to(root)
        asset_path = component_path / cad_path
        if kind == "footprint":
            asset_path = asset_path.parent
        uri = f"${{COMPONENT_INTELLIGENCE_ROOT}}/{asset_path.as_posix()}"
        description = (
            f"{record['identity']['manufacturer']} {record['identity']['mpn']} - "
            f"{record['classification']['function']}"
        )
        lines.append(
            f'  (lib (name "{kicad_quote(nickname)}")(type "KiCad")'
            f'(uri "{kicad_quote(uri)}")(options "")'
            f'(descr "{kicad_quote(description)}"))'
        )
    lines.extend([")", ""])
    return "\n".join(lines)


def capability_summary(record: dict[str, object]) -> str:
    labels = (
        ("identity_verified", "identity"),
        ("data_cross_checked", "data"),
        ("symbol_verified", "symbol"),
        ("footprint_verified", "footprint"),
        ("step_verified", "STEP"),
        ("physically_tested", "physical test"),
    )
    available = [label for field, label in labels if record["verification"][field]]
    return ", ".join(available) if available else "none admitted"


def render_human_catalog(root: Path = ROOT) -> str:
    """Render a browsable catalog without changing the machine-readable contract."""
    complete = load_records(root, "components")
    candidates = load_records(root, "candidates")
    lines = [
        "# Component catalog",
        "",
        "Generated by `scripts/build_catalog.py` from canonical component records. Do not edit this file directly.",
        "",
        "The [complete catalog](catalog.json) contains packages admitted through the repository's local data and native-CAD gate. "
        "The [candidate catalog](candidate-catalog.json) is incomplete work and must not be consumed as finished CAD.",
        "",
        f"## Complete packages ({len(complete)})",
        "",
        "| Exact MPN | Manufacturer | Category | Function | Package | Reviewed | Physical evidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, record_path, record in complete:
        identity = record["identity"]
        target = markdown_path(record_path.parent.relative_to(root)) + "/"
        values = (
            f"[{markdown_cell(identity['mpn'])}]({target})",
            markdown_cell(identity["manufacturer"]),
            markdown_cell(record["classification"]["category"]),
            markdown_cell(record["classification"]["function"]),
            markdown_cell(record["package"]["name"]),
            markdown_cell(record["verification"]["reviewed_on"]),
            "yes" if record["verification"]["physically_tested"] else "no",
        )
        lines.append("| " + " | ".join(values) + " |")

    lines.extend([
        "",
        f"## Candidates ({len(candidates)})",
        "",
        "Candidates can contain useful reviewed facts, but each one is excluded from the complete KiCad tables.",
        "",
        "| Exact MPN | Manufacturer | Function | Package | Admitted capabilities | Active findings |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for _, record_path, record in candidates:
        identity = record["identity"]
        target = markdown_path(record_path.parent.relative_to(root)) + "/"
        active_findings = sum(
            finding["status"] == "active" for finding in record["integration"]["findings"]
        )
        values = (
            f"[{markdown_cell(identity['mpn'])}]({target})",
            markdown_cell(identity["manufacturer"]),
            markdown_cell(record["classification"]["function"]),
            markdown_cell(record["package"]["name"]),
            markdown_cell(capability_summary(record)),
            str(active_findings),
        )
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")
    return "\n".join(lines)


def render_readme(record: dict[str, object], area: str) -> str:
    identity = record["identity"]
    verification = record["verification"]
    findings = [item for item in record["integration"]["findings"] if item["status"] == "active"]
    heading = "Complete package" if area == "components" else "Candidate work"
    boundary = (
        "This directory is listed in the complete catalog and contains the verified native symbol, footprint, and STEP model."
        if area == "components"
        else "This directory is incomplete and excluded from the complete catalog. Do not consume it as a finished CAD package."
    )
    lines = [
        f"# {identity['mpn']}", "",
        f"{identity['manufacturer']} {record['classification']['function']} in {record['package']['name']}.", "",
        f"## {heading}", "", boundary, "",
        f"- Identity verified: `{str(verification['identity_verified']).lower()}`",
        f"- Data cross-checked: `{str(verification['data_cross_checked']).lower()}`",
        f"- Native symbol verified: `{str(verification['symbol_verified']).lower()}`",
        f"- Native footprint verified: `{str(verification['footprint_verified']).lower()}`",
        f"- STEP model verified: `{str(verification['step_verified']).lower()}`",
        f"- Physically tested: `{str(verification['physically_tested']).lower()}`",
    ]
    if findings:
        lines.extend(["", "## Integration findings", ""])
        lines.extend(f"- {finding['summary']}" for finding in findings)
    lines.extend(["", "## Official sources", ""])
    lines.extend(f"- [{source['title']}]({source['url']})" for source in record["sources"])
    lines.extend(["", "`component.json` is the canonical machine-readable record.", ""])
    return "\n".join(lines)


def generated_outputs(root: Path = ROOT) -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for area, (filename, _) in CATALOGS.items():
        outputs[root / filename] = json.dumps(build_catalog(root, area), indent=2, ensure_ascii=False) + "\n"
        for _, record_path, record in load_records(root, area):
            outputs[record_path.parent / "README.md"] = render_readme(record, area)
    outputs[root / "CATALOG.md"] = render_human_catalog(root)
    outputs[root / "kicad" / "sym-lib-table"] = render_kicad_library_table(root, "symbol")
    outputs[root / "kicad" / "fp-lib-table"] = render_kicad_library_table(root, "footprint")
    outputs[root / "assets" / "component-catalog-graph.svg"] = render_component_graph(root)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when generated files are stale")
    args = parser.parse_args()
    outputs = generated_outputs()
    stale = [str(path.relative_to(ROOT)) for path, expected in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    if args.check:
        if stale:
            print(f"generated files are stale: {stale}")
            return 1
        print("PASS generated catalogs, component summaries, KiCad tables, and catalog graph")
        return 0
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"WROTE {len(outputs)} generated files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
