"""Collaborative filtering recommendation engine.

This module implements a hybrid collaborative filtering approach that combines
4 different similarity methods with weighted scoring:
1. Citation-based similarity (35%) - Jaccard on cited papers
2. Topic affinity (30%) - Shared research topics
3. Author collaboration (20%) - Co-authorship networks
4. Citation velocity (15%) - Similar growth patterns

The engine also applies diversity filtering and time decay preferences.

Usage:
    >>> from graphlit.recommendations.collaborative_filter import CollaborativeFilterRecommender
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

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from graphlit.database.neo4j_client import Neo4jClient

from graphlit.database import queries
from graphlit.recommendations.similarity import (
    citation_velocity_similarity,
    topic_affinity_score,
)

logger = structlog.get_logger(__name__)


class CollaborativeFilterError(Exception):
    """Raised when collaborative filtering operations fail."""

    pass


class CollaborativeFilterRecommender:
    """Hybrid collaborative filtering recommendation engine.

    Combines multiple similarity methods to generate diverse, high-quality
    paper recommendations. Applies weighted scoring, diversity filtering,
    and time decay preferences.

    Attributes:
        client: Neo4jClient for database operations.
        current_year: Current year for citation velocity calculations.
        similarity_weights: Weights for combining similarity methods.
    """

    # Similarity method weights (must sum to 1.0)
    CITATION_WEIGHT = 0.35
    TOPIC_WEIGHT = 0.30
    AUTHOR_WEIGHT = 0.20
    VELOCITY_WEIGHT = 0.15

    def __init__(self, client: Neo4jClient) -> None:
        """Initialize collaborative filter recommender.

        Args:
            client: Connected Neo4jClient instance.
        """
        self.client = client
        self.current_year = datetime.now().year

        # Validate weights sum to 1.0
        total_weight = (
            self.CITATION_WEIGHT
            + self.TOPIC_WEIGHT
            + self.AUTHOR_WEIGHT
            + self.VELOCITY_WEIGHT
        )
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Similarity weights must sum to 1.0, got {total_weight:.4f}")

    # =========================================================================
    # Method 1: Citation-Based Similarity
    # =========================================================================

    async def _get_citation_based_candidates(
        self,
        paper_id: str,
        limit: int,
    ) -> dict[str, dict[str, Any]]:
        """Get candidate papers based on citation overlap.

        Args:
            paper_id: Source paper ID.
            limit: Maximum candidates to fetch.

        Returns:
            Dict mapping paper_id → candidate info with similarity_score.
        """
        logger.debug("fetching_citation_candidates", paper_id=paper_id)

        try:
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_CITATION_OVERLAP_PAPERS,
                    paper_id=paper_id,
                    min_overlap=2,
                    limit=limit,
                )
                records = await result.data()

            candidates = {}
            for record in records:
                impact_score = (
                    float(record["impact_score"]) if record["impact_score"] else None
                )
                candidates[str(record["paper_id"])] = {
                    "title": str(record["title"]),
                    "year": int(record["year"]) if record["year"] else None,
                    "citations": int(record["citations"]) if record["citations"] else 0,
                    "impact_score": impact_score,
                    "similarity_score": float(record["jaccard_similarity"]),
                    "method": "citation_overlap",
                }

            logger.debug(
                "citation_candidates_fetched",
                count=len(candidates),
            )

            return candidates

        except Exception as e:
            logger.warning(
                "citation_candidates_failed",
                paper_id=paper_id,
                error=str(e),
            )
            return {}

    # =========================================================================
    # Method 2: Topic-Based Similarity
    # =========================================================================

    async def _get_topic_based_candidates(
        self,
        paper_id: str,
        limit: int,
    ) -> dict[str, dict[str, Any]]:
        """Get candidate papers based on topic similarity.

        Args:
            paper_id: Source paper ID.
            limit: Maximum candidates to fetch.

        Returns:
            Dict mapping paper_id → candidate info with similarity_score.
        """
        logger.debug("fetching_topic_candidates", paper_id=paper_id)

        try:
            # Get source paper topics
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_PAPER_TOPICS,
                    paper_id=paper_id,
                )
                topic_records = await result.values()

                if not topic_records:
                    return {}

                source_topics = [(str(rec[0]), float(rec[2])) for rec in topic_records]

                # Get similar papers
                result = await session.run(
                    queries.GET_SIMILAR_TOPIC_PAPERS,
                    paper_id=paper_id,
                    min_shared_topics=1,
                    limit=limit,
                )
                records = await result.data()

            candidates = {}
            for record in records:
                candidate_topics_raw = record["target_topics"]
                candidate_topics = [
                    (str(t["topic_id"]), float(t["score"]))
                    for t in candidate_topics_raw
                ]

                affinity = topic_affinity_score(source_topics, candidate_topics)
                impact_score = (
                    float(record["impact_score"]) if record["impact_score"] else None
                )

                candidates[str(record["paper_id"])] = {
                    "title": str(record["title"]),
                    "year": int(record["year"]) if record["year"] else None,
                    "citations": int(record["citations"]) if record["citations"] else 0,
                    "impact_score": impact_score,
                    "similarity_score": affinity,
                    "method": "topic_similarity",
                }

            logger.debug(
                "topic_candidates_fetched",
                count=len(candidates),
            )

            return candidates

        except Exception as e:
            logger.warning(
                "topic_candidates_failed",
                paper_id=paper_id,
                error=str(e),
            )
            return {}

    # =========================================================================
    # Method 3: Author Collaboration Network
    # =========================================================================

    async def _get_author_based_candidates(
        self,
        paper_id: str,
        limit: int,
    ) -> dict[str, dict[str, Any]]:
        """Get candidate papers based on author collaboration.

        Args:
            paper_id: Source paper ID.
            limit: Maximum candidates to fetch.

        Returns:
            Dict mapping paper_id → candidate info with similarity_score.
        """
        logger.debug("fetching_author_candidates", paper_id=paper_id)

        try:
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_COAUTHOR_NETWORK_PAPERS,
                    paper_id=paper_id,
                    min_shared_authors=1,
                    limit=limit,
                )
                records = await result.data()

            candidates = {}
            for record in records:
                # Normalize by number of shared authors (max observed ~10)
                shared_count = int(record["shared_author_count"])
                similarity = min(shared_count / 3.0, 1.0)
                impact_score = (
                    float(record["impact_score"]) if record["impact_score"] else None
                )

                candidates[str(record["paper_id"])] = {
                    "title": str(record["title"]),
                    "year": int(record["year"]) if record["year"] else None,
                    "citations": int(record["citations"]) if record["citations"] else 0,
                    "impact_score": impact_score,
                    "similarity_score": similarity,
                    "method": "author_collaboration",
                    "shared_authors": list(record["shared_author_names"]),
                }

            logger.debug(
                "author_candidates_fetched",
                count=len(candidates),
            )

            return candidates

        except Exception as e:
            logger.warning(
                "author_candidates_failed",
                paper_id=paper_id,
                error=str(e),
            )
            return {}

    # =========================================================================
    # Method 4: Citation Velocity Similarity
    # =========================================================================

    async def _get_velocity_based_candidates(
        self,
        paper_id: str,
        limit: int,
    ) -> dict[str, dict[str, Any]]:
        """Get candidate papers with similar citation velocity.

        Args:
            paper_id: Source paper ID.
            limit: Maximum candidates to fetch.

        Returns:
            Dict mapping paper_id → candidate info with similarity_score.
        """
        logger.debug("fetching_velocity_candidates", paper_id=paper_id)

        try:
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_SIMILAR_VELOCITY_PAPERS,
                    paper_id=paper_id,
                    current_year=self.current_year,
                    max_velocity_diff=10.0,
                    limit=limit,
                )
                records = await result.data()

            candidates = {}
            for record in records:
                velocity = float(record["velocity"])
                velocity_diff = float(record["velocity_diff"])

                # Use exponential decay for similarity
                similarity = citation_velocity_similarity(
                    velocity, velocity - velocity_diff, max_diff=10.0
                )
                impact_score = (
                    float(record["impact_score"]) if record["impact_score"] else None
                )

                candidates[str(record["paper_id"])] = {
                    "title": str(record["title"]),
                    "year": int(record["year"]) if record["year"] else None,
                    "citations": int(record["citations"]) if record["citations"] else 0,
                    "impact_score": impact_score,
                    "similarity_score": similarity,
                    "method": "velocity_similarity",
                }

            logger.debug(
                "velocity_candidates_fetched",
                count=len(candidates),
            )

            return candidates

        except Exception as e:
            logger.warning(
                "velocity_candidates_failed",
                paper_id=paper_id,
                error=str(e),
            )
            return {}

    # =========================================================================
    # Score Aggregation and Filtering
    # =========================================================================

    def _aggregate_candidates(
        self,
        citation_candidates: dict[str, dict[str, Any]],
        topic_candidates: dict[str, dict[str, Any]],
        author_candidates: dict[str, dict[str, Any]],
        velocity_candidates: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Aggregate candidates from all methods with weighted scoring.

        Args:
            citation_candidates: Results from citation-based method.
            topic_candidates: Results from topic-based method.
            author_candidates: Results from author-based method.
            velocity_candidates: Results from velocity-based method.

        Returns:
            Dict mapping paper_id → aggregated candidate info.
        """
        aggregated: dict[str, dict[str, Any]] = {}

        # Collect all unique candidate IDs
        all_candidate_ids = set(
            list(citation_candidates.keys())
            + list(topic_candidates.keys())
            + list(author_candidates.keys())
            + list(velocity_candidates.keys())
        )

        for candidate_id in all_candidate_ids:
            # Get scores from each method (0.0 if not present)
            citation_score = citation_candidates.get(candidate_id, {}).get("similarity_score", 0.0)
            topic_score = topic_candidates.get(candidate_id, {}).get("similarity_score", 0.0)
            author_score = author_candidates.get(candidate_id, {}).get("similarity_score", 0.0)
            velocity_score = velocity_candidates.get(candidate_id, {}).get("similarity_score", 0.0)

            # Weighted combination
            combined_score = (
                self.CITATION_WEIGHT * citation_score
                + self.TOPIC_WEIGHT * topic_score
                + self.AUTHOR_WEIGHT * author_score
                + self.VELOCITY_WEIGHT * velocity_score
            )

            # Get metadata from any available source (prefer citation > topic > author > velocity)
            metadata = (
                citation_candidates.get(candidate_id)
                or topic_candidates.get(candidate_id)
                or author_candidates.get(candidate_id)
                or velocity_candidates.get(candidate_id)
                or {}
            )

            # Determine primary recommendation reason
            method_scores = {
                "citation_overlap": citation_score,
                "topic_similarity": topic_score,
                "author_collaboration": author_score,
                "velocity_similarity": velocity_score,
            }
            primary_method = max(method_scores, key=method_scores.get)  # type: ignore

            aggregated[candidate_id] = {
                "title": metadata.get("title", "Unknown"),
                "year": metadata.get("year"),
                "citations": metadata.get("citations", 0),
                "impact_score": metadata.get("impact_score"),
                "combined_score": combined_score,
                "recommendation_reason": primary_method,
                "component_scores": {
                    "citation": round(citation_score, 4),
                    "topic": round(topic_score, 4),
                    "author": round(author_score, 4),
                    "velocity": round(velocity_score, 4),
                },
            }

        return aggregated

    def _apply_diversity_filter(
        self,
        candidates: list[dict[str, Any]],
        diversity_factor: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Apply diversity filtering to avoid clustering same year/community.

        Args:
            candidates: List of candidate recommendations.
            diversity_factor: Penalty factor for clustered papers (0-1).

        Returns:
            Filtered and re-ranked candidates.
        """
        year_counts: dict[int | None, int] = defaultdict(int)
        filtered = []

        for candidate in candidates:
            year = candidate["year"]

            # Apply penalty if >3 papers from same year
            penalty = 1.0
            if year is not None and year_counts[year] >= 3:
                penalty = 1.0 - diversity_factor

            # Adjust combined score
            candidate["combined_score"] *= penalty
            year_counts[year] += 1

            filtered.append(candidate)

        # Re-sort after penalty
        filtered.sort(key=lambda x: x["combined_score"], reverse=True)

        return filtered

    def _apply_time_decay(
        self,
        candidates: list[dict[str, Any]],
        year_preference: int = 2020,
    ) -> list[dict[str, Any]]:
        """Apply time decay preference for recent papers.

        Args:
            candidates: List of candidate recommendations.
            year_preference: Year threshold for boosting recent papers.

        Returns:
            Candidates with adjusted scores based on recency.
        """
        for candidate in candidates:
            year = candidate["year"]

            if year is None:
                continue

            # Boost recent papers (>= year_preference)
            if year >= year_preference:
                recency_ratio = (year - year_preference) / (self.current_year - year_preference + 1)
                boost = 1.0 + 0.1 * recency_ratio
                candidate["combined_score"] *= boost

            # Penalize old papers (< year_preference)
            else:
                age_ratio = (year_preference - year) / year_preference
                penalty = 0.9 - 0.05 * age_ratio
                candidate["combined_score"] *= max(penalty, 0.5)

        # Re-sort after adjustment
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)

        return candidates

    # =========================================================================
    # Public API
    # =========================================================================

    async def get_paper_recommendations(
        self,
        paper_id: str,
        limit: int = 10,
        min_similarity: float = 0.3,
        year_preference: int = 2020,
        diversity_factor: float = 0.3,
    ) -> list[dict[str, Any]]:
        """Get personalized paper recommendations using collaborative filtering.

        Combines 4 similarity methods with weighted scoring, diversity filtering,
        and time decay preferences.

        Args:
            paper_id: Source paper ID to find recommendations for.
            limit: Maximum number of recommendations to return.
            min_similarity: Minimum combined similarity score (0-1).
            year_preference: Boost papers published after this year.
            diversity_factor: Penalty for clustering (0-1, default 0.3).

        Returns:
            List of recommendation dicts sorted by combined score.

        Raises:
            CollaborativeFilterError: If recommendation generation fails.
        """
        logger.info(
            "get_paper_recommendations",
            paper_id=paper_id,
            limit=limit,
            min_similarity=min_similarity,
        )

        try:
            # Fetch candidates from all 4 methods in parallel for 3-4x speedup
            (
                citation_candidates,
                topic_candidates,
                author_candidates,
                velocity_candidates,
            ) = await asyncio.gather(
                self._get_citation_based_candidates(paper_id, limit=limit * 2),
                self._get_topic_based_candidates(paper_id, limit=limit * 2),
                self._get_author_based_candidates(paper_id, limit=limit * 2),
                self._get_velocity_based_candidates(paper_id, limit=limit * 2),
            )

            # Aggregate candidates with weighted scoring
            aggregated = self._aggregate_candidates(
                citation_candidates,
                topic_candidates,
                author_candidates,
                velocity_candidates,
            )

            # Convert to list and filter by min_similarity
            candidates = [
                {"paper_id": pid, **data}
                for pid, data in aggregated.items()
                if data["combined_score"] >= min_similarity
            ]

            if not candidates:
                logger.info("no_recommendations_found", paper_id=paper_id)
                return []

            # Sort by combined score
            candidates.sort(key=lambda x: x["combined_score"], reverse=True)

            # Apply diversity filtering
            candidates = self._apply_diversity_filter(candidates, diversity_factor)

            # Apply time decay preference
            candidates = self._apply_time_decay(candidates, year_preference)

            # Take top N
            recommendations = candidates[:limit]

            # Format final output
            final_recommendations = []
            for rec in recommendations:
                final_recommendations.append(
                    {
                        "paper_id": rec["paper_id"],
                        "title": rec["title"],
                        "year": rec["year"],
                        "citations": rec["citations"],
                        "impact_score": rec["impact_score"],
                        "similarity_score": round(rec["combined_score"], 4),
                        "recommendation_reason": rec["recommendation_reason"],
                        "component_scores": rec["component_scores"],
                    }
                )

            logger.info(
                "recommendations_generated",
                paper_id=paper_id,
                recommendations_count=len(final_recommendations),
                avg_similarity=round(
                    sum(r["similarity_score"] for r in final_recommendations)
                    / len(final_recommendations),
                    4,
                )
                if final_recommendations
                else 0.0,
            )

            return final_recommendations

        except Exception as e:
            logger.error(
                "get_paper_recommendations_failed",
                paper_id=paper_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise CollaborativeFilterError(
                f"Failed to generate recommendations for {paper_id}: {e}"
            ) from e
