# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import Counter
import re
import unittest
import xml.etree.ElementTree as ET

from scripts.build_catalog import (
    ROOT,
    generated_outputs,
    load_records,
    native_library_records,
    render_human_catalog,
    render_kicad_library_table,
)
from scripts.generate_component_graph import (
    ComponentNode,
    load_component_nodes,
    render_component_graph,
    validate_taxonomy,
    validate_visual_contract,
)


LIBRARY_NAME = re.compile(r'\(lib \(name "([^"]+)"\)')


class CatalogGenerationTests(unittest.TestCase):
    def test_checked_in_generated_outputs_are_current(self) -> None:
        stale = [
            path.relative_to(ROOT).as_posix()
            for path, expected in generated_outputs(ROOT).items()
            if not path.is_file() or path.read_text(encoding="utf-8") != expected
        ]
        self.assertEqual([], stale)

    def test_kicad_tables_expose_every_complete_package_once(self) -> None:
        expected = [name for name, _, _ in native_library_records(ROOT)]
        symbols = LIBRARY_NAME.findall(render_kicad_library_table(ROOT, "symbol"))
        footprints = LIBRARY_NAME.findall(render_kicad_library_table(ROOT, "footprint"))
        self.assertEqual(expected, symbols)
        self.assertEqual(expected, footprints)
        self.assertEqual(len(expected), len(set(expected)))

    def test_table_nicknames_match_symbol_footprint_properties(self) -> None:
        for nickname, record_path, record in native_library_records(ROOT):
            symbol_path = record_path.parent / record["cad"]["symbol"]["path"]
            symbol = symbol_path.read_text(encoding="utf-8")
            self.assertIn(
                f'(property "Footprint" "{nickname}:{nickname}"',
                symbol,
                record["id"],
            )

    def test_human_catalog_names_both_trust_tiers(self) -> None:
        catalog = render_human_catalog(ROOT)
        complete = len(load_records(ROOT, "components"))
        candidates = len(load_records(ROOT, "candidates"))
        self.assertIn(f"## Complete packages ({complete})", catalog)
        self.assertIn(f"## Candidates ({candidates})", catalog)
        self.assertIn("24LC256-I%252FSN/", catalog)

    def test_component_graph_contains_each_complete_mpn_once(self) -> None:
        graph = ET.fromstring(render_component_graph(ROOT))
        self.assertEqual("0 0 1600 900", graph.attrib["viewBox"])
        device_nodes = [
            node for node in graph.iter() if node.attrib.get("data-node-kind") == "device"
        ]
        actual_mpns = Counter(node.attrib["data-mpn"] for node in device_nodes)
        expected_mpns = Counter(node.mpn for node in load_component_nodes(ROOT))
        self.assertEqual(expected_mpns, actual_mpns)

        candidate_mpns = {
            record["identity"]["mpn"] for _, _, record in load_records(ROOT, "candidates")
        }
        self.assertTrue(candidate_mpns.isdisjoint(actual_mpns))

        category_nodes = {
            node.attrib["data-category"]
            for node in graph.iter()
            if node.attrib.get("data-node-kind") == "category"
        }
        expected_categories = {node.category for node in load_component_nodes(ROOT)}
        self.assertEqual(expected_categories, category_nodes)

    def test_component_graph_is_deterministic_and_fails_on_unmapped_category(self) -> None:
        self.assertEqual(render_component_graph(ROOT), render_component_graph(ROOT))
        with self.assertRaisesRegex(ValueError, "missing from graph presentation taxonomy"):
            validate_taxonomy(
                [ComponentNode(mpn="EXACT-MPN", category="new-category", path="components/test")]
            )

    def test_component_graph_keeps_the_lyon_visual_contract(self) -> None:
        svg = render_component_graph(ROOT)
        validate_visual_contract(svg)
        self.assertEqual(1, svg.count("#EA5C22"))
        self.assertIn("'Helvetica Neue', Arial, system-ui", svg)
        self.assertIn("ui-monospace, 'SF Mono', Menlo, monospace", svg)
        for decorative_treatment in ("feDropShadow", 'id="grid"', "radialGradient"):
            self.assertNotIn(decorative_treatment, svg)


if __name__ == "__main__":
    unittest.main()
