#!/usr/bin/env python3
# Copyright 2026 Lyon Industries
# SPDX-License-Identifier: Apache-2.0

"""Render a KiCad PCB with the repository's inspection-image style."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STYLE = ROOT / "quality/pcb-render-style.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--style", type=Path, default=DEFAULT_STYLE)
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--height", type=int, default=800)
    parser.add_argument("--side", default="top")
    parser.add_argument("--quality", choices=("basic", "high", "user", "job_settings"))
    parser.add_argument("--zoom", type=float, default=1.0)
    parser.add_argument("--pan")
    parser.add_argument("--pivot")
    parser.add_argument("--rotate")
    parser.add_argument("--perspective", action="store_true")
    parser.add_argument("--define-var", action="append", default=[])
    return parser.parse_args()


def find_kicad_cli(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    executable = shutil.which("kicad-cli")
    if executable is None:
        raise SystemExit("kicad-cli was not found; pass --kicad-cli explicitly")
    return Path(executable)


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    if len(value) != 6:
        raise ValueError("background_hex must contain exactly six hexadecimal digits")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def grade_exposed_copper(image: Image.Image, target_hex: str) -> None:
    target = hex_rgb(target_hex)
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = pixels[x, y]
            if red > 150 and green > 105 and blue < 105 and red > blue * 1.8:
                pixels[x, y] = target


def main() -> None:
    args = parse_args()
    style = json.loads(args.style.read_text(encoding="utf-8"))
    render = style["render"]
    if render["use_board_stackup_colors"] is not True:
        raise ValueError("the repository PCB render style requires stackup colors")
    cli = find_kicad_cli(args.kicad_cli)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="component-pcb-render-") as temp_dir:
        transparent = Path(temp_dir) / "transparent.png"
        supersample = render["supersample"]
        command = [
            str(cli),
            "pcb",
            "render",
            "--output",
            str(transparent),
            "--width",
            str(args.width * supersample),
            "--height",
            str(args.height * supersample),
            "--side",
            args.side,
            "--background",
            "transparent",
            "--quality",
            args.quality or render["quality"],
            "--preset",
            render["preset"],
            "--zoom",
            str(args.zoom),
        ]
        if render["floor"]:
            command.append("--floor")
        if args.pan:
            command.extend(("--pan", args.pan))
        if args.pivot:
            command.extend(("--pivot", args.pivot))
        if args.rotate:
            command.extend(("--rotate", args.rotate))
        if args.perspective:
            command.append("--perspective")
        for definition in args.define_var:
            command.extend(("--define-var", definition))
        command.append(str(args.input))

        subprocess.run(command, check=True)
        with Image.open(transparent) as source:
            rendered = source.convert("RGBA")
        alpha = rendered.getchannel("A").point(
            lambda value: 255
            if value >= render["minimum_foreground_alpha"]
            else 0
        )
        rendered.putalpha(alpha)
        background = Image.new(
            "RGBA", rendered.size, (*hex_rgb(render["background_hex"]), 255)
        )
        background.alpha_composite(rendered)
        output = background.convert("RGB").resize(
            (args.width, args.height), Image.Resampling.LANCZOS
        )
        grade_exposed_copper(
            output, style["board"]["surface_finish"]["render_hex"]
        )
        output.save(args.output, optimize=True)

    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
