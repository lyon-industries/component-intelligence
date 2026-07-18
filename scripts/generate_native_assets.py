#!/usr/bin/env python3
"""Generate native CAD from a reviewed component record.

This is maintainer tooling, not part of the consumer contract. The record owns
the reviewed pin map, pad geometry, body envelope, and source locators. This
script only serializes those facts into KiCad and STEP files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import uuid
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = uuid.UUID("d6af7d50-a67d-4cd9-b054-4596de90c39c")


def quote_path_component(value: str) -> str:
    return quote(value, safe="-._~")


def native_asset_name(value: str) -> str:
    """Return a KiCad-safe name while preserving the exact MPN in the record.

    Repository directories remain percent-encoded so exact identities with `/`
    or `,` are unambiguous. KiCad library and asset names use `_` for characters
    that the KiCad Library Convention rejects.
    """
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_.+\-]", "_", value)).strip("_")


def uid(component_id: str, key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{component_id}:{key}"))


def q(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def nominal(value: object, *, prefer: str = "typ") -> float:
    if isinstance(value, (int, float)):
        return float(value)
    assert isinstance(value, dict)
    for key in dict.fromkeys((prefer, "typ", "max", "min")):
        if key in value:
            return float(value[key])
    raise ValueError(f"no usable numeric value in {value!r}")


def pin_electrical_type(value: str) -> str:
    return {
        "input": "input",
        "output": "output",
        "bidirectional": "bidirectional",
        "power-input": "power_in",
        "power-output": "power_out",
        "ground": "power_in",
        "passive": "passive",
        "open-collector": "open_collector",
        "open-drain": "open_collector",
        "no-connect": "no_connect",
        "mechanical": "passive",
    }[value]


def reference_prefix(record: dict[str, object]) -> str:
    """Return the conventional schematic designator for the component class."""
    return {
        "capacitor": "C",
        "diode": "D",
        "inductor": "L",
        "resistor": "R",
        "switch": "SW",
        "transistor": "Q",
    }.get(record["classification"]["category"], "U")


def lead_axis(record: dict[str, object]) -> str:
    """Infer whether gull-wing terminals leave the body along x or y.

    The explicit pad rows are authoritative. Two x rows describe the usual
    SOIC/DBV left-right arrangement; two y rows describe the rotated SOT-23
    top-bottom arrangement used by the normalized footprint coordinates.
    """
    pads = record["package"]["land_pattern"]["pads"]
    unique_x = {float(pad["x_mm"]) for pad in pads}
    unique_y = {float(pad["y_mm"]) for pad in pads}
    if len(pads) == 2:
        return "x" if len(unique_x) > len(unique_y) else "y"
    return "x" if len(unique_x) <= len(unique_y) else "y"


def oriented_body_dimensions(record: dict[str, object]) -> tuple[float, float]:
    body = record["package"]["body_dimensions_mm"]
    length = nominal(body["length"])
    width = nominal(body.get("width", body.get("molded_width")))
    if record["classification"]["category"] in {"capacitor", "inductor", "resistor", "switch"}:
        return length, width
    if record["classification"]["category"] == "diode" and len(record["electrical"]["pins"]) == 2:
        return length, width
    return (width, length) if lead_axis(record) == "x" else (length, width)


def body_height(record: dict[str, object]) -> float:
    body = record["package"]["body_dimensions_mm"]
    return nominal(body.get("height", body.get("height_from_pcb")), prefer="max")


def _graphic_polyline(points: list[tuple[float, float]], *, width: float = 0.254) -> str:
    coordinates = " ".join(f"(xy {x:g} {y:g})" for x, y in points)
    return f'''\t\t\t(polyline
\t\t\t\t(pts {coordinates})
\t\t\t\t(stroke (width {width:g}) (type default))
\t\t\t\t(fill (type none))
\t\t\t)'''


def _graphic_rectangle(x1: float, y1: float, x2: float, y2: float, *, fill: str = "background") -> str:
    return f'''\t\t\t(rectangle
\t\t\t\t(start {x1:g} {y1:g})
\t\t\t\t(end {x2:g} {y2:g})
\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t(fill (type {fill}))
\t\t\t)'''


def _graphic_circle(x: float, y: float, radius: float, *, fill: str = "none") -> str:
    return f'''\t\t\t(circle
\t\t\t\t(center {x:g} {y:g})
\t\t\t\t(radius {radius:g})
\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t(fill (type {fill}))
\t\t\t)'''


def _graphic_text(value: str, x: float, y: float, *, size: float = 1.27) -> str:
    return f'''\t\t\t(text "{q(value)}"
\t\t\t\t(at {x:g} {y:g} 0)
\t\t\t\t(effects (font (size {size:g} {size:g})))
\t\t\t)'''


def _pin_block(pin: dict[str, object], x: float, y: float, angle: int, *, length: float = 2.54) -> str:
    return f'''\t\t\t(pin {pin_electrical_type(pin["electrical_type"])} line
\t\t\t\t(at {x:g} {y:g} {angle})
\t\t\t\t(length {length:g})
\t\t\t\t(name "{q(pin["name"])}" (effects (font (size 1.27 1.27))))
\t\t\t\t(number "{q(pin["number"])}" (effects (font (size 1.27 1.27))))
\t\t\t)'''


def _passive_symbol(record: dict[str, object]) -> tuple[str, str, float, float, bool]:
    category = record["classification"]["category"]
    pins = record["electrical"]["pins"]
    assert len(pins) == 2
    graphics: list[str]
    if category == "resistor":
        graphics = [_graphic_rectangle(-1.27, 1.016, 1.27, -1.016)]
    elif category == "capacitor":
        graphics = [
            _graphic_polyline([(-0.762, -2.032), (-0.762, 2.032)], width=0.508),
            _graphic_polyline([(0.762, -2.032), (0.762, 2.032)], width=0.508),
        ]
    elif category == "inductor":
        graphics = [
            '''\t\t\t(arc (start -2.54 0) (mid -1.905 -0.635) (end -1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))''',
            '''\t\t\t(arc (start -1.27 0) (mid -0.635 -0.635) (end 0 0) (stroke (width 0.254) (type default)) (fill (type none)))''',
            '''\t\t\t(arc (start 0 0) (mid 0.635 -0.635) (end 1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))''',
            '''\t\t\t(arc (start 1.27 0) (mid 1.905 -0.635) (end 2.54 0) (stroke (width 0.254) (type default)) (fill (type none)))''',
        ]
    else:  # two-terminal diode / LED
        if pins[0]["name"].upper().startswith("A"):
            graphics = [
                _graphic_polyline([(1.27, -1.27), (1.27, 1.27)], width=0.254),
                _graphic_polyline([(-1.27, -1.27), (-1.27, 1.27), (1.27, 0), (-1.27, -1.27)], width=0.254),
            ]
        else:
            graphics = [
                _graphic_polyline([(-1.27, -1.27), (-1.27, 1.27)], width=0.254),
                _graphic_polyline([(1.27, -1.27), (1.27, 1.27), (-1.27, 0), (1.27, -1.27)], width=0.254),
            ]
        if "LED" in record["classification"]["function"].upper() or "LED" in record["classification"]["keywords"]:
            graphics.extend([
                _graphic_polyline([(-0.75, -1.8), (-1.75, -2.8), (-1.2, -2.8)], width=0.2),
                _graphic_polyline([(0.25, -1.8), (-0.75, -2.8), (-0.2, -2.8)], width=0.2),
            ])
    pin_blocks = "\n".join([
        _pin_block(pins[0], -5.08, 0, 0, length=2.54),
        _pin_block(pins[1], 5.08, 0, 180, length=2.54),
    ])
    return "\n".join(graphics), pin_blocks, 3.81, 2.54, True


def _switch_symbol(record: dict[str, object]) -> tuple[str, str, float, float, bool]:
    pins = record["electrical"]["pins"]
    left = pins[:2]
    right = pins[2:]
    graphics = "\n".join([
        _graphic_polyline([(-5.08, 2.54), (-5.08, -2.54)]),
        _graphic_polyline([(-5.08, 0), (-1.524, 0)]),
        _graphic_circle(-1.27, 0, 0.254),
        _graphic_polyline([(-1.016, 0.254), (0.889, 1.524)], width=0.381),
        _graphic_circle(1.27, 0, 0.254),
        _graphic_polyline([(1.524, 0), (5.08, 0)]),
        _graphic_polyline([(5.08, 2.54), (5.08, -2.54)]),
    ])
    blocks = []
    for pin, y in zip(left, (2.54, -2.54)):
        blocks.append(_pin_block(pin, -7.62, y, 0))
    for pin, y in zip(right, (2.54, -2.54)):
        blocks.append(_pin_block(pin, 7.62, y, 180))
    return graphics, "\n".join(blocks), 6.35, 3.81, False


def _functional_symbol(record: dict[str, object]) -> tuple[str, str, float, float, bool]:
    pins = record["electrical"]["pins"]
    top = [pin for pin in pins if pin["electrical_type"] == "power-input" and pin["name"].upper() not in {"GND", "VSS", "VSSA", "V-"}]
    bottom = [pin for pin in pins if pin["electrical_type"] == "ground" or pin["name"].upper() in {"GND", "VSS", "VSSA", "V-"}]
    right = [pin for pin in pins if pin["electrical_type"] in {"output", "power-output", "open-collector", "open-drain"}]
    assigned = {id(pin) for pin in top + bottom + right}
    left = [pin for pin in pins if id(pin) not in assigned]
    rows = max(len(left), len(right), 2)
    half_height = math.ceil(max(3.81, (rows + 1) * 1.27) / 2.54) * 2.54
    half_width = math.ceil(max(5.08, (max(len(top), len(bottom), 1) + 1) * 1.27) / 2.54) * 2.54

    def side(items: list[dict[str, object]], side_name: str) -> list[str]:
        blocks = []
        if side_name in {"left", "right"}:
            start = ((len(items) - 1) // 2) * 2.54
            for index, pin in enumerate(items):
                y = start - index * 2.54
                x = -(half_width + 2.54) if side_name == "left" else half_width + 2.54
                blocks.append(_pin_block(pin, x, y, 0 if side_name == "left" else 180))
        else:
            start = -((len(items) - 1) // 2) * 2.54
            for index, pin in enumerate(items):
                x = start + index * 2.54
                y = half_height + 2.54 if side_name == "top" else -(half_height + 2.54)
                blocks.append(_pin_block(pin, x, y, 270 if side_name == "top" else 90))
        return blocks

    label = {
        "logic": "LOGIC",
        "amplifier": "OP AMP",
        "comparator": "COMP",
        "microcontroller": "MCU",
        "current-sensor": "CURRENT / POWER",
    }.get(record["classification"]["category"], record["classification"]["category"].replace("-", " ").upper())
    graphics = "\n".join([
        _graphic_rectangle(-half_width, half_height, half_width, -half_height),
        _graphic_text(label, 0, 0, size=1.016),
    ])
    blocks = side(left, "left") + side(right, "right") + side(top, "top") + side(bottom, "bottom")
    return graphics, "\n".join(blocks), half_width, half_height, False


def symbol_text(record: dict[str, object]) -> str:
    identity = record["identity"]
    pins = record["electrical"]["pins"]
    source_url = record["sources"][0]["url"]
    mpn = identity["mpn"]
    library_name = native_asset_name(mpn)
    reference = reference_prefix(record)
    category = record["classification"]["category"]
    if len(pins) == 2 and category in {"capacitor", "diode", "inductor", "resistor"}:
        graphics, pin_blocks, half_width, half_height, hide_pin_names = _passive_symbol(record)
    elif category == "switch":
        graphics, pin_blocks, half_width, half_height, hide_pin_names = _switch_symbol(record)
    else:
        graphics, pin_blocks, half_width, half_height, hide_pin_names = _functional_symbol(record)
    pin_names = "\t\t(pin_names (offset 0) (hide yes))" if hide_pin_names else "\t\t(pin_names (offset 0.508))"
    keywords = " ".join(record["classification"]["keywords"])
    footprint_filter = library_name.replace("_", "?").replace("-", "?")
    return f'''(kicad_symbol_lib
\t(version 20251024)
\t(generator "component-intelligence")
\t(generator_version "2.0")
\t(symbol "{q(library_name)}"
{pin_names}
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(duplicate_pin_numbers_are_jumpers no)
\t\t(property "Reference" "{reference}" (at 0 {half_height + 1.27:g} 0) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "{q(mpn)}" (at 0 {-half_height - 1.27:g} 0) (show_name no) (do_not_autoplace no) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "{q(library_name)}:{q(library_name)}" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Datasheet" "{q(source_url)}" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Description" "{q(record["classification"]["function"])}" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "ki_keywords" "{q(keywords)}" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "ki_fp_filters" "{q(footprint_filter)}:*" (at 0 0 0) (show_name no) (do_not_autoplace no) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(symbol "{q(library_name)}_0_1"
{graphics}
\t\t)
\t\t(symbol "{q(library_name)}_1_1"
{pin_blocks}
\t\t)
\t\t(embedded_fonts no)
\t)
)\n'''


def footprint_text(record: dict[str, object], area: str) -> str:
    identity = record["identity"]
    component_id = record["id"]
    mpn = identity["mpn"]
    library_name = native_asset_name(mpn)
    land = record["package"]["land_pattern"]
    body_x, body_y = oriented_body_dimensions(record)
    pad_x = max(abs(float(pad["x_mm"])) + float(pad["width_mm"]) / 2 for pad in land["pads"])
    pad_y = max(abs(float(pad["y_mm"])) + float(pad["height_mm"]) / 2 for pad in land["pads"])
    def round_out(value: float) -> float:
        return math.ceil((value - 1e-9) / 0.05) * 0.05

    court_x = round_out(max(body_x / 2, pad_x) + 0.5)
    court_y = round_out(max(body_y / 2, pad_y) + 0.5)
    fab_x = body_x / 2
    fab_y = body_y / 2
    source_url = record["sources"][0]["url"]

    def line(x1: float, y1: float, x2: float, y2: float, layer: str, width: float, key: str) -> str:
        return f'''\t(fp_line (start {x1:g} {y1:g}) (end {x2:g} {y2:g}) (stroke (width {width:g}) (type default)) (layer "{layer}") (uuid "{uid(component_id, key)}"))'''

    lines = [
        line(-court_x, -court_y, court_x, -court_y, "F.CrtYd", 0.05, "court-top"),
        line(court_x, -court_y, court_x, court_y, "F.CrtYd", 0.05, "court-right"),
        line(court_x, court_y, -court_x, court_y, "F.CrtYd", 0.05, "court-bottom"),
        line(-court_x, court_y, -court_x, -court_y, "F.CrtYd", 0.05, "court-left"),
        line(-fab_x + 0.5, -fab_y, fab_x, -fab_y, "F.Fab", 0.1, "fab-top"),
        line(fab_x, -fab_y, fab_x, fab_y, "F.Fab", 0.1, "fab-right"),
        line(fab_x, fab_y, -fab_x, fab_y, "F.Fab", 0.1, "fab-bottom"),
        line(-fab_x, fab_y, -fab_x, -fab_y + 0.5, "F.Fab", 0.1, "fab-left"),
        line(-fab_x, -fab_y + 0.5, -fab_x + 0.5, -fab_y, "F.Fab", 0.1, "fab-pin1"),
    ]
    if lead_axis(record) == "x":
        pad_edge_y = max(abs(float(pad["y_mm"])) + float(pad["height_mm"]) / 2 for pad in land["pads"])
        silk_y = max(fab_y + 0.12, pad_edge_y + 0.27)
        lines.extend([
            line(-fab_x + 0.35, -silk_y, fab_x - 0.35, -silk_y, "F.SilkS", 0.12, "silk-top"),
            line(-fab_x + 0.35, silk_y, fab_x - 0.35, silk_y, "F.SilkS", 0.12, "silk-bottom"),
        ])
    else:
        pad_edge_x = max(abs(float(pad["x_mm"])) + float(pad["width_mm"]) / 2 for pad in land["pads"])
        silk_x = max(fab_x + 0.12, pad_edge_x + 0.27)
        lines.extend([
            line(-silk_x, -fab_y + 0.35, -silk_x, fab_y - 0.35, "F.SilkS", 0.12, "silk-left"),
            line(silk_x, -fab_y + 0.35, silk_x, fab_y - 0.35, "F.SilkS", 0.12, "silk-right"),
        ])
    pads = []
    for index, pad in enumerate(land["pads"]):
        shape = "roundrect" if index else "roundrect"
        pads.append(
            f'''\t(pad "{q(pad["number"])}" smd {shape} (at {float(pad["x_mm"]):g} {float(pad["y_mm"]):g}) (size {float(pad["width_mm"]):g} {float(pad["height_mm"]):g}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (uuid "{uid(component_id, f"pad-{index}")}"))'''
        )
    pin_names = {str(pin["name"]).strip().lower() for pin in record["electrical"]["pins"]}
    needs_pin_one_marker = len(record["electrical"]["pins"]) > 2 or bool(
        pin_names & {"a", "k", "anode", "cathode", "+", "-"}
    )
    pin_one_marker = ""
    if needs_pin_one_marker:
        pad_one = land["pads"][0]
        pad_one_x = float(pad_one["x_mm"])
        pad_one_y = float(pad_one["y_mm"])
        if abs(pad_one_x) >= abs(pad_one_y):
            direction = math.copysign(1, pad_one_x or -1)
            marker_x = pad_one_x + direction * (float(pad_one["width_mm"]) / 2 + 0.34)
            marker_y = pad_one_y
        else:
            direction = math.copysign(1, pad_one_y or -1)
            marker_x = pad_one_x
            marker_y = pad_one_y + direction * (float(pad_one["height_mm"]) / 2 + 0.34)
        pin_one_marker = f'''\t(fp_circle (center {marker_x:g} {marker_y:g}) (end {marker_x + 0.06:g} {marker_y:g}) (stroke (width 0.12) (type default)) (fill yes) (layer "F.SilkS") (uuid "{uid(component_id, "silk-pin1")}"))'''
    directory_name = quote_path_component(identity["mpn"])
    model_path = f'${{COMPONENT_INTELLIGENCE_ROOT}}/{area}/{identity["manufacturer_slug"]}/{directory_name}/{record["cad"]["step_model"]["path"]}'
    return f'''(footprint "{q(library_name)}"
\t(version 20260206)
\t(generator "component-intelligence")
\t(generator_version "2.0")
\t(layer "F.Cu")
\t(descr "{q(identity["manufacturer"])} {q(mpn)}, source-dimensioned {q(record["package"]["name"])} footprint; {q(source_url)}")
\t(tags "{q(record["package"]["name"].replace(',', ' '))} {q(library_name)}")
\t(property "Reference" "REF**" (at 0 {-court_y - 1:g} 0) (layer "F.SilkS") (uuid "{uid(component_id, "reference")}") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "{q(library_name)}" (at 0 {court_y + 1:g} 0) (layer "F.Fab") (uuid "{uid(component_id, "value")}") (effects (font (size 1 1) (thickness 0.15))))
\t(attr smd)
{chr(10).join(lines)}
{pin_one_marker}
\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{uid(component_id, "fab-reference")}") (effects (font (size 0.5 0.5) (thickness 0.08))))
{chr(10).join(pads)}
\t(model "{q(model_path)}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
\t(embedded_fonts no)
)\n'''


def write_step(record: dict[str, object], target: Path) -> None:
    try:
        import cadquery as cq
    except ImportError as exc:
        raise SystemExit("STEP generation requires CadQuery 2.8 or newer") from exc

    body = record["package"]["body_dimensions_mm"]
    body_x, body_y = oriented_body_dimensions(record)
    body_z = body_height(record)
    category = record["classification"]["category"]
    if len(record["electrical"]["pins"]) == 2 and category in {"capacitor", "diode", "inductor", "resistor"}:
        end_cap = min(body_x * 0.22, 0.35)
        body_shape = cq.Workplane("XY").box(body_x - 2 * end_cap, body_y, body_z).translate((0, 0, body_z / 2))
        solids = [body_shape.val()]
        for sign in (-1, 1):
            terminal = cq.Workplane("XY").box(end_cap, body_y, min(body_z, 0.25)).translate(
                (sign * (body_x - end_cap) / 2, 0, min(body_z, 0.25) / 2)
            )
            solids.append(terminal.val())
        target.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(cq.Compound.makeCompound(solids), str(target), exportType="STEP")
        _normalize_step_text(record, target)
        return
    standoff = min(0.15, body_z * 0.12)
    body_shape = cq.Workplane("XY").box(body_x, body_y, body_z - standoff).translate((0, 0, standoff + (body_z - standoff) / 2))
    marker = cq.Workplane("XY").cylinder(0.03, min(body_x, body_y) * 0.08).translate(
        (-body_x * 0.3, -body_y * 0.3, body_z - 0.03)
    )
    body_shape = body_shape.cut(marker)
    solids = [body_shape.val()]
    terminal_span = nominal(body.get("overall_width", body.get("width", body.get("molded_width"))))
    axis = lead_axis(record)
    for pad in record["package"]["land_pattern"]["pads"]:
        if axis == "x":
            position = float(pad["x_mm"])
            outer = terminal_span / 2
            inner = body_x * 0.45
            lead_length = max(0.2, outer - inner)
            center = (outer + inner) / 2 * (1 if position > 0 else -1)
            transverse = min(float(pad["height_mm"]) * 0.72, 0.5)
            lead = cq.Workplane("XY").box(lead_length, transverse, 0.12).translate(
                (center, float(pad["y_mm"]), 0.06)
            )
        else:
            position = float(pad["y_mm"])
            outer = terminal_span / 2
            inner = body_y * 0.45
            lead_length = max(0.2, outer - inner)
            center = (outer + inner) / 2 * (1 if position > 0 else -1)
            transverse = min(float(pad["width_mm"]) * 0.72, 0.5)
            lead = cq.Workplane("XY").box(transverse, lead_length, 0.12).translate(
                (float(pad["x_mm"]), center, 0.06)
            )
        solids.append(lead.val())
    target.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Compound.makeCompound(solids), str(target), exportType="STEP")
    _normalize_step_text(record, target)


def _normalize_step_text(record: dict[str, object], target: Path) -> None:
    step_text = target.read_text(encoding="utf-8")
    step_text = re.sub(
        r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')",
        r"\g<1>1970-01-01T00:00:00\2",
        step_text,
        count=1,
    )
    step_text = re.sub(
        r"Open CASCADE STEP translator [^']+",
        "Component Intelligence native CAD generator",
        step_text,
    )
    occurrence = iter(range(1, len(record["package"]["land_pattern"]["pads"]) + 2))
    step_text = re.sub(
        r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('[^']*'",
        lambda _: f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(occurrence)}'",
        step_text,
    )
    step_text = "\n".join(line.rstrip() for line in step_text.splitlines()) + "\n"
    target.write_text(step_text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate(component_dir: Path, area: str) -> None:
    record_path = component_dir / "component.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    old_paths = {
        name: component_dir / record["cad"][name]["path"]
        for name in ("symbol", "footprint", "step_model")
    }
    name = native_asset_name(record["identity"]["mpn"])
    record["cad"]["symbol"]["path"] = f"{name}.kicad_sym"
    record["cad"]["footprint"]["path"] = f"{name}.pretty/{name}.kicad_mod"
    record["cad"]["step_model"]["path"] = f"{name}.3dshapes/{name}.step"
    symbol = component_dir / record["cad"]["symbol"]["path"]
    footprint = component_dir / record["cad"]["footprint"]["path"]
    step = component_dir / record["cad"]["step_model"]["path"]
    symbol.parent.mkdir(parents=True, exist_ok=True)
    symbol.write_text(symbol_text(record), encoding="utf-8")
    footprint.parent.mkdir(parents=True, exist_ok=True)
    footprint.write_text(footprint_text(record, area), encoding="utf-8")
    write_step(record, step)
    record["cad"]["symbol"]["sha256"] = sha256_file(symbol)
    record["cad"]["symbol"]["tool_version"] = "Component Intelligence native CAD generator 2.0 / KiCad 10 syntax"
    record["cad"]["footprint"]["sha256"] = sha256_file(footprint)
    record["cad"]["footprint"]["tool_version"] = "Component Intelligence native CAD generator 2.0 / KiCad 10 syntax"
    record["cad"]["step_model"]["sha256"] = sha256_file(step)
    record["cad"]["step_model"]["tool_version"] = "CadQuery 2.8.0 / Open CASCADE 7.9.3"
    seen_checks: set[str] = set()
    record["verification"]["checks"] = [
        check
        for check in record["verification"]["checks"]
        if not (check["name"] in seen_checks or seen_checks.add(check["name"]))
    ]
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for old_path in old_paths.values():
        if old_path not in {symbol, footprint, step} and old_path.is_file():
            old_path.unlink()
            if old_path.parent != component_dir:
                try:
                    old_path.parent.rmdir()
                except OSError:
                    pass
    print(component_dir.relative_to(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("component_dirs", nargs="+", type=Path)
    parser.add_argument("--area", choices=("components", "candidates"), default="candidates")
    args = parser.parse_args()
    for path in args.component_dirs:
        generate(path.resolve(), args.area)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
