"""Cypher query templates for Neo4j operations.

This module contains all Cypher queries used by the Neo4j client.
Queries use MERGE for idempotency, ensuring safe resumable operations.
"""

from __future__ import annotations

# =============================================================================
# Index Creation Queries
# =============================================================================

CREATE_PAPER_INDEX = """
CREATE INDEX paper_openalex_id IF NOT EXISTS
FOR (p:Paper)
ON (p.openalex_id)
"""

CREATE_PAPER_DOI_INDEX = """
CREATE INDEX paper_doi IF NOT EXISTS
FOR (p:Paper)
ON (p.doi)
"""

CREATE_AUTHOR_INDEX = """
CREATE INDEX author_openalex_id IF NOT EXISTS
FOR (a:Author)
ON (a.openalex_id)
"""

CREATE_VENUE_INDEX = """
CREATE INDEX venue_openalex_id IF NOT EXISTS
FOR (v:Venue)
ON (v.openalex_id)
"""

CREATE_TOPIC_INDEX = """
CREATE INDEX topic_openalex_id IF NOT EXISTS
FOR (t:Topic)
ON (t.openalex_id)
"""

ALL_INDEX_QUERIES = [
    CREATE_PAPER_INDEX,
    CREATE_PAPER_DOI_INDEX,
    CREATE_AUTHOR_INDEX,
    CREATE_VENUE_INDEX,
    CREATE_TOPIC_INDEX,
]

# =============================================================================
# Paper Queries
# =============================================================================

MERGE_PAPER = """
MERGE (p:Paper {openalex_id: $openalex_id})
SET p.doi = $doi,
    p.title = $title,
    p.year = $year,
    p.citations = $citations,
    p.abstract = $abstract
RETURN p.openalex_id AS id
"""

GET_PAPER = """
MATCH (p:Paper {openalex_id: $openalex_id})
RETURN p
"""

PAPER_EXISTS = """
MATCH (p:Paper {openalex_id: $openalex_id})
RETURN count(p) > 0 AS exists
"""

COUNT_PAPERS = """
MATCH (p:Paper)
RETURN count(p) AS count
"""

GET_ALL_PAPER_IDS = """
MATCH (p:Paper)
RETURN p.openalex_id AS id
"""

# =============================================================================
# Author Queries
# =============================================================================

MERGE_AUTHOR = """
MERGE (a:Author {openalex_id: $openalex_id})
SET a.name = $name,
    a.orcid = $orcid,
    a.institution = $institution
RETURN a.openalex_id AS id
"""

# =============================================================================
# Venue Queries
# =============================================================================

MERGE_VENUE = """
MERGE (v:Venue {openalex_id: $openalex_id})
SET v.name = $name,
    v.type = $venue_type,
    v.publisher = $publisher
RETURN v.openalex_id AS id
"""

# =============================================================================
# Topic Queries
# =============================================================================

MERGE_TOPIC = """
MERGE (t:Topic {openalex_id: $openalex_id})
SET t.name = $name,
    t.level = $level
RETURN t.openalex_id AS id
"""

# =============================================================================
# Relationship Queries
# =============================================================================

MERGE_AUTHORSHIP = """
MATCH (p:Paper {openalex_id: $paper_id})
MATCH (a:Author {openalex_id: $author_id})
MERGE (p)-[r:AUTHORED_BY]->(a)
SET r.position = $position
"""

MERGE_PUBLICATION = """
MATCH (p:Paper {openalex_id: $paper_id})
MATCH (v:Venue {openalex_id: $venue_id})
MERGE (p)-[:PUBLISHED_IN]->(v)
"""

MERGE_TOPIC_ASSIGNMENT = """
MATCH (p:Paper {openalex_id: $paper_id})
MATCH (t:Topic {openalex_id: $topic_id})
MERGE (p)-[r:BELONGS_TO_TOPIC]->(t)
SET r.score = $score
"""

MERGE_CITATION = """
MATCH (citing:Paper {openalex_id: $citing_id})
MATCH (cited:Paper {openalex_id: $cited_id})
MERGE (citing)-[:CITES]->(cited)
"""

# =============================================================================
# Statistics Queries
# =============================================================================

GET_GRAPH_STATS = """
MATCH (p:Paper)
OPTIONAL MATCH (a:Author)
OPTIONAL MATCH (v:Venue)
OPTIONAL MATCH (t:Topic)
OPTIONAL MATCH ()-[c:CITES]->()
RETURN
    count(DISTINCT p) AS papers,
    count(DISTINCT a) AS authors,
    count(DISTINCT v) AS venues,
    count(DISTINCT t) AS topics,
    count(c) AS citations
"""

# =============================================================================
# Cleanup Queries (for testing)
# =============================================================================

DELETE_ALL = """
MATCH (n)
DETACH DELETE n
"""
