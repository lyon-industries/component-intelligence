#!/usr/bin/env python3
"""Generate the 16:9 complete-tier component catalog graph."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = Path("assets/component-catalog-graph.svg")
WIDTH = 1600
HEIGHT = 900
LYON_PALETTE = frozenset({"#05080B", "#0B2630", "#2A302E", "#9FB9CC", "#EA5C22", "#EAEEF0"})
PROPELLANT = "#EA5C22"
HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b")


@dataclass(frozen=True)
class Domain:
    """A maintained presentation grouping for canonical component categories."""

    key: str
    title: str
    categories: tuple[str, ...]
    box: tuple[int, int, int, int]


@dataclass(frozen=True)
class ComponentNode:
    """The graph fields read from one complete canonical record."""

    mpn: str
    category: str
    path: str


# These domains exist only to make the README graph readable. The categories
# below are the canonical values from classification.category. Keeping the map
# explicit makes a newly introduced category fail closed until it is placed
# deliberately.
DOMAINS = (
    Domain(
        "analog-measurement",
        "Analog & measurement",
        ("amplifier", "comparator", "current-sensor", "data-converter", "timer"),
        (32, 92, 500, 338),
    ),
    Domain(
        "discretes-protection",
        "Discretes & protection",
        ("diode", "protection", "transistor"),
        (32, 470, 500, 350),
    ),
    Domain(
        "power-regulation",
        "Power & regulation",
        ("battery-management", "power", "power-management"),
        (560, 92, 480, 235),
    ),
    Domain(
        "passives-electromechanical",
        "Passives & electromechanical",
        ("capacitor", "inductor", "resistor", "switch"),
        (560, 635, 480, 185),
    ),
    Domain(
        "digital-connectivity",
        "Digital & connectivity",
        ("interface", "logic", "memory", "microcontroller"),
        (1068, 92, 500, 728),
    ),
)

CATEGORY_TO_DOMAIN = {
    category: domain.key
    for domain in DOMAINS
    for category in domain.categories
}

PANEL_HEADER_HEIGHT = 55
PANEL_BOTTOM_PADDING = 12
CATEGORY_LABEL_HEIGHT = 20
CATEGORY_GAP = 9
CHIP_HEIGHT = 30
CHIP_GAP = 6
PANEL_COLUMNS = 2


def humanize(value: str) -> str:
    """Turn a canonical slug into a compact display label."""
    return value.replace("-", " ").capitalize()


def load_component_nodes(root: Path = ROOT) -> list[ComponentNode]:
    """Load exact MPNs and categories from the complete tier only."""
    nodes: list[ComponentNode] = []
    for path in sorted((root / "components").glob("*/*/component.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        nodes.append(
            ComponentNode(
                mpn=record["identity"]["mpn"],
                category=record["classification"]["category"],
                path=path.parent.relative_to(root).as_posix(),
            )
        )
    nodes.sort(key=lambda node: (node.category, node.mpn.casefold(), node.mpn))
    return nodes


def count_candidates(root: Path = ROOT) -> int:
    """Return the quarantined candidate count without exposing candidate devices."""
    return sum(1 for _ in (root / "candidates").glob("*/*/component.json"))


def validate_taxonomy(nodes: list[ComponentNode]) -> None:
    """Fail closed when graph taxonomy or identity would be ambiguous."""
    mapped_categories = [category for domain in DOMAINS for category in domain.categories]
    duplicate_categories = sorted(
        category for category in set(mapped_categories) if mapped_categories.count(category) > 1
    )
    if duplicate_categories:
        raise ValueError(
            f"categories mapped to multiple presentation domains: {duplicate_categories}"
        )

    observed = {node.category for node in nodes}
    unmapped = sorted(observed - set(CATEGORY_TO_DOMAIN))
    if unmapped:
        raise ValueError(
            "complete component categories missing from graph presentation taxonomy: "
            f"{unmapped}"
        )

    mpns = [node.mpn for node in nodes]
    duplicate_mpns = sorted(mpn for mpn in set(mpns) if mpns.count(mpn) > 1)
    if duplicate_mpns:
        raise ValueError(f"exact MPNs are not unique in complete-tier graph: {duplicate_mpns}")


def validate_visual_contract(svg: str) -> None:
    """Keep generated artwork inside the Lyon Industries visual contract."""
    colors = {match.upper() for match in HEX_COLOR.findall(svg)}
    unexpected = sorted(colors - LYON_PALETTE)
    if unexpected:
        raise ValueError(f"component graph uses colors outside the Lyon palette: {unexpected}")
    if svg.count(PROPELLANT) != 1:
        raise ValueError("component graph must contain exactly one Propellant ignition")
    disallowed = ("feDropShadow", 'id="grid"', "radialGradient")
    present = [token for token in disallowed if token in svg]
    if present:
        raise ValueError(f"component graph contains disallowed decorative treatment: {present}")


def group_height(device_count: int) -> int:
    """Return the vertical height needed by one category branch."""
    return (
        CATEGORY_LABEL_HEIGHT
        + device_count * CHIP_HEIGHT
        + max(0, device_count - 1) * CHIP_GAP
        + CATEGORY_GAP
    )


def category_columns(
    domain: Domain,
    grouped: dict[str, list[ComponentNode]],
) -> list[list[tuple[str, list[ComponentNode]]]]:
    """Balance category branches across two readable panel columns."""
    categories = [
        (category, grouped.get(category, []))
        for category in domain.categories
        if grouped.get(category)
    ]
    categories.sort(key=lambda item: (-group_height(len(item[1])), item[0]))
    columns: list[list[tuple[str, list[ComponentNode]]]] = [
        [] for _ in range(PANEL_COLUMNS)
    ]
    heights = [0] * PANEL_COLUMNS
    for category, devices in categories:
        column_index = min(range(PANEL_COLUMNS), key=lambda index: (heights[index], index))
        columns[column_index].append((category, devices))
        heights[column_index] += group_height(len(devices))

    available_height = domain.box[3] - PANEL_HEADER_HEIGHT - PANEL_BOTTOM_PADDING
    required_height = max(heights, default=0)
    if required_height > available_height:
        raise ValueError(
            f"component graph capacity exceeded for {domain.title}: "
            f"needs {required_height}px, has {available_height}px; "
            "increase the panel or revise the 16:9 layout without truncating devices"
        )
    return columns


def render_device_node(
    node: ComponentNode,
    category: str,
    x: float,
    y: float,
    width: float,
) -> list[str]:
    """Render one typed exact-MPN device node."""
    label_width = max(1.0, width - 24)
    font_size = min(16.0, label_width / max(1.0, len(node.mpn) * 0.61))
    if font_size < 12.0:
        raise ValueError(
            f"exact MPN {node.mpn!r} cannot fit the component graph without text below 12px"
        )
    font_size = round(font_size, 2)
    return [
        (
            f'<g data-node-kind="device" data-mpn="{escape(node.mpn, quote=True)}" '
            f'data-category="{escape(category, quote=True)}" '
            f'data-record-path="{escape(node.path, quote=True)}">'
        ),
        f'<circle cx="{x + 2:.1f}" cy="{y + 15:.1f}" r="1.75" fill="#9FB9CC" opacity="0.72"/>',
        (
            f'<text x="{x + 12:.1f}" y="{y + 20.5:.1f}" class="mpn" '
            f'font-size="{font_size}">{escape(node.mpn)}</text>'
        ),
        "</g>",
    ]


def render_domain_panel(
    domain: Domain,
    grouped: dict[str, list[ComponentNode]],
) -> list[str]:
    """Render a domain, its canonical categories, and all exact-MPN nodes."""
    x, y, width, height = domain.box
    device_count = sum(len(grouped.get(category, [])) for category in domain.categories)
    columns = category_columns(domain, grouped)
    inner_padding = 0
    column_gap = 24
    column_width = (width - 2 * inner_padding - column_gap) / PANEL_COLUMNS
    lines = [
        (
            f'<g data-node-kind="domain" data-domain="{domain.key}" '
            f'data-device-count="{device_count}">'
        ),
        (
            f'<line x1="{x}" y1="{y}" x2="{x + width}" y2="{y}" '
            'stroke="#9FB9CC" stroke-opacity="0.28" stroke-width="1"/>'
        ),
        (
            f'<text x="{x}" y="{y + 31}" class="domain-title">'
            f'{escape(domain.title)}</text>'
        ),
        (
            f'<text x="{x + width}" y="{y + 29}" class="domain-count" '
            f'text-anchor="end">{device_count:02d} DEVICES</text>'
        ),
        (
            f'<line x1="{x}" y1="{y + 44}" x2="{x + width}" y2="{y + 44}" '
            'stroke="#9FB9CC" stroke-opacity="0.12" stroke-width="1"/>'
        ),
    ]

    for column_index, categories in enumerate(columns):
        group_x = x + inner_padding + column_index * (column_width + column_gap)
        group_y = y + PANEL_HEADER_HEIGHT
        for category, devices in categories:
            category_y = group_y
            branch_x = group_x + 5
            chip_x = group_x + 18
            chip_width = column_width - 18
            last_device_center = (
                category_y
                + CATEGORY_LABEL_HEIGHT
                + (len(devices) - 1) * (CHIP_HEIGHT + CHIP_GAP)
                + CHIP_HEIGHT / 2
            )
            lines.extend(
                [
                    (
                        '<g data-node-kind="category" '
                        f'data-category="{escape(category, quote=True)}" '
                        f'data-device-count="{len(devices)}">'
                    ),
                    (
                        f'<rect x="{branch_x - 1.5:.1f}" y="{category_y + 6.5:.1f}" '
                        'width="3" height="3" fill="#9FB9CC" opacity="0.82"/>'
                    ),
                    (
                        f'<text x="{group_x + 16:.1f}" y="{category_y + 13:.1f}" '
                        f'class="category">{escape(humanize(category).upper())}</text>'
                    ),
                    (
                        f'<text x="{group_x + column_width:.1f}" y="{category_y + 13:.1f}" '
                        f'class="category-count" text-anchor="end">{len(devices):02d}</text>'
                    ),
                    (
                        f'<line x1="{branch_x:.1f}" y1="{category_y + 13:.1f}" '
                        f'x2="{branch_x:.1f}" y2="{last_device_center:.1f}" '
                        'stroke="#9FB9CC" stroke-opacity="0.24" stroke-width="1"/>'
                    ),
                ]
            )
            for device_index, node in enumerate(devices):
                chip_y = (
                    category_y
                    + CATEGORY_LABEL_HEIGHT
                    + device_index * (CHIP_HEIGHT + CHIP_GAP)
                )
                chip_center = chip_y + CHIP_HEIGHT / 2
                lines.append(
                    f'<line x1="{branch_x:.1f}" y1="{chip_center:.1f}" '
                    f'x2="{chip_x:.1f}" y2="{chip_center:.1f}" '
                    'stroke="#9FB9CC" stroke-opacity="0.24" stroke-width="1"/>'
                )
                lines.extend(render_device_node(node, category, chip_x, chip_y, chip_width))
            lines.append("</g>")
            group_y += group_height(len(devices))

    lines.append("</g>")
    return lines


def render_repository_node(complete_count: int, candidate_count: int) -> list[str]:
    """Render the central repository node."""
    x, y, width, height = 600, 352, 400, 250
    candidate_label = "CANDIDATE" if candidate_count == 1 else "CANDIDATES"
    return [
        '<g data-node-kind="repository" data-repository="component-intelligence">',
        (
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
            'fill="#0B2630" fill-opacity="0.94" stroke="#9FB9CC" '
            'stroke-opacity="0.34" stroke-width="1"/>'
        ),
        f'<rect x="{x}" y="{y}" width="64" height="3" fill="#EA5C22"/>',
        f'<text x="{x + 32}" y="{y + 36}" class="repo-label">REPOSITORY / COMPLETE TIER</text>',
        f'<text x="{x + 32}" y="{y + 78}" class="repo-name">component-intelligence</text>',
        (
            f'<text x="{x + 32}" y="{y + 113}" class="repo-count">'
            f'{complete_count} exact-MPN packages</text>'
        ),
        (
            f'<line x1="{x + 32}" y1="{y + 132}" x2="{x + width - 32}" y2="{y + 132}" '
            'stroke="#9FB9CC" stroke-opacity="0.18" stroke-width="1"/>'
        ),
        f'<text x="{x + 32}" y="{y + 159}" class="repo-detail">SOURCE / component.json</text>',
        (
            f'<text x="{x + 32}" y="{y + 184}" class="repo-detail">'
            'EDA / KiCad 10 symbol + footprint</text>'
        ),
        (
            f'<text x="{x + 32}" y="{y + 209}" class="repo-detail">'
            'MECHANICAL / nominal STEP envelope</text>'
        ),
        (
            f'<text x="{x + 32}" y="{y + 235}" class="candidate-note">'
            f'{candidate_count:02d} {candidate_label} / STAGED OUTSIDE GRAPH</text>'
        ),
        "</g>",
    ]


def render_spokes() -> list[str]:
    """Render repository-to-domain edges behind the graph nodes."""
    paths = (
        "M 600 430 H 552 V 261 H 532",
        "M 600 525 H 552 V 645 H 532",
        "M 800 352 V 327",
        "M 800 602 V 635",
        "M 1000 477 H 1036 V 456 H 1068",
    )
    lines = ['<g aria-hidden="true">']
    for path in paths:
        lines.append(
            f'<path d="{path}" fill="none" stroke="#9FB9CC" stroke-opacity="0.32" '
            'stroke-width="1"/>'
        )
    lines.append("</g>")
    return lines


def render_component_graph(root: Path = ROOT) -> str:
    """Render the deterministic 1600×900 complete-tier SVG graph."""
    nodes = load_component_nodes(root)
    validate_taxonomy(nodes)
    grouped: dict[str, list[ComponentNode]] = {}
    for node in nodes:
        grouped.setdefault(node.category, []).append(node)
    candidate_count = count_candidates(root)
    observed_categories = len(grouped)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="graph-title graph-desc">'
        ),
        '<title id="graph-title">Component Intelligence complete catalog graph</title>',
        (
            '<desc id="graph-desc">The repository connects to five maintained '
            f'presentation domains, {observed_categories} canonical categories, '
            f'and all {len(nodes)} complete exact-MPN component packages. '
            'Candidate devices are staged separately and are not shown as component nodes.</desc>'
        ),
        "<defs>",
        '<linearGradient id="background" x1="0" y1="1" x2="1" y2="0">',
        '<stop offset="0" stop-color="#05080B"/>',
        '<stop offset="0.62" stop-color="#05080B"/>',
        '<stop offset="1" stop-color="#0B2630"/>',
        "</linearGradient>",
        '<filter id="grain" x="0" y="0" width="100%" height="100%">',
        (
            '<feTurbulence type="fractalNoise" baseFrequency="0.86" '
            'numOctaves="2" seed="17" stitchTiles="stitch"/>'
        ),
        '<feColorMatrix type="saturate" values="0"/>',
        "</filter>",
        "<style>",
        (
            "text { font-family: 'Helvetica Neue', Arial, system-ui, sans-serif; "
            "font-weight: 400; fill: #EAEEF0; }"
        ),
        (
            ".header-label, .header-meta, .domain-count, .category, "
            ".category-count, .repo-label, .repo-detail, .candidate-note, .footer { "
            "font-family: ui-monospace, 'SF Mono', Menlo, monospace; "
            "font-variant-numeric: tabular-nums; }"
        ),
        (
            ".header-label { font-size: 11px; font-weight: 500; "
            "letter-spacing: 1.5px; fill: #9FB9CC; }"
        ),
        ".headline { font-size: 37px; font-weight: 400; letter-spacing: -0.5px; }",
        (
            ".header-meta { font-size: 10px; font-weight: 500; "
            "letter-spacing: 1.1px; fill: #9FB9CC; }"
        ),
        ".domain-title { font-size: 20px; font-weight: 500; }",
        (
            ".domain-count { font-size: 11px; font-weight: 500; "
            "letter-spacing: 1px; fill: #9FB9CC; }"
        ),
        (
            ".category { font-size: 11px; font-weight: 500; "
            "letter-spacing: 1.2px; fill: #9FB9CC; }"
        ),
        (
            ".category-count { font-size: 11px; font-weight: 500; "
            "letter-spacing: 0.8px; fill: #9FB9CC; }"
        ),
        (
            ".mpn { font-family: ui-monospace, 'SF Mono', Menlo, monospace; "
            "font-weight: 400; fill: #EAEEF0; }"
        ),
        (
            ".repo-label { font-size: 11px; font-weight: 500; "
            "letter-spacing: 1.3px; fill: #9FB9CC; }"
        ),
        ".repo-name { font-size: 29px; font-weight: 400; letter-spacing: -0.35px; }",
        ".repo-count { font-size: 18px; font-weight: 400; fill: #EAEEF0; }",
        (
            ".repo-detail { font-size: 10px; font-weight: 500; "
            "letter-spacing: 0.7px; fill: #9FB9CC; }"
        ),
        (
            ".candidate-note { font-size: 10px; font-weight: 500; "
            "letter-spacing: 0.8px; fill: #9FB9CC; }"
        ),
        ".footer { font-size: 10px; font-weight: 500; letter-spacing: 1px; fill: #9FB9CC; }",
        "</style>",
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#background)"/>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" filter="url(#grain)" opacity="0.045"/>',
        '<text x="32" y="27" class="header-label">CATALOG MAP / COMPLETE TIER</text>',
        (
            '<text x="32" y="66" class="headline">Component Intelligence</text>'
        ),
        (
            '<text x="1568" y="22" class="header-meta" text-anchor="end">'
            'SOURCE / components/*/*/component.json</text>'
        ),
        (
            '<text x="1568" y="42" class="header-meta" text-anchor="end">'
            'VIEW / REPOSITORY · DOMAIN · CATEGORY · EXACT MPN</text>'
        ),
        (
            f'<text x="1568" y="62" class="header-meta" text-anchor="end">'
            f'STATE / {len(nodes):02d} COMPLETE · {candidate_count:02d} CANDIDATES STAGED</text>'
        ),
    ]
    lines.extend(render_spokes())
    for domain in DOMAINS:
        lines.extend(render_domain_panel(domain, grouped))
    lines.extend(render_repository_node(len(nodes), candidate_count))
    lines.extend(
        [
            (
                '<line x1="32" y1="852" x2="1568" y2="852" stroke="#9FB9CC" '
                'stroke-opacity="0.18" stroke-width="1"/>'
            ),
            (
                '<text x="32" y="878" class="footer">TRUST BOUNDARY / '
                'CANDIDATE DEVICES EXCLUDED</text>'
            ),
            (
                '<text x="1568" y="878" class="footer" text-anchor="end">'
                'GENERATED FILE / scripts/build_catalog.py</text>'
            ),
            "</svg>",
            "",
        ]
    )
    svg = "\n".join(lines)
    validate_visual_contract(svg)
    return svg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when the graph is stale")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / OUTPUT_PATH,
        help="output SVG path (default: assets/component-catalog-graph.svg)",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    expected = render_component_graph(ROOT)
    current = output.read_text(encoding="utf-8") if output.is_file() else None
    if args.check:
        if current != expected:
            print(f"component catalog graph is stale: {output}")
            return 1
        print(f"PASS current component catalog graph: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(f"WROTE component catalog graph: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
