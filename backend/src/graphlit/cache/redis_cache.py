"""Redis cache client for recommendation results.

This module provides async Redis caching with graceful degradation.
When Redis is unavailable, all operations return None/False but do not
raise exceptions, allowing the system to continue without caching.

Usage:
    >>> from graphlit.cache.redis_cache import RecommendationCache
    >>> from graphlit.config import RedisSettings
    >>>
    >>> settings = RedisSettings()
    >>> cache = RecommendationCache(settings)
    >>>
    >>> # Connect (best-effort, no exception if unavailable)
    >>> await cache.connect()
    >>>
    >>> # Get/set with automatic JSON serialization
    >>> recommendations = await cache.get_recommendations("paper:W123:10")
    >>> if recommendations is None:
    ...     recommendations = compute_recommendations()
    ...     await cache.set_recommendations("paper:W123:10", recommendations, ttl=3600)
    >>>
    >>> # Cleanup
    >>> await cache.close()
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from graphlit.config import RedisSettings

try:
    from redis.asyncio import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = structlog.get_logger(__name__)


class RecommendationCache:
    """Async Redis cache for recommendation results.

    Provides graceful degradation: all methods return None/False when
    Redis is unavailable or operations fail. Never raises exceptions
    to callers.

    Attributes:
        settings: Redis configuration settings.
        client: Redis async client instance (None if unavailable).
        available: Whether Redis connection is established.
        stats: Cache statistics (hits, misses, errors).
    """

    def __init__(self, settings: RedisSettings) -> None:
        """Initialize Redis cache client.

        Args:
            settings: Redis configuration from Settings.redis.
        """
        self.settings = settings
        self.client: Any = None
        self.available = False

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0,
            "invalidations": 0,
        }

    async def connect(self) -> bool:
        """Connect to Redis server (best-effort).

        Returns:
            True if connection succeeded, False if Redis unavailable.
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis_unavailable", reason="redis library not installed")
            return False

        try:
            # Create async Redis client
            self.client = Redis.from_url(
                self.settings.uri,
                db=self.settings.db,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
            )

            # Test connection with PING
            if self.client is not None:
                await self.client.ping()

            self.available = True
            logger.info(
                "redis_connected",
                uri=self.settings.uri,
                db=self.settings.db,
            )
            return True

        except Exception as e:
            logger.warning(
                "redis_connection_failed",
                uri=self.settings.uri,
                error=str(e),
                error_type=type(e).__name__,
            )
            self.client = None
            self.available = False
            return False

    async def close(self) -> None:
        """Close Redis connection (best-effort)."""
        if self.client is not None:
            try:
                await self.client.close()
                logger.info("redis_disconnected")
            except Exception as e:
                logger.warning("redis_close_failed", error=str(e))
            finally:
                self.client = None
                self.available = False

    # =========================================================================
    # Recommendation Caching
    # =========================================================================

    async def get_recommendations(self, key: str) -> list[dict[str, Any]] | None:
        """Get cached recommendations (returns None on miss or error).

        Args:
            key: Cache key (e.g., "recommendations:paper:W123:10")

        Returns:
            List of recommendation dicts if cached, None if miss or unavailable.
        """
        if not self.available or self.client is None:
            return None

        try:
            value = await self.client.get(key)

            if value is None:
                self.stats["misses"] += 1
                logger.debug("cache_miss", key=key)
                return None

            # Deserialize JSON
            recommendations: list[dict[str, Any]] = json.loads(value)

            self.stats["hits"] += 1
            logger.debug(
                "cache_hit",
                key=key,
                recommendations_count=len(recommendations),
            )

            return recommendations

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "cache_get_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    async def set_recommendations(
        self,
        key: str,
        recommendations: list[dict[str, Any]],
        ttl_seconds: int = 3600,
    ) -> bool:
        """Store recommendations in cache with TTL (best-effort).

        Args:
            key: Cache key
            recommendations: List of recommendation dicts
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if stored successfully, False if unavailable or error.
        """
        if not self.available or self.client is None:
            return False

        try:
            # Serialize to JSON
            value = json.dumps(recommendations)

            # Store with TTL
            await self.client.setex(key, ttl_seconds, value)

            self.stats["sets"] += 1
            logger.debug(
                "cache_set",
                key=key,
                recommendations_count=len(recommendations),
                ttl_seconds=ttl_seconds,
            )

            return True

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "cache_set_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    # =========================================================================
    # Similarity Matrix Caching
    # =========================================================================

    async def get_similarity_matrix(self) -> dict[str, dict[str, float]] | None:
        """Get cached similarity matrix (returns None on miss or error).

        Returns:
            Nested dict mapping paper_id → {paper_id → similarity} if cached,
            None if miss or unavailable.
        """
        if not self.available or self.client is None:
            return None

        key = "similarities:matrix"

        try:
            value = await self.client.get(key)

            if value is None:
                self.stats["misses"] += 1
                logger.debug("similarity_matrix_cache_miss")
                return None

            # Deserialize JSON
            matrix: dict[str, dict[str, float]] = json.loads(value)

            self.stats["hits"] += 1
            logger.debug(
                "similarity_matrix_cache_hit",
                papers_count=len(matrix),
            )

            return matrix

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "similarity_matrix_get_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    async def set_similarity_matrix(
        self,
        matrix: dict[str, dict[str, float]],
    ) -> bool:
        """Store similarity matrix in cache with 24-hour TTL (best-effort).

        Args:
            matrix: Nested dict mapping paper_id → {paper_id → similarity}

        Returns:
            True if stored successfully, False if unavailable or error.
        """
        if not self.available or self.client is None:
            return False

        key = "similarities:matrix"
        ttl_seconds = 86400  # 24 hours

        try:
            # Serialize to JSON
            value = json.dumps(matrix)

            # Store with TTL
            await self.client.setex(key, ttl_seconds, value)

            self.stats["sets"] += 1
            logger.debug(
                "similarity_matrix_cached",
                papers_count=len(matrix),
                ttl_seconds=ttl_seconds,
            )

            return True

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "similarity_matrix_set_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    # =========================================================================
    # Cache Invalidation
    # =========================================================================

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern (best-effort).

        Args:
            pattern: Redis key pattern (e.g., "recommendations:paper:*")

        Returns:
            Number of keys deleted, 0 if unavailable or error.
        """
        if not self.available or self.client is None:
            return 0

        try:
            # Find keys matching pattern
            keys = []
            async for key in self.client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if not keys:
                logger.debug("invalidate_pattern_no_matches", pattern=pattern)
                return 0

            # Delete all matching keys
            deleted: int = await self.client.delete(*keys)

            self.stats["invalidations"] += deleted
            logger.info(
                "cache_invalidated",
                pattern=pattern,
                deleted_count=deleted,
            )

            return deleted

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "cache_invalidation_failed",
                pattern=pattern,
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0

    async def invalidate_key(self, key: str) -> bool:
        """Invalidate a single cache key (best-effort).

        Args:
            key: Exact cache key to delete

        Returns:
            True if deleted, False if unavailable or error.
        """
        if not self.available or self.client is None:
            return False

        try:
            deleted = await self.client.delete(key)

            if deleted > 0:
                self.stats["invalidations"] += 1
                logger.debug("cache_key_invalidated", key=key)
                return True

            return False

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "cache_key_invalidation_failed",
                key=key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    # =========================================================================
    # Cache Statistics
    # =========================================================================

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics and Redis server info.

        Returns:
            Dictionary with cache stats (hits, misses, etc.) and server info.
        """
        stats: dict[str, Any] = {
            "available": self.available,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "sets": self.stats["sets"],
            "invalidations": self.stats["invalidations"],
            "hit_rate": 0.0,
        }

        # Calculate hit rate
        total_requests = self.stats["hits"] + self.stats["misses"]
        if total_requests > 0:
            stats["hit_rate"] = self.stats["hits"] / total_requests

        # Get Redis server info if available
        if self.available and self.client is not None:
            try:
                info = await self.client.info()

                stats["keys_count"] = await self.client.dbsize()
                stats["memory_used_mb"] = info.get("used_memory", 0) / (1024 * 1024)
                stats["evicted_keys"] = info.get("evicted_keys", 0)
                stats["connected_clients"] = info.get("connected_clients", 0)

            except Exception as e:
                logger.warning("redis_info_failed", error=str(e))

        return stats

    async def clear_all(self) -> int:
        """Clear all keys in the current database (dangerous, for testing only).

        Returns:
            Number of keys deleted, 0 if unavailable or error.
        """
        if not self.available or self.client is None:
            return 0

        try:
            # Get all keys
            keys = []
            async for key in self.client.scan_iter(count=1000):
                keys.append(key)

            if not keys:
                return 0

            # Delete all
            deleted: int = await self.client.delete(*keys)

            logger.warning("cache_cleared_all", deleted_count=deleted)

            return deleted

        except Exception as e:
            self.stats["errors"] += 1
            logger.warning(
                "cache_clear_all_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0
