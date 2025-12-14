"""Async Neo4j client for graph database operations.

This module provides an async client for Neo4j with connection management,
transaction handling, and CRUD operations for academic entities.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from graphlit.config import Neo4jSettings
from graphlit.database import queries
from graphlit.models import Author, Paper, Topic, Venue

if TYPE_CHECKING:
    from types import TracebackType

    from neo4j import AsyncDriver, AsyncSession


logger = structlog.get_logger(__name__)


class Neo4jConnectionError(Exception):
    """Raised when Neo4j connection fails."""

    pass


class Neo4jClient:
    """Async client for Neo4j graph database operations.

    Provides connection management, session handling, and CRUD operations
    for papers, authors, venues, topics, and their relationships.

    All insert operations use MERGE for idempotency, ensuring safe
    resumable execution.

    Example:
        >>> async with Neo4jClient(settings) as client:
        ...     await client.upsert_paper(paper)
        ...     count = await client.get_paper_count()
    """

    def __init__(self, settings: Neo4jSettings) -> None:
        """Initialize the Neo4j client.

        Args:
            settings: Neo4j configuration settings.
        """
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            settings.uri,
            auth=(settings.username, settings.password),
        )
        self._database = settings.database
        self._closed = False

    async def __aenter__(self) -> Neo4jClient:
        """Enter async context manager and initialize database."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close resources."""
        await self.close()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Create a database session context.

        Yields:
            AsyncSession: Neo4j async session.

        Example:
            >>> async with client.session() as session:
            ...     result = await session.run("MATCH (n) RETURN n")
        """
        session = self._driver.session(database=self._database)
        try:
            yield session
        finally:
            await session.close()

    async def initialize(self) -> None:
        """Initialize database with indexes.

        Creates indexes for efficient lookups on openalex_id fields.
        Safe to call multiple times (uses IF NOT EXISTS).
        """
        logger.info("initializing_database")
        try:
            async with self.session() as session:
                for query in queries.ALL_INDEX_QUERIES:
                    await session.run(query)
            logger.info("database_initialized", indexes=len(queries.ALL_INDEX_QUERIES))
        except ServiceUnavailable as e:
            logger.error("database_connection_failed", error=str(e))
            raise Neo4jConnectionError(f"Failed to connect to Neo4j: {e}") from e

    async def close(self) -> None:
        """Close the database driver and release resources."""
        if not self._closed:
            await self._driver.close()
            self._closed = True
            logger.debug("neo4j_client_closed")

    async def verify_connection(self) -> bool:
        """Verify database connectivity.

        Returns:
            True if connection is healthy, False otherwise.
        """
        try:
            async with self.session() as session:
                result = await session.run("RETURN 1 AS n")
                record = await result.single()
                return record is not None and record["n"] == 1
        except Neo4jError as e:
            logger.error("connection_verification_failed", error=str(e))
            return False

    # =========================================================================
    # Paper Operations
    # =========================================================================

    async def upsert_paper(self, paper: Paper) -> bool:
        """Insert or update a paper node.

        Args:
            paper: Paper model to upsert.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                result = await session.run(
                    queries.MERGE_PAPER,
                    openalex_id=paper.openalex_id,
                    doi=paper.doi,
                    title=paper.title,
                    year=paper.year,
                    citations=paper.citations,
                    abstract=paper.abstract,
                )
                record = await result.single()
                return record is not None
        except Neo4jError as e:
            logger.error("upsert_paper_failed", paper_id=paper.openalex_id, error=str(e))
            return False

    async def paper_exists(self, openalex_id: str) -> bool:
        """Check if a paper exists in the database.

        Args:
            openalex_id: OpenAlex paper ID.

        Returns:
            True if paper exists.
        """
        try:
            async with self.session() as session:
                result = await session.run(
                    queries.PAPER_EXISTS,
                    openalex_id=openalex_id,
                )
                record = await result.single()
                return record is not None and record["exists"]
        except Neo4jError as e:
            logger.error("paper_exists_check_failed", paper_id=openalex_id, error=str(e))
            return False

    async def get_paper_count(self) -> int:
        """Get total number of papers in the database.

        Returns:
            Number of Paper nodes.
        """
        try:
            async with self.session() as session:
                result = await session.run(queries.COUNT_PAPERS)
                record = await result.single()
                return record["count"] if record else 0
        except Neo4jError as e:
            logger.error("get_paper_count_failed", error=str(e))
            return 0

    async def get_all_paper_ids(self) -> set[str]:
        """Get all paper IDs in the database.

        Returns:
            Set of OpenAlex paper IDs.
        """
        try:
            async with self.session() as session:
                result = await session.run(queries.GET_ALL_PAPER_IDS)
                records = await result.values()
                return {str(r[0]) for r in records}
        except Neo4jError as e:
            logger.error("get_all_paper_ids_failed", error=str(e))
            return set()

    # =========================================================================
    # Author Operations
    # =========================================================================

    async def upsert_author(self, author: Author) -> bool:
        """Insert or update an author node.

        Args:
            author: Author model to upsert.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                result = await session.run(
                    queries.MERGE_AUTHOR,
                    openalex_id=author.openalex_id,
                    name=author.name,
                    orcid=author.orcid,
                    institution=author.institution,
                )
                record = await result.single()
                return record is not None
        except Neo4jError as e:
            logger.error("upsert_author_failed", author_id=author.openalex_id, error=str(e))
            return False

    # =========================================================================
    # Venue Operations
    # =========================================================================

    async def upsert_venue(self, venue: Venue) -> bool:
        """Insert or update a venue node.

        Args:
            venue: Venue model to upsert.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                result = await session.run(
                    queries.MERGE_VENUE,
                    openalex_id=venue.openalex_id,
                    name=venue.name,
                    venue_type=venue.venue_type,
                    publisher=venue.publisher,
                )
                record = await result.single()
                return record is not None
        except Neo4jError as e:
            logger.error("upsert_venue_failed", venue_id=venue.openalex_id, error=str(e))
            return False

    # =========================================================================
    # Topic Operations
    # =========================================================================

    async def upsert_topic(self, topic: Topic) -> bool:
        """Insert or update a topic node.

        Args:
            topic: Topic model to upsert.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                result = await session.run(
                    queries.MERGE_TOPIC,
                    openalex_id=topic.openalex_id,
                    name=topic.name,
                    level=topic.level,
                )
                record = await result.single()
                return record is not None
        except Neo4jError as e:
            logger.error("upsert_topic_failed", topic_id=topic.openalex_id, error=str(e))
            return False

    # =========================================================================
    # Relationship Operations
    # =========================================================================

    async def create_authorship(
        self,
        paper_id: str,
        author_id: str,
        position: int,
    ) -> bool:
        """Create AUTHORED_BY relationship between paper and author.

        Args:
            paper_id: OpenAlex paper ID.
            author_id: OpenAlex author ID.
            position: Author position (0-indexed).

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                await session.run(
                    queries.MERGE_AUTHORSHIP,
                    paper_id=paper_id,
                    author_id=author_id,
                    position=position,
                )
                return True
        except Neo4jError as e:
            logger.error(
                "create_authorship_failed",
                paper_id=paper_id,
                author_id=author_id,
                error=str(e),
            )
            return False

    async def create_publication(self, paper_id: str, venue_id: str) -> bool:
        """Create PUBLISHED_IN relationship between paper and venue.

        Args:
            paper_id: OpenAlex paper ID.
            venue_id: OpenAlex venue ID.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                await session.run(
                    queries.MERGE_PUBLICATION,
                    paper_id=paper_id,
                    venue_id=venue_id,
                )
                return True
        except Neo4jError as e:
            logger.error(
                "create_publication_failed",
                paper_id=paper_id,
                venue_id=venue_id,
                error=str(e),
            )
            return False

    async def create_topic_assignment(
        self,
        paper_id: str,
        topic_id: str,
        score: float,
    ) -> bool:
        """Create BELONGS_TO_TOPIC relationship between paper and topic.

        Args:
            paper_id: OpenAlex paper ID.
            topic_id: OpenAlex topic ID.
            score: Relevance score (0.0 to 1.0).

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                await session.run(
                    queries.MERGE_TOPIC_ASSIGNMENT,
                    paper_id=paper_id,
                    topic_id=topic_id,
                    score=score,
                )
                return True
        except Neo4jError as e:
            logger.error(
                "create_topic_assignment_failed",
                paper_id=paper_id,
                topic_id=topic_id,
                error=str(e),
            )
            return False

    async def create_citation(self, citing_id: str, cited_id: str) -> bool:
        """Create CITES relationship between two papers.

        Args:
            citing_id: OpenAlex ID of the citing paper.
            cited_id: OpenAlex ID of the cited paper.

        Returns:
            True if operation succeeded.
        """
        try:
            async with self.session() as session:
                await session.run(
                    queries.MERGE_CITATION,
                    citing_id=citing_id,
                    cited_id=cited_id,
                )
                return True
        except Neo4jError as e:
            logger.error(
                "create_citation_failed",
                citing_id=citing_id,
                cited_id=cited_id,
                error=str(e),
            )
            return False

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_graph_stats(self) -> dict[str, int]:
        """Get statistics about the graph.

        Returns:
            Dictionary with counts of papers, authors, venues, topics, citations.
        """
        try:
            async with self.session() as session:
                result = await session.run(queries.GET_GRAPH_STATS)
                record = await result.single()
                if record:
                    return {
                        "papers": record["papers"],
                        "authors": record["authors"],
                        "venues": record["venues"],
                        "topics": record["topics"],
                        "citations": record["citations"],
                    }
                return {"papers": 0, "authors": 0, "venues": 0, "topics": 0, "citations": 0}
        except Neo4jError as e:
            logger.error("get_graph_stats_failed", error=str(e))
            return {"papers": 0, "authors": 0, "venues": 0, "topics": 0, "citations": 0}

    # =========================================================================
    # Cleanup (for testing)
    # =========================================================================

    async def delete_all(self) -> None:
        """Delete all nodes and relationships.

        WARNING: This is destructive! Use only in tests.
        """
        logger.warning("deleting_all_data")
        try:
            async with self.session() as session:
                await session.run(queries.DELETE_ALL)
        except Neo4jError as e:
            logger.error("delete_all_failed", error=str(e))
