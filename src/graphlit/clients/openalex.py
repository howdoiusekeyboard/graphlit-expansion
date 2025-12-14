"""Async HTTP client for OpenAlex API.

This module provides an async client for interacting with the OpenAlex API
with rate limiting, retry logic, and proper error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import structlog
from aiolimiter import AsyncLimiter

from graphlit.config import OpenAlexSettings
from graphlit.utils.retry import async_retry

if TYPE_CHECKING:
    from types import TracebackType


logger = structlog.get_logger(__name__)


class OpenAlexError(Exception):
    """Base exception for OpenAlex API errors."""

    pass


class OpenAlexRateLimitError(OpenAlexError):
    """Raised when rate limit is exceeded."""

    pass


class OpenAlexNotFoundError(OpenAlexError):
    """Raised when a resource is not found (404)."""

    pass


class OpenAlexClient:
    """Async HTTP client for OpenAlex API.

    Provides rate-limited access to OpenAlex API endpoints with automatic
    retry on transient failures and proper resource management.

    Attributes:
        base_url: OpenAlex API base URL.
        limiter: Async rate limiter for request throttling.

    Example:
        >>> async with OpenAlexClient(settings) as client:
        ...     work = await client.get_work("W2741809807")
        ...     if work:
        ...         print(work["title"])
    """

    def __init__(self, settings: OpenAlexSettings) -> None:
        """Initialize the OpenAlex client.

        Args:
            settings: OpenAlex configuration settings.
        """
        self.base_url = str(settings.base_url).rstrip("/")
        self.limiter = AsyncLimiter(
            max_rate=settings.rate_limit_per_second,
            time_period=1.0,
        )
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.timeout_seconds),
            headers={
                "User-Agent": settings.user_agent,
                "Accept": "application/json",
            },
            follow_redirects=True,
        )
        self._max_retries = settings.max_retries
        self._closed = False

    async def __aenter__(self) -> OpenAlexClient:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close resources."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if not self._closed:
            await self._client.aclose()
            self._closed = True
            logger.debug("openalex_client_closed")

    async def _request(self, url: str) -> dict[str, Any] | None:
        """Make a rate-limited request to the API.

        Args:
            url: Full URL to request.

        Returns:
            JSON response as dict, or None if not found.

        Raises:
            OpenAlexError: On non-recoverable API errors.
        """
        async with self.limiter:
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code == 404:
                    logger.debug("resource_not_found", url=url)
                    return None
                if status_code == 429:
                    logger.warning("rate_limit_exceeded", url=url)
                    raise OpenAlexRateLimitError("Rate limit exceeded") from e
                logger.error("api_error", url=url, status_code=status_code)
                raise OpenAlexError(f"API error: {status_code}") from e

            except httpx.TimeoutException as e:
                logger.warning("request_timeout", url=url)
                raise OpenAlexError("Request timeout") from e

            except httpx.RequestError as e:
                logger.error("request_error", url=url, error=str(e))
                raise OpenAlexError(f"Request error: {e}") from e

    @async_retry(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(OpenAlexError,),
        retry_on=lambda e: not isinstance(e, OpenAlexNotFoundError),
    )
    async def _request_with_retry(self, url: str) -> dict[str, Any] | None:
        """Make a request with automatic retry on transient failures."""
        return await self._request(url)

    async def get_work(self, openalex_id: str) -> dict[str, Any] | None:
        """Fetch a single work by OpenAlex ID.

        Args:
            openalex_id: OpenAlex work ID (e.g., 'W2741809807').

        Returns:
            Work data as dict, or None if not found.

        Example:
            >>> work = await client.get_work("W2741809807")
            >>> print(work["title"])
        """
        # Handle both full URLs and IDs
        if openalex_id.startswith("https://"):
            work_id = openalex_id.split("/")[-1]
        else:
            work_id = openalex_id

        url = f"{self.base_url}/works/{work_id}"
        logger.debug("fetching_work", openalex_id=work_id)

        result = await self._request_with_retry(url)
        if result:
            logger.debug("work_fetched", openalex_id=work_id, title=result.get("title", "")[:50])
        return result

    async def get_work_by_doi(self, doi: str) -> dict[str, Any] | None:
        """Fetch a work by DOI.

        Args:
            doi: Digital Object Identifier (with or without URL prefix).

        Returns:
            Work data as dict, or None if not found.

        Example:
            >>> work = await client.get_work_by_doi("10.1145/3292500.3330919")
        """
        # Normalize DOI format
        if doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        elif doi.startswith("http://doi.org/"):
            doi = doi.replace("http://doi.org/", "")

        url = f"{self.base_url}/works/doi:{doi}"
        logger.debug("fetching_work_by_doi", doi=doi)

        result = await self._request_with_retry(url)
        if result:
            logger.debug(
                "work_fetched_by_doi",
                doi=doi,
                openalex_id=result.get("id", ""),
            )
        return result

    async def get_works_batch(
        self,
        openalex_ids: list[str],
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch multiple works in a single request.

        OpenAlex supports filtering by multiple IDs using the pipe separator.
        This is more efficient than making individual requests.

        Args:
            openalex_ids: List of OpenAlex work IDs.
            per_page: Results per page (max 200).

        Returns:
            List of work data dicts.

        Example:
            >>> works = await client.get_works_batch(["W123", "W456", "W789"])
        """
        if not openalex_ids:
            return []

        # OpenAlex uses short IDs in filter
        short_ids = []
        for oid in openalex_ids:
            if oid.startswith("https://"):
                short_ids.append(oid.split("/")[-1])
            else:
                short_ids.append(oid)

        # Batch in groups of 50 (API limit)
        results: list[dict[str, Any]] = []
        for i in range(0, len(short_ids), per_page):
            batch = short_ids[i : i + per_page]
            filter_value = "|".join(batch)
            url = f"{self.base_url}/works?filter=openalex_id:{filter_value}&per_page={per_page}"

            logger.debug("fetching_works_batch", count=len(batch))
            response = await self._request_with_retry(url)

            if response and "results" in response:
                results.extend(response["results"])

        return results

    async def get_cited_by_works(
        self,
        openalex_id: str,
        per_page: int = 50,
        max_results: int = 100,
    ) -> list[str]:
        """Fetch IDs of works that cite the given work.

        Args:
            openalex_id: OpenAlex work ID.
            per_page: Results per page.
            max_results: Maximum total results to fetch.

        Returns:
            List of OpenAlex IDs of citing works.
        """
        if openalex_id.startswith("https://"):
            work_id = openalex_id.split("/")[-1]
        else:
            work_id = openalex_id

        url = (
            f"{self.base_url}/works?"
            f"filter=cites:{work_id}&"
            f"select=id&"
            f"per_page={min(per_page, max_results)}"
        )

        logger.debug("fetching_cited_by", openalex_id=work_id)
        response = await self._request_with_retry(url)

        if response and "results" in response:
            return [w["id"] for w in response["results"][:max_results]]
        return []

    async def health_check(self) -> bool:
        """Check if the OpenAlex API is accessible.

        Returns:
            True if API is healthy, False otherwise.
        """
        try:
            url = f"{self.base_url}/works?per_page=1"
            response = await self._request(url)
            return response is not None
        except OpenAlexError:
            return False
