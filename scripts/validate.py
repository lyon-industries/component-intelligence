#!/usr/bin/env python3
"""Validate candidate evidence and the complete-package trust boundary."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

from jsonschema import Draft202012Validator, FormatChecker

try:
    from scripts.build_catalog import CATALOGS, build_catalog, load_records, render_readme
    from scripts.generate_native_assets import (
        body_height,
        footprint_text,
        native_asset_name,
        oriented_body_dimensions,
        pin_electrical_type,
        symbol_text,
    )
except ModuleNotFoundError:
    from build_catalog import CATALOGS, build_catalog, load_records, render_readme
    from generate_native_assets import (
        body_height,
        footprint_text,
        native_asset_name,
        oriented_body_dimensions,
        pin_electrical_type,
        symbol_text,
    )


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


def _on_grid(value: float, grid: float = 0.05) -> bool:
    return math.isclose(value / grid, round(value / grid), abs_tol=1e-7)


def _silk_line_hits_pad(
    line: tuple[float, float, float, float, float],
    pad: tuple[float, float, float, float],
    clearance: float = 0.2,
) -> bool:
    x1, y1, x2, y2, width = line
    px, py, pw, ph = pad
    margin = clearance + width / 2
    xmin, xmax = px - pw / 2 - margin, px + pw / 2 + margin
    ymin, ymax = py - ph / 2 - margin, py + ph / 2 + margin
    if math.isclose(y1, y2):
        return ymin <= y1 <= ymax and max(min(x1, x2), xmin) <= min(max(x1, x2), xmax)
    if math.isclose(x1, x2):
        return xmin <= x1 <= xmax and max(min(y1, y2), ymin) <= min(max(y1, y2), ymax)
    return False


def _validate_step_geometry(record: dict[str, object], asset_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        import cadquery as cq
    except ImportError:
        return ["CadQuery is required to reopen and measure included STEP models"]
    try:
        model = cq.importers.importStep(str(asset_path))
        solid_count = model.solids().size()
        bounds = model.val().BoundingBox()
    except Exception as exc:  # pragma: no cover - backend error text varies
        return [f"STEP model could not be reopened: {exc}"]
    if solid_count < 1:
        errors.append("STEP model contains no reopenable solid")
        return errors
    expected_x, expected_y = oriented_body_dimensions(record)
    expected_z = body_height(record)
    if not math.isclose(bounds.zmin, 0, abs_tol=0.02):
        errors.append(f"STEP seating plane is z={bounds.zmin:g} mm, expected 0 mm")
    if not math.isclose(bounds.zmax, expected_z, abs_tol=0.05):
        errors.append(f"STEP height is {bounds.zmax:g} mm, expected {expected_z:g} mm")
    if bounds.xlen + 0.05 < expected_x or bounds.ylen + 0.05 < expected_y:
        errors.append("STEP body envelope is smaller than the normalized body dimensions")
    pads = record["package"]["land_pattern"]["pads"]
    pad_span_x = 2 * max(abs(float(pad["x_mm"])) + float(pad["width_mm"]) / 2 for pad in pads)
    pad_span_y = 2 * max(abs(float(pad["y_mm"])) + float(pad["height_mm"]) / 2 for pad in pads)
    if bounds.xlen > max(expected_x, pad_span_x) + 0.5 or bounds.ylen > max(expected_y, pad_span_y) + 0.5:
        errors.append("STEP envelope exceeds the normalized body and land-pattern envelope")
    return errors


def validate_native_asset(record: dict[str, object], name: str, asset_path: Path, area: str) -> list[str]:
    """Check that native CAD structure agrees with the normalized record."""
    errors: list[str] = []
    text = asset_path.read_text(encoding="utf-8", errors="replace")
    expected_pins = {pin["number"] for pin in record["electrical"]["pins"]}
    expected_pads = [
        (pad["number"], float(pad["x_mm"]), float(pad["y_mm"]), float(pad["width_mm"]), float(pad["height_mm"]))
        for pad in record["package"]["land_pattern"]["pads"]
    ]
    if name == "symbol":
        if not text.startswith("(kicad_symbol_lib"):
            errors.append("symbol is not a KiCad symbol library")
        if text != symbol_text(record):
            errors.append("symbol is not reproducible from the current reviewed record and generator")
        pattern = re.compile(
            r'\(pin\s+([a-z_]+)\s+\w+.*?\(name\s+"([^"]*)".*?\(number\s+"([^"]+)"',
            re.DOTALL,
        )
        parsed = pattern.findall(text)
        actual = {number: (pin_name, electrical_type) for electrical_type, pin_name, number in parsed}
        expected = {
            pin["number"]: (pin["name"], pin_electrical_type(pin["electrical_type"]))
            for pin in record["electrical"]["pins"]
        }
        if len(parsed) != len(actual):
            errors.append("symbol contains duplicate pin numbers")
        if actual != expected:
            errors.append("symbol pin numbers, names, or electrical types differ from record")
    elif name == "footprint":
        if not text.startswith("(footprint"):
            errors.append("footprint is not a KiCad footprint")
        if text != footprint_text(record, area):
            errors.append("footprint is not reproducible from the current reviewed record and generator")
        if '(layer "F.CrtYd")' not in text or '(layer "F.Fab")' not in text:
            errors.append("footprint lacks F.CrtYd or F.Fab geometry")
        pattern = re.compile(
            r'\(pad\s+"([^"]+)"\s+smd\s+\w+\s+\(at\s+([-+\d.eE]+)\s+([-+\d.eE]+)(?:\s+[-+\d.eE]+)?\)\s+\(size\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)\s+\(layers\s+([^\)]+)\)'
        )
        parsed_pads = pattern.findall(text)
        actual_pads = [
            (number, float(x), float(y), float(width), float(height))
            for number, x, y, width, height, _ in parsed_pads
        ]
        rounded_actual = Counter((number, *(round(value, 6) for value in values)) for number, *values in actual_pads)
        rounded_expected = Counter((number, *(round(value, 6) for value in values)) for number, *values in expected_pads)
        if rounded_actual != rounded_expected:
            errors.append("footprint pad coordinates or sizes differ from record")
        for number, *_, layers in parsed_pads:
            if not {'"F.Cu"', '"F.Paste"', '"F.Mask"'}.issubset(set(layers.split())):
                errors.append(f"footprint pad {number} lacks F.Cu, F.Paste, or F.Mask")
        if {pad[0] for pad in expected_pads} != expected_pins:
            errors.append("footprint pad numbers differ from the electrical pin map")
        if not re.search(r'\(property\s+"Reference"\s+"REF\*\*"', text):
            errors.append("footprint reference field is not REF**")
        if f'(property "Value" "{native_asset_name(record["identity"]["mpn"])}"' not in text:
            errors.append("footprint value does not match its KiCad-safe native name")
        if not re.search(r'\(fp_text\s+user\s+"\$\{REFERENCE\}".*?\(layer\s+"F\.Fab"\)', text, re.DOTALL):
            errors.append("footprint lacks the F.Fab reference text")
        pin_names = {str(pin["name"]).strip().lower() for pin in record["electrical"]["pins"]}
        needs_pin_one_marker = len(record["electrical"]["pins"]) > 2 or bool(
            pin_names & {"a", "k", "anode", "cathode", "+", "-"}
        )
        if needs_pin_one_marker and not re.search(r'\(fp_circle.*?\(layer\s+"F\.SilkS"\)', text, re.DOTALL):
            errors.append("footprint lacks a silkscreen pin-one marker")
        courtyard_pattern = re.compile(
            r'\(fp_line\s+\(start\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)\s+\(end\s+([-+\d.eE]+)\s+([-+\d.eE]+)\).*?\(layer\s+"F\.CrtYd"\)',
            re.DOTALL,
        )
        courtyard = [tuple(float(value) for value in match) for match in courtyard_pattern.findall(text)]
        if len(courtyard) != 4 or any(not _on_grid(value) for line in courtyard for value in line):
            errors.append("footprint courtyard is not a four-line rectangle on the 0.05 mm grid")
        silk_pattern = re.compile(
            r'\(fp_line\s+\(start\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)\s+\(end\s+([-+\d.eE]+)\s+([-+\d.eE]+)\)\s+\(stroke\s+\(width\s+([-+\d.eE]+)\)[^\n]*?\(layer\s+"F\.SilkS"\)',
        )
        silk_lines = [tuple(float(value) for value in match) for match in silk_pattern.findall(text)]
        pad_rects = [(x, y, width, height) for _, x, y, width, height in expected_pads]
        if any(_silk_line_hits_pad(line, pad) for line in silk_lines for pad in pad_rects):
            errors.append("footprint silkscreen violates the 0.20 mm pad clearance")
        expected_model = f'${{COMPONENT_INTELLIGENCE_ROOT}}/{area}/{record["identity"]["manufacturer_slug"]}/{quote(record["identity"]["mpn"], safe="-._~")}/{record["cad"]["step_model"]["path"]}'
        if f'(model "{expected_model}"' not in text:
            errors.append("footprint STEP path does not match the record and repository layout")
    elif name == "step_model":
        if not text.lstrip().startswith("ISO-10303-21;") or "END-ISO-10303-21;" not in text:
            errors.append("STEP model is not a complete ISO-10303-21 exchange file")
        if not any(token in text for token in ("MANIFOLD_SOLID_BREP", "FACETED_BREP", "SHELL_BASED_SURFACE_MODEL")):
            errors.append("STEP model contains no supported solid or shell representation")
        errors.extend(_validate_step_geometry(record, asset_path))
    return errors


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
        for dimension, value in record["package"]["body_dimensions_mm"].items():
            candidates = [value] if isinstance(value, (int, float)) else value.values()
            if any(float(candidate) <= 0 for candidate in candidates):
                errors.append(f"{relative}: body dimension {dimension} must be positive")

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
                        else:
                            errors.extend(
                                f"{relative}: {name}: {message}"
                                for message in validate_native_asset(record, name, asset_path, area)
                            )
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
        check_names = [check["name"] for check in verification["checks"]]
        if len(check_names) != len(set(check_names)):
            errors.append(f"{relative}: duplicate verification check name")

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
