"""Community detection module using Neo4j GDS Louvain algorithm.

This module provides functionality to:
1. Detect citation network communities using Louvain algorithm
2. Auto-label communities based on aggregated topic distributions
3. Find bridging papers that connect different communities
4. Generate markdown reports with community insights

Usage:
    >>> from graphlit.analytics.community_detector import CommunityDetector
    >>> from graphlit.config import get_settings
    >>> from graphlit.database.neo4j_client import Neo4jClient
    >>> from graphlit.database.graph_algorithms import GraphAlgorithms
    >>>
    >>> settings = get_settings()
    >>> async with Neo4jClient(settings.neo4j) as client:
    ...     gds = GraphAlgorithms(client, settings.analytics)
    ...     detector = CommunityDetector(client, gds, settings.analytics)
    ...
    ...     # Run full community detection pipeline
    ...     communities = await detector.detect_communities()
    ...     labels = await detector.label_communities()
    ...     bridging = await detector.find_bridging_papers(min_communities=2)
    ...
    ...     # Generate report
    ...     report = await detector.export_community_report("community_report.md")
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from graphlit.config import AnalyticsSettings
    from graphlit.database.graph_algorithms import GraphAlgorithms
    from graphlit.database.neo4j_client import Neo4jClient

from graphlit.database import queries

logger = structlog.get_logger(__name__)


class CommunityDetectionError(Exception):
    """Raised when community detection operations fail."""

    pass


class CommunityDetector:
    """Community detection service using Neo4j GDS Louvain algorithm.

    Provides methods to detect, analyze, and report on citation network
    communities.

    Attributes:
        client: Neo4jClient for database operations.
        gds: GraphAlgorithms wrapper for GDS operations.
        settings: Analytics configuration settings.
    """

    def __init__(
        self,
        client: Neo4jClient,
        gds: GraphAlgorithms,
        settings: AnalyticsSettings,
    ) -> None:
        """Initialize CommunityDetector.

        Args:
            client: Connected Neo4jClient instance.
            gds: GraphAlgorithms instance for GDS operations.
            settings: Analytics configuration settings.
        """
        self.client = client
        self.gds = gds
        self.settings = settings

    async def detect_communities(self) -> dict[int, list[str]]:
        """Detect communities using Louvain algorithm.

        This method:
        1. Projects citation graph into GDS (if not exists)
        2. Runs Louvain community detection
        3. Groups papers by community ID
        4. Filters out small communities (< min_community_size)

        Returns:
            Dictionary mapping community_id → list of paper_ids.
            Only includes communities with >= min_community_size papers.

        Raises:
            CommunityDetectionError: If detection fails.

        Example:
            >>> communities = await detector.detect_communities()
            >>> communities
            {0: ['W123', 'W456', 'W789'], 1: ['W111', 'W222'], ...}
        """
        logger.info("community_detection_started")

        try:
            # Ensure graph projection exists
            if not await self.gds.graph_exists():
                logger.info("projecting_citation_graph")
                await self.gds.project_citation_graph()

            # Run Louvain algorithm
            paper_to_community = await self.gds.detect_communities_louvain()

            # Group by community
            communities: dict[int, list[str]] = defaultdict(list)
            for paper_id, community_id in paper_to_community.items():
                communities[community_id].append(paper_id)

            # Filter small communities
            min_size = self.settings.min_community_size
            filtered_communities = {
                cid: papers
                for cid, papers in communities.items()
                if len(papers) >= min_size
            }

            logger.info(
                "community_detection_completed",
                total_communities=len(communities),
                filtered_communities=len(filtered_communities),
                min_size=min_size,
                total_papers=sum(len(papers) for papers in filtered_communities.values()),
            )

            return filtered_communities

        except Exception as e:
            logger.error("community_detection_failed", error=str(e))
            raise CommunityDetectionError(f"Failed to detect communities: {e}") from e

    async def label_communities(self) -> dict[int, str]:
        """Auto-generate descriptive labels for each community.

        Labels are created by:
        1. Fetching top topics for each community (by frequency & score)
        2. Combining top 3 topic names with "&"
        3. Falling back to "Community {id}" if no topics found

        Returns:
            Dictionary mapping community_id → descriptive_label.

        Example:
            >>> labels = await detector.label_communities()
            >>> labels
            {0: 'Machine Learning & Neural Networks & Deep Learning',
             1: 'Graph Theory & Algorithms',
             ...}
        """
        logger.info("labeling_communities_started")

        try:
            # Get unique community IDs
            query = """
            MATCH (p:Paper)
            WHERE p.community IS NOT NULL
            RETURN DISTINCT p.community AS community_id
            ORDER BY community_id
            """

            async with self.client.session() as session:
                result = await session.run(query)
                records = await result.values()
                community_ids = [int(rec[0]) for rec in records]

            # Generate labels for each community
            labels: dict[int, str] = {}

            for community_id in community_ids:
                async with self.client.session() as session:
                    result = await session.run(
                        queries.GET_COMMUNITY_TOPIC_DISTRIBUTION,
                        community_id=community_id,
                    )
                    records = await result.values()

                    if records:
                        # Take top 3 topics
                        top_topics = [str(rec[1]) for rec in records[:3]]
                        label = " & ".join(top_topics)
                    else:
                        label = f"Community {community_id}"

                    labels[community_id] = label

            logger.info(
                "community_labeling_completed",
                total_communities=len(labels),
            )

            return labels

        except Exception as e:
            logger.error("community_labeling_failed", error=str(e))
            return {}

    async def find_bridging_papers(
        self,
        limit: int = 20,
        min_communities: int = 2,
    ) -> list[dict[str, Any]]:
        """Find papers that bridge multiple communities.

        Bridging papers have:
        - High betweenness centrality (on many shortest paths)
        - Citations to papers in multiple different communities

        Args:
            limit: Maximum number of bridging papers to return.
            min_communities: Minimum number of communities a paper must cite.

        Returns:
            List of dicts with keys:
            - paper_id: OpenAlex paper ID
            - title: Paper title
            - community_id: Paper's own community
            - betweenness: Betweenness centrality score
            - cross_community_citations: Number of communities cited

        Example:
            >>> bridging = await detector.find_bridging_papers(limit=10)
            >>> bridging[0]
            {'paper_id': 'W123', 'title': 'Survey of ML',
             'community_id': 0, 'betweenness': 0.95,
             'cross_community_citations': 4}
        """
        logger.info(
            "finding_bridging_papers",
            limit=limit,
            min_communities=min_communities,
        )

        try:
            # Ensure betweenness centrality is calculated
            betweenness_scores = await self.gds.calculate_betweenness_centrality()

            if not betweenness_scores:
                logger.warning("no_betweenness_scores_available")
                return []

            # Find bridging papers
            async with self.client.session() as session:
                result = await session.run(
                    queries.GET_BRIDGING_PAPERS,
                    limit=limit,
                    min_communities=min_communities,
                )
                records = await result.values()

                bridging_papers = [
                    {
                        "paper_id": str(rec[0]),
                        "title": str(rec[1]),
                        "community_id": int(rec[2]),
                        "betweenness": float(rec[3]),
                        "cross_community_citations": int(rec[4]),
                    }
                    for rec in records
                ]

            logger.info(
                "bridging_papers_found",
                count=len(bridging_papers),
            )

            return bridging_papers

        except Exception as e:
            logger.error("bridging_papers_search_failed", error=str(e))
            return []

    async def get_community_stats(self) -> list[dict[str, Any]]:
        """Get statistics for all communities.

        Returns:
            List of dicts with keys:
            - community_id: Community identifier
            - paper_count: Number of papers in community
            - avg_citations: Average citations per paper
            - year_range: Tuple of (min_year, max_year)
        """
        try:
            async with self.client.session() as session:
                result = await session.run(queries.GET_COMMUNITY_STATS)
                records = await result.values()

                stats = [
                    {
                        "community_id": int(rec[0]),
                        "paper_count": int(rec[1]),
                        "avg_citations": float(rec[2]) if rec[2] else 0.0,
                        "year_range": (
                            (int(rec[4]), int(rec[3])) if rec[4] and rec[3] else (0, 0)
                        ),
                    }
                    for rec in records
                ]

            return stats

        except Exception as e:
            logger.error("community_stats_failed", error=str(e))
            return []

    async def export_community_report(
        self,
        output_path: str | Path = "community_report.md",
    ) -> str:
        """Generate comprehensive markdown report on communities.

        Report includes:
        - Overview statistics (total communities, papers)
        - Community summaries (size, label, top topics)
        - Bridging papers analysis
        - Visualizations (ASCII art or markdown tables)

        Args:
            output_path: Path to save markdown report.

        Returns:
            Absolute path to generated report file.

        Raises:
            CommunityDetectionError: If report generation fails.
        """
        logger.info("generating_community_report", output_path=str(output_path))

        try:
            # Gather all data
            communities = await self.detect_communities()
            labels = await self.label_communities()
            stats = await self.get_community_stats()
            bridging = await self.find_bridging_papers(limit=15)

            # Build markdown report
            lines = [
                "# Citation Network Community Analysis Report",
                "",
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Overview",
                "",
                f"- **Total Communities:** {len(communities)}",
                f"- **Total Papers:** {sum(len(papers) for papers in communities.values())}",
                f"- **Bridging Papers:** {len(bridging)}",
                "",
                "## Community Summaries",
                "",
            ]

            # Add community details
            for stat in stats:
                cid = stat["community_id"]
                label = labels.get(cid, f"Community {cid}")

                lines.extend(
                    [
                        f"### {label} (Community {cid})",
                        "",
                        f"- **Papers:** {stat['paper_count']}",
                        f"- **Avg Citations:** {stat['avg_citations']:.1f}",
                        f"- **Year Range:** {stat['year_range'][0]}–{stat['year_range'][1]}",
                        "",
                        "**Top Topics:**",
                        "",
                    ]
                )

                # Fetch top topics for this community
                async with self.client.session() as session:
                    result = await session.run(
                        queries.GET_COMMUNITY_TOPIC_DISTRIBUTION,
                        community_id=cid,
                    )
                    topic_records = await result.values()

                    for i, topic_rec in enumerate(topic_records[:5], 1):
                        topic_name = str(topic_rec[1])
                        paper_count = int(topic_rec[2])
                        avg_score = float(topic_rec[3])
                        lines.append(
                            f"{i}. **{topic_name}** "
                            f"({paper_count} papers, avg score: {avg_score:.2f})"
                        )

                lines.append("")

            # Add bridging papers section
            lines.extend(
                [
                    "## Bridging Papers",
                    "",
                    "Papers that connect multiple communities (high betweenness centrality):",
                    "",
                    "| Paper ID | Title | Community | Betweenness | Cross-Community Citations |",
                    "|----------|-------|-----------|-------------|---------------------------|",
                ]
            )

            for paper in bridging:
                lines.append(
                    f"| {paper['paper_id'][:10]}... | "
                    f"{paper['title'][:50]}... | "
                    f"{paper['community_id']} | "
                    f"{paper['betweenness']:.3f} | "
                    f"{paper['cross_community_citations']} |"
                )

            lines.append("")

            # Write to file
            output_file = Path(output_path)
            output_file.write_text("\n".join(lines), encoding="utf-8")

            logger.info(
                "community_report_generated",
                output_path=str(output_file.absolute()),
                communities=len(communities),
                bridging_papers=len(bridging),
            )

            return str(output_file.absolute())

        except Exception as e:
            logger.error("report_generation_failed", error=str(e))
            raise CommunityDetectionError(f"Failed to generate report: {e}") from e
