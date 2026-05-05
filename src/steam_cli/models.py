from __future__ import annotations

from dataclasses import dataclass
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
