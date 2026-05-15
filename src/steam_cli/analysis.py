from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .models import SteamGame

SortKey = str


@dataclass(frozen=True)
class LibrarySummary:
    path: Path
    game_count: int
    install_size_bytes: int
    unknown_size_count: int


@dataclass(frozen=True)
class GamesSummary:
    game_count: int
    install_size_bytes: int
    unknown_size_count: int
    playtime_forever_minutes: int | None
    unknown_playtime_count: int | None
    libraries: tuple[LibrarySummary, ...]


def sort_games(games: list[SteamGame], sort_key: SortKey, descending: bool = False) -> list[SteamGame]:
    known: list[SteamGame] = []
    unknown: list[SteamGame] = []
    key_func = _sort_value_func(sort_key)

    for game in games:
        value = key_func(game)
        if value is None:
            unknown.append(game)
        else:
            known.append(game)

    return sorted(known, key=key_func, reverse=descending) + unknown


def summarize_games(games: list[SteamGame], include_playtime: bool = False) -> GamesSummary:
    install_size_bytes = 0
    unknown_size_count = 0
    playtime_forever_minutes = 0
    unknown_playtime_count = 0
    library_totals: dict[Path, dict[str, int]] = {}

    for game in games:
        library_path = _library_path(game.install_path)
        library_summary = library_totals.setdefault(
            library_path,
            {"game_count": 0, "install_size_bytes": 0, "unknown_size_count": 0},
        )
        library_summary["game_count"] += 1

        if game.install_size_bytes is None:
            unknown_size_count += 1
            library_summary["unknown_size_count"] += 1
        else:
            install_size_bytes += game.install_size_bytes
            library_summary["install_size_bytes"] += game.install_size_bytes

        if include_playtime:
            if game.playtime_forever_minutes is None:
                unknown_playtime_count += 1
            else:
                playtime_forever_minutes += game.playtime_forever_minutes

    libraries = tuple(
        LibrarySummary(
            path=path,
            game_count=values["game_count"],
            install_size_bytes=values["install_size_bytes"],
            unknown_size_count=values["unknown_size_count"],
        )
        for path, values in sorted(library_totals.items(), key=lambda item: str(item[0]).casefold())
    )

    return GamesSummary(
        game_count=len(games),
        install_size_bytes=install_size_bytes,
        unknown_size_count=unknown_size_count,
        playtime_forever_minutes=playtime_forever_minutes if include_playtime else None,
        unknown_playtime_count=unknown_playtime_count if include_playtime else None,
        libraries=libraries,
    )


def _sort_value_func(sort_key: SortKey) -> Callable[[SteamGame], object | None]:
    if sort_key == "name":
        return lambda game: game.name.casefold()
    if sort_key == "size":
        return lambda game: game.install_size_bytes
    if sort_key == "last-updated":
        return lambda game: game.last_updated_at
    if sort_key == "playtime":
        return lambda game: game.playtime_forever_minutes
    raise ValueError(f"unsupported sort key: {sort_key}")


def _library_path(install_path: Path) -> Path:
    if (
        install_path.parent.name.casefold() == "common"
        and install_path.parent.parent.name.casefold() == "steamapps"
    ):
        return install_path.parent.parent.parent
    return install_path.parent
