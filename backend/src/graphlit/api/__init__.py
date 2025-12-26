"""FastAPI REST API for GraphLit ResearchRadar.

This module provides the main FastAPI application with recommendation
endpoints, admin endpoints, and health checks.

Usage:
    >>> from graphlit.api import app
    >>>
    >>> # Run with uvicorn
    >>> # uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

__all__ = ["app", "create_app"]


def __getattr__(name: str) -> object:
    """Lazy import to avoid loading FastAPI unless needed."""
    if name == "app":
        from graphlit.api.main import app

        return app

    if name == "create_app":
        from graphlit.api.main import create_app

        return create_app

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
