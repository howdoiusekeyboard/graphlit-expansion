"""Get complete graph statistics."""
import asyncio
from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient


async def get_count(client: Neo4jClient, label: str) -> int:
    """Get count for a specific node type."""
    query = f"MATCH (n:{label}) RETURN count(n) AS count"
    async with client.session() as session:
        result = await session.run(query)
        record = await result.single()
        return record["count"] if record else 0


async def get_citation_count(client: Neo4jClient) -> int:
    """Get citation relationship count."""
    query = "MATCH ()-[r:CITES]->() RETURN count(r) AS count"
    async with client.session() as session:
        result = await session.run(query)
        record = await result.single()
        return record["count"] if record else 0


async def main() -> None:
    settings = get_settings()
    client = Neo4jClient(settings.neo4j)

    try:
        await client.initialize()

        print("\n" + "="*70)
        print("              GRAPHLIT EXPANSION - FINAL RESULTS")
        print("="*70)

        papers = await get_count(client, "Paper")
        print(f"  Papers:           {papers:,}")

        authors = await get_count(client, "Author")
        print(f"  Authors:          {authors:,}")

        venues = await get_count(client, "Venue")
        print(f"  Venues:           {venues:,}")

        topics = await get_count(client, "Topic")
        print(f"  Topics:           {topics:,}")

        citations = await get_citation_count(client)
        print(f"  Citation Links:   {citations:,}")

        print("="*70)
        print(f"\n  [SUCCESS] Expanded from 15 seeds to {papers:,} papers!")
        print(f"  [SUCCESS] Created citation network with {citations:,} relationships!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
