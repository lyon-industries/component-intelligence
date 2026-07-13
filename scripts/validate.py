#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "component.schema.json"
CATALOG_PATH = ROOT / "catalog.json"


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)


def main() -> int:
    errors: list[str] = []
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    catalog = load_json(CATALOG_PATH)

    entries = catalog.get("components", [])
    catalog_ids: set[str] = set()
    record_ids: set[str] = set()
    catalog_paths: set[str] = set()

    sort_keys = [(entry["manufacturer_slug"], entry["mpn"]) for entry in entries]
    if sort_keys != sorted(sort_keys):
        errors.append("catalog components are not sorted by manufacturer slug and MPN")

    for entry in entries:
        component_id = entry["id"]
        if component_id in catalog_ids:
            errors.append(f"duplicate catalog id: {component_id}")
        catalog_ids.add(component_id)

        record_relative_path = entry["path"]
        if record_relative_path in catalog_paths:
            errors.append(f"duplicate catalog path: {record_relative_path}")
        catalog_paths.add(record_relative_path)

        record_path = ROOT / record_relative_path
        if not record_path.is_file():
            errors.append(f"missing component record: {record_relative_path}")
            continue

        if not (record_path.parent / "README.md").is_file():
            errors.append(f"{record_relative_path}: missing component README.md")

        record = load_json(record_path)
        for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = "/".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{entry['path']}:{location}: {error.message}")

        if record["id"] != component_id:
            errors.append(f"{entry['path']}: catalog and record ids differ")
        if record["id"] in record_ids:
            errors.append(f"duplicate record id: {record['id']}")
        record_ids.add(record["id"])

        identity = record["identity"]
        if identity["manufacturer_slug"] != entry["manufacturer_slug"]:
            errors.append(f"{entry['path']}: manufacturer slug differs from catalog")
        if identity["mpn"] != entry["mpn"]:
            errors.append(f"{entry['path']}: MPN differs from catalog")

        expected_path = (
            Path("components")
            / identity["manufacturer_slug"]
            / quote(identity["mpn"], safe="")
            / "component.json"
        )
        if Path(record_relative_path) != expected_path:
            errors.append(
                f"{record_relative_path}: path does not match manufacturer slug and MPN"
            )
        if entry["manufacturer"] != identity["manufacturer"]:
            errors.append(f"{record_relative_path}: manufacturer differs from catalog")

        orderable = identity.get("orderable")
        orderable_checked_on = identity.get("orderable_checked_on")
        if orderable is True and not orderable_checked_on:
            errors.append(f"{record_relative_path}: orderable part lacks checked date")
        if orderable is not True and orderable_checked_on:
            errors.append(
                f"{record_relative_path}: non-confirmed orderability has a checked date"
            )

        pins = record["electrical"]["pins"]
        pin_numbers = [pin["number"] for pin in pins]
        pin_set = set(pin_numbers)
        if len(pin_numbers) != len(pin_set):
            errors.append(f"{entry['path']}: duplicate pin number")
        if len(pin_numbers) != record["package"]["pin_count"]:
            errors.append(f"{entry['path']}: package pin count differs from pin map")

        groups = record["electrical"]["internally_common_terminal_groups"]
        grouped: set[str] = set()
        for group in groups:
            missing = set(group) - pin_set
            if missing:
                errors.append(f"{entry['path']}: common group names unknown pins {sorted(missing)}")
            overlap = grouped.intersection(group)
            if overlap:
                errors.append(f"{entry['path']}: pins appear in multiple common groups {sorted(overlap)}")
            grouped.update(group)

        pads = record["package"]["land_pattern"].get("pads", [])
        if pads:
            pad_numbers = {pad["number"] for pad in pads}
            if len(pads) != record["package"]["land_pattern"]["pad_count"]:
                errors.append(f"{entry['path']}: pad count differs from listed pads")
            if pad_numbers != pin_set:
                errors.append(f"{entry['path']}: pad numbers differ from electrical pins")

        source_id_list = [source["id"] for source in record["sources"]]
        source_ids = set(source_id_list)
        if len(source_id_list) != len(source_ids):
            errors.append(f"{record_relative_path}: duplicate source id")
        for source in record["sources"]:
            if source["retrieval_status"] == "captured-and-hashed" and not source["sha256"]:
                errors.append(f"{entry['path']}: captured source lacks a hash")
            if source["retrieval_status"] == "captured-and-hashed" and not source.get("byte_size"):
                errors.append(f"{entry['path']}: captured source lacks a byte size")
            if source["retrieval_status"] == "browser-reviewed-byte-capture-blocked" and source["sha256"]:
                errors.append(f"{entry['path']}: blocked byte capture must not claim a hash")
            if source["retrieval_status"] == "browser-reviewed-byte-capture-blocked" and source.get("byte_size"):
                errors.append(f"{entry['path']}: blocked byte capture must not claim a byte size")
            page_count = source.get("page_count")
            if page_count:
                for locator in source["locators"]:
                    if locator["page"] > page_count:
                        errors.append(
                            f"{record_relative_path}: source locator page {locator['page']} "
                            f"exceeds {page_count}-page source {source['id']}"
                        )

        for pin in pins:
            if pin["source_id"] not in source_ids:
                errors.append(f"{entry['path']}: pin {pin['number']} references an unknown source")
        for rating in record["electrical"]["ratings"]:
            if rating["source_id"] not in source_ids:
                errors.append(f"{entry['path']}: rating {rating['name']} references an unknown source")

        land_source_id = record["package"]["land_pattern"]["source_id"]
        if land_source_id not in source_ids:
            errors.append(f"{record_relative_path}: land pattern references an unknown source")
        for assembly_field in ("packing", "orientation"):
            assembly_source_id = record["assembly"][assembly_field].get("source_id")
            if assembly_source_id and assembly_source_id not in source_ids:
                errors.append(
                    f"{record_relative_path}: {assembly_field} references an unknown source"
                )

        for asset_name, asset in record["cad"].items():
            if asset["path"]:
                asset_path = record_path.parent / asset["path"]
                if not asset_path.is_file():
                    errors.append(f"{entry['path']}: missing {asset_name} asset {asset['path']}")

        validation = record["validation"]
        if validation["evidence_state"] != entry["evidence_state"]:
            errors.append(f"{record_relative_path}: evidence state differs from catalog")
        if validation["physical_state"] != entry["physical_state"]:
            errors.append(f"{record_relative_path}: physical state differs from catalog")
        if not validation["known_issues"]:
            errors.append(f"{record_relative_path}: no known integration risk is recorded")
        if validation["physical_state"] == "not-tested" and validation["release_state"] == "production-approved":
            errors.append(f"{entry['path']}: untested component cannot be production-approved")
        if validation["evidence_state"] == "physically-verified" and validation["physical_state"] == "not-tested":
            errors.append(f"{entry['path']}: physical evidence state conflicts with test state")

    if catalog_ids != record_ids:
        errors.append("catalog and loaded record id sets differ")

    discovered_paths = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "components").glob("*/*/component.json")
    }
    orphan_paths = discovered_paths - catalog_paths
    missing_paths = catalog_paths - discovered_paths
    if orphan_paths:
        errors.append(f"component records missing from catalog: {sorted(orphan_paths)}")
    if missing_paths:
        errors.append(f"catalog paths missing from components tree: {sorted(missing_paths)}")

    if errors:
        for error in errors:
            fail(error)
        return 1

    print(f"PASS schema: {SCHEMA_PATH.relative_to(ROOT)}")
    print(f"PASS catalog: {len(entries)} component records")
    print(
        "PASS semantic checks: catalog coverage, paths, ids, pins, pads, sources, "
        "assets, orderability, and release states"
    )
    print("LIMIT: extracted and cross-checked records are not physical qualification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
