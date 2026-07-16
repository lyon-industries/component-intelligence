#!/usr/bin/env python3
# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

"""Generate the PTS815 Rev A physical-qualification coupon in KiCad 10."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew


COMPONENT = Path(__file__).resolve().parent
FOOTPRINT_LIBRARY = COMPONENT / "PTS815SJM250SMTRLFS.pretty"
OUTPUT = COMPONENT / "qualification/coupon-rev-a/pts815-coupon-rev-a.kicad_pcb"
STYLE_PATH = COMPONENT.parents[2] / "quality/pcb-render-style.json"


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I_MM(x, y)


def add_text(
    board: pcbnew.BOARD,
    value: str,
    x: float,
    y: float,
    *,
    size: float = 1.0,
) -> None:
    text = pcbnew.PCB_TEXT(board)
    text.SetText(value)
    text.SetPosition(point(x, y))
    text.SetLayer(pcbnew.F_SilkS)
    text.SetTextSize(point(size, size))
    text.SetTextThickness(mm(0.15))
    board.Add(text)


def add_testpoint(
    board: pcbnew.BOARD,
    reference: str,
    terminal: str,
    x: float,
    y: float,
    net: pcbnew.NETINFO_ITEM,
) -> pcbnew.PAD:
    footprint = pcbnew.FOOTPRINT(board)
    footprint.SetReference(reference)
    footprint.SetValue(f"TERMINAL_{terminal}")
    footprint.SetAttributes(pcbnew.FP_SMD)
    footprint.Reference().SetVisible(False)
    footprint.Value().SetVisible(False)

    pad = pcbnew.PAD(footprint)
    pad.SetNumber("1")
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(point(3.0, 3.0))
    layers = pcbnew.LSET()
    layers.AddLayer(pcbnew.F_Cu)
    layers.AddLayer(pcbnew.F_Mask)
    pad.SetLayerSet(layers)
    pad.SetPosition(point(0, 0))
    pad.SetNet(net)
    footprint.Add(pad)
    footprint.SetPosition(point(x, y))
    board.Add(footprint)
    add_text(board, f"{reference} / PIN {terminal}", x, y + 2.4, size=0.8)
    return pad


def add_track(
    board: pcbnew.BOARD,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    net: pcbnew.NETINFO_ITEM,
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(end)
    track.SetWidth(mm(0.35))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(net)
    board.Add(track)


def add_edge_line(
    board: pcbnew.BOARD,
    start: tuple[float, float],
    end: tuple[float, float],
) -> None:
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
    edge.SetStart(point(*start))
    edge.SetEnd(point(*end))
    edge.SetWidth(mm(0.05))
    edge.SetLayer(pcbnew.Edge_Cuts)
    board.Add(edge)


def add_edge_arc(
    board: pcbnew.BOARD,
    start: tuple[float, float],
    midpoint: tuple[float, float],
    end: tuple[float, float],
) -> None:
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_ARC)
    edge.SetArcGeometry(point(*start), point(*midpoint), point(*end))
    edge.SetWidth(mm(0.05))
    edge.SetLayer(pcbnew.Edge_Cuts)
    board.Add(edge)


def add_rounded_outline(
    board: pcbnew.BOARD,
    width: float,
    height: float,
    radius: float,
) -> None:
    diagonal = radius / math.sqrt(2)
    for start, end in (
        ((radius, 0.0), (width - radius, 0.0)),
        ((width, radius), (width, height - radius)),
        ((width - radius, height), (radius, height)),
        ((0.0, height - radius), (0.0, radius)),
    ):
        add_edge_line(board, start, end)
    for start, midpoint, end in (
        (
            (width - radius, 0.0),
            (width - radius + diagonal, radius - diagonal),
            (width, radius),
        ),
        (
            (width, height - radius),
            (width - radius + diagonal, height - radius + diagonal),
            (width - radius, height),
        ),
        (
            (radius, height),
            (radius - diagonal, height - radius + diagonal),
            (0.0, height - radius),
        ),
        (
            (0.0, radius),
            (radius - diagonal, radius - diagonal),
            (radius, 0.0),
        ),
    ):
        add_edge_arc(board, start, midpoint, end)


def add_physical_stackup(path: Path, style: dict[str, object]) -> None:
    board_style = style["board"]
    stackup = f'''\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "{board_style["silkscreen"]["kicad_color"]}"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "{board_style["solder_mask"]["kicad_color"]}") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "core") (color "FR4 natural") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "{board_style["solder_mask"]["kicad_color"]}") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "{board_style["silkscreen"]["kicad_color"]}"))
\t\t\t(copper_finish "{board_style["surface_finish"]["kicad_name"]}")
\t\t\t(dielectric_constraints no)
\t\t)
'''
    board = path.read_text(encoding="utf-8")
    marker = "\t(setup\n"
    if board.count(marker) != 1:
        raise RuntimeError("could not find the unique KiCad setup block")
    path.write_text(board.replace(marker, marker + stackup, 1), encoding="utf-8")


def main() -> None:
    style = json.loads(STYLE_PATH.read_text(encoding="utf-8"))
    board = pcbnew.BOARD()
    title = board.GetTitleBlock()
    title.SetTitle("PTS815 physical qualification coupon")
    title.SetDate("2026-07-16")
    title.SetRevision("A")
    title.SetCompany("Lyon Industries")
    title.SetComment(0, "FOUR INDEPENDENT TERMINALS - NOT A PRODUCT PCB")

    switch = pcbnew.FootprintLoad(
        str(FOOTPRINT_LIBRARY), "PTS815SJM250SMTRLFS"
    )
    if switch is None:
        raise RuntimeError(f"KiCad could not load {FOOTPRINT_LIBRARY}")
    switch.SetReference("SW1")
    switch.SetPosition(point(15, 10))
    board.Add(switch)

    locations = {
        "1": (5.0, 5.0),
        "2": (25.0, 5.0),
        "3": (5.0, 15.0),
        "4": (25.0, 15.0),
    }
    for terminal, (x, y) in locations.items():
        net = pcbnew.NETINFO_ITEM(board, f"TERMINAL_{terminal}")
        board.Add(net)
        switch_pad = switch.FindPadByNumber(terminal)
        switch_pad.SetNet(net)
        testpoint_pad = add_testpoint(
            board, f"TP{terminal}", terminal, x, y, net
        )
        add_track(board, switch_pad.GetPosition(), testpoint_pad.GetPosition(), net)

    add_rounded_outline(board, 30.0, 20.0, style["board"]["corner_radius_mm"])

    add_text(board, "PTS815 COUPON REV A", 15, 2.0, size=1.2)
    add_text(board, "NO COPPER JOINS THE DUT TERMINALS", 15, 18.5, size=0.9)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(OUTPUT), board)
    add_physical_stackup(OUTPUT, style)
    print(f"KiCad {pcbnew.Version()}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
