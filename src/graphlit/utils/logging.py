"""Structured logging configuration using structlog.

This module configures structlog for JSON-structured logging with
proper formatting, timestamps, and log level filtering.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog
from structlog.typing import FilteringBoundLogger

if TYPE_CHECKING:
    from structlog.types import Processor


def setup_logging(*, debug: bool = False) -> None:
    """Configure structured logging for the application.

    Sets up structlog with:
    - ISO timestamp formatting
    - Log level filtering based on debug flag
    - Console rendering with colors for development
    - Context variable merging for request tracking

    Args:
        debug: If True, sets log level to DEBUG; otherwise INFO.

    Example:
        >>> setup_logging(debug=True)
        >>> logger = structlog.get_logger(__name__)
        >>> logger.info("message", key="value")
    """
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Define processor chain
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True, pad_event=30),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module).

    Returns:
        A bound logger instance with context support.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_started", paper_id="W123")
    """
    logger: FilteringBoundLogger = structlog.get_logger(name)
    return logger
