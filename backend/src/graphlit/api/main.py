"""FastAPI application for GraphLit ResearchRadar API.

This module provides the main FastAPI application with:
- Recommendation endpoints (collaborative filtering)
- Admin endpoints (cache management)
- Health check
- CORS middleware
- Lifespan management for connections

To run the API server:
    uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    pass

from graphlit.api.dependencies import shutdown_connections
from graphlit.api.routes import admin, recommendations

logger = structlog.get_logger(__name__)


# =============================================================================
# Lifespan Context Manager
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle (startup/shutdown).

    Handles:
    - Logging application startup
    - Graceful shutdown of Neo4j and Redis connections

    Args:
        app: FastAPI application instance.

    Yields:
        None (allows application to run).
    """
    # Startup
    logger.info(
        "api_startup",
        title=app.title,
        version=app.version,
        docs_url=app.docs_url,
    )

    yield

    # Shutdown
    logger.info("api_shutdown")
    await shutdown_connections()


# =============================================================================
# FastAPI Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance with:
        - Recommendation routes
        - Admin routes
        - CORS middleware
        - Lifespan management
    """
    app = FastAPI(
        title="ResearchRadar API",
        description=(
            "AI-powered citation intelligence platform for academic literature. "
            "Provides collaborative filtering recommendations, community detection, "
            "and predictive impact scoring."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ==========================================================================
    # CORS Middleware
    # ==========================================================================

    # TODO: Restrict origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins (development only)
        allow_credentials=True,
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all headers
    )

    # ==========================================================================
    # Router Registration
    # ==========================================================================

    app.include_router(recommendations.router)
    app.include_router(admin.router)

    # ==========================================================================
    # Health Check Endpoint
    # ==========================================================================

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Simple health status.
        """
        return {"status": "healthy", "service": "ResearchRadar API"}

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information.

        Returns:
            API metadata and links.
        """
        return {
            "service": "ResearchRadar API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "recommendations": "/api/v1/recommendations",
            "admin": "/api/v1/admin",
        }

    return app


# =============================================================================
# Application Instance
# =============================================================================

# For uvicorn: uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8000 --reload
app = create_app()
