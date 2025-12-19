# GraphLit Academic Citation Network Data Expansion System

## Context
You are building a production-grade Python system to expand an academic literature graph database from 15 to 1000+ papers using the OpenAlex API and Neo4j graph database. This is Phase 2 of the GraphLit project - a literature survey assistance tool for researchers.

## Project Objective
Implement a robust, maintainable data pipeline that:
1. Fetches academic paper metadata from OpenAlex API (open-source alternative to Microsoft Academic)
2. Performs snowball sampling (BFS traversal) through citation networks
3. Maps external API data to internal Neo4j graph schema
4. Handles rate limiting, errors, and interruptions gracefully
5. Provides real-time progress monitoring and logging

## Technology Stack Requirements

### Core Dependencies (Latest Stable Versions)
- **Python**: 3.11+ (use modern typing with `from __future__ import annotations`)
- **Neo4j Driver**: `neo4j==5.26.0` (official driver, Bolt protocol)
- **HTTP Client**: `httpx==0.27.0` (async-capable, prefer over `requests`)
- **Configuration**: `pydantic==2.9.2` + `pydantic-settings==2.5.2` (type-safe config)
- **Logging**: `structlog==24.4.0` (structured logging for production)
- **Progress**: `rich==13.9.4` (modern CLI with progress bars)
- **Rate Limiting**: `aiolimiter==1.2.1` (async rate limiting)

### Development Tools
- **Linting**: `ruff==0.7.4` (replaces black, flake8, isort)
- **Type Checking**: `mypy==1.13.0` (strict mode)
- **Testing**: `pytest==8.3.4` + `pytest-asyncio==0.24.0`
- **Environment**: `python-dotenv==1.0.1`

## Architecture Blueprint

### Project Structure
graphlit-expansion/
├── pyproject.toml # Modern Python project config (PEP 621)
├── .env.example # Environment variables template
├── .env # Local secrets (gitignored)
├── README.md # Comprehensive documentation
├── ARCHITECTURE.md # System design document
│
├── src/
│ └── graphlit/
│ ├── init.py
│ ├── config.py # Pydantic settings
│ ├── models.py # Domain models (Paper, Author, etc.)
│ │
│ ├── clients/
│ │ ├── init.py
│ │ └── openalex.py # OpenAlex API client (async)
│ │
│ ├── database/
│ │ ├── init.py
│ │ ├── neo4j_client.py # Neo4j operations
│ │ └── queries.py # Cypher query templates
│ │
│ ├── pipeline/
│ │ ├── init.py
│ │ ├── mapper.py # API → Domain model transformation
│ │ └── orchestrator.py # Main expansion logic
│ │
│ └── utils/
│ ├── init.py
│ ├── logging.py # Structured logging setup
│ └── retry.py # Retry decorators
│
├── tests/
│ ├── init.py
│ ├── conftest.py # Pytest fixtures
│ ├── test_openalex.py
│ ├── test_mapper.py
│ └── test_orchestrator.py
│
├── data/
│ └── seeds.json # Initial 15 seed paper DOIs
│
└── logs/ # Application logs (gitignored)

## Implementation Requirements

### 1. Configuration Management (Pydantic V2)
Use Pydantic Settings for type-safe, validated configuration:

```python
# src/graphlit/config.py
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class OpenAlexSettings(BaseSettings):
    base_url: HttpUrl = "https://api.openalex.org"
    user_agent: str
    rate_limit_per_second: int = 10
    timeout_seconds: int = 30
    max_retries: int = 3

class Neo4jSettings(BaseSettings):
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    
    model_config = SettingsConfigDict(env_prefix="NEO4J_")

class ExpansionSettings(BaseSettings):
    max_papers: int = 1000
    max_depth: int = 2
    year_min: int = 2015
    year_max: int = 2025
    cs_concept_ids: list[str] = Field(default_factory=list)

class Settings(BaseSettings):
    openalex: OpenAlexSettings
    neo4j: Neo4jSettings
    expansion: ExpansionSettings
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__"
    )
```

### 2. Domain Models (Dataclasses with Validation)
Use modern Python dataclasses with proper typing:

```python
# src/graphlit/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True, slots=True)  # Immutable, memory-efficient
class Paper:
    openalex_id: str
    doi: Optional[str]
    title: str
    year: int
    citations: int
    abstract: Optional[str] = None
    
    def __post_init__(self):
        if not self.openalex_id.startswith('W'):
            raise ValueError(f"Invalid OpenAlex ID: {self.openalex_id}")

@dataclass(frozen=True, slots=True)
class Author:
    openalex_id: str
    name: str
    orcid: Optional[str] = None
    institution: Optional[str] = None

# Similar for Venue, Topic...
```

### 3. Async HTTP Client (httpx)
Implement async API client for better performance:

