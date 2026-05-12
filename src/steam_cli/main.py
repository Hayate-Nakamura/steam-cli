from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .exporter import format_games_csv, format_games_json, format_games_table
from .scanner import SteamNotFoundError, find_installed_games
from .settings import (
    SteamCliConfigError,
    configure_settings,
    format_configuration_status,
    get_configuration_status,
    reset_configuration,
    resolve_language,
)
from .store import localize_game_names
from .webapi import SteamWebApiConfigError, add_playtime, filter_playtime_games


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

    configure_parser = subparsers.add_parser("config", help="Manage steam-cli settings.")
    configure_parser.add_argument("--steam-id", help="SteamID64 to save or inspect.")
    configure_parser.add_argument("--web-api-key", help="Steam Web API key to save or inspect.")
    configure_parser.add_argument("--language", help="Steamworks API language code to save or inspect.")
    configure_parser.add_argument("--status", action="store_true", help="Show saved settings status.")
    configure_parser.add_argument("--reset", action="store_true", help="Remove saved settings.")
    configure_parser.add_argument("--yes", action="store_true", help="Skip confirmation for --reset.")

    list_parser = subparsers.add_parser("list", help="List installed Steam games.")
    list_format = list_parser.add_mutually_exclusive_group()
    list_format.add_argument("--json", action="store_true", help="Print games as JSON.")
    list_format.add_argument("--csv", action="store_true", help="Print games as CSV.")
    list_parser.add_argument("--details", action="store_true", help="Include detailed name source fields.")
    list_parser.add_argument("--with-playtime", action="store_true", help="Include Steam Web API playtime.")
    list_parser.add_argument("--refresh", action="store_true", help="Refresh Steam Web API playtime cache.")
    list_parser.add_argument("--steam-id", help="SteamID64 for Steam Web API requests.")
    list_parser.add_argument("--web-api-key", help="Steam Web API key.")

    export_parser = subparsers.add_parser("export", help="Export installed Steam games.")
    export_format = export_parser.add_mutually_exclusive_group(required=True)
    export_format.add_argument("--csv", type=Path, help="CSV file path to write.")
    export_format.add_argument("--json", type=Path, help="JSON file path to write.")
    export_parser.add_argument("--details", action="store_true", help="Include detailed name source fields.")

    filter_parser = subparsers.add_parser("filter", help="Filter installed Steam games.")
    play_state = filter_parser.add_mutually_exclusive_group()
    play_state.add_argument("--unplayed", action="store_true", help="Show games with 0 minutes of playtime.")
    play_state.add_argument("--played", action="store_true", help="Show games with more than 0 minutes of playtime.")
    filter_parser.add_argument("--min-playtime", type=_non_negative_int, help="Minimum total playtime in minutes.")
    filter_parser.add_argument("--max-playtime", type=_non_negative_int, help="Maximum total playtime in minutes.")
    filter_format = filter_parser.add_mutually_exclusive_group()
    filter_format.add_argument("--json", action="store_true", help="Print games as JSON.")
    filter_format.add_argument("--csv", action="store_true", help="Print games as CSV.")
    filter_parser.add_argument("--details", action="store_true", help="Include detailed name source fields.")
    filter_parser.add_argument("--refresh", action="store_true", help="Refresh Steam Web API playtime cache.")
    filter_parser.add_argument("--steam-id", help="SteamID64 for Steam Web API requests.")
    filter_parser.add_argument("--web-api-key", help="Steam Web API key.")
    return parser


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "config":
        if args.status:
            result = get_configuration_status(args.steam_id, args.web_api_key, args.language)
            print(format_configuration_status(result))
            return 0 if result.has_web_api_credentials and result.is_valid else 1

        if args.reset:
            if not args.yes:
                answer = input("Remove saved steam-cli settings? [y/N]: ").strip().lower()
                if answer not in {"y", "yes"}:
                    print("Canceled.")
                    return 1
            config_path = reset_configuration()
            print(f"Removed saved settings at {config_path}")
            return 0

        try:
            config_path = configure_settings(args.steam_id, args.web_api_key, args.language)
        except SteamCliConfigError as exc:
            print(f"steam-cli: {exc}", file=sys.stderr)
            return 1
        print(f"Saved steam-cli settings to {config_path}")
        return 0

    if args.command == "filter":
        _validate_filter_args(parser, args)

    try:
        games = find_installed_games(args.steam_path)
    except SteamNotFoundError as exc:
        print(f"steam-cli: {exc}", file=sys.stderr)
        return 1
    language, _ = resolve_language(args.language)
    games = localize_game_names(games, language)
    games = sorted(games, key=lambda game: game.name.casefold())

    if args.command == "list":
        if args.with_playtime:
            try:
                games = add_playtime(games, args.steam_id, args.web_api_key, refresh=args.refresh)
            except SteamWebApiConfigError as exc:
                print(f"steam-cli: {exc}", file=sys.stderr)
                return 1
        if args.json:
            print(format_games_json(games, args.details, args.with_playtime))
            return 0
        if args.csv:
            print(format_games_csv(games, args.details, args.with_playtime), end="")
            return 0
        print(format_games_table(games, args.details, args.with_playtime))
        return 0

    if args.command == "export":
        if args.csv:
            args.csv.write_text(format_games_csv(games, args.details), encoding="utf-8", newline="")
            return 0
        args.json.write_text(format_games_json(games, args.details), encoding="utf-8")
        return 0

    if args.command == "filter":
        try:
            games = add_playtime(games, args.steam_id, args.web_api_key, refresh=args.refresh)
        except SteamWebApiConfigError as exc:
            print(f"steam-cli: {exc}", file=sys.stderr)
            return 1

        games = filter_playtime_games(
            games,
            played=args.played,
            unplayed=args.unplayed,
            min_playtime=args.min_playtime,
            max_playtime=args.max_playtime,
        )

        if args.json:
            print(format_games_json(games, args.details, show_playtime=True))
            return 0
        if args.csv:
            print(format_games_csv(games, args.details, show_playtime=True), end="")
            return 0
        print(format_games_table(games, args.details, show_playtime=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _validate_filter_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if not any(
        (
            args.unplayed,
            args.played,
            args.min_playtime is not None,
            args.max_playtime is not None,
        )
    ):
        parser.error(
            "filter requires at least one of --unplayed, --played, --min-playtime, or --max-playtime"
        )
    if args.min_playtime is not None and args.max_playtime is not None and args.min_playtime > args.max_playtime:
        parser.error("--min-playtime must be less than or equal to --max-playtime")


if __name__ == "__main__":
    raise SystemExit(main())
