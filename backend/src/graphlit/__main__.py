"""CLI entry point for GraphLit Data Expansion System.

This module provides the main entry point for running the expansion
pipeline from the command line.

Usage:
    python -m graphlit
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from graphlit.clients.openalex import OpenAlexClient
from graphlit.config import Settings, get_settings
from graphlit.database.neo4j_client import Neo4jClient, Neo4jConnectionError
from graphlit.pipeline.mapper import Mapper
from graphlit.pipeline.orchestrator import ExpansionOrchestrator
from graphlit.utils.logging import setup_logging

console = Console()


def load_seed_dois(seeds_path: Path) -> list[str]:
    """Load seed paper DOIs from JSON file.

    Args:
        seeds_path: Path to seeds.json file.

    Returns:
        List of DOI strings.

    Raises:
        FileNotFoundError: If seeds file doesn't exist.
        json.JSONDecodeError: If seeds file is invalid JSON.
    """
    with seeds_path.open(encoding="utf-8") as f:
        seed_data = json.load(f)

    dois: list[str] = []
    for entry in seed_data:
        doi = entry.get("doi")
        if doi:
            dois.append(doi)

    return dois


async def async_main() -> int:
    """Async main entry point.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    # Display banner
    console.print(Panel.fit(
        "[bold cyan]GraphLit Data Expansion Pipeline[/bold cyan]\n"
        "[dim]Academic citation network expansion using OpenAlex & Neo4j[/dim]",
        border_style="cyan",
    ))

    # Load configuration
    try:
        settings: Settings = get_settings()
    except Exception as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        console.print("\nMake sure you have a .env file with required settings.")
        console.print("See .env.example for reference.")
        return 1

    # Setup logging
    setup_logging(debug=settings.debug)

    # Display configuration
    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Max papers: {settings.expansion.max_papers}")
    console.print(f"  Max depth: {settings.expansion.max_depth}")
    console.print(f"  Year range: {settings.expansion.year_min}-{settings.expansion.year_max}")
    console.print(f"  Neo4j: {settings.neo4j.uri}")
    console.print(f"  Debug mode: {settings.debug}")

    # Load seed DOIs
    seeds_path = Path("data/seeds.json")
    if not seeds_path.exists():
        console.print(f"\n[red]Error:[/red] Seeds file not found: {seeds_path}")
        console.print("Create a seeds.json file with your seed paper DOIs.")
        return 1

    try:
        seed_dois = load_seed_dois(seeds_path)
    except json.JSONDecodeError as e:
        console.print(f"\n[red]Error:[/red] Invalid JSON in seeds file: {e}")
        return 1

    if not seed_dois:
        console.print("\n[red]Error:[/red] No DOIs found in seeds file.")
        return 1

    console.print(f"\n[green]Loaded {len(seed_dois)} seed papers[/green]")

    # Initialize components and run expansion
    try:
        async with OpenAlexClient(settings.openalex) as api_client:
            # Verify API connectivity
            if not await api_client.health_check():
                console.print("\n[red]Error:[/red] Cannot connect to OpenAlex API.")
                return 1
            console.print("[green]OpenAlex API connected[/green]")

            try:
                async with Neo4jClient(settings.neo4j) as db_client:
                    # Verify database connectivity
                    if not await db_client.verify_connection():
                        console.print("\n[red]Error:[/red] Cannot connect to Neo4j database.")
                        return 1
                    console.print("[green]Neo4j database connected[/green]\n")

                    # Create mapper and orchestrator
                    mapper = Mapper(settings.expansion)
                    orchestrator = ExpansionOrchestrator(
                        api_client,
                        db_client,
                        mapper,
                        settings.expansion,
                    )

                    # Run expansion
                    await orchestrator.expand(seed_dois)

            except Neo4jConnectionError as e:
                console.print(f"\n[red]Database error:[/red] {e}")
                console.print("\nMake sure Neo4j is running and credentials are correct.")
                return 1

        console.print("\n[bold green]Pipeline completed successfully![/bold green]")
        return 0

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        console.print("Progress has been saved. Run again to resume.")
        return 130

    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        import traceback
        if settings.debug:
            traceback.print_exc()
        return 1


def main() -> int:
    """Synchronous main entry point.

    Returns:
        Exit code.
    """
    return asyncio.run(async_main())


def run() -> None:
    """Entry point for console script."""
    sys.exit(main())


if __name__ == "__main__":
    run()
