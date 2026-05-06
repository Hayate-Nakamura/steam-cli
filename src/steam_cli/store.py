from __future__ import annotations

import json
import locale
import os
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import SteamGame

STORE_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STORE_NAME_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

FetchJson = Callable[[str], dict[str, object]]

_LOCALE_TO_STEAM_LANGUAGE = {
    "ar": "arabic",
    "bg": "bulgarian",
    "cs": "czech",
    "da": "danish",
    "de": "german",
    "el": "greek",
    "en": "english",
    "es": "spanish",
    "fi": "finnish",
    "fr": "french",
    "hu": "hungarian",
    "id": "indonesian",
    "it": "italian",
    "ja": "japanese",
    "ko": "koreana",
    "nl": "dutch",
    "no": "norwegian",
    "pl": "polish",
    "pt": "portuguese",
    "ro": "romanian",
    "ru": "russian",
    "sv": "swedish",
    "th": "thai",
    "tr": "turkish",
    "uk": "ukrainian",
    "vi": "vietnamese",
    "zh": "schinese",
}

_REGION_TO_STEAM_LANGUAGE = {
    "es_419": "latam",
    "pt_br": "brazilian",
    "zh_cn": "schinese",
    "zh_hans": "schinese",
    "zh_hant": "tchinese",
    "zh_hk": "tchinese",
    "zh_tw": "tchinese",
}

_WINDOWS_LANGUAGE_NAMES = {
    "arabic": "arabic",
    "bulgarian": "bulgarian",
    "chinese": "schinese",
    "czech": "czech",
    "danish": "danish",
    "dutch": "dutch",
    "english": "english",
    "finnish": "finnish",
    "french": "french",
    "german": "german",
    "greek": "greek",
    "hungarian": "hungarian",
    "indonesian": "indonesian",
    "italian": "italian",
    "japanese": "japanese",
    "korean": "koreana",
    "norwegian": "norwegian",
    "polish": "polish",
    "portuguese": "portuguese",
    "romanian": "romanian",
    "russian": "russian",
    "spanish": "spanish",
    "swedish": "swedish",
    "thai": "thai",
    "turkish": "turkish",
    "ukrainian": "ukrainian",
    "vietnamese": "vietnamese",
}


def localize_game_names(
    games: list[SteamGame],
    language: str | None = None,
    fetch_json: FetchJson | None = None,
    cache_path: Path | None = None,
) -> list[SteamGame]:
    if not games:
        return games

    steam_language = language or detect_steam_language()
    localized_names = fetch_store_app_names(
        [game.app_id for game in games],
        steam_language,
        fetch_json=fetch_json,
        cache_path=cache_path,
    )

    if not localized_names:
        return games

    return [
        replace(
            game,
            name=localized_names.get(game.app_id, game.name),
            steam_store_name=localized_names.get(game.app_id),
            name_source="steam_store" if game.app_id in localized_names else "appmanifest",
        )
        for game in games
    ]


def detect_steam_language() -> str:
    language_code, _ = locale.getlocale()
    if not language_code:
        return "english"

    normalized = language_code.lower().replace("-", "_")
    if normalized in _REGION_TO_STEAM_LANGUAGE:
        return _REGION_TO_STEAM_LANGUAGE[normalized]

    language = normalized.split("_", 1)[0]
    if language in _WINDOWS_LANGUAGE_NAMES:
        return _WINDOWS_LANGUAGE_NAMES[language]
    return _LOCALE_TO_STEAM_LANGUAGE.get(language, "english")


def fetch_store_app_names(
    app_ids: list[str],
    language: str,
    fetch_json: FetchJson | None = None,
    cache_path: Path | None = None,
    cache_ttl_seconds: int = STORE_NAME_CACHE_TTL_SECONDS,
    now: int | None = None,
) -> dict[str, str]:
    fetch = fetch_json or _fetch_json
    cache = _StoreNameCache(
        path=cache_path or default_store_name_cache_path(),
        ttl_seconds=cache_ttl_seconds,
        now=now,
    )
    names: dict[str, str] = {}
    missing_app_ids: list[str] = []

    for app_id in app_ids:
        cached_name = cache.get(language, app_id)
        if cached_name is not None:
            names[app_id] = cached_name
        else:
            missing_app_ids.append(app_id)

    for app_id in missing_app_ids:
        params = urlencode(
            {
                "appids": app_id,
                "l": language,
                "filters": "basic",
            }
        )
        url = f"{STORE_APPDETAILS_URL}?{params}"

        try:
            payload = fetch(url)
        except (OSError, URLError, TimeoutError, ValueError):
            continue

        fetched_names = _extract_app_names(payload)
        names.update(fetched_names)
        for fetched_app_id, name in fetched_names.items():
            cache.set(language, fetched_app_id, name)

    cache.save()

    return names


def default_store_name_cache_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "steam-cli" / "store_names.json"

    return Path.home() / ".cache" / "steam-cli" / "store_names.json"


def _fetch_json(url: str) -> dict[str, object]:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_app_names(payload: dict[str, object]) -> dict[str, str]:
    names: dict[str, str] = {}

    for app_id, value in payload.items():
        if not isinstance(value, dict):
            continue
        if value.get("success") is not True:
            continue
        data = value.get("data")
        if not isinstance(data, dict):
            continue
        name = data.get("name")
        if isinstance(name, str) and name:
            names[app_id] = name

    return names


class _StoreNameCache:
    def __init__(self, path: Path, ttl_seconds: int, now: int | None = None) -> None:
        self.path = path
        self.ttl_seconds = ttl_seconds
        self.now = int(time.time()) if now is None else now
        self.data = self._load()
        self.dirty = False

    def get(self, language: str, app_id: str) -> str | None:
        entry = self._entries().get(_cache_key(language, app_id))
        if not isinstance(entry, dict):
            return None

        name = entry.get("name")
        fetched_at = entry.get("fetched_at")
        if not isinstance(name, str) or not isinstance(fetched_at, int):
            return None
        if self.now - fetched_at > self.ttl_seconds:
            return None

        return name

    def set(self, language: str, app_id: str, name: str) -> None:
        self._entries()[_cache_key(language, app_id)] = {
            "name": name,
            "fetched_at": self.now,
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


def _cache_key(language: str, app_id: str) -> str:
    return f"{language}:{app_id}"
