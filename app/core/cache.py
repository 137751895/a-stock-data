"""Minimal file-based TTL cache for upstream API responses.

Design decisions:
- File-based (uses cache_dir from config)
- TTL-based expiration (per-key configurable)
- JSON serialization only (all cached data must be JSON-serializable)
- Can be disabled by setting cache_dir to empty string
- Thread-safe via atomic write (write to temp, then rename)
"""
import hashlib
import json
import os
import time
from pathlib import Path

from app.core.config import settings


def _cache_dir() -> Path | None:
    """Return cache directory path, or None if caching is disabled."""
    if not settings.cache_dir:
        return None
    p = Path(settings.cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cache_key(namespace: str, key: str) -> str:
    """Generate a filesystem-safe cache key."""
    h = hashlib.md5(f"{namespace}:{key}".encode()).hexdigest()
    return f"{namespace}_{h}.json"


def cache_get(namespace: str, key: str, ttl_seconds: int) -> dict | list | None:
    """Read from cache if not expired.

    Returns cached data or None if miss/expired/disabled.
    """
    cache_dir = _cache_dir()
    if cache_dir is None:
        return None

    cache_file = cache_dir / _cache_key(namespace, key)
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            entry = json.load(f)
        if time.time() - entry.get("ts", 0) >= ttl_seconds:
            cache_file.unlink(missing_ok=True)
            return None
        return entry.get("data")
    except (json.JSONDecodeError, OSError, KeyError):
        cache_file.unlink(missing_ok=True)
        return None


def cache_set(namespace: str, key: str, data: dict | list) -> None:
    """Write data to cache.

    Does nothing if caching is disabled.
    """
    cache_dir = _cache_dir()
    if cache_dir is None:
        return

    cache_file = cache_dir / _cache_key(namespace, key)
    entry = {"ts": time.time(), "data": data}

    # Atomic write: write to temp file then rename
    tmp_file = cache_file.with_suffix(".tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        os.replace(str(tmp_file), str(cache_file))
    except OSError:
        tmp_file.unlink(missing_ok=True)
