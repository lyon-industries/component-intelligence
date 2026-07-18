# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.build_catalog import generated_outputs, render_readme
from scripts.validate import ROOT, sha256_file, validate_repository


FIXED_TODAY = date(2026, 7, 18)


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class RepositoryValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "repository"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "tmp"))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def regenerate(self) -> None:
        for path, content in generated_outputs(self.root).items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def replace_asset_text(self, component: str, asset_name: str, text: str) -> None:
        record_path = self.root / component / "component.json"
        record = read_json(record_path)
        asset_path = record_path.parent / record["cad"][asset_name]["path"]
        asset_path.write_text(text, encoding="utf-8")
        record["cad"][asset_name]["sha256"] = sha256_file(asset_path)
        write_json(record_path, record)
        self.regenerate()

    def validate(self) -> tuple[list[str], object]:
        return validate_repository(self.root, today=FIXED_TODAY)

    def test_current_repository_passes_with_hard_trust_boundary(self) -> None:
        errors, stats = self.validate()
        self.assertEqual([], errors)
        self.assertEqual(len(list(self.root.glob("components/*/*/component.json"))), stats.complete)
        self.assertEqual(len(list(self.root.glob("candidates/*/*/component.json"))), stats.candidates)
        self.assertGreater(stats.complete, 0)
        self.assertGreater(stats.candidates, 0)

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
        self.assertEqual(len(list(self.root.glob("candidates/*/*/component.json"))), stats.candidates)

    def test_incomplete_record_cannot_enter_complete_catalog(self) -> None:
        source = self.root / "candidates/analog-devices/MAX3485ESA%2B"
        target = self.root / "components/analog-devices/MAX3485ESA%2B"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, target)
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
        path = self.root / "candidates/analog-devices/MAX3485ESA%2B/component.json"
        record = read_json(path)
        record["cad"]["symbol"]["verified"] = True
        record["verification"]["symbol_verified"] = True
        write_json(path, record)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("unavailable symbol cannot be verified" in error for error in errors), errors)

    def test_physical_flag_requires_exact_mpn_evidence(self) -> None:
        path = self.root / "candidates/analog-devices/MAX3485ESA%2B/component.json"
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

    def test_symbol_pin_name_tampering_is_detected_after_hash_refresh(self) -> None:
        component = "components/littelfuse/PTS815SJM250SMTRLFS"
        record = read_json(self.root / component / "component.json")
        asset_path = self.root / component / record["cad"]["symbol"]["path"]
        text = asset_path.read_text(encoding="utf-8")
        self.assertIn('(name "POLE_A"', text)
        self.replace_asset_text(component, "symbol", text.replace('(name "POLE_A"', '(name "WRONG"', 1))
        errors, _ = self.validate()
        self.assertTrue(
            any("symbol pin numbers, names, or electrical types differ from record" in error for error in errors),
            errors,
        )

    def test_duplicate_footprint_pad_is_detected_after_hash_refresh(self) -> None:
        component = "components/littelfuse/PTS815SJM250SMTRLFS"
        record = read_json(self.root / component / "component.json")
        asset_path = self.root / component / record["cad"]["footprint"]["path"]
        lines = asset_path.read_text(encoding="utf-8").splitlines()
        pad_index = next(index for index, line in enumerate(lines) if line.startswith('\t(pad "1"'))
        lines.insert(pad_index + 1, lines[pad_index])
        self.replace_asset_text(component, "footprint", "\n".join(lines) + "\n")
        errors, _ = self.validate()
        self.assertTrue(any("footprint pad coordinates or sizes differ from record" in error for error in errors), errors)

    def test_silkscreen_pad_collision_is_detected_after_hash_refresh(self) -> None:
        component = "components/littelfuse/PTS815SJM250SMTRLFS"
        record = read_json(self.root / component / "component.json")
        asset_path = self.root / component / record["cad"]["footprint"]["path"]
        lines = asset_path.read_text(encoding="utf-8").splitlines()
        pad = record["package"]["land_pattern"]["pads"][0]
        collision = (
            f'(start {float(pad["x_mm"]) - 0.1:g} {float(pad["y_mm"]):g}) '
            f'(end {float(pad["x_mm"]) + 0.1:g} {float(pad["y_mm"]):g})'
        )
        for index, line in enumerate(lines):
            if line.startswith("\t(fp_line") and '(layer "F.SilkS")' in line:
                lines[index], substitutions = re.subn(
                    r'\(start [-+\d.eE]+ [-+\d.eE]+\) \(end [-+\d.eE]+ [-+\d.eE]+\)',
                    collision,
                    line,
                    count=1,
                )
                self.assertEqual(1, substitutions)
                break
        else:  # pragma: no cover - the source fixture is itself invalid if reached
            self.fail("fixture footprint has no F.SilkS line")
        self.replace_asset_text(component, "footprint", "\n".join(lines) + "\n")
        errors, _ = self.validate()
        self.assertTrue(any("silkscreen violates the 0.20 mm pad clearance" in error for error in errors), errors)

    def test_step_seating_offset_is_detected_after_hash_refresh(self) -> None:
        import cadquery as cq

        component = "components/littelfuse/PTS815SJM250SMTRLFS"
        record_path = self.root / component / "component.json"
        record = read_json(record_path)
        asset_path = record_path.parent / record["cad"]["step_model"]["path"]
        model = cq.importers.importStep(str(asset_path)).translate((0, 0, 0.25))
        cq.exporters.export(model, str(asset_path), exportType="STEP")
        record["cad"]["step_model"]["sha256"] = sha256_file(asset_path)
        write_json(record_path, record)
        self.regenerate()
        errors, _ = self.validate()
        self.assertTrue(any("STEP seating plane is" in error for error in errors), errors)

    def test_stale_complete_catalog_is_detected(self) -> None:
        catalog_path = self.root / "catalog.json"
        catalog = read_json(catalog_path)
        catalog["components"][0]["function"] = "stale"
        write_json(catalog_path, catalog)
        errors, _ = self.validate()
        self.assertIn("catalog.json is stale; run python3 scripts/build_catalog.py", errors)

    def test_generated_summaries_name_the_trust_tier(self) -> None:
        complete = read_json(self.root / "components/littelfuse/PTS815SJM250SMTRLFS/component.json")
        candidate = read_json(self.root / "candidates/analog-devices/MAX3485ESA%2B/component.json")
        self.assertIn("Complete package", render_readme(complete, "components"))
        self.assertIn("excluded from the complete catalog", render_readme(candidate, "candidates"))


if __name__ == "__main__":
    unittest.main()
