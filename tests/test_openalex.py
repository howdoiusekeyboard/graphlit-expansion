"""Tests for OpenAlex API client."""

from __future__ import annotations

from typing import Any

import pytest

from graphlit.clients.openalex import OpenAlexClient
from graphlit.config import OpenAlexSettings


@pytest.fixture
def settings() -> OpenAlexSettings:
    """Create test settings."""
    return OpenAlexSettings(
        base_url="https://api.openalex.org",
        user_agent="GraphLit-Test/1.0",
        rate_limit_per_second=100,  # High limit for tests
        timeout_seconds=5,
        max_retries=1,
    )


@pytest.fixture
def mock_work_response() -> dict[str, Any]:
    """Mock OpenAlex work response."""
    return {
        "id": "https://openalex.org/W2741809807",
        "doi": "https://doi.org/10.1234/test",
        "title": "Test Paper",
        "publication_year": 2023,
        "cited_by_count": 100,
    }


class TestOpenAlexClient:
    """Tests for OpenAlexClient."""

    @pytest.mark.asyncio
    async def test_get_work_success(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
        mock_work_response: dict[str, Any],
    ) -> None:
        """Test successful work fetch."""
        httpx_mock.add_response(
            url="https://api.openalex.org/works/W2741809807",
            json=mock_work_response,
        )

        async with OpenAlexClient(settings) as client:
            work = await client.get_work("W2741809807")

        assert work is not None
        assert work["id"] == "https://openalex.org/W2741809807"
        assert work["title"] == "Test Paper"

    @pytest.mark.asyncio
    async def test_get_work_not_found(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
    ) -> None:
        """Test 404 response returns None."""
        httpx_mock.add_response(
            url="https://api.openalex.org/works/W9999999999",
            status_code=404,
        )

        async with OpenAlexClient(settings) as client:
            work = await client.get_work("W9999999999")

        assert work is None

    @pytest.mark.asyncio
    async def test_get_work_by_doi(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
        mock_work_response: dict[str, Any],
    ) -> None:
        """Test fetching work by DOI."""
        httpx_mock.add_response(
            url="https://api.openalex.org/works/doi:10.1234/test",
            json=mock_work_response,
        )

        async with OpenAlexClient(settings) as client:
            work = await client.get_work_by_doi("10.1234/test")

        assert work is not None
        assert work["doi"] == "https://doi.org/10.1234/test"

    @pytest.mark.asyncio
    async def test_get_work_by_doi_with_url_prefix(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
        mock_work_response: dict[str, Any],
    ) -> None:
        """Test fetching work by DOI with URL prefix."""
        httpx_mock.add_response(
            url="https://api.openalex.org/works/doi:10.1234/test",
            json=mock_work_response,
        )

        async with OpenAlexClient(settings) as client:
            work = await client.get_work_by_doi("https://doi.org/10.1234/test")

        assert work is not None

    @pytest.mark.asyncio
    async def test_get_work_with_full_url(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
        mock_work_response: dict[str, Any],
    ) -> None:
        """Test fetching work with full OpenAlex URL."""
        httpx_mock.add_response(
            url="https://api.openalex.org/works/W2741809807",
            json=mock_work_response,
        )

        async with OpenAlexClient(settings) as client:
            work = await client.get_work("https://openalex.org/W2741809807")

        assert work is not None

    @pytest.mark.asyncio
    async def test_get_works_batch(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
    ) -> None:
        """Test batch fetching works."""
        batch_response = {
            "results": [
                {"id": "https://openalex.org/W123", "title": "Paper 1"},
                {"id": "https://openalex.org/W456", "title": "Paper 2"},
            ]
        }
        httpx_mock.add_response(
            method="GET",
            json=batch_response,
        )

        async with OpenAlexClient(settings) as client:
            works = await client.get_works_batch(["W123", "W456"])

        assert len(works) == 2

    @pytest.mark.asyncio
    async def test_get_works_batch_empty(
        self,
        settings: OpenAlexSettings,
    ) -> None:
        """Test batch fetch with empty list."""
        async with OpenAlexClient(settings) as client:
            works = await client.get_works_batch([])

        assert works == []

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
    ) -> None:
        """Test health check returns True on success."""
        httpx_mock.add_response(
            json={"results": [{"id": "W1"}]},
        )

        async with OpenAlexClient(settings) as client:
            healthy = await client.health_check()

        assert healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
    ) -> None:
        """Test health check returns False on failure."""
        httpx_mock.add_response(status_code=500)

        async with OpenAlexClient(settings) as client:
            healthy = await client.health_check()

        assert healthy is False

    @pytest.mark.asyncio
    async def test_context_manager(
        self,
        settings: OpenAlexSettings,
    ) -> None:
        """Test async context manager properly closes client."""
        client = OpenAlexClient(settings)
        async with client:
            assert client._closed is False
        assert client._closed is True

    @pytest.mark.asyncio
    async def test_get_cited_by_works(
        self,
        httpx_mock: Any,
        settings: OpenAlexSettings,
    ) -> None:
        """Test fetching citing works."""
        response = {
            "results": [
                {"id": "https://openalex.org/W111"},
                {"id": "https://openalex.org/W222"},
            ]
        }
        httpx_mock.add_response(json=response)

        async with OpenAlexClient(settings) as client:
            citing = await client.get_cited_by_works("W123")

        assert len(citing) == 2
        assert "https://openalex.org/W111" in citing
