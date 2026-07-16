#!/usr/bin/env python3
"""Validate candidate evidence and the complete-package trust boundary."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

from jsonschema import Draft202012Validator, FormatChecker

try:
    from scripts.build_catalog import CATALOGS, build_catalog, load_records, render_readme
except ModuleNotFoundError:
    from build_catalog import CATALOGS, build_catalog, load_records, render_readme


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ValidationStats:
    complete: int
    candidates: int
    findings: int
    physically_tested: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def complete_package_blockers(record: dict[str, object]) -> list[str]:
    verification = record["verification"]
    blockers = []
    for flag in ("identity_verified", "data_cross_checked", "symbol_verified", "footprint_verified", "step_verified"):
        if not verification[flag]:
            blockers.append(f"{flag} is false")
    for name in ("symbol", "footprint", "step_model"):
        asset = record["cad"][name]
        if asset["availability"] != "included" or not asset["verified"]:
            blockers.append(f"{name} is not included and verified")
    land = record["package"]["land_pattern"]
    if land["status"] != "cross-checked":
        blockers.append("land pattern is not cross-checked")
    if not land["pads"]:
        blockers.append("explicit pad geometry is missing")
    if not land["coordinate_convention"]:
        blockers.append("land-pattern coordinate convention is missing")
    if not verification["checks"]:
        blockers.append("verification checks are missing")
    if record["rights"]["source_rights_status"] == "review-required":
        blockers.append("source rights review is open")
    if any(finding["status"] == "active" and finding["severity"] == "fabrication-stop" for finding in record["integration"]["findings"]):
        blockers.append("active fabrication-stop finding remains")
    return blockers


def validate_repository(root: Path = ROOT, *, today: date | None = None) -> tuple[list[str], ValidationStats]:
    today = today or date.today()
    errors: list[str] = []
    schema = json.loads((root / "schema/component.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = load_records(root)
    ids: set[str] = set()
    counts = {"components": 0, "candidates": 0, "findings": 0, "tested": 0}

    for area, record_path, record in records:
        counts[area] += 1
        relative = str(record_path.relative_to(root))
        schema_errors = sorted(validator.iter_errors(record), key=lambda item: list(item.path))
        for error in schema_errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{relative}:{location}: {error.message}")
        if schema_errors:
            continue

        component_id = record["id"]
        if component_id in ids:
            errors.append(f"duplicate component id across trust tiers: {component_id}")
        ids.add(component_id)
        identity = record["identity"]
        encoded_mpn = quote(identity["mpn"], safe="-._~")
        expected = Path(area) / identity["manufacturer_slug"] / encoded_mpn / "component.json"
        if relative != str(expected):
            errors.append(f"{relative}: path does not match exact identity; expected {expected}")
        if component_id != f"component:{identity['manufacturer_slug']}:{identity['mpn']}":
            errors.append(f"{relative}: id does not match identity")
        readme_path = record_path.parent / "README.md"
        if not readme_path.is_file() or readme_path.read_text(encoding="utf-8") != render_readme(record, area):
            errors.append(f"{relative}: generated README.md is missing or stale")

        blockers = complete_package_blockers(record)
        if area == "components" and blockers:
            errors.extend(f"{relative}: complete-package blocker: {blocker}" for blocker in blockers)
        if area == "candidates" and not blockers:
            errors.append(f"{relative}: candidate satisfies the complete-package gate and must be promoted")

        if identity["orderable"] is True and not identity["orderable_checked_on"]:
            errors.append(f"{relative}: orderable=true requires orderable_checked_on")
        if identity["orderable"] is not True and identity["orderable_checked_on"]:
            errors.append(f"{relative}: unconfirmed orderability cannot have a checked date")
        for value, label in ((identity["orderable_checked_on"], "orderability"), (record["verification"]["reviewed_on"], "review")):
            if value and date.fromisoformat(value) > today:
                errors.append(f"{relative}: {label} date is in the future")

        source_ids = [source["id"] for source in record["sources"]]
        source_set = set(source_ids)
        if len(source_ids) != len(source_set):
            errors.append(f"{relative}: duplicate source id")
        for source in record["sources"]:
            retrieved = datetime.fromisoformat(source["retrieved_at"].replace("Z", "+00:00"))
            if retrieved > datetime.now(timezone.utc):
                errors.append(f"{relative}: source retrieval date is in the future")
            captured = source["retrieval_status"] == "captured-and-hashed"
            if captured != bool(source["sha256"] and source["byte_size"]):
                errors.append(f"{relative}: source capture state conflicts with hash or byte size")
            if source["page_count"] and any(locator["page"] > source["page_count"] for locator in source["locators"]):
                errors.append(f"{relative}: source locator exceeds page count for {source['id']}")

        pins = record["electrical"]["pins"]
        pin_numbers = [pin["number"] for pin in pins]
        pin_set = set(pin_numbers)
        if len(pin_numbers) != len(pin_set):
            errors.append(f"{relative}: duplicate pin number")
        if len(pin_numbers) != record["package"]["pin_count"]:
            errors.append(f"{relative}: package pin count differs from pin map")
        if any(pin["source_id"] not in source_set for pin in pins):
            errors.append(f"{relative}: pin references unknown source")
        grouped: set[str] = set()
        for group in record["electrical"]["internally_common_terminal_groups"]:
            if set(group) - pin_set:
                errors.append(f"{relative}: terminal group references unknown pin")
            if grouped.intersection(group):
                errors.append(f"{relative}: terminal appears in multiple common groups")
            grouped.update(group)

        rating_keys = [rating["key"] for rating in record["electrical"]["ratings"]]
        if len(rating_keys) != len(set(rating_keys)):
            errors.append(f"{relative}: duplicate normalized rating key")
        if any(rating["source_id"] not in source_set for rating in record["electrical"]["ratings"]):
            errors.append(f"{relative}: rating references unknown source")

        land = record["package"]["land_pattern"]
        if land["source_id"] and land["source_id"] not in source_set:
            errors.append(f"{relative}: land pattern references unknown source")
        if land["pads"] and len(land["pads"]) != land["pad_count"]:
            errors.append(f"{relative}: explicit pad count differs from land pattern")

        verification = record["verification"]
        for name, asset in record["cad"].items():
            if asset["availability"] == "included":
                if not asset["path"] or not asset["format"] or not asset["sha256"]:
                    errors.append(f"{relative}: included {name} lacks path, format, or hash")
                else:
                    asset_path = (record_path.parent / asset["path"]).resolve()
                    try:
                        asset_path.relative_to(root.resolve())
                    except ValueError:
                        errors.append(f"{relative}: {name} escapes repository root")
                    else:
                        if not asset_path.is_file():
                            errors.append(f"{relative}: missing included {name} {asset['path']}")
                        elif sha256_file(asset_path) != asset["sha256"]:
                            errors.append(f"{relative}: {name} hash differs")
            elif asset["path"] or asset["format"] or asset["sha256"] or asset["tool_version"]:
                errors.append(f"{relative}: unavailable {name} carries a local asset claim")
            if asset["availability"] != "included" and asset["verified"]:
                errors.append(f"{relative}: unavailable {name} cannot be verified")
            if any(source_id not in source_set for source_id in asset["source_ids"]):
                errors.append(f"{relative}: {name} references unknown source")
            flag = f"{'step' if name == 'step_model' else name}_verified"
            if verification[flag] != asset["verified"]:
                errors.append(f"{relative}: {name} verification flag differs from asset")

        evidence = verification["physical_test_evidence"]
        if verification["physically_tested"] != bool(evidence):
            errors.append(f"{relative}: physically_tested must match physical_test_evidence")
        if any(test["exact_mpn"] != identity["mpn"] for test in evidence):
            errors.append(f"{relative}: physical test exact MPN differs")
        counts["tested"] += int(verification["physically_tested"])

        finding_ids = [finding["id"] for finding in record["integration"]["findings"]]
        if len(finding_ids) != len(set(finding_ids)):
            errors.append(f"{relative}: duplicate finding id")
        if any(source_id not in source_set for finding in record["integration"]["findings"] for source_id in finding["source_ids"]):
            errors.append(f"{relative}: finding references unknown source")
        counts["findings"] += len(finding_ids)

    for area, (filename, _) in CATALOGS.items():
        try:
            actual = json.loads((root / filename).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            actual = None
        if actual != build_catalog(root, area):
            errors.append(f"{filename} is stale; run python3 scripts/build_catalog.py")

    stats = ValidationStats(counts["components"], counts["candidates"], counts["findings"], counts["tested"])
    return errors, stats


def main() -> int:
    errors, stats = validate_repository()
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print("PASS schema, evidence, assets, and trust-tier validation")
    print(f"PASS complete catalog: {stats.complete} packages")
    print(f"PASS candidate catalog: {stats.candidates} staged records")
    print(f"PASS shared evidence: {stats.findings} findings; {stats.physically_tested} physically tested")
    print("BOUNDARY: default catalog contains complete local CAD packages only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
