from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import SteamGame, SteamLibrary
from .parser import parse_key_values_file


class SteamNotFoundError(RuntimeError):
    pass


def find_steam_path() -> Path:
    try:
        import winreg
    except ImportError as exc:
        raise SteamNotFoundError(
            "Steam path auto-detection is only available on Windows. Use --steam-path."
        ) from exc

    registry_locations = (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
    )

    for root, subkey in registry_locations:
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "SteamPath")
        except OSError:
            continue

        path = Path(value)
        if path.exists():
            return path

    raise SteamNotFoundError("Steam installation was not found in the Windows registry.")


def find_libraries(steam_path: Path | None = None) -> list[SteamLibrary]:
    steam_root = steam_path or find_steam_path()
    libraries: list[SteamLibrary] = [SteamLibrary(steam_root)]
    library_file = steam_root / "steamapps" / "libraryfolders.vdf"

    if not library_file.exists():
        return libraries

    data = parse_key_values_file(library_file)
    libraryfolders = data.get("libraryfolders")
    if not isinstance(libraryfolders, dict):
        return libraries

    for key in sorted(libraryfolders, key=_library_sort_key):
        value = libraryfolders[key]
        library_path = _extract_library_path(value)
        if library_path is None:
            continue

        library = SteamLibrary(library_path)
        if library not in libraries:
            libraries.append(library)

    return libraries


def find_installed_games(steam_path: Path | None = None) -> list[SteamGame]:
    games: list[SteamGame] = []

    for library in find_libraries(steam_path):
        for manifest_path in sorted(library.steamapps_path.glob("appmanifest_*.acf")):
            game = _game_from_manifest(library, manifest_path)
            if game is not None:
                games.append(game)

    return sorted(games, key=lambda game: game.name.casefold())


def _game_from_manifest(library: SteamLibrary, manifest_path: Path) -> SteamGame | None:
    data = parse_key_values_file(manifest_path)
    app_state = data.get("AppState")
    if not isinstance(app_state, dict):
        return None

    app_id = _string_value(app_state.get("appid"))
    name = _string_value(app_state.get("name"))
    install_dir = _string_value(app_state.get("installdir"))
    install_size_bytes = _int_value(app_state.get("SizeOnDisk"))
    last_updated_at = _timestamp_value(app_state.get("LastUpdated"))

    if not app_id or not name or not install_dir:
        return None

    return SteamGame(
        app_id=app_id,
        name=name,
        install_path=library.steamapps_path / "common" / install_dir,
        install_size_bytes=install_size_bytes,
        last_updated_at=last_updated_at,
        appmanifest_name=name,
    )


def _extract_library_path(value: object) -> Path | None:
    if isinstance(value, str):
        return Path(value)

    if isinstance(value, dict):
        path = value.get("path")
        if isinstance(path, str):
            return Path(path)

    return None


def _library_sort_key(key: str) -> tuple[int, str]:
    if key.isdigit():
        return int(key), key
    return 999_999, key


def _string_value(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _int_value(value: object) -> int | None:
    if not isinstance(value, str) or not value.isdigit():
        return None
    return int(value)


def _timestamp_value(value: object) -> datetime | None:
    timestamp = _int_value(value)
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp).astimezone()
