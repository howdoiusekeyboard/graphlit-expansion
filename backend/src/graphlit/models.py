"""Domain models for academic entities.

This module defines immutable, type-safe dataclasses representing
academic papers, authors, venues, and topics in the citation network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ModelValidationError(ValueError):
    """Raised when model validation fails."""

    pass


@dataclass(frozen=True, slots=True)
class Paper:
    """An academic paper in the citation network.

    Attributes:
        openalex_id: Unique OpenAlex identifier (starts with 'W').
        doi: Digital Object Identifier (optional).
        title: Paper title.
        year: Publication year.
        citations: Number of citations (cited_by_count).
        abstract: Paper abstract text (optional).
    """

    openalex_id: str
    doi: str | None
    title: str
    year: int
    citations: int
    abstract: str | None = None

    def __post_init__(self) -> None:
        """Validate paper attributes after initialization."""
        if not self.openalex_id:
            raise ModelValidationError("openalex_id cannot be empty")
        if not self.openalex_id.startswith("W"):
            raise ModelValidationError(
                f"Invalid OpenAlex paper ID format: {self.openalex_id}. Must start with 'W'."
            )
        if not self.title:
            raise ModelValidationError("title cannot be empty")
        if self.year < 1900 or self.year > 2100:
            raise ModelValidationError(f"Invalid year: {self.year}. Must be between 1900-2100.")
        if self.citations < 0:
            raise ModelValidationError(f"citations cannot be negative: {self.citations}")


@dataclass(frozen=True, slots=True)
class Author:
    """An author of academic papers.

    Attributes:
        openalex_id: Unique OpenAlex identifier (starts with 'A').
        name: Author's display name.
        orcid: ORCID identifier (optional).
        institution: Primary institution affiliation (optional).
    """

    openalex_id: str
    name: str
    orcid: str | None = None
    institution: str | None = None

    def __post_init__(self) -> None:
        """Validate author attributes after initialization."""
        if not self.openalex_id:
            raise ModelValidationError("openalex_id cannot be empty")
        if not self.openalex_id.startswith("A"):
            raise ModelValidationError(
                f"Invalid OpenAlex author ID format: {self.openalex_id}. Must start with 'A'."
            )
        if not self.name:
            raise ModelValidationError("name cannot be empty")


@dataclass(frozen=True, slots=True)
class Venue:
    """A publication venue (journal, conference, etc.).

    Attributes:
        openalex_id: Unique OpenAlex identifier (starts with 'S' for source).
        name: Venue name.
        venue_type: Type of venue (journal, conference, repository, etc.).
        publisher: Publisher name (optional).
    """

    openalex_id: str
    name: str
    venue_type: str | None = None
    publisher: str | None = None

    def __post_init__(self) -> None:
        """Validate venue attributes after initialization."""
        if not self.openalex_id:
            raise ModelValidationError("openalex_id cannot be empty")
        if not self.openalex_id.startswith("S"):
            raise ModelValidationError(
                f"Invalid OpenAlex venue ID format: {self.openalex_id}. Must start with 'S'."
            )
        if not self.name:
            raise ModelValidationError("name cannot be empty")


@dataclass(frozen=True, slots=True)
class Topic:
    """A research topic/concept.

    Attributes:
        openalex_id: Unique OpenAlex identifier (starts with 'T' or 'C' for concepts).
        name: Topic name.
        level: Hierarchy level (0=domain, 1=field, 2=subfield, 3=topic).
    """

    openalex_id: str
    name: str
    level: int

    def __post_init__(self) -> None:
        """Validate topic attributes after initialization."""
        if not self.openalex_id:
            raise ModelValidationError("openalex_id cannot be empty")
        # Topics can start with 'T' (new topics) or 'C' (legacy concepts)
        if not (self.openalex_id.startswith("T") or self.openalex_id.startswith("C")):
            raise ModelValidationError(
                f"Invalid OpenAlex topic ID format: {self.openalex_id}. "
                "Must start with 'T' or 'C'."
            )
        if not self.name:
            raise ModelValidationError("name cannot be empty")
        if self.level < 0 or self.level > 5:
            raise ModelValidationError(f"Invalid topic level: {self.level}. Must be 0-5.")


@dataclass(frozen=True, slots=True)
class Authorship:
    """Relationship between a paper and an author.

    Attributes:
        paper_id: OpenAlex paper ID.
        author_id: OpenAlex author ID.
        position: Author position (0=first author, 1=second, etc.).
    """

    paper_id: str
    author_id: str
    position: int

    def __post_init__(self) -> None:
        """Validate authorship attributes after initialization."""
        if not self.paper_id or not self.paper_id.startswith("W"):
            raise ModelValidationError(f"Invalid paper_id: {self.paper_id}")
        if not self.author_id or not self.author_id.startswith("A"):
            raise ModelValidationError(f"Invalid author_id: {self.author_id}")
        if self.position < 0:
            raise ModelValidationError(f"position cannot be negative: {self.position}")


@dataclass(frozen=True, slots=True)
class TopicAssignment:
    """Relationship between a paper and a topic with relevance score.

    Attributes:
        paper_id: OpenAlex paper ID.
        topic_id: OpenAlex topic ID.
        score: Relevance score (0.0 to 1.0).
    """

    paper_id: str
    topic_id: str
    score: float

    def __post_init__(self) -> None:
        """Validate topic assignment attributes after initialization."""
        if not self.paper_id or not self.paper_id.startswith("W"):
            raise ModelValidationError(f"Invalid paper_id: {self.paper_id}")
        if not self.topic_id:
            raise ModelValidationError("topic_id cannot be empty")
        if not (0.0 <= self.score <= 1.0):
            raise ModelValidationError(f"score must be between 0.0 and 1.0: {self.score}")


@dataclass(frozen=True, slots=True)
class Citation:
    """A citation relationship between two papers.

    Attributes:
        citing_id: OpenAlex ID of the citing paper.
        cited_id: OpenAlex ID of the cited paper.
    """

    citing_id: str
    cited_id: str

    def __post_init__(self) -> None:
        """Validate citation attributes after initialization."""
        if not self.citing_id or not self.citing_id.startswith("W"):
            raise ModelValidationError(f"Invalid citing_id: {self.citing_id}")
        if not self.cited_id or not self.cited_id.startswith("W"):
            raise ModelValidationError(f"Invalid cited_id: {self.cited_id}")
        if self.citing_id == self.cited_id:
            raise ModelValidationError("A paper cannot cite itself")


@dataclass(slots=True)
class ExpansionStats:
    """Statistics for the expansion process.

    Mutable dataclass to track progress during expansion.

    Attributes:
        processed: Number of papers successfully processed.
        skipped: Number of papers skipped (filtered or invalid).
        errors: Number of papers that failed to process.
        api_calls: Total number of API calls made.
        queue_size: Current size of the BFS queue.
    """

    processed: int = field(default=0)
    skipped: int = field(default=0)
    errors: int = field(default=0)
    api_calls: int = field(default=0)
    queue_size: int = field(default=0)

    def increment_processed(self) -> None:
        """Increment processed counter."""
        self.processed += 1

    def increment_skipped(self) -> None:
        """Increment skipped counter."""
        self.skipped += 1

    def increment_errors(self) -> None:
        """Increment errors counter."""
        self.errors += 1

    def increment_api_calls(self) -> None:
        """Increment API calls counter."""
        self.api_calls += 1

    def to_dict(self) -> dict[str, int]:
        """Convert stats to dictionary for logging."""
        return {
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": self.errors,
            "api_calls": self.api_calls,
            "queue_size": self.queue_size,
        }
