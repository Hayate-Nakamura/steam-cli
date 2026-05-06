from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SteamLibrary:
    path: Path

    @property
    def steamapps_path(self) -> Path:
        return self.path / "steamapps"


@dataclass(frozen=True)
class SteamGame:
    app_id: str
    name: str
    install_path: Path
    install_size_bytes: int | None = None
    last_updated_at: datetime | None = None
    appmanifest_name: str | None = None
    steam_store_name: str | None = None
    name_source: str = "appmanifest"
