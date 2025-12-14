# GraphLit Expansion Architecture

## System Overview

```
╔══════════════════════════════════════════════════════════════════╗
║             GraphLit Expansion System Architecture               ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────┐                                  ┌──────────────┐
│   Seed DOIs     │                                  │   Neo4j DB   │
│  (seeds.json)   │                                  │ (Graph Store)│
└────────┬────────┘                                  └──────▲───────┘
         │                                                   │
         │ Input                                      Persist│
         │                                                   │
         ▼                                                   │
┌─────────────────────────────────────────────────────────────────┐
│                        Orchestrator (BFS)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Queue Management  • Depth Control  • Progress Tracking │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ Fetch & Transform
         ▼
┌─────────────────┐
│     Mapper      │
│  (Transform)    │
│  JSON → Models  │
└────────┬────────┘
         │
         │ API Request
         ▼
┌─────────────────┐
│  OpenAlex API   │
│     Client      │
│ (Rate Limited)  │
└─────────────────┘
```

## Data Flow

1. **Initialization Phase**
   - Load 15 seed DOIs from `seeds.json`
   - Resolve DOIs → OpenAlex IDs via API
   - Initialize BFS queue with (id, depth=0) tuples

2. **Expansion Phase (BFS Loop)**
```python
while queue not empty AND papers < max_papers:
    paper_id, depth = queue.pop()
    
    if paper_id visited:
        continue
    
    work = fetch_from_openalex(paper_id)
    
    if not should_include(work):
        continue
    
    paper, authors, venue, topics = map_to_models(work)
    
    insert_to_neo4j(paper, authors, venue, topics)
    
    if depth < max_depth:
        enqueue(work.references, depth+1)
        enqueue(work.citations, depth+1)
    
    visited.add(paper_id)
```

3. **Relationship Creation Phase**
- Second pass: iterate visited papers
- For each paper, fetch its `referenced_works`
- Create `CITES` edges where both papers exist in graph

## Components

### 1. Configuration Layer (Pydantic)
- **Purpose**: Type-safe, validated settings
- **Source**: `.env` file + defaults
- **Validation**: Pydantic V2 with custom validators
- **Hot-reload**: Not supported (restart required)

### 2. API Client (httpx + aiolimiter)
- **Purpose**: Fetch paper metadata from OpenAlex
- **Concurrency**: Async with rate limiting
- **Error Handling**: Exponential backoff on 429/500
- **Caching**: None (stateless, idempotent operations)

### 3. Mapper (Pure Functions)
- **Purpose**: Transform API JSON → Domain Models
- **Input**: OpenAlex work JSON
- **Output**: `Paper`, `Author`, `Venue`, `Topic` dataclasses
- **Filtering**: Year range, concept IDs, missing fields

### 4. Neo4j Client (Async Driver)
- **Purpose**: Graph database operations
- **Transactions**: Explicit per-operation
- **Idempotency**: `MERGE` for all inserts
- **Indexes**: Created on startup for performance

### 5. Orchestrator (State Machine)
- **Purpose**: Coordinate expansion workflow
- **Algorithm**: Breadth-First Search (BFS)
- **State**: `visited: Set[str]`, `queue: deque`
- **Progress**: Real-time via Rich progress bars

## Neo4j Schema

```cypher
// Node Types
(:Paper {openalex_id, doi, title, year, citations, abstract})
(:Author {openalex_id, name, orcid, institution})
(:Venue {openalex_id, name, type, publisher})
(:Topic {openalex_id, name, level})

// Relationship Types
(:Paper)-[:CITES]->(:Paper)
(:Paper)-[:AUTHORED_BY {position}]->(:Author)
(:Paper)-[:PUBLISHED_IN]->(:Venue)
(:Paper)-[:BELONGS_TO_TOPIC {score}]->(:Topic)
```

## Performance Characteristics

| Operation | Time Complexity | API Calls | DB Operations |
|-----------|----------------|-----------|---------------|
| Fetch Paper | O(1) | 1 | 0 |
| Map to Models | O(n) where n=authors | 0 | 0 |
| Insert Paper | O(1) | 0 | 1 MERGE |
| Enqueue Neighbors | O(k) where k=refs+cites | 0 | 0 |
| Full Expansion | O(V + E) | V | V + 4V + E |

**Bottleneck**: OpenAlex rate limit (10 req/s)  
**Expected Runtime**: 1000 papers / 10 req/s ≈ 100 seconds + overhead ≈ 5-10 hours

## Error Handling Strategy

```python
try:
    work = await api.get_work(paper_id)
except httpx.HTTPStatusError as e:
    if e.status_code == 429:
        await asyncio.sleep(exponential_backoff())
        retry()
    elif e.status_code == 404:
        log.warning("paper_not_found", id=paper_id)
        continue
    else:
        raise
except httpx.TimeoutException:
    log.warning("timeout", id=paper_id)
    retry_with_backoff()
```

## Observability

- **Logging**: Structured JSON logs via `structlog`
- **Metrics**: Papers processed, API calls, errors
- **Progress**: Rich progress bars in terminal
- **Debugging**: Set `DEBUG=1` for verbose logs

## Scaling Considerations

### Current (1K papers)
- Single-threaded async
- In-memory queue
- No persistence of queue state

### Future (10K+ papers)
- Persist queue to Redis
- Distribute via Celery
- Add Prometheus metrics
- Implement circuit breakers

## Testing Strategy

### Unit Tests
- `test_mapper.py`: Pure function tests
- `test_models.py`: Dataclass validation

### Integration Tests
- `test_openalex.py`: Mock API with `pytest-httpx`
- `test_neo4j.py`: Use `testcontainers` for real DB

### E2E Tests
- Smoke test: 50-paper expansion
- Verify all relationships created
- Check idempotency (run twice, same result)

## Deployment

### Local Development
```bash
docker-compose up -d # Neo4j container
python -m graphlit # Run expansion
```

### Production (Future)
- Docker image with multi-stage build
- Kubernetes CronJob for scheduled runs
- Secrets via Vault/AWS Secrets Manager