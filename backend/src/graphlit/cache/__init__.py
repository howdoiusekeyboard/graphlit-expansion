"""Caching layer for GraphLit ResearchRadar.

This module provides in-memory caching for expensive operations:
- Recommendation results (1 hour TTL)
- Query results (1 hour TTL)

The cache is stored in memory using cachetools and is automatically cleared
on application restart. User profiles are persisted to Neo4j for durability.

Usage:
    >>> from graphlit.cache import InMemoryCache
    >>>
    >>> cache = InMemoryCache(maxsize=1000, ttl=3600)
    >>>
    >>> # Get/set cached data
    >>> cached = await cache.get("recommendations:paper:W123")
    >>> if cached is None:
    ...     # Cache miss
    ...     data = compute_expensive_recommendations()
    ...     await cache.set("recommendations:paper:W123", data)
"""

from __future__ import annotations

__all__ = ["InMemoryCache"]


def __getattr__(name: str) -> type:
    """Lazy import for cache implementation."""
    if name == "InMemoryCache":
        from graphlit.cache.memory_cache import InMemoryCache

        return InMemoryCache

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
