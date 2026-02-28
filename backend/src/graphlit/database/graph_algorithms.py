"""Python-based graph algorithm implementations using networkx.

Replaces Neo4j GDS dependency with pure Python implementations,
making the analytics pipeline compatible with Neo4j AuraDB Free (no GDS plugin).

Algorithms:
- Community detection (Louvain via networkx.community.louvain_communities)
- Centrality metrics (PageRank, Betweenness via networkx)
- Graph projection (Cypher fetch → networkx DiGraph)

All results are written back to Neo4j as node properties via batched UNWIND + MATCH + SET queries.

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

import networkx as nx
import structlog
from neo4j.exceptions import Neo4jError

if TYPE_CHECKING:
    from graphlit.config import AnalyticsSettings
    from graphlit.database.neo4j_client import Neo4jClient

logger = structlog.get_logger(__name__)

_BATCH_SIZE = 500


class GDSError(Exception):
    """Raised when a graph algorithm operation fails."""


class GraphAlgorithms:
    """Graph algorithm wrapper using networkx (AuraDB-compatible).

    Fetches citation graph from Neo4j via Cypher, builds a networkx DiGraph
    in memory, runs algorithms in Python, and writes results back to Neo4j.

    Attributes:
        client: Neo4jClient instance for database operations.
        settings: AnalyticsSettings for algorithm parameters.
    """

    def __init__(self, client: Neo4jClient, settings: AnalyticsSettings) -> None:
        self.client = client
        self.settings = settings
        self.graph_name = settings.gds_graph_name
        self._graph: nx.DiGraph | None = None

    # =========================================================================
    # Graph Projection (Cypher → networkx)
    # =========================================================================

    async def graph_exists(self) -> bool:
        """Check if the in-memory networkx graph has been built."""
        return self._graph is not None and len(self._graph) > 0

    async def drop_graph_if_exists(self) -> bool:
        """Clear the in-memory networkx graph."""
        self._graph = None
        logger.debug("graph_cleared", graph_name=self.graph_name)
        return True

    async def project_citation_graph(self) -> dict[str, Any]:
        """Build networkx DiGraph from Neo4j citation data.

        Fetches all Paper nodes and CITES edges via Cypher, then constructs
        an in-memory directed graph for algorithm execution.

        Returns:
            Dictionary with projection statistics (nodeCount, relationshipCount).

        Raises:
            GDSError: If projection fails.
        """
        await self.drop_graph_if_exists()

        paper_query = """
        MATCH (p:Paper)
        WHERE p.openalex_id IS NOT NULL
        RETURN p.openalex_id AS id, p.year AS year, p.citations AS citations
        """

        edge_query = """
        MATCH (a:Paper)-[:CITES]->(b:Paper)
        WHERE a.openalex_id IS NOT NULL AND b.openalex_id IS NOT NULL
        RETURN a.openalex_id AS source, b.openalex_id AS target
        """

        try:
            graph: nx.DiGraph = nx.DiGraph()

            async with self.client.session() as session:
                result = await session.run(paper_query)
                records = await result.values()
                for rec in records:
                    graph.add_node(str(rec[0]), year=rec[1], citations=rec[2] or 0)

            async with self.client.session() as session:
                result = await session.run(edge_query)
                records = await result.values()
                for rec in records:
                    src, tgt = str(rec[0]), str(rec[1])
                    if src in graph and tgt in graph:
                        graph.add_edge(src, tgt)

            self._graph = graph

            stats: dict[str, Any] = {
                "graphName": self.graph_name,
                "nodeCount": graph.number_of_nodes(),
                "relationshipCount": graph.number_of_edges(),
                "projectMillis": 0,
            }

            logger.info(
                "graph_projected",
                graph_name=stats["graphName"],
                nodes=stats["nodeCount"],
                relationships=stats["relationshipCount"],
            )

            return stats

        except Neo4jError as e:
            logger.error("graph_projection_failed", error=str(e))
            raise GDSError(f"Failed to project citation graph: {e}") from e

    # =========================================================================
    # Community Detection (Louvain)
    # =========================================================================

    async def detect_communities_louvain(self) -> dict[str, int]:
        """Detect communities using networkx Louvain algorithm.

        Runs louvain_communities on the projected citation graph and writes
        community assignments back to Neo4j as a 'community' property.

        Returns:
            Dictionary mapping paper_id → community_id (int, 0-indexed).

        Raises:
            GDSError: If algorithm fails or graph doesn't exist.
        """
        if self._graph is None or len(self._graph) == 0:
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. Call project_citation_graph() first."
            )

        try:
            # networkx 3.6.1: louvain_communities works on DiGraph directly
            communities_list: list[set[Any]] = nx.community.louvain_communities(
                self._graph,
                seed=42,
                resolution=1.0,
                threshold=self.settings.louvain_tolerance,
                max_level=self.settings.louvain_max_iterations,
            )

            # Build paper → community mapping
            paper_to_community: dict[str, int] = {}
            for community_id, members in enumerate(communities_list):
                for node in members:
                    paper_to_community[str(node)] = community_id

            # Batch write community assignments to Neo4j
            write_query = """
            UNWIND $assignments AS a
            MATCH (p:Paper {openalex_id: a.paper_id})
            SET p.community = a.community_id
            """

            assignments = [
                {"paper_id": pid, "community_id": cid} for pid, cid in paper_to_community.items()
            ]

            for i in range(0, len(assignments), _BATCH_SIZE):
                chunk = assignments[i : i + _BATCH_SIZE]
                async with self.client.session() as session:
                    await session.run(write_query, assignments=chunk)

            logger.info(
                "louvain_completed",
                communities=len(communities_list),
                total_papers=len(paper_to_community),
            )

            return paper_to_community

        except Neo4jError as e:
            logger.error("louvain_algorithm_failed", error=str(e))
            raise GDSError(f"Louvain algorithm failed: {e}") from e
        except Exception as e:
            logger.error("louvain_algorithm_failed", error=str(e))
            raise GDSError(f"Louvain algorithm failed: {e}") from e

    # =========================================================================
    # Centrality Metrics (PageRank)
    # =========================================================================

    async def calculate_pagerank(self) -> dict[str, float]:
        """Calculate PageRank centrality using networkx.

        Runs nx.pagerank on the projected graph, normalizes scores to 0-1,
        and writes them back to Neo4j as 'pagerank' property on Paper nodes.

        Returns:
            Dictionary mapping paper_id → normalized_pagerank (0.0 to 1.0).

        Raises:
            GDSError: If algorithm fails or graph doesn't exist.
        """
        if self._graph is None or len(self._graph) == 0:
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. Call project_citation_graph() first."
            )

        try:
            # networkx 3.6.1: pagerank with configurable damping and iterations
            raw_scores: dict[Any, float] = nx.pagerank(
                self._graph,
                alpha=self.settings.pagerank_damping_factor,
                max_iter=self.settings.pagerank_max_iterations,
                tol=0.0001,
            )

            # Normalize to 0-1 range
            max_score = max(raw_scores.values()) if raw_scores else 1.0
            if max_score > 0:
                normalized = {
                    str(node): float(score / max_score) for node, score in raw_scores.items()
                }
            else:
                normalized = {str(node): 0.0 for node in raw_scores}

            # Batch write pagerank scores to Neo4j
            write_query = """
            UNWIND $scores AS s
            MATCH (p:Paper {openalex_id: s.paper_id})
            SET p.pagerank = s.score
            """

            score_list = [{"paper_id": pid, "score": score} for pid, score in normalized.items()]

            for i in range(0, len(score_list), _BATCH_SIZE):
                chunk = score_list[i : i + _BATCH_SIZE]
                async with self.client.session() as session:
                    await session.run(write_query, scores=chunk)

            logger.info(
                "pagerank_completed",
                papers_scored=len(normalized),
                max_score=max(normalized.values()) if normalized else 0.0,
                min_score=min(normalized.values()) if normalized else 0.0,
            )

            return normalized

        except Neo4jError as e:
            logger.error("pagerank_algorithm_failed", error=str(e))
            raise GDSError(f"PageRank algorithm failed: {e}") from e
        except Exception as e:
            logger.error("pagerank_algorithm_failed", error=str(e))
            raise GDSError(f"PageRank algorithm failed: {e}") from e

    # =========================================================================
    # Betweenness Centrality (for Bridging Papers)
    # =========================================================================

    async def calculate_betweenness_centrality(self) -> dict[str, float]:
        """Calculate betweenness centrality using networkx.

        High betweenness = node sits on many shortest paths = bridges communities.
        Uses sampling (k=500) for graphs with >500 nodes for performance.

        Returns:
            Dictionary mapping paper_id → normalized betweenness (0.0 to 1.0).

        Raises:
            GDSError: If algorithm fails or graph doesn't exist.
        """
        if self._graph is None or len(self._graph) == 0:
            raise GDSError(
                f"Graph '{self.graph_name}' does not exist. Call project_citation_graph() first."
            )

        try:
            n = self._graph.number_of_nodes()
            # networkx 3.6.1: k-sampling for approximation on large graphs
            # 3.6 has 50x faster Dijkstra which benefits this computation
            sample_k = min(n, 500) if n > 500 else None

            raw_scores: dict[Any, float] = nx.betweenness_centrality(
                self._graph,
                k=sample_k,
                normalized=True,
                seed=42,
            )

            # Normalize to 0-1 range (re-normalize after sampling)
            max_score = max(raw_scores.values()) if raw_scores else 1.0
            if max_score > 0:
                normalized = {
                    str(node): float(score / max_score) for node, score in raw_scores.items()
                }
            else:
                normalized = {str(node): 0.0 for node in raw_scores}

            # Batch write betweenness scores to Neo4j
            write_query = """
            UNWIND $scores AS s
            MATCH (p:Paper {openalex_id: s.paper_id})
            SET p.betweenness = s.score
            """

            score_list = [{"paper_id": pid, "score": score} for pid, score in normalized.items()]

            for i in range(0, len(score_list), _BATCH_SIZE):
                chunk = score_list[i : i + _BATCH_SIZE]
                async with self.client.session() as session:
                    await session.run(write_query, scores=chunk)

            logger.info(
                "betweenness_completed",
                papers_scored=len(normalized),
            )

            return normalized

        except Neo4jError as e:
            logger.error("betweenness_algorithm_failed", error=str(e))
            raise GDSError(f"Betweenness algorithm failed: {e}") from e
        except Exception as e:
            logger.error("betweenness_algorithm_failed", error=str(e))
            raise GDSError(f"Betweenness algorithm failed: {e}") from e
