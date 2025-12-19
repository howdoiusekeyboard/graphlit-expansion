# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**GraphLit Expansion System** is a production-grade Python data pipeline for expanding academic literature citation networks from 15 seed papers to 1000+ papers using the OpenAlex API and Neo4j graph database. This represents Phase 2 of the GraphLit project (a literature survey assistance tool for researchers).

**Current Status:** Design/planning phase. The repository contains comprehensive architecture and implementation specifications (`architechture.md`, `Master Prompt.md`) but no implementation code yet.

## Technology Stack

**Runtime (Python 3.11+):**
- `httpx==0.27.0` - Async HTTP client for OpenAlex API
- `neo4j==5.26.0` - Official Neo4j async driver (Bolt protocol)
- `pydantic==2.9.2` + `pydantic-settings==2.5.2` - Type-safe configuration from `.env`
- `structlog==24.4.0` - Structured JSON logging
- `rich==13.9.4` - CLI progress bars and output
- `aiolimiter==1.2.1` - Async rate limiting (10 req/sec for OpenAlex)

**Development:**
- `ruff==0.7.4` - Linting (replaces black, flake8, isort)
- `mypy==1.13.0` - Strict type checking
- `pytest==8.3.4` + `pytest-asyncio==0.24.0` - Testing framework
- `pytest-httpx==0.30.0` - Mock API calls

## High-Level Architecture

### Core Algorithm: Breadth-First Search (BFS)
The system performs snowball sampling through citation networks:

1. **Initialization:** Load 15 seed DOIs from `data/seeds.json` → resolve to OpenAlex IDs
2. **BFS Expansion:** Pop (paper_id, depth) from queue → fetch metadata → validate → insert to Neo4j → enqueue references/citations if depth < max_depth
3. **Relationship Creation:** Second pass to create `CITES` edges between papers that both exist in the graph

**Bottleneck:** OpenAlex API rate limit (10 requests/second) - Expected runtime ~5-10 hours for 1000 papers

### Component Interactions

```
Orchestrator (BFS State Machine)
    ↓ coordinates
OpenAlex API Client (httpx + aiolimiter)
    ↓ fetches JSON
Mapper (Pure Functions)
    ↓ transforms to
Domain Models (Paper, Author, Venue, Topic)
    ↓ inserted via
Neo4j Client (Async Driver)
    ↓ persists to
Neo4j Graph Database
```

**Key Design Decisions:**
- **Async everywhere:** All I/O operations (API, database) use asyncio
- **Idempotency:** Neo4j uses `MERGE` statements for resumability after interruptions
- **Rate limiting:** `aiolimiter` ensures compliance with OpenAlex 10 req/sec limit
- **Error handling:** Exponential backoff on 429/500 errors, graceful 404 handling
- **Stateful BFS:** In-memory queue (`deque`) and visited set; future: Redis for scale

### Neo4j Schema

**Nodes:**
- `(:Paper {openalex_id, doi, title, year, citations, abstract})`
- `(:Author {openalex_id, name, orcid, institution})`
- `(:Venue {openalex_id, name, type, publisher})`
- `(:Topic {openalex_id, name, level})`

**Relationships:**
- `(:Paper)-[:CITES]->(:Paper)` - Citation edges
- `(:Paper)-[:AUTHORED_BY {position}]->(:Author)` - Authorship with order
- `(:Paper)-[:PUBLISHED_IN]->(:Venue)` - Publication venue
- `(:Paper)-[:BELONGS_TO_TOPIC {score}]->(:Topic)` - Topic classification

## Planned Project Structure

```
graphlit-expansion/
├── src/graphlit/
│   ├── config.py              # Pydantic settings from .env
│   ├── models.py              # Domain models (dataclasses)
│   ├── clients/openalex.py    # Async API client
│   ├── database/
│   │   ├── neo4j_client.py    # Graph DB operations
│   │   └── queries.py         # Cypher templates
│   ├── pipeline/
│   │   ├── mapper.py          # API JSON → Domain models
│   │   └── orchestrator.py    # BFS expansion logic
│   ├── utils/
│   │   ├── logging.py         # structlog configuration
│   │   └── retry.py           # Exponential backoff
│   └── __main__.py            # CLI entry point
├── tests/                     # pytest tests with httpx mocking
├── data/seeds.json            # 15 initial seed paper DOIs
└── pyproject.toml             # PEP 621 project config
```

