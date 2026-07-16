#!/usr/bin/env python3
"""Generate native CAD from a reviewed component record.

This is maintainer tooling, not part of the consumer contract. The record owns
the reviewed pin map, pad geometry, body envelope, and source locators. This
script only serializes those facts into KiCad and STEP files.
"""

from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = uuid.UUID("d6af7d50-a67d-4cd9-b054-4596de90c39c")


def quote_path_component(value: str) -> str:
    return quote(value, safe="-._~")


def uid(component_id: str, key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{component_id}:{key}"))


def q(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def nominal(value: object, *, prefer: str = "typ") -> float:
    if isinstance(value, (int, float)):
        return float(value)
    assert isinstance(value, dict)
    for key in (prefer, "max", "min"):
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


def symbol_text(record: dict[str, object]) -> str:
    identity = record["identity"]
    pins = record["electrical"]["pins"]
    source_url = record["sources"][0]["url"]
    mpn = identity["mpn"]
    library_name = quote_path_component(mpn)
    left = [pin for pin in pins if pin["electrical_type"] not in {"output", "power-output", "open-collector", "open-drain"}]
    right = [pin for pin in pins if pin not in left]
    rows = max(len(left), len(right), 2)
    half_height = (rows + 1) * 1.27
    half_width = 5.08

    def positions(items: list[dict[str, object]], side: str) -> list[str]:
        result = []
        top = (len(items) - 1) * 1.27
        for index, pin in enumerate(items):
            y = top - index * 2.54
            x = -7.62 if side == "left" else 7.62
            angle = 0 if side == "left" else 180
            result.append(
                f'''\t\t\t(pin {pin_electrical_type(pin["electrical_type"])} line
\t\t\t\t(at {x:g} {y:g} {angle})
\t\t\t\t(length 2.54)
\t\t\t\t(name "{q(pin["name"])}" (effects (font (size 1.016 1.016))))
\t\t\t\t(number "{q(pin["number"])}" (effects (font (size 1.016 1.016))))
\t\t\t)'''
            )
        return result

    pin_blocks = "\n".join(positions(left, "left") + positions(right, "right"))
    return f'''(kicad_symbol_lib
\t(version 20231120)
\t(generator "component-intelligence")
\t(symbol "{q(library_name)}"
\t\t(pin_names (offset 1.016))
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(property "Reference" "U" (at 0 {half_height + 1.27:g} 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "{q(mpn)}" (at 0 {half_height:g} 0) (effects (font (size 1.016 1.016))))
\t\t(property "Footprint" "{q(library_name)}:{q(library_name)}" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Datasheet" "{q(source_url)}" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(property "Description" "{q(record["classification"]["function"])}" (at 0 0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(symbol "{q(library_name)}_0_1"
\t\t\t(rectangle (start {-half_width:g} {half_height:g}) (end {half_width:g} {-half_height:g}) (stroke (width 0.254) (type default)) (fill (type background)))
\t\t)
\t\t(symbol "{q(library_name)}_1_1"
{pin_blocks}
\t\t)
\t)
)\n'''


def footprint_text(record: dict[str, object], area: str) -> str:
    identity = record["identity"]
    component_id = record["id"]
    mpn = identity["mpn"]
    library_name = quote_path_component(mpn)
    land = record["package"]["land_pattern"]
    body = record["package"]["body_dimensions_mm"]
    body_x = nominal(body.get("width", body.get("molded_width")))
    body_y = nominal(body["length"])
    pad_x = max(abs(float(pad["x_mm"])) + float(pad["width_mm"]) / 2 for pad in land["pads"])
    pad_y = max(abs(float(pad["y_mm"])) + float(pad["height_mm"]) / 2 for pad in land["pads"])
    court_x = max(body_x / 2, pad_x) + 0.25
    court_y = max(body_y / 2, pad_y) + 0.25
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
        line(-fab_x, -fab_y - 0.15, fab_x, -fab_y - 0.15, "F.SilkS", 0.15, "silk-top"),
        line(-fab_x, fab_y + 0.15, fab_x, fab_y + 0.15, "F.SilkS", 0.15, "silk-bottom"),
    ]
    pads = []
    for index, pad in enumerate(land["pads"]):
        shape = "roundrect" if index else "roundrect"
        pads.append(
            f'''\t(pad "{q(pad["number"])}" smd {shape} (at {float(pad["x_mm"]):g} {float(pad["y_mm"]):g}) (size {float(pad["width_mm"]):g} {float(pad["height_mm"]):g}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (uuid "{uid(component_id, f"pad-{index}")}"))'''
        )
    directory_name = quote_path_component(identity["mpn"])
    model_path = f'${{COMPONENT_INTELLIGENCE_ROOT}}/{area}/{identity["manufacturer_slug"]}/{directory_name}/{record["cad"]["step_model"]["path"]}'
    return f'''(footprint "{q(library_name)}"
\t(version 20240108)
\t(generator "component-intelligence")
\t(layer "F.Cu")
\t(descr "{q(identity["manufacturer"])} {q(mpn)}, source-dimensioned {q(record["package"]["name"])} footprint")
\t(tags "{q(record["package"]["name"])} {q(mpn)}")
\t(property "Reference" "U**" (at 0 {-court_y - 1:g} 0) (layer "F.SilkS") (uuid "{uid(component_id, "reference")}") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "{q(mpn)}" (at 0 {court_y + 1:g} 0) (layer "F.Fab") (hide yes) (uuid "{uid(component_id, "value")}") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Datasheet" "{q(source_url)}" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{uid(component_id, "datasheet")}") (effects (font (size 1.27 1.27))))
\t(attr smd)
{chr(10).join(lines)}
{chr(10).join(pads)}
\t(model "{q(model_path)}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))
)\n'''


def write_step(record: dict[str, object], target: Path) -> None:
    try:
        import cadquery as cq
    except ImportError as exc:
        raise SystemExit("STEP generation requires CadQuery 2.8 or newer") from exc

    body = record["package"]["body_dimensions_mm"]
    body_x = nominal(body.get("width", body.get("molded_width")))
    body_y = nominal(body["length"])
    body_z = nominal(body["height"], prefer="max")
    standoff = min(0.15, body_z * 0.12)
    body_shape = cq.Workplane("XY").box(body_x, body_y, body_z - standoff).translate((0, 0, standoff + (body_z - standoff) / 2))
    marker = cq.Workplane("XY").cylinder(0.03, min(body_x, body_y) * 0.08).translate(
        (-body_x * 0.3, -body_y * 0.3, body_z - 0.03)
    )
    body_shape = body_shape.cut(marker)
    solids = [body_shape.val()]
    overall_x = nominal(body.get("overall_width", body.get("width", body.get("molded_width"))))
    for pad in record["package"]["land_pattern"]["pads"]:
        pad_position_x = float(pad["x_mm"])
        outer_x = overall_x / 2
        inner_x = body_x * 0.45
        lead_x = max(0.2, outer_x - inner_x)
        lead_center_x = 0.0 if pad_position_x == 0 else (outer_x + inner_x) / 2 * (1 if pad_position_x > 0 else -1)
        lead_y = min(float(pad["height_mm"]) * 0.72, 0.5)
        solids.append(
            cq.Workplane("XY")
            .box(lead_x, lead_y, 0.12)
            .translate((lead_center_x, float(pad["y_mm"]), 0.06))
            .val()
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Compound.makeCompound(solids), str(target), exportType="STEP")
    step_text = target.read_text(encoding="utf-8")
    step_text = re.sub(
        r"(FILE_NAME\('Open CASCADE Shape Model',')[^']+(')",
        r"\g<1>1970-01-01T00:00:00\2",
        step_text,
        count=1,
    )
    step_text = "\n".join(line.rstrip() for line in step_text.splitlines()) + "\n"
    target.write_text(step_text, encoding="utf-8")


def generate(component_dir: Path, area: str) -> None:
    record_path = component_dir / "component.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    symbol = component_dir / record["cad"]["symbol"]["path"]
    footprint = component_dir / record["cad"]["footprint"]["path"]
    step = component_dir / record["cad"]["step_model"]["path"]
    symbol.write_text(symbol_text(record), encoding="utf-8")
    footprint.parent.mkdir(parents=True, exist_ok=True)
    footprint.write_text(footprint_text(record, area), encoding="utf-8")
    write_step(record, step)
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
