#!/usr/bin/env python3
"""Open every complete native library with a real KiCad 10 CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"FAIL {' '.join(command)}\n{detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kicad-cli",
        default="kicad-cli",
        help="KiCad 10 CLI executable (default: kicad-cli on PATH)",
    )
    args = parser.parse_args()
    cli = str(Path(args.kicad_cli).expanduser()) if "/" in args.kicad_cli else args.kicad_cli
    try:
        version = subprocess.run(
            [cli, "--version"], cwd=ROOT, text=True, capture_output=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"FAIL unable to run KiCad CLI: {exc}") from exc
    if not version.startswith("10."):
        raise SystemExit(f"FAIL KiCad 10 is required, found {version or 'unknown version'}")

    records = []
    for record_path in sorted((ROOT / "components").glob("*/*/component.json")):
        records.append((record_path, json.loads(record_path.read_text(encoding="utf-8"))))

    with tempfile.TemporaryDirectory(prefix="component-intelligence-kicad-") as temporary:
        output_root = Path(temporary)
        for record_path, record in records:
            native_name = Path(record["cad"]["symbol"]["path"]).stem
            symbol_output = output_root / "symbols" / native_name
            footprint_output = output_root / "footprints" / native_name
            symbol_output.mkdir(parents=True)
            footprint_output.mkdir(parents=True)
            symbol_path = record_path.parent / record["cad"]["symbol"]["path"]
            footprint_path = record_path.parent / record["cad"]["footprint"]["path"]
            run([
                cli,
                "sym",
                "export",
                "svg",
                "--black-and-white",
                "--output",
                str(symbol_output),
                str(symbol_path),
            ])
            run([
                cli,
                "fp",
                "export",
                "svg",
                "--black-and-white",
                "--layers",
                "F.Cu,F.SilkS,F.Fab,F.CrtYd",
                "--define-var",
                f"COMPONENT_INTELLIGENCE_ROOT={ROOT}",
                "--output",
                str(footprint_output),
                str(footprint_path.parent),
            ])
            if not list(symbol_output.glob("*.svg")):
                raise SystemExit(f"FAIL KiCad produced no symbol SVG for {record['id']}")
            if not list(footprint_output.glob("*.svg")):
                raise SystemExit(f"FAIL KiCad produced no footprint SVG for {record['id']}")

    print(f"PASS KiCad {version} native import: {len(records)} symbols; {len(records)} footprints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
