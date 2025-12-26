"""Quick script to check community assignments in database."""
import asyncio
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.config import get_settings


async def main():
    settings = get_settings()
    async with Neo4jClient(settings.neo4j) as client:
        async with client.session() as session:
            # Check what communities exist
            result = await session.run('''
                MATCH (p:Paper)
                WHERE p.community IS NOT NULL
                RETURN DISTINCT p.community AS community_id, count(p) AS paper_count
                ORDER BY community_id
            ''')
            records = await result.data()

            print('Communities in database:')
            if records:
                for rec in records:
                    print(f"  Community {rec['community_id']}: {rec['paper_count']} papers")
            else:
                print('  ❌ NO COMMUNITIES FOUND - Papers have no community assignments!')

            # Check total papers
            result2 = await session.run('MATCH (p:Paper) RETURN count(p) AS total')
            total_rec = await result2.single()
            print(f"\nTotal papers: {total_rec['total']}")

            # Check if communities were ever calculated
            result3 = await session.run('MATCH (p:Paper) RETURN p.community AS community LIMIT 5')
            sample = await result3.data()
            print(f"\nSample paper communities: {[r['community'] for r in sample]}")


if __name__ == "__main__":
    asyncio.run(main())
