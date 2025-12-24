"""In-memory cache with TTL support using cachetools.

This module provides a thread-safe in-memory cache with automatic expiration.
It replaces Redis for simple caching use cases where persistence and
distribution across multiple processes are not required.

Usage:
    >>> from graphlit.cache.memory_cache import InMemoryCache
    >>>
    >>> cache = InMemoryCache(maxsize=1000, ttl=3600)
    >>>
    >>> # Get/set with automatic TTL
    >>> result = await cache.get("recommendations:paper:W123")
    >>> if result is None:
    ...     result = compute_recommendations()
    ...     await cache.set("recommendations:paper:W123", result)
    >>>
    >>> # Get cache stats
    >>> stats = cache.get_stats()
"""

from __future__ import annotations

import json
from typing import Any, cast

import structlog
from cachetools import TTLCache

logger = structlog.get_logger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support.

    Provides a simple key-value cache with automatic expiration using
    cachetools.TTLCache. All operations are async-compatible for use
    with FastAPI.

    Attributes:
        cache: TTLCache instance with configurable size and TTL
        maxsize: Maximum number of entries
        default_ttl: Default time-to-live in seconds
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 3600) -> None:
        """Initialize cache with max size and default TTL.

        Args:
            maxsize: Maximum number of entries in cache
            ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)
        self.maxsize = maxsize
        self.default_ttl = ttl
        self._hit_count = 0
        self._miss_count = 0

        logger.info(
            "cache_initialized",
            maxsize=maxsize,
            ttl=ttl,
        )

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        try:
            value = self.cache[key]
            self._hit_count += 1

            logger.debug("cache_hit", key=key)

            # Deserialize JSON if stored as string
            if isinstance(value, str):
                return json.loads(value)
            return value

        except KeyError:
            self._miss_count += 1
            logger.debug("cache_miss", key=key)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set value in cache.

        Note: Custom TTL per key is not supported by cachetools.TTLCache.
        All entries use the default TTL set during initialization.

        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized if dict/list)
            ttl_seconds: Ignored (all entries use default TTL)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize to JSON if dict/list for consistency with Redis behavior
            if isinstance(value, dict | list):
                value = json.dumps(value)

            self.cache[key] = value

            logger.debug(
                "cache_set",
                key=key,
                ttl_used=self.default_ttl,
            )

            return True

        except Exception as e:
            logger.warning(
                "cache_set_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if key didn't exist
        """
        try:
            del self.cache[key]
            logger.debug("cache_deleted", key=key)
            return True

        except KeyError:
            logger.debug("cache_delete_miss", key=key)
            return False

    async def clear(self) -> bool:
        """Clear all cache entries.

        Returns:
            True if successful
        """
        self.cache.clear()
        self._hit_count = 0
        self._miss_count = 0

        logger.info("cache_cleared")
        return True

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (
            self._hit_count / total_requests if total_requests > 0 else 0.0
        )

        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "ttl_seconds": self.default_ttl,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate": round(hit_rate, 3),
            "available": True,  # Always available (in-memory)
        }

    async def get_recommendations(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Get cached recommendations (convenience method).

        Args:
            cache_key: Cache key for recommendations

        Returns:
            List of recommendation dicts or None if not found
        """
        result = await self.get(cache_key)
        if result is not None and isinstance(result, list):
            return cast(list[dict[str, Any]], result)
        return None

    async def set_recommendations(
        self,
        cache_key: str,
        recommendations: list[dict[str, Any]],
        ttl_seconds: int = 3600,
    ) -> bool:
        """Set cached recommendations (convenience method).

        Args:
            cache_key: Cache key for recommendations
            recommendations: List of recommendation dicts
            ttl_seconds: Ignored (uses default TTL)

        Returns:
            True if successful
        """
        return await self.set(cache_key, recommendations, ttl_seconds)
