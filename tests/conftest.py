"""Pytest fixtures for GraphLit tests."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def sample_work() -> dict[str, Any]:
    """Sample OpenAlex work JSON response."""
    return {
        "id": "https://openalex.org/W2741809807",
        "doi": "https://doi.org/10.1145/3292500.3330919",
        "title": "Graph Neural Networks: A Review of Methods and Applications",
        "display_name": "Graph Neural Networks: A Review of Methods and Applications",
        "publication_year": 2021,
        "cited_by_count": 1500,
        "abstract_inverted_index": {
            "Graph": [0],
            "neural": [1],
            "networks": [2],
            "have": [3],
            "achieved": [4],
            "great": [5],
            "success": [6],
        },
        "authorships": [
            {
                "author": {
                    "id": "https://openalex.org/A5023888391",
                    "display_name": "Jie Zhou",
                    "orcid": "https://orcid.org/0000-0001-2345-6789",
                },
                "institutions": [
                    {"display_name": "Tsinghua University"}
                ],
                "author_position": "first",
            },
            {
                "author": {
                    "id": "https://openalex.org/A5012345678",
                    "display_name": "Ganqu Cui",
                    "orcid": None,
                },
                "institutions": [],
                "author_position": "middle",
            },
        ],
        "primary_location": {
            "source": {
                "id": "https://openalex.org/S12345678",
                "display_name": "AI Open",
                "type": "journal",
                "host_organization_name": "Elsevier",
            }
        },
        "topics": [
            {
                "id": "https://openalex.org/T12345",
                "display_name": "Graph Neural Networks",
                "level": 2,
                "score": 0.95,
            },
            {
                "id": "https://openalex.org/T67890",
                "display_name": "Deep Learning",
                "level": 1,
                "score": 0.88,
            },
        ],
        "concepts": [
            {
                "id": "https://openalex.org/C41008148",
                "display_name": "Computer Science",
                "level": 0,
                "score": 0.92,
            },
        ],
        "referenced_works": [
            "https://openalex.org/W123456789",
            "https://openalex.org/W987654321",
            "https://openalex.org/W555555555",
        ],
        "related_works": [
            "https://openalex.org/W111111111",
            "https://openalex.org/W222222222",
        ],
    }


@pytest.fixture
def sample_work_minimal() -> dict[str, Any]:
    """Minimal OpenAlex work with only required fields."""
    return {
        "id": "https://openalex.org/W9999999999",
        "title": "Minimal Paper",
        "publication_year": 2023,
        "cited_by_count": 0,
    }


@pytest.fixture
def sample_work_no_title() -> dict[str, Any]:
    """OpenAlex work missing title (should be filtered)."""
    return {
        "id": "https://openalex.org/W8888888888",
        "publication_year": 2023,
        "cited_by_count": 5,
    }


@pytest.fixture
def sample_work_old() -> dict[str, Any]:
    """OpenAlex work from before year filter (should be filtered)."""
    return {
        "id": "https://openalex.org/W7777777777",
        "title": "Old Paper",
        "publication_year": 2010,
        "cited_by_count": 100,
    }


@pytest.fixture
def sample_inverted_index() -> dict[str, list[int]]:
    """Sample inverted index for abstract reconstruction."""
    return {
        "This": [0],
        "is": [1, 4],
        "a": [2],
        "test": [3],
        "abstract.": [5],
    }
