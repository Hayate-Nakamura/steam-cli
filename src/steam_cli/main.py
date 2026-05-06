from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporter import format_games_csv, format_games_json, format_games_table
from .scanner import SteamNotFoundError, find_installed_games
from .store import localize_game_names


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
    parser.add_argument(
        "--language",
        help="Steam Store API language code for localized app names. Defaults to the OS locale.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List installed Steam games.")
    list_format = list_parser.add_mutually_exclusive_group()
    list_format.add_argument("--json", action="store_true", help="Print games as JSON.")
    list_format.add_argument("--csv", action="store_true", help="Print games as CSV.")
    list_parser.add_argument("--details", action="store_true", help="Include detailed name source fields.")

    export_parser = subparsers.add_parser("export", help="Export installed Steam games.")
    export_parser.add_argument("--csv", type=Path, required=True, help="CSV file path to write.")
    export_parser.add_argument("--details", action="store_true", help="Include detailed name source fields.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        games = find_installed_games(args.steam_path)
    except SteamNotFoundError as exc:
        print(f"steam-cli: {exc}", file=sys.stderr)
        return 1
    games = localize_game_names(games, args.language)
    games = sorted(games, key=lambda game: game.name.casefold())

    if args.command == "list":
        if args.json:
            print(format_games_json(games, args.details))
            return 0
        if args.csv:
            print(format_games_csv(games, args.details), end="")
            return 0
        print(format_games_table(games, args.details))
        return 0

    if args.command == "export":
        args.csv.write_text(format_games_csv(games, args.details), encoding="utf-8", newline="")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
