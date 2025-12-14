"""Tests for Mapper transformation functions."""

from __future__ import annotations

from typing import Any

import pytest

from graphlit.config import ExpansionSettings
from graphlit.pipeline.mapper import Mapper


@pytest.fixture
def mapper() -> Mapper:
    """Create a mapper with default settings."""
    settings = ExpansionSettings(
        max_papers=1000,
        max_depth=2,
        year_min=2015,
        year_max=2025,
    )
    return Mapper(settings)


@pytest.fixture
def mapper_with_concepts() -> Mapper:
    """Create a mapper with concept filtering."""
    settings = ExpansionSettings(
        max_papers=1000,
        max_depth=2,
        year_min=2015,
        year_max=2025,
        cs_concept_ids=["C41008148"],  # Computer Science
    )
    return Mapper(settings)


class TestExtractId:
    """Tests for extract_id method."""

    def test_extract_from_url(self, mapper: Mapper) -> None:
        """Test extracting ID from full URL."""
        result = mapper.extract_id("https://openalex.org/W123456789")
        assert result == "W123456789"

    def test_extract_from_short_id(self, mapper: Mapper) -> None:
        """Test extracting ID from short ID (passthrough)."""
        result = mapper.extract_id("W123456789")
        assert result == "W123456789"


class TestReconstructAbstract:
    """Tests for reconstruct_abstract method."""

    def test_reconstruct_simple_abstract(
        self,
        mapper: Mapper,
        sample_inverted_index: dict[str, list[int]],
    ) -> None:
        """Test reconstructing a simple abstract."""
        result = mapper.reconstruct_abstract(sample_inverted_index)
        assert result == "This is a test is abstract."

    def test_reconstruct_none_input(self, mapper: Mapper) -> None:
        """Test with None input."""
        result = mapper.reconstruct_abstract(None)
        assert result is None

    def test_reconstruct_empty_input(self, mapper: Mapper) -> None:
        """Test with empty input."""
        result = mapper.reconstruct_abstract({})
        assert result is None


class TestMapPaper:
    """Tests for map_paper method."""

    def test_map_full_paper(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test mapping a complete work."""
        paper = mapper.map_paper(sample_work)

        assert paper.openalex_id == "W2741809807"
        assert paper.doi == "10.1145/3292500.3330919"
        assert paper.title == "Graph Neural Networks: A Review of Methods and Applications"
        assert paper.year == 2021
        assert paper.citations == 1500
        assert paper.abstract is not None
        assert "Graph" in paper.abstract

    def test_map_minimal_paper(
        self,
        mapper: Mapper,
        sample_work_minimal: dict[str, Any],
    ) -> None:
        """Test mapping a minimal work."""
        paper = mapper.map_paper(sample_work_minimal)

        assert paper.openalex_id == "W9999999999"
        assert paper.doi is None
        assert paper.title == "Minimal Paper"
        assert paper.year == 2023
        assert paper.citations == 0
        assert paper.abstract is None

    def test_map_paper_missing_id(self, mapper: Mapper) -> None:
        """Test that missing ID raises error."""
        with pytest.raises(ValueError, match="missing id"):
            mapper.map_paper({})


class TestMapAuthors:
    """Tests for map_authors method."""

    def test_map_authors(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test extracting authors from work."""
        authors = mapper.map_authors(sample_work)

        assert len(authors) == 2
        author1, pos1 = authors[0]
        author2, pos2 = authors[1]

        assert author1.openalex_id == "A5023888391"
        assert author1.name == "Jie Zhou"
        assert author1.institution == "Tsinghua University"
        assert pos1 == 0

        assert author2.openalex_id == "A5012345678"
        assert author2.name == "Ganqu Cui"
        assert author2.institution is None
        assert pos2 == 1

    def test_map_authors_empty(self, mapper: Mapper) -> None:
        """Test with no authors."""
        authors = mapper.map_authors({"authorships": []})
        assert len(authors) == 0


class TestMapVenue:
    """Tests for map_venue method."""

    def test_map_venue(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test extracting venue from work."""
        venue = mapper.map_venue(sample_work)

        assert venue is not None
        assert venue.openalex_id == "S12345678"
        assert venue.name == "AI Open"
        assert venue.venue_type == "journal"
        assert venue.publisher == "Elsevier"

    def test_map_venue_missing(self, mapper: Mapper) -> None:
        """Test with no venue."""
        venue = mapper.map_venue({})
        assert venue is None


class TestMapTopics:
    """Tests for map_topics method."""

    def test_map_topics(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test extracting topics from work."""
        topics = mapper.map_topics(sample_work)

        assert len(topics) >= 2
        topic1, score1 = topics[0]

        assert topic1.openalex_id == "T12345"
        assert topic1.name == "Graph Neural Networks"
        assert topic1.level == 2
        assert score1 == 0.95


class TestShouldInclude:
    """Tests for should_include filtering method."""

    def test_include_valid_work(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test that valid work is included."""
        assert mapper.should_include(sample_work) is True

    def test_exclude_no_year(self, mapper: Mapper) -> None:
        """Test that work without year is excluded."""
        work = {"id": "W123", "title": "Test"}
        assert mapper.should_include(work) is False

    def test_exclude_old_work(
        self,
        mapper: Mapper,
        sample_work_old: dict[str, Any],
    ) -> None:
        """Test that work before year_min is excluded."""
        assert mapper.should_include(sample_work_old) is False

    def test_exclude_no_title(
        self,
        mapper: Mapper,
        sample_work_no_title: dict[str, Any],
    ) -> None:
        """Test that work without title is excluded."""
        assert mapper.should_include(sample_work_no_title) is False

    def test_concept_filtering_include(
        self,
        mapper_with_concepts: Mapper,
        sample_work: dict[str, Any],
    ) -> None:
        """Test that work with matching concept is included."""
        assert mapper_with_concepts.should_include(sample_work) is True

    def test_concept_filtering_exclude(
        self,
        mapper_with_concepts: Mapper,
    ) -> None:
        """Test that work without matching concept is excluded."""
        work = {
            "id": "W123",
            "title": "Biology Paper",
            "publication_year": 2023,
            "concepts": [
                {"id": "https://openalex.org/C12345", "display_name": "Biology"}
            ],
        }
        assert mapper_with_concepts.should_include(work) is False


class TestGetReferenceIds:
    """Tests for get_reference_ids method."""

    def test_get_references(self, mapper: Mapper, sample_work: dict[str, Any]) -> None:
        """Test extracting reference IDs."""
        refs = mapper.get_reference_ids(sample_work)

        assert len(refs) == 3
        assert "W123456789" in refs
        assert "W987654321" in refs

    def test_get_references_with_limit(
        self,
        mapper: Mapper,
        sample_work: dict[str, Any],
    ) -> None:
        """Test limiting number of references."""
        refs = mapper.get_reference_ids(sample_work, limit=2)
        assert len(refs) == 2

    def test_get_references_empty(self, mapper: Mapper) -> None:
        """Test with no references."""
        refs = mapper.get_reference_ids({})
        assert len(refs) == 0


class TestGetRelatedWorkIds:
    """Tests for get_related_work_ids method."""

    def test_get_related_works(
        self,
        mapper: Mapper,
        sample_work: dict[str, Any],
    ) -> None:
        """Test extracting related work IDs."""
        related = mapper.get_related_work_ids(sample_work)

        assert len(related) == 2
        assert "W111111111" in related
