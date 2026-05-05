from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporter import format_games_table
from .scanner import SteamNotFoundError, find_installed_games


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="steam-cli",
        description="Inspect installed Steam games from the local Steam library.",
    )
    parser.add_argument(
        "--steam-path",
        type=Path,
        help="Steam installation path. If omitted, steam-cli reads it from the Windows registry.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List installed Steam games.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        try:
            games = find_installed_games(args.steam_path)
        except SteamNotFoundError as exc:
            print(f"steam-cli: {exc}", file=sys.stderr)
            return 1

        print(format_games_table(games))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
