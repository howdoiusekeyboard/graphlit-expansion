"""BFS orchestrator for citation network expansion.

This module provides the main expansion logic using Breadth-First Search
to traverse the citation network and populate the Neo4j graph database.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from graphlit.clients.openalex import OpenAlexClient
from graphlit.config import ExpansionSettings
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.models import ExpansionStats
from graphlit.pipeline.mapper import Mapper

if TYPE_CHECKING:
    from typing import Any


logger = structlog.get_logger(__name__)


class ExpansionOrchestrator:
    """Orchestrates BFS expansion of citation network.

    Coordinates the OpenAlex API client, Neo4j database client, and
    mapper to expand from seed papers to a full citation network.

    The expansion uses Breadth-First Search to traverse citations,
    respecting depth limits and paper count constraints.

    Attributes:
        api: OpenAlex API client.
        db: Neo4j database client.
        mapper: Data transformation mapper.
        settings: Expansion configuration.
        stats: Expansion statistics tracker.

    Example:
        >>> async with OpenAlexClient(api_settings) as api:
        ...     async with Neo4jClient(db_settings) as db:
        ...         orchestrator = ExpansionOrchestrator(api, db, mapper, settings)
        ...         await orchestrator.expand(seed_dois)
    """

    def __init__(
        self,
        openalex_client: OpenAlexClient,
        neo4j_client: Neo4jClient,
        mapper: Mapper,
        settings: ExpansionSettings,
    ) -> None:
        """Initialize the expansion orchestrator.

        Args:
            openalex_client: OpenAlex API client.
            neo4j_client: Neo4j database client.
            mapper: Data transformation mapper.
            settings: Expansion configuration.
        """
        self.api = openalex_client
        self.db = neo4j_client
        self.mapper = mapper
        self.settings = settings

        self.console = Console()
        self.stats = ExpansionStats()

        # BFS state
        self._visited: set[str] = set()
        self._queue: deque[tuple[str, int]] = deque()  # (openalex_id, depth)
        self._pending_citations: list[tuple[str, list[str]]] = []  # For second pass

    async def expand(self, seed_dois: list[str]) -> ExpansionStats:
        """Execute the full expansion workflow.

        This is the main entry point that coordinates:
        1. Resolving seed DOIs to OpenAlex IDs
        2. BFS expansion of the citation network
        3. Creating citation edges between existing papers

        Args:
            seed_dois: List of DOIs for seed papers.

        Returns:
            ExpansionStats with final counts.
        """
        logger.info("expansion_started", seed_count=len(seed_dois))

        self.console.print(Panel(
            f"[bold]Starting expansion from {len(seed_dois)} seed papers[/bold]\n"
            f"Target: {self.settings.max_papers} papers, max depth: {self.settings.max_depth}",
            title="GraphLit Expansion",
            border_style="cyan",
        ))

        # Load existing papers from database (for resumability)
        existing_ids = await self.db.get_all_paper_ids()
        self._visited = existing_ids
        logger.info("loaded_existing_papers", count=len(existing_ids))

        # Phase 1: Resolve seeds
        await self._resolve_seeds(seed_dois)

        # Phase 2: BFS expansion
        await self._run_bfs_expansion()

        # Phase 3: Create citation edges
        await self._create_citation_edges()

        # Final stats
        self.stats.queue_size = len(self._queue)
        graph_stats = await self.db.get_graph_stats()

        self.console.print(Panel(
            f"[green]Expansion complete![/green]\n\n"
            f"Papers processed: {self.stats.processed}\n"
            f"Papers skipped: {self.stats.skipped}\n"
            f"Errors: {self.stats.errors}\n"
            f"API calls: {self.stats.api_calls}\n\n"
            f"[bold]Graph Statistics:[/bold]\n"
            f"  Papers: {graph_stats['papers']}\n"
            f"  Authors: {graph_stats['authors']}\n"
            f"  Venues: {graph_stats['venues']}\n"
            f"  Topics: {graph_stats['topics']}\n"
            f"  Citations: {graph_stats['citations']}",
            title="Expansion Complete",
            border_style="green",
        ))

        logger.info(
            "expansion_complete",
            **self.stats.to_dict(),
            **graph_stats,
        )

        return self.stats

    async def _resolve_seeds(self, dois: list[str]) -> None:
        """Resolve seed DOIs to OpenAlex IDs and enqueue.

        Args:
            dois: List of DOIs to resolve.
        """
        logger.info("resolving_seeds", count=len(dois))

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Resolving seed DOIs...", total=len(dois))

            for doi in dois:
                work = await self.api.get_work_by_doi(doi)
                self.stats.increment_api_calls()

                if work:
                    openalex_id = self.mapper.extract_id(work["id"])
                    if openalex_id not in self._visited:
                        self._queue.append((openalex_id, 0))
                        logger.info(
                            "seed_resolved",
                            doi=doi,
                            openalex_id=openalex_id,
                            title=work.get("title", "")[:50],
                        )
                    else:
                        logger.debug("seed_already_exists", doi=doi, openalex_id=openalex_id)
                else:
                    logger.warning("seed_not_found", doi=doi)
                    self.stats.increment_skipped()

                progress.update(task, advance=1)

        logger.info("seeds_resolved", queue_size=len(self._queue))

    async def _run_bfs_expansion(self) -> None:
        """Execute BFS traversal of citation network."""
        logger.info(
            "bfs_started",
            queue_size=len(self._queue),
            max_papers=self.settings.max_papers,
        )

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Expanding citation network...",
                total=self.settings.max_papers,
            )
            progress.update(task, completed=len(self._visited))

            while self._queue and len(self._visited) < self.settings.max_papers:
                openalex_id, depth = self._queue.popleft()

                if openalex_id in self._visited:
                    continue

                success = await self._process_paper(openalex_id, depth)

                if success:
                    self._visited.add(openalex_id)
                    self.stats.increment_processed()
                    progress.update(task, completed=len(self._visited))

                    # Log progress every 100 papers
                    if self.stats.processed % 100 == 0:
                        logger.info(
                            "expansion_progress",
                            processed=self.stats.processed,
                            visited=len(self._visited),
                            queue=len(self._queue),
                        )

        logger.info(
            "bfs_complete",
            visited=len(self._visited),
            queue_remaining=len(self._queue),
        )

    async def _process_paper(self, openalex_id: str, depth: int) -> bool:
        """Process a single paper: fetch, validate, insert, enqueue neighbors.

        Args:
            openalex_id: OpenAlex work ID.
            depth: Current BFS depth.

        Returns:
            True if paper was successfully processed.
        """
        try:
            # Fetch from API
            work = await self.api.get_work(openalex_id)
            self.stats.increment_api_calls()

            if not work:
                logger.debug("paper_not_found", openalex_id=openalex_id)
                self.stats.increment_skipped()
                return False

            # Validate inclusion criteria
            if not self.mapper.should_include(work):
                self.stats.increment_skipped()
                return False

            # Insert paper and related entities
            await self._insert_paper_data(work)

            # Store references for citation edge creation
            ref_ids = self.mapper.get_reference_ids(work, limit=100)
            if ref_ids:
                self._pending_citations.append((openalex_id, ref_ids))

            # Enqueue neighbors if not at max depth
            if depth < self.settings.max_depth:
                self._enqueue_neighbors(work, depth)

            return True

        except Exception as e:
            logger.error(
                "paper_processing_error",
                openalex_id=openalex_id,
                error=str(e),
                exc_info=True,
            )
            self.stats.increment_errors()
            return False

    async def _insert_paper_data(self, work: dict[str, Any]) -> None:
        """Insert paper and all related entities to Neo4j.

        Args:
            work: OpenAlex work JSON.
        """
        # Insert paper
        paper = self.mapper.map_paper(work)
        await self.db.upsert_paper(paper)

        # Insert authors and relationships
        for author, position in self.mapper.map_authors(work):
            await self.db.upsert_author(author)
            await self.db.create_authorship(
                paper.openalex_id,
                author.openalex_id,
                position,
            )

        # Insert venue if present
        venue = self.mapper.map_venue(work)
        if venue:
            await self.db.upsert_venue(venue)
            await self.db.create_publication(paper.openalex_id, venue.openalex_id)

        # Insert topics
        for topic, score in self.mapper.map_topics(work):
            await self.db.upsert_topic(topic)
            await self.db.create_topic_assignment(
                paper.openalex_id,
                topic.openalex_id,
                score,
            )

    def _enqueue_neighbors(self, work: dict[str, Any], current_depth: int) -> None:
        """Add referenced works to the queue.

        Args:
            work: OpenAlex work JSON.
            current_depth: Current BFS depth.
        """
        # Get references (outgoing citations)
        ref_ids = self.mapper.get_reference_ids(work, limit=50)
        new_depth = current_depth + 1

        for ref_id in ref_ids:
            if ref_id not in self._visited:
                self._queue.append((ref_id, new_depth))

    async def _create_citation_edges(self) -> None:
        """Create CITES relationships between papers in the graph.

        This is a second pass that creates edges only between
        papers that both exist in the graph.
        """
        if not self._pending_citations:
            return

        logger.info("creating_citation_edges", pending=len(self._pending_citations))

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Creating citation edges...",
                total=len(self._pending_citations),
            )

            citation_count = 0
            for citing_id, ref_ids in self._pending_citations:
                for cited_id in ref_ids:
                    if cited_id in self._visited:
                        await self.db.create_citation(citing_id, cited_id)
                        citation_count += 1

                progress.update(task, advance=1)

        logger.info("citation_edges_created", count=citation_count)
