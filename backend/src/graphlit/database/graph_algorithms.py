"""Neo4j Graph Data Science (GDS) algorithm wrappers.

This module provides async wrappers for GDS graph algorithms including:
- Graph projection (creating in-memory graphs from Neo4j)
- Community detection (Louvain)
- Centrality metrics (PageRank, Betweenness)
- Graph cleanup

Usage:
    >>> from graphlit.database.graph_algorithms import GraphAlgorithms
    >>> from graphlit.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> async with Neo4jClient(settings.neo4j) as client:
    ...     gds = GraphAlgorithms(client, settings.analytics)
    ...     await gds.project_citation_graph()
    ...     communities = await gds.detect_communities_louvain()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from neo4j.exceptions import Neo4jError

if TYPE_CHECKING:
    from graphlit.config import AnalyticsSettings
    from graphlit.database.neo4j_client import Neo4jClient

logger = structlog.get_logger(__name__)


class GDSError(Exception):
    """Raised when a GDS operation fails."""

    pass


class GraphAlgorithms:
    """Wrapper for Neo4j Graph Data Science operations.

    Provides type-safe async methods for graph projections and algorithms.
    Handles GDS-specific error cases and logging.

    Attributes:
        client: Neo4jClient instance for database operations.
        settings: AnalyticsSettings for algorithm parameters.
    """

    def __init__(self, client: Neo4jClient, settings: AnalyticsSettings) -> None:
        """Initialize GraphAlgorithms wrapper.

        Args:
            client: Connected Neo4jClient instance.
            settings: Analytics configuration settings.
        """
        self.client = client
        self.settings = settings
        self.graph_name = settings.gds_graph_name

    # =========================================================================
    # Graph Projection Operations
    # =========================================================================

    async def graph_exists(self) -> bool:
        """Check if the GDS in-memory graph exists.

        Returns:
            True if graph projection exists in GDS catalog.
        """
        query = """
        CALL gds.graph.exists($graphName)
        YIELD exists
        RETURN exists
        """
        try:
            async with self.client.session() as session:
                result = await session.run(query, graphName=self.graph_name)
                record = await result.single()
                return record is not None and record["exists"]
        except Neo4jError as e:
            logger.error("graph_exists_check_failed", error=str(e))
            return False

    async def drop_graph_if_exists(self) -> bool:
        """Drop the GDS in-memory graph if it exists.

        Returns:
            True if graph was dropped successfully or didn't exist.
        """
        if not await self.graph_exists():
            logger.debug("graph_does_not_exist", graph_name=self.graph_name)
            return True

        query = """
        CALL gds.graph.drop($graphName, false)
        YIELD graphName
        RETURN graphName
        """
        try:
            async with self.client.session() as session:
                result = await session.run(query, graphName=self.graph_name)
                record = await result.single()
                success = record is not None
                if success:
                    logger.info("graph_dropped", graph_name=self.graph_name)
                return success
        except Neo4jError as e:
            logger.error("graph_drop_failed", error=str(e))
            raise GDSError(f"Failed to drop graph: {e}") from e

    async def project_citation_graph(self) -> dict[str, Any]:
        """Project citation network into GDS in-memory graph.

        Creates a native projection with:
        - Nodes: All Paper nodes
        - Relationships: CITES relationships (directed)
        - Node properties: year, citations (for filtering/weighting)

        Returns:
            Dictionary with projection statistics:
            - nodeCount: Number of nodes projected
            - relationshipCount: Number of relationships projected
            - projectMillis: Time taken for projection

        Raises:
            GDSError: If projection fails.
        """
        # Drop existing graph if present
        await self.drop_graph_if_exists()

        query = """
        CALL gds.graph.project(
            $graphName,
            'Paper',
            'CITES',
            {
                nodeProperties: ['year', 'citations'],
                relationshipProperties: []
            }
        )
        YIELD graphName, nodeCount, relationshipCount, projectMillis
        RETURN graphName, nodeCount, relationshipCount, projectMillis
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query, graphName=self.graph_name)
                record = await result.single()

                if record is None:
                    raise GDSError("Graph projection returned no results")

                stats = {
                    "graphName": record["graphName"],
                    "nodeCount": record["nodeCount"],
                    "relationshipCount": record["relationshipCount"],
                    "projectMillis": record["projectMillis"],
                }

                logger.info(
                    "graph_projected",
                    graph_name=stats["graphName"],
                    nodes=stats["nodeCount"],
                    relationships=stats["relationshipCount"],
                    duration_ms=stats["projectMillis"],
                )

                return stats

        except Neo4jError as e:
            logger.error("graph_projection_failed", error=str(e))
            raise GDSError(f"Failed to project citation graph: {e}") from e

    # =========================================================================
    # Community Detection (Louvain)
    # =========================================================================

    async def detect_communities_louvain(self) -> dict[str, int]:
        """Detect communities using Louvain algorithm.

        Runs GDS Louvain algorithm on the projected citation graph and writes
        results back to Neo4j as a 'community' property on Paper nodes.

        Returns:
            Dictionary mapping paper_id (OpenAlex ID) → community_id (int).
            Community IDs are sequential integers starting from 0.

        Raises:
            GDSError: If Louvain algorithm fails or graph doesn't exist.

        Example:
            >>> communities = await gds.detect_communities_louvain()
            >>> communities
            {'W123': 0, 'W456': 0, 'W789': 1, ...}  # Papers W123, W456 in community 0
        """
        # Ensure graph exists
        if not await self.graph_exists():
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. "
                "Call project_citation_graph() first."
            )

        # Run Louvain algorithm with write mode
        query = """
        CALL gds.louvain.write(
            $graphName,
            {
                writeProperty: 'community',
                maxIterations: $maxIterations,
                tolerance: $tolerance,
                includeIntermediateCommunities: false
            }
        )
        YIELD communityCount, modularity, ranLevels, computeMillis, writeMillis
        RETURN communityCount, modularity, ranLevels, computeMillis, writeMillis
        """

        try:
            async with self.client.session() as session:
                result = await session.run(
                    query,
                    graphName=self.graph_name,
                    maxIterations=self.settings.louvain_max_iterations,
                    tolerance=self.settings.louvain_tolerance,
                )
                record = await result.single()

                if record is None:
                    raise GDSError("Louvain algorithm returned no results")

                logger.info(
                    "louvain_completed",
                    communities=record["communityCount"],
                    modularity=record["modularity"],
                    levels=record["ranLevels"],
                    compute_ms=record["computeMillis"],
                    write_ms=record["writeMillis"],
                )

        except Neo4jError as e:
            logger.error("louvain_algorithm_failed", error=str(e))
            raise GDSError(f"Louvain algorithm failed: {e}") from e

        # Fetch all paper → community mappings
        fetch_query = """
        MATCH (p:Paper)
        WHERE p.community IS NOT NULL
        RETURN p.openalex_id AS paper_id, p.community AS community_id
        ORDER BY p.community, p.openalex_id
        """

        try:
            async with self.client.session() as session:
                result = await session.run(fetch_query)
                records = await result.values()

                communities = {str(rec[0]): int(rec[1]) for rec in records}

                logger.info(
                    "communities_fetched",
                    total_papers=len(communities),
                    unique_communities=len(set(communities.values())),
                )

                return communities

        except Neo4jError as e:
            logger.error("community_fetch_failed", error=str(e))
            raise GDSError(f"Failed to fetch community assignments: {e}") from e

    # =========================================================================
    # Centrality Metrics (PageRank)
    # =========================================================================

    async def calculate_pagerank(self) -> dict[str, float]:
        """Calculate PageRank centrality for all papers.

        Runs GDS PageRank algorithm and writes scores back to Neo4j as
        'pagerank' property on Paper nodes.

        Returns:
            Dictionary mapping paper_id → pagerank_score (0.0 to 1.0).
            Scores are normalized so the maximum score is 1.0.

        Raises:
            GDSError: If PageRank algorithm fails or graph doesn't exist.
        """
        if not await self.graph_exists():
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. "
                "Call project_citation_graph() first."
            )

        query = """
        CALL gds.pageRank.write(
            $graphName,
            {
                writeProperty: 'pagerank',
                dampingFactor: $dampingFactor,
                maxIterations: $maxIterations,
                tolerance: 0.0001
            }
        )
        YIELD ranIterations, didConverge, computeMillis, writeMillis
        RETURN ranIterations, didConverge, computeMillis, writeMillis
        """

        try:
            async with self.client.session() as session:
                result = await session.run(
                    query,
                    graphName=self.graph_name,
                    dampingFactor=self.settings.pagerank_damping_factor,
                    maxIterations=self.settings.pagerank_max_iterations,
                )
                record = await result.single()

                if record is None:
                    raise GDSError("PageRank algorithm returned no results")

                logger.info(
                    "pagerank_completed",
                    iterations=record["ranIterations"],
                    converged=record["didConverge"],
                    compute_ms=record["computeMillis"],
                    write_ms=record["writeMillis"],
                )

        except Neo4jError as e:
            logger.error("pagerank_algorithm_failed", error=str(e))
            raise GDSError(f"PageRank algorithm failed: {e}") from e

        # Fetch and normalize scores
        fetch_query = """
        MATCH (p:Paper)
        WHERE p.pagerank IS NOT NULL
        WITH max(p.pagerank) AS max_score
        MATCH (p:Paper)
        WHERE p.pagerank IS NOT NULL
        RETURN p.openalex_id AS paper_id,
               p.pagerank / max_score AS normalized_score
        ORDER BY normalized_score DESC
        """

        try:
            async with self.client.session() as session:
                result = await session.run(fetch_query)
                records = await result.values()

                scores = {str(rec[0]): float(rec[1]) for rec in records}

                logger.info(
                    "pagerank_scores_fetched",
                    total_papers=len(scores),
                    max_score=max(scores.values()) if scores else 0.0,
                    min_score=min(scores.values()) if scores else 0.0,
                )

                return scores

        except Neo4jError as e:
            logger.error("pagerank_fetch_failed", error=str(e))
            raise GDSError(f"Failed to fetch PageRank scores: {e}") from e

    # =========================================================================
    # Betweenness Centrality (for Bridging Papers)
    # =========================================================================

    async def calculate_betweenness_centrality(self) -> dict[str, float]:
        """Calculate betweenness centrality for finding bridging papers.

        Betweenness centrality measures how often a node appears on shortest
        paths between other nodes. High betweenness = bridging communities.

        Returns:
            Dictionary mapping paper_id → betweenness_score (normalized 0-1).

        Raises:
            GDSError: If algorithm fails or graph doesn't exist.
        """
        if not await self.graph_exists():
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. "
                "Call project_citation_graph() first."
            )

        query = """
        CALL gds.betweenness.write(
            $graphName,
            {
                writeProperty: 'betweenness'
            }
        )
        YIELD computeMillis, writeMillis
        RETURN computeMillis, writeMillis
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query, graphName=self.graph_name)
                record = await result.single()

                if record:
                    logger.info(
                        "betweenness_completed",
                        compute_ms=record["computeMillis"],
                        write_ms=record["writeMillis"],
                    )

        except Neo4jError as e:
            logger.error("betweenness_algorithm_failed", error=str(e))
            raise GDSError(f"Betweenness algorithm failed: {e}") from e

        # Fetch normalized scores
        fetch_query = """
        MATCH (p:Paper)
        WHERE p.betweenness IS NOT NULL
        WITH max(p.betweenness) AS max_score
        MATCH (p:Paper)
        WHERE p.betweenness IS NOT NULL
        RETURN p.openalex_id AS paper_id,
               CASE WHEN max_score > 0
                    THEN p.betweenness / max_score
                    ELSE 0.0
               END AS normalized_score
        ORDER BY normalized_score DESC
        """

        try:
            async with self.client.session() as session:
                result = await session.run(fetch_query)
                records = await result.values()

                scores = {str(rec[0]): float(rec[1]) for rec in records}

                logger.info("betweenness_scores_fetched", total_papers=len(scores))

                return scores

        except Neo4jError as e:
            logger.error("betweenness_fetch_failed", error=str(e))
            raise GDSError(f"Failed to fetch betweenness scores: {e}") from e
