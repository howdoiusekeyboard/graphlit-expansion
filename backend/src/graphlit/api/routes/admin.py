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

from graphlit.api.dependencies import get_redis_cache
from graphlit.cache.redis_cache import RecommendationCache

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

    available: bool = Field(..., description="Whether Redis is available")
    hits: int = Field(..., description="Cache hit count")
    misses: int = Field(..., description="Cache miss count")
    errors: int = Field(..., description="Cache error count")
    sets: int = Field(..., description="Cache set count")
    invalidations: int = Field(..., description="Invalidation count")
    hit_rate: float = Field(..., description="Cache hit rate (0-1)")
    keys_count: int | None = Field(None, description="Total keys in cache")
    memory_used_mb: float | None = Field(None, description="Memory used (MB)")
    evicted_keys: int | None = Field(None, description="Evicted keys count")
    connected_clients: int | None = Field(None, description="Connected client count")


class InvalidateCacheRequest(BaseModel):
    """Request to invalidate cache keys by pattern."""

    pattern: str = Field(..., description="Redis key pattern (e.g., 'recommendations:paper:*')")


class InvalidateCacheResponse(BaseModel):
    """Response for cache invalidation."""

    pattern: str = Field(..., description="Pattern used for invalidation")
    deleted_count: int = Field(..., description="Number of keys deleted")
    status: str = Field(..., description="Status message")


# =============================================================================
# Endpoint 1: Cache Statistics
# =============================================================================


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache: RecommendationCache = Depends(get_redis_cache),
) -> CacheStatsResponse:
    """Get cache statistics and performance metrics.

    Returns detailed statistics about the Redis cache including:
    - Hit/miss rates
    - Memory usage
    - Key counts
    - Client connections

    Args:
        cache: Injected Redis cache instance.

    Returns:
        CacheStatsResponse with comprehensive cache metrics.
    """
    logger.info("api_get_cache_stats")

    try:
        stats = await cache.get_stats()

        return CacheStatsResponse(
            available=bool(stats["available"]),
            hits=int(stats["hits"]),
            misses=int(stats["misses"]),
            errors=int(stats["errors"]),
            sets=int(stats["sets"]),
            invalidations=int(stats["invalidations"]),
            hit_rate=float(stats["hit_rate"]),
            keys_count=int(stats["keys_count"]) if "keys_count" in stats else None,
            memory_used_mb=float(stats["memory_used_mb"])
            if "memory_used_mb" in stats
            else None,
            evicted_keys=int(stats["evicted_keys"]) if "evicted_keys" in stats else None,
            connected_clients=int(stats["connected_clients"])
            if "connected_clients" in stats
            else None,
        )

    except Exception as e:
        logger.error("get_cache_stats_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 2: Cache Invalidation
# =============================================================================


@router.post("/cache/invalidate", response_model=InvalidateCacheResponse)
async def invalidate_cache(
    request: InvalidateCacheRequest,
    cache: RecommendationCache = Depends(get_redis_cache),
) -> InvalidateCacheResponse:
    """Invalidate cache keys matching a pattern.

    Use this endpoint to manually clear cache entries. Useful for:
    - Clearing all recommendation caches
    - Invalidating specific paper caches
    - Resetting cache after data updates

    Common patterns:
    - `recommendations:*` - All recommendations
    - `recommendations:paper:*` - All paper recommendations
    - `recommendations:paper:W123456:*` - Specific paper
    - `similarities:*` - All similarity matrices

    Args:
        request: Invalidation request with pattern.
        cache: Injected Redis cache instance.

    Returns:
        InvalidateCacheResponse with deletion count.

    Raises:
        HTTPException 422: If pattern is empty or invalid.
        HTTPException 503: If Redis is unavailable.
    """
    logger.info("api_invalidate_cache", pattern=request.pattern)

    # Validate pattern
    if not request.pattern or request.pattern.strip() == "":
        raise HTTPException(
            status_code=422,
            detail="Pattern cannot be empty",
        )

    # Check if Redis is available
    if not cache.available:
        raise HTTPException(
            status_code=503,
            detail="Redis cache is unavailable",
        )

    try:
        deleted_count = await cache.invalidate_pattern(request.pattern)

        logger.info(
            "cache_invalidated",
            pattern=request.pattern,
            deleted_count=deleted_count,
        )

        return InvalidateCacheResponse(
            pattern=request.pattern,
            deleted_count=deleted_count,
            status="success",
        )

    except Exception as e:
        logger.error("invalidate_cache_failed", pattern=request.pattern, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}",
        ) from e
