"""Configuration management using Pydantic V2 Settings.

This module provides type-safe configuration loading from environment variables
and .env files using pydantic-settings with nested delimiter support.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAlexSettings(BaseSettings):
    """Configuration for OpenAlex API client."""

    model_config = SettingsConfigDict(env_prefix="OPENALEX__")

    base_url: str = Field(
        default="https://api.openalex.org/",
        description="OpenAlex API base URL",
    )
    user_agent: str = Field(
        default="GraphLit/1.0 (mailto:contact@example.com)",
        description="User agent string with email for polite pool access",
    )
    rate_limit_per_second: Annotated[int, Field(ge=1, le=100)] = Field(
        default=10,
        description="Maximum API requests per second",
    )
    timeout_seconds: Annotated[int, Field(ge=1, le=300)] = Field(
        default=30,
        description="HTTP request timeout in seconds",
    )
    max_retries: Annotated[int, Field(ge=0, le=10)] = Field(
        default=3,
        description="Maximum retry attempts for failed requests",
    )


class Neo4jSettings(BaseSettings):
    """Configuration for Neo4j database connection."""

    model_config = SettingsConfigDict(env_prefix="NEO4J__")

    uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j Bolt connection URI",
    )
    username: str = Field(
        default="neo4j",
        description="Neo4j username",
    )
    password: str = Field(
        default="password",
        description="Neo4j password",
    )
    database: str = Field(
        default="neo4j",
        description="Neo4j database name",
    )


class ExpansionSettings(BaseSettings):
    """Configuration for citation network expansion."""

    model_config = SettingsConfigDict(env_prefix="EXPANSION__")

    max_papers: Annotated[int, Field(ge=1, le=100000)] = Field(
        default=1000,
        description="Maximum number of papers to collect",
    )
    max_depth: Annotated[int, Field(ge=0, le=10)] = Field(
        default=2,
        description="Maximum BFS traversal depth",
    )
    year_min: Annotated[int, Field(ge=1900, le=2100)] = Field(
        default=2015,
        description="Minimum publication year filter",
    )
    year_max: Annotated[int, Field(ge=1900, le=2100)] = Field(
        default=2025,
        description="Maximum publication year filter",
    )
    cs_concept_ids: list[str] = Field(
        default_factory=list,
        description="OpenAlex concept IDs for filtering (empty = all fields)",
    )


class AnalyticsSettings(BaseSettings):
    """Configuration for analytics and graph algorithms."""

    model_config = SettingsConfigDict(env_prefix="ANALYTICS__")

    gds_graph_name: str = Field(
        default="citation_network",
        description="GDS graph projection name",
    )
    louvain_max_iterations: Annotated[int, Field(ge=1, le=100)] = Field(
        default=10,
        description="Maximum Louvain algorithm iterations",
    )
    louvain_tolerance: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.0001,
        description="Louvain convergence tolerance",
    )
    min_community_size: Annotated[int, Field(ge=1, le=100)] = Field(
        default=3,
        description="Minimum community size threshold",
    )
    pagerank_weight: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.30,
        description="PageRank weight in impact score",
    )
    citation_velocity_weight: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.25,
        description="Citation velocity weight in impact score",
    )
    author_reputation_weight: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.25,
        description="Author reputation weight in impact score",
    )
    topic_momentum_weight: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.20,
        description="Topic momentum weight in impact score",
    )
    pagerank_damping_factor: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.85,
        description="PageRank damping factor",
    )
    pagerank_max_iterations: Annotated[int, Field(ge=1, le=100)] = Field(
        default=20,
        description="Maximum PageRank iterations",
    )


class Settings(BaseSettings):
    """Root configuration aggregating all settings.

    Settings are loaded from environment variables with nested delimiter '__'.
    Example: OPENALEX__USER_AGENT sets openalex.user_agent

    Usage:
        settings = Settings()
        print(settings.openalex.user_agent)
        print(settings.neo4j.uri)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    openalex: OpenAlexSettings = Field(default_factory=OpenAlexSettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    expansion: ExpansionSettings = Field(default_factory=ExpansionSettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    debug: bool = Field(
        default=False,
        description="Enable debug mode for verbose logging",
    )


def get_settings() -> Settings:
    """Load and return application settings.

    Returns:
        Settings: Validated configuration instance.

    Raises:
        ValidationError: If configuration values are invalid.
    """
    return Settings()
