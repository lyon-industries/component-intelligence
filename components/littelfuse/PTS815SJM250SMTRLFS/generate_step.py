#!/usr/bin/env python3
# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

"""Generate the original mechanical-clearance STEP model for the PTS815 switch.

Run with CadQuery 2.8.0. The model uses nominal dimensions from page 1 of the
Littelfuse/C&K PTS815 datasheet. It deliberately represents the clearance
envelope and terminal locations, not undocumented cosmetic detail.
"""

from __future__ import annotations

import re
from pathlib import Path

import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box


OUTPUT = Path(__file__).with_name("PTS815SJM250SMTRLFS.3dshapes") / (
    "PTS815SJM250SMTRLFS.step"
)
MODEL_REVISION_TIMESTAMP = "2026-07-16T00:00:00"


def centred_box(length: float, width: float, height: float, z: float) -> cq.Workplane:
    return cq.Workplane("XY").box(length, width, height).translate((0, 0, z))


def build_model() -> cq.Compound:
    # The body top excluding the actuator is dimensioned at 2.2 mm. The exact
    # order code has 2.5 mm overall height and a 0.20 +/- 0.10 mm travel.
    body = centred_box(4.2, 3.2, 2.05, 1.175).edges("|Z").fillet(0.10)
    cover = centred_box(3.0, 2.2, 0.15, 2.125).edges("|Z").fillet(0.08)
    actuator = (
        cq.Workplane("XY")
        .circle(1.55 / 2)
        .extrude(0.30)
        .translate((0, 0, 2.20))
    )

    # Four 0.55 mm-wide J terminals. The 4.6 mm package span and 2.15 mm
    # terminal-row spacing are source dimensions; the thin boxes are a
    # conservative seating representation for board/enclosure interference.
    terminals = []
    for x in (-2.15, 2.15):
        for y in (-1.075, 1.075):
            terminals.append(centred_box(0.30, 0.55, 0.15, 0.075).val())
            terminals[-1] = terminals[-1].moved(cq.Location(cq.Vector(x, y, 0)))

    return cq.Compound.makeCompound(
        [body.val(), cover.val(), actuator.val(), *terminals]
    )


def bounds_mm(shape: cq.Compound) -> tuple[float, float, float, float, float, float]:
    box = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, box)
    return tuple(round(value, 6) for value in box.Get())


def main() -> None:
    model = build_model()
    bounds = bounds_mm(model)
    expected = (-2.3, -1.6, 0.0, 2.3, 1.6, 2.5)
    if any(abs(actual - wanted) > 1e-5 for actual, wanted in zip(bounds, expected)):
        raise RuntimeError(f"unexpected model bounds {bounds}; expected {expected}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(OUTPUT), exportType="STEP")

    # Open CASCADE inserts the wall-clock time into FILE_NAME. Normalize that
    # one metadata field so identical geometry produces identical bytes.
    step_text = OUTPUT.read_text(encoding="utf-8")
    step_text, replacements = re.subn(
        r"(FILE_NAME\('Open CASCADE Shape Model',)'[^']+'",
        rf"\1'{MODEL_REVISION_TIMESTAMP}'",
        step_text,
        count=1,
    )
    if replacements != 1:
        raise RuntimeError("could not normalize STEP FILE_NAME timestamp")
    step_text = "\n".join(line.rstrip() for line in step_text.splitlines()) + "\n"
    OUTPUT.write_text(step_text, encoding="utf-8")

    print(f"wrote {OUTPUT}")
    print(f"bounds mm: {bounds}")


if __name__ == "__main__":
    main()
