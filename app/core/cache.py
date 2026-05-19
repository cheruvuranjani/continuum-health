import time
import json
from pathlib import Path


class InMemoryCache:
    """
    Simple TTL-based in-memory cache.
    """

    def __init__(self):
        self._store: dict = {}

    def get(self, key: str):
        """Returns cached value if not expired, None if miss or expired."""
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]  # expired — evict it
            return None
        return value

    def set(self, key: str, value, ttl_seconds: int = 3600):
        """Cache value with TTL. Default 1 hour."""
        self._store[key] = (value, time.time() + ttl_seconds)

    def flush(self, key: str = None):
        """Flush specific key or entire cache."""
        if key:
            self._store.pop(key, None)
        else:
            self._store.clear()