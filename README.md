# GraphLit Expansion System

Expands academic citation networks from seed papers using OpenAlex API and Neo4j. Starts with 15 seed DOIs and performs breadth-first traversal to collect 1000+ connected papers with full metadata.

## Features

- Async I/O with httpx and Neo4j async driver
- Rate limiting (10 req/sec for OpenAlex polite pool)
- Resumable via idempotent MERGE operations
- Real-time progress bars (Rich)
- Structured JSON logging (structlog)
- Type-safe configuration (Pydantic)
- Passes mypy strict mode

## Prerequisites

- Python 3.12 or later
- Neo4j Desktop 1.5.0+ (download from neo4j.com/download)
- OpenAlex polite pool access (free, requires email)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/graphlit-expansion.git
cd graphlit-expansion
```

### 2. Neo4j Desktop Setup

**Install Neo4j Desktop:**
1. Download from https://neo4j.com/download/
2. Install and create Neo4j account (free)

**Create Database:**
1. Open Neo4j Desktop
2. Click "New" → "Create Project" → name it "GraphLit"
3. Click "Add" → "Local DBMS"
4. Name: "literature-survey"
5. Password: Choose a password (save it for step 4)
6. Version: 5.x (latest stable)
7. Click "Create"

**Start Database:**
1. Click "Start" on your database
2. Wait for status to show "Active"
3. Click on the database → "Open" → copy the Bolt URL
   - Should be: `bolt://localhost:7687`
   - Or: `neo4j://localhost:7687`

### 3. Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install package
pip install -e ".[dev]"
```

### 4. Configuration

```bash
# Copy template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env`:

```bash
# Your academic email (required for OpenAlex polite pool)
OPENALEX__USER_AGENT=GraphLit/1.0 (mailto:your.email@university.edu)

# Neo4j credentials from step 2
NEO4J__URI=bolt://localhost:7687
NEO4J__USERNAME=neo4j
NEO4J__PASSWORD=<password-from-step-2>
NEO4J__DATABASE=neo4j

# Expansion settings (defaults)
EXPANSION__MAX_PAPERS=1000
EXPANSION__MAX_DEPTH=2
EXPANSION__YEAR_MIN=2015
EXPANSION__YEAR_MAX=2025
```

## Usage

### Run Expansion

```bash
python -m graphlit
```

Pipeline stages:
1. Connects to Neo4j and OpenAlex
2. Loads seed DOIs from `data/seeds.json`
3. Resolves DOIs to OpenAlex work IDs
4. Performs BFS expansion to MAX_DEPTH
5. Creates citation relationships
6. Prints statistics

Expected runtime: 5-10 hours for 1000 papers (limited by API rate)

### Verify Results

```bash
# Quick stats
python quick_check.py

# Detailed graph verification
python verify_graph.py

# Full statistics report
python full_stats.py
```

Or query Neo4j Browser:
1. Neo4j Desktop → Open database → "Open Neo4j Browser"
2. Run: `MATCH (p:Paper) RETURN count(p)`

## Neo4j Schema

**Nodes:**
- `Paper`: openalex_id, doi, title, year, citations, abstract
- `Author`: openalex_id, name, orcid, institution
- `Venue`: openalex_id, name, type, publisher
- `Topic`: openalex_id, name, level

**Relationships:**
- `(Paper)-[:CITES]->(Paper)` - citation edges
- `(Paper)-[:AUTHORED_BY {position}]->(Author)` - authorship order
- `(Paper)-[:PUBLISHED_IN]->(Venue)` - publication venue
- `(Paper)-[:BELONGS_TO_TOPIC {score}]->(Topic)` - topic scores

**Sample queries:**

```cypher
// Most cited papers
MATCH (p:Paper)
RETURN p.title, p.citations
ORDER BY p.citations DESC LIMIT 10

// Papers by author
MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author {name: "Jie Zhou"})
RETURN p.title, p.year

// Citation chains
MATCH path = (p1:Paper)-[:CITES*1..3]->(p2:Paper)
WHERE p1.title CONTAINS "GNN"
RETURN path LIMIT 10
```

## Development

### Code Quality

```bash
# Type checking (must pass)
mypy --strict src/

# Linting
ruff check src/ tests/

# Auto-format
ruff format src/ tests/
```

### Testing

```bash
pytest                                    # All tests
pytest --cov=graphlit --cov-report=term  # With coverage
pytest tests/test_mapper.py -v           # Specific file
```

## Troubleshooting

**"Cannot connect to Neo4j database"**
- Check database status in Neo4j Desktop (should show "Active")
- Verify password in `.env` matches database password
- Try `neo4j://localhost:7687` instead of `bolt://localhost:7687`

**"Rate limit exceeded"**
- Pipeline handles this automatically with exponential backoff
- Persistent errors: lower `OPENALEX__RATE_LIMIT_PER_SECOND` to 8

**"Seed not found in OpenAlex"**
- Some DOIs may not exist in OpenAlex - this is expected
- Check `expansion_log.txt` for specific failed DOIs
- Pipeline continues with available seeds

**Resuming after interruption**
- Run `python -m graphlit` again
- Pipeline loads existing papers from Neo4j
- Only new papers are fetched

## Technology Stack

- Python 3.12+
- httpx 0.27.0 (async HTTP)
- neo4j 5.26.0 (graph database driver)
- pydantic 2.9.2 (configuration)
- structlog 24.4.0 (logging)
- rich 13.9.4 (progress bars)
- aiolimiter 1.2.1 (rate limiting)

See `architechture.md` for system design details.

## License

MIT License
