"""Tests for personalized feed endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from graphlit.api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


class TestPersonalizedFeed:
    """Test suite for personalized recommendation feed."""

    def test_cold_start_returns_trending_papers(self, client: TestClient) -> None:
        """Test that new users get trending papers (cold start)."""
        response = client.get("/api/v1/recommendations/feed/new_user_123?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        assert "total" in data
        assert len(data["recommendations"]) <= 10

        # Cold start should return trending papers
        if data["total"] > 0:
            assert data["recommendations"][0]["recommendation_reason"] == "trending"

    def test_personalized_feed_with_viewing_history(self, client: TestClient) -> None:
        """Test that users with viewing history get personalized recommendations."""
        # First, track some paper views to build history
        session_id = "test_user_with_history"

        # Track 3 paper views
        for paper_id in ["W2741809807", "W2963919853", "W2741809807"]:
            response = client.post(
                "/api/v1/recommendations/track/view",
                json={"user_session_id": session_id, "paper_id": paper_id},
            )
            assert response.status_code == 204

        # Now get personalized feed
        response = client.get(f"/api/v1/recommendations/feed/{session_id}?limit=15")

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        assert "total" in data
        assert len(data["recommendations"]) <= 15

        # Should get personalized recommendations (might still be trending if no recs found)
        if data["total"] > 0:
            reason = data["recommendations"][0]["recommendation_reason"]
            assert reason in ["personalized", "trending"]

    def test_feed_respects_limit_parameter(self, client: TestClient) -> None:
        """Test that limit parameter is respected."""
        for limit in [5, 10, 20]:
            response = client.get(
                f"/api/v1/recommendations/feed/limit_test_user?limit={limit}"
            )

            assert response.status_code == 200
            data = response.json()

            # Should return at most 'limit' papers
            assert len(data["recommendations"]) <= limit

    def test_feed_invalid_limit_returns_error(self, client: TestClient) -> None:
        """Test that invalid limit values are rejected."""
        # Limit too high
        response = client.get("/api/v1/recommendations/feed/test_user?limit=100")
        assert response.status_code == 422

        # Limit too low
        response = client.get("/api/v1/recommendations/feed/test_user?limit=0")
        assert response.status_code == 422

    def test_feed_response_structure(self, client: TestClient) -> None:
        """Test that feed response has correct structure."""
        response = client.get("/api/v1/recommendations/feed/structure_test?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "recommendations" in data
        assert "total" in data
        assert "cached" in data

        # Check recommendation structure (if any returned)
        if data["total"] > 0:
            rec = data["recommendations"][0]
            assert "paper_id" in rec
            assert "title" in rec
            assert "year" in rec
            assert "citations" in rec
            assert "similarity_score" in rec
            assert "recommendation_reason" in rec

    def test_feed_diversity_different_communities(self, client: TestClient) -> None:
        """Test that feed returns papers from diverse communities."""
        # Track views from papers in different communities
        session_id = "diversity_test_user"

        # Track multiple paper views
        for paper_id in ["W2741809807", "W2963919853", "W2950275683"]:
            client.post(
                "/api/v1/recommendations/track/view",
                json={"user_session_id": session_id, "paper_id": paper_id},
            )

        # Get personalized feed
        response = client.get(f"/api/v1/recommendations/feed/{session_id}?limit=20")

        assert response.status_code == 200
        data = response.json()

        # If we got recommendations, check year diversity
        if data["total"] >= 5:
            years = [rec["year"] for rec in data["recommendations"] if rec["year"]]
            unique_years = set(years)

            # Should have at least 2 different years (diversity)
            assert len(unique_years) >= 2

    def test_feed_caching_works(self, client: TestClient) -> None:
        """Test that feed responses are cached appropriately."""
        session_id = "cache_test_user"

        # First request (cache miss)
        response1 = client.get(f"/api/v1/recommendations/feed/{session_id}?limit=10")
        assert response1.status_code == 200

        # Second request (should hit cache)
        response2 = client.get(f"/api/v1/recommendations/feed/{session_id}?limit=10")
        assert response2.status_code == 200

        # Responses should be identical (cached)
        assert response1.json() == response2.json()

    def test_feed_excludes_already_viewed_papers(self, client: TestClient) -> None:
        """Test that feed doesn't recommend already-viewed papers."""
        session_id = "exclude_viewed_test"

        # Track a view
        viewed_paper = "W2741809807"
        response = client.post(
            "/api/v1/recommendations/track/view",
            json={"user_session_id": session_id, "paper_id": viewed_paper},
        )
        assert response.status_code == 204

        # Get feed
        response = client.get(f"/api/v1/recommendations/feed/{session_id}?limit=20")
        assert response.status_code == 200

        data = response.json()

        # Viewed paper should NOT be in recommendations
        recommended_ids = [rec["paper_id"] for rec in data["recommendations"]]
        assert viewed_paper not in recommended_ids
