"""FastAPI dependency injection for GraphLit ResearchRadar API.

This module provides singleton dependencies for Neo4j, in-memory cache, and
recommendation services. All dependencies are lazily initialized and properly
cleaned up on application shutdown.

Usage:
    from fastapi import Depends
    from graphlit.api.dependencies import get_recommender

    @app.get("/recommendations/{paper_id}")
    async def recommend(
        paper_id: str,
        recommender: CollaborativeFilterRecommender = Depends(get_recommender)
    ):
        return await recommender.get_paper_recommendations(paper_id)
"""

from __future__ import annotations

from typing import Any

import structlog

from graphlit.cache.memory_cache import InMemoryCache
from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.recommendations.collaborative_filter import CollaborativeFilterRecommender

logger = structlog.get_logger(__name__)

# Singleton instances (initialized on first request)
_neo4j_client: Neo4jClient | None = None
_memory_cache: InMemoryCache | None = None
_recommender: CollaborativeFilterRecommender | None = None


# =============================================================================
# Neo4j Client Dependency
# =============================================================================


async def get_neo4j_client() -> Neo4jClient:
    """Get or create singleton Neo4j client.

    Returns:
        Connected Neo4jClient instance.

    Raises:
        Exception: If Neo4j connection fails.
    """
    global _neo4j_client

    if _neo4j_client is None:
        settings = get_settings()

        logger.info("initializing_neo4j_client")
        _neo4j_client = Neo4jClient(settings.neo4j)

        # Verify connection
        if not await _neo4j_client.verify_connection():
            raise RuntimeError("Failed to connect to Neo4j database")

        logger.info("neo4j_client_initialized")

    return _neo4j_client


# =============================================================================
# In-Memory Cache Dependency
# =============================================================================


async def get_cache() -> InMemoryCache:
    """Get or create singleton in-memory cache.

    Returns:
        InMemoryCache instance (always available).

    Note:
        This cache is in-memory only and will be cleared on application restart.
        User profiles are persisted to Neo4j separately.
    """
    global _memory_cache

    if _memory_cache is None:
        logger.info("initializing_memory_cache")
        _memory_cache = InMemoryCache(maxsize=1000, ttl=3600)

        logger.info(
            "memory_cache_initialized",
            maxsize=_memory_cache.maxsize,
            ttl=_memory_cache.default_ttl,
        )

    return _memory_cache


# =============================================================================
# Recommendation Engine Dependency
# =============================================================================


async def get_recommender() -> CollaborativeFilterRecommender:
    """Get or create singleton recommendation engine.

    Returns:
        CollaborativeFilterRecommender instance with active Neo4j connection.

    Raises:
        RuntimeError: If Neo4j connection fails.
    """
    global _recommender

    if _recommender is None:
        # Get Neo4j client (will initialize if needed)
        client = await get_neo4j_client()

        logger.info("initializing_recommender")
        _recommender = CollaborativeFilterRecommender(client)

        logger.info("recommender_initialized")

    return _recommender


# =============================================================================
# Shutdown / Cleanup
# =============================================================================


async def shutdown_connections() -> None:
    """Cleanup all singleton connections on application shutdown.

    This should be called from the FastAPI lifespan context manager.
    """
    global _neo4j_client, _memory_cache, _recommender

    logger.info("shutting_down_connections")

    # Clear in-memory cache
    if _memory_cache is not None:
        await _memory_cache.clear()
        _memory_cache = None

    # Close Neo4j client
    if _neo4j_client is not None:
        await _neo4j_client.close()
        _neo4j_client = None

    # Clear recommender reference
    _recommender = None

    logger.info("connections_shutdown_complete")


# =============================================================================
# Settings Dependency (for routes that need config)
# =============================================================================


def get_settings_dependency() -> Any:
    """Get application settings.

    Returns:
        Settings instance.
    """
    return get_settings()
