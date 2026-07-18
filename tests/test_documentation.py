# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
import unittest
from urllib.parse import unquote

from scripts.validate import ROOT


MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_relative_markdown_links_resolve(self) -> None:
        missing: list[str] = []
        markdown_files = [
            ROOT / "AGENTS.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "QUALITY.md",
            ROOT / "README.md",
            ROOT / "assets" / "README.md",
            *sorted((ROOT / "docs").glob("*.md")),
            *sorted((ROOT / "components").glob("*/*/README.md")),
            *sorted((ROOT / "candidates").glob("*/*/README.md")),
        ]

        for markdown_file in markdown_files:
            text = markdown_file.read_text(encoding="utf-8")
            for match in MARKDOWN_LINK.finditer(text):
                target = match.group(1).strip().strip("<>")
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                relative_target = unquote(target.split("#", 1)[0])
                resolved = markdown_file.parent / relative_target
                if not resolved.exists():
                    missing.append(
                        f"{markdown_file.relative_to(ROOT)} -> {relative_target}"
                    )

        self.assertEqual([], missing)

    def test_generated_component_graph_is_prominent_in_readme(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        graph_reference = 'src="assets/component-catalog-graph.svg"'
        self.assertIn(graph_reference, readme)
        self.assertLess(readme.index(graph_reference), readme.index("## Audited state"))
        self.assertTrue((ROOT / "assets" / "component-catalog-graph.svg").is_file())


if __name__ == "__main__":
    unittest.main()
