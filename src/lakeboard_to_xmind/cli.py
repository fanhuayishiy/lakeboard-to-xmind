from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert_lakeboard_to_xmind, convert_xmind_to_lakeboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lakeboard-to-xmind",
        description="语雀 Lakeboard 思维导图与 XMind 文件互转工具。",
    )
    subparsers = parser.add_subparsers(dest="command")

    to_xmind = subparsers.add_parser("to-xmind", help="将 .lakeboard 转换为 .xmind")
    _add_common_args(to_xmind, source_help="Path to the .lakeboard file")
    to_xmind.add_argument(
        "-t",
        "--template",
        type=Path,
        help="Optional .xmind file to reuse sheet/theme/compatibility files from",
    )
    to_xmind.add_argument("--no-style", action="store_true", help="Do not copy colors, branch styles, summaries, or markers")

    to_lakeboard = subparsers.add_parser("to-lakeboard", help="将 .xmind 反向转换为 .lakeboard")
    _add_common_args(to_lakeboard, source_help="Path to the .xmind file")
    to_lakeboard.add_argument("--no-style", action="store_true", help="Do not copy colors, summaries, boundaries, or markers")
    return parser


def _add_common_args(parser: argparse.ArgumentParser, *, source_help: str) -> None:
    parser.add_argument("source", type=Path, help=source_help)
    parser.add_argument("-o", "--output", type=Path, help="Output path. Defaults to SOURCE with the target suffix")
    parser.add_argument("--no-overwrite", action="store_true", help="Fail if the output file already exists")


def build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lakeboard-to-xmind",
        description="将语雀 Lakeboard 思维导图 .lakeboard 转换为 XMind .xmind。",
    )
    parser.add_argument("source", type=Path, help="Path to the .lakeboard file")
    parser.add_argument("-o", "--output", type=Path, help="Output .xmind path")
    parser.add_argument("-t", "--template", type=Path, help="Optional .xmind compatibility/style template")
    parser.add_argument("--no-style", action="store_true", help="Do not copy colors, branch styles, summaries, or markers")
    parser.add_argument("--no-overwrite", action="store_true", help="Fail if the output file already exists")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser() if argv[:1] in (["to-xmind"], ["to-lakeboard"]) else build_legacy_parser()
    args = parser.parse_args(argv)

    try:
        if getattr(args, "command", None) == "to-lakeboard":
            result = convert_xmind_to_lakeboard(
                args.source,
                args.output,
                overwrite=not args.no_overwrite,
                preserve_style=not args.no_style,
            )
        else:
            result = convert_lakeboard_to_xmind(
                args.source,
                args.output,
                template=getattr(args, "template", None),
                overwrite=not args.no_overwrite,
                preserve_style=not args.no_style,
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
