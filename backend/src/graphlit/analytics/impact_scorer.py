"""Predictive Impact Score (PIS) calculation for research papers.

This module implements a multi-component ML scoring algorithm to predict
paper impact based on graph metrics, citation patterns, and author reputation.

The PIS consists of 4 weighted components:
1. PageRank Centrality (30%) - Graph importance score
2. Citation Velocity (25%) - Citations per year since publication
3. Author Reputation (25%) - Average h-index proxy from authors' other papers
4. Topic Momentum (20%) - Growth rate of paper's topics

Scores are normalized to 0-100 scale, with 100 = highest predicted impact.

Usage:
    >>> from graphlit.analytics.impact_scorer import ImpactScorer
    >>> from graphlit.config import get_settings
    >>> from graphlit.database.neo4j_client import Neo4jClient
    >>> from graphlit.database.graph_algorithms import GraphAlgorithms
    >>>
    >>> settings = get_settings()
    >>> async with Neo4jClient(settings.neo4j) as client:
    ...     gds = GraphAlgorithms(client, settings.analytics)
    ...     scorer = ImpactScorer(client, gds, settings.analytics)
    ...
    ...     # Calculate all scores and rank papers
    ...     await scorer.calculate_all_scores()
    ...     top_papers = await scorer.rank_papers(limit=20)
    ...
    ...     # Save scores to database
    ...     await scorer.save_scores_to_neo4j()
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from graphlit.config import AnalyticsSettings
    from graphlit.database.graph_algorithms import GraphAlgorithms
    from graphlit.database.neo4j_client import Neo4jClient

from graphlit.database import queries

logger = structlog.get_logger(__name__)


class ImpactScoringError(Exception):
    """Raised when impact scoring operations fail."""

    pass


class ImpactScorer:
    """Predictive Impact Score calculator for research papers.

    Calculates multi-component impact scores using graph algorithms,
    citation patterns, and author reputation metrics.

    Attributes:
        client: Neo4jClient for database operations.
        gds: GraphAlgorithms wrapper for GDS operations.
        settings: Analytics configuration settings.
        current_year: Current year for velocity calculations.
        scores: Cache of calculated component scores.
    """

    def __init__(
        self,
        client: Neo4jClient,
        gds: GraphAlgorithms,
        settings: AnalyticsSettings,
    ) -> None:
        """Initialize ImpactScorer.

        Args:
            client: Connected Neo4jClient instance.
            gds: GraphAlgorithms instance for GDS operations.
            settings: Analytics configuration settings.
        """
        self.client = client
        self.gds = gds
        self.settings = settings
        self.current_year = datetime.now().year

        # Cache for component scores: paper_id → score
        self.scores: dict[str, dict[str, float]] = {}

    # =========================================================================
    # Component 1: PageRank Centrality (30%)
    # =========================================================================

    async def calculate_pagerank_centrality(self) -> dict[str, float]:
        """Calculate PageRank centrality for all papers.

        Uses Neo4j GDS PageRank algorithm to measure graph importance.
        Scores are already normalized to 0-1 by GraphAlgorithms.

        Returns:
            Dictionary mapping paper_id → normalized_pagerank (0-1).

        Raises:
            ImpactScoringError: If PageRank calculation fails.
        """
        logger.info("calculating_pagerank_centrality")

        try:
            # Ensure graph projection exists
            if not await self.gds.graph_exists():
                logger.info("projecting_citation_graph_for_pagerank")
                await self.gds.project_citation_graph()

            # Calculate PageRank (returns normalized 0-1 scores)
            pagerank_scores = await self.gds.calculate_pagerank()

            logger.info(
                "pagerank_centrality_completed",
                papers_scored=len(pagerank_scores),
            )

            return pagerank_scores

        except Exception as e:
            logger.error("pagerank_centrality_failed", error=str(e))
            raise ImpactScoringError(f"Failed to calculate PageRank: {e}") from e

    # =========================================================================
    # Component 2: Citation Velocity (25%)
    # =========================================================================

    async def calculate_citation_velocity(self) -> dict[str, float]:
        """Calculate citation velocity (citations per year since publication).

        Velocity = total_citations / (current_year - publication_year + 1)
        The +1 prevents division by zero for papers published this year.

        Returns:
            Dictionary mapping paper_id → normalized_velocity (0-1).

        Raises:
            ImpactScoringError: If velocity calculation fails.
        """
        logger.info("calculating_citation_velocity", current_year=self.current_year)

        query = """
        MATCH (p:Paper)
        WHERE p.year IS NOT NULL AND p.citations IS NOT NULL
        WITH p,
             p.citations AS total_citations,
             ($current_year - p.year + 1) AS years_since_publication
        WHERE years_since_publication > 0
        WITH p,
             toFloat(total_citations) / toFloat(years_since_publication) AS velocity
        WITH max(velocity) AS max_velocity
        MATCH (p:Paper)
        WHERE p.year IS NOT NULL AND p.citations IS NOT NULL
        WITH p,
             p.citations AS total_citations,
             ($current_year - p.year + 1) AS years_since_publication,
             max_velocity
        WHERE years_since_publication > 0
        WITH p,
             toFloat(total_citations) / toFloat(years_since_publication) AS velocity,
             max_velocity
        RETURN p.openalex_id AS paper_id,
               CASE WHEN max_velocity > 0
                    THEN velocity / max_velocity
                    ELSE 0.0
               END AS normalized_velocity
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query, current_year=self.current_year)
                records = await result.values()

                velocities = {str(rec[0]): float(rec[1]) for rec in records}

            logger.info(
                "citation_velocity_completed",
                papers_scored=len(velocities),
                max_velocity=max(velocities.values()) if velocities else 0.0,
            )

            return velocities

        except Exception as e:
            logger.error("citation_velocity_failed", error=str(e))
            raise ImpactScoringError(f"Failed to calculate citation velocity: {e}") from e

    # =========================================================================
    # Component 3: Author Reputation (25%)
    # =========================================================================

    async def calculate_author_reputation_score(self) -> dict[str, float]:
        """Calculate author reputation score (h-index proxy).

        For each paper, computes the average citation count of authors' other
        papers. This serves as a proxy for author h-index / reputation.

        Formula for paper P:
        - Find all authors A of P
        - For each author A, find all other papers by A
        - Compute avg_citations(other papers by A)
        - author_reputation(P) = avg(avg_citations across all authors of P)

        Returns:
            Dictionary mapping paper_id → normalized_reputation (0-1).

        Raises:
            ImpactScoringError: If reputation calculation fails.
        """
        logger.info("calculating_author_reputation")

        query = """
        MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
        WITH p, collect(a) AS authors
        UNWIND authors AS author
        OPTIONAL MATCH (author)<-[:AUTHORED_BY]-(other_paper:Paper)
        WHERE other_paper <> p AND other_paper.citations IS NOT NULL
        WITH p, author, avg(other_paper.citations) AS author_avg_citations
        WITH p, avg(author_avg_citations) AS paper_author_reputation
        WITH max(paper_author_reputation) AS max_reputation
        MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
        WITH p, collect(a) AS authors, max_reputation
        UNWIND authors AS author
        OPTIONAL MATCH (author)<-[:AUTHORED_BY]-(other_paper:Paper)
        WHERE other_paper <> p AND other_paper.citations IS NOT NULL
        WITH p, author, avg(other_paper.citations) AS author_avg_citations, max_reputation
        WITH p, avg(author_avg_citations) AS paper_author_reputation, max_reputation
        WHERE paper_author_reputation IS NOT NULL
        RETURN p.openalex_id AS paper_id,
               CASE WHEN max_reputation > 0
                    THEN paper_author_reputation / max_reputation
                    ELSE 0.0
               END AS normalized_reputation
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query)
                records = await result.values()

                reputations = {str(rec[0]): float(rec[1]) for rec in records}

            logger.info(
                "author_reputation_completed",
                papers_scored=len(reputations),
            )

            return reputations

        except Exception as e:
            logger.error("author_reputation_failed", error=str(e))
            raise ImpactScoringError(f"Failed to calculate author reputation: {e}") from e

    # =========================================================================
    # Component 4: Topic Momentum (20%)
    # =========================================================================

    async def calculate_topic_momentum(self) -> dict[str, float]:
        """Calculate topic momentum (topic growth rate).

        Measures whether a paper's topics are trending upward by comparing
        paper counts in recent years vs older years.

        Momentum = (papers in topic 2020+) / (papers in topic pre-2020 + 1)
        Higher momentum = topic is growing (more recent papers)

        Returns:
            Dictionary mapping paper_id → normalized_momentum (0-1).

        Raises:
            ImpactScoringError: If momentum calculation fails.
        """
        logger.info("calculating_topic_momentum")

        query = """
        MATCH (p:Paper)-[r:BELONGS_TO_TOPIC]->(t:Topic)
        WITH p, collect(t) AS topics
        UNWIND topics AS topic
        MATCH (topic)<-[:BELONGS_TO_TOPIC]-(topic_paper:Paper)
        WHERE topic_paper.year IS NOT NULL
        WITH p, topic,
             sum(CASE WHEN topic_paper.year >= 2020 THEN 1 ELSE 0 END) AS recent_count,
             sum(CASE WHEN topic_paper.year < 2020 THEN 1 ELSE 0 END) AS old_count
        WITH p, topic,
             toFloat(recent_count) / toFloat(old_count + 1) AS topic_momentum
        WITH p, avg(topic_momentum) AS paper_momentum
        WITH max(paper_momentum) AS max_momentum
        MATCH (p:Paper)-[r:BELONGS_TO_TOPIC]->(t:Topic)
        WITH p, collect(t) AS topics, max_momentum
        UNWIND topics AS topic
        MATCH (topic)<-[:BELONGS_TO_TOPIC]-(topic_paper:Paper)
        WHERE topic_paper.year IS NOT NULL
        WITH p, topic,
             sum(CASE WHEN topic_paper.year >= 2020 THEN 1 ELSE 0 END) AS recent_count,
             sum(CASE WHEN topic_paper.year < 2020 THEN 1 ELSE 0 END) AS old_count,
             max_momentum
        WITH p, topic,
             toFloat(recent_count) / toFloat(old_count + 1) AS topic_momentum,
             max_momentum
        WITH p, avg(topic_momentum) AS paper_momentum, max_momentum
        WHERE paper_momentum IS NOT NULL
        RETURN p.openalex_id AS paper_id,
               CASE WHEN max_momentum > 0
                    THEN paper_momentum / max_momentum
                    ELSE 0.0
               END AS normalized_momentum
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query)
                records = await result.values()

                momentums = {str(rec[0]): float(rec[1]) for rec in records}

            logger.info(
                "topic_momentum_completed",
                papers_scored=len(momentums),
            )

            return momentums

        except Exception as e:
            logger.error("topic_momentum_failed", error=str(e))
            raise ImpactScoringError(f"Failed to calculate topic momentum: {e}") from e

    # =========================================================================
    # Composite Score Calculation
    # =========================================================================

    async def calculate_all_scores(self) -> None:
        """Calculate all 4 component scores and cache results.

        This method runs all component calculations in sequence and stores
        results in self.scores for later composite score computation.

        Raises:
            ImpactScoringError: If any component calculation fails.
        """
        logger.info("calculating_all_impact_scores")

        try:
            # Calculate all components
            pagerank = await self.calculate_pagerank_centrality()
            velocity = await self.calculate_citation_velocity()
            reputation = await self.calculate_author_reputation_score()
            momentum = await self.calculate_topic_momentum()

            # Find all paper IDs that have at least one score
            all_paper_ids = set(pagerank.keys()) | set(velocity.keys()) | set(reputation.keys()) | set(momentum.keys())

            # Build composite score cache
            self.scores = {}
            for paper_id in all_paper_ids:
                self.scores[paper_id] = {
                    "pagerank": pagerank.get(paper_id, 0.0),
                    "citation_velocity": velocity.get(paper_id, 0.0),
                    "author_reputation": reputation.get(paper_id, 0.0),
                    "topic_momentum": momentum.get(paper_id, 0.0),
                }

            logger.info(
                "all_impact_scores_calculated",
                total_papers=len(self.scores),
            )

        except Exception as e:
            logger.error("impact_score_calculation_failed", error=str(e))
            raise ImpactScoringError(f"Failed to calculate impact scores: {e}") from e

    def compute_composite_score(self, paper_id: str) -> float:
        """Compute weighted composite PIS for a single paper.

        Formula:
        PIS = (w1 * pagerank) + (w2 * velocity) + (w3 * reputation) + (w4 * momentum)
        Scaled to 0-100.

        Args:
            paper_id: OpenAlex paper ID.

        Returns:
            Composite impact score (0-100).

        Raises:
            ImpactScoringError: If scores not calculated or paper not found.
        """
        if not self.scores:
            raise ImpactScoringError(
                "Scores not calculated. Call calculate_all_scores() first."
            )

        if paper_id not in self.scores:
            raise ImpactScoringError(f"No scores found for paper: {paper_id}")

        components = self.scores[paper_id]

        # Weighted combination (weights are validated to sum to 1.0 in config)
        composite = (
            self.settings.pagerank_weight * components["pagerank"]
            + self.settings.citation_velocity_weight * components["citation_velocity"]
            + self.settings.author_reputation_weight * components["author_reputation"]
            + self.settings.topic_momentum_weight * components["topic_momentum"]
        )

        # Scale to 0-100
        return composite * 100.0

    # =========================================================================
    # Ranking and Persistence
    # =========================================================================

    async def rank_papers(self, limit: int = 20) -> list[dict[str, Any]]:
        """Rank papers by Predictive Impact Score.

        Args:
            limit: Maximum number of top papers to return.

        Returns:
            List of dicts with keys:
            - paper_id: OpenAlex paper ID
            - title: Paper title
            - year: Publication year
            - citations: Total citations
            - impact_score: Composite PIS (0-100)
            - pagerank: Component 1 score (0-1)
            - citation_velocity: Component 2 score (0-1)
            - author_reputation: Component 3 score (0-1)
            - topic_momentum: Component 4 score (0-1)

        Raises:
            ImpactScoringError: If scores not calculated.
        """
        if not self.scores:
            raise ImpactScoringError(
                "Scores not calculated. Call calculate_all_scores() first."
            )

        logger.info("ranking_papers", limit=limit)

        try:
            # Compute composite scores for all papers
            paper_scores: list[tuple[str, float]] = []
            for paper_id in self.scores:
                composite = self.compute_composite_score(paper_id)
                paper_scores.append((paper_id, composite))

            # Sort by impact score descending
            paper_scores.sort(key=lambda x: x[1], reverse=True)

            # Take top N
            top_paper_ids = [paper_id for paper_id, _ in paper_scores[:limit]]

            # Fetch paper metadata
            query = """
            MATCH (p:Paper)
            WHERE p.openalex_id IN $paper_ids
            RETURN p.openalex_id AS paper_id,
                   p.title AS title,
                   p.year AS year,
                   p.citations AS citations
            """

            async with self.client.session() as session:
                result = await session.run(query, paper_ids=top_paper_ids)
                records = await result.values()

                paper_metadata = {
                    str(rec[0]): {
                        "paper_id": str(rec[0]),
                        "title": str(rec[1]),
                        "year": int(rec[2]) if rec[2] else None,
                        "citations": int(rec[3]) if rec[3] else 0,
                    }
                    for rec in records
                }

            # Build ranked results
            ranked_papers: list[dict[str, Any]] = []
            for paper_id, impact_score in paper_scores[:limit]:
                if paper_id in paper_metadata:
                    paper = paper_metadata[paper_id]
                    components = self.scores[paper_id]

                    ranked_papers.append(
                        {
                            "paper_id": paper["paper_id"],
                            "title": paper["title"],
                            "year": paper["year"],
                            "citations": paper["citations"],
                            "impact_score": round(impact_score, 2),
                            "pagerank": round(components["pagerank"], 4),
                            "citation_velocity": round(components["citation_velocity"], 4),
                            "author_reputation": round(components["author_reputation"], 4),
                            "topic_momentum": round(components["topic_momentum"], 4),
                        }
                    )

            logger.info(
                "papers_ranked",
                total_ranked=len(ranked_papers),
            )

            return ranked_papers

        except Exception as e:
            logger.error("paper_ranking_failed", error=str(e))
            raise ImpactScoringError(f"Failed to rank papers: {e}") from e

    async def save_scores_to_neo4j(self) -> int:
        """Save all calculated scores to Neo4j Paper nodes.

        Writes composite impact score and all 4 component scores to the
        database using the UPDATE_PAPER_IMPACT_SCORE query.

        Returns:
            Number of papers updated.

        Raises:
            ImpactScoringError: If scores not calculated or save fails.
        """
        if not self.scores:
            raise ImpactScoringError(
                "Scores not calculated. Call calculate_all_scores() first."
            )

        logger.info("saving_scores_to_neo4j", total_papers=len(self.scores))

        try:
            updated_count = 0

            async with self.client.session() as session:
                for paper_id in self.scores:
                    components = self.scores[paper_id]
                    impact_score = self.compute_composite_score(paper_id)

                    result = await session.run(
                        queries.UPDATE_PAPER_IMPACT_SCORE,
                        paper_id=paper_id,
                        impact_score=impact_score,
                        citation_velocity=components["citation_velocity"],
                        author_reputation=components["author_reputation"],
                        topic_momentum=components["topic_momentum"],
                    )

                    # Check if update succeeded
                    record = await result.single()
                    if record:
                        updated_count += 1

            logger.info(
                "scores_saved_to_neo4j",
                papers_updated=updated_count,
            )

            return updated_count

        except Exception as e:
            logger.error("score_persistence_failed", error=str(e))
            raise ImpactScoringError(f"Failed to save scores to Neo4j: {e}") from e
