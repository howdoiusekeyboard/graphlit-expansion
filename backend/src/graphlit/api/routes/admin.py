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

from graphlit.api.dependencies import get_cache, get_neo4j_client
from graphlit.cache.memory_cache import InMemoryCache
from graphlit.database.neo4j_client import Neo4jClient

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


class DatabaseStatsResponse(BaseModel):
    """Database statistics response."""

    total_papers: int = Field(..., description="Total papers in database")
    total_communities: int = Field(..., description="Total communities detected")
    total_citations: int = Field(..., description="Total citation count across all papers")
    total_authors: int = Field(0, description="Total unique authors")
    total_topics: int = Field(0, description="Total unique topics")
    papers_with_communities: int = Field(
        0, description="Papers assigned to communities"
    )


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


# =============================================================================
# Endpoint 3: Database Statistics
# =============================================================================


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(
    client: Neo4jClient = Depends(get_neo4j_client),
) -> DatabaseStatsResponse:
    """Get real-time database statistics.

    Returns statistics about the Neo4j database including:
    - Total papers
    - Total communities detected
    - Total citations
    - Total authors and topics

    Args:
        client: Injected Neo4j client.

    Returns:
        DatabaseStatsResponse with database metrics.
    """
    logger.info("api_get_database_stats")

    try:
        async with client.session() as session:
            # Get all stats in parallel
            queries_to_run = {
                "total_papers": "MATCH (p:Paper) RETURN count(p) AS count",
                "total_communities": """
                    MATCH (p:Paper)
                    WHERE p.community IS NOT NULL
                    WITH p.community AS community_id, count(p) AS size
                    WHERE size >= 3
                    RETURN count(DISTINCT community_id) AS count
                """,
                "total_citations": """
                    MATCH (p:Paper)
                    RETURN sum(p.citations) AS count
                """,
                "total_authors": "MATCH (a:Author) RETURN count(a) AS count",
                "total_topics": "MATCH (t:Topic) RETURN count(t) AS count",
                "papers_with_communities": """
                    MATCH (p:Paper)
                    WHERE p.community IS NOT NULL
                    RETURN count(p) AS count
                """,
            }

            stats = {}
            for key, query in queries_to_run.items():
                result = await session.run(query)
                record = await result.single()
                stats[key] = int(record["count"]) if record and record["count"] else 0

        logger.info("database_stats_fetched", **stats)

        return DatabaseStatsResponse(
            total_papers=stats["total_papers"],
            total_communities=stats["total_communities"],
            total_citations=stats["total_citations"],
            total_authors=stats["total_authors"],
            total_topics=stats["total_topics"],
            papers_with_communities=stats["papers_with_communities"],
        )

    except Exception as e:
        logger.error("get_database_stats_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 4: Analytics Computation Status
# =============================================================================


class AnalyticsStatusResponse(BaseModel):
    """Analytics computation status."""

    total_papers: int = Field(..., description="Total papers in database")
    pagerank_computed: bool = Field(..., description="Whether any PageRank scores exist")
    pagerank_papers: int = Field(..., description="Papers with PageRank computed")
    pagerank_null_count: int = Field(..., description="Papers missing PageRank")
    impact_scores_computed: bool = Field(
        ..., description="Whether any impact scores exist"
    )
    impact_score_papers: int = Field(..., description="Papers with impact scores")
    impact_score_null_count: int = Field(..., description="Papers missing impact scores")


@router.get("/analytics/status", response_model=AnalyticsStatusResponse)
async def get_analytics_status(
    client: Neo4jClient = Depends(get_neo4j_client),
) -> AnalyticsStatusResponse:
    """Check analytics computation status across all papers.

    Returns statistics about which graph analytics have been computed:
    - PageRank centrality scores
    - Predictive impact scores (PIS)

    This endpoint is useful for monitoring whether the analytics pipeline
    has been run and which papers still need analytics computed.

    Args:
        client: Injected Neo4j client.

    Returns:
        AnalyticsStatusResponse with counts of computed vs missing analytics.
    """
    logger.info("api_analytics_status_check")

    query = """
    MATCH (p:Paper)
    RETURN
      count(p) AS total,
      sum(CASE WHEN p.pagerank IS NOT NULL THEN 1 ELSE 0 END) AS pagerank_count,
      sum(CASE WHEN p.pagerank IS NULL THEN 1 ELSE 0 END) AS pagerank_null,
      sum(CASE WHEN p.impact_score IS NOT NULL THEN 1 ELSE 0 END) AS impact_count,
      sum(CASE WHEN p.impact_score IS NULL THEN 1 ELSE 0 END) AS impact_null
    """

    try:
        async with client.session() as session:
            result = await session.run(query)
            record = await result.single()

            if not record:
                raise HTTPException(
                    status_code=500, detail="Failed to query analytics status"
                )

            total = int(record["total"])
            pagerank_count = int(record["pagerank_count"])
            impact_count = int(record["impact_count"])

            logger.info(
                "analytics_status_fetched",
                total=total,
                pagerank_computed=pagerank_count,
                impact_computed=impact_count,
            )

            return AnalyticsStatusResponse(
                total_papers=total,
                pagerank_computed=(pagerank_count > 0),
                pagerank_papers=pagerank_count,
                pagerank_null_count=int(record["pagerank_null"]),
                impact_scores_computed=(impact_count > 0),
                impact_score_papers=impact_count,
                impact_score_null_count=int(record["impact_null"]),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analytics_status_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get analytics status: {str(e)}"
        ) from e
