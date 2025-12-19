"""Data transformation from OpenAlex API to domain models.

This module provides pure functions for transforming OpenAlex API
JSON responses into validated domain model instances.
"""

from __future__ import annotations

from typing import Any

import structlog

from graphlit.config import ExpansionSettings
from graphlit.models import Author, Paper, Topic, Venue

logger = structlog.get_logger(__name__)


class Mapper:
    """Transform OpenAlex API responses to domain models.

    Provides methods for mapping JSON data from OpenAlex API to
    validated domain model instances with filtering logic.

    Example:
        >>> mapper = Mapper(settings)
        >>> paper = mapper.map_paper(work_json)
        >>> if mapper.should_include(work_json):
        ...     # Process paper
    """

    def __init__(self, settings: ExpansionSettings) -> None:
        """Initialize mapper with expansion settings.

        Args:
            settings: Expansion configuration for filtering.
        """
        self.settings = settings

    def extract_id(self, url_or_id: str) -> str:
        """Extract OpenAlex ID from URL or return ID as-is.

        Args:
            url_or_id: Full OpenAlex URL or short ID.

        Returns:
            Short OpenAlex ID (e.g., 'W2741809807').

        Example:
            >>> mapper.extract_id("https://openalex.org/W123")
            'W123'
            >>> mapper.extract_id("W123")
            'W123'
        """
        if url_or_id.startswith("https://"):
            return url_or_id.split("/")[-1]
        return url_or_id

    def reconstruct_abstract(
        self,
        inverted_index: dict[str, list[int]] | None,
    ) -> str | None:
        """Reconstruct abstract text from OpenAlex inverted index format.

        OpenAlex stores abstracts as inverted indexes for efficiency.
        This method reconstructs the original text.

        Args:
            inverted_index: Dictionary mapping words to position lists.

        Returns:
            Reconstructed abstract text, or None if input is None/empty.

        Example:
            >>> inv_idx = {"Hello": [0], "world": [1]}
            >>> mapper.reconstruct_abstract(inv_idx)
            'Hello world'
        """
        if not inverted_index:
            return None

        # Build list of (position, word) tuples
        word_positions: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        # Sort by position and join
        word_positions.sort(key=lambda x: x[0])
        abstract = " ".join(word for _, word in word_positions)

        # Truncate if too long (abstracts shouldn't be > 10k chars)
        if len(abstract) > 10000:
            abstract = abstract[:10000] + "..."

        return abstract if abstract else None

    def map_paper(self, work: dict[str, Any]) -> Paper:
        """Transform OpenAlex work JSON to Paper model.

        Args:
            work: OpenAlex work JSON response.

        Returns:
            Paper domain model instance.

        Raises:
            ValueError: If required fields are missing.
        """
        openalex_id = self.extract_id(work.get("id", ""))
        if not openalex_id:
            raise ValueError("Work missing id field")

        doi = work.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")

        title = work.get("title") or work.get("display_name") or "Untitled"
        year = work.get("publication_year") or 2000
        citations = work.get("cited_by_count") or 0

        abstract = self.reconstruct_abstract(work.get("abstract_inverted_index"))

        return Paper(
            openalex_id=openalex_id,
            doi=doi,
            title=title,
            year=year,
            citations=citations,
            abstract=abstract,
        )

    def map_authors(self, work: dict[str, Any]) -> list[tuple[Author, int]]:
        """Extract authors with positions from work.

        Args:
            work: OpenAlex work JSON response.

        Returns:
            List of (Author, position) tuples.
        """
        authors: list[tuple[Author, int]] = []
        authorships = work.get("authorships", [])

        for position, authorship in enumerate(authorships):
            author_data = authorship.get("author", {})
            if not author_data:
                continue

            author_id = self.extract_id(author_data.get("id", ""))
            if not author_id or not author_id.startswith("A"):
                continue

            name = author_data.get("display_name", "Unknown")
            orcid = author_data.get("orcid")

            # Get primary institution
            institution = None
            institutions = authorship.get("institutions", [])
            if institutions:
                institution = institutions[0].get("display_name")

            try:
                author = Author(
                    openalex_id=author_id,
                    name=name,
                    orcid=orcid,
                    institution=institution,
                )
                authors.append((author, position))
            except ValueError as e:
                logger.debug("skipping_invalid_author", author_id=author_id, error=str(e))

        return authors

    def map_venue(self, work: dict[str, Any]) -> Venue | None:
        """Extract publication venue from work.

        Args:
            work: OpenAlex work JSON response.

        Returns:
            Venue model or None if not available.
        """
        # Try primary_location first, then best_oa_location
        location = work.get("primary_location") or work.get("best_oa_location")
        if not location:
            return None

        source = location.get("source")
        if not source:
            return None

        venue_id = self.extract_id(source.get("id", ""))
        if not venue_id or not venue_id.startswith("S"):
            return None

        name = source.get("display_name", "Unknown Venue")
        venue_type = source.get("type")
        publisher = source.get("host_organization_name")

        try:
            return Venue(
                openalex_id=venue_id,
                name=name,
                venue_type=venue_type,
                publisher=publisher,
            )
        except ValueError as e:
            logger.debug("skipping_invalid_venue", venue_id=venue_id, error=str(e))
            return None

    def map_topics(self, work: dict[str, Any]) -> list[tuple[Topic, float]]:
        """Extract topics/concepts with scores from work.

        Args:
            work: OpenAlex work JSON response.

        Returns:
            List of (Topic, score) tuples.
        """
        topics: list[tuple[Topic, float]] = []

        # Try topics first (new format), fall back to concepts (legacy)
        topic_list = work.get("topics", []) or work.get("concepts", [])

        for topic_data in topic_list:
            topic_id = self.extract_id(topic_data.get("id", ""))
            if not topic_id:
                continue

            name = topic_data.get("display_name", "Unknown")
            level = topic_data.get("level", 0)
            score = topic_data.get("score", 0.0)

            try:
                topic = Topic(
                    openalex_id=topic_id,
                    name=name,
                    level=level,
                )
                topics.append((topic, score))
            except ValueError as e:
                logger.debug("skipping_invalid_topic", topic_id=topic_id, error=str(e))

        return topics

    def should_include(self, work: dict[str, Any]) -> bool:
        """Check if work meets inclusion criteria.

        Filters based on:
        - Publication year range
        - Required title
        - Optional concept ID filtering

        Args:
            work: OpenAlex work JSON response.

        Returns:
            True if work should be included in the graph.
        """
        # Check year range
        year = work.get("publication_year")
        if year is None:
            logger.debug("filtering_work_no_year", work_id=work.get("id"))
            return False

        if not (self.settings.year_min <= year <= self.settings.year_max):
            logger.debug(
                "filtering_work_year_range",
                work_id=work.get("id"),
                year=year,
                min_year=self.settings.year_min,
                max_year=self.settings.year_max,
            )
            return False

        # Check has title
        if not work.get("title") and not work.get("display_name"):
            logger.debug("filtering_work_no_title", work_id=work.get("id"))
            return False

        # Check CS concepts if configured
        if self.settings.cs_concept_ids:
            work_concept_ids = set()

            # Collect from topics/concepts
            for topic in work.get("topics", []) + work.get("concepts", []):
                topic_id = self.extract_id(topic.get("id", ""))
                if topic_id:
                    work_concept_ids.add(topic_id)

            configured_ids = set(self.settings.cs_concept_ids)
            if not work_concept_ids.intersection(configured_ids):
                logger.debug(
                    "filtering_work_concepts",
                    work_id=work.get("id"),
                )
                return False

        return True

    def get_reference_ids(
        self,
        work: dict[str, Any],
        limit: int = 50,
    ) -> list[str]:
        """Extract referenced work IDs (outgoing citations).

        Args:
            work: OpenAlex work JSON response.
            limit: Maximum number of references to return.

        Returns:
            List of OpenAlex work IDs.
        """
        referenced_works = work.get("referenced_works", [])
        result: list[str] = []

        for ref in referenced_works[:limit]:
            ref_id = self.extract_id(ref) if isinstance(ref, str) else ""
            if ref_id and ref_id.startswith("W"):
                result.append(ref_id)

        return result

    def get_related_work_ids(
        self,
        work: dict[str, Any],
        limit: int = 20,
    ) -> list[str]:
        """Extract related work IDs.

        Args:
            work: OpenAlex work JSON response.
            limit: Maximum number of related works to return.

        Returns:
            List of OpenAlex work IDs.
        """
        related_works = work.get("related_works", [])
        result: list[str] = []

        for rel in related_works[:limit]:
            rel_id = self.extract_id(rel) if isinstance(rel, str) else ""
            if rel_id and rel_id.startswith("W"):
                result.append(rel_id)

        return result
