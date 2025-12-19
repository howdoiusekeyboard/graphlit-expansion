"""Tests for configuration module."""

from __future__ import annotations

import os
from unittest.mock import patch

from graphlit.config import (
    ExpansionSettings,
    Neo4jSettings,
    OpenAlexSettings,
    Settings,
    get_settings,
)


class TestOpenAlexSettings:
    """Tests for OpenAlex settings."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = OpenAlexSettings()

        assert str(settings.base_url) == "https://api.openalex.org/"
        assert settings.rate_limit_per_second == 10
        assert settings.timeout_seconds == 30
        assert settings.max_retries == 3

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        settings = OpenAlexSettings(
            user_agent="Test/1.0",
            rate_limit_per_second=5,
            timeout_seconds=60,
        )

        assert settings.user_agent == "Test/1.0"
        assert settings.rate_limit_per_second == 5
        assert settings.timeout_seconds == 60


class TestNeo4jSettings:
    """Tests for Neo4j settings."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = Neo4jSettings()

        assert settings.uri == "bolt://localhost:7687"
        assert settings.username == "neo4j"
        assert settings.database == "neo4j"

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        settings = Neo4jSettings(
            uri="bolt://remotehost:7687",
            username="admin",
            password="secret",
            database="mydb",
        )

        assert settings.uri == "bolt://remotehost:7687"
        assert settings.username == "admin"
        assert settings.password == "secret"
        assert settings.database == "mydb"


class TestExpansionSettings:
    """Tests for expansion settings."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = ExpansionSettings()

        assert settings.max_papers == 1000
        assert settings.max_depth == 2
        assert settings.year_min == 2015
        assert settings.year_max == 2025
        assert settings.cs_concept_ids == []

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        settings = ExpansionSettings(
            max_papers=500,
            max_depth=3,
            year_min=2020,
            year_max=2024,
            cs_concept_ids=["C123", "C456"],
        )

        assert settings.max_papers == 500
        assert settings.max_depth == 3
        assert settings.year_min == 2020
        assert settings.year_max == 2024
        assert settings.cs_concept_ids == ["C123", "C456"]

    def test_year_validation(self) -> None:
        """Test year range validation."""
        # Valid years should work
        settings = ExpansionSettings(year_min=2000, year_max=2050)
        assert settings.year_min == 2000
        assert settings.year_max == 2050


class TestSettings:
    """Tests for root Settings class."""

    def test_default_settings(self) -> None:
        """Test that Settings loads with defaults."""
        settings = Settings()

        assert settings.openalex is not None
        assert settings.neo4j is not None
        assert settings.expansion is not None
        assert settings.debug is False

    def test_nested_settings(self) -> None:
        """Test accessing nested settings."""
        settings = Settings()

        assert settings.openalex.rate_limit_per_second == 10
        assert settings.neo4j.uri == "bolt://localhost:7687"
        assert settings.expansion.max_papers == 1000

    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_from_env(self) -> None:
        """Test loading debug flag from environment."""
        settings = Settings()
        assert settings.debug is True


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
