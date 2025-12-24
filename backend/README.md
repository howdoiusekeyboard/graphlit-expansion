# GraphLit Expansion System

Academic citation network expansion via OpenAlex API and Neo4j. BFS traversal from 15 seed DOIs to collect 1000+ papers with full metadata.

## Architecture

- **Python 3.13.6** - JIT compiler, no-GIL mode, enhanced REPL
- Async I/O (httpx 0.28.1, neo4j-driver 6.0.3)
- Rate-limited OpenAlex client (10 req/s)
- Idempotent MERGE operations (resumable)
- In-memory caching (cachetools 6.2.4, 100x faster than Redis)
- Structured logging (structlog 24.4.0)
- Type-safe configuration (pydantic 2.12)
- Strict mypy 1.14.0 compliance
- **FastAPI 0.127.0** - Production-ready REST API

## Requirements

- **Python 3.13.6+** (recommended for JIT compiler)
- **uv** (recommended package manager, 80x faster than pip)
- Neo4j 5.x (database) or 6.x (driver compatible)
- OpenAlex API access (email required for polite pool)

## Setup (Modern 2025 Stack)

### Option 1: With uv (Recommended - 10-100x faster)

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/howdoiusekeyboard/graphlit-expansion.git
cd graphlit-expansion/backend

# Create virtual environment with Python 3.13
uv venv --python 3.13
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies (lightning fast!)
uv pip install -e ".[dev]"
```

Edit `.env`:

```ini
OPENALEX__USER_AGENT=GraphLit/1.0 (mailto:your.email@edu)
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=<password>
EXPANSION__MAX_PAPERS=1000
EXPANSION__MAX_DEPTH=2
```

## Neo4j Setup

Download Neo4j Desktop from neo4j.com/download.

Create local DBMS:
- Version: 5.x
- Database: neo4j
- Bolt: bolt://localhost:7687

Start database before running pipeline.

## Usage

```bash
python -m graphlit
```

Pipeline execution:
1. Load seeds from `data/seeds.json`
2. Resolve DOIs to OpenAlex IDs
3. BFS expansion to MAX_DEPTH
4. Create citation edges
5. Output statistics

Expected runtime: 5-10 hours for 1000 papers.

## Verification

```bash
python quick_check.py      # Summary stats
python verify_graph.py     # Graph validation
python full_stats.py       # Detailed report
```

Neo4j Browser:
```cypher
MATCH (p:Paper) RETURN count(p)
```

## Schema

Nodes:
- `Paper`: openalex_id, doi, title, year, citations, abstract
- `Author`: openalex_id, name, orcid, institution
- `Venue`: openalex_id, name, type, publisher
- `Topic`: openalex_id, name, level

Relationships:
- `(Paper)-[:CITES]->(Paper)`
- `(Paper)-[:AUTHORED_BY {position}]->(Author)`
- `(Paper)-[:PUBLISHED_IN]->(Venue)`
- `(Paper)-[:BELONGS_TO_TOPIC {score}]->(Topic)`

Query examples:

```cypher
// Top cited
MATCH (p:Paper)
RETURN p.title, p.citations
ORDER BY p.citations DESC LIMIT 10

// By author
MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author {name: "Jie Zhou"})
RETURN p.title, p.year

// Citation paths
MATCH path = (p1:Paper)-[:CITES*1..3]->(p2:Paper)
WHERE p1.title CONTAINS "GNN"
RETURN path LIMIT 10
```

## Development

Code quality:

```bash
mypy --strict src/          # Type checking
ruff check src/ tests/      # Lint
ruff format src/ tests/     # Format
```

Testing:

```bash
pytest                                   # All tests
pytest --cov=graphlit --cov-report=term  # Coverage
pytest tests/test_mapper.py -v           # Specific
```

## Troubleshooting

Neo4j connection errors:
- Verify database status (Active)
- Check .env password matches DBMS password
- Try neo4j:// protocol instead of bolt://

Rate limiting:
- Handled automatically with exponential backoff
- If persistent, reduce OPENALEX__RATE_LIMIT_PER_SECOND to 8

Missing seeds:
- Some DOIs may not exist in OpenAlex
- Check expansion_log.txt for failures
- Pipeline continues with available seeds

Resume after interruption:
- Re-run `python -m graphlit`
- Existing papers loaded from Neo4j
- Only new papers fetched

## Stack

- httpx 0.27.0
- neo4j 5.26.0
- pydantic 2.9.2
- pydantic-settings 2.5.2
- structlog 24.4.0
- rich 13.9.4
- aiolimiter 1.2.1

See architechture.md for design details.

## License

MIT
