"""Recommendation API endpoints.

This module provides REST API endpoints for paper recommendations using
the collaborative filtering engine with in-memory caching and Neo4j persistence.

Endpoints:
- GET /paper/{paper_id} - Recommendations for a specific paper
- POST /query - Query-based recommendations
- GET /community/{community_id}/trending - Trending papers in community
- GET /feed/{user_session_id} - Personalized user feed
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from graphlit.api.dependencies import get_cache, get_neo4j_client, get_recommender
from graphlit.cache.memory_cache import InMemoryCache
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
    pagerank: float | None = None


class TrendingPapersResponse(BaseModel):
    """Response for trending papers endpoint."""

    community_id: int
    community_label: str | None
    trending_papers: list[TrendingPaperItem]
    total: int


class CommunityNetworkNode(BaseModel):
    """Node in community citation network."""

    paper_id: str = Field(..., description="OpenAlex ID")
    title: str = Field(..., description="Paper title")
    year: int | None = Field(None, description="Publication year")
    citations: int = Field(0, description="Citation count")
    impact_score: float | None = Field(None, description="Predictive impact score")
    community: int | None = Field(None, description="Community ID")
    x: float | None = Field(None, description="Optional x-coordinate for layout")
    y: float | None = Field(None, description="Optional y-coordinate for layout")


class CommunityNetworkEdge(BaseModel):
    """Edge in community citation network."""

    source: str = Field(..., description="Source paper ID")
    target: str = Field(..., description="Target paper ID")


class CommunityNetworkResponse(BaseModel):
    """Community citation network response."""

    papers: list[CommunityNetworkNode] = Field(..., description="Network nodes")
    citations: list[CommunityNetworkEdge] = Field(..., description="Citation edges")


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
    cache: InMemoryCache = Depends(get_cache),
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
    cache: InMemoryCache = Depends(get_cache),
) -> RecommendationsResponse:
    """Get recommendations based on query criteria.

    Filters papers by topics and year range, returning high-impact papers
    that match the specified criteria. Results are cached for 1 hour.

    Args:
        request: Query parameters (topics, year range, exclusions)
        client: Injected Neo4j client
        cache: Injected Redis cache

    Returns:
        RecommendationsResponse with filtered papers ranked by impact score.
        Similarity score reflects topic match quality.
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

    # Fetch papers with topic and year filtering
    try:
        async with client.session() as session:
            result = await session.run(
                queries.GET_ALL_PAPERS_WITH_SCORES,
                year_min=request.year_min,
                year_max=request.year_max,
                topics=request.topics,
                limit=request.limit * 2,  # Over-fetch to account for exclusions
            )
            records = await result.data()

        # Convert to recommendation format with topic matching
        recommendations = [
            {
                "paper_id": str(rec["paper_id"]),
                "title": str(rec["title"]),
                "year": int(rec["year"]) if rec["year"] else None,
                "citations": int(rec["citations"]) if rec["citations"] else 0,
                "impact_score": float(rec["impact_score"]) if rec["impact_score"] else None,
                "similarity_score": (
                    float(rec["topic_match_count"]) / max(len(request.topics), 1)
                    if request.topics
                    else 1.0
                ),
                "recommendation_reason": "topic_match" if request.topics else "high_impact",
                "component_scores": {
                    "matched_topics": rec["matched_topics"],
                    "topic_match_count": rec["topic_match_count"],
                },
            }
            for rec in records
            if rec["paper_id"] not in request.exclude_papers
        ][:request.limit]  # Trim to requested limit after exclusions

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
    min_year: int | None = Query(None, ge=1900, le=2100, description="Minimum publication year"),
    client: Neo4jClient = Depends(get_neo4j_client),
    cache: InMemoryCache = Depends(get_cache),
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
            # Phase 1: Check if community exists and has papers matching year filter
            check_query = """
            MATCH (p:Paper)
            WHERE p.community = $community_id
            RETURN count(p) AS total,
                   sum(CASE WHEN $min_year IS NULL OR p.year >= $min_year THEN 1 ELSE 0 END) AS matching
            """
            check_result = await session.run(
                check_query,
                community_id=community_id,
                min_year=min_year,
            )
            check_record = await check_result.single()

            if not check_record or check_record["total"] == 0:
                # Community doesn't exist
                raise HTTPException(
                    status_code=404,
                    detail=f"Community {community_id} not found",
                )

            # Phase 2: Fetch trending papers
            result = await session.run(
                queries.GET_COMMUNITY_TRENDING_PAPERS,
                community_id=community_id,
                min_year=min_year,
                limit=limit,
            )
            records = await result.data()

            # If no papers match year filter, return empty response (not 404)
            if not records:
                logger.warning(
                    "community_no_matching_papers",
                    community_id=community_id,
                    min_year=min_year,
                    total_papers=check_record["total"],
                    matching_papers=check_record["matching"],
                )
                return TrendingPapersResponse(
                    community_id=community_id,
                    community_label=f"Community {community_id}",
                    trending_papers=[],
                    total=0,
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
                    "pagerank": float(rec["pagerank"]) if rec.get("pagerank") else None,
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


@router.get("/community/{community_id}/network", response_model=CommunityNetworkResponse)
async def get_community_network(
    community_id: int,
    min_year: int | None = Query(None, ge=1900, le=2100, description="Minimum publication year"),
    limit: int = Query(50, ge=10, le=100, description="Maximum papers to return"),
    client: Neo4jClient = Depends(get_neo4j_client),
    cache: InMemoryCache = Depends(get_cache),
) -> CommunityNetworkResponse:
    """Get citation network for a specific community.

    Returns the top N papers by PageRank/impact score within a community
    along with intra-community citation edges for network visualization.

    Args:
        community_id: Community identifier
        min_year: Optional minimum publication year filter
        limit: Maximum number of papers to return (default: 50)
        client: Neo4j database client
        cache: In-memory cache instance

    Returns:
        CommunityNetworkResponse with papers and citations

    Raises:
        HTTPException: 404 if community not found, 500 on query error
    """
    logger.info("api_get_community_network", community_id=community_id, min_year=min_year, limit=limit)

    # Check cache first (4-hour TTL)
    cache_key = f"community_network:{community_id}:{min_year}:{limit}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("community_network_cache_hit", community_id=community_id)
        return CommunityNetworkResponse(**cached)

    try:
        async with client.session() as session:
            # Phase 1: Check if community exists
            check_query = """
            MATCH (p:Paper)
            WHERE p.community = $community_id
            RETURN count(p) AS total
            """
            check_result = await session.run(check_query, community_id=community_id)
            check_record = await check_result.single()

            if not check_record or check_record["total"] == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Community {community_id} not found"
                )

            # Phase 2: Fetch network data
            result = await session.run(
                queries.GET_COMMUNITY_CITATION_NETWORK,
                community_id=community_id,
                min_year=min_year,
                limit=limit,
            )
            record = await result.single()

            if not record or not record["network"]:
                logger.warning("community_network_empty", community_id=community_id)
                return CommunityNetworkResponse(papers=[], citations=[])

            network_data = record["network"]

            # Parse response
            papers = [CommunityNetworkNode(**p) for p in network_data["papers"]]
            citations = [CommunityNetworkEdge(**c) for c in network_data["citations"]]

            response = CommunityNetworkResponse(papers=papers, citations=citations)

            # Cache for 4 hours
            await cache.set(cache_key, response.model_dump(), ttl_seconds=14400)

            logger.info(
                "community_network_success",
                community_id=community_id,
                paper_count=len(papers),
                citation_count=len(citations),
            )

            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("community_network_failed", community_id=community_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch community network: {str(e)}"
        ) from e


