#!/usr/bin/env python3
"""Generate complete and candidate indexes plus component summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/lyon-industries/component-intelligence"
CATALOGS = {
    "components": ("catalog.json", "complete"),
    "candidates": ("candidate-catalog.json", "candidate"),
}


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
        print("PASS complete catalog, candidate catalog, and generated summaries")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print(f"WROTE {len(outputs)} generated files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
