"""Content-based recommendation engine using topic similarity.

This module implements content-based filtering by comparing papers based on
their topic distributions. Papers with similar topics are recommended.

The topic similarity is calculated using weighted topic affinity scores,
where topic assignment strengths from OpenAlex are used as weights.

Usage:
    >>> from graphlit.recommendations.content_based import ContentBasedRecommender
    >>> from graphlit.database.neo4j_client import Neo4jClient
    >>> from graphlit.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> async with Neo4jClient(settings.neo4j) as client:
    ...     recommender = ContentBasedRecommender(client)
    ...     recommendations = await recommender.recommend_by_topic_similarity(
    ...         paper_id="W123456",
    ...         limit=10,
    ...         min_similarity=0.5
    ...     )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from graphlit.database.neo4j_client import Neo4jClient

from graphlit.database import queries
from graphlit.recommendations.similarity import topic_affinity_score

logger = structlog.get_logger(__name__)


class ContentBasedRecommenderError(Exception):
    """Raised when content-based recommendation operations fail."""

    pass


class ContentBasedRecommender:
    """Content-based recommendation engine using topic similarity.

    Recommends papers based on shared topics and topic distribution similarity.
    Uses OpenAlex topic assignments with confidence scores.

    Attributes:
        client: Neo4jClient for database operations.
    """

    def __init__(self, client: Neo4jClient) -> None:
        """Initialize content-based recommender.

        Args:
            client: Connected Neo4jClient instance.
        """
        self.client = client

    async def get_paper_topics(
        self, paper_id: str
    ) -> list[tuple[str, float]]:
        """Fetch topic vector for a paper.

        Args:
            paper_id: OpenAlex paper ID.

        Returns:
            List of (topic_id, score) tuples sorted by score descending.

        Raises:
            ContentBasedRecommenderError: If paper not found or query fails.
        """
        logger.debug("fetching_paper_topics", paper_id=paper_id)

        try:
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_PAPER_TOPICS,
                    paper_id=paper_id,
                )
                records = await result.values()

                if not records:
                    raise ContentBasedRecommenderError(
                        f"Paper not found or has no topics: {paper_id}"
                    )

                topics = [(str(rec[0]), float(rec[2])) for rec in records]

                logger.debug(
                    "paper_topics_fetched",
                    paper_id=paper_id,
                    topics_count=len(topics),
                )

                return topics

        except Exception as e:
            logger.error(
                "get_paper_topics_failed",
                paper_id=paper_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ContentBasedRecommenderError(
                f"Failed to fetch topics for paper {paper_id}: {e}"
            ) from e

    async def recommend_by_topic_similarity(
        self,
        paper_id: str,
        limit: int = 10,
        min_similarity: float = 0.5,
        min_shared_topics: int = 1,
    ) -> list[dict[str, Any]]:
        """Recommend papers with similar topic distributions.

        Algorithm:
        1. Fetch target paper's topic vector
        2. Query papers with overlapping topics (min_shared_topics)
        3. For each candidate, calculate topic affinity score
        4. Filter by min_similarity threshold
        5. Sort by similarity * impact_score
        6. Return top N with metadata

        Args:
            paper_id: OpenAlex paper ID to find similar papers for.
            limit: Maximum number of recommendations to return.
            min_similarity: Minimum topic affinity score (0-1).
            min_shared_topics: Minimum number of shared topics.

        Returns:
            List of recommendation dicts with keys:
            - paper_id: OpenAlex paper ID
            - title: Paper title
            - year: Publication year
            - citations: Citation count
            - impact_score: Predictive Impact Score (0-100) or None
            - similarity_score: Topic affinity score (0-1)
            - recommendation_reason: "topic_similarity"
            - shared_topics: Number of overlapping topics

        Raises:
            ContentBasedRecommenderError: If recommendation fails.
        """
        logger.info(
            "recommend_by_topic_similarity",
            paper_id=paper_id,
            limit=limit,
            min_similarity=min_similarity,
        )

        try:
            # Fetch target paper's topics
            source_topics = await self.get_paper_topics(paper_id)

            # Query candidates with overlapping topics
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_SIMILAR_TOPIC_PAPERS,
                    paper_id=paper_id,
                    min_shared_topics=min_shared_topics,
                    limit=limit * 3,  # Over-fetch to allow filtering
                )
                records = await result.data()

                if not records:
                    logger.info(
                        "no_topic_similar_papers",
                        paper_id=paper_id,
                    )
                    return []

            # Calculate topic affinity for each candidate
            recommendations: list[dict[str, Any]] = []

            for record in records:
                candidate_topics_raw = record["target_topics"]

                # Convert Neo4j map list to tuples
                candidate_topics = [
                    (str(t["topic_id"]), float(t["score"]))
                    for t in candidate_topics_raw
                ]

                # Calculate topic affinity
                affinity = topic_affinity_score(source_topics, candidate_topics)

                # Filter by minimum similarity
                if affinity < min_similarity:
                    continue

                # Build recommendation
                impact_score = (
                    float(record["impact_score"]) if record["impact_score"] else None
                )
                recommendations.append(
                    {
                        "paper_id": str(record["paper_id"]),
                        "title": str(record["title"]),
                        "year": int(record["year"]) if record["year"] else None,
                        "citations": int(record["citations"]) if record["citations"] else 0,
                        "impact_score": impact_score,
                        "similarity_score": round(affinity, 4),
                        "recommendation_reason": "topic_similarity",
                        "shared_topics": int(record["shared_topic_count"]),
                    }
                )

            # Sort by combined score: similarity * (impact_score / 100)
            # Papers with high similarity AND high impact ranked highest
            recommendations.sort(
                key=lambda x: (
                    x["similarity_score"]
                    * (x["impact_score"] / 100.0 if x["impact_score"] else 0.5)
                ),
                reverse=True,
            )

            # Take top N
            recommendations = recommendations[:limit]

            logger.info(
                "topic_recommendations_generated",
                paper_id=paper_id,
                recommendations_count=len(recommendations),
                avg_similarity=round(
                    sum(r["similarity_score"] for r in recommendations)
                    / len(recommendations),
                    4,
                )
                if recommendations
                else 0.0,
            )

            return recommendations

        except ContentBasedRecommenderError:
            raise
        except Exception as e:
            logger.error(
                "recommend_by_topic_similarity_failed",
                paper_id=paper_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ContentBasedRecommenderError(
                f"Failed to generate topic-based recommendations: {e}"
            ) from e
