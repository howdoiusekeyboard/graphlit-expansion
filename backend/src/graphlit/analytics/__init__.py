"""Analytics module for graph-based ML features.

This module provides machine learning algorithms for citation network analysis:
- Community detection using Neo4j GDS Louvain algorithm
- Predictive impact scoring with composite metrics
"""

from __future__ import annotations

__all__ = ["CommunityDetector", "ImpactScorer"]


def __getattr__(name: str) -> type:
    """Lazy import to avoid circular dependencies."""
    if name == "CommunityDetector":
        from graphlit.analytics.community_detector import CommunityDetector

        return CommunityDetector
    if name == "ImpactScorer":
        from graphlit.analytics.impact_scorer import ImpactScorer

        return ImpactScorer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