## Development Commands

**Setup (when implemented):**
```bash
# Start Neo4j database
docker-compose up -d

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with Neo4j credentials and OpenAlex user agent
```

**Running:**
```bash
# Execute expansion pipeline
python -m graphlit

# Enable verbose logging
DEBUG=1 python -m graphlit
```

**Code Quality:**
```bash
# Type checking (must pass with zero errors)
mypy --strict src/

# Linting (must pass with zero violations)
ruff check src/ tests/

# Auto-formatting
ruff format src/ tests/

# Run tests
pytest

# Run tests with coverage
pytest --cov=graphlit --cov-report=term-missing
```

## Code Quality Requirements

**Type Safety (Strict):**
- All files must use `from __future__ import annotations`
- All functions must have explicit return type annotations
- Must pass `mypy --strict --disallow-untyped-defs` with zero errors

**Linting (ruff):**
- Enabled rules: E (pycodestyle), F (pyflakes), I (isort), N (pep8-naming), UP (pyupgrade), ASYNC (async best practices)
- Line length: 100 characters
- Target version: Python 3.11

**Error Handling:**
- Never use bare `except:`
- Log all exceptions with structured context (structlog)
- Implement exponential backoff for retries
- Handle HTTP 429 (rate limit) and 404 (not found) gracefully

**Testing:**
- Unit tests for pure functions (mapper.py)
- Integration tests with mocked APIs (pytest-httpx)
- Neo4j tests with testcontainers (real database)
- Target: 80%+ code coverage

## Configuration Approach

**Environment Variables (.env):**
```bash
# OpenAlex API
OPENALEX__USER_AGENT=GraphLit/1.0 (mailto:your.email@edu)
OPENALEX__RATE_LIMIT_PER_SECOND=10

# Neo4j Database
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=<password>
NEO4J__DATABASE=literature-survey

# Expansion Settings
EXPANSION__MAX_PAPERS=1000
EXPANSION__MAX_DEPTH=2
EXPANSION__YEAR_MIN=2015
EXPANSION__YEAR_MAX=2025
```

**Pydantic Settings:** All config loaded via `pydantic-settings` with:
- Type validation
- Nested configuration with `env_nested_delimiter="__"`
- Automatic `.env` file parsing

## Key Implementation Patterns

1. **Async I/O:** Use `async`/`await` for all API and database operations with `httpx.AsyncClient` and `AsyncGraphDatabase`
2. **Rate Limiting:** Wrap API calls with `async with self.limiter:` using `aiolimiter.AsyncLimiter`
3. **Structured Logging:** Use `structlog` with context: `logger.info("event_name", key=value, ...)`
4. **Progress Tracking:** Use `rich.progress.Progress` for real-time visual feedback
5. **Idempotent Inserts:** Use `MERGE` in Cypher queries for resumability
6. **Explicit Transactions:** Use async context managers for Neo4j sessions

## Acceptance Criteria

When implementation is complete, the system must:
1. Pass `mypy --strict` with zero errors
2. Pass `ruff check` with zero violations
3. Handle network failures gracefully (retry with exponential backoff)
4. Respect OpenAlex rate limits (never exceed 10 req/sec)
5. Support resumable runs (idempotent Neo4j inserts via MERGE)
6. Provide real-time progress visibility (Rich progress bars)
7. Log all operations with structured context (structlog)
8. Complete 1000-paper expansion in <12 hours

## References

- OpenAlex API Documentation: https://docs.openalex.org/
- Neo4j Python Driver: https://neo4j.com/docs/api/python-driver/current/
- Detailed architecture: `architechture.md`
- Implementation specifications: `Master Prompt.md`
