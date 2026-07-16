# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.build_catalog import generated_outputs, render_readme
from scripts.validate import ROOT, validate_repository


FIXED_TODAY = date(2026, 7, 16)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def regenerate(self) -> None:
        for path, content in generated_outputs(self.root).items():
            path.write_text(content, encoding="utf-8")

    def validate(self) -> tuple[list[str], object]:
        return validate_repository(self.root, today=FIXED_TODAY)

    def test_current_repository_passes_with_hard_trust_boundary(self) -> None:
        errors, stats = self.validate()
        self.assertEqual([], errors)
        self.assertEqual(1, stats.complete)
        self.assertEqual(19, stats.candidates)
        self.assertEqual(24, stats.findings)
        self.assertEqual(0, stats.physically_tested)

    def test_partial_candidate_is_allowed(self) -> None:
        source = self.root / "candidates/analog-devices/MAX3485ESA%2B"
        target = self.root / "candidates/analog-devices/MAX3485ESA-TEST"
        shutil.copytree(source, target)
        record = read_json(target / "component.json")
        record["id"] = "component:analog-devices:MAX3485ESA-TEST"
        record["identity"]["mpn"] = "MAX3485ESA-TEST"
        record["verification"]["identity_verified"] = False
        write_json(target / "component.json", record)
        self.regenerate()
        errors, stats = self.validate()
        self.assertEqual([], errors)
        self.assertEqual(20, stats.candidates)

    def test_incomplete_record_cannot_enter_complete_catalog(self) -> None:
        source = self.root / "candidates/ti/LM358DR"
        target = self.root / "components/ti/LM358DR"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("complete-package blocker: symbol_verified is false" in error for error in errors), errors)
        self.assertTrue(any("complete-package blocker: explicit pad geometry is missing" in error for error in errors), errors)

    def test_complete_candidate_must_be_promoted(self) -> None:
        source = self.root / "components/littelfuse/PTS815SJM250SMTRLFS"
        target = self.root / "candidates/littelfuse/PTS815SJM250SMTRLFS"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("candidate satisfies the complete-package gate" in error for error in errors), errors)

    def test_unavailable_asset_cannot_claim_verification(self) -> None:
        path = self.root / "candidates/ti/LM358DR/component.json"
        record = read_json(path)
        record["cad"]["symbol"]["verified"] = True
        record["verification"]["symbol_verified"] = True
        write_json(path, record)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("unavailable symbol cannot be verified" in error for error in errors), errors)

    def test_physical_flag_requires_exact_mpn_evidence(self) -> None:
        path = self.root / "candidates/ti/LM358DR/component.json"
        record = read_json(path)
        record["verification"]["physically_tested"] = True
        write_json(path, record)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("physically_tested must match" in error for error in errors), errors)

    def test_complete_asset_hash_tampering_is_detected(self) -> None:
        path = self.root / "components/littelfuse/PTS815SJM250SMTRLFS/component.json"
        record = read_json(path)
        record["cad"]["symbol"]["sha256"] = "0" * 64
        write_json(path, record)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("symbol hash differs" in error for error in errors), errors)

    def test_stale_complete_catalog_is_detected(self) -> None:
        catalog_path = self.root / "catalog.json"
        catalog = read_json(catalog_path)
        catalog["components"][0]["function"] = "stale"
        write_json(catalog_path, catalog)
        errors, _ = self.validate()
        self.assertIn("catalog.json is stale; run python3 scripts/build_catalog.py", errors)

    def test_generated_summaries_name_the_trust_tier(self) -> None:
        complete = read_json(self.root / "components/littelfuse/PTS815SJM250SMTRLFS/component.json")
        candidate = read_json(self.root / "candidates/ti/LM358DR/component.json")
        self.assertIn("Complete package", render_readme(complete, "components"))
        self.assertIn("excluded from the complete catalog", render_readme(candidate, "candidates"))


if __name__ == "__main__":
    unittest.main()
