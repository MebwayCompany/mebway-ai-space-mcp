"""Render an explicitly supplied safe presentation; never connect automatically."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .renderer import render_html

MAX_INPUT_BYTES = 8 * 1024 * 1024


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Mebway presentation viewer")
    commands = parser.add_subparsers(dest="command", required=True)
    render = commands.add_parser("render", help="Convert safe presentation JSON to standalone HTML")
    render.add_argument("input", type=Path, help="Explicit presentation JSON file")
    render.add_argument("--output", type=Path, required=True, help="New destination HTML file (existing files are never overwritten)")
    args = parser.parse_args()
    try:
        with args.input.open("rb") as source:
            raw = source.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("Presentation exceeds the 8 MiB input limit")
        data = json.loads(raw)
        document = render_html(data)
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files")
        # Encode before opening anything. Exclusive creation refuses existing
        # files, hardlinks and symlinks atomically, without a check/open race.
        encoded = document.encode("utf-8")
        with args.output.open("xb") as destination:
            destination.write(encoded)
    except (OSError, ValueError, RecursionError) as error:
        # Do not echo customer input, paths, or JSON parser excerpts into logs.
        print(f"Cannot render presentation ({type(error).__name__}); check the file and public schema.", file=sys.stderr)
        return 2
    print("Presentation HTML created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
