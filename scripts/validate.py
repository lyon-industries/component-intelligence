#!/usr/bin/env python3
# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_RELATIVE_PATH = Path("schema/component.schema.json")
CATALOG_RELATIVE_PATH = Path("catalog.json")
LEGACY_RELATIVE_PATH = Path("quality/legacy-records.json")
AGENT_READY_PROFILE = "agentic-ee-v1"
ORDERABILITY_MAX_AGE_DAYS = 365
FROZEN_LEGACY_ID_ALLOWLIST = frozenset(
    {
        "component:analog-devices:MAX3485ESA+",
        "component:aos:AO3400A",
        "component:bosch:BME280",
        "component:diodes-inc:AP63205WU-7",
        "component:espressif:ESP32-C3-WROOM-02-N4",
        "component:littelfuse:PTS815SJM250SMTRLFS",
        "component:microchip:24LC256-I/SN",
        "component:microchip:ATtiny85-20SU",
        "component:microchip:MCP73831T-2ACI/OT",
        "component:nexperia:BAT54C,215",
        "component:st:STM32C011F6P6TR",
        "component:st:USBLC6-2SC6",
        "component:ti:ADS1115IDGSR",
        "component:ti:INA219AIDCNR",
        "component:ti:LM358DR",
        "component:ti:NE555DR",
        "component:ti:PCA9306DCTR",
        "component:ti:SN74LVC1G17DBVR",
        "component:ti:TLV75533PDBVR",
        "component:ti:TPS62162DSGR",
    }
)


