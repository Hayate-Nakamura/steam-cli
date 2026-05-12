from __future__ import annotations

import json
import os
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from . import config
from .models import SteamGame

GET_OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
PLAYTIME_CACHE_TTL_SECONDS = 6 * 60 * 60

FetchJson = Callable[[str], dict[str, object]]


class SteamWebApiConfigError(RuntimeError):
    pass


def add_playtime(
    games: list[SteamGame],
    steam_id: str | None = None,
    web_api_key: str | None = None,
    fetch_json: FetchJson | None = None,
    cache_path: Path | None = None,
    refresh: bool = False,
) -> list[SteamGame]:
    if not games:
        return games

    resolved_steam_id = resolve_steam_id(steam_id)
    resolved_web_api_key = resolve_web_api_key(web_api_key)
    playtimes = fetch_owned_game_playtimes(
        resolved_steam_id,
        resolved_web_api_key,
        fetch_json=fetch_json,
        cache_path=cache_path,
        refresh=refresh,
    )

    return [
        replace(game, playtime_forever_minutes=playtimes.get(game.app_id))
        for game in games
    ]


def filter_unplayed_games(games: list[SteamGame]) -> list[SteamGame]:
    return [game for game in games if game.playtime_forever_minutes == 0]


def filter_playtime_games(
    games: list[SteamGame],
    played: bool = False,
    unplayed: bool = False,
    min_playtime: int | None = None,
    max_playtime: int | None = None,
) -> list[SteamGame]:
    filtered_games: list[SteamGame] = []
    for game in games:
        playtime = game.playtime_forever_minutes
        if playtime is None:
            continue
        if unplayed and playtime != 0:
            continue
        if played and playtime <= 0:
            continue
        if min_playtime is not None and playtime < min_playtime:
            continue
        if max_playtime is not None and playtime > max_playtime:
            continue
        filtered_games.append(game)
    return filtered_games


def resolve_steam_id(value: str | None = None) -> str:
    steam_id = value or os.environ.get("STEAM_ID") or config.load_config().steam_id
    if not steam_id:
        raise SteamWebApiConfigError(
            "SteamID64 is required. Use steam-cli config, --steam-id, or STEAM_ID."
        )
    return steam_id


def resolve_web_api_key(value: str | None = None) -> str:
    web_api_key = value or os.environ.get("STEAM_WEB_API_KEY") or config.load_config().web_api_key
    if not web_api_key:
        raise SteamWebApiConfigError(
            "Steam Web API key is required. Use steam-cli config, --web-api-key, or STEAM_WEB_API_KEY."
        )
    return web_api_key


def fetch_owned_game_playtimes(
    steam_id: str,
    web_api_key: str,
    fetch_json: FetchJson | None = None,
    cache_path: Path | None = None,
    cache_ttl_seconds: int = PLAYTIME_CACHE_TTL_SECONDS,
    now: int | None = None,
    refresh: bool = False,
) -> dict[str, int]:
    cache = _PlaytimeCache(
        path=cache_path or default_playtime_cache_path(),
        ttl_seconds=cache_ttl_seconds,
        now=now,
    )
    if not refresh:
        cached_playtimes = cache.get(steam_id)
        if cached_playtimes is not None:
            return cached_playtimes

    params = urlencode(
        {
            "key": web_api_key,
            "steamid": steam_id,
            "include_appinfo": "false",
            "include_played_free_games": "true",
            "format": "json",
        }
    )
    url = f"{GET_OWNED_GAMES_URL}?{params}"

    try:
        payload = (fetch_json or _fetch_json)(url)
    except (OSError, URLError, TimeoutError, ValueError):
        return {}

    playtimes = _extract_playtimes(payload)
    cache.set(steam_id, playtimes)
    cache.save()
    return playtimes


def validate_credentials(
    steam_id: str,
    web_api_key: str,
    fetch_json: FetchJson | None = None,
) -> bool:
    params = urlencode(
        {
            "key": web_api_key,
            "steamid": steam_id,
            "include_appinfo": "false",
            "include_played_free_games": "true",
            "format": "json",
        }
    )
    url = f"{GET_OWNED_GAMES_URL}?{params}"

    try:
        payload = (fetch_json or _fetch_json)(url)
    except (OSError, URLError, TimeoutError, ValueError):
        return False

    return isinstance(payload.get("response"), dict)


def default_playtime_cache_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "steam-cli" / "webapi_playtime.json"

    return Path.home() / ".cache" / "steam-cli" / "webapi_playtime.json"


def _fetch_json(url: str) -> dict[str, object]:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_playtimes(payload: dict[str, object]) -> dict[str, int]:
    response = payload.get("response")
    if not isinstance(response, dict):
        return {}

    games = response.get("games")
    if not isinstance(games, list):
        return {}

    playtimes: dict[str, int] = {}
    for game in games:
        if not isinstance(game, dict):
            continue

        app_id = game.get("appid")
        playtime = game.get("playtime_forever")
        if isinstance(app_id, int) and isinstance(playtime, int):
            playtimes[str(app_id)] = playtime

    return playtimes


class _PlaytimeCache:
    def __init__(self, path: Path, ttl_seconds: int, now: int | None = None) -> None:
        self.path = path
        self.ttl_seconds = ttl_seconds
        self.now = int(time.time()) if now is None else now
        self.data = self._load()
        self.dirty = False

    def get(self, steam_id: str) -> dict[str, int] | None:
        entry = self._entries().get(steam_id)
        if not isinstance(entry, dict):
            return None

        fetched_at = entry.get("fetched_at")
        playtimes = entry.get("playtimes")
        if not isinstance(fetched_at, int) or not isinstance(playtimes, dict):
            return None
        if self.now - fetched_at > self.ttl_seconds:
            return None

        parsed: dict[str, int] = {}
        for app_id, playtime in playtimes.items():
            if isinstance(app_id, str) and isinstance(playtime, int):
                parsed[app_id] = playtime
        return parsed

    def set(self, steam_id: str, playtimes: dict[str, int]) -> None:
        self._entries()[steam_id] = {
            "fetched_at": self.now,
            "playtimes": playtimes,
        }
        self.dirty = True

    def save(self) -> None:
        if not self.dirty:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _entries(self) -> dict[str, object]:
        entries = self.data.setdefault("entries", {})
        if not isinstance(entries, dict):
            self.data["entries"] = {}
            return self.data["entries"]
        return entries

    def _load(self) -> dict[str, object]:
        if not self.path.exists():
            return {"version": 1, "entries": {}}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"version": 1, "entries": {}}

        if not isinstance(data, dict):
            return {"version": 1, "entries": {}}
        if data.get("version") != 1:
            return {"version": 1, "entries": {}}
        if not isinstance(data.get("entries"), dict):
            data["entries"] = {}
        return data
