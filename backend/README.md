# GraphLit ResearchRadar — Backend

Academic citation network expansion and recommendation API. BFS traversal from seed DOIs via OpenAlex API into Neo4j, with collaborative filtering, community detection, and impact scoring.

## Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.14.3 | JIT compiler, no-GIL mode, enhanced REPL |
| FastAPI | 0.133.1 | REST API with strict Content-Type, OpenAPI docs |
| Neo4j | 6.1.0 (driver) | Async graph database, MERGE-based idempotent inserts |
| httpx | 0.28.1 | Async HTTP client for OpenAlex API |
| cachetools | 7.0.1 | In-memory TTLCache (1h TTL, 1000 entries) |
| Pydantic | 2.12.5 | Type-safe config + request/response models |
| structlog | 25.5.0+ | Structured JSON logging |
| aiolimiter | 1.2.1 | Async rate limiter (10 req/s for OpenAlex) |
| ruff | 0.15.3 | Linting (E/F/I/N/UP/ASYNC rules) + 2026 formatter |
| mypy | 1.19+ | Strict type checking (0 errors across 33 files) |
| pytest | 9.0+ | 77 tests with pytest-asyncio + pytest-httpx |
| uv | 0.10.6 | Package manager (10-100x faster than pip) |

## Requirements

- **Python 3.14+** — [python.org/downloads](https://www.python.org/downloads/)
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Neo4j 5.x** — [Neo4j Desktop](https://neo4j.com/download/) or Docker

## Setup

```bash
cd backend

# Create virtual environment
uv venv --python 3.14
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Unix

# Install all dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your Neo4j credentials and OpenAlex email
```

### Environment Variables

```ini
# OpenAlex API
OPENALEX__USER_AGENT=GraphLit/1.0 (mailto:your.email@edu)
OPENALEX__RATE_LIMIT_PER_SECOND=10

# Neo4j Database
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=<your-password>
NEO4J__DATABASE=neo4j

# Pipeline
EXPANSION__MAX_PAPERS=1000
EXPANSION__MAX_DEPTH=2
EXPANSION__YEAR_MIN=2015
EXPANSION__YEAR_MAX=2025
```

## Neo4j Setup

1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create a local DBMS (version 5.x, bolt://localhost:7687)
3. Start the database before running the pipeline or API

Or via Docker:
```bash
docker run -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  neo4j:5-community
```

## Usage

### Data Pipeline (BFS Expansion)

```bash
python -m graphlit              # Expand from seed DOIs → 1000+ papers
DEBUG=1 python -m graphlit      # Verbose logging
```

Pipeline steps:
1. Load seed DOIs from `data/seeds.json`
2. Resolve DOIs to OpenAlex IDs
3. BFS expansion to configured depth
4. Create citation edges (second pass)
5. Run community detection + impact scoring

Expected runtime: 5-10 hours for 1000 papers. Pipeline is idempotent — interrupt and resume safely.

### API Server

```bash
uvicorn graphlit.api.main:app --host 0.0.0.0 --port 8080 --reload
```

- Swagger UI: http://localhost:8080/docs
- OpenAPI Schema: http://localhost:8080/openapi.json

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/recommendations/paper/{id}` | Paper recommendations (collaborative filtering) |
| GET | `/api/v1/recommendations/paper/{id}/detail` | Paper metadata |
| GET | `/api/v1/recommendations/paper/{id}/network` | Citation network (1-hop) |
| POST | `/api/v1/recommendations/query` | Query-based search (topics + year filters) |
| GET | `/api/v1/recommendations/communities` | All communities list |
| GET | `/api/v1/recommendations/community/{id}/trending` | Top papers in a community |
| GET | `/api/v1/recommendations/feed/{session_id}` | Personalized feed |
| POST | `/api/v1/recommendations/track/view` | Track paper views for personalization |
| GET | `/api/v1/admin/cache/stats` | In-memory cache statistics |
| POST | `/api/v1/admin/cache/clear` | Clear cache |
| GET | `/health` | Health check |

### Recommendation Engine

The hybrid recommendation system combines 4 signals:

| Signal | Weight | Method |
|--------|--------|--------|
| Citation overlap | 35% | Jaccard similarity on citation sets |
| Topic affinity | 30% | Cosine similarity on topic vectors |
| Author collaboration | 20% | Shared author network analysis |
| Citation velocity | 15% | Growth rate similarity |

### Personalized Feed Algorithm

- **Time-decayed weighting**: 7-day half-life (`weight = base × 0.5^(days/7)`)
- **Diversity filtering**: Max 3 papers/year, max 5 papers/community
- **Impact boosting**: +10% for high-impact papers (score > 70)
- **Community exploration**: +15% bonus for papers from unvisited communities
- **Smart caching**: 2-min TTL for personalized feeds, 5-min for trending

Cold start (no history) returns trending papers from diverse communities.

## Graph Schema

**Nodes**: `Paper`, `Author`, `Venue`, `Topic`, `UserProfile`

**Relationships**:
- `(Paper)-[:CITES]->(Paper)`
- `(Paper)-[:AUTHORED_BY {position}]->(Author)`
- `(Paper)-[:PUBLISHED_IN]->(Venue)`
- `(Paper)-[:BELONGS_TO_TOPIC {score}]->(Topic)`
- `(UserProfile)-[:VIEWED {timestamp, weight}]->(Paper)`

**Example queries**:
```cypher
-- Top cited papers
MATCH (p:Paper) RETURN p.title, p.citations ORDER BY p.citations DESC LIMIT 10

-- Papers by author
MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author {name: "Jie Zhou"}) RETURN p.title, p.year

-- Citation paths (up to 3 hops)
MATCH path = (p1:Paper)-[:CITES*1..3]->(p2:Paper)
WHERE p1.title CONTAINS "GNN" RETURN path LIMIT 10
```

## Development

### Code Quality (all must pass with zero errors)

```bash
mypy --strict src/              # Type checking (33 files)
ruff check src/ tests/          # Lint (E/F/I/N/UP/ASYNC rules)
ruff format src/ tests/         # Auto-format (2026 style)
```

### Testing

```bash
pytest                                          # All 77 tests
pytest --cov=graphlit --cov-report=term-missing # With coverage
pytest tests/api/test_personalized_feed.py -v   # Feed tests (8 scenarios)
pytest tests/test_mapper.py -v                  # Mapper tests
```

### Graph Verification Scripts

```bash
python quick_check.py           # Summary statistics
python verify_graph.py          # Graph structure validation
python full_stats.py            # Detailed report
```

## Architecture

```
src/graphlit/
├── __main__.py                 # CLI entry: python -m graphlit
├── config.py                   # Pydantic Settings (env_nested_delimiter="__")
├── models.py                   # Frozen dataclasses: Paper, Author, Venue, Topic
├── analytics/
│   ├── community_detector.py   # Louvain community detection via Neo4j GDS
│   └── impact_scorer.py        # Predictive impact score (4 components)
├── api/
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── dependencies.py         # Singleton DI: Neo4j, cache, recommender
│   └── routes/
│       ├── admin.py            # Cache stats + invalidation
│       └── recommendations.py  # 8 recommendation endpoints
├── cache/
│   └── memory_cache.py         # cachetools.TTLCache (1h TTL, 1000 entries)
├── clients/
│   └── openalex.py             # httpx.AsyncClient + aiolimiter (10 req/s)
├── database/
│   ├── neo4j_client.py         # AsyncGraphDatabase, MERGE-based inserts
│   ├── queries.py              # Cypher query templates
│   └── graph_algorithms.py     # PageRank, Louvain via Neo4j GDS
├── pipeline/
│   ├── mapper.py               # OpenAlex JSON → domain models
│   └── orchestrator.py         # BFS expansion with Rich progress bars
├── recommendations/
│   ├── collaborative_filter.py # Hybrid 4-signal recommender
│   ├── content_based.py        # Topic similarity recommender
│   └── similarity.py           # Citation velocity + topic affinity
└── utils/
    ├── logging.py              # structlog configuration
    └── retry.py                # Exponential backoff decorator
```

## Troubleshooting

**Neo4j connection errors**:
- Verify database is running (Active in Neo4j Desktop)
- Check `.env` password matches DBMS password
- Try `neo4j://` protocol instead of `bolt://`

**Rate limiting (429 errors)**:
- Handled automatically with exponential backoff
- If persistent, reduce `OPENALEX__RATE_LIMIT_PER_SECOND` to 8

**Resume after interruption**:
- Re-run `python -m graphlit` — existing papers loaded from Neo4j, only new papers fetched

**Cache not updating**:
- In-memory cache has 1-hour TTL. Clear manually: `POST /api/v1/admin/cache/clear`

## Data Snapshot

- **Papers**: 895 across 8 communities
- **Pipeline last run**: 2025-12-17
- **Top bridging papers**: AlphaFold 2, GPT-3, TensorFlow

## License

MIT
