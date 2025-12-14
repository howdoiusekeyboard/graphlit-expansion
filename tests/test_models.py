"""Tests for domain models."""

from __future__ import annotations

import pytest

from graphlit.models import (
    Author,
    Authorship,
    Citation,
    ExpansionStats,
    ModelValidationError,
    Paper,
    Topic,
    TopicAssignment,
    Venue,
)


class TestPaper:
    """Tests for Paper model."""

    def test_valid_paper(self) -> None:
        """Test creating a valid paper."""
        paper = Paper(
            openalex_id="W123456789",
            doi="10.1234/test",
            title="Test Paper",
            year=2023,
            citations=100,
            abstract="This is a test.",
        )
        assert paper.openalex_id == "W123456789"
        assert paper.doi == "10.1234/test"
        assert paper.title == "Test Paper"
        assert paper.year == 2023
        assert paper.citations == 100

    def test_paper_without_optional_fields(self) -> None:
        """Test paper without doi and abstract."""
        paper = Paper(
            openalex_id="W123456789",
            doi=None,
            title="Test Paper",
            year=2023,
            citations=0,
        )
        assert paper.doi is None
        assert paper.abstract is None

    def test_invalid_openalex_id(self) -> None:
        """Test that invalid OpenAlex ID raises error."""
        with pytest.raises(ModelValidationError, match="Must start with 'W'"):
            Paper(
                openalex_id="A123456789",  # Wrong prefix
                doi=None,
                title="Test",
                year=2023,
                citations=0,
            )

    def test_empty_openalex_id(self) -> None:
        """Test that empty OpenAlex ID raises error."""
        with pytest.raises(ModelValidationError, match="cannot be empty"):
            Paper(
                openalex_id="",
                doi=None,
                title="Test",
                year=2023,
                citations=0,
            )

    def test_empty_title(self) -> None:
        """Test that empty title raises error."""
        with pytest.raises(ModelValidationError, match="title cannot be empty"):
            Paper(
                openalex_id="W123",
                doi=None,
                title="",
                year=2023,
                citations=0,
            )

    def test_invalid_year(self) -> None:
        """Test that invalid year raises error."""
        with pytest.raises(ModelValidationError, match="Invalid year"):
            Paper(
                openalex_id="W123",
                doi=None,
                title="Test",
                year=1800,  # Too old
                citations=0,
            )

    def test_negative_citations(self) -> None:
        """Test that negative citations raises error."""
        with pytest.raises(ModelValidationError, match="cannot be negative"):
            Paper(
                openalex_id="W123",
                doi=None,
                title="Test",
                year=2023,
                citations=-1,
            )

    def test_paper_is_frozen(self) -> None:
        """Test that paper is immutable."""
        paper = Paper(
            openalex_id="W123",
            doi=None,
            title="Test",
            year=2023,
            citations=0,
        )
        with pytest.raises(AttributeError):
            paper.title = "New Title"  # type: ignore[misc]


class TestAuthor:
    """Tests for Author model."""

    def test_valid_author(self) -> None:
        """Test creating a valid author."""
        author = Author(
            openalex_id="A123456789",
            name="John Doe",
            orcid="0000-0001-2345-6789",
            institution="MIT",
        )
        assert author.openalex_id == "A123456789"
        assert author.name == "John Doe"

    def test_invalid_author_id(self) -> None:
        """Test that invalid author ID raises error."""
        with pytest.raises(ModelValidationError, match="Must start with 'A'"):
            Author(
                openalex_id="W123",  # Wrong prefix
                name="John Doe",
            )


class TestVenue:
    """Tests for Venue model."""

    def test_valid_venue(self) -> None:
        """Test creating a valid venue."""
        venue = Venue(
            openalex_id="S123456789",
            name="Nature",
            venue_type="journal",
            publisher="Springer Nature",
        )
        assert venue.openalex_id == "S123456789"
        assert venue.name == "Nature"

    def test_invalid_venue_id(self) -> None:
        """Test that invalid venue ID raises error."""
        with pytest.raises(ModelValidationError, match="Must start with 'S'"):
            Venue(
                openalex_id="V123",  # Wrong prefix
                name="Nature",
            )


class TestTopic:
    """Tests for Topic model."""

    def test_valid_topic(self) -> None:
        """Test creating a valid topic."""
        topic = Topic(
            openalex_id="T123456789",
            name="Machine Learning",
            level=2,
        )
        assert topic.openalex_id == "T123456789"
        assert topic.level == 2

    def test_topic_with_concept_id(self) -> None:
        """Test topic with legacy concept ID (starts with C)."""
        topic = Topic(
            openalex_id="C41008148",
            name="Computer Science",
            level=0,
        )
        assert topic.openalex_id == "C41008148"

    def test_invalid_topic_level(self) -> None:
        """Test that invalid topic level raises error."""
        with pytest.raises(ModelValidationError, match="Invalid topic level"):
            Topic(
                openalex_id="T123",
                name="Test",
                level=10,  # Too high
            )


class TestAuthorship:
    """Tests for Authorship relationship model."""

    def test_valid_authorship(self) -> None:
        """Test creating a valid authorship."""
        authorship = Authorship(
            paper_id="W123",
            author_id="A456",
            position=0,
        )
        assert authorship.position == 0

    def test_invalid_paper_id(self) -> None:
        """Test that invalid paper ID raises error."""
        with pytest.raises(ModelValidationError, match="Invalid paper_id"):
            Authorship(
                paper_id="A123",  # Wrong prefix
                author_id="A456",
                position=0,
            )


class TestTopicAssignment:
    """Tests for TopicAssignment relationship model."""

    def test_valid_topic_assignment(self) -> None:
        """Test creating a valid topic assignment."""
        assignment = TopicAssignment(
            paper_id="W123",
            topic_id="T456",
            score=0.95,
        )
        assert assignment.score == 0.95

    def test_invalid_score(self) -> None:
        """Test that invalid score raises error."""
        with pytest.raises(ModelValidationError, match="score must be between"):
            TopicAssignment(
                paper_id="W123",
                topic_id="T456",
                score=1.5,  # Too high
            )


class TestCitation:
    """Tests for Citation relationship model."""

    def test_valid_citation(self) -> None:
        """Test creating a valid citation."""
        citation = Citation(
            citing_id="W123",
            cited_id="W456",
        )
        assert citation.citing_id == "W123"
        assert citation.cited_id == "W456"

    def test_self_citation(self) -> None:
        """Test that self-citation raises error."""
        with pytest.raises(ModelValidationError, match="cannot cite itself"):
            Citation(
                citing_id="W123",
                cited_id="W123",
            )


class TestExpansionStats:
    """Tests for ExpansionStats mutable model."""

    def test_default_stats(self) -> None:
        """Test default statistics values."""
        stats = ExpansionStats()
        assert stats.processed == 0
        assert stats.skipped == 0
        assert stats.errors == 0

    def test_increment_methods(self) -> None:
        """Test increment methods."""
        stats = ExpansionStats()
        stats.increment_processed()
        stats.increment_processed()
        stats.increment_skipped()
        stats.increment_errors()
        stats.increment_api_calls()

        assert stats.processed == 2
        assert stats.skipped == 1
        assert stats.errors == 1
        assert stats.api_calls == 1

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        stats = ExpansionStats(processed=10, skipped=5, errors=2)
        result = stats.to_dict()

        assert result["processed"] == 10
        assert result["skipped"] == 5
        assert result["errors"] == 2
