from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

from .cache import CacheStatus, get_cache_status
from .config import SteamCliConfig, default_config_path, load_config, save_config
from .store import STORE_NAME_CACHE_TTL_SECONDS, default_store_name_cache_path, detect_steam_language
from .webapi import FetchJson, PLAYTIME_CACHE_TTL_SECONDS, default_playtime_cache_path, validate_credentials


class SteamCliConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConfigureStatus:
    config_path: Path
    steam_id_source: str | None
    web_api_key_source: str | None
    language: str
    language_source: str
    is_valid: bool
    store_name_cache: CacheStatus
    playtime_cache: CacheStatus

    @property
    def has_web_api_credentials(self) -> bool:
        return self.steam_id_source is not None and self.web_api_key_source is not None


def configure_settings(
    steam_id: str | None = None,
    web_api_key: str | None = None,
    language: str | None = None,
    config_path: Path | None = None,
    fetch_json: FetchJson | None = None,
) -> Path:
    current_config = load_config(config_path)
    resolved_steam_id = steam_id or current_config.steam_id or input("SteamID64: ").strip()
    resolved_web_api_key = web_api_key or current_config.web_api_key or getpass("Steam Web API key: ").strip()
    resolved_language = language or current_config.language

    if not resolved_steam_id:
        raise SteamCliConfigError("SteamID64 is required.")
    if not resolved_web_api_key:
        raise SteamCliConfigError("Steam Web API key is required.")

    if not validate_credentials(resolved_steam_id, resolved_web_api_key, fetch_json=fetch_json):
        raise SteamCliConfigError(
            "Could not validate SteamID64 and Steam Web API key with Steam Web API."
        )

    return save_config(
        SteamCliConfig(
            steam_id=resolved_steam_id,
            web_api_key=resolved_web_api_key,
            language=resolved_language,
        ),
        path=config_path,
    )


def get_configuration_status(
    steam_id: str | None = None,
    web_api_key: str | None = None,
    language: str | None = None,
    config_path: Path | None = None,
    fetch_json: FetchJson | None = None,
) -> ConfigureStatus:
    resolved_config_path = config_path or default_config_path()
    stored_config = load_config(resolved_config_path)

    resolved_steam_id, steam_id_source = _resolve_value_with_source(
        cli_value=steam_id,
        env_name="STEAM_ID",
        config_value=stored_config.steam_id,
    )
    resolved_web_api_key, web_api_key_source = _resolve_value_with_source(
        cli_value=web_api_key,
        env_name="STEAM_WEB_API_KEY",
        config_value=stored_config.web_api_key,
    )
    resolved_language, language_source = resolve_language(language, stored_config)

    is_valid = False
    if resolved_steam_id and resolved_web_api_key:
        is_valid = validate_credentials(
            resolved_steam_id,
            resolved_web_api_key,
            fetch_json=fetch_json,
        )

    return ConfigureStatus(
        config_path=resolved_config_path,
        steam_id_source=steam_id_source,
        web_api_key_source=web_api_key_source,
        language=resolved_language,
        language_source=language_source,
        is_valid=is_valid,
        store_name_cache=get_cache_status(
            default_store_name_cache_path(),
            STORE_NAME_CACHE_TTL_SECONDS,
        ),
        playtime_cache=get_cache_status(
            default_playtime_cache_path(),
            PLAYTIME_CACHE_TTL_SECONDS,
        ),
    )


def reset_configuration(config_path: Path | None = None) -> Path:
    resolved_config_path = config_path or default_config_path()
    if resolved_config_path.exists():
        resolved_config_path.unlink()
    return resolved_config_path


def resolve_language(
    cli_value: str | None = None,
    stored_config: SteamCliConfig | None = None,
) -> tuple[str, str]:
    if cli_value:
        return cli_value, "command-line option"

    env_value = os.environ.get("STEAM_CLI_LANGUAGE")
    if env_value:
        return env_value, "STEAM_CLI_LANGUAGE environment variable"

    config_value = (stored_config or load_config()).language
    if config_value:
        return config_value, "config file"

    return detect_steam_language(), "OS locale"


def format_configuration_status(result: ConfigureStatus) -> str:
    lines = [
        f"Config file: {result.config_path}",
        f"SteamID64: {_format_source(result.steam_id_source)}",
        f"Steam Web API key: {_format_source(result.web_api_key_source)}",
        f"Language: {result.language} ({result.language_source})",
        f"Steam Store name cache: {_format_cache_status(result.store_name_cache)}",
        f"Steam Web API playtime cache: {_format_cache_status(result.playtime_cache)}",
    ]
    if not result.has_web_api_credentials:
        lines.append("Steam Web API validation: skipped")
    else:
        lines.append(f"Steam Web API validation: {'OK' if result.is_valid else 'failed'}")
    return "\n".join(lines)


def _resolve_value_with_source(
    cli_value: str | None,
    env_name: str,
    config_value: str | None,
) -> tuple[str | None, str | None]:
    if cli_value:
        return cli_value, "command-line option"

    env_value = os.environ.get(env_name)
    if env_value:
        return env_value, f"{env_name} environment variable"

    if config_value:
        return config_value, "config file"

    return None, None


def _format_source(source: str | None) -> str:
    if source is None:
        return "missing"
    return f"configured ({source})"


def _format_cache_status(status: CacheStatus) -> str:
    if not status.exists:
        return f"missing ({status.path})"
    return (
        f"{status.entry_count} entries, "
        f"{status.fresh_count} fresh, "
        f"{status.expired_count} expired ({status.path})"
    )
