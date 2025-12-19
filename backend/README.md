# GraphLit Expansion System

Academic citation network expansion via OpenAlex API and Neo4j. BFS traversal from 15 seed DOIs to collect 1000+ papers with full metadata.

## Architecture

- Async I/O (httpx, neo4j-driver)
- Rate-limited OpenAlex client (10 req/s)
- Idempotent MERGE operations (resumable)
- Structured logging (structlog)
- Type-safe configuration (pydantic-settings)
- Strict mypy compliance

## Requirements

- Python 3.12+
- Neo4j 5.x
- OpenAlex API access (email required for polite pool)

## Setup

```bash
git clone https://github.com/howdoiusekeyboard/graphlit-expansion.git
cd graphlit-expansion

# Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install
pip install -e ".[dev]"

# Configure
copy .env.example .env  # Windows
cp .env.example .env  # Unix
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
