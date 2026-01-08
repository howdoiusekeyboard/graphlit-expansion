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

# Performance indexes for query optimization
CREATE_PAPER_YEAR_INDEX = """
CREATE INDEX paper_year IF NOT EXISTS
FOR (p:Paper)
ON (p.year)
"""

CREATE_PAPER_IMPACT_SCORE_INDEX = """
CREATE INDEX paper_impact_score IF NOT EXISTS
FOR (p:Paper)
ON (p.impact_score)
"""

CREATE_PAPER_CITATIONS_INDEX = """
CREATE INDEX paper_citations IF NOT EXISTS
FOR (p:Paper)
ON (p.citations)
"""

CREATE_PAPER_COMMUNITY_INDEX = """
CREATE INDEX paper_community IF NOT EXISTS
FOR (p:Paper)
ON (p.community)
"""

CREATE_USER_PROFILE_INDEX = """
CREATE INDEX user_profile_session_id IF NOT EXISTS
FOR (u:UserProfile)
ON (u.session_id)
"""

ALL_INDEX_QUERIES = [
    CREATE_PAPER_INDEX,
    CREATE_PAPER_DOI_INDEX,
    CREATE_AUTHOR_INDEX,
    CREATE_VENUE_INDEX,
    CREATE_TOPIC_INDEX,
    CREATE_PAPER_YEAR_INDEX,
    CREATE_PAPER_IMPACT_SCORE_INDEX,
    CREATE_PAPER_CITATIONS_INDEX,
    CREATE_PAPER_COMMUNITY_INDEX,
    CREATE_USER_PROFILE_INDEX,
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
WITH count(p) AS papers
MATCH (a:Author)
WITH papers, count(a) AS authors
MATCH (v:Venue)
WITH papers, authors, count(v) AS venues
MATCH (t:Topic)
WITH papers, authors, venues, count(t) AS topics
MATCH ()-[c:CITES]->()
RETURN papers, authors, venues, topics, count(c) AS citations
"""

# =============================================================================
# Recommendation Queries
# =============================================================================

GET_ALL_PAPERS_WITH_SCORES = """
MATCH (p:Paper)
WHERE ($year_min IS NULL OR p.year >= $year_min)
  AND ($year_max IS NULL OR p.year <= $year_max)
  AND p.openalex_id IS NOT NULL
  AND p.openalex_id <> 'None'
  AND p.title IS NOT NULL
  AND (
    SIZE($topics) = 0
    OR SIZE([topic IN $topics WHERE toLower(p.title) CONTAINS toLower(topic)]) > 0
  )
OPTIONAL MATCH (p)-[r:BELONGS_TO_TOPIC]->(t:Topic)
WITH p, COLLECT(DISTINCT t.name) AS matched_topics,
     SIZE([topic IN $topics WHERE toLower(p.title) CONTAINS toLower(topic)]) AS topic_match_count
RETURN DISTINCT p.openalex_id AS paper_id,
       p.title AS title,
       p.year AS year,
       p.citations AS citations,
       p.impact_score AS impact_score,
       matched_topics,
       topic_match_count
ORDER BY p.impact_score DESC, p.citations DESC
LIMIT $limit
"""

GET_CITATION_OVERLAP_PAPERS = """
MATCH (source:Paper {openalex_id: $paper_id})-[:CITES]->(cited:Paper)
WITH source, COLLECT(cited.openalex_id) AS source_citations
MATCH (candidate:Paper)-[:CITES]->(cited:Paper)
WHERE candidate.openalex_id <> $paper_id
  AND cited.openalex_id IN source_citations
WITH candidate, source_citations, COLLECT(DISTINCT cited.openalex_id) AS candidate_citations
WITH candidate, source_citations, candidate_citations,
     SIZE([x IN source_citations WHERE x IN candidate_citations]) AS overlap,
     SIZE(
         source_citations +
         [x IN candidate_citations WHERE NOT x IN source_citations]
     ) AS union_size
WHERE overlap > 0
RETURN candidate.openalex_id AS paper_id,
       candidate.title AS title,
       candidate.year AS year,
       candidate.citations AS citations,
       candidate.impact_score AS impact_score,
       toFloat(overlap) / toFloat(union_size) AS jaccard_similarity
ORDER BY jaccard_similarity DESC
LIMIT $limit
"""

GET_PAPER_TOPICS = """
MATCH (p:Paper {openalex_id: $paper_id})-[r:BELONGS_TO_TOPIC]->(t:Topic)
RETURN t.openalex_id AS topic_id,
       t.name AS topic_name,
       r.score AS score
ORDER BY r.score DESC
"""

GET_SIMILAR_TOPIC_PAPERS = """
MATCH (source:Paper {openalex_id: $paper_id})-[r1:BELONGS_TO_TOPIC]->(t:Topic)
      <-[r2:BELONGS_TO_TOPIC]-(candidate:Paper)
WHERE candidate.openalex_id <> $paper_id
WITH candidate, SUM(r1.score * r2.score) AS topic_similarity
WHERE topic_similarity > 0
RETURN candidate.openalex_id AS paper_id,
       candidate.title AS title,
       candidate.year AS year,
       candidate.citations AS citations,
       candidate.impact_score AS impact_score,
       topic_similarity
ORDER BY topic_similarity DESC
LIMIT $limit
"""

GET_COAUTHOR_NETWORK_PAPERS = """
MATCH (source:Paper {openalex_id: $paper_id})-[:AUTHORED_BY]->(author:Author)
      <-[:AUTHORED_BY]-(candidate:Paper)
WHERE candidate.openalex_id <> $paper_id
WITH candidate, COUNT(DISTINCT author) AS shared_authors
WHERE shared_authors > 0
RETURN candidate.openalex_id AS paper_id,
       candidate.title AS title,
       candidate.year AS year,
       candidate.citations AS citations,
       candidate.impact_score AS impact_score,
       shared_authors
ORDER BY shared_authors DESC
LIMIT $limit
"""

GET_SIMILAR_VELOCITY_PAPERS = """
MATCH (source:Paper {openalex_id: $paper_id})
WITH source, toFloat(source.citations) / (2025 - source.year + 1) AS source_velocity
MATCH (candidate:Paper)
WHERE candidate.openalex_id <> $paper_id
  AND candidate.year IS NOT NULL
WITH candidate, source_velocity,
     toFloat(candidate.citations) / (2025 - candidate.year + 1) AS candidate_velocity
WITH candidate, source_velocity, candidate_velocity,
     abs(source_velocity - candidate_velocity) AS velocity_diff
WHERE velocity_diff < source_velocity * 0.5
RETURN candidate.openalex_id AS paper_id,
       candidate.title AS title,
       candidate.year AS year,
       candidate.citations AS citations,
       candidate.impact_score AS impact_score,
       candidate_velocity AS citation_velocity
ORDER BY velocity_diff ASC
LIMIT $limit
"""

GET_COMMUNITY_TRENDING_PAPERS = """
MATCH (p:Paper)
WHERE p.community = $community_id
  AND ($min_year IS NULL OR p.year >= $min_year)
  AND p.openalex_id IS NOT NULL
  AND p.openalex_id <> 'None'
RETURN p.openalex_id AS paper_id,
       p.title AS title,
       p.year AS year,
       p.citations AS citations,
       p.impact_score AS impact_score,
       p.pagerank AS pagerank,
       p.community AS community
ORDER BY COALESCE(p.pagerank, 0.0) DESC, COALESCE(p.impact_score, 0.0) DESC, p.citations DESC
LIMIT $limit
"""

GET_COMMUNITY_CITATION_NETWORK = """
MATCH (p:Paper)
WHERE p.community = $community_id
  AND ($min_year IS NULL OR p.year >= $min_year)
  AND p.impact_score IS NOT NULL
  AND p.openalex_id IS NOT NULL
  AND p.openalex_id <> 'None'
WITH p
ORDER BY COALESCE(p.pagerank, 0.0) DESC, COALESCE(p.impact_score, 0.0) DESC
LIMIT $limit

WITH collect(p) AS community_papers
UNWIND community_papers AS source_paper

OPTIONAL MATCH (source_paper)-[:CITES]->(cited_paper:Paper)
WHERE cited_paper IN community_papers

WITH community_papers,
     collect(DISTINCT {
       source: source_paper.openalex_id,
       target: cited_paper.openalex_id
     }) AS citation_edges

RETURN {
  papers: [paper IN community_papers | {
    paper_id: paper.openalex_id,
    title: paper.title,
    year: paper.year,
    citations: paper.citations,
    impact_score: paper.impact_score,
    community: paper.community
  }],
  citations: [edge IN citation_edges WHERE edge.target IS NOT NULL | edge]
} AS network
"""

# =============================================================================
# User Profile Queries
# =============================================================================

MERGE_USER_PROFILE = """
MERGE (u:UserProfile {session_id: $session_id})
ON CREATE SET u.created_at = datetime()
SET u.updated_at = datetime(),
    u.viewed_papers = $viewed_papers,
    u.preferred_communities = $preferred_communities
RETURN u.session_id AS session_id
"""

GET_USER_PROFILE = """
MATCH (u:UserProfile {session_id: $session_id})
RETURN {
    session_id: u.session_id,
    viewed_papers: u.viewed_papers,
    preferred_communities: u.preferred_communities,
    created_at: toString(u.created_at),
    updated_at: toString(u.updated_at)
} AS profile
"""

ADD_VIEWED_PAPER = """
MATCH (u:UserProfile {session_id: $session_id})
MATCH (p:Paper {openalex_id: $paper_id})
MERGE (u)-[v:VIEWED]->(p)
SET v.timestamp = datetime(),
    v.weight = $weight
WITH u, p
SET u.viewed_papers = CASE
    WHEN $paper_id IN u.viewed_papers THEN u.viewed_papers
    ELSE u.viewed_papers + [$paper_id]
END,
    u.updated_at = datetime()
RETURN u.session_id AS session_id
"""

GET_USER_VIEWING_HISTORY = """
MATCH (u:UserProfile {session_id: $session_id})-[v:VIEWED]->(p:Paper)
RETURN p.openalex_id AS paper_id,
       p.title AS title,
       v.timestamp AS viewed_at,
       v.weight AS weight
ORDER BY v.timestamp DESC
LIMIT $limit
"""

# =============================================================================
# Analytics Queries
# =============================================================================

UPDATE_PAPER_IMPACT_SCORE = """
MATCH (p:Paper {openalex_id: $paper_id})
SET p.impact_score = $impact_score
RETURN p.openalex_id AS paper_id, p.impact_score AS impact_score
"""

GET_COMMUNITY_TOPIC_DISTRIBUTION = """
MATCH (p:Paper {community: $community_id})-[r:BELONGS_TO_TOPIC]->(t:Topic)
WITH t.name AS topic, sum(r.score) AS total_score, count(p) AS paper_count
RETURN topic, total_score, paper_count
ORDER BY total_score DESC
"""

GET_BRIDGING_PAPERS = """
MATCH (p:Paper)
WHERE p.betweenness IS NOT NULL
WITH p, size([(p)-[:CITES]->() | 1]) AS out_degree
WHERE out_degree >= $min_communities
RETURN p.openalex_id AS paper_id,
       p.title AS title,
       p.year AS year,
       p.citations AS citations,
       p.betweenness AS betweenness_score,
       out_degree AS connected_communities
ORDER BY p.betweenness DESC
LIMIT $limit
"""

GET_COMMUNITY_STATS = """
MATCH (p:Paper)
WHERE p.community IS NOT NULL
WITH p.community AS community_id,
     count(p) AS size,
     avg(p.citations) AS avg_citations,
     max(p.year) AS max_year,
     min(p.year) AS min_year
WHERE size >= 3
RETURN community_id, size, avg_citations, max_year, min_year
ORDER BY size DESC
"""

GET_COMMUNITY_ANALYTICS = """
// Get all papers in the community
MATCH (p:Paper)
WHERE p.community = $community_id
  AND p.openalex_id IS NOT NULL
  AND p.openalex_id <> 'None'
WITH collect(p) AS community_papers, count(p) AS total_papers

// Calculate network density (citation edges within community)
WITH community_papers, total_papers,
     [paper IN community_papers | paper.openalex_id] AS paper_ids
UNWIND community_papers AS source
OPTIONAL MATCH (source)-[:CITES]->(target:Paper)
WHERE target.openalex_id IN paper_ids
WITH community_papers, total_papers, paper_ids,
     count(DISTINCT target) AS citations_count
WITH community_papers, total_papers,
     sum(citations_count) AS total_edges

// Calculate possible edges
WITH community_papers, total_papers, total_edges,
     CASE
       WHEN total_papers > 1 THEN total_papers * (total_papers - 1)
       ELSE 1
     END AS possible_edges

// Calculate bridging nodes (PageRank > 0.3 - papers that bridge to other communities)
WITH community_papers, total_papers, total_edges, possible_edges,
     [paper IN community_papers
      WHERE paper.pagerank IS NOT NULL AND paper.pagerank > 0.3
      | paper] AS bridging_papers

// Calculate average PageRank
WITH community_papers, total_papers, total_edges, possible_edges, bridging_papers,
     reduce(
       sum = 0.0,
       paper IN community_papers | sum + COALESCE(paper.pagerank, 0.0)
     ) AS total_pagerank

// Calculate growth rate (papers published in recent years vs older)
WITH community_papers, total_papers, total_edges, possible_edges, bridging_papers, total_pagerank,
     [paper IN community_papers WHERE paper.year >= 2023 | paper] AS recent_papers,
     [paper IN community_papers WHERE paper.year < 2023 | paper] AS older_papers
WITH community_papers, total_papers, total_edges, possible_edges, bridging_papers, total_pagerank,
     size(recent_papers) AS recent_count,
     size(older_papers) AS older_count

// Get topic distribution
UNWIND community_papers AS paper
OPTIONAL MATCH (paper)-[r:BELONGS_TO_TOPIC]->(t:Topic)
WITH total_papers, total_edges, possible_edges, bridging_papers, total_pagerank,
     recent_count, older_count,
     t.name AS topic_name,
     sum(COALESCE(r.score, 0)) AS topic_score,
     count(DISTINCT paper) AS topic_paper_count
WHERE topic_name IS NOT NULL

// Group topics
WITH total_papers, total_edges, possible_edges, bridging_papers, total_pagerank,
     recent_count, older_count,
     collect({
       name: topic_name,
       value: toInteger(topic_score * 100),
       paper_count: topic_paper_count
     }) AS topic_distribution

// Return final analytics
RETURN {
  network_density: CASE
    WHEN possible_edges > 0 THEN toFloat(total_edges) / toFloat(possible_edges)
    ELSE 0.0
  END,
  centrality_mode: 'PageRank',
  avg_pagerank: CASE
    WHEN total_papers > 0 THEN total_pagerank / toFloat(total_papers)
    ELSE 0.0
  END,
  bridging_nodes_percent: CASE
    WHEN total_papers > 0 THEN toFloat(size(bridging_papers)) / toFloat(total_papers)
    ELSE 0.0
  END,
  growth_rate: CASE
    WHEN older_count > 0 THEN (toFloat(recent_count) - toFloat(older_count)) / toFloat(older_count)
    WHEN recent_count > 0 THEN 1.0
    ELSE 0.0
  END,
  topic_distribution: topic_distribution,
  total_papers: total_papers
} AS analytics
"""

# =============================================================================
# Cleanup Queries (for testing)
# =============================================================================

DELETE_ALL = """
MATCH (n)
DETACH DELETE n
"""
