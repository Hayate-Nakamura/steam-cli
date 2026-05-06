from __future__ import annotations

import csv
import json
from io import StringIO

from .models import SteamGame


def format_games_table(games: list[SteamGame], details: bool = False) -> str:
    if not games:
        return "No installed Steam games found."

    rows = [
        _table_headers(details),
        *[_table_row(game, details) for game in games],
    ]
    widths = [max(len(row[column]) for row in rows) for column in range(len(rows[0]))]

    lines = [
        _format_row(rows[0], widths),
        _format_row(tuple("-" * width for width in widths), widths),
    ]
    lines.extend(_format_row(row, widths) for row in rows[1:])
    return "\n".join(lines)


def format_games_json(games: list[SteamGame], details: bool = False) -> str:
    return json.dumps([game_to_dict(game, details) for game in games], ensure_ascii=False, indent=2)


def format_games_csv(games: list[SteamGame], details: bool = False) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(game_to_dict_fields(details)))
    writer.writeheader()
    writer.writerows(game_to_dict(game, details) for game in games)
    return output.getvalue()


def game_to_dict(game: SteamGame, details: bool = False) -> dict[str, object]:
    data: dict[str, object] = {
        "app_id": game.app_id,
        "name": game.name,
        "install_path": str(game.install_path),
        "install_size_bytes": game.install_size_bytes,
        "last_updated_at": _format_datetime(game.last_updated_at),
    }
    if details:
        data.update(
            {
                "appmanifest_name": game.appmanifest_name or "",
                "steam_store_name": game.steam_store_name or "",
                "name_source": game.name_source,
            }
        )
    return data


def game_to_dict_fields(details: bool = False) -> tuple[str, ...]:
    fields = ("app_id", "name", "install_path", "install_size_bytes", "last_updated_at")
    if not details:
        return fields
    return fields + ("appmanifest_name", "steam_store_name", "name_source")


def _table_headers(details: bool) -> tuple[str, ...]:
    headers = ("AppID", "Name", "Size", "Last Updated", "Install Path")
    if not details:
        return headers
    return headers + ("AppManifest Name", "Steam Store Name", "Name Source")


def _table_row(game: SteamGame, details: bool) -> tuple[str, ...]:
    row = (
        game.app_id,
        game.name,
        _format_size(game.install_size_bytes),
        _format_datetime(game.last_updated_at),
        str(game.install_path),
    )
    if not details:
        return row
    return row + (
        game.appmanifest_name or "",
        game.steam_store_name or "",
        game.name_source,
    )


def _format_row(row: tuple[str, ...], widths: list[int]) -> str:
    return "  ".join(value.ljust(width) for value, width in zip(row, widths))


def _format_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "-"

    units = ("B", "KB", "MB", "GB", "TB")
    size = float(size_bytes)
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def _format_datetime(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y/%m/%d %H:%M:%S")
    return str(value)
