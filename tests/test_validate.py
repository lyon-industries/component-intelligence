# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.validate import ROOT, validate_repository


FIXED_TODAY = date(2026, 7, 16)


def read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(
            ROOT,
            self.root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def validate(self) -> tuple[list[str], object]:
        return validate_repository(self.root, today=FIXED_TODAY)

    def test_current_repository_passes_with_frozen_legacy_debt(self) -> None:
        errors, stats = self.validate()

        self.assertEqual([], errors)
        self.assertEqual(20, stats.records)
        self.assertEqual(0, stats.agent_ready)
        self.assertEqual(20, stats.legacy)

    def test_new_reference_only_record_is_rejected(self) -> None:
        catalog_path = self.root / "catalog.json"
        catalog = read_json(catalog_path)
        source_entry = copy.deepcopy(catalog["components"][0])
        source_path = self.root / source_entry["path"]
        new_mpn = "MAX3485ESA-TEST"
        new_id = "component:analog-devices:MAX3485ESA-TEST"
        new_relative_path = Path(
            "components/analog-devices/MAX3485ESA-TEST/component.json"
        )
        new_directory = (self.root / new_relative_path).parent
        shutil.copytree(source_path.parent, new_directory)

        record = read_json(new_directory / "component.json")
        record["id"] = new_id
        record["identity"]["mpn"] = new_mpn
        write_json(new_directory / "component.json", record)

        source_entry["id"] = new_id
        source_entry["mpn"] = new_mpn
        source_entry["path"] = str(new_relative_path)
        catalog["components"].append(source_entry)
        catalog["components"].sort(
            key=lambda item: (item["manufacturer_slug"], item["mpn"])
        )
        write_json(catalog_path, catalog)

        errors, _ = self.validate()

        self.assertTrue(
            any("new records must be agent-ready" in error for error in errors),
            errors,
        )

    def test_false_agent_ready_claim_exposes_blockers(self) -> None:
        record_path = self.root / "components/diodes-inc/AP63205WU-7/component.json"
        record = read_json(record_path)
        record["validation"]["release_state"] = "agent-ready"
        write_json(record_path, record)

        errors, _ = self.validate()

        self.assertTrue(
            any("exact MPN orderability is not confirmed" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("symbol is not approved for machine use" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("exact package lacks assembly-tested" in error for error in errors),
            errors,
        )

    def test_legacy_baseline_cannot_grow(self) -> None:
        legacy_path = self.root / "quality/legacy-records.json"
        legacy = read_json(legacy_path)
        legacy["component_ids"].append("component:test:NOT-IN-CATALOG")
        legacy["component_ids"].sort()
        write_json(legacy_path, legacy)

        errors, _ = self.validate()

        self.assertTrue(
            any("legacy baseline grew" in error for error in errors), errors
        )
        self.assertTrue(
            any(
                "not present when the admission rule was activated" in error
                for error in errors
            ),
            errors,
        )
        self.assertTrue(
            any("legacy ids missing from catalog" in error for error in errors),
            errors,
        )

    def test_svg_preview_cannot_be_declared_machine_usable(self) -> None:
        record_path = self.root / "components/diodes-inc/AP63205WU-7/component.json"
        record = read_json(record_path)
        svg_path = record_path.parent / "symbol.svg"
        symbol = record["cad"]["symbol"]
        symbol["status"] = "cross-checked"
        symbol["format"] = "svg"
        symbol["sha256"] = hashlib.sha256(svg_path.read_bytes()).hexdigest()
        symbol["manufacturing_use"] = True
        write_json(record_path, record)

        errors, _ = self.validate()

        self.assertTrue(
            any(
                "SVG preview cannot be a machine-use symbol" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
