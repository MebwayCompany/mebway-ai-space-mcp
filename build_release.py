"""Build a public-only ZIP from explicit paths; never recurse through the repo."""
from __future__ import annotations

import argparse
from pathlib import Path
import stat
import sys
import zipfile

PUBLIC_FILES = (
    "README.md", "LICENSE", "SECURITY.md", "PRIVACY.md", "pyproject.toml", "build_release.py", "server.json",
    "examples/client-config.json", "examples/presentation.json",
    "mebway_mcp/__init__.py", "mebway_mcp/__main__.py", "mebway_mcp/renderer.py",
)


def build_release(output: Path) -> None:
    root = Path(__file__).resolve().parent
    contents = []
    for name in PUBLIC_FILES:
        source = root / name
        for component in [source, *source.parents]:
            if component == root:
                break
            if component.is_symlink():
                raise ValueError("Symlinks are not allowed in a public release")
        if not source.is_file() or not stat.S_ISREG(source.stat().st_mode):
            raise ValueError("Public release requires regular allowlisted files")
        if output.resolve() == source.resolve():
            raise ValueError("Release output cannot overwrite a source file")
        contents.append((name, source.read_bytes()))
    # Create only after every source passes validation; refuse overwriting an existing artifact.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an allowlisted public Mebway MCP archive")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        build_release(args.output)
    except (OSError, ValueError) as error:
        print(f"Public release refused ({type(error).__name__}).", file=sys.stderr)
        return 2
    print("Public release archive created; review its contents before publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
