"""Check community 513 status in Neo4j database.

This script investigates why community 513 returns 404 for trending papers.
Checks: paper count, year range, pagerank status, impact_score status.
"""

from __future__ import annotations

import asyncio

from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient


async def main() -> None:
    """Investigate community 513 state and diagnose 404 error."""
    print("=" * 70)
    print("COMMUNITY 513 DIAGNOSTIC REPORT")
    print("=" * 70)

    settings = get_settings()

    async with Neo4jClient(settings.neo4j) as client:
        async with client.session() as session:
            # Query 1: Total papers and year statistics
            result = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.community = $community_id
                RETURN count(p) AS total,
                       min(p.year) AS min_year,
                       max(p.year) AS max_year,
                       avg(p.citations) AS avg_citations
                """,
                community_id=513,
            )
            stats_record = await result.single()

            if not stats_record or stats_record["total"] == 0:
                print("\n❌ Community 513 does NOT exist in database!")
                print("This explains the 404 error.\n")
                print("=" * 70)
                return

            total = stats_record["total"]
            min_year = stats_record["min_year"]
            max_year = stats_record["max_year"]
            avg_cit = stats_record["avg_citations"]

            # Query 2: Year filter check
            result2 = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.community = $community_id AND p.year >= 2020
                RETURN count(p) AS recent
                """,
                community_id=513,
            )
            recent = (await result2.single())["recent"]

            # Query 3: Analytics status
            result3 = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.community = $community_id
                RETURN
                  sum(CASE WHEN p.pagerank IS NULL THEN 1 ELSE 0 END) AS null_pagerank,
                  sum(CASE WHEN p.impact_score IS NULL THEN 1 ELSE 0 END) AS null_impact
                """,
                community_id=513,
            )
            analytics = await result3.single()

            # Query 4: Sample papers
            result4 = await session.run(
                """
                MATCH (p:Paper)
                WHERE p.community = $community_id
                RETURN p.openalex_id AS id, p.title AS title, p.year AS year,
                       p.citations AS citations, p.pagerank AS pagerank,
                       p.impact_score AS impact_score
                ORDER BY p.citations DESC
                LIMIT 5
                """,
                community_id=513,
            )
            samples = await result4.data()

            # Print diagnostic report
            print(f"\n📊 Paper Statistics:")
            print(f"   Total papers: {total}")
            print(f"   Year range: {min_year} - {max_year}")
            print(f"   Papers >= 2020: {recent}")
            print(f"   Papers < 2020: {total - recent}")
            print(f"   Avg citations: {avg_cit:.1f}")

            print(f"\n🧮 Analytics Status:")
            print(f"   Papers with NULL pagerank: {analytics['null_pagerank']} / {total}")
            print(
                f"   Papers with NULL impact_score: {analytics['null_impact']} / {total}"
            )

            print(f"\n📄 Sample Papers (Top 5 by citations):")
            for i, p in enumerate(samples, 1):
                title = p["title"][:60] + "..." if len(p["title"]) > 60 else p["title"]
                print(f"\n   [{i}] {title}")
                print(f"       ID: {p['id']}")
                print(f"       Year: {p['year']}, Citations: {p['citations']}")
                print(f"       PageRank: {p['pagerank']}, Impact: {p['impact_score']}")

            # Diagnosis
            print(f"\n🔍 WHY 404 OCCURS:")
            if recent == 0:
                print("   ❌ Year filter (>= 2020) excludes ALL papers in community 513")
                print("   → Trending papers query returns empty → API raises 404")
            elif analytics["null_pagerank"] == total:
                print("   ❌ PageRank is NULL for ALL papers")
                print("   → ORDER BY p.pagerank sorts non-deterministically")
                print("   → Query may return empty or inconsistent results")
            else:
                print("   ✅ Analytics computed, year filter has matches")
                print("   → Issue may be elsewhere (check API logs)")

            print("\n" + "=" * 70)
            print("RECOMMENDED ACTIONS:")
            print("=" * 70)
            if analytics["null_pagerank"] > 0:
                print("1. Run analytics pipeline: python run_community_detection.py")
                print("2. Verify PageRank computed: curl http://localhost:8080/api/v1/admin/analytics/status")
            if recent == 0:
                print("3. Adjust year filter in API query (remove min_year=2020 default)")
            print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
