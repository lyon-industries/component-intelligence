# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts.generate_native_assets import (
    ROOT,
    body_height,
    footprint_text,
    lead_axis,
    native_asset_name,
    oriented_body_dimensions,
    reference_prefix,
    symbol_text,
)


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
        self.assertEqual("R", reference_prefix(record("components/wurth-elektronik/560112116005")))
        self.assertEqual("C", reference_prefix(record("components/wurth-elektronik/885382206004")))
        self.assertEqual("L", reference_prefix(record("components/wurth-elektronik/74404024100")))
        self.assertEqual("SW", reference_prefix(record("components/littelfuse/PTS815SJM250SMTRLFS")))

    def test_passive_and_switch_body_dimensions_use_the_reviewed_record(self) -> None:
        resistor = record("components/wurth-elektronik/560112116005")
        inductor = record("components/wurth-elektronik/74404024100")
        switch = record("components/littelfuse/PTS815SJM250SMTRLFS")
        self.assertEqual((1.6, 0.8), oriented_body_dimensions(resistor))
        self.assertEqual((2.5, 2.0), oriented_body_dimensions(inductor))
        self.assertEqual(2.5, body_height(switch))

    def test_kicad_safe_asset_name_preserves_exact_mpn_in_record_and_paths(self) -> None:
        component = record("components/nexperia/BAT54C%2C215")
        self.assertEqual("BAT54C_215", native_asset_name(component["identity"]["mpn"]))
        symbol = symbol_text(component)
        footprint = footprint_text(component, "components")
        self.assertIn('(symbol "BAT54C_215"', symbol)
        self.assertIn('(property "Value" "BAT54C,215"', symbol)
        self.assertIn('(property "Footprint" "BAT54C_215:BAT54C_215"', symbol)
        self.assertIn(
            '${COMPONENT_INTELLIGENCE_ROOT}/components/nexperia/BAT54C%2C215/BAT54C_215.3dshapes/BAT54C_215.step',
            footprint,
        )


if __name__ == "__main__":
    unittest.main()
