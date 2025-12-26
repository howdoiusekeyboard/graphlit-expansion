"""Diagnose why 45 papers are missing impact scores."""
from __future__ import annotations

import asyncio

import structlog
from rich.console import Console
from rich.table import Table

from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient

logger = structlog.get_logger(__name__)
console = Console()


async def main() -> None:
    """Investigate papers missing impact scores."""
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]GraphLit Impact Score Diagnostic Report[/bold cyan]")
    console.print("=" * 80 + "\n")

    settings = get_settings()

    async with Neo4jClient(settings.neo4j) as client:
        async with client.session() as session:
            # Query 1: Overall statistics
            console.print("[bold]📊 Overall Statistics[/bold]")
            result = await session.run("""
                MATCH (p:Paper)
                RETURN
                  count(p) AS total,
                  sum(CASE WHEN p.impact_score IS NOT NULL THEN 1 ELSE 0 END) AS with_score,
                  sum(CASE WHEN p.impact_score IS NULL THEN 1 ELSE 0 END) AS without_score
            """)
            stats = await result.single()
            total = stats["total"]
            with_score = stats["with_score"]
            without_score = stats["without_score"]

            console.print(f"   Total papers: [green]{total}[/green]")
            console.print(f"   With impact scores: [green]{with_score}[/green] ({with_score/total*100:.1f}%)")
            console.print(f"   Missing impact scores: [red]{without_score}[/red] ({without_score/total*100:.1f}%)")
            console.print()

            if without_score == 0:
                console.print("✅ [bold green]All papers have impact scores![/bold green]\n")
                return

            # Query 2: Analyze missing papers metadata
            console.print("[bold]🔍 Metadata Analysis of Missing Papers[/bold]\n")
            result = await session.run("""
                MATCH (p:Paper)
                WHERE p.impact_score IS NULL
                OPTIONAL MATCH (p)-[:AUTHORED_BY]->(a:Author)
                OPTIONAL MATCH (p)-[:BELONGS_TO_TOPIC]->(t:Topic)
                RETURN
                  p.openalex_id AS paper_id,
                  p.title AS title,
                  p.year AS year,
                  p.citations AS citations,
                  p.pagerank AS pagerank,
                  count(DISTINCT a) AS author_count,
                  count(DISTINCT t) AS topic_count
                ORDER BY p.year DESC
            """)
            missing_papers = await result.data()

            # Pattern analysis
            patterns = {
                "missing_year": 0,
                "missing_pagerank": 0,
                "missing_authors": 0,
                "missing_topics": 0,
                "zero_citations": 0,
                "recent_2024_plus": 0,
            }

            for paper in missing_papers:
                if paper["year"] is None:
                    patterns["missing_year"] += 1
                if paper["pagerank"] is None:
                    patterns["missing_pagerank"] += 1
                if paper["author_count"] == 0:
                    patterns["missing_authors"] += 1
                if paper["topic_count"] == 0:
                    patterns["missing_topics"] += 1
                if paper["citations"] == 0:
                    patterns["zero_citations"] += 1
                if paper["year"] and paper["year"] >= 2024:
                    patterns["recent_2024_plus"] += 1

            # Display pattern table
            table = Table(title="Common Patterns in Missing Scores")
            table.add_column("Issue", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            table.add_column("% of Missing", justify="right")

            for pattern, count in patterns.items():
                pct = (count / without_score * 100) if without_score > 0 else 0
                table.add_row(
                    pattern.replace("_", " ").title(),
                    str(count),
                    f"{pct:.1f}%",
                )

            console.print(table)
            console.print()

            # Sample papers
            console.print("[bold]📄 Sample of Papers Missing Impact Scores (First 5)[/bold]\n")
            for i, paper in enumerate(missing_papers[:5], 1):
                console.print(f"[bold]{i}. {paper['title'][:60]}...[/bold]")
                console.print(f"   Paper ID: {paper['paper_id']}")
                console.print(f"   Year: {paper['year'] or 'NULL'}")
                console.print(f"   Citations: {paper['citations']}")
                console.print(f"   PageRank: {paper['pagerank'] or 'NULL'}")
                console.print(f"   Authors: {paper['author_count']}")
                console.print(f"   Topics: {paper['topic_count']}")
                console.print()

            # Recommendations
            console.print("[bold yellow]💡 Recommendations[/bold yellow]\n")

            if patterns["missing_pagerank"] == without_score:
                console.print("   ❌ [red]ALL missing papers have NULL PageRank[/red]")
                console.print("   → PageRank is a required component for impact scoring")
                console.print("   → Re-run: python run_community_detection.py")
                console.print()

            if patterns["missing_year"] > 0:
                console.print(f"   ⚠️  {patterns['missing_year']} papers missing publication year")
                console.print("   → Year is required for citation velocity component")
                console.print("   → Check OpenAlex data quality for these papers")
                console.print()

            if patterns["missing_authors"] > 0:
                console.print(f"   ⚠️  {patterns['missing_authors']} papers missing author data")
                console.print("   → Authors required for reputation component")
                console.print("   → Check AUTHORED_BY relationships in Neo4j")
                console.print()

            if patterns["missing_topics"] > 0:
                console.print(f"   ⚠️  {patterns['missing_topics']} papers missing topic data")
                console.print("   → Topics required for momentum component")
                console.print("   → Check BELONGS_TO_TOPIC relationships")
                console.print()

            if patterns["recent_2024_plus"] > 0:
                console.print(f"   ℹ️  {patterns['recent_2024_plus']} papers from 2024-2025")
                console.print("   → Very recent papers may legitimately have low scores")
                console.print("   → This is expected and not necessarily an error")
                console.print()

            console.print("=" * 80)
            console.print("[bold green]✅ Diagnostic complete![/bold green]")
            console.print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
