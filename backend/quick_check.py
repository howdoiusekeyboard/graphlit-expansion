"""Quick connectivity and simple count check."""
import asyncio
from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient


async def main() -> None:
    settings = get_settings()
    client = Neo4jClient(settings.neo4j)

    try:
        await client.initialize()
        print("Connected to Neo4j successfully!")

        # Simple paper count
        count = await client.get_paper_count()
        print(f"\nPaper count: {count:,}")

        # Check if we can verify connection
        is_healthy = await client.verify_connection()
        print(f"Database healthy: {is_healthy}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
