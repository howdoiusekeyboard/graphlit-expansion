"""Query and endpoint performance profiling decorators.

This module provides decorators to measure execution time of async functions,
with automatic logging of slow queries and endpoints.
"""

from __future__ import annotations

import functools
import time
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import structlog

if TYPE_CHECKING:
    from collections.abc import Awaitable

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def profile_endpoint(endpoint_name: str, slow_threshold_ms: float = 500.0) -> Callable[[F], F]:
    """Decorator to profile API endpoint execution time.

    Logs execution time for all requests. Logs a warning if execution
    time exceeds the slow threshold.

    Args:
        endpoint_name: Human-readable name of the endpoint for logging.
        slow_threshold_ms: Threshold in milliseconds above which to log a warning.
            Default: 500ms.

    Returns:
        Decorated function that tracks execution time.

    Example:
        >>> @profile_endpoint("get_paper_recommendations", slow_threshold_ms=300.0)
        >>> async def get_paper_recommendations(paper_id: str) -> list[dict]:
        ...     # endpoint implementation
        ...     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            log_context = {
                "endpoint": endpoint_name,
                "elapsed_ms": round(elapsed_ms, 2),
            }

            if elapsed_ms > slow_threshold_ms:
                logger.warning(
                    "slow_endpoint",
                    **log_context,
                    threshold_ms=slow_threshold_ms,
                )
            else:
                logger.info("endpoint_executed", **log_context)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def profile_query(query_name: str, slow_threshold_ms: float = 300.0) -> Callable[[F], F]:
    """Decorator to profile database query execution time.

    Logs execution time for all queries. Logs a warning if execution
    time exceeds the slow threshold.

    Args:
        query_name: Human-readable name of the query for logging.
        slow_threshold_ms: Threshold in milliseconds above which to log a warning.
            Default: 300ms.

    Returns:
        Decorated function that tracks execution time.

    Example:
        >>> @profile_query("get_citation_overlap_papers", slow_threshold_ms=200.0)
        >>> async def get_citation_based_candidates(paper_id: str) -> list[dict]:
        ...     # query implementation
        ...     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            log_context = {
                "query": query_name,
                "elapsed_ms": round(elapsed_ms, 2),
            }

            if elapsed_ms > slow_threshold_ms:
                logger.warning(
                    "slow_query",
                    **log_context,
                    threshold_ms=slow_threshold_ms,
                )
            else:
                logger.debug("query_executed", **log_context)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator
