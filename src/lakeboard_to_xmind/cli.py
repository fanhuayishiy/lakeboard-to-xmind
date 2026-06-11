from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert_lakeboard_to_xmind


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lakeboard-to-xmind",
        description="Convert a Lakeboard mind map (.lakeboard) into an XMind workbook (.xmind).",
    )
    parser.add_argument("source", type=Path, help="Path to the .lakeboard file")
    parser.add_argument("-o", "--output", type=Path, help="Output .xmind path. Defaults to SOURCE with .xmind suffix")
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        help="Optional .xmind file to reuse sheet/theme/compatibility files from",
    )
    parser.add_argument("--no-overwrite", action="store_true", help="Fail if the output file already exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = convert_lakeboard_to_xmind(
            args.source,
            args.output,
            template=args.template,
            overwrite=not args.no_overwrite,
        )
    except Exception as exc:  # pragma: no cover - keeps CLI errors readable
        print(f"lakeboard-to-xmind: error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote: {result.output}")
    print(f"Root: {result.root_title}")
    print(f"Topics: {result.topic_count} ({result.first_level_count} first-level branches)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
