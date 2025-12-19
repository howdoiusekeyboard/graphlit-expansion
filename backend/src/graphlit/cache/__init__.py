"""Caching layer for GraphLit ResearchRadar.

This module provides Redis-based caching for expensive operations:
- Recommendation results (1 hour TTL)
- Similarity matrices (24 hour TTL)
- Topic mappings (4 hour TTL)

The cache gracefully degrades when Redis is unavailable - the system
remains fully functional without caching, just with slower performance.

Usage:
    >>> from graphlit.cache import RecommendationCache
    >>> from graphlit.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> cache = RecommendationCache(settings.redis)
    >>>
    >>> # Connect to Redis (or fail gracefully)
    >>> if await cache.connect():
    ...     print("Redis available")
    ... else:
    ...     print("Redis unavailable - degraded mode")
    >>>
    >>> # Try to get cached data
    >>> cached = await cache.get_recommendations("key")
    >>> if cached is None:
    ...     # Cache miss or unavailable
    ...     data = compute_expensive_recommendations()
    ...     await cache.set_recommendations("key", data, ttl=3600)
"""

from __future__ import annotations

__all__ = ["RecommendationCache"]


def __getattr__(name: str) -> type:
    """Lazy import to avoid loading Redis dependencies if not needed."""
    if name == "RecommendationCache":
        from graphlit.cache.redis_cache import RecommendationCache

        return RecommendationCache

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
