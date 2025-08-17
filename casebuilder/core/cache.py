import asyncio
from typing import Any, Dict, Optional

class SimpleCache:
    """A simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._loop = asyncio.get_event_loop()

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in the cache with an optional TTL."""
        self._cache[key] = value
        if ttl:
            self._loop.call_later(ttl, self.delete, key)

    async def delete(self, key: str):
        """Delete a value from the cache."""
        if key in self._cache:
            del self._cache[key]

    async def clear(self):
        """Clear the entire cache."""
        self._cache.clear()

cache = SimpleCache()
