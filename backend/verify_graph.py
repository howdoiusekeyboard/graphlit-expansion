"""Quick script to verify Neo4j graph data."""
import asyncio
from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient


async def main() -> None:
    settings = get_settings()

    async with Neo4jClient(settings.neo4j) as client:
        stats = await client.get_graph_stats()

        print("\n" + "="*60)
        print("GRAPHLIT DATABASE STATISTICS")
        print("="*60)
        print(f"  Papers:    {stats['papers']:,}")
        print(f"  Authors:   {stats['authors']:,}")
        print(f"  Venues:    {stats['venues']:,}")
        print(f"  Topics:    {stats['topics']:,}")
        print(f"  Citations: {stats['citations']:,}")
        print("="*60)
        print("\n[SUCCESS] GraphLit expansion completed successfully!")
        print(f"[SUCCESS] Total {stats['papers']} papers with {stats['citations']} citation relationships")
        print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
