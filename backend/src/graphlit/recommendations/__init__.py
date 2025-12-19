"""Recommendation engines for GraphLit ResearchRadar.

This module provides collaborative filtering and content-based recommendation
algorithms for academic papers:
- Collaborative filtering with 4 similarity methods
- Content-based filtering using topic similarity
- Similarity calculation utilities

Usage:
    >>> from graphlit.recommendations import CollaborativeFilterRecommender
    >>> from graphlit.database.neo4j_client import Neo4jClient
    >>> from graphlit.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> async with Neo4jClient(settings.neo4j) as client:
    ...     recommender = CollaborativeFilterRecommender(client)
    ...     recommendations = await recommender.get_paper_recommendations(
    ...         paper_id="W123456",
    ...         limit=10
    ...     )
"""

from __future__ import annotations

__all__ = ["CollaborativeFilterRecommender", "ContentBasedRecommender", "similarity"]


def __getattr__(name: str) -> object:
    """Lazy import to avoid loading dependencies unnecessarily."""
    if name == "CollaborativeFilterRecommender":
        from graphlit.recommendations.collaborative_filter import (
            CollaborativeFilterRecommender,
        )

        return CollaborativeFilterRecommender

    if name == "ContentBasedRecommender":
        from graphlit.recommendations.content_based import ContentBasedRecommender

        return ContentBasedRecommender

    if name == "similarity":
        from graphlit.recommendations import similarity as similarity_module

        return similarity_module

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
