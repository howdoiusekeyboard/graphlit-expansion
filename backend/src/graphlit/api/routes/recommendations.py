"""Recommendation API endpoints.

This module provides REST API endpoints for paper recommendations using
the collaborative filtering engine with Redis caching.

Endpoints:
- GET /paper/{paper_id} - Recommendations for a specific paper
- POST /query - Query-based recommendations
- GET /community/{community_id}/trending - Trending papers in community
- GET /feed/{user_session_id} - Personalized user feed (placeholder)
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from graphlit.api.dependencies import get_neo4j_client, get_recommender, get_redis_cache
from graphlit.cache.redis_cache import RecommendationCache
from graphlit.database import queries
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.recommendations.collaborative_filter import (
    CollaborativeFilterError,
    CollaborativeFilterRecommender,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["recommendations"],
)


# =============================================================================
# Pydantic Models
# =============================================================================


class RecommendationItem(BaseModel):
    """Single recommendation item."""

    paper_id: str = Field(..., description="OpenAlex paper ID")
    title: str = Field(..., description="Paper title")
    year: int | None = Field(None, description="Publication year")
    citations: int = Field(..., description="Citation count")
    impact_score: float | None = Field(None, description="Predictive Impact Score (0-100)")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    recommendation_reason: str = Field(..., description="Primary recommendation method")
    component_scores: dict[str, float] | None = Field(
        None, description="Component similarity scores"
    )


class PaperDetailItem(BaseModel):
    """Full paper metadata."""

    paper_id: str
    title: str
    year: int | None
    citations: int
    impact_score: float | None
    abstract: str | None
    doi: str | None
    community: int | None
    topics: list[str] = []


class RecommendationsResponse(BaseModel):
    """Response for recommendation endpoints."""

    recommendations: list[RecommendationItem]
    total: int = Field(..., description="Number of recommendations returned")
    cached: bool = Field(..., description="Whether result was cached")
    cache_ttl_seconds: int | None = Field(None, description="Cache TTL if cached")


class CommunityListItem(BaseModel):
    """Summary of a community cluster."""

    id: int
    paper_count: int
    avg_impact: float | None
    top_topics: list[str] = []


class CommunitiesResponse(BaseModel):
    """Response for communities list endpoint."""

    communities: list[CommunityListItem]
    total: int


class TrendingPaperItem(BaseModel):
    """Trending paper in a community."""

    paper_id: str
    title: str
    year: int | None
    citations: int
    impact_score: float | None
    citation_velocity: float | None
    topic_momentum: float | None


class TrendingPapersResponse(BaseModel):
    """Response for trending papers endpoint."""

    community_id: int
    community_label: str | None
    trending_papers: list[TrendingPaperItem]
    total: int


# =============================================================================
# Endpoint 1: Recommendations for a Paper
# =============================================================================


@router.get("/paper/{paper_id}", response_model=RecommendationsResponse)
async def get_paper_recommendations(
    paper_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum recommendations to return"),
    min_similarity: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum similarity threshold"
    ),
    recommender: CollaborativeFilterRecommender = Depends(get_recommender),
    cache: RecommendationCache = Depends(get_redis_cache),
) -> RecommendationsResponse:
    """Get personalized recommendations for a specific paper.

    Uses collaborative filtering with 4 similarity methods:
    - Citation overlap (35%)
    - Topic affinity (30%)
    - Author collaboration (20%)
    - Citation velocity (15%)

    Args:
        paper_id: OpenAlex paper ID (e.g., W123456789)
        limit: Maximum number of recommendations (1-50)
        min_similarity: Minimum similarity score filter (0-1)
        recommender: Injected recommendation engine
        cache: Injected Redis cache

    Returns:
        RecommendationsResponse with list of recommendations and metadata.

    Raises:
        HTTPException 404: Paper not found or no recommendations available
        HTTPException 500: Recommendation engine failure
    """
    logger.info(
        "api_get_paper_recommendations",
        paper_id=paper_id,
        limit=limit,
        min_similarity=min_similarity,
    )

    # Generate cache key
    cache_key = f"recommendations:paper:{paper_id}:{limit}:{min_similarity}"

    # Try cache first
    cached_recommendations = await cache.get_recommendations(cache_key)
    if cached_recommendations is not None:
        logger.info("cache_hit", cache_key=cache_key)
        return RecommendationsResponse(
            recommendations=[
                RecommendationItem.model_validate(rec) for rec in cached_recommendations
            ],
            total=len(cached_recommendations),
            cached=True,
            cache_ttl_seconds=3600,
        )

    # Cache miss - compute recommendations
    try:
        recommendations = await recommender.get_paper_recommendations(
            paper_id=paper_id,
            limit=limit,
            min_similarity=min_similarity,
        )

        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for paper {paper_id}",
            )

        # Store in cache (best-effort)
        await cache.set_recommendations(cache_key, recommendations, ttl_seconds=3600)

        return RecommendationsResponse(
            recommendations=[
                RecommendationItem.model_validate(rec) for rec in recommendations
            ],
            total=len(recommendations),
            cached=False,
            cache_ttl_seconds=None,
        )

    except CollaborativeFilterError as e:
        logger.error("recommendation_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 2: Query-Based Recommendations (Placeholder)
# =============================================================================


class QueryRequest(BaseModel):
    """Request body for query-based recommendations."""

    topics: list[str] = Field(..., description="Topic keywords to match")
    exclude_papers: list[str] = Field(
        default_factory=list, description="Paper IDs to exclude"
    )
    year_min: int | None = Field(None, ge=1900, le=2100, description="Minimum year")
    year_max: int | None = Field(None, ge=1900, le=2100, description="Maximum year")
    limit: int = Field(10, ge=1, le=50, description="Maximum results")


@router.post("/query", response_model=RecommendationsResponse)
async def query_recommendations(
    request: QueryRequest,
    client: Neo4jClient = Depends(get_neo4j_client),
    cache: RecommendationCache = Depends(get_redis_cache),
) -> RecommendationsResponse:
    """Get recommendations based on query criteria (placeholder).

    Note: This is a simplified implementation that returns top papers by impact score.
    Full query-based filtering will be implemented in a future iteration.

    Args:
        request: Query parameters (topics, year range, exclusions)
        client: Injected Neo4j client
        cache: Injected Redis cache

    Returns:
        RecommendationsResponse with query results.
    """
    logger.info("api_query_recommendations", request=request.model_dump())

    # Generate cache key from query hash
    import hashlib
    import json

    query_hash = hashlib.md5(
        json.dumps(request.model_dump(), sort_keys=True).encode()
    ).hexdigest()
    cache_key = f"recommendations:query:{query_hash}"

    # Try cache
    cached = await cache.get_recommendations(cache_key)
    if cached is not None:
        return RecommendationsResponse(
            recommendations=[
                RecommendationItem.model_validate(rec) for rec in cached
            ],
            total=len(cached),
            cached=True,
            cache_ttl_seconds=3600,
        )

    # Fetch top papers (simplified - no topic filtering yet)
    try:
        async with client.session() as session:
            result = await session.run(
                queries.GET_ALL_PAPERS_WITH_SCORES,
                limit=request.limit,
            )
            records = await result.data()

        # Convert to recommendation format
        recommendations = [
            {
                "paper_id": str(rec["paper_id"]),
                "title": str(rec["title"]),
                "year": int(rec["year"]) if rec["year"] else None,
                "citations": int(rec["citations"]) if rec["citations"] else 0,
                "impact_score": float(rec["impact_score"]) if rec["impact_score"] else None,
                "similarity_score": 1.0,
                "recommendation_reason": "high_impact",
                "component_scores": None,
            }
            for rec in records
            if rec["paper_id"] not in request.exclude_papers
        ]

        # Cache result
        await cache.set_recommendations(cache_key, recommendations, ttl_seconds=3600)

        return RecommendationsResponse(
            recommendations=[
                RecommendationItem.model_validate(rec) for rec in recommendations
            ],
            total=len(recommendations),
            cached=False,
            cache_ttl_seconds=None,
        )

    except Exception as e:
        logger.error("query_recommendations_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 3: Trending Papers in Community
# =============================================================================


@router.get(
    "/community/{community_id}/trending",
    response_model=TrendingPapersResponse,
)
async def get_trending_papers(
    community_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum papers to return"),
    min_year: int = Query(2020, ge=1900, le=2100, description="Minimum publication year"),
    client: Neo4jClient = Depends(get_neo4j_client),
    cache: RecommendationCache = Depends(get_redis_cache),
) -> TrendingPapersResponse:
    """Get trending papers in a community.

    Returns recent high-impact papers in the specified community,
    sorted by topic momentum and impact score.

    Args:
        community_id: Community ID from Louvain detection
        limit: Maximum papers to return (1-50)
        min_year: Minimum publication year
        client: Injected Neo4j client
        cache: Injected Redis cache

    Returns:
        TrendingPapersResponse with trending papers.

    Raises:
        HTTPException 404: Community not found
        HTTPException 500: Query failure
    """
    logger.info(
        "api_get_trending_papers",
        community_id=community_id,
        limit=limit,
        min_year=min_year,
    )

    # Cache key
    cache_key = f"recommendations:community:{community_id}:{limit}:{min_year}"

    # Try cache (4 hour TTL for community data)
    cached = await cache.get_recommendations(cache_key)
    if cached is not None:
        return TrendingPapersResponse(
            community_id=community_id,
            community_label=cached[0].get("community_label") if cached else None,
            trending_papers=[
                TrendingPaperItem.model_validate(p) for p in cached
            ],
            total=len(cached),
        )

    # Fetch trending papers
    try:
        async with client.session() as session:
            result = await session.run(
                queries.GET_COMMUNITY_TRENDING_PAPERS,
                community_id=community_id,
                min_year=min_year,
                limit=limit,
            )
            records = await result.data()

            if not records:
                raise HTTPException(
                    status_code=404,
                    detail=f"Community {community_id} not found or has no papers",
                )

            # Convert to response format
            trending = [
                {
                    "paper_id": str(rec["paper_id"]),
                    "title": str(rec["title"]),
                    "year": int(rec["year"]) if rec["year"] else None,
                    "citations": int(rec["citations"]) if rec["citations"] else 0,
                    "impact_score": float(rec["impact_score"])
                    if rec["impact_score"]
                    else None,
                    "citation_velocity": float(rec["citation_velocity"])
                    if rec["citation_velocity"]
                    else None,
                    "topic_momentum": float(rec["topic_momentum"])
                    if rec["topic_momentum"]
                    else None,
                }
                for rec in records
            ]

            # Get community label (fetch from first paper or use generic)
            community_label = f"Community {community_id}"

            # Cache result (4 hours)
            cache_data = [
                {**p, "community_label": community_label} for p in trending
            ]
            await cache.set_recommendations(cache_key, cache_data, ttl_seconds=14400)

            return TrendingPapersResponse(
                community_id=community_id,
                community_label=community_label,
                trending_papers=[
                    TrendingPaperItem.model_validate(p) for p in trending
                ],
                total=len(trending),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("trending_papers_failed", community_id=community_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trending papers: {str(e)}",
        ) from e


# =============================================================================
# Endpoint 4: Personalized User Feed (Placeholder)
# =============================================================================


@router.get("/feed/{user_session_id}", response_model=RecommendationsResponse)
async def get_personalized_feed(
    user_session_id: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum papers to return"),
) -> RecommendationsResponse:
    """Get personalized recommendation feed for a user (placeholder).

    Note: This is a placeholder for future user personalization features.
    Currently returns an empty list.

    Args:
        user_session_id: User session identifier
        limit: Maximum papers to return

    Returns:
        Empty RecommendationsResponse (placeholder).
    """
    logger.info("api_get_personalized_feed", user_session_id=user_session_id)

    # Placeholder - return empty
    return RecommendationsResponse(
        recommendations=[],
        total=0,
        cached=False,
        cache_ttl_seconds=None,
    )


# =============================================================================
# Endpoint 5: Paper Detail
# =============================================================================


@router.get("/paper/{paper_id}/detail", response_model=PaperDetailItem)
async def get_paper_detail(
    paper_id: str,
    client: Neo4jClient = Depends(get_neo4j_client),
) -> PaperDetailItem:
    """Get full metadata for a specific paper."""
    logger.info("api_get_paper_detail", paper_id=paper_id)

    try:
        async with client.session() as session:
            result = await session.run(queries.GET_PAPER, openalex_id=paper_id)
            record = await result.single()

            if not record:
                raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

            p = record["p"]

            # Fetch topics
            topic_result = await session.run(
                "MATCH (p:Paper {openalex_id: $id})-[:BELONGS_TO_TOPIC]->(t:Topic) RETURN t.name AS name",
                id=paper_id,
            )
            topics = [rec["name"] for rec in await topic_result.data()]

            return PaperDetailItem(
                paper_id=p["openalex_id"],
                title=p["title"],
                year=p.get("year"),
                citations=p.get("citations", 0),
                impact_score=p.get("impact_score"),
                abstract=p.get("abstract"),
                doi=p.get("doi"),
                community=p.get("community"),
                topics=topics,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_detail_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# =============================================================================
# Endpoint 5.1: Paper Citation Network
# =============================================================================


class CitationNetworkNode(BaseModel):
    paper_id: str
    title: str
    year: int | None
    citations: int
    impact_score: float | None
    community: int | None


class CitationNetworkEdge(BaseModel):
    source: str
    target: str


class CitationNetworkResponse(BaseModel):
    papers: list[CitationNetworkNode]
    citations: list[CitationNetworkEdge]


@router.get("/paper/{paper_id}/network", response_model=CitationNetworkResponse)
async def get_paper_network(
    paper_id: str,
    client: Neo4jClient = Depends(get_neo4j_client),
) -> CitationNetworkResponse:
    """Get citation network (1-hop) for a specific paper."""
    logger.info("api_get_paper_network", paper_id=paper_id)

    try:
        async with client.session() as session:
            # Query for cited and citing papers
            query = """
            MATCH (p:Paper {openalex_id: $id})
            OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
            OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
            WITH p, collect(DISTINCT cited) AS cited_list, collect(DISTINCT citing) AS citing_list
            RETURN p, cited_list, citing_list
            """
            result = await session.run(query, id=paper_id)
            record = await result.single()

            if not record:
                raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

            p = record["p"]
            cited_list = record["cited_list"]
            citing_list = record["citing_list"]

            nodes = []
            edges = []

            # Add central node
            nodes.append(
                CitationNetworkNode(
                    paper_id=p["openalex_id"],
                    title=p["title"],
                    year=p.get("year"),
                    citations=p.get("citations", 0),
                    impact_score=p.get("impact_score"),
                    community=p.get("community"),
                )
            )

            # Add cited papers and edges
            for cited in cited_list:
                if not cited:
                    continue
                nodes.append(
                    CitationNetworkNode(
                        paper_id=cited["openalex_id"],
                        title=cited["title"],
                        year=cited.get("year"),
                        citations=cited.get("citations", 0),
                        impact_score=cited.get("impact_score"),
                        community=cited.get("community"),
                    )
                )
                edges.append(
                    CitationNetworkEdge(source=p["openalex_id"], target=cited["openalex_id"])
                )

            # Add citing papers and edges
            for citing in citing_list:
                if not citing:
                    continue
                nodes.append(
                    CitationNetworkNode(
                        paper_id=citing["openalex_id"],
                        title=citing["title"],
                        year=citing.get("year"),
                        citations=citing.get("citations", 0),
                        impact_score=citing.get("impact_score"),
                        community=citing.get("community"),
                    )
                )
                edges.append(
                    CitationNetworkEdge(source=citing["openalex_id"], target=p["openalex_id"])
                )

            # Deduplicate nodes by paper_id
            seen_ids = set()
            unique_nodes = []
            for node in nodes:
                if node.paper_id not in seen_ids:
                    unique_nodes.append(node)
                    seen_ids.add(node.paper_id)

            return CitationNetworkResponse(papers=unique_nodes, citations=edges)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("paper_network_failed", paper_id=paper_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# =============================================================================
# Endpoint 6: Communities List
# =============================================================================


@router.get("/communities", response_model=CommunitiesResponse)
async def get_communities(
    client: Neo4jClient = Depends(get_neo4j_client),
) -> CommunitiesResponse:
    """Get all detected communities with summary stats."""
    logger.info("api_get_communities")

    try:
        async with client.session() as session:
            # Query for community stats and top topics
            query = """
            MATCH (p:Paper)
            WHERE p.community IS NOT NULL
            WITH p.community AS comm_id, count(p) AS paper_count, avg(p.impact_score) AS avg_impact
            MATCH (p2:Paper {community: comm_id})-[:BELONGS_TO_TOPIC]->(t:Topic)
            WITH comm_id, paper_count, avg_impact, t.name AS topic_name, count(p2) AS topic_weight
            ORDER BY topic_weight DESC
            WITH comm_id, paper_count, avg_impact, collect(topic_name)[0..5] AS top_topics
            RETURN comm_id, paper_count, avg_impact, top_topics
            ORDER BY comm_id
            """
            result = await session.run(query)
            records = await result.data()

            communities = [
                CommunityListItem(
                    id=rec["comm_id"],
                    paper_count=rec["paper_count"],
                    avg_impact=rec["avg_impact"],
                    top_topics=rec["top_topics"],
                )
                for rec in records
            ]

            return CommunitiesResponse(communities=communities, total=len(communities))

    except Exception as e:
        logger.error("get_communities_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# =============================================================================
# Endpoint 7: Track Paper View
# =============================================================================


class ViewTrackRequest(BaseModel):
    """Request for tracking a paper view."""

    user_session_id: str
    paper_id: str


@router.post("/track/view", status_code=204)
async def track_view(
    request: ViewTrackRequest,
) -> None:
    """Track a paper view for personalization (placeholder)."""
    logger.info("api_track_view", **request.model_dump())
    # In a real app, we'd store this in Redis or Neo4j
    return