```python
# src/graphlit/clients/openalex.py
import httpx
from aiolimiter import AsyncLimiter
from typing import Optional
import structlog

class OpenAlexClient:
    def __init__(self, settings: OpenAlexSettings):
        self.base_url = str(settings.base_url)
        self.limiter = AsyncLimiter(
            max_rate=settings.rate_limit_per_second,
            time_period=1.0
        )
        self.client = httpx.AsyncClient(
            timeout=settings.timeout_seconds,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True
        )
        self.logger = structlog.get_logger(__name__)
    
    async def get_work(self, openalex_id: str) -> Optional[dict]:
        async with self.limiter:
            url = f"{self.base_url}/works/{openalex_id}"
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                self.logger.warning("api_error", status=e.response.status_code)
                return None
    
    async def close(self):
        await self.client.aclose()
```

### 4. Neo4j Operations (Explicit Transactions)
Use context managers and parameterized queries:

src/graphlit/database/neo4j_client.py
from neo4j import GraphDatabase, AsyncGraphDatabase
from contextlib import asynccontextmanager
import structlog

```python
class Neo4jClient:
    def __init__(self, settings: Neo4jSettings):
        self.driver = AsyncGraphDatabase.driver(
            settings.uri,
            auth=(settings.username, settings.password)
        )\n        self.database = settings.database
        self.logger = structlog.get_logger(__name__)
    
    @asynccontextmanager
    async def session(self):
    async with self.driver.session(database=self.database) as session:
        yield session

async def upsert_paper(self, paper: Paper) -> bool:
    query = """
    MERGE (p:Paper {openalex_id: $openalex_id})
    SET p += $properties
    RETURN p.openalex_id
    """
    async with self.session() as session:
        result = await session.run(
            query,
            openalex_id=paper.openalex_id,
            properties={
                "doi": paper.doi,
                "title": paper.title,
                "year": paper.year,
                "citations": paper.citations
            }
        )
        return await result.single() is not None

    async def close(self):
        await self.driver.close()
```

### 5. Structured Logging (structlog)
Production-grade logging with context:

```python
# src/graphlit/utils/logging.py
import structlog
import logging

def setup_logging(debug: bool = False):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True)
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )
```

### 6. Main Orchestrator (Async BFS)
Coordinate the expansion with proper error handling:

```python
# src/graphlit/pipeline/orchestrator.py
import asyncio
from collections import deque
from typing import Set
from rich.progress import Progress, SpinnerColumn, TextColumn
import structlog

class ExpansionOrchestrator:
    def __init__(
        self,
        openalex_client: OpenAlexClient,
        neo4j_client: Neo4jClient,
        mapper: Mapper,
        settings: ExpansionSettings
    ):
        self.api = openalex_client
        self.db = neo4j_client
        self.mapper = mapper
        self.settings = settings
        self.logger = structlog.get_logger(__name__)
        self.visited: Set[str] = set()
        self.queue: deque[tuple[str, int]] = deque()
    
    async def expand(self, seed_dois: list[str]):
        """Main expansion workflow"""
        self.logger.info("expansion_started", seeds=len(seed_dois))
        
        # Resolve seeds to OpenAlex IDs
        for doi in seed_dois:
            work = await self.api.get_work_by_doi(doi)
            if work:
                self.queue.append((work['id'], 0))
        
        # BFS with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(
                "Expanding graph...",
                total=self.settings.max_papers
            )
            
            while self.queue and len(self.visited) < self.settings.max_papers:
                openalex_id, depth = self.queue.popleft()
                
                if openalex_id in self.visited:
                    continue
                
                success = await self._process_paper(openalex_id, depth)
                if success:
                    self.visited.add(openalex_id)
                    progress.update(task, advance=1)
        
        self.logger.info("expansion_complete", papers=len(self.visited))
    
    async def _process_paper(self, openalex_id: str, depth: int) -> bool:
        """Process single paper with error handling"""
        try:
            work = await self.api.get_work(openalex_id)
            if not work:
                return False
            
            # Map and validate
            paper = self.mapper.map_paper(work)
            if not self.mapper.should_include(work):
                return False
            
            # Insert to Neo4j
            await self.db.upsert_paper(paper)
            
            # Add neighbors to queue
            if depth < self.settings.max_depth:
                await self._enqueue_neighbors(work, depth)
            
            return True
        
        except Exception as e:
            self.logger.error("paper_processing_failed", error=str(e))
            return False
    
    async def _enqueue_neighbors(self, work: dict, depth: int):
        """Add references and citations to queue"""
        for ref in work.get('referenced_works', [])[:50]:
            if ref not in self.visited:
                self.queue.append((ref, depth + 1))
```

### 7. Entry Point (CLI with Rich)
Modern CLI with async support:

