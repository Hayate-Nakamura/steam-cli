from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CacheStatus:
    path: Path
    exists: bool
    entry_count: int = 0
    fresh_count: int = 0
    expired_count: int = 0


def get_cache_status(path: Path, ttl_seconds: int, now: int | None = None) -> CacheStatus:
    if not path.exists():
        return CacheStatus(path=path, exists=False)

    current_time = int(time.time()) if now is None else now

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return CacheStatus(path=path, exists=True)

    if not isinstance(data, dict):
        return CacheStatus(path=path, exists=True)

    entries = data.get("entries")
    if not isinstance(entries, dict):
        return CacheStatus(path=path, exists=True)

    fresh_count = 0
    expired_count = 0
    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        fetched_at = entry.get("fetched_at")
        if not isinstance(fetched_at, int):
            continue
        if current_time - fetched_at > ttl_seconds:
            expired_count += 1
        else:
            fresh_count += 1

    return CacheStatus(
        path=path,
        exists=True,
        entry_count=len(entries),
        fresh_count=fresh_count,
        expired_count=expired_count,
    )
