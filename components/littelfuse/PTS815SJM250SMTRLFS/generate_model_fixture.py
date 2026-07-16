#!/usr/bin/env python3
# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

"""Generate the non-fabrication KiCad fixture used for the STEP preview."""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew

from generate_coupon import (
    FOOTPRINT_LIBRARY,
    STYLE_PATH,
    add_physical_stackup,
    add_rounded_outline,
    point,
)


COMPONENT = Path(__file__).resolve().parent
OUTPUT = COMPONENT / "preview/model-fixture.kicad_pcb"


def main() -> None:
    style = json.loads(STYLE_PATH.read_text(encoding="utf-8"))
    board = pcbnew.BOARD()
    title = board.GetTitleBlock()
    title.SetTitle("PTS815 STEP model render fixture")
    title.SetDate("2026-07-16")
    title.SetRevision("A")
    title.SetCompany("Lyon Industries")
    title.SetComment(0, "RENDER FIXTURE - NOT FOR FABRICATION")

    switch = pcbnew.FootprintLoad(
        str(FOOTPRINT_LIBRARY), "PTS815SJM250SMTRLFS"
    )
    if switch is None:
        raise RuntimeError(f"KiCad could not load {FOOTPRINT_LIBRARY}")
    switch.SetReference("SW1")
    switch.SetPosition(point(4.5, 3.5))
    board.Add(switch)

    add_rounded_outline(board, 9.0, 7.0, style["board"]["corner_radius_mm"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(OUTPUT), board)
    add_physical_stackup(OUTPUT, style)
    print(f"KiCad {pcbnew.Version()}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
