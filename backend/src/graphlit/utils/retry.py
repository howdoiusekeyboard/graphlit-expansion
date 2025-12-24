"""Async retry utilities with exponential backoff.

This module provides decorators and utilities for handling transient failures
in async operations with configurable retry logic and backoff strategies.
"""

from __future__ import annotations

import asyncio
import functools
import random
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

import structlog

P = ParamSpec("P")
T = TypeVar("T")

logger = structlog.get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, attempts: int, last_exception: Exception) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Current attempt number (0-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter: If True, add random jitter to prevent thundering herd.

    Returns:
        Calculated delay in seconds.

    Example:
        >>> calculate_backoff(0)  # ~1.0 seconds
        >>> calculate_backoff(3)  # ~8.0 seconds (capped at max_delay)
    """
    delay: float = min(base_delay * (2**attempt), max_delay)
    if jitter:
        jitter_factor: float = 0.5 + random.random()
        delay = delay * jitter_factor
    return delay


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    retry_on: Callable[[Exception], bool] | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """Decorator for async functions with exponential backoff retry.

    Retries the decorated async function on specified exceptions with
    exponential backoff between attempts.

    Args:
        max_retries: Maximum number of retry attempts (0 = no retries).
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry.
        retry_on: Optional callable to determine if exception should trigger retry.

    Returns:
        Decorator function.

    Raises:
        RetryError: When all retry attempts are exhausted.

    Example:
        >>> @async_retry(max_retries=3, exceptions=(httpx.HTTPError,))
        ... async def fetch_data(url: str) -> dict:
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url)
        ...         return response.json()
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if we should retry this specific exception
                    if retry_on is not None and not retry_on(e):
                        raise

                    # Check if we have retries left
                    if attempt >= max_retries:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e),
                        )
                        raise RetryError(
                            f"Failed after {attempt + 1} attempts: {e}",
                            attempts=attempt + 1,
                            last_exception=e,
                        ) from e

                    # Calculate and apply backoff
                    delay = calculate_backoff(attempt, base_delay, max_delay)
                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=round(delay, 2),
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

            # This should never be reached, but satisfies type checker
            assert last_exception is not None
            raise RetryError(
                f"Failed after {max_retries + 1} attempts",
                attempts=max_retries + 1,
                last_exception=last_exception,
            )

        return wrapper

    return decorator


def should_retry_http_error(exception: Exception) -> bool:
    """Determine if an HTTP error should trigger a retry.

    Retries on:
    - 429 Too Many Requests (rate limit)
    - 500, 502, 503, 504 (server errors)
    - Connection/Timeout errors

    Does NOT retry on:
    - 400, 401, 403, 404 (client errors)

    Args:
        exception: The exception to evaluate.

    Returns:
        True if the exception should trigger a retry.
    """
    # Import here to avoid circular imports and optional dependency issues
    try:
        import httpx

        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code in {429, 500, 502, 503, 504}
        if isinstance(exception, httpx.TimeoutException | httpx.ConnectError):
            return True
    except ImportError:
        pass

    return False


async def retry_async[T](
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Execute an async callable with retry logic.

    Functional alternative to the decorator for one-off retries.

    Args:
        func: Async callable to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay for exponential backoff.
        max_delay: Maximum delay cap.
        exceptions: Tuple of exception types to catch.

    Returns:
        Result of the callable.

    Raises:
        RetryError: When all retry attempts are exhausted.

    Example:
        >>> result = await retry_async(
        ...     lambda: fetch_paper("W123"),
        ...     max_retries=3,
        ... )
    """

    @async_retry(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exceptions=exceptions,
    )
    async def wrapper() -> T:
        return await func()

    return await wrapper()
