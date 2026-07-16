# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import re
import unittest
from datetime import date
from pathlib import Path

from PIL import Image

from scripts.validate import ROOT, readiness_blockers


COMPONENT = ROOT / "components/littelfuse/PTS815SJM250SMTRLFS"
RECORD_PATH = COMPONENT / "component.json"
PCB_STYLE_PATH = ROOT / "quality/pcb-render-style.json"


def read_record() -> dict[str, object]:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def assert_balanced_sexpression(test: unittest.TestCase, text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            test.assertGreaterEqual(depth, 0)
    test.assertFalse(in_string)
    test.assertEqual(0, depth)


class PTS815DigitalQualificationTests(unittest.TestCase):
    def test_record_exposes_exact_terminal_topology_and_boundaries(self) -> None:
        record = read_record()
        pins = record["electrical"]["pins"]

        self.assertEqual(["1", "2", "3", "4"], [pin["number"] for pin in pins])
        self.assertTrue(all(pin["electrical_type"] == "passive" for pin in pins))
        self.assertEqual(
            [["1", "2"], ["3", "4"]],
            record["electrical"]["internally_common_terminal_groups"],
        )
        self.assertTrue(
            all(rating.get("boundary") for rating in record["electrical"]["ratings"])
        )

    def test_native_symbol_has_four_passive_pins_and_common_pair_labels(self) -> None:
        symbol = (COMPONENT / "PTS815SJM250SMTRLFS.kicad_sym").read_text(
            encoding="utf-8"
        )
        assert_balanced_sexpression(self, symbol)

        self.assertEqual(4, symbol.count("(pin passive line"))
        for pin_number in ("1", "2", "3", "4"):
            self.assertEqual(1, symbol.count(f'(number "{pin_number}"'))
        self.assertEqual(2, symbol.count('(name "POLE_A"'))
        self.assertEqual(2, symbol.count('(name "POLE_B"'))
        self.assertIn('(text "1-2 COMMON"', symbol)
        self.assertIn('(text "3-4 COMMON"', symbol)

    def test_native_footprint_matches_normalized_pad_contract(self) -> None:
        record = read_record()
        footprint = (
            COMPONENT
            / "PTS815SJM250SMTRLFS.pretty/PTS815SJM250SMTRLFS.kicad_mod"
        ).read_text(encoding="utf-8")
        assert_balanced_sexpression(self, footprint)

        actual: dict[str, tuple[float, float, float, float]] = {}
        pad_pattern = re.compile(
            r'\(pad "([1-4])" smd roundrect\s*'
            r'\(at ([-0-9.]+) ([-0-9.]+)\)\s*'
            r'\(size ([-0-9.]+) ([-0-9.]+)\)',
            re.MULTILINE,
        )
        for match in pad_pattern.finditer(footprint):
            actual[match.group(1)] = tuple(float(value) for value in match.groups()[1:])

        expected = {
            pad["number"]: (
                pad["x_mm"],
                pad["y_mm"],
                pad["width_mm"],
                pad["height_mm"],
            )
            for pad in record["package"]["land_pattern"]["pads"]
        }
        self.assertEqual(expected, actual)
        self.assertEqual(4, footprint.count('(layers "F.Cu" "F.Mask" "F.Paste")'))
        self.assertEqual(4, footprint.count("(solder_mask_margin 0.05)"))
        self.assertNotIn("solder_paste_margin", footprint)
        self.assertIn('(layer "F.CrtYd")', footprint)
        self.assertIn('(layer "F.Fab")', footprint)
        self.assertIn("${COMPONENT_INTELLIGENCE_ROOT}", footprint)

    def test_declared_asset_hashes_match_repository_bytes(self) -> None:
        record = read_record()
        for asset in record["cad"].values():
            path = COMPONENT / asset["path"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(asset["sha256"], digest, path)

    def test_step_is_ap214_in_millimetres(self) -> None:
        step = (
            COMPONENT
            / "PTS815SJM250SMTRLFS.3dshapes/PTS815SJM250SMTRLFS.step"
        ).read_text(encoding="utf-8")
        self.assertTrue(step.startswith("ISO-10303-21;"))
        self.assertIn("10303 214", step)
        self.assertIn("SI_UNIT(.MILLI.,.METRE.)", step)
        self.assertTrue(step.rstrip().endswith("END-ISO-10303-21;"))

    def test_physical_coupon_keeps_all_four_terminals_independent(self) -> None:
        qualification = json.loads(
            (
                COMPONENT / "qualification/coupon-rev-a/qualification.json"
            ).read_text(encoding="utf-8")
        )
        board = (
            COMPONENT
            / "qualification/coupon-rev-a/pts815-coupon-rev-a.kicad_pcb"
        ).read_text(encoding="utf-8")

        self.assertEqual("design-verified-not-fabricated", qualification["fixture"]["state"])
        self.assertEqual("lyon-industries-pcb-v1", qualification["board_style"]["style_id"])
        self.assertEqual(0, qualification["design_verification"]["drc_violations"])
        self.assertEqual(0, qualification["design_verification"]["unconnected_items"])
        self.assertEqual("not-tested", qualification["planned_functional_test"]["current_result"])
        for terminal in ("1", "2", "3", "4"):
            self.assertIn(f'(net "TERMINAL_{terminal}")', board)
            self.assertIn(f'(property "Reference" "TP{terminal}"', board)
        self.assertEqual(4, board.count('(segment\n'))
        self.assertIn("NO COPPER JOINS THE DUT TERMINALS", board)

    def test_coupon_uses_repository_pcb_brand_style(self) -> None:
        style = json.loads(PCB_STYLE_PATH.read_text(encoding="utf-8"))
        coupon = (
            COMPONENT
            / "qualification/coupon-rev-a/pts815-coupon-rev-a.kicad_pcb"
        ).read_text(encoding="utf-8")
        model_fixture = (COMPONENT / "preview/model-fixture.kicad_pcb").read_text(
            encoding="utf-8"
        )

        self.assertEqual("#FFFFFF", style["render"]["background_hex"])
        self.assertEqual("Black", style["board"]["solder_mask"]["kicad_color"])
        self.assertEqual("White", style["board"]["silkscreen"]["kicad_color"])
        self.assertEqual("ENIG", style["board"]["surface_finish"]["kicad_name"])
        self.assertEqual(1.5, style["board"]["corner_radius_mm"])
        for board in (coupon, model_fixture):
            self.assertEqual(2, board.count('(color "Black")'))
            self.assertEqual(2, board.count('(color "White")'))
            self.assertIn('(copper_finish "ENIG")', board)
            self.assertEqual(4, board.count("(gr_arc"))
        self.assertIn("RENDER FIXTURE - NOT FOR FABRICATION", model_fixture)

    def test_pcb_renders_have_white_background_black_board_and_gold_copper(self) -> None:
        paths = (
            COMPONENT / "model.png",
            COMPONENT / "qualification/coupon-rev-a/coupon-render.png",
        )
        for path in paths:
            with Image.open(path) as image:
                rgb = image.convert("RGB")
                corners = (
                    rgb.getpixel((0, 0)),
                    rgb.getpixel((rgb.width - 1, 0)),
                    rgb.getpixel((0, rgb.height - 1)),
                    rgb.getpixel((rgb.width - 1, rgb.height - 1)),
                )
                self.assertEqual(((255, 255, 255),) * 4, corners, path)
                pixels = list(rgb.getdata())
                self.assertGreater(
                    sum(red < 55 and green < 65 and blue < 70 for red, green, blue in pixels),
                    1000,
                    path,
                )
        with Image.open(
            COMPONENT / "qualification/coupon-rev-a/coupon-render.png"
        ) as coupon:
            self.assertGreater(
                sum(
                    red > 140 and 75 < green < 210 and blue < 100
                    for red, green, blue in coupon.convert("RGB").getdata()
                ),
                100,
            )

    def test_candidate_is_blocked_only_by_declared_open_qualification_work(self) -> None:
        blockers = readiness_blockers(read_record(), date(2026, 7, 16))
        self.assertEqual(
            [
                "exact package lacks assembly-tested physical evidence",
                "one or more validation checks remain open",
                "one or more known issues remain open",
                "a fabrication-stop issue is not resolved",
            ],
            blockers,
        )


if __name__ == "__main__":
    unittest.main()
