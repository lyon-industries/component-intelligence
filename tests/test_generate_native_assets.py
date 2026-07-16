# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts.generate_native_assets import ROOT, lead_axis, oriented_body_dimensions, reference_prefix


def record(path: str) -> dict[str, object]:
    return json.loads((ROOT / path / "component.json").read_text(encoding="utf-8"))


class NativeAssetGeometryTests(unittest.TestCase):
    def test_sot23_pad_rows_rotate_body_and_leads_together(self) -> None:
        component = record("components/nexperia/BAT54C%2C215")
        self.assertEqual("y", lead_axis(component))
        self.assertEqual((2.9, 1.3), oriented_body_dimensions(component))

    def test_dbv_pad_rows_keep_left_right_lead_axis(self) -> None:
        component = record("components/ti/SN74LVC1G17DBVR")
        self.assertEqual("x", lead_axis(component))
        self.assertEqual((1.6, 2.9), oriented_body_dimensions(component))

    def test_conventional_reference_prefixes(self) -> None:
        self.assertEqual("D", reference_prefix(record("components/nexperia/BAT54C%2C215")))
        self.assertEqual("Q", reference_prefix(record("components/aos/AO3400A")))
        self.assertEqual("U", reference_prefix(record("components/ti/SN74LVC1G17DBVR")))


if __name__ == "__main__":
    unittest.main()
