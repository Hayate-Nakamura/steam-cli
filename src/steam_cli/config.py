from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    web_api_key = _load_web_api_key(data)
    language = data.get("language")
    return SteamCliConfig(
        steam_id=steam_id if isinstance(steam_id, str) and steam_id else None,
        web_api_key=web_api_key,
        language=language if isinstance(language, str) and language else None,
    )


def save_config(config: SteamCliConfig, path: Path | None = None) -> Path:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
        "version": 2,
        "steam_id": config.steam_id,
        "language": config.language,
    }
    web_api_key = _dump_web_api_key(config.web_api_key)
    if web_api_key is not None:
        data.update(web_api_key)
    config_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return config_path


def _load_web_api_key(data: dict[str, Any]) -> str | None:
    protected = data.get("web_api_key_protected")
    if isinstance(protected, dict):
        scheme = protected.get("scheme")
        ciphertext = protected.get("ciphertext")
        if scheme == "windows-dpapi" and isinstance(ciphertext, str):
            decrypted = _unprotect_windows_secret(ciphertext)
            return decrypted if decrypted else None

    legacy_web_api_key = data.get("web_api_key")
    if isinstance(legacy_web_api_key, str) and legacy_web_api_key:
        return legacy_web_api_key

    return None


def _dump_web_api_key(web_api_key: str | None) -> dict[str, object] | None:
    if not web_api_key:
        return None

    protected = _protect_windows_secret(web_api_key)
    if protected:
        return {
            "web_api_key_protected": {
                "scheme": "windows-dpapi",
                "ciphertext": protected,
            }
        }

    return {"web_api_key": web_api_key}


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _protect_windows_secret(secret: str) -> str | None:
    if sys.platform != "win32":
        return None

    payload = secret.encode("utf-8")
    input_buffer = ctypes.create_string_buffer(payload)
    input_blob = _DataBlob(len(payload), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = _DataBlob()

    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        return None

    try:
        encrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return base64.b64encode(encrypted).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def _unprotect_windows_secret(ciphertext: str) -> str | None:
    if sys.platform != "win32":
        return None

    try:
        encrypted = base64.b64decode(ciphertext)
    except ValueError:
        return None

    input_buffer = ctypes.create_string_buffer(encrypted)
    input_blob = _DataBlob(len(encrypted), ctypes.cast(input_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output_blob = _DataBlob()

    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        return None

    try:
        decrypted = ctypes.string_at(output_blob.pbData, output_blob.cbData)
        return decrypted.decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)
