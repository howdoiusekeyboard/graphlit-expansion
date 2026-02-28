"""FastAPI application for GraphLit ResearchRadar API.

This module provides the main FastAPI application with:
- Recommendation endpoints (collaborative filtering)
- Admin endpoints (cache management)
- Health check
- CORS middleware
- Lifespan management for connections

To run the API server:
    uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    pass

from graphlit.api.dependencies import get_neo4j_client, shutdown_connections
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

    allowed_origins = [
        "https://graphlit.kushagragolash.tech",
        "https://graphlit-expansion.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )

    # ==========================================================================
    # Router Registration
    # ==========================================================================

    app.include_router(recommendations.router)
    app.include_router(admin.router)

    # ==========================================================================
    # Health Check Endpoint
    # ==========================================================================

    @app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint that verifies Neo4j connectivity.

        Pings Neo4j with a lightweight read query (RETURN 1) to keep
        both Koyeb and AuraDB Free alive via external cron pings.

        Returns:
            Health status with Neo4j connectivity info.
        """
        neo4j_status = "unknown"
        try:
            client = await get_neo4j_client()
            if await client.verify_connection():
                neo4j_status = "connected"
            else:
                neo4j_status = "disconnected"
        except Exception as exc:
            logger.warning("neo4j_health_check_failed", error=str(exc))
            neo4j_status = "error"

        status = "healthy" if neo4j_status == "connected" else "degraded"
        return {"status": status, "service": "ResearchRadar API", "neo4j": neo4j_status}

    @app.api_route("/", methods=["GET", "HEAD"], tags=["root"])
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

# For uvicorn: uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8080 --reload
app = create_app()