```python
# src/graphlit/__main__.py
import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .config import Settings
from .clients.openalex import OpenAlexClient
from .database.neo4j_client import Neo4jClient
from .pipeline.mapper import Mapper
from .pipeline.orchestrator import ExpansionOrchestrator
from .utils.logging import setup_logging

console = Console()

async def main():
    """Entry point"""
    console.print(Panel.fit(
        "[bold cyan]GraphLit Data Expansion Pipeline[/bold cyan]",
        border_style="cyan"
    ))
    
    # Load config
    settings = Settings()
    setup_logging(debug=False)
    
    # Load seeds
    seeds_path = Path("data/seeds.json")
    with seeds_path.open() as f:
        seed_data = json.load(f)
    seed_dois = [p['doi'] for p in seed_data if p.get('doi')]
    
    # Initialize components
    api_client = OpenAlexClient(settings.openalex)
    db_client = Neo4jClient(settings.neo4j)
    mapper = Mapper(settings.expansion)
    
    orchestrator = ExpansionOrchestrator(
        api_client, db_client, mapper, settings.expansion
    )
    
    try:
        await orchestrator.expand(seed_dois)
        console.print("[bold green]✓[/bold green] Expansion complete!")
    
    except KeyboardInterrupt:
        console.print("[yellow]⚠[/yellow] Interrupted by user")
    
    finally:
        await api_client.close()
        await db_client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Code Quality Requirements

### Type Safety
- Enable strict mypy: `--strict --disallow-untyped-defs`
- Use `from __future__ import annotations` in all files
- Annotate all function signatures with return types

### Code Style
- Use `ruff` with these rules enabled:
  - `E` (pycodestyle errors)
  - `F` (pyflakes)
  - `I` (isort)
  - `N` (pep8-naming)
  - `UP` (pyupgrade for modern syntax)
  - `ASYNC` (async best practices)

### Error Handling
- Never use bare `except:`
- Log all exceptions with context
- Implement exponential backoff for retries
- Handle rate limits gracefully (429 errors)

### Testing
- Write unit tests for mapper functions
- Mock API calls with `pytest-httpx`
- Test Neo4j operations with `testcontainers`
- Aim for 80%+ code coverage

## Configuration Files

### pyproject.toml
```toml
[project]
name = "graphlit-expansion"
version = "1.0.0"
description = "Academic citation network expansion system"
requires-python = ">=3.11"
dependencies = [
    "httpx==0.27.0",
    "neo4j==5.26.0",
    "pydantic==2.9.2",
    "pydantic-settings==2.5.2",
    "structlog==24.4.0",
    "rich==13.9.4",
    "aiolimiter==1.2.1",
    "python-dotenv==1.0.1"
]

[project.optional-dependencies]
dev = [
    "ruff==0.7.4",
    "mypy==1.13.0",
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-httpx==0.30.0"
]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "UP", "ASYNC"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### .env.example
```bash
# OpenAlex Configuration
OPENALEX__USER_AGENT=GraphLit/1.0 (mailto:your.email@university.edu)
OPENALEX__RATE_LIMIT_PER_SECOND=10

# Neo4j Configuration
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=your_password_here
NEO4J__DATABASE=literature-survey

# Expansion Settings
EXPANSION__MAX_PAPERS=1000
EXPANSION__MAX_DEPTH=2
EXPANSION__YEAR_MIN=2015
EXPANSION__YEAR_MAX=2025
EXPANSION__CS_CONCEPT_IDS=["C41008148","C154945302","C2778407487"]
```

## Acceptance Criteria

Your implementation must:
1. ✅ Pass `mypy --strict` with zero errors
2. ✅ Pass `ruff check` with zero violations
3. ✅ Handle network failures gracefully (retry + backoff)
4. ✅ Respect OpenAlex rate limits (never exceed 10 req/s)
5. ✅ Be resumable (idempotent Neo4j inserts)
6. ✅ Provide real-time progress visibility
7. ✅ Log all operations with structured context
8. ✅ Complete 1000-paper expansion in <12 hours

## Implementation Steps

1. **Setup project structure** using the layout above
2. **Implement config.py** with Pydantic settings
3. **Implement models.py** with domain entities
4. **Implement openalex.py** with async HTTP client
5. **Implement neo4j_client.py** with async driver
6. **Implement mapper.py** with transformation logic
7. **Implement orchestrator.py** with BFS expansion
8. **Implement __main__.py** with CLI entry point
9. **Add comprehensive docstrings** (Google style)
10. **Write unit tests** for critical paths
11. **Create README.md** with usage instructions
12. **Test end-to-end** with 50-paper dry run

## Additional Context

- OpenAlex API docs: https://docs.openalex.org/
- Neo4j Python driver: https://neo4j.com/docs/api/python-driver/current/
- Target runtime: Python 3.11+ (use modern features)
- Expected performance: 100-200 papers/hour
- Error budget: <5% failed requests acceptable

## Success Metrics

After implementation, you should be able to:
- Run `python -m graphlit` and expand from 15 to 1000 papers
- Resume interrupted runs without duplicates
- View structured logs showing progress
- Query Neo4j to verify 1000+ papers with full relationships
- Show type-safe, maintainable, production-quality code

Begin implementation now, following modern Python best practices.