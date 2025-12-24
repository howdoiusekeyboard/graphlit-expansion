"""Admin API endpoints for cache management and system monitoring.

This module provides administrative endpoints for:
- Cache statistics and monitoring
- Cache invalidation
- System health checks

These endpoints should be protected in production environments.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from graphlit.api.dependencies import get_cache
from graphlit.cache.memory_cache import InMemoryCache

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


# =============================================================================
# Pydantic Models
# =============================================================================


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""

    available: bool = Field(..., description="Whether cache is available")
    size: int = Field(..., description="Current number of keys in cache")
    maxsize: int = Field(..., description="Maximum cache size")
    ttl_seconds: int = Field(..., description="Default TTL in seconds")
    hit_count: int = Field(..., description="Cache hit count")
    miss_count: int = Field(..., description="Cache miss count")
    hit_rate: float = Field(..., description="Cache hit rate (0-1)")


class ClearCacheResponse(BaseModel):
    """Response for cache clear operation."""

    status: str = Field(..., description="Status message")
    previous_size: int = Field(..., description="Number of keys before clearing")


# =============================================================================
# Endpoint 1: Cache Statistics
# =============================================================================


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache: InMemoryCache = Depends(get_cache),
) -> CacheStatsResponse:
    """Get cache statistics and performance metrics.

    Returns statistics about the in-memory cache including:
    - Hit/miss rates
    - Current size
    - TTL settings

    Args:
        cache: Injected in-memory cache instance.

    Returns:
        CacheStatsResponse with cache metrics.
    """
    logger.info("api_get_cache_stats")

    try:
        stats = cache.get_stats()

        return CacheStatsResponse(
            available=bool(stats["available"]),
            size=int(stats["size"]),
            maxsize=int(stats["maxsize"]),
            ttl_seconds=int(stats["ttl_seconds"]),
            hit_count=int(stats["hit_count"]),
            miss_count=int(stats["miss_count"]),
            hit_rate=float(stats["hit_rate"]),
        )

    except Exception as e:
        logger.error("get_cache_stats_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 2: Clear Cache
# =============================================================================


@router.post("/cache/clear", response_model=ClearCacheResponse)
async def clear_cache(
    cache: InMemoryCache = Depends(get_cache),
) -> ClearCacheResponse:
    """Clear all cache entries.

    Use this endpoint to manually clear all cache entries. Useful for:
    - Resetting cache after data updates
    - Clearing stale recommendations
    - Testing cache functionality

    Note: In-memory cache does not support pattern-based invalidation.
    This endpoint clears ALL cached data.

    Args:
        cache: Injected in-memory cache instance.

    Returns:
        ClearCacheResponse with previous cache size.
    """
    logger.info("api_clear_cache")

    try:
        # Get current size before clearing
        stats = cache.get_stats()
        previous_size = stats["size"]

        # Clear all entries
        await cache.clear()

        logger.info(
            "cache_cleared",
            previous_size=previous_size,
        )

        return ClearCacheResponse(
            status="success",
            previous_size=previous_size,
        )

    except Exception as e:
        logger.error("clear_cache_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}",
        ) from e
