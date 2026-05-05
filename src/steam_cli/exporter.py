from __future__ import annotations

from .models import SteamGame


def format_games_table(games: list[SteamGame]) -> str:
    if not games:
        return "No installed Steam games found."

    rows = [
        ("AppID", "Name", "Install Path"),
        *[(game.app_id, game.name, str(game.install_path)) for game in games],
    ]
    widths = [max(len(row[column]) for row in rows) for column in range(3)]

    lines = [
        _format_row(rows[0], widths),
        _format_row(tuple("-" * width for width in widths), widths),
    ]
    lines.extend(_format_row(row, widths) for row in rows[1:])
    return "\n".join(lines)


def _format_row(row: tuple[str, str, str], widths: list[int]) -> str:
    return "  ".join(value.ljust(width) for value, width in zip(row, widths))
