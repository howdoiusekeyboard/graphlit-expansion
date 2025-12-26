"""Run community detection on existing papers in Neo4j database.

This script:
1. Projects the citation graph into GDS
2. Runs Louvain community detection algorithm
3. Assigns community IDs to all papers
4. Auto-labels communities based on top topics
"""
import asyncio
from graphlit.analytics.community_detector import CommunityDetector
from graphlit.analytics.impact_scorer import ImpactScorer
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.database.graph_algorithms import GraphAlgorithms
from graphlit.config import get_settings


async def main() -> None:
    print("=" * 60)
    print("GraphLit Community Detection")
    print("=" * 60)

    settings = get_settings()

    async with Neo4jClient(settings.neo4j) as client:
        # Initialize components
        gds = GraphAlgorithms(client, settings.analytics)
        detector = CommunityDetector(client, gds, settings.analytics)

        # Step 1: Check current state
        print("\n📊 Current database status:")
        async with client.session() as session:
            result = await session.run('MATCH (p:Paper) RETURN count(p) AS total')
            total = (await result.single())['total']
            print(f"   Total papers: {total}")

            result2 = await session.run('''
                MATCH (p:Paper)
                WHERE p.community IS NOT NULL
                RETURN count(p) AS with_community
            ''')
            with_community = (await result2.single())['with_community']
            print(f"   Papers with communities: {with_community}")

        if total == 0:
            print("\n❌ No papers in database! Run the expansion pipeline first:")
            print("   python -m graphlit")
            return

        # Step 2: Detect communities
        print(f"\n🔍 Running Louvain community detection...")
        print(f"   Graph: {settings.analytics.gds_graph_name}")
        print(f"   Max iterations: {settings.analytics.louvain_max_iterations}")
        print(f"   Tolerance: {settings.analytics.louvain_tolerance}")

        await detector.detect_communities()
        print(f"   ✅ Community detection complete!")

        # Step 3: Calculate PageRank
        print(f"\n🧮 Calculating PageRank centrality...")
        try:
            pagerank_scores = await gds.calculate_pagerank()
            print(f"   ✅ PageRank computed for {len(pagerank_scores)} papers")
            if pagerank_scores:
                print(f"   📈 Top score: {max(pagerank_scores.values()):.4f}")
                print(f"   📉 Min score: {min(pagerank_scores.values()):.4f}")
        except Exception as e:
            print(f"   ⚠️  PageRank calculation failed: {e}")
            print(f"   ℹ️  Continuing without PageRank (queries will use fallback)...")

        # Step 4: Calculate Impact Scores (4 components)
        print(f"\n📊 Calculating Predictive Impact Scores...")
        print(f"   Component weights:")
        print(f"   - PageRank Centrality: {settings.analytics.pagerank_weight * 100:.0f}%")
        print(f"   - Citation Velocity: {settings.analytics.citation_velocity_weight * 100:.0f}%")
        print(f"   - Author Reputation: {settings.analytics.author_reputation_weight * 100:.0f}%")
        print(f"   - Topic Momentum: {settings.analytics.topic_momentum_weight * 100:.0f}%")

        try:
            scorer = ImpactScorer(client, gds, settings.analytics)
            print(f"   ⏳ Computing all component scores (this may take 2-5 minutes)...")
            await scorer.calculate_all_scores()

            print(f"   ⏳ Writing scores to Neo4j...")
            await scorer.save_scores_to_neo4j()
            print(f"   ✅ Impact scores saved")

            # Show top papers
            print(f"\n   🏆 Top 5 papers by impact score:")
            top_papers = await scorer.rank_papers(limit=5)
            for i, paper in enumerate(top_papers, 1):
                title = paper['title'][:50] + "..." if len(paper['title']) > 50 else paper['title']
                print(f"      {i}. {title}")
                print(f"         Score: {paper['impact_score']:.1f} | "
                      f"PageRank: {paper['pagerank']:.3f} | "
                      f"Citations: {paper['citations']}")
        except Exception as e:
            print(f"   ⚠️  Impact scoring failed: {e}")
            print(f"   ℹ️  Continuing without impact scores (queries will use fallback)...")

        # Step 5: Display community statistics
        print("\n✅ Analytics pipeline complete!")

        stats = await detector.get_community_stats()
        print(f"\n📈 Detected {len(stats)} communities:")
        print(f"   {'Community':<12} {'Papers':<10} {'Avg Citations':<15}")
        print(f"   {'-'*12} {'-'*10} {'-'*15}")

        for stat in stats[:20]:  # Show top 20
            community_id = stat['community_id']
            paper_count = stat['paper_count']
            avg_citations = stat.get('avg_citations', 0)
            print(f"   {community_id:<12} {paper_count:<10} {avg_citations:<15.1f}")

        if len(stats) > 20:
            print(f"   ... and {len(stats) - 20} more communities")

        print("\n✅ Communities and analytics ready!")

        print("\n" + "=" * 60)
        print("✅ Community detection & analytics finished successfully!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Restart your backend API (Ctrl+C and re-run uvicorn)")
        print("   2. Refresh your frontend browser")
        print("   3. Navigate to Communities page to see trending papers")
        print("   4. Verify analytics: python check_community_513.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