# =============================================================================
# Endpoint 4: Personalized User Feed (Production)
# =============================================================================


@router.get("/feed/{user_session_id}", response_model=RecommendationsResponse)
async def get_personalized_feed(
    user_session_id: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum papers to return"),
    cache: InMemoryCache = Depends(get_cache),
    recommender: CollaborativeFilterRecommender = Depends(get_recommender),
    client: Neo4jClient = Depends(get_neo4j_client),
) -> RecommendationsResponse:
    """Get personalized recommendation feed based on viewing history.

    Uses weighted collaborative filtering on viewed papers with:
    - Time decay (recent views weighted more)
    - Topic diversity (avoid echo chambers)
    - Community diversity (cross-pollinate research areas)
    - Impact boosting (surface high-quality papers)

    Falls back to trending papers for new users (cold start).

    Args:
        user_session_id: User session identifier
        limit: Maximum papers to return
        cache: Injected in-memory cache
        recommender: Injected recommendation engine
        client: Injected Neo4j client

    Returns:
        RecommendationsResponse with personalized papers.
    """
    logger.info("api_get_personalized_feed", user_session_id=user_session_id)

    # Check cache first
    cache_key = f"feed:{user_session_id}:{limit}"
    cached = await cache.get(cache_key)
    if cached:
        logger.info("feed_cache_hit", user_session_id=user_session_id)
        return cached

    try:
        # Get user viewing history from VIEWED relationships (more robust)
        async with client.session() as session:
            result = await session.run(
                """
                MATCH (u:UserProfile {session_id: $session_id})-[v:VIEWED]->(p:Paper)
                RETURN p.openalex_id AS paper_id,
                       v.weight AS weight,
                       v.timestamp AS timestamp,
                       p.community AS community,
                       duration.inDays(v.timestamp, datetime()).days AS days_ago
                ORDER BY v.timestamp DESC
                LIMIT 20
                """,
                session_id=user_session_id,
            )
            viewing_history = await result.data()

        # Extract viewed papers with time-decayed weights
        viewed_papers = []
        paper_weights = {}
        viewed_communities = set()

        for record in viewing_history:
            paper_id = str(record["paper_id"])
            base_weight = float(record["weight"])
            days_ago = int(record["days_ago"]) if record["days_ago"] else 0
            community = record["community"]

            # Apply exponential time decay (half-life = 7 days)
            time_decay = 0.5 ** (days_ago / 7.0)
            decayed_weight = base_weight * time_decay

            viewed_papers.append(paper_id)
            paper_weights[paper_id] = decayed_weight
            if community is not None:
                viewed_communities.add(community)

        # Cold start: No viewing history → return trending papers
        if not viewed_papers:
            logger.info("feed_cold_start", user_session_id=user_session_id)

            # Get high-impact recent papers from diverse communities
            async with client.session() as session:
                result = await session.run(
                    """
                    MATCH (p:Paper)
                    WHERE p.year >= 2020 AND p.impact_score IS NOT NULL
                    WITH p
                    ORDER BY p.impact_score DESC, p.citations DESC
                    WITH p.community AS community, collect(p)[0..3] AS top_papers
                    UNWIND top_papers AS p
                    RETURN p.openalex_id AS paper_id,
                           p.title AS title,
                           p.year AS year,
                           p.citations AS citations,
                           p.impact_score AS impact_score,
                           p.community AS community
                    ORDER BY p.impact_score DESC
                    LIMIT $limit
                    """,
                    limit=limit,
                )
                records = await result.data()

            recommendations = [
                {
                    "paper_id": str(rec["paper_id"]),
                    "title": str(rec["title"]),
                    "year": int(rec["year"]) if rec["year"] else None,
                    "citations": int(rec["citations"]) if rec["citations"] else 0,
                    "impact_score": (
                        float(rec["impact_score"]) if rec["impact_score"] else None
                    ),
                    "similarity_score": 1.0,
                    "recommendation_reason": "trending",
                    "component_scores": None,
                }
                for rec in records
            ]

            response = RecommendationsResponse(
                recommendations=[
                    RecommendationItem.model_validate(rec) for rec in recommendations
                ],
                total=len(recommendations),
                cached=False,
                cache_ttl_seconds=None,
            )

            # Cache for 5 minutes (trending doesn't change often)
            await cache.set(cache_key, response, ttl_seconds=300)
            return response

        # Warm start: Build personalized feed from viewed papers
        logger.info(
            "feed_personalized",
            user_session_id=user_session_id,
            viewed_count=len(viewed_papers),
            viewed_communities=len(viewed_communities),
        )

        # Aggregate recommendations from all viewed papers (weighted by time decay)
        candidate_scores: dict[str, float] = {}
        candidate_metadata: dict[str, dict] = {}

        for paper_id in viewed_papers[:10]:  # Limit to most recent 10 views
            weight = paper_weights.get(paper_id, 1.0)

            # Get recommendations for this paper
            try:
                recs = await recommender.get_paper_recommendations(
                    paper_id=paper_id,
                    limit=15,  # Get more candidates for diversity
                )

                # Add weighted score to candidates
                for rec in recs:
                    rec_id = rec["paper_id"]
                    if rec_id not in viewed_papers:  # Skip already viewed
                        similarity = rec.get("combined_score", rec["similarity_score"])
                        weighted_score = similarity * weight

                        # Aggregate scores from multiple sources
                        candidate_scores[rec_id] = (
                            candidate_scores.get(rec_id, 0.0) + weighted_score
                        )

                        # Store metadata for diversity filtering
                        if rec_id not in candidate_metadata:
                            candidate_metadata[rec_id] = {
                                "title": rec.get("title", ""),
                                "year": rec.get("year"),
                                "method": rec.get("recommendation_reason", "unknown"),
                            }

            except Exception as e:
                logger.warning(
                    "feed_rec_failed",
                    paper_id=paper_id,
                    error=str(e),
                )
                continue

        # Sort by aggregated score and get top candidates
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit * 3]  # Over-fetch 3x for diversity filtering

        # Fallback: No recommendations found, return trending papers
        if not sorted_candidates:
            logger.warning("feed_no_candidates", user_session_id=user_session_id)
            # Recursively call with "trending" session to get cold start response
            return await get_personalized_feed(
                user_session_id="trending",
                limit=limit,
                cache=cache,
                recommender=recommender,
                client=client,
            )

        candidate_ids = [cid for cid, _ in sorted_candidates]

        # Fetch full paper details including community for diversity filtering
        async with client.session() as session:
            result = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.openalex_id IN $paper_ids
                RETURN p.openalex_id AS paper_id,
                       p.title AS title,
                       p.year AS year,
                       p.citations AS citations,
                       p.impact_score AS impact_score,
                       p.community AS community
                """,
                paper_ids=candidate_ids,
            )
            records = await result.data()

        # Create recommendation list with aggregated scores
        recommendations = []
        for rec in records:
            rec_id = str(rec["paper_id"])
            aggregated_score = candidate_scores.get(rec_id, 0.0)
            impact_score = (
                float(rec["impact_score"]) if rec["impact_score"] else None
            )
            community = rec["community"]

            # Boost score for high-impact papers (10% bonus)
            final_score = aggregated_score
            if impact_score and impact_score > 70:
                final_score *= 1.1

            # Boost score for papers from new communities (diversity bonus: 15%)
            if community and community not in viewed_communities:
                final_score *= 1.15

            recommendations.append({
                "paper_id": rec_id,
                "title": str(rec["title"]),
                "year": int(rec["year"]) if rec["year"] else None,
                "citations": int(rec["citations"]) if rec["citations"] else 0,
                "impact_score": impact_score,
                "similarity_score": final_score,
                "recommendation_reason": "personalized",
                "component_scores": None,
                "community": community,
            })

        # Apply diversity filtering to avoid year/community clustering
        recommendations_diverse = []
        year_counts: dict[int | None, int] = {}
        community_counts: dict[int | None, int] = {}

        # Sort by final score first
        recommendations.sort(key=lambda x: float(x["similarity_score"]), reverse=True)

        for rec in recommendations:
            year = rec["year"]
            community = rec["community"]

            # Apply diversity penalty if too many from same year/community
            year_count = year_counts.get(year, 0)
            community_count = community_counts.get(community, 0)

            # Accept if diversity is good (max 3 per year, max 5 per community)
            if year_count < 3 and community_count < 5:
                # Remove temporary community field before returning
                rec_copy = {k: v for k, v in rec.items() if k != "community"}
                recommendations_diverse.append(rec_copy)
                year_counts[year] = year_count + 1
                community_counts[community] = community_count + 1

            if len(recommendations_diverse) >= limit:
                break

        # If we don't have enough diverse recommendations, backfill
        if len(recommendations_diverse) < limit:
            for rec in recommendations:
                if len(recommendations_diverse) >= limit:
                    break
                rec_id = rec["paper_id"]
                if not any(r["paper_id"] == rec_id for r in recommendations_diverse):
                    rec_copy = {k: v for k, v in rec.items() if k != "community"}
                    recommendations_diverse.append(rec_copy)

        response = RecommendationsResponse(
            recommendations=[
                RecommendationItem.model_validate(rec)
                for rec in recommendations_diverse[:limit]
            ],
            total=len(recommendations_diverse[:limit]),
            cached=False,
            cache_ttl_seconds=None,
        )

        # Cache personalized feed for 2 minutes (balance freshness vs performance)
        await cache.set(cache_key, response, ttl_seconds=120)

        logger.info(
            "feed_generated",
            user_session_id=user_session_id,
            total_recommendations=len(recommendations_diverse),
            unique_communities=len(community_counts),
        )

        return response

    except Exception as e:
        logger.error("personalized_feed_failed", user_session_id=user_session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate personalized feed: {str(e)}",
        ) from e


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
                """
                MATCH (p:Paper {openalex_id: $id})-[:BELONGS_TO_TOPIC]->(t:Topic)
                RETURN t.name AS name
                """,
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
    client: Neo4jClient = Depends(get_neo4j_client),
) -> None:
    """Track a paper view for personalization.

    Stores the view in the user's profile (Neo4j) with default engagement weight.
    This data powers personalized recommendations in the feed.

    Args:
        request: View tracking data (session_id, paper_id)
        client: Injected Neo4j client
    """
    logger.info("api_track_view", **request.model_dump())

    try:
        # Add viewed paper to user profile in Neo4j
        async with client.session() as session:
            # First, ensure user profile exists
            await session.run(
                queries.MERGE_USER_PROFILE,
                session_id=request.user_session_id,
                viewed_papers=[],
                paper_weights={},
                preferred_topics={},
                preferred_communities=[],
            )

            # Then add the viewed paper
            await session.run(
                queries.ADD_VIEWED_PAPER,
                session_id=request.user_session_id,
                paper_id=request.paper_id,
                weight=1.0,  # Default engagement weight
            )

        logger.debug(
            "view_tracked",
            session_id=request.user_session_id,
            paper_id=request.paper_id,
        )

    except Exception as e:
        logger.warning(
            "view_tracking_failed",
            session_id=request.user_session_id,
            paper_id=request.paper_id,
            error=str(e),
        )
        # Don't fail the request if tracking fails

    return
