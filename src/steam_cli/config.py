from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SteamCliConfig:
    steam_id: str | None = None
    web_api_key: str | None = None
    language: str | None = None


def default_config_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "steam-cli" / "config.json"

    try:
        home = Path.home()
    except RuntimeError:
        return Path("steam-cli-config.json")

    return home / ".config" / "steam-cli" / "config.json"


def load_config(path: Path | None = None) -> SteamCliConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return SteamCliConfig()

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return SteamCliConfig()

    if not isinstance(data, dict):
        return SteamCliConfig()

    steam_id = data.get("steam_id")
    web_api_key = data.get("web_api_key")
    language = data.get("language")
    return SteamCliConfig(
        steam_id=steam_id if isinstance(steam_id, str) and steam_id else None,
        web_api_key=web_api_key if isinstance(web_api_key, str) and web_api_key else None,
        language=language if isinstance(language, str) and language else None,
    )


def save_config(config: SteamCliConfig, path: Path | None = None) -> Path:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "steam_id": config.steam_id,
                "web_api_key": config.web_api_key,
                "language": config.language,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return config_path