@dataclass(frozen=True)
class ValidationStats:
    records: int
    agent_ready: int
    legacy: int


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_asset_path(root: Path, record_path: Path, value: str) -> Path | None:
    candidate = (record_path.parent / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def readiness_blockers(record: dict[str, object], today: date) -> list[str]:
    blockers: list[str] = []
    identity = record["identity"]
    electrical = record["electrical"]
    package = record["package"]
    cad = record["cad"]
    assembly = record["assembly"]
    validation = record["validation"]
    rights = record["rights"]

    if identity.get("orderable") is not True:
        blockers.append("exact MPN orderability is not confirmed")
    checked_on = identity.get("orderable_checked_on")
    if not checked_on:
        blockers.append("orderability check date is missing")
    else:
        checked_date = date.fromisoformat(checked_on)
        age_days = (today - checked_date).days
        if age_days < 0:
            blockers.append("orderability check date is in the future")
        elif age_days > ORDERABILITY_MAX_AGE_DAYS:
            blockers.append(
                f"orderability check is {age_days} days old; maximum is "
                f"{ORDERABILITY_MAX_AGE_DAYS}"
            )

    if validation["evidence_state"] not in {"cross-checked", "physically-verified"}:
        blockers.append("evidence is not independently cross-checked")
    if validation["physical_state"] != "assembly-tested":
        blockers.append("exact package lacks assembly-tested physical evidence")

    pins = electrical["pins"]
    if any(not pin.get("electrical_type") for pin in pins):
        blockers.append("one or more pins lack an electrical type")
    ratings = electrical["ratings"]
    if not ratings:
        blockers.append("no bounded electrical ratings are recorded")
    elif any(not rating.get("boundary") for rating in ratings):
        blockers.append("one or more ratings lack boundary semantics")

    land_pattern = package["land_pattern"]
    pads = land_pattern.get("pads", [])
    if land_pattern["status"] != "cross-checked":
        blockers.append("land pattern is not cross-checked")
    if not pads:
        blockers.append("explicit pad geometry is missing")
    if not land_pattern.get("coordinate_convention"):
        blockers.append("land-pattern coordinate convention is missing")

    for asset_name in ("symbol", "footprint"):
        asset = cad[asset_name]
        if asset["status"] != "cross-checked":
            blockers.append(f"{asset_name} is not cross-checked")
        if not asset.get("path"):
            blockers.append(f"machine-usable {asset_name} path is missing")
        if asset.get("manufacturing_use") is not True:
            blockers.append(f"{asset_name} is not approved for machine use")
        if not asset.get("format"):
            blockers.append(f"{asset_name} format is missing")
        elif asset["format"].lower() in {"svg", "image/svg+xml"}:
            blockers.append(f"{asset_name} is an SVG preview, not a native EDA asset")
        if not asset.get("sha256"):
            blockers.append(f"{asset_name} hash is missing")

    step_model = cad["step_model"]
    if step_model["status"] == "not-applicable":
        if not step_model.get("reason"):
            blockers.append("STEP not-applicable decision lacks a reason")
    else:
        if step_model["status"] != "cross-checked":
            blockers.append("STEP model is neither cross-checked nor not-applicable")
        if not step_model.get("path"):
            blockers.append("checked STEP path is missing")
        if step_model.get("manufacturing_use") is not True:
            blockers.append("STEP model is not approved for machine use")
        if not step_model.get("format"):
            blockers.append("STEP model format is missing")
        if not step_model.get("sha256"):
            blockers.append("STEP model hash is missing")

    if assembly["orientation"]["status"] != "documented":
        blockers.append("assembly orientation is not fully documented")
    if any(check["status"] == "open" for check in validation["checks"]):
        blockers.append("one or more validation checks remain open")
    if any(issue["status"] == "open" for issue in validation["known_issues"]):
        blockers.append("one or more known issues remain open")
    if any(
        issue["severity"] == "fabrication-stop"
        and issue["status"] != "resolved-in-example"
        for issue in validation["known_issues"]
    ):
        blockers.append("a fabrication-stop issue is not resolved")
    if rights["source_rights_status"] == "review-required":
        blockers.append("source rights review remains open")

    return blockers


def validate_repository(
    root: Path = ROOT, *, today: date | None = None
) -> tuple[list[str], ValidationStats]:
    errors: list[str] = []
    today = today or date.today()
    schema_path = root / SCHEMA_RELATIVE_PATH
    catalog_path = root / CATALOG_RELATIVE_PATH
    legacy_path = root / LEGACY_RELATIVE_PATH

    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    catalog = load_json(catalog_path)
    legacy = load_json(legacy_path)

    schema_version = schema["properties"]["schema_version"]["const"]
    if catalog.get("schema_version") != schema_version:
        errors.append("catalog schema version differs from component schema")

    entries = catalog.get("components")
    if not isinstance(entries, list):
        errors.append("catalog components must be an array")
        return errors, ValidationStats(records=0, agent_ready=0, legacy=0)

    legacy_ids_list = legacy.get("component_ids")
    if not isinstance(legacy_ids_list, list):
        errors.append("legacy component_ids must be an array")
        legacy_ids_list = []
    if legacy_ids_list != sorted(legacy_ids_list):
        errors.append("legacy component ids are not sorted")
    if len(legacy_ids_list) != len(set(legacy_ids_list)):
        errors.append("legacy component ids contain duplicates")
    maximum_count = legacy.get("maximum_count")
    if not isinstance(maximum_count, int) or maximum_count < 0:
        errors.append("legacy maximum_count must be a non-negative integer")
        maximum_count = 0
    if len(legacy_ids_list) > maximum_count:
        errors.append(
            f"legacy baseline grew to {len(legacy_ids_list)} records; maximum is "
            f"{maximum_count}"
        )
    legacy_ids = set(legacy_ids_list)
    unrecognized_legacy_ids = legacy_ids - FROZEN_LEGACY_ID_ALLOWLIST
    if unrecognized_legacy_ids:
        errors.append(
            "legacy baseline contains ids not present when the admission rule was "
            f"activated: {sorted(unrecognized_legacy_ids)}"
        )

    catalog_ids: set[str] = set()
    record_ids: set[str] = set()
    catalog_paths: set[str] = set()
    release_states: dict[str, str] = {}

    required_entry_fields = {
        "id",
        "manufacturer_slug",
        "manufacturer",
        "mpn",
        "path",
        "evidence_state",
        "physical_state",
        "release_state",
    }
    if any(not isinstance(entry, dict) for entry in entries):
        errors.append("catalog entries must be objects")
        return errors, ValidationStats(records=0, agent_ready=0, legacy=len(legacy_ids))
    entry_shape_invalid = False
    for index, entry in enumerate(entries):
        missing = required_entry_fields - set(entry)
        if missing:
            errors.append(f"catalog entry {index} lacks fields {sorted(missing)}")
            entry_shape_invalid = True
    if entry_shape_invalid:
        return errors, ValidationStats(records=0, agent_ready=0, legacy=len(legacy_ids))

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

        record_path = root / record_relative_path
        if not record_path.is_file():
            errors.append(f"missing component record: {record_relative_path}")
            continue
        try:
            record_path.resolve().relative_to(root.resolve())
        except ValueError:
            errors.append(
                f"component record escapes repository root: {record_relative_path}"
            )
            continue

        if not (record_path.parent / "README.md").is_file():
            errors.append(f"{record_relative_path}: missing component README.md")

        record = load_json(record_path)
        schema_errors = sorted(
            validator.iter_errors(record), key=lambda item: list(item.path)
        )
        for error in schema_errors:
            location = "/".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{entry['path']}:{location}: {error.message}")

        record_id = record.get("id")
        if record_id != component_id:
            errors.append(f"{entry['path']}: catalog and record ids differ")
        if isinstance(record_id, str):
            if record_id in record_ids:
                errors.append(f"duplicate record id: {record_id}")
            record_ids.add(record_id)
        if schema_errors:
            continue

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
        if orderable_checked_on and date.fromisoformat(orderable_checked_on) > today:
            errors.append(
                f"{record_relative_path}: orderability checked date is in the future"
            )
        if date.fromisoformat(record["validation"]["reviewed_on"]) > today:
            errors.append(f"{record_relative_path}: review date is in the future")
        for source in record["sources"]:
            retrieved = datetime.fromisoformat(
                source["retrieved_at"].replace("Z", "+00:00")
            )
            if retrieved > datetime.now(timezone.utc):
                errors.append(
                    f"{record_relative_path}: source retrieval date is in the future"
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
                errors.append(
                    f"{entry['path']}: common group names unknown pins {sorted(missing)}"
                )
            overlap = grouped.intersection(group)
            if overlap:
                errors.append(
                    f"{entry['path']}: pins appear in multiple common groups "
                    f"{sorted(overlap)}"
                )
            grouped.update(group)

        pads = record["package"]["land_pattern"].get("pads", [])
        if pads:
            pad_numbers = {pad["number"] for pad in pads}
            if len(pads) != record["package"]["land_pattern"]["pad_count"]:
                errors.append(f"{entry['path']}: pad count differs from listed pads")
            if pad_numbers != pin_set:
                errors.append(
                    f"{entry['path']}: pad numbers differ from electrical pins"
                )

        source_id_list = [source["id"] for source in record["sources"]]
        source_ids = set(source_id_list)
        if len(source_id_list) != len(source_ids):
            errors.append(f"{record_relative_path}: duplicate source id")
        for source in record["sources"]:
            if (
                source["retrieval_status"] == "captured-and-hashed"
                and not source["sha256"]
            ):
                errors.append(f"{entry['path']}: captured source lacks a hash")
            if source["retrieval_status"] == "captured-and-hashed" and not source.get(
                "byte_size"
            ):
                errors.append(f"{entry['path']}: captured source lacks a byte size")
            if (
                source["retrieval_status"] == "browser-reviewed-byte-capture-blocked"
                and source["sha256"]
            ):
                errors.append(
                    f"{entry['path']}: blocked byte capture must not claim a hash"
                )
            if source[
                "retrieval_status"
            ] == "browser-reviewed-byte-capture-blocked" and source.get("byte_size"):
                errors.append(
                    f"{entry['path']}: blocked byte capture must not claim a byte size"
                )
            page_count = source.get("page_count")
            if page_count:
                for locator in source["locators"]:
                    if locator["page"] > page_count:
                        errors.append(
                            f"{record_relative_path}: source locator page "
                            f"{locator['page']} exceeds {page_count}-page source "
                            f"{source['id']}"
                        )

        for pin in pins:
            if pin["source_id"] not in source_ids:
                errors.append(
                    f"{entry['path']}: pin {pin['number']} references an unknown source"
                )
        for rating in record["electrical"]["ratings"]:
            if rating["source_id"] not in source_ids:
                errors.append(
                    f"{entry['path']}: rating {rating['name']} references an unknown source"
                )

        land_source_id = record["package"]["land_pattern"]["source_id"]
        if land_source_id not in source_ids:
            errors.append(
                f"{record_relative_path}: land pattern references an unknown source"
            )
        for assembly_field in ("packing", "orientation"):
            assembly_source_id = record["assembly"][assembly_field].get("source_id")
            if assembly_source_id and assembly_source_id not in source_ids:
                errors.append(
                    f"{record_relative_path}: {assembly_field} references an unknown source"
                )

        for asset_name, asset in record["cad"].items():
            asset_value = asset.get("path")
            if asset_value:
                asset_path = relative_asset_path(root, record_path, asset_value)
                if asset_path is None:
                    errors.append(
                        f"{entry['path']}: {asset_name} asset escapes repository root"
                    )
                elif not asset_path.is_file():
                    errors.append(
                        f"{entry['path']}: missing {asset_name} asset {asset_value}"
                    )
                elif asset.get("sha256") and sha256_file(asset_path) != asset["sha256"]:
                    errors.append(f"{entry['path']}: {asset_name} asset hash differs")
            if asset.get("manufacturing_use") is True:
                if asset["status"] != "cross-checked":
                    errors.append(
                        f"{entry['path']}: machine-use {asset_name} is not cross-checked"
                    )
                if (
                    not asset_value
                    or not asset.get("format")
                    or not asset.get("sha256")
                ):
                    errors.append(
                        f"{entry['path']}: machine-use {asset_name} lacks path, format, or hash"
                    )
                if asset.get("format", "").lower() in {"svg", "image/svg+xml"}:
                    errors.append(
                        f"{entry['path']}: SVG preview cannot be a machine-use "
                        f"{asset_name}"
                    )
            if asset["status"] == "not-applicable" and (
                asset_value or asset.get("manufacturing_use") or not asset.get("reason")
            ):
                errors.append(
                    f"{entry['path']}: not-applicable {asset_name} has an asset or lacks a reason"
                )

        validation = record["validation"]
        release_state = validation["release_state"]
        release_states[record_id] = release_state
        if validation["evidence_state"] != entry["evidence_state"]:
            errors.append(
                f"{record_relative_path}: evidence state differs from catalog"
            )
        if validation["physical_state"] != entry["physical_state"]:
            errors.append(
                f"{record_relative_path}: physical state differs from catalog"
            )
        if release_state != entry["release_state"]:
            errors.append(f"{record_relative_path}: release state differs from catalog")
        if not validation["known_issues"]:
            errors.append(
                f"{record_relative_path}: no known integration risk is recorded"
            )
        if (
            validation["physical_state"] == "not-tested"
            and release_state == "production-approved"
        ):
            errors.append(
                f"{entry['path']}: untested component cannot be production-approved"
            )
        if (
            validation["evidence_state"] == "physically-verified"
            and validation["physical_state"] == "not-tested"
        ):
            errors.append(
                f"{entry['path']}: physical evidence state conflicts with test state"
            )
        if release_state == "production-approved":
            errors.append(
                f"{entry['path']}: production-approved is historical; use an application "
                "approval outside the shared catalog"
            )
        if release_state == "agent-ready":
            for blocker in readiness_blockers(record, today):
                errors.append(
                    f"{entry['path']}: {AGENT_READY_PROFILE} blocker: {blocker}"
                )

    if catalog_ids != record_ids:
        errors.append("catalog and loaded record id sets differ")

    discovered_paths = {
        str(path.relative_to(root))
        for path in (root / "components").glob("*/*/component.json")
    }
    orphan_paths = discovered_paths - catalog_paths
    missing_paths = catalog_paths - discovered_paths
    if orphan_paths:
        errors.append(f"component records missing from catalog: {sorted(orphan_paths)}")
    if missing_paths:
        errors.append(
            f"catalog paths missing from components tree: {sorted(missing_paths)}"
        )

    legacy_missing_from_catalog = legacy_ids - catalog_ids
    if legacy_missing_from_catalog:
        errors.append(
            f"legacy ids missing from catalog: {sorted(legacy_missing_from_catalog)}"
        )
    ready_ids = {
        component_id
        for component_id, state in release_states.items()
        if state == "agent-ready"
    }
    stale_legacy_ids = legacy_ids.intersection(ready_ids)
    if stale_legacy_ids:
        errors.append(
            f"agent-ready records remain in legacy baseline: {sorted(stale_legacy_ids)}"
        )
    non_ready_ids = catalog_ids - ready_ids
    unadmitted_ids = non_ready_ids - legacy_ids
    if unadmitted_ids:
        errors.append(
            "new records must be agent-ready; non-ready ids outside the frozen legacy "
            f"baseline: {sorted(unadmitted_ids)}"
        )

    stats = ValidationStats(
        records=len(entries), agent_ready=len(ready_ids), legacy=len(legacy_ids)
    )
    return errors, stats


def main() -> int:
    errors, stats = validate_repository()
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    print(f"PASS schema: {SCHEMA_RELATIVE_PATH}")
    print(f"PASS catalog: {stats.records} component records")
    print(
        "PASS semantic checks: catalog coverage, paths, ids, pins, pads, sources, "
        "assets, orderability, rights, and release states"
    )
    print(
        f"PASS admission policy: {stats.agent_ready} agent-ready; "
        f"{stats.legacy} frozen legacy records"
    )
    print(
        "LIMIT: legacy records are remediation inventory and are not approved for "
        "autonomous schematic or PCB placement"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
