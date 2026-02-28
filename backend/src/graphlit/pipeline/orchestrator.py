"""BFS orchestrator for citation network expansion.

This module provides the main expansion logic using Breadth-First Search
to traverse the citation network and populate the Neo4j graph database.
Uses concurrent API fetching and batch Neo4j writes for performance.
"""

from __future__ import annotations

import asyncio
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
    respecting depth limits and paper count constraints. Papers are
    fetched concurrently and written to Neo4j in batches for performance.

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

        self.console.print(
            Panel(
                f"[bold]Starting expansion from {len(seed_dois)} seed papers[/bold]\n"
                f"Target: {self.settings.max_papers} papers, "
                f"max depth: {self.settings.max_depth}\n"
                f"Concurrency: {self.settings.concurrent_fetches} parallel fetches",
                title="GraphLit Expansion",
                border_style="cyan",
            )
        )

        # Load existing papers from database (for resumability)
        existing_ids = await self.db.get_all_paper_ids()
        self._visited = existing_ids
        logger.info("loaded_existing_papers", count=len(existing_ids))

        # Phase 1: Resolve seeds
        await self._resolve_seeds(seed_dois)

        # Phase 2: BFS expansion (concurrent fetch + batch write)
        await self._run_bfs_expansion()

        # Phase 3: Create citation edges (batch)
        await self._create_citation_edges()

        # Final stats
        self.stats.queue_size = len(self._queue)
        graph_stats = await self.db.get_graph_stats()

        self.console.print(
            Panel(
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
            )
        )

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
                        logger.debug(
                            "seed_already_exists", doi=doi, openalex_id=openalex_id
                        )
                else:
                    logger.warning("seed_not_found", doi=doi)
                    self.stats.increment_skipped()

                progress.update(task, advance=1)

        logger.info("seeds_resolved", queue_size=len(self._queue))

    async def _fetch_paper(
        self,
        openalex_id: str,
        sem: asyncio.Semaphore,
    ) -> tuple[str, dict[str, Any] | None]:
        """Fetch a single paper with semaphore-bounded concurrency.

        Args:
            openalex_id: OpenAlex work ID.
            sem: Semaphore for concurrency control.

        Returns:
            Tuple of (openalex_id, work_data or None).
        """
        async with sem:
            work = await self.api.get_work(openalex_id)
            self.stats.increment_api_calls()
            return (openalex_id, work)

    async def _run_bfs_expansion(self) -> None:
        """Execute BFS traversal with concurrent fetching and batch Neo4j writes."""
        logger.info(
            "bfs_started",
            queue_size=len(self._queue),
            max_papers=self.settings.max_papers,
            concurrent_fetches=self.settings.concurrent_fetches,
        )

        sem = asyncio.Semaphore(self.settings.concurrent_fetches)

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
                # 1. Collect a wave of papers from the queue
                wave: list[tuple[str, int]] = []
                wave_ids: set[str] = set()
                remaining = self.settings.max_papers - len(self._visited)
                wave_size = min(self.settings.concurrent_fetches, remaining)

                while self._queue and len(wave) < wave_size:
                    oid, depth = self._queue.popleft()
                    if oid not in self._visited and oid not in wave_ids:
                        wave.append((oid, depth))
                        wave_ids.add(oid)

                if not wave:
                    break

                # 2. Fetch all papers in the wave concurrently
                fetch_tasks = [self._fetch_paper(oid, sem) for oid, _ in wave]
                fetch_results: list[tuple[str, dict[str, Any] | None] | BaseException] = (
                    await asyncio.gather(*fetch_tasks, return_exceptions=True)
                )

                # 3. Map results and collect batch data
                papers_batch: list[dict[str, Any]] = []
                authors_batch: list[dict[str, Any]] = []
                authorships_batch: list[dict[str, Any]] = []
                venues_batch: list[dict[str, Any]] = []
                publications_batch: list[dict[str, Any]] = []
                topics_batch: list[dict[str, Any]] = []
                topic_assignments_batch: list[dict[str, Any]] = []
                successful_ids: list[str] = []

                for i, result in enumerate(fetch_results):
                    if isinstance(result, BaseException):
                        logger.error(
                            "fetch_error",
                            openalex_id=wave[i][0],
                            error=str(result),
                        )
                        self.stats.increment_errors()
                        continue

                    oid, work = result
                    depth = wave[i][1]

                    if not work:
                        self.stats.increment_skipped()
                        continue

                    if not self.mapper.should_include(work):
                        self.stats.increment_skipped()
                        continue

                    try:
                        self._collect_paper_batch_data(
                            oid,
                            work,
                            depth,
                            papers_batch,
                            authors_batch,
                            authorships_batch,
                            venues_batch,
                            publications_batch,
                            topics_batch,
                            topic_assignments_batch,
                        )
                        successful_ids.append(oid)
                    except Exception as e:
                        logger.error(
                            "mapping_error", openalex_id=oid, error=str(e)
                        )
                        self.stats.increment_errors()

                # 4. Batch write to Neo4j
                await self._write_batch(
                    papers_batch,
                    authors_batch,
                    authorships_batch,
                    venues_batch,
                    publications_batch,
                    topics_batch,
                    topic_assignments_batch,
                )

                # 5. Update state
                self._visited.update(successful_ids)
                for _ in successful_ids:
                    self.stats.increment_processed()
                progress.update(task, completed=len(self._visited))

                if self.stats.processed > 0 and self.stats.processed % 100 < len(
                    successful_ids
                ):
                    logger.info(
                        "expansion_progress",
                        processed=self.stats.processed,
                        visited=len(self._visited),
                        queue=len(self._queue),
                        wave_size=len(wave),
                        wave_success=len(successful_ids),
                    )

        logger.info(
            "bfs_complete",
            visited=len(self._visited),
            queue_remaining=len(self._queue),
        )

    def _collect_paper_batch_data(
        self,
        openalex_id: str,
        work: dict[str, Any],
        depth: int,
        papers_batch: list[dict[str, Any]],
        authors_batch: list[dict[str, Any]],
        authorships_batch: list[dict[str, Any]],
        venues_batch: list[dict[str, Any]],
        publications_batch: list[dict[str, Any]],
        topics_batch: list[dict[str, Any]],
        topic_assignments_batch: list[dict[str, Any]],
    ) -> None:
        """Map a work to batch dicts and collect citation refs / neighbors.

        Args:
            openalex_id: OpenAlex work ID.
            work: OpenAlex work JSON.
            depth: Current BFS depth.
            papers_batch: Accumulator for paper dicts.
            authors_batch: Accumulator for author dicts.
            authorships_batch: Accumulator for authorship dicts.
            venues_batch: Accumulator for venue dicts.
            publications_batch: Accumulator for publication dicts.
            topics_batch: Accumulator for topic dicts.
            topic_assignments_batch: Accumulator for topic assignment dicts.
        """
        paper = self.mapper.map_paper(work)
        papers_batch.append({
            "openalex_id": paper.openalex_id,
            "doi": paper.doi,
            "title": paper.title,
            "year": paper.year,
            "citations": paper.citations,
            "abstract": paper.abstract,
        })

        for author, position in self.mapper.map_authors(work):
            authors_batch.append({
                "openalex_id": author.openalex_id,
                "name": author.name,
                "orcid": author.orcid,
                "institution": author.institution,
            })
            authorships_batch.append({
                "paper_id": paper.openalex_id,
                "author_id": author.openalex_id,
                "position": position,
            })

        venue = self.mapper.map_venue(work)
        if venue:
            venues_batch.append({
                "openalex_id": venue.openalex_id,
                "name": venue.name,
                "venue_type": venue.venue_type,
                "publisher": venue.publisher,
            })
            publications_batch.append({
                "paper_id": paper.openalex_id,
                "venue_id": venue.openalex_id,
            })

        for topic, score in self.mapper.map_topics(work):
            topics_batch.append({
                "openalex_id": topic.openalex_id,
                "name": topic.name,
                "level": topic.level,
            })
            topic_assignments_batch.append({
                "paper_id": paper.openalex_id,
                "topic_id": topic.openalex_id,
                "score": score,
            })

        # Collect citation references for phase 3
        ref_ids = self.mapper.get_reference_ids(work, limit=100)
        if ref_ids:
            self._pending_citations.append((openalex_id, ref_ids))

        # Enqueue neighbors for next BFS wave
        if depth < self.settings.max_depth:
            self._enqueue_neighbors(work, depth)

    async def _write_batch(
        self,
        papers: list[dict[str, Any]],
        authors: list[dict[str, Any]],
        authorships: list[dict[str, Any]],
        venues: list[dict[str, Any]],
        publications: list[dict[str, Any]],
        topics: list[dict[str, Any]],
        topic_assignments: list[dict[str, Any]],
    ) -> None:
        """Write all collected batch data to Neo4j.

        Nodes are written before relationships to ensure MATCH succeeds.

        Args:
            papers: Paper node dicts.
            authors: Author node dicts.
            authorships: Authorship relationship dicts.
            venues: Venue node dicts.
            publications: Publication relationship dicts.
            topics: Topic node dicts.
            topic_assignments: Topic assignment relationship dicts.
        """
        # Write nodes first
        if papers:
            await self.db.upsert_papers_batch(papers)
        if authors:
            await self.db.upsert_authors_batch(authors)
        if venues:
            await self.db.upsert_venues_batch(venues)
        if topics:
            await self.db.upsert_topics_batch(topics)

        # Then relationships (need nodes to exist)
        if authorships:
            await self.db.create_authorships_batch(authorships)
        if publications:
            await self.db.create_publications_batch(publications)
        if topic_assignments:
            await self.db.create_topic_assignments_batch(topic_assignments)

    def _enqueue_neighbors(self, work: dict[str, Any], current_depth: int) -> None:
        """Add referenced works to the queue.

        Args:
            work: OpenAlex work JSON.
            current_depth: Current BFS depth.
        """
        ref_ids = self.mapper.get_reference_ids(work, limit=50)
        new_depth = current_depth + 1

        for ref_id in ref_ids:
            if ref_id not in self._visited:
                self._queue.append((ref_id, new_depth))

    async def _create_citation_edges(self) -> None:
        """Create CITES relationships between papers in the graph.

        This is a second pass that creates edges only between
        papers that both exist in the graph, using batch writes.

        If _pending_citations is empty (resume case), fetches all papers
        from the database and retrieves their references from OpenAlex API
        concurrently.
        """
        # Handle resume case: fetch references concurrently
        if not self._pending_citations:
            await self._fetch_references_for_existing_papers()

        if not self._pending_citations:
            logger.info("no_citations_to_create")
            return

        # Collect all valid citation pairs (both papers must exist)
        citations_batch: list[dict[str, Any]] = []
        for citing_id, ref_ids in self._pending_citations:
            for cited_id in ref_ids:
                if cited_id in self._visited:
                    citations_batch.append({
                        "citing_id": citing_id,
                        "cited_id": cited_id,
                    })

        if citations_batch:
            logger.info("creating_citation_edges", count=len(citations_batch))
            await self.db.create_citations_batch(citations_batch)
            logger.info("citation_edges_created", count=len(citations_batch))

    async def _fetch_references_for_existing_papers(self) -> None:
        """Fetch references for existing papers concurrently (resume case)."""
        logger.info(
            "fetching_references_for_existing_papers", count=len(self._visited)
        )

        paper_ids = list(self._visited)
        sem = asyncio.Semaphore(self.settings.concurrent_fetches)

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "Fetching references for existing papers...",
                total=len(paper_ids),
            )

            # Process in concurrent waves
            for i in range(0, len(paper_ids), self.settings.concurrent_fetches):
                wave = paper_ids[i : i + self.settings.concurrent_fetches]
                fetch_tasks = [self._fetch_paper(pid, sem) for pid in wave]
                results: list[
                    tuple[str, dict[str, Any] | None] | BaseException
                ] = await asyncio.gather(*fetch_tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, BaseException):
                        continue
                    pid, work = result
                    if work:
                        ref_ids = self.mapper.get_reference_ids(work, limit=100)
                        if ref_ids:
                            self._pending_citations.append((pid, ref_ids))

                progress.update(task, advance=len(wave))

                if (i // self.settings.concurrent_fetches) % 10 == 0 and i > 0:
                    logger.info(
                        "references_fetch_progress",
                        fetched=i + len(wave),
                        total=len(paper_ids),
                        citations_found=len(self._pending_citations),
                    )

        logger.info("references_fetched", total=len(self._pending_citations))
